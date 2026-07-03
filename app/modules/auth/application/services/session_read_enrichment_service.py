"""F6-P4 — enriquecimiento post-query del Session Store read layer vía gateways."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.core.organization.org_read_gateway import OrgReadGateway


def _coerce_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


class SessionReadEnrichmentService:
    """Enriquece filas session-only con identidad y org desde Data Plane."""

    @staticmethod
    async def resolve_search_user_ids(
        cliente_id: UUID,
        search: Optional[str],
    ) -> Optional[List[UUID]]:
        if not search or not search.strip():
            return None
        ctx = IdentityContext(cliente_id=cliente_id)
        return await IdentityGateway.search_user_ids(ctx, search.strip())

    @staticmethod
    async def enrich_admin_rows(
        cliente_id: UUID,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not rows:
            return rows

        usuario_ids: List[UUID] = []
        empresa_ids: List[UUID] = []
        for row in rows:
            uid = _coerce_uuid(row.get("usuario_id"))
            if uid:
                usuario_ids.append(uid)
            eid = _coerce_uuid(row.get("empresa_id"))
            if eid:
                empresa_ids.append(eid)

        ctx = IdentityContext(cliente_id=cliente_id)
        users = await IdentityGateway.get_users_by_ids(ctx, usuario_ids)
        empresas = await OrgReadGateway.get_empresa_display_names_by_ids(
            cliente_id,
            empresa_ids,
        )

        enriched: List[Dict[str, Any]] = []
        for row in rows:
            merged = dict(row)
            uid = _coerce_uuid(row.get("usuario_id"))
            if uid and uid in users:
                merged.update(users[uid])
            eid = _coerce_uuid(row.get("empresa_id"))
            if eid and eid in empresas:
                merged["empresa_nombre"] = empresas[eid]
            enriched.append(merged)
        return enriched


__all__ = ["SessionReadEnrichmentService"]
