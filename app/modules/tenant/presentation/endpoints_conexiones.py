# app/api/v1/endpoints/conexiones.py
"""
M?dulo de endpoints para la gesti?n de conexiones de base de datos en arquitectura multi-tenant.

Este m?dulo proporciona una API REST completa para operaciones sobre conexiones de BD
por cliente, incluyendo creaci?n, configuraci?n, testing y gesti?n del ciclo de vida.

Caracter?sticas principales:
- Autenticaci?n JWT con requerimiento de nivel de super administrador para todas las operaciones.
- Encriptaci?n segura de credenciales de base de datos.
- Testing de conectividad en tiempo real.
- Soporte para m?ltiples motores de base de datos.
- Validaci?n de configuraciones de conexi?n.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from app.modules.tenant.presentation.schemas import ConexionRead, ConexionCreate, ConexionUpdate, ConexionTest
from app.modules.tenant.application.services.conexion_service import ConexionService
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.core.authorization.rbac import require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/clientes/{cliente_id}/",
    response_model=List[ConexionRead],
    summary="Listar conexiones de un cliente",
    description="""
    Obtiene la lista de todas las conexiones de base de datos configuradas para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Par?metros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Lista de conexiones recuperada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.leer"))],
)
@require_super_admin()
async def listar_conexiones_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Lista todas las conexiones de BD para un cliente espec?fico.
    """
    logger.info(f"Solicitud GET /conexiones/clientes/{cliente_id} recibida")
    try:
        conexiones = await ConexionService.obtener_conexiones_cliente(cliente_id)
        logger.info(f"Conexiones recuperadas para cliente {cliente_id}: {len(conexiones)} conexiones")
        return conexiones
    except Exception as e:
        logger.exception(f"Error inesperado en listar_conexiones_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al listar las conexiones del cliente."
        )


@router.get(
    "/clientes/{cliente_id}/principal/",
    response_model=Optional[ConexionRead],
    summary="Obtener conexi?n principal del cliente",
    description="""
    Obtiene la conexi?n principal configurada para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Par?metros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Conexi?n principal encontrada (puede ser null si no existe)
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.leer"))],
)
@require_super_admin()
async def obtener_conexion_principal(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene la conexi?n principal para un cliente espec?fico.
    """
    logger.info(f"Solicitud GET /conexiones/clientes/{cliente_id}/principal recibida")
    try:
        conexion = await ConexionService.obtener_conexion_principal(cliente_id)
        if conexion:
            logger.info(f"Conexi?n principal encontrada para cliente {cliente_id}")
        else:
            logger.info(f"No se encontr? conexi?n principal para cliente {cliente_id}")
        return conexion
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_conexion_principal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la conexi?n principal."
        )


@router.post(
    "/clientes/{cliente_id}/",
    response_model=ConexionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva conexi?n",
    description="""
    Crea una nueva conexi?n de base de datos para un cliente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Par?metros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 201: Conexi?n creada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 409: Conflicto - ya existe conexi?n principal para este cliente
    - 422: Error de validaci?n en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.crear"))],
)
@require_super_admin()
async def crear_conexion(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    conexion_data: ConexionCreate = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Crea una nueva conexi?n de BD para un cliente.
    """
    logger.info(f"Solicitud POST /conexiones/clientes/{cliente_id} recibida")
    try:
        conexion_creada = await ConexionService.crear_conexion(
            conexion_data=conexion_data,
            creado_por_usuario_id=current_user.usuario_id
        )
        logger.info(f"Conexi?n creada exitosamente con ID: {conexion_creada.conexion_id}")
        return conexion_creada
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en crear_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la conexi?n."
        )


@router.put(
    "/{conexion_id}/",
    response_model=ConexionRead,
    summary="Actualizar conexi?n",
    description="""
    Actualiza una conexi?n de base de datos existente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Par?metros de ruta:**
    - conexion_id: ID de la conexi?n a actualizar
    
    **Respuestas:**
    - 200: Conexi?n actualizada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Conexi?n no encontrada
    - 409: Conflicto - ya existe conexi?n principal para este cliente
    - 422: Error de validaci?n en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.actualizar"))],
)
@require_super_admin()
async def actualizar_conexion(
    conexion_id: UUID = Path(..., description="ID de la conexi?n"),
    conexion_data: ConexionUpdate = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Actualiza una conexi?n existente.
    """
    logger.info(f"Solicitud PUT /conexiones/{conexion_id} recibida")
    try:
        conexion_actualizada = await ConexionService.actualizar_conexion(conexion_id, conexion_data)
        logger.info(f"Conexi?n {conexion_id} actualizada exitosamente")
        return conexion_actualizada
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar la conexi?n."
        )


@router.delete(
    "/{conexion_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar conexi?n",
    description="""
    Desactiva una conexi?n de base de datos (eliminaci?n l?gica).
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Par?metros de ruta:**
    - conexion_id: ID de la conexi?n a desactivar
    
    **Respuestas:**
    - 204: Conexi?n desactivada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Conexi?n no encontrada
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.eliminar"))],
)
@require_super_admin()
async def desactivar_conexion(
    conexion_id: UUID = Path(..., description="ID de la conexi?n"),
    current_user=Depends(get_current_active_user)
):
    """
    Desactiva una conexi?n (eliminaci?n l?gica).
    """
    logger.info(f"Solicitud DELETE /conexiones/{conexion_id} recibida")
    try:
        conexion_desactivada = await ConexionService.desactivar_conexion(conexion_id)
        logger.info(f"Conexi?n {conexion_id} desactivada exitosamente")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en desactivar_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al desactivar la conexi?n."
        )


@router.post(
    "/test",
    summary="Testear conexi?n",
    description="""
    Testea la conectividad de una configuraci?n de conexi?n sin guardarla.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Respuestas:**
    - 200: Resultado del test de conexi?n
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 422: Error de validaci?n en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.conexion.leer"))],
)
@require_super_admin()
async def test_conexion(
    conexion_test: ConexionTest = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Testea la conectividad de una configuraci?n de conexi?n.
    """
    logger.info(f"Solicitud POST /conexiones/test recibida para servidor: {conexion_test.servidor}")
    try:
        resultado = await ConexionService.test_conexion(conexion_test)
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en test_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al testear la conexi?n."
        )