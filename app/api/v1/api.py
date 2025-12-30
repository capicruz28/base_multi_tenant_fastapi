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
from app.modules.rbac.presentation import endpoints_permisos
from app.modules.menus.presentation import endpoints as menus_endpoints
from app.modules.menus.presentation import endpoints_areas
from app.modules.tenant.presentation import endpoints_clientes, endpoints_modulos, endpoints_conexiones
from app.modules.superadmin.presentation import endpoints_usuarios as superadmin_usuarios_endpoints
from app.modules.superadmin.presentation import endpoints_auditoria as superadmin_auditoria_endpoints
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

# ========================================
# ENDPOINTS DE GESTIÓN DE MENÚS Y NAVEGACIÓN
# ========================================
api_router.include_router(
    menus_endpoints.router,
    prefix="/menus",
    tags=["Menus"]
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