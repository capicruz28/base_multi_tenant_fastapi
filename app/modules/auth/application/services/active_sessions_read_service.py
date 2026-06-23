"""Servicio único de lectura de sesiones activas (IAM-SESSIONS-V1 Enterprise)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import Request
from sqlalchemy import and_, func, or_, select

from app.core.application.base_service import BaseService
from app.core.config import settings
from app.core.logging_config import get_logger
from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
    get_active_sessions_by_user_core,
)
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import RefreshTokensTable, UsuarioTable
from app.infrastructure.database.tables_erp import OrgEmpresaTable
from app.modules.auth.application.session.active_session_read_columns import (
    active_session_token_columns,
)
from app.modules.auth.application.session.session_read_mapper import (
    map_row_to_admin_session,
    map_row_to_user_session,
)
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.presentation.schemas_admin_sessions import (
    AdminSessionRead,
    PaginatedAdminSessionsResponse,
)
from app.modules.auth.presentation.schemas_sessions import UserSessionRead
from app.shared.pagination.builder import build_paginated_response, calc_total_paginas
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

logger = get_logger(__name__)

ADMIN_SESSIONS_SORT_COLUMNS = frozenset(
    {
        "created_at",
        "last_used_at",
        "expires_at",
        "ip_address",
        "device_name",
        "client_type",
        "nombre_usuario",
        "token_id",
    }
)

_SORT_DIR_DEFAULTS: Dict[str, str] = {
    "created_at": "desc",
    "last_used_at": "desc",
    "expires_at": "desc",
}


def _session_column_map() -> Dict[str, Any]:
    cols = active_session_token_columns()
    by_name = {c.name: c for c in cols}
    return {
        "created_at": by_name["created_at"],
        "last_used_at": by_name["last_used_at"],
        "expires_at": by_name["expires_at"],
        "ip_address": by_name["ip_address"],
        "device_name": by_name["device_name"],
        "client_type": by_name["client_type"],
        "nombre_usuario": UsuarioTable.c.nombre_usuario,
        "token_id": by_name["token_id"],
    }


def _admin_base_from():
    return (
        RefreshTokensTable.join(
            UsuarioTable,
            RefreshTokensTable.c.usuario_id == UsuarioTable.c.usuario_id,
        )
        .outerjoin(
            OrgEmpresaTable,
            and_(
                RefreshTokensTable.c.empresa_id == OrgEmpresaTable.c.empresa_id,
                OrgEmpresaTable.c.cliente_id == RefreshTokensTable.c.cliente_id,
            ),
        )
    )


def _active_session_filters(
    cliente_id: UUID,
    *,
    client_type: Optional[str] = None,
    usuario_id: Optional[UUID] = None,
    search: Optional[str] = None,
):
    conditions = [
        RefreshTokensTable.c.cliente_id == cliente_id,
        RefreshTokensTable.c.is_revoked == False,  # noqa: E712
        RefreshTokensTable.c.expires_at > func.getdate(),
    ]
    if client_type:
        conditions.append(RefreshTokensTable.c.client_type == client_type)
    if usuario_id:
        conditions.append(RefreshTokensTable.c.usuario_id == usuario_id)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                UsuarioTable.c.nombre_usuario.like(pattern),
                UsuarioTable.c.nombre.like(pattern),
                UsuarioTable.c.apellido.like(pattern),
                RefreshTokensTable.c.ip_address.like(pattern),
                RefreshTokensTable.c.device_name.like(pattern),
            )
        )
    return and_(*conditions)


def _admin_select_columns():
    empresa_nombre = func.coalesce(
        OrgEmpresaTable.c.nombre_comercial,
        OrgEmpresaTable.c.razon_social,
    ).label("empresa_nombre")
    return select(
        *active_session_token_columns(),
        UsuarioTable.c.nombre_usuario,
        UsuarioTable.c.nombre,
        UsuarioTable.c.apellido,
        empresa_nombre,
    )


class ActiveSessionsReadService(BaseService):
    """Único servicio público de listado y enriquecimiento de sesiones activas."""

    @staticmethod
    async def resolve_current_token_id(
        request: Request,
        client_type: str,
        cliente_id: UUID,
    ) -> Optional[UUID]:
        """Resuelve token_id del refresh en request (solo módulo sesiones — GATE AJUSTE 5)."""
        refresh_token: Optional[str] = None
        if client_type == "web":
            refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
        else:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    refresh_token = body.get("refresh_token")
            except Exception:
                refresh_token = None

        return await RefreshTokenService.resolve_current_token_id_from_refresh(
            refresh_token,
            cliente_id,
        )

    @staticmethod
    async def list_user_sessions(
        cliente_id: UUID,
        usuario_id: UUID,
        *,
        current_token_id: Optional[UUID] = None,
    ) -> List[UserSessionRead]:
        rows = await get_active_sessions_by_user_core(usuario_id, cliente_id)
        return [
            map_row_to_user_session(row, current_token_id=current_token_id)
            for row in rows
        ]

    @staticmethod
    async def list_admin_sessions(
        cliente_id: UUID,
        *,
        pagination: ErpPaginationParams,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        client_type: Optional[str] = None,
        usuario_id: Optional[UUID] = None,
    ) -> Union[List[AdminSessionRead], PaginatedAdminSessionsResponse]:
        where_clause = _active_session_filters(
            cliente_id,
            client_type=client_type,
            usuario_id=usuario_id,
            search=search,
        )
        column_map = _session_column_map()
        default_order = [
            (RefreshTokensTable.c.last_used_at, "desc"),
            (RefreshTokensTable.c.token_id, "asc"),
        ]

        list_query = _admin_select_columns().select_from(_admin_base_from()).where(where_clause)
        list_query = apply_erp_sort(
            list_query,
            allowed_columns=ADMIN_SESSIONS_SORT_COLUMNS,
            column_map=column_map,
            sort_by=sort_by,
            sort_dir=sort_order,
            default_order=default_order,
            tie_breaker=("token_id", RefreshTokensTable.c.token_id),
            column_dir_defaults=_SORT_DIR_DEFAULTS,
        )
        list_query = apply_erp_pagination(list_query, pagination)

        total: Optional[int] = None
        if pagination.is_paginated:
            count_query = (
                select(func.count())
                .select_from(_admin_base_from())
                .where(where_clause)
            )
            count_rows = await execute_query(count_query, client_id=cliente_id)
            total = extract_count(count_rows)

        rows = await execute_query(list_query, client_id=cliente_id)
        items = [map_row_to_admin_session(row) for row in rows]

        if not pagination.is_paginated:
            logger.info(
                "[ADMIN-SESSIONS] Modo legacy: %s sesiones (cliente=%s)",
                len(items),
                cliente_id,
            )
            return items

        envelope = build_paginated_response(items, total or 0, pagination)
        return PaginatedAdminSessionsResponse(
            items=envelope.items,
            total=envelope.total,
            sessions=envelope.items,
            total_sesiones=envelope.total,
            pagina_actual=envelope.pagina_actual,
            total_paginas=calc_total_paginas(total or 0, pagination.limit),
            limit=envelope.limit,
        )

    @staticmethod
    async def get_owned_session_row_for_user(
        token_id: UUID,
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Fila refresh_tokens del usuario (cualquier estado) — ownership self-revoke."""
        query = (
            _admin_select_columns()
            .select_from(_admin_base_from())
            .where(
                and_(
                    RefreshTokensTable.c.token_id == token_id,
                    RefreshTokensTable.c.cliente_id == cliente_id,
                    RefreshTokensTable.c.usuario_id == usuario_id,
                )
            )
        )
        rows = await execute_query(query, client_id=cliente_id)
        return rows[0] if rows else None

    @staticmethod
    async def get_active_session_row_for_user(
        token_id: UUID,
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Verifica sesión activa propiedad del usuario (self-revoke)."""
        query = (
            _admin_select_columns()
            .select_from(_admin_base_from())
            .where(
                and_(
                    RefreshTokensTable.c.token_id == token_id,
                    RefreshTokensTable.c.cliente_id == cliente_id,
                    RefreshTokensTable.c.usuario_id == usuario_id,
                    RefreshTokensTable.c.is_revoked == False,  # noqa: E712
                    RefreshTokensTable.c.expires_at > func.getdate(),
                )
            )
        )
        rows = await execute_query(query, client_id=cliente_id)
        return rows[0] if rows else None


__all__ = [
    "ADMIN_SESSIONS_SORT_COLUMNS",
    "ActiveSessionsReadService",
]
