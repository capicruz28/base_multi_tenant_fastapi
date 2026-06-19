"""IAM-SESSIONS-PA-001 — listado admin de sesiones activas (paginación opt-in)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, func, or_, select

from app.core.application.base_service import BaseService
from app.core.logging_config import get_logger
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import RefreshTokensTable, UsuarioTable
from app.modules.auth.presentation.schemas_admin_sessions import (
    AdminSessionRead,
    PaginatedAdminSessionsResponse,
)
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
    return {
        "created_at": RefreshTokensTable.c.created_at,
        "last_used_at": RefreshTokensTable.c.last_used_at,
        "expires_at": RefreshTokensTable.c.expires_at,
        "ip_address": RefreshTokensTable.c.ip_address,
        "device_name": RefreshTokensTable.c.device_name,
        "client_type": RefreshTokensTable.c.client_type,
        "nombre_usuario": UsuarioTable.c.nombre_usuario,
        "token_id": RefreshTokensTable.c.token_id,
    }


def _base_from():
    return RefreshTokensTable.join(
        UsuarioTable,
        RefreshTokensTable.c.usuario_id == UsuarioTable.c.usuario_id,
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


def _select_columns():
    return select(
        RefreshTokensTable.c.token_id,
        RefreshTokensTable.c.usuario_id,
        RefreshTokensTable.c.cliente_id,
        RefreshTokensTable.c.created_at,
        RefreshTokensTable.c.last_used_at,
        RefreshTokensTable.c.expires_at,
        RefreshTokensTable.c.device_name,
        RefreshTokensTable.c.device_id,
        RefreshTokensTable.c.ip_address,
        RefreshTokensTable.c.user_agent,
        RefreshTokensTable.c.client_type,
        UsuarioTable.c.nombre_usuario,
        UsuarioTable.c.nombre,
        UsuarioTable.c.apellido,
    )


class AdminSessionsService(BaseService):
    """Consultas de sesiones activas para administradores tenant."""

    @staticmethod
    async def list_admin_active_sessions(
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

        list_query = _select_columns().select_from(_base_from()).where(where_clause)
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
                .select_from(_base_from())
                .where(where_clause)
            )
            count_rows = await execute_query(count_query, client_id=cliente_id)
            total = extract_count(count_rows)

        rows = await execute_query(list_query, client_id=cliente_id)
        items = [AdminSessionRead.model_validate(row) for row in rows]

        if not pagination.is_paginated:
            logger.info(
                "[ADMIN-SESSIONS] Modo legacy: %s sesiones (cliente=%s)",
                len(items),
                cliente_id,
            )
            return items

        envelope = build_paginated_response(items, total or 0, pagination)
        return PaginatedAdminSessionsResponse(
            sessions=envelope.items,
            total_sesiones=envelope.total,
            pagina_actual=envelope.pagina_actual,
            total_paginas=calc_total_paginas(total or 0, pagination.limit),
            limit=envelope.limit,
        )
