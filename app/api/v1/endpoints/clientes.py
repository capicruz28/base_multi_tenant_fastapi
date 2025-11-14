# app/api/v1/endpoints/clientes.py
"""
Módulo de endpoints para la gestión de clientes en arquitectura multi-tenant.

Este módulo proporciona una API REST completa para operaciones CRUD sobre clientes,
incluyendo creación, lectura, actualización, suspensión y configuración.

Características principales:
- Autenticación JWT con requerimiento de rol 'SUPER_ADMIN' para todas las operaciones.
- Validaciones robustas de datos de entrada.
- Gestión completa del ciclo de vida de clientes.
- Integración con políticas de autenticación y módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any, Optional
import logging

from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteRead
from app.services.cliente_service import ClienteService
from app.api.deps import RoleChecker

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencia para requerir rol SUPER_ADMIN
require_super_admin = RoleChecker(["SUPER_ADMIN"])


@router.post(
    "/",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo cliente",
    description="""
    Crea un nuevo cliente en el sistema. **Solo accesible por SUPER_ADMIN**.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Validaciones:**
    - subdominio único y válido
    - código_cliente único
    - Campos obligatorios: razon_social, subdominio, codigo_cliente
    
    **Respuestas:**
    - 201: Cliente creado exitosamente
    - 409: Conflicto - subdominio o código ya existen
    - 422: Error de validación en los datos de entrada
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def crear_cliente(cliente_ ClienteCreate = Body(...)):
    """
    Crea un nuevo cliente en el sistema.
    """
    logger.info(f"Solicitud POST /clientes/ recibida para crear cliente: '{cliente_data.razon_social}'")
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
    - Rol 'SUPER_ADMIN'
    
    **Respuestas:**
    - 200: Lista de clientes recuperada exitosamente
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def listar_clientes():
    """
    Lista todos los clientes del sistema.
    """
    logger.info("Solicitud GET /clientes/ recibida (listar todos)")
    try:
        # El servicio debe tener un método para listar clientes
        # Por ahora, usaremos una query directa como placeholder
        query = """
        SELECT 
            cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
            tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
            favicon_url, color_primario, color_secundario, tema_personalizado,
            plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
            fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
            es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        ORDER BY razon_social
        """
        from app.db.queries import execute_query
        resultados = execute_query(query)
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
    "/{id}/",
    response_model=ClienteRead,
    summary="Obtener detalle de un cliente",
    description="""
    Obtiene los detalles completos de un cliente específico.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - id: ID del cliente a consultar
    
    **Respuestas:**
    - 200: Cliente encontrado y devuelto
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def obtener_cliente(id: int):
    """
    Obtiene los detalles de un cliente por su ID.
    """
    logger.info(f"Solicitud GET /clientes/{id}/ recibida")
    try:
        cliente = await ClienteService.obtener_cliente_por_id(id)
        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {id} no encontrado."
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
    "/{id}/",
    response_model=ClienteRead,
    summary="Actualizar un cliente",
    description="""
    Actualiza la información de un cliente existente.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - id: ID del cliente a actualizar
    
    **Respuestas:**
    - 200: Cliente actualizado exitosamente
    - 404: Cliente no encontrado
    - 409: Conflicto - subdominio o código ya existen
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def actualizar_cliente(id: int, cliente_ ClienteUpdate = Body(...)):
    """
    Actualiza un cliente existente.
    """
    logger.info(f"Solicitud PUT /clientes/{id}/ recibida para actualizar")
    try:
        # Placeholder: el servicio necesita un método `actualizar_cliente`
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Endpoint de actualización de cliente no implementado aún."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en actualizar_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al actualizar el cliente."
        )


@router.put(
    "/{id}/suspend/",
    response_model=ClienteRead,
    summary="Suspender un cliente",
    description="""
    Suspende un cliente cambiando su estado de suscripción a 'suspendido'.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - id: ID del cliente a suspender
    
    **Respuestas:**
    - 200: Cliente suspendido exitosamente
    - 404: Cliente no encontrado
    - 400: Cliente ya está suspendido
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def suspender_cliente(id: int):
    """
    Suspende un cliente.
    """
    logger.info(f"Solicitud PUT /clientes/{id}/suspend/ recibida")
    try:
        cliente_suspendido = await ClienteService.suspender_cliente(id)
        return cliente_suspendido
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en suspender_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al suspender el cliente."
        )


@router.get(
    "/{id}/config/",
    summary="Obtener configuración de un cliente",
    description="""
    Obtiene la configuración completa de un cliente, incluyendo políticas de autenticación
    y módulos activos.
    
    **Permisos requeridos:**
    - Rol 'SUPER_ADMIN'
    
    **Parámetros de ruta:**
    - id: ID del cliente
    
    **Respuestas:**
    - 200: Configuración del cliente
    - 404: Cliente no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_super_admin)]
)
async def obtener_configuracion_cliente(id: int):
    """
    Obtiene la configuración de un cliente.
    """
    logger.info(f"Solicitud GET /clientes/{id}/config/ recibida")
    try:
        from app.services.tenant_service import TenantService
        config = await TenantService.obtener_configuracion_tenant(id)
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en obtener_configuracion_cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener la configuración del cliente."
        )