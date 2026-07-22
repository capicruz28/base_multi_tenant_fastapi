"""CodigoRuntimeSnapshotService — owner del Runtime Snapshot (Etapa 1).

Proyección read-only: cfg_codigo_secuencia ∩ módulos activos ∩ SequenceCatalog.
No usa Gateway, ensure_row, allocate, preview ni DTOs Admin.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.tenant.routing import (
    OPERATION_CLASS_TENANT_DATA,
    get_connection_for_tenant,
)
from app.infrastructure.database.queries.cfg import list_codigo_secuencias
from app.modules.cfg.application.runtime.codigo_runtime_snapshot_types import (
    CodigoRuntimeSequence,
    CodigoRuntimeSnapshot,
)
from app.modules.modulos.application.services.cliente_modulo_service import (
    ClienteModuloService,
)

_SCHEMA_VERSION = "1.0"


def _optional_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _sort_key(item: CodigoRuntimeSequence) -> tuple:
    return (
        item.sequence_key,
        item.scope_type,
        str(item.empresa_id or ""),
        str(item.almacen_id or ""),
        str(item.punto_venta_id or ""),
    )


def _item_canonical_dict(item: CodigoRuntimeSequence) -> Dict[str, Any]:
    return {
        "allow_manual": item.allow_manual,
        "almacen_id": str(item.almacen_id) if item.almacen_id else None,
        "empresa_id": str(item.empresa_id) if item.empresa_id else None,
        "es_activo": item.es_activo,
        "generation_policy": item.generation_policy,
        "longitud_numero": item.longitud_numero,
        "max_output_length": item.max_output_length,
        "modulo_codigo": item.modulo_codigo,
        "normalize_case": item.normalize_case,
        "prefijo": item.prefijo,
        "punto_venta_id": str(item.punto_venta_id) if item.punto_venta_id else None,
        "scope_type": item.scope_type,
        "separador": item.separador,
        "sequence_key": item.sequence_key,
        "supports_preview": item.supports_preview,
    }


def _compute_content_revision(items: List[CodigoRuntimeSequence]) -> str:
    payload = [_item_canonical_dict(item) for item in items]
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _project_row(row: Dict[str, Any]) -> Optional[CodigoRuntimeSequence]:
    key = str(row.get("sequence_key") or "").strip()
    if not key or not SequenceCatalog.contains(key):
        return None
    defn = SequenceCatalog.get(key)
    return CodigoRuntimeSequence(
        sequence_key=key,
        modulo_codigo=defn.modulo_codigo,
        scope_type=str(row.get("scope_type") or defn.scope_type.value),
        generation_policy=str(row.get("generation_policy") or ""),
        es_activo=bool(row.get("es_activo", True)),
        prefijo=str(row.get("prefijo") or ""),
        separador=str(row.get("separador") or ""),
        longitud_numero=int(row["longitud_numero"]),
        supports_preview=bool(defn.supports_preview),
        allow_manual=bool(defn.allow_manual),
        normalize_case=defn.normalize_case.value,
        max_output_length=int(defn.max_output_length),
        empresa_id=_optional_uuid(row.get("empresa_id")),
        almacen_id=_optional_uuid(row.get("almacen_id")),
        punto_venta_id=_optional_uuid(row.get("punto_venta_id")),
    )


class CodigoRuntimeSnapshotService:
    """Construye ``CodigoRuntimeSnapshot`` para un tenant (Shared / Dedicated)."""

    schema_version: str = _SCHEMA_VERSION

    async def build_snapshot(self, cliente_id: UUID) -> CodigoRuntimeSnapshot:
        codigos_activos = await ClienteModuloService.obtener_codigos_modulos_activos_cliente(
            cliente_id
        )

        async with get_connection_for_tenant(
            cliente_id, OPERATION_CLASS_TENANT_DATA
        ) as session:
            rows = await list_codigo_secuencias(cliente_id, session=session)

        items: List[CodigoRuntimeSequence] = []
        for row in rows:
            projected = _project_row(row)
            if projected is None:
                continue
            if projected.modulo_codigo.upper() not in codigos_activos:
                continue
            items.append(projected)

        items.sort(key=_sort_key)
        content_revision = _compute_content_revision(items)

        return CodigoRuntimeSnapshot(
            schema_version=self.schema_version,
            generated_at=datetime.utcnow(),
            content_revision=content_revision,
            items=tuple(items),
        )


__all__ = ["CodigoRuntimeSnapshotService"]
