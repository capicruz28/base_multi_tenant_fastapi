"""F6-P1 — políticas de filtro tenant para Identity Store."""
from enum import Enum


class IdentityScope(str, Enum):
    """
    ROW_SCOPED: filtro ``cliente_id`` en SQL (Shared / Platform con cliente SYSTEM).
    ENGINE_SCOPED: aislamiento por engine DP dedicado — sin inyectar ``cliente_id``.
    """

    ROW_SCOPED = "row_scoped"
    ENGINE_SCOPED = "engine_scoped"


__all__ = ["IdentityScope"]
