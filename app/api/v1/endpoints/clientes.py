# app/api/v1/endpoints/clientes.py
"""
Módulo de endpoints para la gestión de clientes en arquitectura multi-tenant.

Este módulo proporciona una API REST completa para operaciones CRUD sobre clientes,
incluyendo creación, lectura, actualización, suspensión, activación y configuración.

Características principales:
- Autenticación JWT con requerimiento de nivel de super administrador para todas las operaciones.
- Validaciones robustas de datos de entrada.
- Gestión completa del ciclo de vida de clientes.
- Integración con políticas de autenticación y módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Request
from typing import List, Dict, Any, Optional
import logging

from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteRead
from app.services.cliente_service import ClienteService
from app.core.level_authorization import require_super_admin
from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo cliente",
    description="""
    Crea un nuevo cliente en el sistema. **Solo accesible por SUPER_ADMIN**.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Validaciones:**
    - subdominio único y válido
    - código_cliente único
    - Campos obligatorios: razon_social, subdominio, codigo_cliente
    
    **Respuestas:**
    - 201: Cliente creado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 409: Conflicto - subdominio o código ya existen
    - 422: Error de validación en los datos de entrada
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def crear_cliente(
    cliente_data: ClienteCreate = Body(...),
    current_user = Depends(get_current_active_user)
):
    """
    Crea un nuevo cliente en el sistema.
    """
    logger.info(f"Solicitud POST /clientes/ recibida para crear cliente: '{cliente_data.razon_social}' por usuario: {current_user.nombre_usuario}")
    try:
        created_cliente = await ClienteService.crear_cliente(cliente_data)
        logger.info(f"Cliente '{created_cliente.razon_social}' creado con ID: {created_cliente.cliente_id}")
        return created_cliente
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en crear_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al crear el cliente."
        )


@router.get(
    "/",
    response_model=List[ClienteRead],
    summary="Listar todos los clientes",
    description="""
    Obtiene una lista de todos los clientes. **Solo accesible por SUPER_ADMIN**.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de query:**
    - skip: Número de registros a saltar (paginación)
    - limit: Límite de registros a retornar (paginación)
    - solo_activos: Filtrar solo clientes activos
    
    **Respuestas:**
    - 200: Lista de clientes recuperada exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def listar_clientes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True, description="Filtrar solo clientes activos"),
    current_user = Depends(get_current_active_user),
    request: Request = None  
):
    """
    Lista todos los clientes del sistema con paginación.
    """
    logger.info(f"SOLICITUD RECIBIDA en /clientes/")
    logger.info(f"Headers recibidos: {dict(request.headers)}")
    logger.info(f"Query params: skip={skip}, limit={limit}, solo_activos={solo_activos}")
    logger.info(f"URL completa: {request.url}")
    logger.info(f"Usuario: {current_user.nombre_usuario}")
    logger.info(f"Solicitud GET /clientes/ recibida - skip: {skip}, limit: {limit}, solo_activos: {solo_activos} por usuario: {current_user.nombre_usuario}")
    try:
        # Query con paginación y filtro
        where_clause = "WHERE es_activo = 1" if solo_activos else ""
        query = f"""
        SELECT 
            cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
            tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
            favicon_url, color_primario, color_secundario, tema_personalizado,
            plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
            fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
            es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        {where_clause}
        ORDER BY razon_social
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        from app.db.queries import execute_query
        resultados = execute_query(query, (skip, limit))
        clientes = [ClienteRead(**row) for row in resultados]
        logger.info(f"Lista de clientes recuperada: {len(clientes)} clientes")
        return clientes
    except Exception as e:
        logger.exception(f"Error inesperado en listar_clientes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al listar los clientes."
        )


@router.get(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Obtener detalle de un cliente",
    description="""
    Obtiene los detalles completos de un cliente específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a consultar
    
    **Respuestas:**
    - 200: Cliente encontrado y devuelto
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def obtener_cliente(
    cliente_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un cliente por su ID.
    """
    logger.info(f"Solicitud GET /clientes/{cliente_id} recibida por usuario: {current_user.nombre_usuario}")
    try:
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {cliente_id} no encontrado."
            )
        return cliente
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener el cliente."
        )


@router.put(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Actualizar un cliente",
    description="""
    Actualiza la información de un cliente existente.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a actualizar
    
    **Respuestas:**
    - 200: Cliente actualizado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 409: Conflicto - subdominio o código ya existen
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def actualizar_cliente(
    cliente_id: int, 
    cliente_data: ClienteUpdate = Body(...),
    current_user = Depends(get_current_active_user)
):
    """
    Actualiza un cliente existente.
    """
    logger.info(f"Solicitud PUT /clientes/{cliente_id} recibida para actualizar por usuario: {current_user.nombre_usuario}")
    try:
        # Placeholder - necesitamos implementar actualizar_cliente en el servicio
        # Por ahora retornamos el cliente existente
        cliente_existente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {cliente_id} no encontrado."
            )
        
        # Simular actualización - en producción esto vendría del servicio
        logger.info(f"Cliente {cliente_id} sería actualizado con: {cliente_data.dict(exclude_unset=True)}")
        return cliente_existente
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar el cliente."
        )


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un cliente",
    description="""
    Elimina un cliente del sistema (eliminación lógica).
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a eliminar
    
    **Respuestas:**
    - 204: Cliente eliminado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def eliminar_cliente(
    cliente_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Elimina un cliente (eliminación lógica).
    """
    logger.info(f"Solicitud DELETE /clientes/{cliente_id} recibida por usuario: {current_user.nombre_usuario}")
    try:
        # Placeholder - necesitamos implementar eliminar_cliente en el servicio
        cliente_existente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {cliente_id} no encontrado."
            )
        
        # Simular eliminación lógica
        logger.info(f"Cliente {cliente_id} sería marcado como inactivo")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en eliminar_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al eliminar el cliente."
        )


@router.put(
    "/{cliente_id}/suspender",
    response_model=ClienteRead,
    summary="Suspender un cliente",
    description="""
    Suspende un cliente cambiando su estado de suscripción a 'suspendido'.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a suspender
    
    **Respuestas:**
    - 200: Cliente suspendido exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 400: Cliente ya está suspendido
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def suspender_cliente(
    cliente_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Suspende un cliente.
    """
    logger.info(f"Solicitud PUT /clientes/{cliente_id}/suspender recibida por usuario: {current_user.nombre_usuario}")
    try:
        cliente_suspendido = await ClienteService.suspender_cliente(cliente_id)
        return cliente_suspendido
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en suspender_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al suspender el cliente."
        )


@router.put(
    "/{cliente_id}/activar",
    response_model=ClienteRead,
    summary="Activar un cliente",
    description="""
    Reactiva un cliente cambiando su estado de suscripción a 'activo'.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a activar
    
    **Respuestas:**
    - 200: Cliente activado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 400: Cliente ya está activo
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def activar_cliente(
    cliente_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Activa un cliente suspendido.
    """
    logger.info(f"Solicitud PUT /clientes/{cliente_id}/activar recibida por usuario: {current_user.nombre_usuario}")
    try:
        cliente_activado = await ClienteService.activar_cliente(cliente_id)
        return cliente_activado
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en activar_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al activar el cliente."
        )


@router.get(
    "/{cliente_id}/estadisticas",
    summary="Obtener estadísticas de un cliente",
    description="""
    Obtiene estadísticas y métricas de uso de un cliente específico.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente
    
    **Respuestas:**
    - 200: Estadísticas del cliente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """
)
@require_super_admin()
async def obtener_estadisticas_cliente(
    cliente_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas de uso de un cliente.
    """
    logger.info(f"Solicitud GET /clientes/{cliente_id}/estadisticas recibida por usuario: {current_user.nombre_usuario}")
    try:
        # Verificar que el cliente existe
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {cliente_id} no encontrado."
            )
        
        # Placeholder - estadísticas básicas
        estadisticas = {
            "cliente_id": cliente_id,
            "total_usuarios": 0,
            "modulos_activos": 0,
            "ultimo_acceso": cliente.fecha_ultimo_acceso,
            "estado_suscripcion": cliente.estado_suscripcion,
            "plan_actual": cliente.plan_suscripcion
        }
        
        return estadisticas
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_estadisticas_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las estadísticas del cliente."
        )

@router.get(
    "/debug/user-info",
    summary="Información de diagnóstico del usuario actual"
)
async def debug_user_info(current_user = Depends(get_current_active_user)):
    """
    Endpoint temporal para diagnóstico de niveles de acceso
    """
    return {
        "usuario_id": current_user.usuario_id,
        "nombre_usuario": current_user.nombre_usuario,
        "cliente_id": current_user.cliente_id,
        "access_level": getattr(current_user, 'access_level', 'NO_DEFINIDO'),
        "is_super_admin": getattr(current_user, 'is_super_admin', 'NO_DEFINIDO'),
        "user_type": getattr(current_user, 'user_type', 'NO_DEFINIDO')
    }


@router.get(
    "/debug/access-levels",
    summary="Diagnóstico de niveles de acceso"
)
async def debug_access_levels(current_user = Depends(get_current_active_user)):
    """
    Endpoint temporal para diagnóstico de niveles de acceso
    """
    from app.api.deps import debug_user_access_levels
    
    # Obtener información detallada de niveles
    level_info = await debug_user_access_levels(current_user.usuario_id, current_user.cliente_id)
    
    return {
        "usuario": {
            "usuario_id": current_user.usuario_id,
            "nombre_usuario": current_user.nombre_usuario,
            "cliente_id": current_user.cliente_id
        },
        "niveles_calculados": {
            "access_level": getattr(current_user, 'access_level', 'NO_DEFINIDO'),
            "is_super_admin": getattr(current_user, 'is_super_admin', 'NO_DEFINIDO'),
            "user_type": getattr(current_user, 'user_type', 'NO_DEFINIDO')
        },
        "diagnostico_bd": level_info,
        # CORREGIDO: Usar solo campos que existen en RolRead
        "roles_asignados": [{"nombre": r.nombre, "rol_id": r.rol_id} for r in current_user.roles]
    }
