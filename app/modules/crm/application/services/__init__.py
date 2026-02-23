# app/modules/crm/application/services/__init__.py
"""
Servicios de aplicación para el módulo CRM (Customer Relationship Management).
"""

from app.modules.crm.application.services.campana_service import (
    list_campanas,
    get_campana_by_id,
    create_campana,
    update_campana,
)
from app.modules.crm.application.services.lead_service import (
    list_leads,
    get_lead_by_id,
    create_lead,
    update_lead,
)
from app.modules.crm.application.services.oportunidad_service import (
    list_oportunidades,
    get_oportunidad_by_id,
    create_oportunidad,
    update_oportunidad,
)
from app.modules.crm.application.services.actividad_service import (
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
