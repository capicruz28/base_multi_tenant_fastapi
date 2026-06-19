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
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import Optional
from uuid import UUID
import logging

from app.modules.tenant.presentation.schemas import (
    ClienteCreate, ClienteUpdate, ClienteRead,
    PaginatedClienteResponse, ClienteStatsResponse, ClienteResponse, ClienteCreateResponse,
    ClienteDeleteResponse,
    BrandingRead
)
from app.modules.tenant.application.services.cliente_onboarding_service import (
    MENSAJE_CREACION_EXITOSA,
)
from app.modules.tenant.application.services.cliente_service import ClienteService
from app.core.authorization.lbac import require_super_admin
from app.core.authorization.rbac import require_permission
from app.api.deps import get_current_active_user
from math import ceil

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ClienteCreateResponse,
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
    """,
    dependencies=[Depends(require_permission("tenant.cliente.crear"))],
)
@require_super_admin()
async def crear_cliente(
    cliente_data: ClienteCreate = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Crea un nuevo cliente en el sistema.
    """
    logger.info(
        f"Solicitud POST /clientes/ recibida para crear cliente: '{cliente_data.razon_social}' "
        f"por usuario: {current_user.nombre_usuario}"
    )
    resultado = await ClienteService.crear_cliente(cliente_data)
    created_cliente = resultado.cliente
    logger.info(f"Cliente '{created_cliente.razon_social}' creado con ID: {created_cliente.cliente_id}")
    return ClienteCreateResponse(
        success=True,
        message=MENSAJE_CREACION_EXITOSA,
        data=created_cliente,
        credenciales_iniciales=resultado.credenciales,
    )


@router.get(
    "/",
    response_model=PaginatedClienteResponse,
    summary="Listar todos los clientes",
    description="""
    Obtiene una lista paginada de todos los clientes. **Solo accesible por SUPER_ADMIN**.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de query:**
    - skip: Número de registros a saltar (paginación)
    - limit: Límite de registros a retornar (paginación)
    - solo_activos: Filtrar solo clientes activos
    - solo_inactivos: Filtrar solo clientes inactivos (es_activo=0); tiene precedencia sobre solo_activos
    - buscar: Texto para buscar en razón social, nombre comercial, código o subdominio
    
    **Respuestas:**
    - 200: Lista de clientes recuperada exitosamente con metadatos de paginación
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.cliente.leer"))],
)
@require_super_admin()
async def listar_clientes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True, description="Filtrar solo clientes activos"),
    solo_inactivos: bool = Query(
        False,
        description="Filtrar solo clientes inactivos (es_activo=0); excluye suspendidos",
    ),
    buscar: Optional[str] = Query(None, description="Texto para buscar en razón social, nombre comercial, código o subdominio"),
    current_user=Depends(get_current_active_user)
):
    """
    Lista todos los clientes del sistema con paginación y búsqueda.
    """
    logger.info(
        f"Solicitud GET /clientes/ recibida - skip: {skip}, limit: {limit}, "
        f"solo_activos: {solo_activos}, solo_inactivos: {solo_inactivos}, buscar: {buscar} "
        f"por usuario: {current_user.nombre_usuario}"
    )
    clientes, total = await ClienteService.listar_clientes(
        skip=skip,
        limit=limit,
        solo_activos=solo_activos,
        solo_inactivos=solo_inactivos,
        buscar=buscar
    )

    total_paginas = ceil(total / limit) if limit > 0 else 0
    pagina_actual = (skip // limit) + 1 if limit > 0 else 1

    return PaginatedClienteResponse(
        clientes=clientes,
        total_clientes=total,
        pagina_actual=pagina_actual,
        total_paginas=total_paginas,
        items_por_pagina=limit
    )


@router.get(
    "/{cliente_id}/",
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
    """,
    dependencies=[Depends(require_permission("tenant.cliente.leer"))],
)
@require_super_admin()
async def obtener_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene los detalles de un cliente por su ID.
    """
    logger.info(f"Solicitud GET /clientes/{cliente_id} recibida por usuario: {current_user.nombre_usuario}")
    cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado."
        )
    return cliente


@router.put(
    "/{cliente_id}/",
    response_model=ClienteResponse,
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
    """,
    dependencies=[Depends(require_permission("tenant.cliente.actualizar"))],
)
@require_super_admin()
async def actualizar_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    cliente_data: ClienteUpdate = Body(...),
    current_user=Depends(get_current_active_user)
):
    """
    Actualiza un cliente existente.
    """
    logger.info(
        f"Solicitud PUT /clientes/{cliente_id} recibida para actualizar "
        f"por usuario: {current_user.nombre_usuario}"
    )
    cliente_actualizado = await ClienteService.actualizar_cliente(cliente_id, cliente_data)
    logger.info(f"Cliente {cliente_id} actualizado exitosamente")
    return ClienteResponse(
        success=True,
        message=f"Cliente '{cliente_actualizado.razon_social}' actualizado exitosamente",
        data=cliente_actualizado
    )


@router.delete(
    "/{cliente_id}/",
    response_model=ClienteDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar un cliente",
    description="""
    Elimina un cliente del sistema (eliminación lógica - marca como inactivo).
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a eliminar
    
    **Nota:** No se puede eliminar el cliente SYSTEM.
    
    **Respuestas:**
    - 200: Cliente eliminado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 400: No se puede eliminar el cliente SYSTEM
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.cliente.eliminar"))],
)
@require_super_admin()
async def eliminar_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Elimina un cliente (eliminación lógica).
    """
    logger.info(f"Solicitud DELETE /clientes/{cliente_id} recibida por usuario: {current_user.nombre_usuario}")
    await ClienteService.eliminar_cliente(cliente_id)
    logger.info(f"Cliente {cliente_id} eliminado exitosamente")
    return ClienteDeleteResponse(
        success=True,
        message=f"Cliente con ID {cliente_id} eliminado exitosamente (marcado como inactivo)",
        cliente_id=cliente_id
    )


@router.put(
    "/{cliente_id}/suspender/",
    response_model=ClienteResponse,
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
    """,
    dependencies=[Depends(require_permission("tenant.cliente.actualizar"))],
)
@require_super_admin()
async def suspender_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Suspende un cliente.
    """
    logger.info(
        f"Solicitud PUT /clientes/{cliente_id}/suspender recibida por usuario: {current_user.nombre_usuario}"
    )
    cliente_suspendido = await ClienteService.suspender_cliente(cliente_id)
    return ClienteResponse(
        success=True,
        message=f"Cliente '{cliente_suspendido.razon_social}' suspendido exitosamente",
        data=cliente_suspendido
    )


@router.put(
    "/{cliente_id}/activar/",
    response_model=ClienteResponse,
    summary="Activar un cliente",
    description="""
    Reactiva un cliente: suscripción 'activo' y registro operativo (es_activo=1).

    Aplica tanto a clientes suspendidos como a clientes desactivados (eliminación lógica),
    restaurando visibilidad en listados y acceso operativo del tenant.
    
    **Permisos requeridos:**
    - Nivel de acceso 5 (Super Administrador)
    
    **Parámetros de ruta:**
    - cliente_id: ID del cliente a activar
    
    **Respuestas:**
    - 200: Cliente activado exitosamente
    - 403: Acceso denegado - se requiere nivel de super administrador
    - 404: Cliente no encontrado
    - 400: Cliente ya está activo (es_activo=1 y estado_suscripcion=activo)
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.cliente.actualizar"))],
)
@require_super_admin()
async def activar_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Activa o reactiva un cliente (suscripción y es_activo).
    """
    logger.info(
        f"Solicitud PUT /clientes/{cliente_id}/activar recibida por usuario: {current_user.nombre_usuario}"
    )
    cliente_activado = await ClienteService.activar_cliente(cliente_id)
    return ClienteResponse(
        success=True,
        message=f"Cliente '{cliente_activado.razon_social}' activado exitosamente",
        data=cliente_activado
    )


@router.get(
    "/{cliente_id}/estadisticas/",
    response_model=ClienteStatsResponse,
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
    """,
    dependencies=[Depends(require_permission("tenant.cliente.leer"))],
)
@require_super_admin()
async def obtener_estadisticas_cliente(
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene estadísticas de uso de un cliente.
    """
    logger.info(
        f"Solicitud GET /clientes/{cliente_id}/estadisticas recibida por usuario: {current_user.nombre_usuario}"
    )
    return await ClienteService.obtener_estadisticas(cliente_id)


@router.get(
    "/debug/user-info",
    summary="Información de diagnóstico del usuario actual"
)
async def debug_user_info(current_user=Depends(get_current_active_user)):
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
async def debug_access_levels(current_user=Depends(get_current_active_user)):
    """
    Endpoint temporal para diagnóstico de niveles de acceso
    """
    from app.api.deps import debug_user_access_levels

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
        "roles_asignados": [{"nombre": r.nombre, "rol_id": r.rol_id} for r in current_user.roles]
    }


@router.get(
    "/branding",
    response_model=BrandingRead,
    summary="Obtener branding por subdominio (público)",
    description="""
    Obtiene la configuración de branding de un tenant basándose en su subdominio.
    **Este endpoint es público y no requiere autenticación.**
    
    Útil para mostrar el branding personalizado en la página de login antes de que el usuario se autentique.
    
    **Características:**
    - ✅ Público: No requiere autenticación (sin token JWT)
    - ✅ Sin cookies: No requiere cookies de sesión
    - ✅ Read-only: Solo lectura, no modifica datos
    - Retorna valores por defecto si no hay branding configurado (200 OK)
    - Parsea tema_personalizado de JSON a objeto
    
    **Parámetros:**
    - subdominio (query, requerido): Subdominio del tenant (ej: 'techcorp', 'acme')
    
    **Respuestas:**
    - 200: Branding obtenido exitosamente (o valores por defecto si no hay branding)
    - 400: Subdominio inválido o vacío
    - 404: Subdominio no encontrado o cliente inactivo
    - 500: Error interno del servidor
    """
)
async def obtener_branding_por_subdominio(
    subdominio: str = Query(..., description="Subdominio del tenant", min_length=1)
):
    """
    Obtiene la configuración de branding por subdominio (endpoint público).
    """
    logger.info(f"Solicitud GET /branding recibida para subdominio={subdominio}")
    return await ClienteService.get_branding_by_subdomain(subdominio)


@router.get(
    "/tenant/branding",
    response_model=BrandingRead,
    summary="Obtener configuración de branding del tenant actual",
    description="""
    Obtiene la configuración de branding del cliente (tenant) actual.
    
    **Características:**
    - Usa el cliente_id del contexto de tenant (middleware)
    - No requiere autenticación de super admin
    - Solo retorna campos de branding (ligero y optimizado)
    - Parsea tema_personalizado de JSON a objeto
    
    **Permisos requeridos:**
    - Usuario autenticado (cualquier nivel)
    
    **Respuestas:**
    - 200: Branding obtenido exitosamente
    - 400: No se pudo determinar el tenant actual
    - 404: Cliente no encontrado o inactivo
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("tenant.branding.leer"))],
)
async def obtener_branding_tenant(
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene la configuración de branding del tenant actual.
    """
    try:
        from app.core.tenant.context import get_current_client_id

        cliente_id = get_current_client_id()
        logger.info(
            f"Solicitud GET /tenant/branding recibida para cliente_id={cliente_id} "
            f"por usuario: {current_user.nombre_usuario}"
        )
        return await ClienteService.get_branding_by_cliente(cliente_id)
    except RuntimeError as e:
        logger.error(f"Error obteniendo contexto de tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo determinar el tenant actual. Verifique que el request incluya el subdominio correcto."
        ) from e
