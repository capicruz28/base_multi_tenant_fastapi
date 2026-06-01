# app/modules/org/presentation/endpoints.py
"""
Router principal del módulo ORG (Organización).
Agrupa todos los sub-routers bajo el prefijo /org.
"""
from fastapi import APIRouter, Depends

from app.modules.org.presentation.org_deps import (
    require_org_company_erp_session,
    require_org_tenant_erp_session,
)
from app.modules.org.presentation.endpoints_empresa import router as router_empresa
from app.modules.org.presentation.endpoints_sucursales import router as router_sucursales
from app.modules.org.presentation.endpoints_centros_costo import router as router_centros_costo
from app.modules.org.presentation.endpoints_departamentos import router as router_departamentos
from app.modules.org.presentation.endpoints_cargos import router as router_cargos
from app.modules.org.presentation.endpoints_parametros import router as router_parametros

router = APIRouter()

router.include_router(
    router_empresa,
    prefix="/empresa",
    tags=["ORG - Empresa"],
    dependencies=[Depends(require_org_tenant_erp_session)],
)
router.include_router(
    router_sucursales,
    prefix="/sucursales",
    tags=["ORG - Sucursales"],
    dependencies=[Depends(require_org_company_erp_session)],
)
router.include_router(
    router_centros_costo,
    prefix="/centros-costo",
    tags=["ORG - Centros de costo"],
    dependencies=[Depends(require_org_company_erp_session)],
)
router.include_router(
    router_departamentos,
    prefix="/departamentos",
    tags=["ORG - Departamentos"],
    dependencies=[Depends(require_org_company_erp_session)],
)
router.include_router(
    router_cargos,
    prefix="/cargos",
    tags=["ORG - Cargos"],
    dependencies=[Depends(require_org_company_erp_session)],
)
router.include_router(
    router_parametros,
    prefix="/parametros",
    tags=["ORG - Parámetros"],
    dependencies=[Depends(require_org_company_erp_session)],
)