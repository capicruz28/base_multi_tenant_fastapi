# app/infrastructure/database/queries/crm/__init__.py
"""
Queries para el módulo CRM (Customer Relationship Management).
"""

from app.infrastructure.database.queries.crm.campana_queries import (
    list_campanas,
    get_campana_by_id,
    create_campana,
    update_campana,
)
from app.infrastructure.database.queries.crm.lead_queries import (
    list_leads,
    get_lead_by_id,
    create_lead,
    update_lead,
)
from app.infrastructure.database.queries.crm.oportunidad_queries import (
    list_oportunidades,
    get_oportunidad_by_id,
    create_oportunidad,
    update_oportunidad,
)
from app.infrastructure.database.queries.crm.actividad_queries import (
    list_actividades,
    get_actividad_by_id,
    create_actividad,
    update_actividad,
)

__all__ = [
    # Campañas
    "list_campanas",
    "get_campana_by_id",
    "create_campana",
    "update_campana",
    # Leads
    "list_leads",
    "get_lead_by_id",
    "create_lead",
    "update_lead",
    # Oportunidades
    "list_oportunidades",
    "get_oportunidad_by_id",
    "create_oportunidad",
    "update_oportunidad",
    # Actividades
    "list_actividades",
    "get_actividad_by_id",
    "create_actividad",
    "update_actividad",
]
