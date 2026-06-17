"""
Audit snapshot — bootstrap plataforma (identidad + RBAC).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.tenant.application.services.platform_bootstrap_constants import (
    MIN_RP_COUNT_READY,
)
from app.modules.tenant.application.services.platform_rbac_bootstrap_service import (
    ADMIN_PLATFORM_ACCESS,
    CORE_APP_ACCEDER,
    PLATFORM_ADMIN_ROL_CODIGO,
    PlatformRbacBootstrapService,
)


async def audit_platform_ready(session: AsyncSession) -> Dict[str, Any]:
    """Estado completo plataforma: identidad + RBAC."""
    cid = PlatformRbacBootstrapService.resolve_platform_cliente_id()
    cid_str = str(cid)

    cliente_row = (
        await session.execute(
            text("""
                SELECT cliente_id, codigo_cliente, subdominio, es_activo
                FROM cliente WHERE cliente_id = :cid
            """).bindparams(cid=cid_str)
        )
    ).first()

    rol_row = (
        await session.execute(
            text("""
                SELECT rol_id FROM rol
                WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
            """).bindparams(cid=cid_str, codigo=PLATFORM_ADMIN_ROL_CODIGO)
        )
    ).first()
    admin_rol_id: Optional[str] = str(rol_row[0]) if rol_row else None

    usuario_row = None
    usuario_rol_ok = False

    usuario_row = (
        await session.execute(
            text("""
                SELECT usuario_id, nombre_usuario, es_activo
                FROM usuario
                WHERE cliente_id = :cid AND nombre_usuario = :username AND es_eliminado = 0
            """).bindparams(cid=cid_str, username=settings.SUPERADMIN_USERNAME)
        )
    ).first()

    if usuario_row and admin_rol_id:
        ur = (
            await session.execute(
                text("""
                    SELECT 1 FROM usuario_rol ur
                    WHERE ur.usuario_id = :uid AND ur.rol_id = :rid
                      AND ur.cliente_id = :cid AND ur.es_activo = 1
                      AND ur.empresa_id IS NULL
                """).bindparams(
                    uid=str(usuario_row[0]),
                    rid=admin_rol_id,
                    cid=cid_str,
                )
            )
        ).first()
        usuario_rol_ok = ur is not None

    auth_config_row = (
        await session.execute(
            text("SELECT 1 FROM cliente_auth_config WHERE cliente_id = :cid").bindparams(
                cid=cid_str
            )
        )
    ).first()

    rp_count = 0
    has_core_rp = False
    has_tenant_cliente_crear = False
    if admin_rol_id:
        rp_count = int(
            (
                await session.execute(
                    text("""
                        SELECT COUNT(*) FROM rol_permiso
                        WHERE cliente_id = :cid AND rol_id = :rid
                    """).bindparams(cid=cid_str, rid=admin_rol_id)
                )
            ).scalar()
            or 0
        )
        has_core_rp = (
            await session.execute(
                text("""
                    SELECT 1 FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
                    WHERE rp.cliente_id = :cid AND rp.rol_id = :rid AND p.codigo = :core
                """).bindparams(cid=cid_str, rid=admin_rol_id, core=CORE_APP_ACCEDER)
            )
        ).first() is not None
        has_tenant_cliente_crear = (
            await session.execute(
                text("""
                    SELECT 1 FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                    WHERE rp.cliente_id = :cid AND rp.rol_id = :rid
                      AND p.codigo = 'tenant.cliente.crear'
                """).bindparams(cid=cid_str, rid=admin_rol_id)
            )
        ).first() is not None

    cm_sysadmin = int(
        (
            await session.execute(
                text("""
                    SELECT COUNT(*) FROM cliente_modulo cm
                    INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
                    WHERE cm.cliente_id = :cid AND cm.esta_activo = 1
                      AND m.codigo = 'SYS_ADMIN' AND m.es_activo = 1
                """).bindparams(cid=cid_str)
            )
        ).scalar()
        or 0
    )

    perm_platform = (
        await session.execute(
            text("SELECT es_activo FROM permiso WHERE codigo = :c").bindparams(
                c=ADMIN_PLATFORM_ACCESS
            )
        )
    ).first()

    needs_identity = not (
        cliente_row
        and cliente_row[3]
        and admin_rol_id
        and usuario_row
        and usuario_row[2]
        and usuario_rol_ok
    )
    needs_rbac = (
        cm_sysadmin < 1
        or rp_count < MIN_RP_COUNT_READY
        or not (perm_platform and perm_platform[0])
        or not has_core_rp
        or not has_tenant_cliente_crear
    )
    needs_bootstrap = needs_identity or needs_rbac

    return {
        "cliente_id": cid_str,
        "cliente_exists": cliente_row is not None,
        "cliente_activo": bool(cliente_row and cliente_row[3]),
        "codigo_cliente": str(cliente_row[1]) if cliente_row else None,
        "subdominio": str(cliente_row[2]) if cliente_row else None,
        "admin_platform_rol_id": admin_rol_id,
        "admin_platform_rol_exists": admin_rol_id is not None,
        "superadmin_usuario_exists": usuario_row is not None,
        "superadmin_usuario_activo": bool(usuario_row and usuario_row[2]),
        "superadmin_usuario_id": str(usuario_row[0]) if usuario_row else None,
        "usuario_rol_admin_platform": usuario_rol_ok,
        "cliente_auth_config_exists": auth_config_row is not None,
        "rol_permiso_admin_platform_count": rp_count,
        "cliente_modulo_sysadmin_count": cm_sysadmin,
        "admin_platform_access_es_activo": bool(perm_platform and perm_platform[0]),
        "has_core_app_acceder_in_rol_permiso": has_core_rp,
        "has_tenant_cliente_crear": has_tenant_cliente_crear,
        "needs_identity": needs_identity,
        "needs_rbac": needs_rbac,
        "needs_bootstrap": needs_bootstrap,
        # Compat repair_platform_rbac
        "needs_repair": needs_rbac,
    }
