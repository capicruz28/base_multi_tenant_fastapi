"""
Módulo de endpoints para la gestión de conexiones de base de datos en arquitectura multi-tenant.

Este módulo proporciona una API REST completa para operaciones sobre conexiones de BD
por cliente y módulo, incluyendo creación, configuración, testing y gestión del ciclo de vida.

Características principales:
- Autenticación JWT con requerimiento de rol 'SUPER_ADMIN' para todas las operaciones.
- Encriptación segura de credenciales de base de datos.
- Testing de conectividad en tiempo real.
- Soporte para múltiples motores de base de datos.
- Validación de configuraciones de conexión.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any, Optional
import logging

from app.schemas.conexion import ConexionRead, ConexionCreate, ConexionUpdate, ConexionTest
from app.services.conexion_service import ConexionService
from app.api.deps import RoleChecker, get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencia para requerir rol SUPER_ADMIN
require_super_admin = RoleChecker(["SUPER_ADMIN"])


@router.get(
    "/clientes/{cliente_id}",
    response_model=List[ConexionRead],
    summary="Listar conexiones de un cliente",
    description="""
    Obtiene la lista de todas las conexiones de base de datos configuradas para un cliente.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Lista de conexiones recuperada exitosamente
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def listar_conexiones_cliente(cliente_id: int):
    """
    Lista todas las conexiones de BD para un cliente específico.
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
    "/clientes/{cliente_id}/modulos/{modulo_id}/principal",
    response_model=Optional[ConexionRead],
    summary="Obtener conexión principal de módulo",
    description="""
    Obtiene la conexión principal configurada para un módulo específico de un cliente.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    - modulo_id: ID del módulo
    
    **Respuestas:**
    - 200: Conexión principal encontrada (puede ser null si no existe)
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def obtener_conexion_principal(
    cliente_id: int,
    modulo_id: int
):
    """
    Obtiene la conexión principal para un cliente y módulo específicos.
    """
    logger.info(f"Solicitud GET /conexiones/clientes/{cliente_id}/modulos/{modulo_id}/principal recibida")
    try:
        conexion = await ConexionService.obtener_conexion_principal(cliente_id, modulo_id)
        if conexion:
            logger.info(f"Conexión principal encontrada para cliente {cliente_id}, módulo {modulo_id}")
        else:
            logger.info(f"No se encontró conexión principal para cliente {cliente_id}, módulo {modulo_id}")
        return conexion
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_conexion_principal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la conexión principal."
        )


@router.post(
    "/clientes/{cliente_id}",
    response_model=ConexionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva conexión",
    description="""
    Crea una nueva conexión de base de datos para un cliente y módulo.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 201: Conexión creada exitosamente
    - 409: Conflicto - ya existe conexión principal para este cliente-módulo
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def crear_conexion(
    cliente_id: int,
    conexion_data: ConexionCreate = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Crea una nueva conexión de BD para un cliente.
    """
    logger.info(f"Solicitud POST /conexiones/clientes/{cliente_id} recibida")
    try:
        conexion_creada = await ConexionService.crear_conexion(
            conexion_data=conexion_data,
            creado_por_usuario_id=current_user.usuario_id
        )
        logger.info(f"Conexión creada exitosamente con ID: {conexion_creada.conexion_id}")
        return conexion_creada
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en crear_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear la conexión."
        )


@router.put(
    "/{conexion_id}",
    response_model=ConexionRead,
    summary="Actualizar conexión",
    description="""
    Actualiza una conexión de base de datos existente.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - conexion_id: ID de la conexión a actualizar
    
    **Respuestas:**
    - 200: Conexión actualizada exitosamente
    - 404: Conexión no encontrada
    - 409: Conflicto - ya existe conexión principal para este cliente-módulo
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def actualizar_conexion(
    conexion_id: int,
    conexion_data: ConexionUpdate = Body(...)
):
    """
    Actualiza una conexión existente.
    """
    logger.info(f"Solicitud PUT /conexiones/{conexion_id} recibida")
    try:
        conexion_actualizada = await ConexionService.actualizar_conexion(conexion_id, conexion_data)
        logger.info(f"Conexión {conexion_id} actualizada exitosamente")
        return conexion_actualizada
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar la conexión."
        )


@router.delete(
    "/{conexion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar conexión",
    description="""
    Desactiva una conexión de base de datos (eliminación lógica).
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - conexion_id: ID de la conexión a desactivar
    
    **Respuestas:**
    - 204: Conexión desactivada exitosamente
    - 404: Conexión no encontrada
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def desactivar_conexion(conexion_id: int):
    """
    Desactiva una conexión (eliminación lógica).
    """
    logger.info(f"Solicitud DELETE /conexiones/{conexion_id} recibida")
    try:
        conexion_desactivada = await ConexionService.desactivar_conexion(conexion_id)
        logger.info(f"Conexión {conexion_id} desactivada exitosamente")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en desactivar_conexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al desactivar la conexión."
        )


@router.post(
    "/test",
    summary="Testear conexión",
    description="""
    Testea la conectividad de una configuración de conexión sin guardarla.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Respuestas:**
    - 200: Resultado del test de conexión
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def test_conexion(conexion_test: ConexionTest = Body(...)):
    """
    Testea la conectividad de una configuración de conexión.
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
            detail="Error interno del servidor al testear la conexión."
        )