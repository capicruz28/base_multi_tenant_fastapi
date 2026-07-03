"""F8-A — SQL Core auth runtime (empresa default, admin cliente, password policy)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, text

from app.infrastructure.database.tables import RolTable, UsuarioRolTable, UsuarioTable


def _empresa_scope_conditions(*, empresa_id: Optional[UUID]):
    if empresa_id is None:
        return []
    return [
        or_(
            UsuarioRolTable.c.empresa_id.is_(None),
            UsuarioRolTable.c.empresa_id == empresa_id,
        )
    ]


def select_distinct_empresa_ids_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
) -> Select:
    return (
        select(UsuarioRolTable.c.empresa_id)
        .where(
            and_(
                UsuarioRolTable.c.usuario_id == usuario_id,
                UsuarioRolTable.c.cliente_id == cliente_id,
                UsuarioRolTable.c.es_activo == True,
                UsuarioRolTable.c.empresa_id.isnot(None),
            )
        )
        .distinct()
        .order_by(UsuarioRolTable.c.empresa_id)
    )


def select_distinct_empresa_ids_engine_scoped(*, usuario_id: UUID) -> Select:
    return (
        select(UsuarioRolTable.c.empresa_id)
        .where(
            and_(
                UsuarioRolTable.c.usuario_id == usuario_id,
                UsuarioRolTable.c.es_activo == True,
                UsuarioRolTable.c.empresa_id.isnot(None),
            )
        )
        .distinct()
        .order_by(UsuarioRolTable.c.empresa_id)
    )


def select_admin_tenant_wide_count_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
) -> Select:
    return select(func.count().label("admin_sin_empresa_count")).where(
        and_(
            UsuarioRolTable.c.usuario_id == usuario_id,
            UsuarioRolTable.c.cliente_id == cliente_id,
            UsuarioRolTable.c.es_activo == True,
            UsuarioRolTable.c.empresa_id.is_(None),
        )
    )


def select_admin_tenant_wide_count_engine_scoped(*, usuario_id: UUID) -> Select:
    return select(func.count().label("admin_sin_empresa_count")).where(
        and_(
            UsuarioRolTable.c.usuario_id == usuario_id,
            UsuarioRolTable.c.es_activo == True,
            UsuarioRolTable.c.empresa_id.is_(None),
        )
    )


def select_user_role_names_row_scoped(
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
    return (
        select(RolTable.c.nombre)
        .distinct()
        .select_from(
            UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
        )
        .where(and_(*conditions))
        .order_by(RolTable.c.nombre)
    )


def select_user_role_names_engine_scoped(
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
    return (
        select(RolTable.c.nombre)
        .distinct()
        .select_from(
            UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
        )
        .where(and_(*conditions))
        .order_by(RolTable.c.nombre)
    )


def select_user_roles_for_auth_row_scoped(
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
    return (
        select(
            RolTable.c.rol_id,
            RolTable.c.nombre,
            RolTable.c.descripcion,
            RolTable.c.nivel_acceso,
            RolTable.c.codigo_rol,
            RolTable.c.es_activo,
            RolTable.c.fecha_creacion,
            RolTable.c.cliente_id,
        )
        .select_from(
            UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
        )
        .where(and_(*conditions))
    )


def select_user_roles_for_auth_engine_scoped(
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
    return (
        select(
            RolTable.c.rol_id,
            RolTable.c.nombre,
            RolTable.c.descripcion,
            RolTable.c.nivel_acceso,
            RolTable.c.codigo_rol,
            RolTable.c.es_activo,
            RolTable.c.fecha_creacion,
            RolTable.c.cliente_id,
        )
        .select_from(
            UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
        )
        .where(and_(*conditions))
    )


def select_user_password_policy_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
) -> Select:
    return select(
        UsuarioTable.c.requiere_cambio_contrasena,
        UsuarioTable.c.proveedor_autenticacion,
        UsuarioTable.c.contrasena,
    ).where(
        and_(
            UsuarioTable.c.usuario_id == usuario_id,
            UsuarioTable.c.cliente_id == cliente_id,
            UsuarioTable.c.es_eliminado == 0,
        )
    )


def select_user_password_policy_engine_scoped(*, usuario_id: UUID) -> Select:
    return select(
        UsuarioTable.c.requiere_cambio_contrasena,
        UsuarioTable.c.proveedor_autenticacion,
        UsuarioTable.c.contrasena,
    ).where(
        and_(
            UsuarioTable.c.usuario_id == usuario_id,
            UsuarioTable.c.es_eliminado == 0,
        )
    )


def text_user_empresa_default_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
):
    return text(
        """
        SELECT empresa_default_id
        FROM usuario
        WHERE usuario_id = :usuario_id
          AND cliente_id = :cliente_id
          AND es_eliminado = 0
        """
    ).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)


def text_user_empresa_default_engine_scoped(*, usuario_id: UUID):
    return text(
        """
        SELECT empresa_default_id
        FROM usuario
        WHERE usuario_id = :usuario_id
          AND es_eliminado = 0
        """
    ).bindparams(usuario_id=usuario_id)


def text_admin_cliente_count_row_scoped(
    *,
    usuario_id: UUID,
    cliente_id: UUID,
    empresa_id: Optional[UUID] = None,
):
    if empresa_id is not None:
        return text(
            """
            SELECT COUNT(*) AS admin_cliente_count
            FROM usuario_rol ur
            INNER JOIN rol r ON ur.rol_id = r.rol_id
            WHERE ur.usuario_id = :usuario_id
              AND ur.cliente_id = :cliente_id
              AND ur.es_activo = 1
              AND r.es_activo = 1
              AND r.es_admin_cliente = 1
              AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)
            """
        ).bindparams(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            empresa_id=empresa_id,
        )
    return text(
        """
        SELECT COUNT(*) AS admin_cliente_count
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = :usuario_id
          AND ur.cliente_id = :cliente_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND r.es_admin_cliente = 1
        """
    ).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)


def text_admin_cliente_count_engine_scoped(
    *,
    usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
):
    if empresa_id is not None:
        return text(
            """
            SELECT COUNT(*) AS admin_cliente_count
            FROM usuario_rol ur
            INNER JOIN rol r ON ur.rol_id = r.rol_id
            WHERE ur.usuario_id = :usuario_id
              AND ur.es_activo = 1
              AND r.es_activo = 1
              AND r.es_admin_cliente = 1
              AND (ur.empresa_id IS NULL OR ur.empresa_id = :empresa_id)
            """
        ).bindparams(usuario_id=usuario_id, empresa_id=empresa_id)
    return text(
        """
        SELECT COUNT(*) AS admin_cliente_count
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = :usuario_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND r.es_admin_cliente = 1
        """
    ).bindparams(usuario_id=usuario_id)


def text_platform_superadmin_count(
    *,
    usuario_id: UUID,
    system_cliente_id: UUID,
):
    return text(
        """
        SELECT COUNT(*) AS super_admin_count
        FROM usuario_rol ur
        INNER JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = :usuario_id
          AND ur.cliente_id = :cliente_id
          AND ur.es_activo = 1
          AND r.es_activo = 1
          AND r.codigo_rol = 'SUPER_ADMIN'
          AND r.nivel_acceso = 5
        """
    ).bindparams(usuario_id=usuario_id, cliente_id=system_cliente_id)


__all__ = [
    "select_admin_tenant_wide_count_engine_scoped",
    "select_admin_tenant_wide_count_row_scoped",
    "select_distinct_empresa_ids_engine_scoped",
    "select_distinct_empresa_ids_row_scoped",
    "select_user_password_policy_engine_scoped",
    "select_user_password_policy_row_scoped",
    "select_user_role_names_engine_scoped",
    "select_user_role_names_row_scoped",
    "select_user_roles_for_auth_engine_scoped",
    "select_user_roles_for_auth_row_scoped",
    "text_admin_cliente_count_engine_scoped",
    "text_admin_cliente_count_row_scoped",
    "text_platform_superadmin_count",
    "text_user_empresa_default_engine_scoped",
    "text_user_empresa_default_row_scoped",
]
