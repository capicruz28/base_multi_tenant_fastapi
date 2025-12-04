"""
Módulo de endpoints para la gestión de configuraciones de autenticación en arquitectura multi-tenant.

Este módulo proporciona una API REST completa para operaciones sobre políticas de autenticación
por cliente, incluyendo configuración de políticas de contraseñas, 2FA, control de sesiones
y restricciones de acceso.

Características principales:
- Autenticación JWT con requerimiento de rol 'SUPER_ADMIN' para todas las operaciones.
- Validación de coherencia entre políticas de seguridad.
- Configuración granular de políticas por cliente.
- Valores por defecto coherentes con mejores prácticas.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from typing import Dict, Any
from uuid import UUID
import logging

from app.modules.auth.presentation.schemas import AuthConfigRead, AuthConfigUpdate
from app.modules.auth.application.services.auth_config_service import AuthConfigService
from app.api.deps import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencia para requerir rol SUPER_ADMIN
require_super_admin = RoleChecker(["SUPER_ADMIN"])


@router.get(
    "/clientes/{cliente_id}",
    response_model=AuthConfigRead,
    summary="Obtener configuración de autenticación",
    description="""
    Obtiene la configuración de autenticación para un cliente específico.
    Si no existe, crea una configuración por defecto.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Configuración de autenticación recuperada/creada
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def obtener_config_auth_cliente(cliente_id: UUID = Path(..., description="ID del cliente")):
    """
    Obtiene la configuración de autenticación para un cliente.
    """
    logger.info(f"Solicitud GET /auth-config/clientes/{cliente_id} recibida")
    try:
        config = await AuthConfigService.obtener_config_cliente(cliente_id)
        logger.info(f"Configuración de autenticación recuperada para cliente {cliente_id}")
        return config
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_config_auth_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la configuración de autenticación."
        )


@router.put(
    "/clientes/{cliente_id}",
    response_model=AuthConfigRead,
    summary="Actualizar configuración de autenticación",
    description="""
    Actualiza la configuración de autenticación para un cliente específico.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Configuración actualizada exitosamente
    - 404: Cliente no encontrado
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def actualizar_config_auth_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    config_data: AuthConfigUpdate = Body(...)
):
    """
    Actualiza la configuración de autenticación para un cliente.
    """
    logger.info(f"Solicitud PUT /auth-config/clientes/{cliente_id} recibida")
    try:
        config_actualizada = await AuthConfigService.actualizar_config_cliente(cliente_id, config_data)
        logger.info(f"Configuración de autenticación actualizada para cliente {cliente_id}")
        return config_actualizada
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_config_auth_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar la configuración de autenticación."
        )


@router.get(
    "/global",
    response_model=AuthConfigRead,
    summary="Obtener configuración global por defecto",
    description="""
    Obtiene la configuración de autenticación por defecto del sistema.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Respuestas:**
    - 200: Configuración global por defecto
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def obtener_config_auth_global():
    """
    Obtiene la configuración de autenticación global por defecto.
    """
    logger.info("Solicitud GET /auth-config/global recibida")
    try:
        config_global = await AuthConfigService.obtener_config_global()
        logger.info("Configuración global de autenticación recuperada")
        return config_global
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_config_auth_global: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la configuración global de autenticación."
        )