"""
T1 — Provisiona bundle BASE_OPERATIVE en MANAGER_TENANT y USER_TENANT.

Idempotente: INSERT rol_permiso solo para permisos faltantes.
No modifica ADMIN_TENANT (OWNER_FULL).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.base_operative_constants import (
    BASE_OPERATIVE_MISSING_PERMISO,
    BASE_OPERATIVE_PERMISSION_CODIGOS,
    BASE_OPERATIVE_ROLE_NOT_FOUND,
    OPERATIVE_ROLE_CODIGOS,
)

logger = logging.getLogger(__name__)


def _bind_codes(codes: tuple[str, ...]) -> tuple[str, Dict[str, Any]]:
    placeholders = ", ".join(f":pc{i}" for i in range(len(codes)))
    bind = {f"pc{i}": codes[i] for i in range(len(codes))}
    return placeholders, bind


class BaseOperativeService:
    """Grants BASE_OPERATIVE (rol_permiso) para roles operativos."""

    @staticmethod
    async def apply_to_operative_roles(
        session: AsyncSession,
        *,
        cliente_id: UUID,
    ) -> Dict[str, Any]:
        """Aplica BASE_OPERATIVE a MANAGER_TENANT y USER_TENANT del tenant."""
        role_results: List[Dict[str, Any]] = []
        total_inserted = 0
        for codigo_rol in OPERATIVE_ROLE_CODIGOS:
            rol_id = await BaseOperativeService._resolve_rol_id(
                session, cliente_id=cliente_id, codigo_rol=codigo_rol
            )
            if rol_id is None:
                logger.warning(
                    "BASE_OPERATIVE: rol %s no encontrado cliente=%s",
                    codigo_rol,
                    cliente_id,
                )
                role_results.append(
                    {
                        "codigo_rol": codigo_rol,
                        "rol_id": None,
                        "skipped": True,
                        "reason": BASE_OPERATIVE_ROLE_NOT_FOUND,
                        "inserted": 0,
                    }
                )
                continue
            one = await BaseOperativeService.apply_to_role(
                session,
                cliente_id=cliente_id,
                rol_id=rol_id,
                codigo_rol=codigo_rol,
            )
            role_results.append(one)
            total_inserted += int(one.get("inserted", 0))
        return {
            "cliente_id": str(cliente_id),
            "roles": role_results,
            "total_inserted": total_inserted,
            "expected_codigos": list(BASE_OPERATIVE_PERMISSION_CODIGOS),
        }

    @staticmethod
    async def apply_to_role(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
        codigo_rol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Inserta permisos BASE_OPERATIVE faltantes para un rol."""
        count_before = await BaseOperativeService._count_base_grants(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        missing = await BaseOperativeService._missing_permiso_codigos(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        if missing:
            await BaseOperativeService._insert_grants(
                session,
                cliente_id=cliente_id,
                rol_id=rol_id,
                permiso_codigos=missing,
            )
        count_after = await BaseOperativeService._count_base_grants(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        present = await BaseOperativeService._list_present_codigos(
            session, cliente_id=cliente_id, rol_id=rol_id
        )
        inserted = max(0, count_after - count_before)
        complete = set(present) >= set(BASE_OPERATIVE_PERMISSION_CODIGOS)
        return {
            "codigo_rol": codigo_rol,
            "rol_id": str(rol_id),
            "inserted": inserted,
            "total_base_grants": count_after,
            "codigos_present": present,
            "codigos_missing": [
                c for c in BASE_OPERATIVE_PERMISSION_CODIGOS if c not in present
            ],
            "complete": complete,
        }

    @staticmethod
    async def ensure_for_operative_role(
        cliente_id: UUID,
        rol_id: UUID,
        codigo_rol: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Hook assign rol: asegura BASE_OPERATIVE si codigo_rol es MANAGER/USER.
        Usa conexión ADMIN independiente (fuera de transacción onboarding).
        """
        if not codigo_rol or codigo_rol not in OPERATIVE_ROLE_CODIGOS:
            return None
        from app.infrastructure.database.connection_async import (
            DatabaseConnection,
            get_db_connection,
        )

        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await BaseOperativeService.apply_to_role(
                session,
                cliente_id=cliente_id,
                rol_id=rol_id,
                codigo_rol=codigo_rol,
            )
            await session.commit()
        if int(result.get("inserted", 0)) > 0:
            BaseOperativeService._invalidate_tenant_cache(cliente_id)
        return result

    @staticmethod
    async def audit_operative_roles(
        session: AsyncSession,
        *,
        cliente_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Lista roles operativos incompletos (repair dry-run)."""
        cid_filter = "AND r.cliente_id = :cliente_id" if cliente_id else ""
        bind: Dict[str, Any] = {}
        if cliente_id:
            bind["cliente_id"] = cliente_id
        codes_ph, codes_bind = _bind_codes(BASE_OPERATIVE_PERMISSION_CODIGOS)
        bind.update(codes_bind)

        rows = (
            await session.execute(
                text(f"""
                    SELECT r.cliente_id, r.rol_id, r.codigo_rol, c.subdominio,
                           COUNT(DISTINCT p.codigo) AS base_count
                    FROM rol r
                    INNER JOIN cliente c ON c.cliente_id = r.cliente_id
                    LEFT JOIN rol_permiso rp
                        ON rp.rol_id = r.rol_id AND rp.cliente_id = r.cliente_id
                    LEFT JOIN permiso p
                        ON p.permiso_id = rp.permiso_id
                       AND p.es_activo = 1
                       AND p.codigo IN ({codes_ph})
                    WHERE r.es_activo = 1
                      AND r.codigo_rol IN ('MANAGER_TENANT', 'USER_TENANT')
                      {cid_filter}
                    GROUP BY r.cliente_id, r.rol_id, r.codigo_rol, c.subdominio
                    HAVING COUNT(DISTINCT p.codigo) < :expected
                """).bindparams(**bind, expected=len(BASE_OPERATIVE_PERMISSION_CODIGOS))
            )
        ).fetchall()

        out: List[Dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "cliente_id": str(row[0]),
                    "rol_id": str(row[1]),
                    "codigo_rol": row[2],
                    "subdominio": row[3],
                    "base_count": int(row[4]),
                    "expected": len(BASE_OPERATIVE_PERMISSION_CODIGOS),
                    "needs_repair": True,
                }
            )
        return out

    @staticmethod
    async def _resolve_rol_id(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        codigo_rol: str,
    ) -> Optional[UUID]:
        row = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cliente_id
                      AND codigo_rol = :codigo_rol
                      AND es_activo = 1
                """).bindparams(cliente_id=cliente_id, codigo_rol=codigo_rol)
            )
        ).fetchone()
        if not row:
            return None
        rid = row[0]
        return rid if isinstance(rid, UUID) else UUID(str(rid))

    @staticmethod
    async def _count_base_grants(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
    ) -> int:
        codes_ph, codes_bind = _bind_codes(BASE_OPERATIVE_PERMISSION_CODIGOS)
        bind = {
            "cliente_id": cliente_id,
            "rol_id": rol_id,
            **codes_bind,
        }
        row = (
            await session.execute(
                text(f"""
                    SELECT COUNT(*) FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :rol_id
                      AND p.codigo IN ({codes_ph})
                """).bindparams(**bind)
            )
        ).fetchone()
        return int(row[0] if row else 0)

    @staticmethod
    async def _list_present_codigos(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
    ) -> List[str]:
        codes_ph, codes_bind = _bind_codes(BASE_OPERATIVE_PERMISSION_CODIGOS)
        bind = {
            "cliente_id": cliente_id,
            "rol_id": rol_id,
            **codes_bind,
        }
        rows = (
            await session.execute(
                text(f"""
                    SELECT p.codigo FROM rol_permiso rp
                    INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
                    WHERE rp.cliente_id = :cliente_id
                      AND rp.rol_id = :rol_id
                      AND p.codigo IN ({codes_ph})
                    ORDER BY p.codigo
                """).bindparams(**bind)
            )
        ).fetchall()
        return [str(r[0]) for r in rows]

    @staticmethod
    async def _missing_permiso_codigos(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
    ) -> List[str]:
        present = set(
            await BaseOperativeService._list_present_codigos(
                session, cliente_id=cliente_id, rol_id=rol_id
            )
        )
        missing = [c for c in BASE_OPERATIVE_PERMISSION_CODIGOS if c not in present]
        if not missing:
            return []
        codes_ph, codes_bind = _bind_codes(tuple(missing))
        bind = {**codes_bind}
        rows = (
            await session.execute(
                text(f"""
                    SELECT codigo FROM permiso
                    WHERE es_activo = 1 AND codigo IN ({codes_ph})
                """).bindparams(**bind)
            )
        ).fetchall()
        found = {str(r[0]) for r in rows}
        not_in_catalog = [c for c in missing if c not in found]
        if not_in_catalog:
            raise DatabaseError(
                detail=(
                    "Catálogo permiso incompleto para BASE_OPERATIVE: "
                    f"{', '.join(not_in_catalog)}"
                ),
                internal_code=BASE_OPERATIVE_MISSING_PERMISO,
            )
        return missing

    @staticmethod
    async def _insert_grants(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        rol_id: UUID,
        permiso_codigos: List[str],
    ) -> None:
        if not permiso_codigos:
            return
        codes_ph, codes_bind = _bind_codes(tuple(permiso_codigos))
        bind = {
            "cliente_id": cliente_id,
            "rol_id": rol_id,
            **codes_bind,
        }
        await session.execute(
            text(f"""
                INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)
                SELECT NEWID(), :cliente_id, :rol_id, p.permiso_id, GETDATE()
                FROM permiso p
                WHERE p.es_activo = 1
                  AND p.codigo IN ({codes_ph})
                  AND NOT EXISTS (
                        SELECT 1 FROM rol_permiso rp
                        WHERE rp.cliente_id = :cliente_id
                          AND rp.rol_id = :rol_id
                          AND rp.permiso_id = p.permiso_id
                  )
            """).bindparams(**bind)
        )

    @staticmethod
    def _invalidate_tenant_cache(cliente_id: UUID) -> None:
        try:
            from app.core.authorization.permission_resolver import get_permission_resolver

            get_permission_resolver().invalidate_for_tenant(cliente_id)
        except Exception as exc:
            logger.debug("BASE_OPERATIVE cache invalidation (no bloqueante): %s", exc)
