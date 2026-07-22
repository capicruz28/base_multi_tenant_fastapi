"""Servicios de administración de cfg_codigo_secuencia (MVP Backend).

Spec: cfg-implementation-spec v1.0 — Etapa 6.
Orquesta queries/cfg + SequenceCatalog + Gateway.preview.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from app.core.codigo.enums import GenerationOperation
from app.core.codigo.generation_context import GenerationContext
from app.core.codigo.gateway.codigo_generacion_gateway import CodigoGeneracionGateway
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.exceptions import CustomException, NotFoundError, ValidationError
from app.core.tenant.routing import (
    OPERATION_CLASS_TENANT_DATA,
    get_connection_for_tenant,
)
from app.infrastructure.database.queries.cfg import (
    get_codigo_secuencia_by_id,
    list_codigo_secuencias,
    set_codigo_secuencia_activo,
    update_codigo_secuencia_config,
)
from app.modules.modulos.application.services.cliente_modulo_service import (
    ClienteModuloService,
)
from app.modules.cfg.presentation.schemas import (
    CodigoSecuenciaPreviewResponse,
    CodigoSecuenciaRead,
    CodigoSecuenciaUpdate,
    PaginatedCodigoSecuenciaResponse,
)
from app.shared.pagination import (
    ErpPaginationParams,
    ErpSortParams,
    build_paginated_response,
)
from app.shared.pagination.query_helpers import apply_memory_sort

_NOT_FOUND = "Secuencia de código no encontrada."
_ORG_EMPRESA_KEY = "org_empresa"
_ALLOWED_SEPARATORS = frozenset({"", "-"})
_ALLOWED_GENERATION_POLICIES = frozenset(
    {"AUTO_REQUIRED", "AUTO_DEFAULT", "MANUAL_ONLY"}
)
_PREFIX_RE = re.compile(r"^[A-Z0-9]*$")

_SORT_WHITELIST = frozenset(
    {
        "sequence_key",
        "scope_type",
        "prefijo",
        "ultimo_numero",
        "es_activo",
        "fecha_creacion",
        "fecha_actualizacion",
    }
)


# ---------------------------------------------------------------------------
# Helpers privados (enrich / validación / preview context)
# ---------------------------------------------------------------------------


def _raise_org_empresa_locked() -> None:
    raise CustomException(
        status_code=422,
        detail="La secuencia de empresa está protegida por el sistema.",
        internal_code="ORG_EMPRESA_CFG_LOCKED",
    )


def _is_org_empresa(row: Dict[str, Any]) -> bool:
    return str(row.get("sequence_key") or "") == _ORG_EMPRESA_KEY


def _enrich_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Fusiona fila cfg + metadatos SequenceCatalog (BR-EN-*)."""
    out = dict(row)
    key = str(out.get("sequence_key") or "")
    out["config_locked"] = key == _ORG_EMPRESA_KEY

    if not key or not SequenceCatalog.contains(key):
        out.update(
            {
                "entity_table": None,
                "code_column": None,
                "modulo_codigo": None,
                "catalog_policy": None,
                "supports_preview": None,
                "allow_manual": None,
                "sequence_family": None,
                "default_prefix": None,
                "default_separator": None,
                "default_padding": None,
                "policy_drift": False,
            }
        )
        return out

    defn = SequenceCatalog.get(key)
    catalog_policy = defn.policy.value
    cfg_policy = str(out.get("generation_policy") or "")
    out.update(
        {
            "entity_table": defn.table_name,
            "code_column": defn.code_column,
            "modulo_codigo": defn.modulo_codigo,
            "catalog_policy": catalog_policy,
            "supports_preview": defn.supports_preview,
            "allow_manual": defn.allow_manual,
            "sequence_family": defn.sequence_family.value,
            "default_prefix": defn.default_prefix,
            "default_separator": defn.default_separator,
            "default_padding": defn.default_padding,
            "policy_drift": cfg_policy != catalog_policy,
        }
    )
    return out


def _row_to_read(row: Dict[str, Any]) -> CodigoSecuenciaRead:
    return CodigoSecuenciaRead.model_validate(_enrich_row(row))


def _build_preview_context(row: Dict[str, Any], cliente_id: UUID) -> GenerationContext:
    """Scope desde la fila cfg (BR-PV-04)."""
    return GenerationContext(
        client_id=cliente_id,
        operation=GenerationOperation.PREVIEW,
        empresa_id=row.get("empresa_id"),
        almacen_id=row.get("almacen_id"),
        punto_venta_id=row.get("punto_venta_id"),
    )


def _validate_patch_payload(
    row: Dict[str, Any],
    data: CodigoSecuenciaUpdate,
) -> Dict[str, Any]:
    """Validaciones PATCH sin BD (BR PATCH + org_empresa lock)."""
    if _is_org_empresa(row):
        _raise_org_empresa_locked()

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        raise CustomException(
            status_code=422,
            detail="Debe enviar al menos un campo configurable.",
            internal_code="VALIDATION_ERROR",
        )

    if "prefijo" in payload:
        prefijo = payload["prefijo"]
        if prefijo is None or prefijo == "":
            raise CustomException(
                status_code=422,
                detail="El prefijo es inválido.",
                internal_code="CFG_PREFIX_INVALID",
            )
        if len(prefijo) > 10 or not _PREFIX_RE.match(prefijo):
            raise CustomException(
                status_code=422,
                detail="El prefijo es inválido (máx. 10, alfanumérico).",
                internal_code="CFG_PREFIX_INVALID",
            )

    if "separador" in payload:
        sep = payload["separador"]
        if sep is None or sep not in _ALLOWED_SEPARATORS:
            raise CustomException(
                status_code=422,
                detail="El separador solo admite cadena vacía o '-'.",
                internal_code="CFG_SEPARATOR_INVALID",
            )

    if "longitud_numero" in payload:
        pad = payload["longitud_numero"]
        if pad is None or int(pad) < 1:
            raise CustomException(
                status_code=422,
                detail="longitud_numero debe ser >= 1.",
                internal_code="CFG_PADDING_INVALID",
            )
        key = str(row.get("sequence_key") or "")
        if key and SequenceCatalog.contains(key):
            defn = SequenceCatalog.get(key)
            # Parte numérica no debe superar max_output_length en peor caso FMT_STANDARD.
            if int(pad) > defn.max_output_length:
                raise CustomException(
                    status_code=422,
                    detail="longitud_numero excede el máximo permitido para esta secuencia.",
                    internal_code="CFG_PADDING_INVALID",
                )

    if "numero_inicial" in payload:
        piso = payload["numero_inicial"]
        if piso is None or int(piso) < 1:
            raise CustomException(
                status_code=422,
                detail="numero_inicial debe ser >= 1.",
                internal_code="CFG_NUMERO_INICIAL_INVALID",
            )

    if "generation_policy" in payload:
        policy = payload["generation_policy"]
        if policy is None or policy not in _ALLOWED_GENERATION_POLICIES:
            raise CustomException(
                status_code=422,
                detail=(
                    "generation_policy solo admite AUTO_REQUIRED, "
                    "AUTO_DEFAULT o MANUAL_ONLY."
                ),
                internal_code="CFG_GENERATION_POLICY_INVALID",
            )

    return payload


def _require_row(
    row: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if row is None:
        raise NotFoundError(detail=_NOT_FOUND)
    return row


# ---------------------------------------------------------------------------
# Servicios públicos
# ---------------------------------------------------------------------------


async def list_codigo_secuencias_servicio(
    cliente_id: UUID,
    *,
    empresa_id: Optional[UUID] = None,
    scope_type: Optional[str] = None,
    sequence_key: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
    modulo_codigo: Optional[str] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[CodigoSecuenciaRead], PaginatedCodigoSecuenciaResponse]:
    """Listado G-04: SQL nativo → enrich → SaaS módulos activos → filtro módulo → sort → page."""
    codigos_activos = await ClienteModuloService.obtener_codigos_modulos_activos_cliente(
        cliente_id
    )
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        rows = await list_codigo_secuencias(
            cliente_id,
            empresa_id=empresa_id,
            scope_type=scope_type,
            sequence_key=sequence_key,
            es_activo=es_activo,
            buscar=buscar,
            session=session,
        )

    enriched = [_enrich_row(r) for r in rows]
    enriched = [
        r
        for r in enriched
        if (r.get("modulo_codigo") or "").upper() in codigos_activos
    ]

    if modulo_codigo:
        needle = modulo_codigo.strip().upper()
        enriched = [
            r
            for r in enriched
            if (r.get("modulo_codigo") or "").upper() == needle
        ]

    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    enriched = apply_memory_sort(
        enriched,
        allowed_columns=_SORT_WHITELIST,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_key=lambda r: (
            str(r.get("modulo_codigo") or ""),
            str(r.get("sequence_key") or ""),
        ),
        tie_breaker_key=lambda r: str(r.get("secuencia_id") or ""),
    )

    items = [CodigoSecuenciaRead.model_validate(r) for r in enriched]

    if pagination is not None and pagination.is_paginated:
        total = len(items)
        page_slice = items[
            pagination.offset : pagination.offset + pagination.limit
        ]
        envelope = build_paginated_response(page_slice, total, pagination)
        return PaginatedCodigoSecuenciaResponse(
            items=envelope.items,
            total=envelope.total,
            pagina_actual=envelope.pagina_actual,
            total_paginas=envelope.total_paginas,
            limit=envelope.limit,
        )

    return items


async def get_codigo_secuencia_servicio(
    cliente_id: UUID,
    secuencia_id: UUID,
) -> CodigoSecuenciaRead:
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        row = await get_codigo_secuencia_by_id(
            cliente_id, secuencia_id, session=session
        )
    return _row_to_read(_require_row(row))


async def update_codigo_secuencia_servicio(
    cliente_id: UUID,
    secuencia_id: UUID,
    data: CodigoSecuenciaUpdate,
    *,
    usuario_id: UUID,
) -> CodigoSecuenciaRead:
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            row = _require_row(
                await get_codigo_secuencia_by_id(
                    cliente_id, secuencia_id, session=session
                )
            )
            payload = _validate_patch_payload(row, data)
            updated = await update_codigo_secuencia_config(
                cliente_id,
                secuencia_id,
                payload,
                session=session,
                usuario_actualizacion_id=usuario_id,
            )
    return _row_to_read(_require_row(updated))


async def desactivar_codigo_secuencia_servicio(
    cliente_id: UUID,
    secuencia_id: UUID,
    *,
    usuario_id: UUID,
) -> CodigoSecuenciaRead:
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            row = _require_row(
                await get_codigo_secuencia_by_id(
                    cliente_id, secuencia_id, session=session
                )
            )
            if _is_org_empresa(row):
                _raise_org_empresa_locked()
            if row.get("es_activo") is False:
                return _row_to_read(row)
            updated = await set_codigo_secuencia_activo(
                cliente_id,
                secuencia_id,
                False,
                session=session,
                usuario_actualizacion_id=usuario_id,
            )
    return _row_to_read(_require_row(updated))


async def reactivar_codigo_secuencia_servicio(
    cliente_id: UUID,
    secuencia_id: UUID,
    *,
    usuario_id: UUID,
) -> CodigoSecuenciaRead:
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            row = _require_row(
                await get_codigo_secuencia_by_id(
                    cliente_id, secuencia_id, session=session
                )
            )
            if row.get("es_activo") is True:
                return _row_to_read(row)
            updated = await set_codigo_secuencia_activo(
                cliente_id,
                secuencia_id,
                True,
                session=session,
                usuario_actualizacion_id=usuario_id,
            )
    return _row_to_read(_require_row(updated))


async def preview_codigo_secuencia_servicio(
    cliente_id: UUID,
    secuencia_id: UUID,
) -> CodigoSecuenciaPreviewResponse:
    async with get_connection_for_tenant(
        cliente_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        row = _require_row(
            await get_codigo_secuencia_by_id(
                cliente_id, secuencia_id, session=session
            )
        )
        key = str(row.get("sequence_key") or "")
        if key and SequenceCatalog.contains(key):
            defn = SequenceCatalog.get(key)
            if not defn.supports_preview:
                raise CustomException(
                    status_code=422,
                    detail="Preview no permitido para esta secuencia.",
                    internal_code="PREVIEW_NOT_ALLOWED",
                )
        elif key:
            # Key desconocida en catálogo: Gateway fallará con SEQUENCE_KEY_UNKNOWN
            pass

        ultimo_antes = int(row.get("ultimo_numero") or 0)
        context = _build_preview_context(row, cliente_id)
        try:
            result = await CodigoGeneracionGateway.preview(
                key, context, session
            )
        except ValidationError as exc:
            # Alinear PREVIEW_NOT_ALLOWED del Motor a HTTP 422 si aplica
            if getattr(exc, "internal_code", None) == "PREVIEW_NOT_ALLOWED":
                raise CustomException(
                    status_code=422,
                    detail=exc.detail,
                    internal_code="PREVIEW_NOT_ALLOWED",
                ) from exc
            raise

        # G-05: inactiva permitida; contador no muta en preview
        return CodigoSecuenciaPreviewResponse(
            secuencia_id=row["secuencia_id"],
            sequence_key=key,
            codigo_estimado=result.code,
            ultimo_numero_actual=ultimo_antes,
            numero_inicial=int(row.get("numero_inicial") or 1),
            consume_contador=False,
            es_activo=bool(row.get("es_activo", True)),
            disclaimer=result.disclaimer,
        )
