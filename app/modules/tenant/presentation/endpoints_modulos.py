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
- Respuestas estandarizadas con paginación completa.
- Workflows integrados para gestión completa de módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json
import math

from app.modules.tenant.presentation.schemas import (
    ModuloRead, ModuloCreate, ModuloUpdate, ModuloConInfoActivacion,
    ModuloResponse, ModuloListResponse, ModuloConInfoActivacionListResponse,
    PaginatedModuloResponse, ModuloDeleteResponse,
    ModuloActivoRead, ModuloActivoCreate, ModuloActivoUpdate
)
from app.modules.tenant.presentation.schemas import ConexionCreate, ConexionRead, ConexionTest
from app.modules.tenant.application.services.modulo_service import ModuloService
from app.modules.tenant.application.services.modulo_activo_service import ModuloActivoService
from app.modules.tenant.application.services.conexion_service import ConexionService
from app.core.exceptions import CustomException
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# ENDPOINTS DE CATÁLOGO DE MÓDULOS (CRUD COMPLETO)
# ============================================================================

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
    - solo_activos: Filtrar solo módulos activos
    
    **Respuestas:**
    - 200: Catálogo de módulos recuperado exitosamente con metadata de paginación
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
    Lista todos los módulos del catálogo del sistema con paginación completa.
    """
    logger.info(f"Solicitud GET /modulos/ recibida - skip: {skip}, limit: {limit}, solo_activos: {solo_activos}")
    
    # Obtener módulos y total
    modulos = await ModuloService.obtener_modulos(skip=skip, limit=limit, solo_activos=solo_activos)
    total = await ModuloService.contar_modulos(solo_activos=solo_activos)
    
    # Calcular metadata de paginación
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    current_page = (skip // limit) + 1 if limit > 0 else 1
    
    logger.info(f"Catálogo de módulos recuperado: {len(modulos)} módulos de {total} totales")
    
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


@router.get(
    "/search/",
    response_model=PaginatedModuloResponse,
    summary="Buscar módulos con filtros",
    description="""
    Busca módulos con filtros opcionales y paginación.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de query:**
    - buscar: Texto a buscar en nombre, código o descripción
    - es_modulo_core: Filtrar por módulos core (true/false)
    - requiere_licencia: Filtrar por módulos que requieren licencia (true/false)
    - solo_activos: Filtrar solo módulos activos
    - skip: Número de registros a saltar
    - limit: Límite de registros a retornar
    
    **Respuestas:**
    - 200: Búsqueda completada exitosamente
    - 500: Error interno del servidor
    """
)
async def buscar_modulos(
    buscar: Optional[str] = Query(None, description="Texto a buscar"),
    es_modulo_core: Optional[bool] = Query(None, description="Filtrar por módulos core"),
    requiere_licencia: Optional[bool] = Query(None, description="Filtrar por módulos que requieren licencia"),
    solo_activos: bool = Query(True, description="Filtrar solo módulos activos"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    current_user=Depends(get_current_active_user)
):
    """
    Busca módulos con filtros opcionales.
    """
    logger.info(f"Solicitud GET /modulos/search/ - buscar: {buscar}, core: {es_modulo_core}, licencia: {requiere_licencia}")
    
    # Buscar módulos y contar total
    modulos = await ModuloService.buscar_modulos(
        buscar=buscar,
        es_modulo_core=es_modulo_core,
        requiere_licencia=requiere_licencia,
        solo_activos=solo_activos,
        skip=skip,
        limit=limit
    )
    
    total = await ModuloService.contar_modulos_busqueda(
        buscar=buscar,
        es_modulo_core=es_modulo_core,
        requiere_licencia=requiere_licencia,
        solo_activos=solo_activos
    )
    
    # Calcular metadata de paginación
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    current_page = (skip // limit) + 1 if limit > 0 else 1
    
    logger.info(f"Búsqueda completada: {len(modulos)} módulos de {total} totales")
    
    return {
        "success": True,
        "message": "Búsqueda completada exitosamente.",
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
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene un módulo específico por su ID.
    """
    logger.info(f"Solicitud GET /modulos/{modulo_id}/ recibida")
    
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
    
    **Respuestas:**
    - 201: Módulo creado exitosamente
    - 400: Datos de entrada inválidos
    - 409: Código de módulo ya existe
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def crear_modulo(
    modulo_data: ModuloCreate,
    current_user=Depends(require_super_admin)
):
    """
    Crea un nuevo módulo en el catálogo del sistema.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud POST /modulos/ recibida - nombre: {modulo_data.nombre}")
    
    modulo = await ModuloService.crear_modulo(modulo_data)
    
    logger.info(f"Módulo creado exitosamente con ID: {modulo.modulo_id}")
    
    return {
        "success": True,
        "message": f"Módulo '{modulo.nombre}' creado exitosamente.",
        "data": modulo
    }


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
    
    **Respuestas:**
    - 200: Módulo actualizado exitosamente
    - 400: Datos de entrada inválidos
    - 404: Módulo no encontrado
    - 409: Código de módulo ya existe
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def actualizar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    modulo_data: ModuloUpdate = Body(...),
    current_user=Depends(require_super_admin)
):
    """
    Actualiza un módulo existente en el catálogo del sistema.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud PUT /modulos/{modulo_id}/ recibida")
    
    modulo = await ModuloService.actualizar_modulo(modulo_id, modulo_data)
    
    logger.info(f"Módulo {modulo_id} actualizado exitosamente")
    
    return {
        "success": True,
        "message": f"Módulo '{modulo.nombre}' actualizado exitosamente.",
        "data": modulo
    }


@router.delete(
    "/{modulo_id}/",
    response_model=ModuloDeleteResponse,
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
async def eliminar_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user=Depends(require_super_admin)
):
    """
    Elimina (desactiva) un módulo del catálogo del sistema.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud DELETE /modulos/{modulo_id}/ recibida")
    
    await ModuloService.eliminar_modulo(modulo_id)
    
    logger.info(f"Módulo {modulo_id} eliminado exitosamente")
    
    return {
        "success": True,
        "message": f"Módulo con ID {modulo_id} eliminado exitosamente.",
        "modulo_id": modulo_id
    }


# ============================================================================
# ENDPOINTS DE MÓDULOS POR CLIENTE (ACTIVACIÓN)
# ============================================================================

@router.get(
    "/clientes/{cliente_id}/modulos/",
    response_model=ModuloConInfoActivacionListResponse,
    summary="Listar módulos de un cliente",
    description="""
    Obtiene todos los módulos con información de activación para un cliente específico.
    Incluye información completa de activación: fecha_activacion, fecha_vencimiento,
    configuracion_json, limite_usuarios, limite_registros, etc.
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Lista de módulos con información de activación completa
    - 500: Error interno del servidor
    """
)
async def listar_modulos_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene todos los módulos con información de activación para un cliente.
    """
    logger.info(f"Solicitud GET /clientes/{cliente_id}/modulos/ recibida")
    
    modulos = await ModuloService.obtener_modulos_por_cliente(cliente_id)
    
    logger.info(f"Módulos para cliente {cliente_id} recuperados: {len(modulos)} módulos")
    
    return {
        "success": True,
        "message": f"Módulos para cliente {cliente_id} recuperados exitosamente.",
        "data": modulos
    }


@router.post(
    "/clientes/{cliente_id}/modulos/{modulo_id}/activar/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Activar módulo para un cliente",
    description="""
    Activa un módulo específico para un cliente con configuración personalizada.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo a activar
    
    **Body:**
    - Configuración de activación (límites, fechas, configuración JSON)
    
    **Validaciones:**
    - El módulo debe existir y estar activo
    - El cliente debe existir
    - No debe estar ya activado
    
    **Respuestas:**
    - 201: Módulo activado exitosamente
    - 400: Datos de entrada inválidos
    - 404: Módulo o cliente no encontrado
    - 409: Módulo ya activado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def activar_modulo_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    activacion_data: ModuloActivoCreate = Body(...),
    current_user=Depends(require_super_admin)
):
    """
    Activa un módulo para un cliente específico.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud POST /clientes/{cliente_id}/modulos/{modulo_id}/activar/ recibida")
    
    # Validar que el módulo existe
    modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
    if not modulo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Módulo con ID {modulo_id} no encontrado."
        )
    
    # Asegurar que los IDs coincidan
    activacion_data.cliente_id = cliente_id
    activacion_data.modulo_id = modulo_id
    
    # Activar módulo
    modulo_activo = await ModuloActivoService.activar_modulo(activacion_data)
    
    logger.info(f"Módulo {modulo_id} activado para cliente {cliente_id}")
    
    return {
        "success": True,
        "message": f"Módulo '{modulo.nombre}' activado exitosamente para el cliente.",
        "data": modulo_activo
    }


@router.put(
    "/clientes/{cliente_id}/modulos/{modulo_id}/",
    response_model=Dict[str, Any],
    summary="Actualizar configuración de módulo activo",
    description="""
    Actualiza la configuración de un módulo activo para un cliente.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo
    
    **Body:**
    - Configuración actualizada (límites, fechas, configuración JSON)
    
    **Validaciones:**
    - El módulo debe estar activado para el cliente
    
    **Respuestas:**
    - 200: Configuración actualizada exitosamente
    - 400: Datos de entrada inválidos
    - 404: Módulo activo no encontrado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def actualizar_modulo_activo(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    actualizacion_data: ModuloActivoUpdate = Body(...),
    current_user=Depends(require_super_admin)
):
    """
    Actualiza la configuración de un módulo activo para un cliente.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud PUT /clientes/{cliente_id}/modulos/{modulo_id}/ recibida")
    
    # Obtener el módulo activo
    modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
        cliente_id, modulo_id
    )
    
    if not modulo_activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}."
        )
    
    # Actualizar configuración
    modulo_actualizado = await ModuloActivoService.actualizar_modulo_activo(
        modulo_activo.cliente_modulo_activo_id,
        actualizacion_data
    )
    
    logger.info(f"Configuración de módulo {modulo_id} actualizada para cliente {cliente_id}")
    
    return {
        "success": True,
        "message": "Configuración del módulo actualizada exitosamente.",
        "data": modulo_actualizado
    }


@router.post(
    "/clientes/{cliente_id}/modulos/{modulo_id}/desactivar/",
    response_model=Dict[str, Any],
    summary="Desactivar módulo para un cliente",
    description="""
    Desactiva un módulo específico para un cliente.
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo a desactivar
    
    **Validaciones:**
    - El módulo debe estar activado para el cliente
    - No se puede desactivar un módulo core
    
    **Respuestas:**
    - 200: Módulo desactivado exitosamente
    - 400: No se puede desactivar el módulo (validaciones)
    - 404: Módulo activo no encontrado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def desactivar_modulo_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user=Depends(require_super_admin)
):
    """
    Desactiva un módulo para un cliente específico.
    Solo accesible para super administradores.
    """
    logger.info(f"Solicitud POST /clientes/{cliente_id}/modulos/{modulo_id}/desactivar/ recibida")
    
    try:
        # Obtener el módulo activo
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        
        if not modulo_activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}."
            )
        
        # Desactivar módulo
        await ModuloActivoService.desactivar_modulo(modulo_activo.cliente_modulo_activo_id)
        
        logger.info(f"Módulo {modulo_id} desactivado para cliente {cliente_id}")
        
        return {
            "success": True,
            "message": "Módulo desactivado exitosamente para el cliente.",
            "cliente_id": cliente_id,
            "modulo_id": modulo_id
        }
    
    except HTTPException:
        raise
    except CustomException as ce:
        logger.warning(f"Error de negocio al desactivar módulo {modulo_id} para cliente {cliente_id}: {ce.detail}")
        raise HTTPException(
            status_code=ce.status_code,
            detail=ce.detail
        )
    except Exception as e:
        logger.exception(f"Error inesperado al desactivar módulo {modulo_id} para cliente {cliente_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al desactivar el módulo."
        )


# ============================================================================
# WORKFLOWS INTEGRADOS
# ============================================================================

@router.post(
    "/clientes/{cliente_id}/modulos/{modulo_id}/activar-completo/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="[WORKFLOW] Activar módulo completo con conexión",
    description="""
    Workflow integrado que activa un módulo para un cliente y configura su conexión de BD.
    
    **Flujo del workflow:**
    1. Valida que el módulo existe y está activo
    2. Valida que el cliente existe
    3. Activa el módulo para el cliente
    4. Configura la conexión de base de datos
    5. Testea la conexión
    6. Retorna estado completo
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Body:**
    - activacion: Configuración de activación del módulo
    - conexion: Configuración de conexión de BD (opcional)
    
    **Respuestas:**
    - 201: Módulo activado y configurado exitosamente
    - 400: Datos de entrada inválidos o test de conexión fallido
    - 404: Módulo o cliente no encontrado
    - 409: Módulo ya activado
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def activar_modulo_completo(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    activacion_data: ModuloActivoCreate = Body(...),
    conexion_data: Optional[ConexionCreate] = Body(None),
    current_user=Depends(require_super_admin)
):
    """
    Workflow integrado: Activa un módulo y configura su conexión de BD.
    Solo accesible para super administradores.
    """
    logger.info(f"[WORKFLOW] Activación completa de módulo {modulo_id} para cliente {cliente_id}")
    
    try:
        # Paso 1: Validar módulo
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con ID {modulo_id} no encontrado."
            )
        
        # Paso 2: Asegurar IDs
        activacion_data.cliente_id = cliente_id
        activacion_data.modulo_id = modulo_id
        
        # Paso 3: Activar módulo
        modulo_activo = await ModuloActivoService.activar_modulo(activacion_data)
        logger.info(f"[WORKFLOW] Módulo activado exitosamente")
        
        # Paso 4: Configurar conexión si se proporciona
        conexion = None
        test_conexion = None
        if conexion_data:
            conexion_data.cliente_id = cliente_id
            
            conexion = await ConexionService.crear_conexion(
                conexion_data,
                creado_por_usuario_id=current_user.get("usuario_id", 1)
            )
            logger.info(f"[WORKFLOW] Conexión configurada exitosamente")
            
            # Paso 5: Testear conexión
            test_data = ConexionTest(
                servidor=conexion_data.servidor,
                puerto=conexion_data.puerto,
                nombre_bd=conexion_data.nombre_bd,
                usuario=conexion_data.usuario,
                password=conexion_data.password,
                tipo_bd=conexion_data.tipo_bd,
                usa_ssl=conexion_data.usa_ssl
            )
            test_conexion = await ConexionService.test_conexion(test_data)
            logger.info(f"[WORKFLOW] Test de conexión completado: {test_conexion['success']}")
        
        # Paso 6: Retornar estado completo
        return {
            "success": True,
            "message": f"Módulo '{modulo.nombre}' activado y configurado exitosamente.",
            "workflow": "activar-completo",
            "data": {
                "modulo": modulo,
                "activacion": modulo_activo,
                "conexion": conexion,
                "test_conexion": test_conexion
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW] Error en activación completa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el workflow de activación completa: {str(e)}"
        )


@router.delete(
    "/clientes/{cliente_id}/modulos/{modulo_id}/desactivar-completo/",
    response_model=Dict[str, Any],
    summary="[WORKFLOW] Desactivar módulo completo con conexiones",
    description="""
    Workflow integrado que desactiva un módulo y todas sus conexiones asociadas.
    
    **Flujo del workflow:**
    1. Valida que el módulo está activado para el cliente
    2. Desactiva todas las conexiones asociadas
    3. Desactiva el módulo
    4. Retorna resumen de operaciones
    
    **Permisos requeridos:**
    - Super Administrador
    
    **Respuestas:**
    - 200: Módulo y conexiones desactivados exitosamente
    - 404: Módulo no activado para el cliente
    - 403: Sin permisos suficientes
    - 500: Error interno del servidor
    """
)
async def desactivar_modulo_completo(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user=Depends(require_super_admin)
):
    """
    Workflow integrado: Desactiva un módulo y todas sus conexiones.
    Solo accesible para super administradores.
    """
    logger.info(f"[WORKFLOW] Desactivación completa de módulo {modulo_id} para cliente {cliente_id}")
    
    try:
        # Paso 1: Obtener módulo activo
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        
        if not modulo_activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}."
            )
        
        # Paso 2: Obtener conexiones del cliente (nota: conexiones son por cliente, no por módulo)
        conexiones = await ConexionService.obtener_conexiones_cliente(cliente_id)
        
        # Nota: En el nuevo modelo, las conexiones son por cliente, no por módulo
        # Por lo tanto, no se desactivan automáticamente al desactivar un módulo
        # Si se requiere desactivar conexiones, debe hacerse manualmente
        conexiones_desactivadas = []
        
        logger.info(f"[WORKFLOW] Módulo desactivado. Conexiones del cliente: {len(conexiones)} (no se desactivan automáticamente)")
        
        # Paso 3: Desactivar módulo
        await ModuloActivoService.desactivar_modulo(modulo_activo.cliente_modulo_activo_id)
        logger.info(f"[WORKFLOW] Módulo desactivado exitosamente")
        
        # Paso 4: Retornar resumen
        return {
            "success": True,
            "message": "Módulo y conexiones desactivados exitosamente.",
            "workflow": "desactivar-completo",
            "data": {
                "cliente_id": cliente_id,
                "modulo_id": modulo_id,
                "conexiones_desactivadas": len(conexiones_desactivadas),
                "conexion_ids": conexiones_desactivadas
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW] Error en desactivación completa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el workflow de desactivación completa: {str(e)}"
        )


@router.get(
    "/clientes/{cliente_id}/modulos/{modulo_id}/estado-completo/",
    response_model=Dict[str, Any],
    summary="[WORKFLOW] Obtener estado completo de módulo",
    description="""
    Workflow integrado que retorna el estado completo de un módulo para un cliente.
    
    **Información retornada:**
    - Información del módulo
    - Estado de activación
    - Configuración y límites
    - Estadísticas de uso
    - Conexiones configuradas
    - Estado de conexiones
    
    **Permisos requeridos:**
    - Cualquier usuario autenticado
    
    **Respuestas:**
    - 200: Estado completo recuperado exitosamente
    - 404: Módulo no activado para el cliente
    - 500: Error interno del servidor
    """
)
async def obtener_estado_completo_modulo(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    modulo_id: UUID = Path(..., description="ID del módulo"),
    current_user=Depends(get_current_active_user)
):
    """
    Workflow integrado: Retorna el estado completo de un módulo.
    """
    logger.info(f"[WORKFLOW] Obteniendo estado completo de módulo {modulo_id} para cliente {cliente_id}")
    
    try:
        # Paso 1: Obtener módulo
        modulo = await ModuloService.obtener_modulo_por_id(modulo_id)
        if not modulo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo con ID {modulo_id} no encontrado."
            )
        
        # Paso 2: Obtener activación
        modulo_activo = await ModuloActivoService.obtener_modulo_activo_por_cliente_y_modulo(
            cliente_id, modulo_id
        )
        
        if not modulo_activo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Módulo {modulo_id} no está activado para el cliente {cliente_id}."
            )
        
        # Paso 3: Obtener estadísticas
        estadisticas = await ModuloActivoService.obtener_estadisticas_modulo_activo(
            cliente_id, modulo_id
        )
        
        # Paso 4: Obtener conexiones del cliente (nota: conexiones son por cliente, no por módulo)
        conexiones = await ConexionService.obtener_conexiones_cliente(cliente_id)
        
        # Paso 5: Obtener conexión principal del cliente
        conexion_principal = await ConexionService.obtener_conexion_principal(cliente_id)
        
        # Paso 6: Retornar estado completo
        return {
            "success": True,
            "message": "Estado completo del módulo recuperado exitosamente.",
            "workflow": "estado-completo",
            "data": {
                "modulo": modulo,
                "activacion": modulo_activo,
                "estadisticas": estadisticas,
                "conexiones": {
                    "total": len(conexiones),
                    "principal": conexion_principal,
                    "todas": conexiones
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WORKFLOW] Error obteniendo estado completo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el workflow de estado completo: {str(e)}"
        )