"""F6-P1/P2a — SQL Core de identidad (usuario login + access level)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import Select, Update, and_, case, func, or_, select, update

from app.infrastructure.database.tables import RolTable, UsuarioRolTable, UsuarioTable


def _access_level_base_select():
    super_admin_count = func.count(
        case(
            (
                and_(
                    RolTable.c.codigo_rol == "SUPER_ADMIN",
                    RolTable.c.nivel_acceso == 5,
                ),
                1,
            ),
            else_=None,
        )
    ).label("super_admin_count")
    return select(
        func.coalesce(func.max(RolTable.c.nivel_acceso), 1).label("max_level"),
        super_admin_count,
        func.count().label("total_roles"),
    ).select_from(
        UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
    )


def _empresa_scope_conditions(*, empresa_id: Optional[UUID]):
    if empresa_id is None:
        return []
    return [
        or_(
            UsuarioRolTable.c.empresa_id.is_(None),
            UsuarioRolTable.c.empresa_id == empresa_id,
        )
    ]


def select_user_access_level_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Select:
    conditions = [
        UsuarioRolTable.c.usuario_id == usuario_id,
        UsuarioRolTable.c.cliente_id == cliente_id,
        UsuarioRolTable.c.es_activo == True,
        RolTable.c.es_activo == True,
        or_(RolTable.c.cliente_id == cliente_id, RolTable.c.cliente_id.is_(None)),
        *_empresa_scope_conditions(empresa_id=empresa_id),
    ]
    return _access_level_base_select().where(and_(*conditions))


def select_user_access_level_engine_scoped(
    *,
    usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Select:
    conditions = [
        UsuarioRolTable.c.usuario_id == usuario_id,
        UsuarioRolTable.c.es_activo == True,
        RolTable.c.es_activo == True,
        *_empresa_scope_conditions(empresa_id=empresa_id),
    ]
    return _access_level_base_select().where(and_(*conditions))


def select_user_by_username_row_scoped(
    *,
    cliente_id: UUID,
    username: str,
) -> Select:
    return (
        select(
            UsuarioTable.c.usuario_id,
            UsuarioTable.c.cliente_id,
            UsuarioTable.c.nombre_usuario,
            UsuarioTable.c.correo,
            UsuarioTable.c.contrasena,
            UsuarioTable.c.nombre,
            UsuarioTable.c.apellido,
            UsuarioTable.c.es_activo,
            UsuarioTable.c.requiere_cambio_contrasena,
            UsuarioTable.c.proveedor_autenticacion,
        )
        .where(
            and_(
                UsuarioTable.c.cliente_id == cliente_id,
                UsuarioTable.c.nombre_usuario == username,
                UsuarioTable.c.es_eliminado == 0,
            )
        )
    )


def select_user_by_username_engine_scoped(*, username: str) -> Select:
    return (
        select(
            UsuarioTable.c.usuario_id,
            UsuarioTable.c.cliente_id,
            UsuarioTable.c.nombre_usuario,
            UsuarioTable.c.correo,
            UsuarioTable.c.contrasena,
            UsuarioTable.c.nombre,
            UsuarioTable.c.apellido,
            UsuarioTable.c.es_activo,
            UsuarioTable.c.requiere_cambio_contrasena,
            UsuarioTable.c.proveedor_autenticacion,
        )
        .where(
            and_(
                UsuarioTable.c.nombre_usuario == username,
                UsuarioTable.c.es_eliminado == 0,
            )
        )
    )


def update_user_last_access(*, usuario_id: UUID) -> Update:
    return (
        update(UsuarioTable)
        .where(UsuarioTable.c.usuario_id == usuario_id)
        .values(fecha_ultimo_acceso=func.getdate())
    )


def _user_display_columns():
    return (
        UsuarioTable.c.usuario_id,
        UsuarioTable.c.nombre_usuario,
        UsuarioTable.c.nombre,
        UsuarioTable.c.apellido,
    )


def select_users_by_ids_row_scoped(
    *,
    cliente_id: UUID,
    usuario_ids: list[UUID],
) -> Select:
    return select(*_user_display_columns()).where(
        and_(
            UsuarioTable.c.cliente_id == cliente_id,
            UsuarioTable.c.usuario_id.in_(usuario_ids),
            UsuarioTable.c.es_eliminado == 0,
        )
    )


def select_users_by_ids_engine_scoped(*, usuario_ids: list[UUID]) -> Select:
    return select(*_user_display_columns()).where(
        and_(
            UsuarioTable.c.usuario_id.in_(usuario_ids),
            UsuarioTable.c.es_eliminado == 0,
        )
    )


def search_user_ids_row_scoped(*, cliente_id: UUID, search: str) -> Select:
    pattern = f"%{search}%"
    return select(UsuarioTable.c.usuario_id).where(
        and_(
            UsuarioTable.c.cliente_id == cliente_id,
            UsuarioTable.c.es_eliminado == 0,
            or_(
                UsuarioTable.c.nombre_usuario.like(pattern),
                UsuarioTable.c.nombre.like(pattern),
                UsuarioTable.c.apellido.like(pattern),
            ),
        )
    )


def search_user_ids_engine_scoped(*, search: str) -> Select:
    pattern = f"%{search}%"
    return select(UsuarioTable.c.usuario_id).where(
        and_(
            UsuarioTable.c.es_eliminado == 0,
            or_(
                UsuarioTable.c.nombre_usuario.like(pattern),
                UsuarioTable.c.nombre.like(pattern),
                UsuarioTable.c.apellido.like(pattern),
            ),
        )
    )


__all__ = [
    "search_user_ids_engine_scoped",
    "search_user_ids_row_scoped",
    "select_user_access_level_engine_scoped",
    "select_user_access_level_row_scoped",
    "select_user_by_username_engine_scoped",
    "select_user_by_username_row_scoped",
    "select_users_by_ids_engine_scoped",
    "select_users_by_ids_row_scoped",
    "update_user_last_access",
]
