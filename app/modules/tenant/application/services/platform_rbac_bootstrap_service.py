"""
Bootstrap RBAC para cliente plataforma (SUPERADMIN / QA D010).

Cierra el gap: D010 crea roles ADMIN_PLATFORM pero S020 asignó rol_permiso antes
de que existieran esos roles; permission_sync desactiva admin.platform.access.

No sustituye onboarding tenant (ADMIN_TENANT).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.onboarding_rbac_service import (
    OnboardingRbacService,
)

logger = logging.getLogger(__name__)

CORE_APP_ACCEDER = "core.app.acceder"
ADMIN_PLATFORM_ACCESS = "admin.platform.access"
ADMIN_TENANT_ACCESS = "admin.tenant.access"
PLATFORM_ADMIN_ROL_CODIGO = "ADMIN_PLATFORM"
PLATFORM_MODULOS: tuple[str, ...] = ("SYS_ADMIN",)

# Permisos seed de menú admin que sync no debe dejar inactivos tras repair.
PLATFORM_REACTIVATE_CODIGOS: tuple[str, ...] = (
    ADMIN_PLATFORM_ACCESS,
    ADMIN_TENANT_ACCESS,
)


class PlatformRbacBootstrapService:
    """Activa SYS_ADMIN en cliente plataforma y grants ADMIN_PLATFORM (idempotente)."""

    @staticmethod
    def resolve_platform_cliente_id() -> UUID:
        raw = (getattr(settings, "SUPERADMIN_CLIENTE_ID", None) or "").strip()
        if not raw:
            raise DatabaseError(
                detail="SUPERADMIN_CLIENTE_ID no configurado.",
                internal_code="PLATFORM_CLIENTE_ID_MISSING",
            )
        return UUID(str(raw))

    @staticmethod
    async def bootstrap_platform_rbac(
        session: AsyncSession,
        *,
        cliente_id: Optional[UUID] = None,
        activado_por_usuario_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        cid = cliente_id or PlatformRbacBootstrapService.resolve_platform_cliente_id()
        await OnboardingRbacService._validar_catalogo_permiso(session)

        reactivated = await PlatformRbacBootstrapService._reactivar_permisos_menu_admin(
            session
        )
        modulos = await OnboardingRbacService.activar_modulos_base_cliente(
            session,
            cliente_id=cid,
            activado_por_usuario_id=activado_por_usuario_id,
            modulos_codigo=PLATFORM_MODULOS,
        )
        admin_rol_id = await PlatformRbacBootstrapService._resolve_admin_platform_rol_id(
            session, cliente_id=cid
        )
        grants = await PlatformRbacBootstrapService.asignar_permisos_admin_platform(
            session,
            cliente_id=cid,
            admin_rol_id=admin_rol_id,
        )
        logger.info(
            "Platform RBAC bootstrap cliente=%s modulos=%s rol_permiso_insertados=%s reactivated=%s",
            cid,
            modulos,
            grants.get("inserted", 0),
            reactivated,
        )
        return {
            "cliente_id": str(cid),
            "modulos": modulos,
            "grants": grants,
            "reactivated_permisos": reactivated,
        }

    @staticmethod
    async def _reactivar_permisos_menu_admin(session: AsyncSession) -> int:
        placeholders = ", ".join(f":c{i}" for i in range(len(PLATFORM_REACTIVATE_CODIGOS)))
        bind = {f"c{i}": PLATFORM_REACTIVATE_CODIGOS[i] for i in range(len(PLATFORM_REACTIVATE_CODIGOS))}
        sql = text(f"""
            UPDATE permiso
            SET es_activo = 1
            WHERE codigo IN ({placeholders})
              AND es_activo = 0
        """).bindparams(**bind)
        result = await session.execute(sql)
        return int(result.rowcount or 0)

    @staticmethod
    async def _resolve_admin_platform_rol_id(
        session: AsyncSession, *, cliente_id: UUID
    ) -> UUID:
        sql = text("""
            SELECT rol_id FROM rol
            WHERE cliente_id = :cliente_id
              AND codigo_rol = :codigo_rol
              AND es_activo = 1
        """).bindparams(cliente_id=cliente_id, codigo_rol=PLATFORM_ADMIN_ROL_CODIGO)
        row = (await session.execute(sql)).fetchone()
        if not row:
            raise DatabaseError(
                detail=(
                    f"Rol {PLATFORM_ADMIN_ROL_CODIGO} no encontrado para cliente plataforma. "
                    "Ejecute D010 o cree el rol antes del repair."
                ),
                internal_code="PLATFORM_ADMIN_ROLE_NOT_FOUND",
            )
        rid = row[0]
        return rid if isinstance(rid, UUID) else UUID(str(rid))

    @staticmethod
    async def asignar_permisos_admin_platform(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
    ) -> Dict[str, Any]:
        """
        Grants ADMIN_PLATFORM: core, admin.platform.access, admin.usuario.*,
        admin.rol.*, tenant.*, modulos.* (incluye tenant.cliente.crear en plataforma).
        """
        sql_grant = text("""
            INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
            SELECT NEWID(), :cliente_id, :admin_rol_id, p.permiso_id, GETDATE()
            FROM permiso p
            WHERE p.es_activo = 1
              AND (
                    p.codigo = :core_app_acceder
                 OR p.codigo = :admin_platform_access
                 OR p.codigo LIKE 'admin.usuario.%'
                 OR p.codigo LIKE 'admin.rol.%'
                 OR p.codigo LIKE 'tenant.%'
                 OR p.codigo LIKE 'modulos.%'
              )
              AND NOT EXISTS (
                    SELECT 1 FROM rol_permiso rp
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :admin_rol_id
                      AND rp.permiso_id = p.permiso_id
              )
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            core_app_acceder=CORE_APP_ACCEDER,
            admin_platform_access=ADMIN_PLATFORM_ACCESS,
        )

        sql_count = text("""
            SELECT COUNT(*) FROM rol_permiso
            WHERE cliente_id = :cliente_id AND rol_id = :admin_rol_id
        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)

        before = int(((await session.execute(sql_count)).fetchone() or [0])[0])
        await session.execute(sql_grant)
        after = int(((await session.execute(sql_count)).fetchone() or [0])[0])

        sql_codes = text("""
            SELECT p.codigo FROM rol_permiso rp
            INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
            WHERE rp.cliente_id = :cliente_id AND rp.rol_id = :admin_rol_id
            ORDER BY p.codigo
        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)
        codigos = [str(r[0]) for r in (await session.execute(sql_codes)).fetchall()]

        return {
            "inserted": max(0, after - before),
            "total": after,
            "codigos": codigos,
            "has_admin_platform_access": ADMIN_PLATFORM_ACCESS in codigos,
            "has_core_app_acceder": CORE_APP_ACCEDER in codigos,
            "has_tenant_cliente_crear": "tenant.cliente.crear" in codigos,
        }
