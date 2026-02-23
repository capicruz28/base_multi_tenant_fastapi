# app/modules/crm/presentation/endpoints.py
"""
Router principal del módulo CRM (Customer Relationship Management).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.crm.presentation.endpoints_campanas import router as campanas_router
from app.modules.crm.presentation.endpoints_leads import router as leads_router
from app.modules.crm.presentation.endpoints_oportunidades import router as oportunidades_router
from app.modules.crm.presentation.endpoints_actividades import router as actividades_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(campanas_router, prefix="/campanas", tags=["CRM - Campañas"])
router.include_router(leads_router, prefix="/leads", tags=["CRM - Leads"])
router.include_router(oportunidades_router, prefix="/oportunidades", tags=["CRM - Oportunidades"])
router.include_router(actividades_router, prefix="/actividades", tags=["CRM - Actividades"])
