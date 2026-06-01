"""
OwnerSyncService v1.0 — sincroniza rol_permiso + rol_menu_permiso para ADMIN_TENANT.

Modelo Owner:
  cliente_modulo     → contrato comercial
  rol_menu_permiso   → visibilidad UI
  rol_permiso        → permisos API
"""
from __future__ import annotations

import logging
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.owner_sync_constants import (
    ADMIN_ROL_CODIGO,
    OWNER_SYNC_ADMIN_ROLE_NOT_FOUND,
    OWNER_SYNC_MODULE_NOT_CONTRACTED,
    OWNER_SYNC_MODULE_NOT_FOUND,
    OWNER_SYNC_ZERO_GRANTS,
)
from app.modules.tenant.application.services.owner_sync_result import (
    OwnerSyncBatchResult,
    OwnerSyncDeactivateResult,
    OwnerSyncResult,
)

logger = logging.getLogger(__name__)

_SYS_ADMIN_MENU_FILTER = """
  AND mm.codigo LIKE N'SYS_ADMIN.TENANT.%'
  AND mm.codigo NOT LIKE N'SYS_ADMIN.PLATFORM.%'
  AND mm.codigo NOT LIKE N'SYS_ADMIN.CATALOGOS.%'
"""


class OwnerSyncService:
    """Sincroniza grants owner (ADMIN_TENANT) al activar módulos comerciales."""

    @staticmethod
    async def resolve_admin_tenant_rol_id(
        session: AsyncSession,
        *,
        cliente_id: UUID,
    ) -> UUID:
        sql = text("""
            SELECT rol_id FROM rol
            WHERE cliente_id = :cliente_id
              AND codigo_rol = :codigo_rol
              AND es_activo = 1
        """).bindparams(cliente_id=cliente_id, codigo_rol=ADMIN_ROL_CODIGO)
        row = (await session.execute(sql)).fetchone()
        if not row:
            raise DatabaseError(
                detail="Rol ADMIN_TENANT no encontrado para OwnerSync.",
                internal_code=OWNER_SYNC_ADMIN_ROLE_NOT_FOUND,
            )
        rid = row[0]
        return rid if isinstance(rid, UUID) else UUID(str(rid))

    @staticmethod
    async def sync_modules_for_owner(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        modulos_codigo: Sequence[str],
        admin_rol_id: UUID | None = None,
    ) -> OwnerSyncBatchResult:
        resolved_admin = admin_rol_id or await OwnerSyncService.resolve_admin_tenant_rol_id(
            session, cliente_id=cliente_id
        )
        results: List[OwnerSyncResult] = []
        for codigo in modulos_codigo:
            code = (codigo or "").strip().upper()
            if not code:
                continue
            result = await OwnerSyncService.sync_module_for_owner(
                session,
                cliente_id=cliente_id,
                modulo_codigo=code,
                admin_rol_id=resolved_admin,
            )
            results.append(result)
        return OwnerSyncBatchResult(cliente_id=cliente_id, results=results)

    @staticmethod
    async def sync_module_for_owner(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        modulo_codigo: str,
        admin_rol_id: UUID | None = None,
    ) -> OwnerSyncResult:
        code = modulo_codigo.strip().upper()
        admin_id = admin_rol_id or await OwnerSyncService.resolve_admin_tenant_rol_id(
            session, cliente_id=cliente_id
        )

        await OwnerSyncService._assert_module_contracted(session, cliente_id=cliente_id, modulo_codigo=code)
        await OwnerSyncService._assert_module_catalog(session, modulo_codigo=code)

        rp_inserted = await OwnerSyncService._sync_rol_permiso_module(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_id,
            modulo_codigo=code,
        )
        rp_total = await OwnerSyncService._count_rol_permiso_module(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_id,
            modulo_codigo=code,
        )

        rmp_inserted = await OwnerSyncService._sync_rol_menu_permiso_module(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_id,
            modulo_codigo=code,
        )
        rmp_total = await OwnerSyncService._count_rol_menu_permiso_module(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_id,
            modulo_codigo=code,
        )

        if rp_total == 0 and rmp_total == 0:
            raise DatabaseError(
                detail=f"OwnerSync sin grants para módulo {code} (catálogo vacío o inconsistente).",
                internal_code=OWNER_SYNC_ZERO_GRANTS,
            )

        menu_sample = await OwnerSyncService._sample_menu_codigos(
            session, cliente_id=cliente_id, admin_rol_id=admin_id, modulo_codigo=code
        )
        perm_sample = await OwnerSyncService._sample_permiso_codigos(
            session, cliente_id=cliente_id, admin_rol_id=admin_id, modulo_codigo=code
        )

        logger.info(
            "OwnerSync cliente=%s modulo=%s rp_inserted=%s rmp_inserted=%s rp_total=%s rmp_total=%s",
            cliente_id,
            code,
            rp_inserted,
            rmp_inserted,
            rp_total,
            rmp_total,
        )

        return OwnerSyncResult(
            cliente_id=cliente_id,
            modulo_codigo=code,
            admin_rol_id=admin_id,
            rol_permiso_inserted=rp_inserted,
            rol_permiso_total_module=rp_total,
            rol_menu_permiso_inserted=rmp_inserted,
            rol_menu_permiso_total_module=rmp_total,
            menu_codigos_sample=menu_sample[:10],
            permiso_codigos_sample=perm_sample[:10],
        )

    @staticmethod
    async def on_module_deactivated(
        *,
        cliente_id: UUID,
        modulo_codigo: str,
    ) -> OwnerSyncDeactivateResult:
        """v1.0 runtime-only: sin DELETE en RBAC; invalidación cache post-commit."""
        cache_invalidated = False
        try:
            from app.core.authorization.permission_resolver import get_permission_resolver

            get_permission_resolver().invalidate_for_tenant(cliente_id)
            cache_invalidated = True
        except Exception as exc:
            logger.debug("OwnerSync deactivate cache invalidation (no bloqueante): %s", exc)
        return OwnerSyncDeactivateResult(
            cliente_id=cliente_id,
            modulo_codigo=modulo_codigo.strip().upper(),
            runtime_only=True,
            cache_invalidated=cache_invalidated,
        )

    @staticmethod
    async def _assert_module_catalog(session: AsyncSession, *, modulo_codigo: str) -> None:
        sql = text("""
            SELECT 1 FROM modulo
            WHERE codigo = :modulo_codigo AND es_activo = 1
        """).bindparams(modulo_codigo=modulo_codigo)
        row = (await session.execute(sql)).fetchone()
        if not row:
            raise DatabaseError(
                detail=f"Módulo {modulo_codigo} no encontrado en catálogo.",
                internal_code=OWNER_SYNC_MODULE_NOT_FOUND,
            )

    @staticmethod
    async def _assert_module_contracted(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        modulo_codigo: str,
    ) -> None:
        sql = text("""
            SELECT 1
            FROM cliente_modulo cm
            INNER JOIN modulo m ON m.modulo_id = cm.modulo_id
            WHERE cm.cliente_id = :cliente_id
              AND m.codigo = :modulo_codigo
              AND cm.esta_activo = 1
              AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > GETDATE())
        """).bindparams(cliente_id=cliente_id, modulo_codigo=modulo_codigo)
        row = (await session.execute(sql)).fetchone()
        if not row:
            raise DatabaseError(
                detail=f"Módulo {modulo_codigo} no contratado/activo para el tenant.",
                internal_code=OWNER_SYNC_MODULE_NOT_CONTRACTED,
            )

    @staticmethod
    async def _sync_rol_permiso_module(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> int:
        count_before = await OwnerSyncService._count_rol_permiso_module(
            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id, modulo_codigo=modulo_codigo
        )
        sql = text("""
            INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
            SELECT NEWID(), :cliente_id, :admin_rol_id, p.permiso_id, GETDATE()
            FROM permiso p
            INNER JOIN modulo m ON m.modulo_id = p.modulo_id
            WHERE m.codigo = :modulo_codigo
              AND m.es_activo = 1
              AND p.es_activo = 1
              AND NOT EXISTS (
                    SELECT 1 FROM rol_permiso rp
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :admin_rol_id
                      AND rp.permiso_id = p.permiso_id
              )
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        await session.execute(sql)
        count_after = await OwnerSyncService._count_rol_permiso_module(
            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id, modulo_codigo=modulo_codigo
        )
        return max(0, count_after - count_before)

    @staticmethod
    async def _count_rol_permiso_module(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> int:
        sql = text("""
            SELECT COUNT(*) AS total
            FROM rol_permiso rp
            INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
            INNER JOIN modulo m ON m.modulo_id = p.modulo_id
            WHERE rp.cliente_id = :cliente_id
              AND rp.rol_id = :admin_rol_id
              AND m.codigo = :modulo_codigo
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        row = (await session.execute(sql)).fetchone()
        return int(row[0] if row else 0)

    @staticmethod
    async def _sync_rol_menu_permiso_module(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> int:
        count_before = await OwnerSyncService._count_rol_menu_permiso_module(
            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id, modulo_codigo=modulo_codigo
        )
        sys_admin_extra = _SYS_ADMIN_MENU_FILTER if modulo_codigo == "SYS_ADMIN" else ""
        sql = text(f"""
            INSERT INTO rol_menu_permiso (
                permiso_id, cliente_id, rol_id, menu_id, empresa_id,
                puede_ver, puede_crear, puede_editar, puede_eliminar,
                puede_exportar, puede_imprimir, puede_aprobar
            )
            SELECT
                NEWID(), :cliente_id, :admin_rol_id, mm.menu_id, NULL,
                1, 1, 1, 1, 1, 1, 0
            FROM modulo_menu mm
            INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
            INNER JOIN cliente_modulo cm
                ON cm.modulo_id = m.modulo_id
               AND cm.cliente_id = :cliente_id
               AND cm.esta_activo = 1
               AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > GETDATE())
            WHERE m.codigo = :modulo_codigo
              AND m.es_activo = 1
              AND mm.es_activo = 1
              AND mm.es_visible = 1
              AND (mm.cliente_id IS NULL OR mm.cliente_id = :cliente_id)
              {sys_admin_extra}
              AND NOT EXISTS (
                    SELECT 1 FROM rol_menu_permiso rmp
                    WHERE rmp.cliente_id = :cliente_id
                      AND rmp.rol_id = :admin_rol_id
                      AND rmp.menu_id = mm.menu_id
                      AND rmp.empresa_id IS NULL
              )
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        await session.execute(sql)
        count_after = await OwnerSyncService._count_rol_menu_permiso_module(
            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id, modulo_codigo=modulo_codigo
        )
        return max(0, count_after - count_before)

    @staticmethod
    async def _count_rol_menu_permiso_module(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> int:
        sys_admin_extra = _SYS_ADMIN_MENU_FILTER if modulo_codigo == "SYS_ADMIN" else ""
        sql = text(f"""
            SELECT COUNT(*) AS total
            FROM rol_menu_permiso rmp
            INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id
            INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
            WHERE rmp.cliente_id = :cliente_id
              AND rmp.rol_id = :admin_rol_id
              AND rmp.empresa_id IS NULL
              AND m.codigo = :modulo_codigo
              {sys_admin_extra}
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        row = (await session.execute(sql)).fetchone()
        return int(row[0] if row else 0)

    @staticmethod
    async def _sample_menu_codigos(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> List[str]:
        sys_admin_extra = _SYS_ADMIN_MENU_FILTER if modulo_codigo == "SYS_ADMIN" else ""
        sql = text(f"""
            SELECT mm.codigo
            FROM rol_menu_permiso rmp
            INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id
            INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
            WHERE rmp.cliente_id = :cliente_id
              AND rmp.rol_id = :admin_rol_id
              AND rmp.empresa_id IS NULL
              AND m.codigo = :modulo_codigo
              {sys_admin_extra}
            ORDER BY mm.codigo
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        rows = (await session.execute(sql)).fetchall()
        return [str(r[0]) for r in rows if r and r[0]]

    @staticmethod
    async def _sample_permiso_codigos(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        admin_rol_id: UUID,
        modulo_codigo: str,
    ) -> List[str]:
        sql = text("""
            SELECT p.codigo
            FROM rol_permiso rp
            INNER JOIN permiso p ON p.permiso_id = rp.permiso_id
            INNER JOIN modulo m ON m.modulo_id = p.modulo_id
            WHERE rp.cliente_id = :cliente_id
              AND rp.rol_id = :admin_rol_id
              AND m.codigo = :modulo_codigo
              AND p.es_activo = 1
            ORDER BY p.codigo
        """).bindparams(
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            modulo_codigo=modulo_codigo,
        )
        rows = (await session.execute(sql)).fetchall()
        return [str(r[0]) for r in rows if r and r[0]]

    @staticmethod
    async def count_expected_owner_menu_grants(
        session: AsyncSession,
        *,
        cliente_id: UUID,
    ) -> int:
        """Menús elegibles para owner según cliente_modulo activo (trial ~18)."""
        sql = text(f"""
            SELECT COUNT(DISTINCT mm.menu_id) AS total
            FROM modulo_menu mm
            INNER JOIN modulo m ON m.modulo_id = mm.modulo_id
            INNER JOIN cliente_modulo cm ON cm.modulo_id = m.modulo_id
                AND cm.cliente_id = :cliente_id
                AND cm.esta_activo = 1
            WHERE m.es_activo = 1
              AND mm.es_activo = 1
              AND mm.es_visible = 1
              AND (mm.cliente_id IS NULL OR mm.cliente_id = :cliente_id)
              AND (
                    m.codigo NOT IN ('SYS_ADMIN')
                    OR (
                        mm.codigo LIKE N'SYS_ADMIN.TENANT.%'
                        AND mm.codigo NOT LIKE N'SYS_ADMIN.PLATFORM.%'
                        AND mm.codigo NOT LIKE N'SYS_ADMIN.CATALOGOS.%'
                    )
              )
        """).bindparams(cliente_id=cliente_id)
        row = (await session.execute(sql)).fetchone()
        return int(row[0] if row else 0)
