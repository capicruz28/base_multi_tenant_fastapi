# app/modules/modulos/presentation/endpoints_cliente_modulo.py
"""
Endpoints para la gestión de activación de módulos por cliente.

Este módulo proporciona una API REST completa para activar, desactivar y configurar
módulos específicos para cada cliente.

⚠️ CRÍTICO: Al activar un módulo, se aplican automáticamente las plantillas de roles.

Características principales:
- Activación/desactivación de módulos por cliente
- Configuración personalizada de módulos
- Gestión de límites y licencias
- Extensión de vencimientos
- Validación de dependencias
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.modules.modulos.presentation.schemas import (
    ClienteModuloRead, ClienteModuloCreate, ClienteModuloUpdate
)
from app.modules.modulos.application.services.cliente_modulo_service import ClienteModuloService
from app.core.exceptions import CustomException
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/cliente/{cliente_id}/",
    response_model=dict,
    summary="Listar módulos activos de un cliente",
    description="Obtiene todos los módulos activos para un cliente específico.",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def listar_modulos_activos_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Lista todos los módulos activos para un cliente."""
    try:
        modulos = await ClienteModuloService.obtener_modulos_activos_cliente(cliente_id)
        return {
            "success": True,
            "message": f"Módulos activos para cliente {cliente_id} obtenidos exitosamente.",
            "data": modulos
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/{cliente_modulo_id}/",
    response_model=dict,
    summary="Obtener detalle de módulo activo",
    description="Obtiene los detalles completos de un módulo activo específico.",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_modulo_activo(
    cliente_modulo_id: UUID = Path(..., description="ID del módulo activo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene un módulo activo específico por su ID."""
    try:
        modulo = await ClienteModuloService.obtener_modulo_activo_por_id(cliente_modulo_id)
        if not modulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo activo con ID {cliente_modulo_id} no encontrado."
            )
        return {
            "success": True,
            "message": "Módulo activo recuperado exitosamente.",
            "data": modulo
        }
    except HTTPException:
        raise
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/activar/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Activar módulo para un cliente",
    description="""
    Activa un módulo para un cliente específico.
    
    ⚠️ CRÍTICO: Al activar un módulo, se aplican automáticamente todas las plantillas
    de roles activas del módulo, creando los roles correspondientes para el cliente.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Validaciones:**
    - El módulo debe existir y estar activo en el catálogo
    - El cliente debe existir
    - No debe estar ya activado
    - Deben cumplirse las dependencias (módulos requeridos)
    
    **Respuestas:**
    - 201: Módulo activado exitosamente
    - 400: Datos de entrada inválidos o dependencias no cumplidas
    - 404: Módulo o cliente no encontrado
    - 409: Módulo ya está activado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def activar_modulo_cliente(
    modulo_data: ClienteModuloCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Activa un módulo para un cliente específico. Aplica automáticamente plantillas de roles."""
    logger.info(f"Solicitud POST /cliente-modulo/activar/ - cliente: {modulo_data.cliente_id}, módulo: {modulo_data.modulo_id}")
    
    try:
        # Agregar usuario que activa
        modulo_data.activado_por_usuario_id = current_user.usuario_id
        
        modulo_activo = await ClienteModuloService.activar_modulo_cliente(modulo_data)
        
        logger.info(f"Módulo {modulo_data.modulo_id} activado exitosamente para cliente {modulo_data.cliente_id}")
        
        return {
            "success": True,
            "message": f"Módulo activado exitosamente para el cliente. Las plantillas de roles han sido aplicadas automáticamente.",
            "data": modulo_activo
        }
    except CustomException as ce:
        logger.error(f"Error al activar módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al activar módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al activar módulo."
        )


@router.delete(
    "/cliente/{cliente_id}/modulo/{modulo_id}/",
    status_code=status.HTTP_200_OK,
    summary="Desactivar módulo para un cliente",
    description="""
    Desactiva un módulo para un cliente específico.
    Implementa desactivación lógica (soft delete).
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Validaciones:**
    - El módulo debe estar activado para el cliente
    - No se puede desactivar un módulo core
    
    **Respuestas:**
    - 200: Módulo desactivado exitosamente
    - 400: No se puede desactivar (validaciones)
    - 404: Módulo activo no encontrado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def desactivar_modulo_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Desactiva un módulo para un cliente específico."""
    logger.info(f"Solicitud DELETE /cliente-modulo/cliente/{cliente_id}/modulo/{modulo_id}/ recibida")
    
    try:
        await ClienteModuloService.desactivar_modulo_cliente(cliente_id, modulo_id)
        
        logger.info(f"Módulo {modulo_id} desactivado exitosamente para cliente {cliente_id}")
        
        return {
            "success": True,
            "message": f"Módulo desactivado exitosamente para el cliente.",
            "cliente_id": cliente_id,
            "modulo_id": modulo_id
        }
    except CustomException as ce:
        logger.error(f"Error al desactivar módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al desactivar módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al desactivar módulo."
        )


@router.put(
    "/cliente/{cliente_id}/modulo/{modulo_id}/configuracion/",
    response_model=dict,
    summary="Actualizar configuración de módulo activo",
    description="Actualiza la configuración personalizada de un módulo activo.",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def actualizar_configuracion(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    configuracion: Dict[str, Any] = Body(..., description="Configuración personalizada"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza la configuración personalizada de un módulo activo."""
    try:
        modulo = await ClienteModuloService.actualizar_configuracion(cliente_id, modulo_id, configuracion)
        return {
            "success": True,
            "message": "Configuración actualizada exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/cliente/{cliente_id}/modulo/{modulo_id}/limites/",
    response_model=dict,
    summary="Actualizar límites de módulo activo",
    description="Actualiza los límites de uso de un módulo activo.",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def actualizar_limites(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    limite_usuarios: Optional[int] = Body(None, description="Límite de usuarios"),
    limite_registros: Optional[int] = Body(None, description="Límite de registros"),
    limite_transacciones_mes: Optional[int] = Body(None, description="Límite de transacciones por mes"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza los límites de uso de un módulo activo."""
    try:
        modulo = await ClienteModuloService.actualizar_limites(
            cliente_id, modulo_id, limite_usuarios, limite_registros, limite_transacciones_mes
        )
        return {
            "success": True,
            "message": "Límites actualizados exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/cliente/{cliente_id}/modulo/{modulo_id}/extender-vencimiento/",
    response_model=dict,
    summary="Extender vencimiento de módulo activo",
    description="Extiende el vencimiento de un módulo activo agregando días.",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def extender_vencimiento(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    dias: int = Body(..., ge=1, description="Días a extender"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Extiende el vencimiento de un módulo activo."""
    try:
        modulo = await ClienteModuloService.extender_vencimiento(cliente_id, modulo_id, dias)
        return {
            "success": True,
            "message": f"Vencimiento extendido {dias} días exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/cliente/{cliente_id}/modulo/{modulo_id}/validar-licencia/",
    response_model=dict,
    summary="Validar licencia de módulo activo",
    description="Valida la licencia de un módulo (está activo + no vencido).",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def validar_licencia(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Valida la licencia de un módulo activo."""
    try:
        validacion = await ClienteModuloService.validar_licencia(cliente_id, modulo_id)
        return {
            "success": True,
            "message": "Validación de licencia completada.",
            "data": validacion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

