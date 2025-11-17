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
from app.api.v1.endpoints import (
    usuarios, auth, menus, roles, permisos, areas, autorizacion,
    clientes, modulos, conexiones, auth_config
)

api_router = APIRouter()

# ========================================
# ENDPOINTS DE AUTENTICACIÓN Y SEGURIDAD
# ========================================
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
)

api_router.include_router(
    auth_config.router,
    prefix="/auth-config",
    tags=["Configuración de Autenticación"]
)

# ========================================
# ENDPOINTS DE ADMINISTRACIÓN GLOBAL (SUPER ADMIN)
# ========================================
api_router.include_router(
    clientes.router,
    prefix="/clientes",
    tags=["Clientes (Super Admin)"]
)

api_router.include_router(
    modulos.router,
    prefix="/modulos",
    tags=["Módulos (Super Admin)"]
)

api_router.include_router(
    conexiones.router,
    prefix="/conexiones",
    tags=["Conexiones BD (Super Admin)"]
)

# ========================================
# ENDPOINTS DE GESTIÓN DE USUARIOS Y ROLES
# ========================================
api_router.include_router(
    usuarios.router,
    prefix="/usuarios",
    tags=["Usuarios"]
)

api_router.include_router(
    roles.router, 
    prefix="/roles", 
    tags=["Roles"]
)

api_router.include_router(
    permisos.router, 
    prefix="/permisos", 
    tags=["Permisos (Rol-Menú)"]
)

# ========================================
# ENDPOINTS DE GESTIÓN DE MENÚS Y NAVEGACIÓN
# ========================================
api_router.include_router(
    menus.router,
    prefix="/menus",
    tags=["Menus"]
)

api_router.include_router(
    areas.router, 
    prefix="/areas", 
    tags=["Áreas de Menú"]
)

# ========================================
# ENDPOINTS DE LÓGICA DE NEGOCIO ESPECÍFICA
# ========================================
api_router.include_router(
    autorizacion.router,
    prefix="/autorizacion",
    tags=["Autorización de Procesos"]
)