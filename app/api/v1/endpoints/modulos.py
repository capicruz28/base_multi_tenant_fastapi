# app/api/v1/endpoints/modulos.py
"""
Módulo de endpoints para la gestión del catálogo de módulos en arquitectura multi-tenant.

Este módulo proporciona una API REST completa para operaciones sobre el catálogo de módulos,
incluyendo consulta del catálogo global y gestión de activación por cliente.

Características principales:
- Autenticación JWT con requerimiento de nivel de acceso para operaciones de gestión.
- Consulta pública del catálogo de módulos (para usuarios autenticados).
- Activación y configuración de módulos específicos por cliente.
- Validaciones de límites y configuraciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Dict, Any, Optional
import logging
import json

from app.schemas.modulo import ModuloRead, ModuloConInfoActivacion
from app.schemas.modulo_activo import ModuloActivoRead, ModuloActivoCreate, ModuloActivoUpdate
from app.services.modulo_service import ModuloService
from app.services.modulo_activo_service import ModuloActivoService
from app.api.deps import get_current_active_user
from app.core.level_authorization import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=List[ModuloRead],
    summary="Listar catálogo de módulos",
    description="""
    Obtiene la lista de todos los módulos disponibles en el sistema.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de query:**
    - skip: Número de registros a saltar (paginación)
    - limit: Límite de registros a retornar (paginación)
    - solo_activos: Filtrar solo módulos activos
    
    **Respuestas:**
    - 200: Catálogo de módulos recuperado exitosamente
    - 500: Error interno del servidor
    """
)
async def listar_modulos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True, description="Filtrar solo módulos activos"),
    current_user=Depends(get_current_active_user)
):
    """
    Lista todos los módulos del catálogo del sistema.
    """
    logger.info(f"Solicitud GET /modulos/ recibida - skip: {skip}, limit: {limit}, solo_activos: {solo_activos}")
    try:
        modulos = await ModuloService.obtener_modulos(
            skip=skip, 
            limit=limit, 
            solo_activos=solo_activos
        )
        logger.info(f"Catálogo de módulos recuperado: {len(modulos)} módulos")
        return modulos
    except Exception as e:
        logger.exception(f"Error inesperado en listar_modulos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al listar los módulos."
        )


@router.get(
    "/{modulo_id}",
    response_model=ModuloRead,
    summary="Obtener detalle de un módulo",
    description="""
    Obtiene los detalles completos de un módulo específico.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de ruta:**
    - modulo_id: ID del módulo a consultar
    
    **Respuestas:**
    - 200: Módulo encontrado y devuelto
    - 404: Módulo no encontrado
    - 500: Error interno del servidor
    """
)
async def obtener_modulo(
    modulo_id: int,
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un módulo por su ID.
    """
    logger.info(f"Solicitud GET /modulos/{modulo_id} recibida")
    try:
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if modulo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con ID {modulo_id} no encontrado."
            )
        return modulo
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_modulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener el módulo."
        )


@router.get(
    "/clientes/{cliente_id}/modulos",
    response_model=List[ModuloConInfoActivacion],
    summary="Listar módulos de un cliente",
    description="""
    Obtiene la lista de módulos con información de activación para un cliente específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Lista de módulos con estado de activación
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def listar_modulos_cliente(
    cliente_id: int,
    current_user=Depends(get_current_active_user)
):
    """
    Lista todos los módulos con información de activación para un cliente.
    """
    logger.info(f"Solicitud GET /modulos/clientes/{cliente_id}/modulos recibida")
    try:
        modulos_con_activacion = await ModuloService.obtener_modulos_por_cliente(cliente_id)
        
        # Convertir a esquema con información de activación
        modulos_response = []
        for modulo_data in modulos_con_activacion:
            modulo_response = ModuloConInfoActivacion(
                modulo_id=modulo_data["modulo_id"],
                codigo_modulo=modulo_data["codigo_modulo"],
                nombre=modulo_data["nombre"],
                descripcion=modulo_data["descripcion"],
                icono=modulo_data["icono"],
                es_modulo_core=modulo_data["es_modulo_core"],
                requiere_licencia=modulo_data["requiere_licencia"],
                orden=modulo_data["orden"],
                es_activo=modulo_data["modulo_activo"],
                fecha_creacion=modulo_data.get("fecha_creacion"),
                activo_en_cliente=modulo_data["activo_en_cliente"],
                cliente_modulo_activo_id=modulo_data.get("cliente_modulo_activo_id"),
                fecha_activacion=modulo_data.get("fecha_activacion"),
                configuracion_json=modulo_data.get("configuracion_json"),
                limite_usuarios=modulo_data.get("limite_usuarios"),
                limite_registros=modulo_data.get("limite_registros")
            )
            modulos_response.append(modulo_response)
        
        logger.info(f"Módulos con activación recuperados para cliente {cliente_id}: {len(modulos_response)} módulos")
        return modulos_response
        
    except Exception as e:
        logger.exception(f"Error inesperado en listar_modulos_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al listar los módulos del cliente."
        )


@router.post(
    "/clientes/{cliente_id}/modulos/{modulo_id}",
    response_model=ModuloActivoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Activar módulo para cliente",
    description="""
    Activa un módulo específico para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo a activar
    
    **Parámetros de body:**
    - configuracion: Configuración específica del módulo (opcional)
    - limite_usuarios: Límite de usuarios (opcional)
    - limite_registros: Límite de registros (opcional)
    - fecha_vencimiento: Fecha de vencimiento (opcional)
    
    **Respuestas:**
    - 201: Módulo activado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente o módulo no encontrado
    - 409: Módulo ya está activado para este cliente
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def activar_modulo_cliente(
    cliente_id: int,
    modulo_id: int,
    configuracion: Optional[Dict[str, Any]] = Body(None),
    limite_usuarios: Optional[int] = Body(None),
    limite_registros: Optional[int] = Body(None),
    fecha_vencimiento: Optional[str] = Body(None),
    current_user=Depends(get_current_active_user)
):
    """
    Activa un módulo para un cliente específico.
    """
    logger.info(f"Solicitud POST /modulos/clientes/{cliente_id}/modulos/{modulo_id} recibida")
    try:
        modulo_activado = await ModuloActivoService.activar_modulo_cliente(
            cliente_id=cliente_id,
            modulo_id=modulo_id,
            configuracion=configuracion,
            limite_usuarios=limite_usuarios,
            limite_registros=limite_registros,
            fecha_vencimiento=fecha_vencimiento
        )
        
        logger.info(f"Módulo {modulo_id} activado exitosamente para cliente {cliente_id}")
        return modulo_activado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en activar_modulo_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al activar el módulo."
        )


@router.delete(
    "/clientes/{cliente_id}/modulos/{modulo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar módulo para cliente",
    description="""
    Desactiva un módulo específico para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo a desactivar
    
    **Respuestas:**
    - 204: Módulo desactivado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Módulo no encontrado o no activo para este cliente
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def desactivar_modulo_cliente(
    cliente_id: int, 
    modulo_id: int,
    current_user=Depends(get_current_active_user)
):
    """
    Desactiva un módulo para un cliente específico.
    """
    logger.info(f"Solicitud DELETE /modulos/clientes/{cliente_id}/modulos/{modulo_id} recibida")
    try:
        success = await ModuloActivoService.desactivar_modulo_cliente(cliente_id, modulo_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo desactivar el módulo."
            )
            
        logger.info(f"Módulo {modulo_id} desactivado exitosamente para cliente {cliente_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en desactivar_modulo_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al desactivar el módulo."
        )


@router.put(
    "/clientes/{cliente_id}/modulos/{modulo_id}",
    response_model=ModuloActivoRead,
    summary="Actualizar configuración de módulo activo",
    description="""
    Actualiza la configuración de un módulo activo para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo
    
    **Parámetros de body:**
    - configuracion: Nueva configuración (opcional)
    - limite_usuarios: Nuevo límite de usuarios (opcional)
    - limite_registros: Nuevo límite de registros (opcional)
    - fecha_vencimiento: Nueva fecha de vencimiento (opcional)
    
    **Respuestas:**
    - 200: Configuración actualizada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Módulo activo no encontrado
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def actualizar_config_modulo_cliente(
    cliente_id: int,
    modulo_id: int,
    configuracion: Optional[Dict[str, Any]] = Body(None),
    limite_usuarios: Optional[int] = Body(None),
    limite_registros: Optional[int] = Body(None),
    fecha_vencimiento: Optional[str] = Body(None),
    current_user=Depends(get_current_active_user)
):
    """
    Actualiza la configuración de un módulo activo para un cliente.
    """
    logger.info(f"Solicitud PUT /modulos/clientes/{cliente_id}/modulos/{modulo_id} recibida")
    try:
        # Obtener el ID del módulo activo
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_cliente(cliente_id, modulo_id)
        if not modulo_activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El módulo {modulo_id} no está activo para el cliente {cliente_id}."
            )
        
        modulo_actualizado = await ModuloActivoService.actualizar_config_modulo(
            modulo_activo_id=modulo_activo.cliente_modulo_activo_id,
            configuracion=configuracion,
            limite_usuarios=limite_usuarios,
            limite_registros=limite_registros,
            fecha_vencimiento=fecha_vencimiento
        )
        
        logger.info(f"Configuración del módulo {modulo_id} actualizada para cliente {cliente_id}")
        return modulo_actualizado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_config_modulo_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar la configuración del módulo."
        )

@router.get("/test")
async def test_modulos_endpoint():
    """Endpoint temporal para verificar que el router funciona"""
    return {
        "message": "✅ Endpoint de módulos funcionando",
        "status": "active", 
        "timestamp": "2024-01-01T00:00:00Z"
    }