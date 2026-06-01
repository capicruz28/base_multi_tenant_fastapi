"""
T3 — USER_STANDARD: aplica bundle a USER_TENANT.

Idempotente:
- inserta rol_permiso faltantes según catálogo permiso
- inserta rol_menu_permiso faltantes por menu_id (PK permiso_id)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenant.application.services.user_standard_constants import (
    USER_ROL_CODIGO,
    USER_STANDARD_MENU_GRANTS,
    USER_STANDARD_MISSING_PERMISO,
    USER_STANDARD_PERMISSION_CODIGOS,
    USER_STANDARD_ROLE_NOT_FOUND,
)

logger = logging.getLogger(__name__)


def _bind_codes(codes: tuple[str, ...]) -> tuple[str, Dict[str, Any]]:
    placeholders = ", ".join(f":pc{i}" for i in range(len(codes)))
    bind = {f"pc{i}": codes[i] for i in range(len(codes))}
    return placeholders, bind


class UserStandardService:
    @staticmethod
    async def apply_to_user_role(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        user_rol_id: UUID,
    ) -> Dict[str, Any]:
        rp = await UserStandardService._apply_rol_permiso(
            session, cliente_id=cliente_id, rol_id=user_rol_id
        )
        rmp = await UserStandardService._apply_rol_menu_permiso(
            session, cliente_id=cliente_id, rol_id=user_rol_id
        )
        if (rp.get("inserted", 0) or 0) > 0 or (rmp.get("inserted", 0) or 0) > 0:
            UserStandardService._invalidate_tenant_cache(cliente_id)
        return {
            "cliente_id": str(cliente_id),
            "rol_id": str(user_rol_id),
            "bundle": "USER_STANDARD",
            "rol_permiso": rp,
            "rol_menu_permiso": rmp,
            "expected_permiso_codigos": list(USER_STANDARD_PERMISSION_CODIGOS),
            "expected_menu_grants": len(USER_STANDARD_MENU_GRANTS),
        }

    @staticmethod
    async def resolve_user_rol_id(
        session: AsyncSession,
        *,
        cliente_id: UUID,
    ) -> Optional[UUID]:
        row = (
            await session.execute(
                text(
                    """
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cliente_id
                      AND codigo_rol = :codigo_rol
                      AND es_activo = 1
                    """
                ).bindparams(cliente_id=cliente_id, codigo_rol=USER_ROL_CODIGO)
            )
        ).fetchone()
        if not row:
            return None
        return row[0] if isinstance(row[0], UUID) else UUID(str(row[0]))

    @staticmethod
    async def ensure_for_user_role(
        cliente_id: UUID,
        rol_id: UUID,
        codigo_rol: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Hook assign rol: asegura USER_STANDARD si el rol asignado es USER_TENANT.
        Usa conexión ADMIN independiente (fuera de transacción del endpoint).
        """
        if not codigo_rol or codigo_rol != USER_ROL_CODIGO:
            return None
        from app.infrastructure.database.connection_async import (
            DatabaseConnection,
            get_db_connection,
        )

        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await UserStandardService.apply_to_user_role(
                session, cliente_id=cliente_id, user_rol_id=rol_id
            )
            await session.commit()
        return result

    @staticmethod
    async def _apply_rol_permiso(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
    ) -> Dict[str, Any]:
        codes_ph, bind = _bind_codes(USER_STANDARD_PERMISSION_CODIGOS)
        sql_missing = text(
            f"""
            SELECT p.codigo
            FROM permiso p
            WHERE p.es_activo = 1
              AND p.codigo IN ({codes_ph})
              AND NOT EXISTS (
                    SELECT 1 FROM rol_permiso rp
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :rol_id
                      AND rp.permiso_id = p.permiso_id
              )
            ORDER BY p.codigo
            """
        ).bindparams(**bind, cliente_id=cliente_id, rol_id=rol_id)
        rows = (await session.execute(sql_missing)).fetchall()
        missing = [str(r[0]) for r in rows if r and r[0]]

        inserted = 0
        if missing:
            codes_ph2, bind2 = _bind_codes(tuple(missing))
            sql_insert = text(
                f"""
                INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
                SELECT NEWID(), :cliente_id, :rol_id, p.permiso_id, GETDATE()
                FROM permiso p
                WHERE p.es_activo = 1
                  AND p.codigo IN ({codes_ph2})
                  AND NOT EXISTS (
                        SELECT 1 FROM rol_permiso rp
                        WHERE rp.cliente_id = :cliente_id
                          AND rp.rol_id = :rol_id
                          AND rp.permiso_id = p.permiso_id
                  )
                """
            ).bindparams(**bind2, cliente_id=cliente_id, rol_id=rol_id)
            before = await UserStandardService._count_role_permiso(
                session, cliente_id=cliente_id, rol_id=rol_id
            )
            await session.execute(sql_insert)
            after = await UserStandardService._count_role_permiso(
                session, cliente_id=cliente_id, rol_id=rol_id
            )
            inserted = max(0, after - before)

        present = await UserStandardService._list_present_permiso_codigos(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        return {
            "inserted": inserted,
            "expected": len(USER_STANDARD_PERMISSION_CODIGOS),
            "present_count": len(present),
            "missing_count": max(0, len(USER_STANDARD_PERMISSION_CODIGOS) - len(present)),
            "missing_reason": USER_STANDARD_MISSING_PERMISO if missing else None,
        }

    @staticmethod
    async def _apply_rol_menu_permiso(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
    ) -> Dict[str, Any]:
        inserted = 0
        checked = 0
        for menu_id, flags in USER_STANDARD_MENU_GRANTS:
            checked += 1
            sql = text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM rol_menu_permiso
                    WHERE cliente_id = :cliente_id
                      AND rol_id = :rol_id
                      AND menu_id = :menu_id
                )
                INSERT INTO rol_menu_permiso (
                    permiso_id, cliente_id, rol_id, menu_id,
                    puede_ver, puede_crear, puede_editar, puede_eliminar,
                    puede_exportar, puede_imprimir, puede_aprobar,
                    fecha_creacion
                )
                VALUES (
                    NEWID(), :cliente_id, :rol_id, :menu_id,
                    :puede_ver, :puede_crear, :puede_editar, :puede_eliminar,
                    :puede_exportar, :puede_imprimir, :puede_aprobar,
                    GETDATE()
                )
                """
            ).bindparams(
                cliente_id=cliente_id,
                rol_id=rol_id,
                menu_id=menu_id,
                puede_ver=int(flags.get("ver", 0)),
                puede_crear=int(flags.get("crear", 0)),
                puede_editar=int(flags.get("editar", 0)),
                puede_eliminar=int(flags.get("eliminar", 0)),
                puede_exportar=int(flags.get("exportar", 0)),
                puede_imprimir=int(flags.get("imprimir", 0)),
                puede_aprobar=int(flags.get("aprobar", 0)),
            )
            before = await UserStandardService._count_role_menu_permiso(
                session, cliente_id=cliente_id, rol_id=rol_id
            )
            await session.execute(sql)
            after = await UserStandardService._count_role_menu_permiso(
                session, cliente_id=cliente_id, rol_id=rol_id
            )
            inserted += max(0, after - before)

        total = await UserStandardService._count_role_menu_permiso(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        return {
            "checked": checked,
            "inserted": inserted,
            "total": total,
            "expected": len(USER_STANDARD_MENU_GRANTS),
        }

    @staticmethod
    async def _count_role_permiso(
        session: AsyncSession, *, cliente_id: UUID, rol_id: UUID
    ) -> int:
        row = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM rol_permiso
                    WHERE cliente_id = :cliente_id AND rol_id = :rol_id
                    """
                ).bindparams(cliente_id=cliente_id, rol_id=rol_id)
            )
        ).fetchone()
        return int(row[0] if row else 0)

    @staticmethod
    async def _list_present_permiso_codigos(
        session: AsyncSession, *, cliente_id: UUID, rol_id: UUID
    ) -> List[str]:
        codes_ph, bind = _bind_codes(USER_STANDARD_PERMISSION_CODIGOS)
        rows = (
            await session.execute(
                text(
                    f"""
                    SELECT DISTINCT p.codigo
                    FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :rol_id
                      AND p.codigo IN ({codes_ph})
                    ORDER BY p.codigo
                    """
                ).bindparams(**bind, cliente_id=cliente_id, rol_id=rol_id)
            )
        ).fetchall()
        return [str(r[0]) for r in rows if r and r[0]]

    @staticmethod
    async def _count_role_menu_permiso(
        session: AsyncSession, *, cliente_id: UUID, rol_id: UUID
    ) -> int:
        row = (
            await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM rol_menu_permiso
                    WHERE cliente_id = :cliente_id AND rol_id = :rol_id
                    """
                ).bindparams(cliente_id=cliente_id, rol_id=rol_id)
            )
        ).fetchone()
        return int(row[0] if row else 0)

    @staticmethod
    def _invalidate_tenant_cache(cliente_id: UUID) -> None:
        try:
            from app.core.authorization.permission_resolver import get_permission_resolver

            get_permission_resolver().invalidate_for_tenant(cliente_id)
        except Exception as e:
            logger.debug("Permission resolver invalidation (tenant): %s", e)

