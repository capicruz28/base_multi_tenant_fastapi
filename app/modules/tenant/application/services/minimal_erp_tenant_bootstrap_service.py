"""
Bootstrap ERP mínimo al crear tenant: una org_empresa + vínculo admin.

No crea sucursal, almacén, plan contable ni secuencias adicionales.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.modules.tenant.presentation.schemas import ClienteCreate

logger = logging.getLogger(__name__)

CODIGO_EMPRESA_INICIAL = "EMP001"
ADMIN_USERNAME = "admin"


def _normalize_ruc(cliente_data: ClienteCreate, cliente_id: UUID) -> str:
    raw = (cliente_data.ruc or "").strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 8:
        return digits[:11].ljust(11, "0")[:11]
    # RUC sintético determinista por tenant (11 dígitos)
    suffix = str(cliente_id.int % 10_000_000_000).zfill(10)
    return f"20{suffix}"[:11]


class MinimalErpTenantBootstrapService:
    """Empresa sede + defaults de usuario admin (onboarding / repair)."""

    @staticmethod
    async def ensure_empresa_inicial(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        usuario_creacion_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Garantiza una org_empresa activa. Idempotente por cliente_id.
        """
        existing = await MinimalErpTenantBootstrapService._get_primera_empresa_activa(
            session, cliente_id
        )
        if existing:
            return {
                "empresa_id": str(existing["empresa_id"]),
                "codigo_empresa": existing["codigo_empresa"],
                "created": False,
            }

        empresa_id = uuid4()
        ruc = _normalize_ruc(cliente_data, cliente_id)
        nombre_comercial = (
            (cliente_data.nombre_comercial or "").strip()
            or (cliente_data.razon_social or "").strip()
        )[:150]

        sql = text("""
            INSERT INTO org_empresa (
                empresa_id, cliente_id, codigo_empresa, razon_social,
                nombre_comercial, ruc, tipo_documento_tributario,
                email_principal, es_activo, usuario_creacion_id
            )
            VALUES (
                :empresa_id, :cliente_id, :codigo_empresa, :razon_social,
                :nombre_comercial, :ruc, 'RUC',
                :email_principal, 1, :usuario_creacion_id
            )
        """).bindparams(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            codigo_empresa=CODIGO_EMPRESA_INICIAL,
            razon_social=(cliente_data.razon_social or "")[:200],
            nombre_comercial=nombre_comercial or None,
            ruc=ruc,
            email_principal=(cliente_data.contacto_email or "")[:100],
            usuario_creacion_id=usuario_creacion_id,
        )
        try:
            await session.execute(sql)
        except Exception as exc:
            if "UQ_org_empresa" in str(exc) or "UNIQUE" in str(exc).upper():
                row = await MinimalErpTenantBootstrapService._get_primera_empresa_activa(
                    session, cliente_id
                )
                if row:
                    return {
                        "empresa_id": str(row["empresa_id"]),
                        "codigo_empresa": row["codigo_empresa"],
                        "created": False,
                    }
            raise DatabaseError(
                detail=f"No se pudo crear org_empresa inicial: {exc}",
                internal_code="MINIMAL_ERP_EMPRESA_CREATE_FAILED",
            ) from exc

        logger.info(
            "org_empresa inicial creada cliente=%s empresa=%s codigo=%s",
            cliente_id,
            empresa_id,
            CODIGO_EMPRESA_INICIAL,
        )
        return {
            "empresa_id": str(empresa_id),
            "codigo_empresa": CODIGO_EMPRESA_INICIAL,
            "created": True,
        }

    @staticmethod
    async def vincular_admin_empresa(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        usuario_id: UUID,
        admin_rol_id: UUID,
        empresa_id: UUID,
    ) -> Dict[str, Any]:
        """
        M4 — Admin tenant-wide: preferida en usuario; usuario_rol ADMIN con empresa_id NULL.

        ``empresa_id`` solo fija ``usuario.empresa_default_id`` (preferencia login M1),
        no el scope de ``usuario_rol``.
        """
        eid = empresa_id if isinstance(empresa_id, UUID) else UUID(str(empresa_id))

        await session.execute(
            text("""
                UPDATE usuario
                SET empresa_default_id = :empresa_id
                WHERE usuario_id = :usuario_id
                  AND cliente_id = :cliente_id
                  AND es_eliminado = 0
            """).bindparams(
                empresa_id=eid,
                usuario_id=usuario_id,
                cliente_id=cliente_id,
            )
        )

        ur_updated = await session.execute(
            text("""
                UPDATE usuario_rol
                SET empresa_id = NULL, es_activo = 1
                WHERE usuario_id = :usuario_id
                  AND rol_id = :rol_id
                  AND cliente_id = :cliente_id
            """).bindparams(
                usuario_id=usuario_id,
                rol_id=admin_rol_id,
                cliente_id=cliente_id,
            )
        )
        rows = int(getattr(ur_updated, "rowcount", 0) or 0)
        if rows == 0:
            await session.execute(
                text("""
                    INSERT INTO usuario_rol (
                        usuario_rol_id, usuario_id, rol_id, cliente_id,
                        empresa_id, es_activo
                    )
                    VALUES (
                        :usuario_rol_id, :usuario_id, :rol_id, :cliente_id,
                        NULL, 1
                    )
                """).bindparams(
                    usuario_rol_id=uuid4(),
                    usuario_id=usuario_id,
                    rol_id=admin_rol_id,
                    cliente_id=cliente_id,
                )
            )
            rows = 1

        logger.info(
            "[M4] ADMIN_TENANT tenant-wide usuario=%s cliente=%s default=%s",
            usuario_id,
            cliente_id,
            eid,
        )
        return {
            "usuario_id": str(usuario_id),
            "empresa_default_id": str(eid),
            "usuario_rol_empresa_id": None,
            "usuario_rol_updated": rows,
        }

    @staticmethod
    async def bootstrap_minimal_erp(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        usuario_id: UUID,
        admin_rol_id: UUID,
    ) -> Dict[str, Any]:
        emp = await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
            session,
            cliente_id=cliente_id,
            cliente_data=cliente_data,
            usuario_creacion_id=usuario_id,
        )
        empresa_id = UUID(str(emp["empresa_id"]))
        link = await MinimalErpTenantBootstrapService.vincular_admin_empresa(
            session,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            admin_rol_id=admin_rol_id,
            empresa_id=empresa_id,
        )
        return {"empresa": emp, "admin_link": link}

    @staticmethod
    async def _get_primera_empresa_activa(
        session: AsyncSession, cliente_id: UUID
    ) -> Optional[Dict[str, Any]]:
        result = await session.execute(
            text("""
                SELECT TOP 1 empresa_id, codigo_empresa, razon_social
                FROM org_empresa
                WHERE cliente_id = :cliente_id AND es_activo = 1
                ORDER BY fecha_creacion
            """).bindparams(cliente_id=cliente_id)
        )
        row = result.fetchone()
        if not row:
            return None
        return {
            "empresa_id": row[0],
            "codigo_empresa": row[1],
            "razon_social": row[2],
        }
