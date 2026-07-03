"""F6-P4 — Organization Read Gateway: enriquecimiento read-only desde Data Plane."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.infrastructure.database.queries.org.empresa_queries import (
    get_empresa_by_id,
    get_empresas_by_ids,
    list_empresas,
)


class OrgReadGateway:
    """Punto único de lectura org/ERP para enriquecimiento de sesiones (F6-P4)."""

    @staticmethod
    def _empresa_display_name(row: Dict[str, Any]) -> str:
        return str(row.get("nombre_comercial") or row.get("razon_social") or "")

    @staticmethod
    async def get_empresa_display_names_by_ids(
        cliente_id: UUID,
        empresa_ids: List[UUID],
    ) -> Dict[UUID, str]:
        """Batch lookup de nombre visible de empresa por tenant."""
        if not empresa_ids:
            return {}

        unique_ids = list({eid for eid in empresa_ids if eid})
        rows = await get_empresas_by_ids(cliente_id, unique_ids)
        result: Dict[UUID, str] = {}
        for row in rows:
            empresa_id = row.get("empresa_id")
            if not empresa_id:
                continue
            if isinstance(empresa_id, str):
                empresa_id = UUID(empresa_id)
            result[empresa_id] = OrgReadGateway._empresa_display_name(row)
        return result

    @staticmethod
    async def list_active_empresas_for_login(
        cliente_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Empresas activas del tenant para resolución post-login (F8-A)."""
        rows = await list_empresas(cliente_id, solo_activos=True)
        return [
            {
                "empresa_id": row.get("empresa_id"),
                "razon_social": row.get("razon_social"),
                "nombre_comercial": row.get("nombre_comercial"),
            }
            for row in rows
            if row.get("empresa_id")
        ]

    @staticmethod
    async def get_active_empresas_by_ids(
        cliente_id: UUID,
        empresa_ids: List[UUID],
    ) -> List[Dict[str, Any]]:
        """Batch lookup filtrando solo empresas activas."""
        if not empresa_ids:
            return []
        rows = await get_empresas_by_ids(cliente_id, empresa_ids)
        active: List[Dict[str, Any]] = []
        for row in rows:
            if not row.get("es_activo", True):
                continue
            active.append(
                {
                    "empresa_id": row.get("empresa_id"),
                    "razon_social": row.get("razon_social"),
                    "nombre_comercial": row.get("nombre_comercial"),
                }
            )
        return active

    @staticmethod
    async def is_empresa_active(
        cliente_id: UUID,
        empresa_id: UUID,
    ) -> bool:
        """True si la empresa existe, pertenece al tenant y está activa."""
        row = await get_empresa_by_id(cliente_id, empresa_id)
        if not row:
            return False
        return bool(row.get("es_activo", False))


__all__ = ["OrgReadGateway"]
