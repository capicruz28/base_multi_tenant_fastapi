"""Definiciones cerradas Product Reference — F14 Catalog Sync."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional
from uuid import UUID


class CatalogKind(str, Enum):
    MONEDA = "moneda"
    PAIS = "pais"
    DEPARTAMENTO = "departamento"
    PROVINCIA = "provincia"
    DISTRITO = "distrito"


class NormalizationKind(str, Enum):
    UPPER_STRIP = "upper_strip"
    STRIP = "strip"
    UUID = "uuid"
    DECIMALES = "decimales"
    ES_ACTIVO = "es_activo"


# Reglas de normalización por nombre de columna (contrato 05 §5.3).
COLUMN_NORMALIZATION: dict[str, NormalizationKind] = {
    "codigo": NormalizationKind.UPPER_STRIP,
    "codigo_iso2": NormalizationKind.UPPER_STRIP,
    "codigo_iso3": NormalizationKind.UPPER_STRIP,
    "nombre": NormalizationKind.STRIP,
    "simbolo": NormalizationKind.STRIP,
    "ubigeo": NormalizationKind.STRIP,
    "pais_id": NormalizationKind.UUID,
    "departamento_id": NormalizationKind.UUID,
    "provincia_id": NormalizationKind.UUID,
    "decimales": NormalizationKind.DECIMALES,
    "es_activo": NormalizationKind.ES_ACTIVO,
}


@dataclass(frozen=True, slots=True)
class CatalogDefinition:
    kind: CatalogKind
    table_name: str
    primary_key: str
    compare_columns: tuple[str, ...]
    parent_kind: Optional[CatalogKind] = None
    parent_fk_column: Optional[str] = None
    fk_sync_order: int = 0


CATALOG_DEFINITIONS: dict[CatalogKind, CatalogDefinition] = {
    CatalogKind.MONEDA: CatalogDefinition(
        kind=CatalogKind.MONEDA,
        table_name="cat_moneda",
        primary_key="moneda_id",
        compare_columns=("codigo", "nombre", "simbolo", "decimales", "es_activo"),
        fk_sync_order=0,
    ),
    CatalogKind.PAIS: CatalogDefinition(
        kind=CatalogKind.PAIS,
        table_name="cat_pais",
        primary_key="pais_id",
        compare_columns=("codigo_iso2", "codigo_iso3", "nombre", "es_activo"),
        fk_sync_order=1,
    ),
    CatalogKind.DEPARTAMENTO: CatalogDefinition(
        kind=CatalogKind.DEPARTAMENTO,
        table_name="cat_departamento",
        primary_key="departamento_id",
        compare_columns=("pais_id", "codigo", "nombre", "es_activo"),
        parent_kind=CatalogKind.PAIS,
        parent_fk_column="pais_id",
        fk_sync_order=2,
    ),
    CatalogKind.PROVINCIA: CatalogDefinition(
        kind=CatalogKind.PROVINCIA,
        table_name="cat_provincia",
        primary_key="provincia_id",
        compare_columns=("departamento_id", "codigo", "nombre", "es_activo"),
        parent_kind=CatalogKind.DEPARTAMENTO,
        parent_fk_column="departamento_id",
        fk_sync_order=3,
    ),
    CatalogKind.DISTRITO: CatalogDefinition(
        kind=CatalogKind.DISTRITO,
        table_name="cat_distrito",
        primary_key="distrito_id",
        compare_columns=("provincia_id", "codigo", "nombre", "ubigeo", "es_activo"),
        parent_kind=CatalogKind.PROVINCIA,
        parent_fk_column="provincia_id",
        fk_sync_order=4,
    ),
}


def get_catalog_definition(kind: CatalogKind) -> CatalogDefinition:
    try:
        return CATALOG_DEFINITIONS[kind]
    except KeyError as exc:
        raise ValueError(f"Catálogo no soportado: {kind!r}") from exc


def normalize_column_value(column: str, value: Any) -> Any:
    rule = COLUMN_NORMALIZATION.get(column)
    if rule is None:
        return value
    if rule == NormalizationKind.UPPER_STRIP:
        return (str(value) if value is not None else "").strip().upper()
    if rule == NormalizationKind.STRIP:
        return (str(value) if value is not None else "").strip()
    if rule == NormalizationKind.UUID:
        if value is None:
            return ""
        if isinstance(value, UUID):
            return str(value).lower()
        return str(value).strip().lower()
    if rule == NormalizationKind.DECIMALES:
        return int(value if value is not None else 2)
    if rule == NormalizationKind.ES_ACTIVO:
        if value is None:
            return True
        return bool(value)
    return value


def normalize_row_for_compare(
    row: Mapping[str, Any],
    definition: CatalogDefinition,
) -> dict[str, Any]:
    return {
        column: normalize_column_value(column, row.get(column))
        for column in definition.compare_columns
    }


def canonical_primary_key(row: Mapping[str, Any], definition: CatalogDefinition) -> str:
    raw = row.get(definition.primary_key)
    if raw is None:
        return ""
    if isinstance(raw, UUID):
        return str(raw).lower()
    return str(raw).strip().lower()


def extract_compare_payload(
    row: Mapping[str, Any],
    definition: CatalogDefinition,
) -> dict[str, Any]:
    return {column: row.get(column) for column in definition.compare_columns}


def sort_catalog_kinds_by_fk_order(kinds: list[CatalogKind]) -> list[CatalogKind]:
    return sorted(kinds, key=lambda item: CATALOG_DEFINITIONS[item].fk_sync_order)


__all__ = [
    "CATALOG_DEFINITIONS",
    "COLUMN_NORMALIZATION",
    "CatalogDefinition",
    "CatalogKind",
    "NormalizationKind",
    "canonical_primary_key",
    "extract_compare_payload",
    "get_catalog_definition",
    "normalize_column_value",
    "normalize_row_for_compare",
    "sort_catalog_kinds_by_fk_order",
]
