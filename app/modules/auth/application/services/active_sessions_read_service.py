"""Servicio único de lectura de sesiones activas (C09 — IAM Session V2)."""
from __future__ import annotations

from dataclasses import dataclass
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
from app.infrastructure.database.queries.auth.session import (
    get_family_by_session_id_core,
    list_active_sessions_oldest_first_core,
)
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
    UsuarioTable,
)
from app.infrastructure.database.tables_erp import OrgEmpresaTable
from app.modules.auth.application.session.active_session_read_columns import (
    ADMIN_SESSIONS_SORT_COLUMNS_V1,
    active_session_token_columns,
    active_session_v2_session_columns,
    admin_sessions_sort_columns,
    normalize_admin_sort_by,
    v2_session_column_map,
)
from app.modules.auth.application.session.session_read_mapper import (
    map_row_to_admin_session,
    map_row_to_user_session,
)
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.services.session_query_service import SessionQueryService
from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from app.modules.auth.presentation.schemas_admin_sessions import (
    AdminSessionRead,
    PaginatedAdminSessionsResponse,
)
from app.modules.auth.presentation.schemas_sessions import UserSessionRead
from app.shared.pagination.builder import build_paginated_response, calc_total_paginas
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

logger = get_logger(__name__)

# Compat legacy tests/imports — whitelist V1.
ADMIN_SESSIONS_SORT_COLUMNS = ADMIN_SESSIONS_SORT_COLUMNS_V1

_SORT_DIR_DEFAULTS: Dict[str, str] = {
    "created_at": "desc",
    "last_used_at": "desc",
    "last_refresh_at": "desc",
    "expires_at": "desc",
}


@dataclass(frozen=True)
class SessionRevokeTarget:
    """Resolución read-only de identificador de revocación (session_id o token_id)."""

    session_id: Optional[UUID]
    token_id: Optional[UUID]
    usuario_id: Optional[UUID]
    is_active: bool
    row: Optional[Dict[str, Any]] = None


def _session_column_map_v1() -> Dict[str, Any]:
    token_cols = {c.name: c for c in active_session_token_columns()}
    return {
        "created_at": token_cols["created_at"],
        "last_used_at": token_cols["last_used_at"],
        "expires_at": token_cols["expires_at"],
        "ip_address": UserSessionTable.c.last_seen_ip,
        "device_name": UserSessionTable.c.device_name,
        "client_type": UserSessionTable.c.platform,
        "nombre_usuario": UsuarioTable.c.nombre_usuario,
        "token_id": token_cols["token_id"],
    }


def _admin_base_from_v1():
    return (
        RefreshTokensTable.join(
            UserSessionTable,
            RefreshTokensTable.c.session_id == UserSessionTable.c.session_id,
            isouter=True,
        )
        .join(
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


def _admin_base_from_v2():
    return (
        UserSessionTable.join(
            TokenFamilyTable,
            and_(
                TokenFamilyTable.c.session_id == UserSessionTable.c.session_id,
                TokenFamilyTable.c.cliente_id == UserSessionTable.c.cliente_id,
                TokenFamilyTable.c.is_compromised == False,  # noqa: E712
            ),
        )
        .join(
            RefreshTokensTable,
            RefreshTokensTable.c.token_id == TokenFamilyTable.c.current_token_id,
        )
        .join(
            UsuarioTable,
            UserSessionTable.c.usuario_id == UsuarioTable.c.usuario_id,
        )
        .outerjoin(
            OrgEmpresaTable,
            and_(
                UserSessionTable.c.empresa_id == OrgEmpresaTable.c.empresa_id,
                OrgEmpresaTable.c.cliente_id == UserSessionTable.c.cliente_id,
            ),
        )
    )


def _active_session_filters_v1(
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
        conditions.append(UserSessionTable.c.platform == client_type)
    if usuario_id:
        conditions.append(RefreshTokensTable.c.usuario_id == usuario_id)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                UsuarioTable.c.nombre_usuario.like(pattern),
                UsuarioTable.c.nombre.like(pattern),
                UsuarioTable.c.apellido.like(pattern),
                UserSessionTable.c.last_seen_ip.like(pattern),
                UserSessionTable.c.login_ip.like(pattern),
                UserSessionTable.c.device_name.like(pattern),
            )
        )
    return and_(*conditions)


def _active_session_filters_v2(
    cliente_id: UUID,
    *,
    platform: Optional[str] = None,
    usuario_id: Optional[UUID] = None,
    search: Optional[str] = None,
):
    conditions = [
        UserSessionTable.c.cliente_id == cliente_id,
        UserSessionTable.c.is_active == True,  # noqa: E712
        UserSessionTable.c.expires_at > func.getdate(),
        TokenFamilyTable.c.current_token_id.isnot(None),
        RefreshTokensTable.c.is_revoked == False,  # noqa: E712
        RefreshTokensTable.c.is_used == False,  # noqa: E712
        RefreshTokensTable.c.expires_at > func.getdate(),
    ]
    if platform:
        conditions.append(UserSessionTable.c.platform == platform)
    if usuario_id:
        conditions.append(UserSessionTable.c.usuario_id == usuario_id)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(
                UsuarioTable.c.nombre_usuario.like(pattern),
                UsuarioTable.c.nombre.like(pattern),
                UsuarioTable.c.apellido.like(pattern),
                UserSessionTable.c.login_ip.like(pattern),
                UserSessionTable.c.last_seen_ip.like(pattern),
                UserSessionTable.c.device_name.like(pattern),
                UserSessionTable.c.platform.like(pattern),
            )
        )
    return and_(*conditions)


def _admin_select_columns_v1():
    empresa_nombre = func.coalesce(
        OrgEmpresaTable.c.nombre_comercial,
        OrgEmpresaTable.c.razon_social,
    ).label("empresa_nombre")
    return select(
        *active_session_token_columns(),
        UserSessionTable.c.device_name,
        UserSessionTable.c.device_id,
        UserSessionTable.c.last_seen_ip.label("ip_address"),
        UserSessionTable.c.user_agent,
        UserSessionTable.c.platform.label("client_type"),
        UsuarioTable.c.nombre_usuario,
        UsuarioTable.c.nombre,
        UsuarioTable.c.apellido,
        empresa_nombre,
    )


def _admin_select_columns_v2():
    empresa_nombre = func.coalesce(
        OrgEmpresaTable.c.nombre_comercial,
        OrgEmpresaTable.c.razon_social,
    ).label("empresa_nombre")
    session_cols = {c.name: c for c in active_session_v2_session_columns()}
    return select(
        session_cols["session_id"],
        session_cols["usuario_id"],
        session_cols["cliente_id"],
        session_cols["empresa_id"],
        session_cols["login_method"],
        session_cols["platform"],
        session_cols["device_name"],
        session_cols["device_id"],
        session_cols["user_agent"],
        session_cols["login_ip"],
        session_cols["last_seen_ip"],
        session_cols["created_at"],
        session_cols["last_refresh_at"],
        session_cols["expires_at"],
        session_cols["revoked_at"],
        session_cols["revoked_reason"],
        RefreshTokensTable.c.token_id,
        TokenFamilyTable.c.family_id,
        UsuarioTable.c.nombre_usuario,
        UsuarioTable.c.nombre,
        UsuarioTable.c.apellido,
        empresa_nombre,
    )


def _build_v2_composite_row(
    session_row: Dict[str, Any],
    family_row: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    token_id = family_row.get("current_token_id")
    if not token_id or family_row.get("is_compromised"):
        return None
    platform = str(session_row.get("platform") or "web")
    return {
        **session_row,
        "token_id": token_id,
        "family_id": family_row.get("family_id"),
        "platform": platform,
        "client_type": platform,
        "last_used_at": session_row.get("last_refresh_at"),
        "ip_address": session_row.get("last_seen_ip") or session_row.get("login_ip"),
    }


class ActiveSessionsReadService(BaseService):
    """Único servicio público de listado y enriquecimiento de sesiones activas."""

    @staticmethod
    async def resolve_current_token_id(
        request: Request,
        client_type: str,
        cliente_id: UUID,
    ) -> Optional[UUID]:
        """Resuelve token_id del refresh en request (V1)."""
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
    async def resolve_current_session_id(
        request: Request,
        client_type: str,
        cliente_id: UUID,
    ) -> Optional[UUID]:
        """Resuelve session_id del refresh en request (V2 — C08/C10)."""
        if not is_session_v2_enabled(cliente_id):
            return None

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

        if not refresh_token:
            return None

        from app.modules.auth.application.services.session_probe_service import (
            SessionProbeService,
        )

        probe = await SessionProbeService.resolve_context(
            cliente_id,
            refresh_token=refresh_token,
        )
        return probe.current_session_id

    @staticmethod
    async def list_user_sessions(
        cliente_id: UUID,
        usuario_id: UUID,
        *,
        current_token_id: Optional[UUID] = None,
        current_session_id: Optional[UUID] = None,
    ) -> List[UserSessionRead]:
        if is_session_v2_enabled(cliente_id):
            return await ActiveSessionsReadService._list_user_sessions_v2(
                cliente_id,
                usuario_id,
                current_session_id=current_session_id,
                current_token_id=current_token_id,
            )

        rows = await get_active_sessions_by_user_core(usuario_id, cliente_id)
        enriched: List[Dict[str, Any]] = []
        for row in rows:
            merged = dict(row)
            session_id = merged.get("session_id")
            if session_id:
                session_row = await SessionQueryService.get_session(
                    session_id,
                    cliente_id,
                )
                if session_row:
                    merged.setdefault(
                        "client_type",
                        session_row.get("platform") or "web",
                    )
                    merged.setdefault("device_name", session_row.get("device_name"))
                    merged.setdefault("device_id", session_row.get("device_id"))
                    merged.setdefault(
                        "ip_address",
                        session_row.get("last_seen_ip") or session_row.get("login_ip"),
                    )
                    merged.setdefault("user_agent", session_row.get("user_agent"))
            enriched.append(merged)
        return [
            map_row_to_user_session(row, current_token_id=current_token_id)
            for row in enriched
        ]

    @staticmethod
    async def _list_user_sessions_v2(
        cliente_id: UUID,
        usuario_id: UUID,
        *,
        current_session_id: Optional[UUID],
        current_token_id: Optional[UUID],
    ) -> List[UserSessionRead]:
        session_rows = await list_active_sessions_oldest_first_core(
            usuario_id,
            cliente_id,
        )
        session_rows.sort(
            key=lambda r: (
                r.get("last_refresh_at") or r.get("created_at"),
                str(r.get("session_id")),
            ),
            reverse=True,
        )

        items: List[UserSessionRead] = []
        for session_row in session_rows:
            session_id = session_row.get("session_id")
            if not session_id:
                continue
            family_row = await get_family_by_session_id_core(session_id, cliente_id)
            if not family_row:
                continue
            composite = _build_v2_composite_row(session_row, family_row)
            if not composite:
                continue
            items.append(
                map_row_to_user_session(
                    composite,
                    current_session_id=current_session_id,
                    current_token_id=current_token_id,
                    v2=True,
                )
            )
        return items

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
        v2 = is_session_v2_enabled(cliente_id)
        if v2:
            return await ActiveSessionsReadService._list_admin_sessions_v2(
                cliente_id,
                pagination=pagination,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                platform=client_type,
                usuario_id=usuario_id,
            )
        return await ActiveSessionsReadService._list_admin_sessions_v1(
            cliente_id,
            pagination=pagination,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            client_type=client_type,
            usuario_id=usuario_id,
        )

    @staticmethod
    async def _list_admin_sessions_v1(
        cliente_id: UUID,
        *,
        pagination: ErpPaginationParams,
        search: Optional[str],
        sort_by: Optional[str],
        sort_order: Optional[str],
        client_type: Optional[str],
        usuario_id: Optional[UUID],
    ) -> Union[List[AdminSessionRead], PaginatedAdminSessionsResponse]:
        where_clause = _active_session_filters_v1(
            cliente_id,
            client_type=client_type,
            usuario_id=usuario_id,
            search=search,
        )
        column_map = _session_column_map_v1()
        default_order = [
            (RefreshTokensTable.c.last_used_at, "desc"),
            (RefreshTokensTable.c.token_id, "asc"),
        ]

        list_query = (
            _admin_select_columns_v1().select_from(_admin_base_from_v1()).where(where_clause)
        )
        list_query = apply_erp_sort(
            list_query,
            allowed_columns=admin_sessions_sort_columns(v2_enabled=False),
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
                .select_from(_admin_base_from_v1())
                .where(where_clause)
            )
            count_rows = await execute_query(count_query, client_id=cliente_id)
            total = extract_count(count_rows)

        rows = await execute_query(list_query, client_id=cliente_id)
        items = [map_row_to_admin_session(row) for row in rows]

        if not pagination.is_paginated:
            logger.info(
                "[ADMIN-SESSIONS] Modo legacy V1: %s sesiones (cliente=%s)",
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
    async def _list_admin_sessions_v2(
        cliente_id: UUID,
        *,
        pagination: ErpPaginationParams,
        search: Optional[str],
        sort_by: Optional[str],
        sort_order: Optional[str],
        platform: Optional[str],
        usuario_id: Optional[UUID],
    ) -> Union[List[AdminSessionRead], PaginatedAdminSessionsResponse]:
        normalized_sort = normalize_admin_sort_by(sort_by, v2_enabled=True)
        where_clause = _active_session_filters_v2(
            cliente_id,
            platform=platform,
            usuario_id=usuario_id,
            search=search,
        )
        column_map = v2_session_column_map()
        column_map["nombre_usuario"] = UsuarioTable.c.nombre_usuario
        column_map["token_id"] = RefreshTokensTable.c.token_id
        column_map["family_id"] = TokenFamilyTable.c.family_id

        default_order = [
            (UserSessionTable.c.last_refresh_at, "desc"),
            (UserSessionTable.c.session_id, "asc"),
        ]

        list_query = (
            _admin_select_columns_v2().select_from(_admin_base_from_v2()).where(where_clause)
        )
        list_query = apply_erp_sort(
            list_query,
            allowed_columns=admin_sessions_sort_columns(v2_enabled=True),
            column_map=column_map,
            sort_by=normalized_sort,
            sort_dir=sort_order,
            default_order=default_order,
            tie_breaker=("session_id", UserSessionTable.c.session_id),
            column_dir_defaults=_SORT_DIR_DEFAULTS,
        )
        list_query = apply_erp_pagination(list_query, pagination)

        total: Optional[int] = None
        if pagination.is_paginated:
            count_query = (
                select(func.count())
                .select_from(_admin_base_from_v2())
                .where(where_clause)
            )
            count_rows = await execute_query(count_query, client_id=cliente_id)
            total = extract_count(count_rows)

        rows = await execute_query(list_query, client_id=cliente_id)
        items = [
            map_row_to_admin_session(
                {
                    **row,
                    "client_type": row.get("platform") or "web",
                    "last_used_at": row.get("last_refresh_at"),
                    "ip_address": row.get("last_seen_ip") or row.get("login_ip"),
                },
                v2=True,
            )
            for row in rows
        ]

        if not pagination.is_paginated:
            logger.info(
                "[ADMIN-SESSIONS] Modo legacy V2: %s sesiones (cliente=%s)",
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
    async def resolve_user_revoke_target(
        identifier: UUID,
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> SessionRevokeTarget:
        """Resuelve session_id o token_id para self-revoke (read-only)."""
        if is_session_v2_enabled(cliente_id):
            session_row = await SessionQueryService.get_session(identifier, cliente_id)
            if session_row and str(session_row.get("usuario_id")) == str(usuario_id):
                family_row = await SessionQueryService.get_family_for_session(
                    identifier,
                    cliente_id,
                )
                token_id = family_row.get("current_token_id") if family_row else None
                return SessionRevokeTarget(
                    session_id=identifier,
                    token_id=token_id,
                    usuario_id=usuario_id,
                    is_active=True,
                    row=session_row,
                )

            owned = await ActiveSessionsReadService.get_owned_session_row_for_user(
                identifier,
                cliente_id,
                usuario_id,
            )
            if owned:
                session_id = owned.get("session_id")
                active_session = None
                if session_id:
                    active_session = await SessionQueryService.get_session(
                        session_id,
                        cliente_id,
                    )
                return SessionRevokeTarget(
                    session_id=session_id,
                    token_id=identifier,
                    usuario_id=usuario_id,
                    is_active=active_session is not None,
                    row=owned,
                )

            return SessionRevokeTarget(
                session_id=None,
                token_id=None,
                usuario_id=usuario_id,
                is_active=False,
                row=None,
            )

        owned = await ActiveSessionsReadService.get_owned_session_row_for_user(
            identifier,
            cliente_id,
            usuario_id,
        )
        if not owned:
            return SessionRevokeTarget(
                session_id=None,
                token_id=None,
                usuario_id=usuario_id,
                is_active=False,
                row=None,
            )

        active = await ActiveSessionsReadService.get_active_session_row_for_user(
            identifier,
            cliente_id,
            usuario_id,
        )
        return SessionRevokeTarget(
            session_id=owned.get("session_id"),
            token_id=identifier,
            usuario_id=usuario_id,
            is_active=active is not None,
            row=active or owned,
        )

    @staticmethod
    async def resolve_admin_revoke_target(
        identifier: UUID,
        cliente_id: UUID,
    ) -> SessionRevokeTarget:
        """Resuelve session_id o token_id para admin revoke (read-only)."""
        if is_session_v2_enabled(cliente_id):
            session_row = await SessionQueryService.get_session(identifier, cliente_id)
            if session_row:
                family_row = await SessionQueryService.get_family_for_session(
                    identifier,
                    cliente_id,
                )
                return SessionRevokeTarget(
                    session_id=identifier,
                    token_id=(
                        family_row.get("current_token_id") if family_row else None
                    ),
                    usuario_id=session_row.get("usuario_id"),
                    is_active=True,
                    row=session_row,
                )

            owned = await ActiveSessionsReadService.get_owned_session_row_for_admin(
                identifier,
                cliente_id,
            )
            if owned:
                session_id = owned.get("session_id")
                active_session = None
                if session_id:
                    active_session = await SessionQueryService.get_session(
                        session_id,
                        cliente_id,
                    )
                return SessionRevokeTarget(
                    session_id=session_id,
                    token_id=identifier,
                    usuario_id=owned.get("usuario_id"),
                    is_active=active_session is not None,
                    row=owned,
                )

            return SessionRevokeTarget(
                session_id=None,
                token_id=None,
                usuario_id=None,
                is_active=False,
                row=None,
            )

        row = await ActiveSessionsReadService.get_active_session_row_for_admin(
            identifier,
            cliente_id,
        )
        if row:
            return SessionRevokeTarget(
                session_id=row.get("session_id"),
                token_id=identifier,
                usuario_id=row.get("usuario_id"),
                is_active=True,
                row=row,
            )

        owned = await ActiveSessionsReadService.get_owned_session_row_for_admin(
            identifier,
            cliente_id,
        )
        if owned:
            return SessionRevokeTarget(
                session_id=owned.get("session_id"),
                token_id=identifier,
                usuario_id=owned.get("usuario_id"),
                is_active=False,
                row=owned,
            )

        return SessionRevokeTarget(
            session_id=None,
            token_id=None,
            usuario_id=None,
            is_active=False,
            row=None,
        )

    @staticmethod
    async def get_owned_session_row_for_user(
        token_id: UUID,
        cliente_id: UUID,
        usuario_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Fila refresh_tokens del usuario (cualquier estado) — ownership self-revoke V1."""
        query = (
            _admin_select_columns_v1()
            .select_from(_admin_base_from_v1())
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
        """Verifica sesión activa propiedad del usuario (self-revoke V1)."""
        query = (
            _admin_select_columns_v1()
            .select_from(_admin_base_from_v1())
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

    @staticmethod
    async def get_owned_session_row_for_admin(
        token_id: UUID,
        cliente_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        query = (
            _admin_select_columns_v1()
            .select_from(_admin_base_from_v1())
            .where(
                and_(
                    RefreshTokensTable.c.token_id == token_id,
                    RefreshTokensTable.c.cliente_id == cliente_id,
                )
            )
        )
        rows = await execute_query(query, client_id=cliente_id)
        return rows[0] if rows else None

    @staticmethod
    async def get_active_session_row_for_admin(
        token_id: UUID,
        cliente_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        query = (
            _admin_select_columns_v1()
            .select_from(_admin_base_from_v1())
            .where(
                and_(
                    RefreshTokensTable.c.token_id == token_id,
                    RefreshTokensTable.c.cliente_id == cliente_id,
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
    "SessionRevokeTarget",
]
