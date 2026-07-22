"""Queries SQL del módulo CFG (cfg_codigo_secuencia).

Persistencia HTTP canónica — no usar CfgCodigoSecuenciaRepository en el path admin.
"""

from app.infrastructure.database.queries.cfg.codigo_secuencia_queries import (
    get_codigo_secuencia_by_id,
    list_codigo_secuencias,
    set_codigo_secuencia_activo,
    update_codigo_secuencia_config,
)

__all__ = [
    "list_codigo_secuencias",
    "get_codigo_secuencia_by_id",
    "update_codigo_secuencia_config",
    "set_codigo_secuencia_activo",
]
