"""
Router principal de la API v1 para el sistema multi-tenant.

Este módulo centraliza la inclusión de todos los endpoints de la API v1,
organizándolos por funcionalidad y asegurando la coherencia en la estructura
de rutas y tags para la documentación OpenAPI.

Características principales:
- Organización modular de endpoints por dominio de negocio
- Tags consistentes para documentación automática
- Prefijos de rutas organizados lógicamente
- Inclusión de todos los módulos de endpoints
"""
from fastapi import APIRouter
from app.modules.auth.presentation import endpoints as auth_endpoints
from app.modules.auth.presentation import endpoints_auth_config, endpoints_sso
from app.modules.users.presentation import endpoints as users_endpoints
from app.modules.rbac.presentation import endpoints as rbac_endpoints
from app.modules.rbac.presentation import endpoints_permisos, endpoints_permisos_catalogo
from app.modules.menus.presentation import endpoints as menus_endpoints
from app.modules.menus.presentation import endpoints_areas
from app.modules.tenant.presentation import endpoints_clientes, endpoints_modulos, endpoints_conexiones
from app.modules.superadmin.presentation import endpoints_usuarios as superadmin_usuarios_endpoints
from app.modules.superadmin.presentation import endpoints_auditoria as superadmin_auditoria_endpoints
from app.modules.org.presentation import endpoints as org_endpoints
from app.modules.inv.presentation import endpoints as inv_endpoints
from app.modules.pur.presentation import endpoints as pur_endpoints
from app.modules.sls.presentation import endpoints as sls_endpoints
from app.modules.invbill.presentation import endpoints as invbill_endpoints
from app.modules.prc.presentation import endpoints as prc_endpoints
from app.modules.log.presentation import endpoints as log_endpoints
from app.modules.fin.presentation import endpoints as fin_endpoints
from app.modules.wms.presentation import endpoints as wms_endpoints
from app.modules.qms.presentation import endpoints as qms_endpoints
from app.modules.crm.presentation import endpoints as crm_endpoints
from app.modules.pos.presentation import endpoints as pos_endpoints
from app.modules.hcm.presentation import endpoints as hcm_endpoints
from app.modules.mfg.presentation import endpoints as mfg_endpoints
from app.modules.mrp.presentation import endpoints as mrp_endpoints
from app.modules.mps.presentation import endpoints as mps_endpoints
from app.modules.mnt.presentation import endpoints as mnt_endpoints
from app.modules.cst.presentation import endpoints as cst_endpoints
from app.modules.tax.presentation import endpoints as tax_endpoints
from app.modules.bdg.presentation import endpoints as bdg_endpoints
from app.modules.pm.presentation import endpoints as pm_endpoints
from app.modules.svc.presentation import endpoints as svc_endpoints
from app.modules.tkt.presentation import endpoints as tkt_endpoints
from app.modules.dms.presentation import endpoints as dms_endpoints
from app.modules.wfl.presentation import endpoints as wfl_endpoints
from app.modules.bi.presentation import endpoints as bi_endpoints
from app.modules.aud.presentation import endpoints as aud_endpoints
# Nuevos endpoints del módulo modulos
from app.modules.modulos.presentation import (
    endpoints_modulos as modulos_endpoints,
    endpoints_cliente_modulo,
    endpoints_secciones,
    endpoints_menus as modulos_menus_endpoints,
    endpoints_plantillas
)

api_router = APIRouter()

# ========================================
# ENDPOINTS DE AUTENTICACIÓN Y SEGURIDAD
# ========================================
api_router.include_router(
    auth_endpoints.router,
    prefix="/auth",
    tags=["Autenticación"]
)

api_router.include_router(
    endpoints_auth_config.router,
    prefix="/auth-config",
    tags=["Configuración de Autenticación"]
)

api_router.include_router(
    endpoints_sso.router,
    prefix="/sso",
    tags=["SSO - Single Sign On"]
)

# ========================================
# ENDPOINTS DE ADMINISTRACIÓN GLOBAL (SUPER ADMIN)
# ========================================
api_router.include_router(
    endpoints_clientes.router,
    prefix="/clientes",
    tags=["Clientes (Super Admin)"]
)

# Endpoints antiguos de módulos (deprecated - mantener por compatibilidad temporal)
api_router.include_router(
    endpoints_modulos.router,
    prefix="/modulos",
    tags=["Módulos (Super Admin) - Deprecated"]
)

# ========================================
# ENDPOINTS NUEVOS DE GESTIÓN DE MÓDULOS
# ========================================
api_router.include_router(
    modulos_endpoints.router,
    prefix="/modulos-v2",
    tags=["Módulos (Catálogo)"]
)

api_router.include_router(
    endpoints_cliente_modulo.router,
    prefix="/cliente-modulo",
    tags=["Activación de Módulos por Cliente"]
)

api_router.include_router(
    endpoints_secciones.router,
    prefix="/secciones",
    tags=["Secciones de Módulos"]
)

api_router.include_router(
    modulos_menus_endpoints.router,
    prefix="/modulos-menus",
    tags=["Menús de Módulos"]
)

api_router.include_router(
    endpoints_plantillas.router,
    prefix="/plantillas-roles",
    tags=["Plantillas de Roles"]
)

api_router.include_router(
    endpoints_conexiones.router,
    prefix="/conexiones",
    tags=["Conexiones BD (Super Admin)"]
)

# ========================================
# ENDPOINTS DE GESTIÓN DE USUARIOS Y ROLES
# ========================================
api_router.include_router(
    users_endpoints.router,
    prefix="/usuarios",
    tags=["Usuarios"]
)

api_router.include_router(
    rbac_endpoints.router, 
    prefix="/roles", 
    tags=["Roles"]
)

api_router.include_router(
    endpoints_permisos.router, 
    prefix="/permisos", 
    tags=["Permisos (Rol-Menú)"]
)

api_router.include_router(
    endpoints_permisos_catalogo.router,
    prefix="/permisos-catalogo",
    tags=["Permisos de negocio (RBAC)"]
)

# ========================================
# ENDPOINTS DE GESTIÓN DE MENÚS Y NAVEGACIÓN
# ========================================
api_router.include_router(
    menus_endpoints.router,
    prefix="/menus",
    tags=["Menus"]
)

# ========================================
# ENDPOINTS ORG (ORGANIZACIÓN ERP)
# ========================================
api_router.include_router(
    org_endpoints.router,
    prefix="/org",
    tags=["ORG - Organización"]
)

# ========================================
# ENDPOINTS INV (INVENTARIOS ERP)
# ========================================
api_router.include_router(
    inv_endpoints.router,
    prefix="/inv",
    tags=["INV - Inventarios"]
)

# ========================================
# ENDPOINTS PUR (COMPRAS ERP)
# ========================================
api_router.include_router(
    pur_endpoints.router,
    prefix="/pur",
    tags=["PUR - Compras"]
)

# ========================================
# ENDPOINTS SLS (VENTAS ERP)
# ========================================
api_router.include_router(
    sls_endpoints.router,
    prefix="/sls",
    tags=["SLS - Ventas"]
)

# ========================================
# ENDPOINTS INV_BILL (FACTURACIÓN ELECTRÓNICA)
# ========================================
api_router.include_router(
    invbill_endpoints.router,
    prefix="/inv-bill",
    tags=["INV_BILL - Facturación Electrónica"]
)

# ========================================
# ENDPOINTS PRC (GESTIÓN DE PRECIOS Y PROMOCIONES)
# ========================================
api_router.include_router(
    prc_endpoints.router,
    prefix="/prc",
    tags=["PRC - Precios y Promociones"]
)

# ========================================
# ENDPOINTS LOG (LOGÍSTICA Y DISTRIBUCIÓN)
# ========================================
api_router.include_router(
    log_endpoints.router,
    prefix="/log",
    tags=["LOG - Logística y Distribución"]
)

# ========================================
# ENDPOINTS FIN (FINANZAS Y CONTABILIDAD)
# ========================================
api_router.include_router(
    fin_endpoints.router,
    prefix="/fin",
    tags=["FIN - Finanzas y Contabilidad"]
)

# ========================================
# ENDPOINTS WMS (WAREHOUSE MANAGEMENT SYSTEM)
# ========================================
api_router.include_router(
    wms_endpoints.router,
    prefix="/wms",
    tags=["WMS - Gestión de Almacenes"]
)

# ========================================
# ENDPOINTS QMS (QUALITY MANAGEMENT SYSTEM)
# ========================================
api_router.include_router(
    qms_endpoints.router,
    prefix="/qms",
    tags=["QMS - Control de Calidad"]
)

# ========================================
# ENDPOINTS CRM (CUSTOMER RELATIONSHIP MANAGEMENT)
# ========================================
api_router.include_router(
    crm_endpoints.router,
    prefix="/crm",
    tags=["CRM - Gestión de Clientes"]
)

# ========================================
# ENDPOINTS POS (PUNTO DE VENTA)
# ========================================
api_router.include_router(
    pos_endpoints.router,
    prefix="/pos",
    tags=["POS - Punto de Venta"]
)

# ========================================
# ENDPOINTS HCM (PLANILLAS Y RRHH)
# ========================================
api_router.include_router(
    hcm_endpoints.router,
    prefix="/hcm",
    tags=["HCM - Planillas y RRHH"]
)

# ========================================
# ENDPOINTS MFG (MANUFACTURA Y PRODUCCIÓN)
# ========================================
api_router.include_router(
    mfg_endpoints.router,
    prefix="/mfg",
    tags=["MFG - Manufactura y Producción"]
)

# ========================================
# ENDPOINTS MRP (PLANEAMIENTO DE MATERIALES)
# ========================================
api_router.include_router(
    mrp_endpoints.router,
    prefix="/mrp",
    tags=["MRP - Planeamiento de Materiales"]
)

# ========================================
# ENDPOINTS MPS (PLAN MAESTRO DE PRODUCCIÓN)
# ========================================
api_router.include_router(
    mps_endpoints.router,
    prefix="/mps",
    tags=["MPS - Plan Maestro de Producción"]
)

# ========================================
# ENDPOINTS MNT (MANTENIMIENTO DE ACTIVOS)
# ========================================
api_router.include_router(
    mnt_endpoints.router,
    prefix="/mnt",
    tags=["MNT - Mantenimiento"]
)

# ========================================
# ENDPOINTS CST (COSTEO DE PRODUCTOS)
# ========================================
api_router.include_router(
    cst_endpoints.router,
    prefix="/cst",
    tags=["CST - Costeo de Productos"]
)

# ========================================
# ENDPOINTS TAX (LIBROS ELECTRÓNICOS / PLE SUNAT)
# ========================================
api_router.include_router(
    tax_endpoints.router,
    prefix="/tax",
    tags=["TAX - Libros Electrónicos"]
)

# ========================================
# ENDPOINTS BDG (PRESUPUESTOS)
# ========================================
api_router.include_router(
    bdg_endpoints.router,
    prefix="/bdg",
    tags=["BDG - Presupuestos"]
)

# ========================================
# ENDPOINTS PM (GESTIÓN DE PROYECTOS)
# ========================================
api_router.include_router(
    pm_endpoints.router,
    prefix="/pm",
    tags=["PM - Proyectos"]
)

# ========================================
# ENDPOINTS SVC (ÓRDENES DE SERVICIO)
# ========================================
api_router.include_router(
    svc_endpoints.router,
    prefix="/svc",
    tags=["SVC - Ordenes de Servicio"]
)

# ========================================
# ENDPOINTS TKT (MESA DE AYUDA / TICKETS)
# ========================================
api_router.include_router(
    tkt_endpoints.router,
    prefix="/tkt",
    tags=["TKT - Mesa de Ayuda"]
)

# ========================================
# ENDPOINTS DMS (GESTIÓN DOCUMENTAL)
# ========================================
api_router.include_router(
    dms_endpoints.router,
    prefix="/dms",
    tags=["DMS - Documentos"]
)

# ========================================
# ENDPOINTS WFL (FLUJOS DE TRABAJO)
# ========================================
api_router.include_router(
    wfl_endpoints.router,
    prefix="/wfl",
    tags=["WFL - Flujos de Trabajo"]
)

# ========================================
# ENDPOINTS BI (REPORTES & ANALYTICS)
# ========================================
api_router.include_router(
    bi_endpoints.router,
    prefix="/bi",
    tags=["BI - Reportes y Analytics"]
)

# ========================================
# ENDPOINTS AUD (AUDITORÍA Y TRAZABILIDAD)
# ========================================
api_router.include_router(
    aud_endpoints.router,
    prefix="/aud",
    tags=["AUD - Auditoría"]
)

api_router.include_router(
    endpoints_areas.router, 
    prefix="/areas", 
    tags=["Áreas de Menú"]
)


# ========================================
# ENDPOINTS DE SUPERADMIN (GESTIÓN GLOBAL)
# ========================================
api_router.include_router(
    superadmin_usuarios_endpoints.router,
    prefix="/superadmin/usuarios",
    tags=["Usuarios (Super Admin)"]
)

api_router.include_router(
    superadmin_auditoria_endpoints.router,
    prefix="/superadmin/auditoria",
    tags=["Auditoría (Super Admin)"]
)

# ========================================
# ENDPOINTS DE MÉTRICAS Y MONITOREO
# ========================================
from app.api import metrics_endpoint

api_router.include_router(
    metrics_endpoint.router,
    tags=["Métricas y Monitoreo"]
)