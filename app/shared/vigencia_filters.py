"""Filtros de vigencia PA-004 — patrón compartido IAM / Clientes."""

from typing import Dict


VIGENCIA_ES_ACTIVO_CLAUSE = """
        AND (
            (:solo_inactivos = 1 AND {alias}.es_activo = 0)
            OR (:solo_inactivos = 0 AND :solo_activos = 1 AND {alias}.es_activo = 1)
            OR (:solo_inactivos = 0 AND :solo_activos = 0)
        )"""


def resolve_vigencia_flags(solo_activos: bool, solo_inactivos: bool) -> tuple[bool, bool]:
    """Precedencia PA-004 (Clientes): solo_inactivos gana sobre solo_activos."""
    if solo_inactivos:
        return False, True
    return solo_activos, False


def vigencia_bind_params(solo_activos: bool, solo_inactivos: bool) -> Dict[str, int]:
    """Parámetros nombrados para VIGENCIA_ES_ACTIVO_CLAUSE (PA-004 precedencia)."""
    resolved_activos, resolved_inactivos = resolve_vigencia_flags(solo_activos, solo_inactivos)
    return {
        "solo_activos": 1 if resolved_activos else 0,
        "solo_inactivos": 1 if resolved_inactivos else 0,
    }
