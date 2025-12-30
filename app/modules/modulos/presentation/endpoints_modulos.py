# app/modules/modulos/presentation/endpoints_modulos.py
"""
Endpoints para la gestión del catálogo de módulos ERP.

Este módulo proporciona una API REST completa para operaciones sobre el catálogo de módulos,
incluyendo consulta del catálogo global y gestión completa de módulos.

Características principales:
- Autenticación JWT con requerimiento de nivel de acceso para operaciones de gestión
- Consulta pública del catálogo de módulos (para usuarios autenticados)
- Solo SUPER ADMIN puede crear/editar/eliminar módulos
- Validaciones de dependencias entre módulos
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import List, Optional
from uuid import UUID
import logging
import math

from app.modules.modulos.presentation.schemas import (
    ModuloRead, ModuloCreate, ModuloUpdate, ModuloResponse, PaginatedModuloResponse
)
from app.modules.modulos.application.services.modulo_service import ModuloService
from app.core.exceptions import CustomException
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedModuloResponse,
    summary="Listar catálogo de módulos con paginación",
    description="""
    Obtiene la lista de todos los módulos disponibles en el sistema con paginación completa.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de query:**
    - skip: Número de registros a saltar (paginación)
    - limit: Límite de registros a retornar (paginación)
    - solo_activos: Filtrar solo módulos activos (por defecto: False, devuelve todos)
    - categoria: Filtrar por categoría
    
    **Respuestas:**
    - 200: Catálogo de módulos recuperado exitosamente con metadata de paginación
    - 500: Error interno del servidor
    """
)
async def listar_modulos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(False, description="Filtrar solo módulos activos (False = devuelve todos)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Lista todos los módulos del catálogo del sistema con paginación completa."""
    logger.info(f"Solicitud GET /modulos/ recibida - skip: {skip}, limit: {limit}, solo_activos: {solo_activos}")
    
    try:
        modulos = await ModuloService.obtener_modulos(
            skip=skip, 
            limit=limit, 
            solo_activos=solo_activos,
            categoria=categoria
        )
        
        # Contar total (simplificado - en producción debería ser una query separada)
        total = len(modulos)  # TODO: Implementar contar_modulos en el servicio
        
        # Calcular metadata de paginación
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        logger.info(f"Catálogo de módulos recuperado: {len(modulos)} módulos")
        
        return {
            "success": True,
            "message": "Catálogo de módulos recuperado exitosamente.",
            "data": modulos,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "total_pages": total_pages,
                "current_page": current_page,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            }
        }
    except CustomException as ce:
        logger.error(f"Error al listar módulos: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al listar módulos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al listar módulos."
        )


@router.get(
    "/{modulo_id}/",
    response_model=ModuloResponse,
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
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene un módulo específico por su ID."""
    logger.info(f"Solicitud GET /modulos/{modulo_id}/ recibida")
    
    try:
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con ID {modulo_id} no encontrado."
            )
        
        logger.info(f"Módulo {modulo_id} recuperado exitosamente")
        
        return {
            "success": True,
            "message": "Módulo recuperado exitosamente.",
            "data": modulo
        }
    except HTTPException:
        raise
    except CustomException as ce:
        logger.error(f"Error al obtener módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al obtener módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener módulo."
        )


@router.get(
    "/codigo/{codigo}/",
    response_model=ModuloResponse,
    summary="Obtener módulo por código",
    description="""
    Obtiene un módulo específico por su código único.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de ruta:**
    - codigo: Código único del módulo (ej: 'LOGISTICA', 'ALMACEN')
    
    **Respuestas:**
    - 200: Módulo encontrado y devuelto
    - 404: Módulo no encontrado
    - 500: Error interno del servidor
    """
)
async def obtener_modulo_por_codigo(
    codigo: str = Path(..., description="Código del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene un módulo específico por su código único."""
    logger.info(f"Solicitud GET /modulos/codigo/{codigo}/ recibida")
    
    try:
        modulo = await ModuloService.obtener_modulo_por_codigo(codigo.upper())
        if not modulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con código '{codigo}' no encontrado."
            )
        
        return {
            "success": True,
            "message": "Módulo recuperado exitosamente.",
            "data": modulo
        }
    except HTTPException:
        raise
    except CustomException as ce:
        logger.error(f"Error al obtener módulo por código: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al obtener módulo por código: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener módulo."
        )


@router.post(
    "/",
    response_model=ModuloResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo módulo",
    description="""
    Crea un nuevo módulo en el catálogo del sistema.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Validaciones:**
    - El código del módulo debe ser único
    - Todos los campos requeridos deben estar presentes
    - Validación de dependencias si se proporcionan
    
    **Respuestas:**
    - 201: Módulo creado exitosamente
    - 400: Datos de entrada inválidos
    - 409: Código de módulo ya existe
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def crear_modulo(
    modulo_data: ModuloCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Crea un nuevo módulo en el catálogo del sistema. Solo accesible para super administradores."""
    logger.info(f"Solicitud POST /modulos/ recibida - nombre: {modulo_data.nombre}")
    
    try:
        modulo = await ModuloService.crear_modulo(modulo_data)
        
        logger.info(f"Módulo creado exitosamente con ID: {modulo.modulo_id}")
        
        return {
            "success": True,
            "message": f"Módulo '{modulo.nombre}' creado exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        logger.error(f"Error al crear módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al crear módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear módulo."
        )


@router.put(
    "/{modulo_id}/",
    response_model=ModuloResponse,
    summary="Actualizar módulo existente",
    description="""
    Actualiza un módulo existente en el catálogo del sistema.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Validaciones:**
    - El módulo debe existir
    - Si se actualiza el código, debe ser único
    - Validación de dependencias si se actualizan
    
    **Respuestas:**
    - 200: Módulo actualizado exitosamente
    - 400: Datos de entrada inválidos
    - 404: Módulo no encontrado
    - 409: Código de módulo ya existe
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def actualizar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    modulo_data: ModuloUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza un módulo existente en el catálogo del sistema. Solo accesible para super administradores."""
    logger.info(f"Solicitud PUT /modulos/{modulo_id}/ recibida")
    
    try:
        modulo = await ModuloService.actualizar_modulo(modulo_id, modulo_data)
        
        logger.info(f"Módulo {modulo_id} actualizado exitosamente")
        
        return {
            "success": True,
            "message": f"Módulo '{modulo.nombre}' actualizado exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        logger.error(f"Error al actualizar módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar módulo."
        )


@router.delete(
    "/{modulo_id}/",
    status_code=status.HTTP_200_OK,
    summary="Eliminar módulo",
    description="""
    Elimina (desactiva) un módulo del catálogo del sistema.
    Implementa eliminación lógica (soft delete).
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Validaciones:**
    - El módulo debe existir
    - No se puede eliminar un módulo core
    - No se puede eliminar un módulo activo para algún cliente
    
    **Respuestas:**
    - 200: Módulo eliminado exitosamente
    - 400: No se puede eliminar el módulo (validaciones)
    - 404: Módulo no encontrado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def eliminar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Elimina (desactiva) un módulo del catálogo del sistema. Solo accesible para super administradores."""
    logger.info(f"Solicitud DELETE /modulos/{modulo_id}/ recibida")
    
    try:
        await ModuloService.eliminar_modulo(modulo_id)
        
        logger.info(f"Módulo {modulo_id} eliminado exitosamente")
        
        return {
            "success": True,
            "message": f"Módulo con ID {modulo_id} eliminado exitosamente.",
            "modulo_id": modulo_id
        }
    except CustomException as ce:
        logger.error(f"Error al eliminar módulo: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al eliminar módulo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar módulo."
        )


@router.patch(
    "/{modulo_id}/activar/",
    response_model=ModuloResponse,
    summary="Activar módulo",
    description="Activa un módulo del catálogo del sistema."
)
@require_super_admin()
async def activar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Activa un módulo del catálogo."""
    try:
        modulo = await ModuloService.activar_modulo(modulo_id)
        return {
            "success": True,
            "message": f"Módulo '{modulo.nombre}' activado exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{modulo_id}/desactivar/",
    response_model=ModuloResponse,
    summary="Desactivar módulo",
    description="Desactiva un módulo del catálogo del sistema."
)
@require_super_admin()
async def desactivar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Desactiva un módulo del catálogo."""
    try:
        modulo = await ModuloService.desactivar_modulo(modulo_id)
        return {
            "success": True,
            "message": f"Módulo '{modulo.nombre}' desactivado exitosamente.",
            "data": modulo
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/{modulo_id}/dependencias/",
    response_model=dict,
    summary="Validar dependencias de un módulo",
    description="Obtiene información sobre las dependencias de un módulo."
)
async def obtener_dependencias(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene información sobre las dependencias de un módulo."""
    try:
        dependencias = await ModuloService.validar_dependencias(modulo_id)
        return {
            "success": True,
            "message": "Dependencias obtenidas exitosamente.",
            "data": dependencias
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/disponibles/{cliente_id}/",
    response_model=dict,
    summary="Obtener módulos disponibles para un cliente",
    description="Obtiene los módulos que aún no están activados para un cliente."
)
async def obtener_modulos_disponibles(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene módulos disponibles para un cliente."""
    try:
        modulos = await ModuloService.obtener_modulos_disponibles_cliente(cliente_id)
        return {
            "success": True,
            "message": f"Módulos disponibles para cliente {cliente_id} obtenidos exitosamente.",
            "data": modulos
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

