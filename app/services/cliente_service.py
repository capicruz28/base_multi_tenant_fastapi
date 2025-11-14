# app/services/cliente_service.py
"""
Servicio para la gestión completa del ciclo de vida de los clientes en arquitectura multi-tenant.
Este servicio implementa la lógica de negocio central para operaciones sobre la entidad `cliente`,
incluyendo validaciones de unicidad (subdominio, código), activación/suspensión, y gestión de suscripciones.

Características clave:
- Validación estricta de subdominios y códigos únicos
- Creación de datos seed para el cliente SUPER_ADMIN
- Manejo seguro de estados de suscripción
- Integración con políticas de autenticación por defecto
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import Optional, Dict, Any
import re
import logging
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.services.base_service import BaseService
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteRead

logger = logging.getLogger(__name__)


class ClienteService(BaseService):
    """
    Servicio central para la administración de clientes en un entorno multi-tenant.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_subdominio_cliente(subdominio: str) -> None:
        """
        Valida que el subdominio cumpla con las reglas de DNS y no esté en uso.
        """
        if not subdominio:
            raise ValidationError(
                detail="El subdominio es obligatorio.",
                internal_code="SUBDOMAIN_REQUIRED"
            )
        # Validar longitud y caracteres según RFC 1035
        if len(subdominio) > 63:
            raise ValidationError(
                detail="El subdominio no puede exceder los 63 caracteres.",
                internal_code="SUBDOMAIN_TOO_LONG"
            )
        patron = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$"
        if not re.match(patron, subdominio):
            raise ValidationError(
                detail="El subdominio solo puede contener letras minúsculas, números y guiones. "
                       "No puede comenzar ni terminar con guión.",
                internal_code="SUBDOMAIN_INVALID_FORMAT"
            )
        # Verificar unicidad
        query = "SELECT cliente_id FROM cliente WHERE LOWER(subdominio) = LOWER(?) AND es_activo = 1"
        resultado = execute_query(query, (subdominio,))
        if resultado:
            raise ConflictError(
                detail=f"El subdominio '{subdominio}' ya está en uso por otro cliente activo.",
                internal_code="SUBDOMAIN_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_codigo_cliente(codigo_cliente: str) -> None:
        """
        Valida que el código de cliente sea único entre clientes activos.
        """
        if not codigo_cliente:
            raise ValidationError(
                detail="El código de cliente es obligatorio.",
                internal_code="CLIENT_CODE_REQUIRED"
            )
        query = "SELECT cliente_id FROM cliente WHERE LOWER(codigo_cliente) = LOWER(?) AND es_activo = 1"
        resultado = execute_query(query, (codigo_cliente,))
        if resultado:
            raise ConflictError(
                detail=f"El código de cliente '{codigo_cliente}' ya está en uso.",
                internal_code="CLIENT_CODE_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_cliente(cliente_data: ClienteCreate) -> ClienteRead:
        """
        Crea un nuevo cliente en el sistema con todas sus validaciones.
        """
        logger.info(f"Creando nuevo cliente: {cliente_data.razon_social}")

        # Validaciones de unicidad
        await ClienteService._validar_subdominio_cliente(cliente_data.subdominio)
        await ClienteService._validar_codigo_cliente(cliente_data.codigo_cliente)

        # Preparar datos para inserción
        fields = [
            'codigo_cliente', 'subdominio', 'razon_social', 'nombre_comercial', 'ruc',
            'tipo_instalacion', 'servidor_api_local', 'modo_autenticacion', 'logo_url',
            'favicon_url', 'color_primario', 'color_secundario', 'tema_personalizado',
            'plan_suscripcion', 'estado_suscripcion', 'fecha_inicio_suscripcion',
            'fecha_fin_trial', 'contacto_nombre', 'contacto_email', 'contacto_telefono',
            'es_activo', 'es_demo'
        ]
        params = [getattr(cliente_data, field) for field in fields]

        query = f"""
        INSERT INTO cliente ({', '.join(fields)})
        OUTPUT 
            INSERTED.cliente_id,
            INSERTED.codigo_cliente,
            INSERTED.subdominio,
            INSERTED.razon_social,
            INSERTED.nombre_comercial,
            INSERTED.ruc,
            INSERTED.tipo_instalacion,
            INSERTED.servidor_api_local,
            INSERTED.modo_autenticacion,
            INSERTED.logo_url,
            INSERTED.favicon_url,
            INSERTED.color_primario,
            INSERTED.color_secundario,
            INSERTED.tema_personalizado,
            INSERTED.plan_suscripcion,
            INSERTED.estado_suscripcion,
            INSERTED.fecha_inicio_suscripcion,
            INSERTED.fecha_fin_trial,
            INSERTED.contacto_nombre,
            INSERTED.contacto_email,
            INSERTED.contacto_telefono,
            INSERTED.es_activo,
            INSERTED.es_demo,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.fecha_ultimo_acceso
        VALUES ({', '.join(['?'] * len(fields))})
        """

        resultado = execute_insert(query, tuple(params))
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el cliente en la base de datos.",
                internal_code="CLIENT_CREATION_FAILED"
            )

        logger.info(f"Cliente creado exitosamente con ID: {resultado['cliente_id']}")
        return ClienteRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_cliente_por_id(cliente_id: int) -> Optional[ClienteRead]:
        """
        Obtiene un cliente por su ID.
        """
        query = """
        SELECT 
            cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
            tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
            favicon_url, color_primario, color_secundario, tema_personalizado,
            plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
            fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
            es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        WHERE cliente_id = ?
        """
        resultado = execute_query(query, (cliente_id,))
        if not resultado:
            return None
        return ClienteRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def suspender_cliente(cliente_id: int) -> ClienteRead:
        """
        Suspende un cliente cambiando su estado de suscripción a 'suspendido'.
        """
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        if cliente.estado_suscripcion == "suspendido":
            raise ValidationError(
                detail=f"El cliente con ID {cliente_id} ya está suspendido.",
                internal_code="CLIENT_ALREADY_SUSPENDED"
            )

        query = """
        UPDATE cliente
        SET estado_suscripcion = 'suspendido',
            fecha_actualizacion = GETDATE()
        OUTPUT 
            INSERTED.cliente_id,
            INSERTED.codigo_cliente,
            INSERTED.subdominio,
            INSERTED.razon_social,
            INSERTED.nombre_comercial,
            INSERTED.ruc,
            INSERTED.tipo_instalacion,
            INSERTED.servidor_api_local,
            INSERTED.modo_autenticacion,
            INSERTED.logo_url,
            INSERTED.favicon_url,
            INSERTED.color_primario,
            INSERTED.color_secundario,
            INSERTED.tema_personalizado,
            INSERTED.plan_suscripcion,
            INSERTED.estado_suscripcion,
            INSERTED.fecha_inicio_suscripcion,
            INSERTED.fecha_fin_trial,
            INSERTED.contacto_nombre,
            INSERTED.contacto_email,
            INSERTED.contacto_telefono,
            INSERTED.es_activo,
            INSERTED.es_demo,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.fecha_ultimo_acceso
        WHERE cliente_id = ?
        """
        resultado = execute_update(query, (cliente_id,))
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo suspender el cliente.",
                internal_code="CLIENT_SUSPENSION_FAILED"
            )
        logger.info(f"Cliente ID {cliente_id} suspendido exitosamente.")
        return ClienteRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def activar_cliente(cliente_id: int) -> ClienteRead:
        """
        Reactiva un cliente cambiando su estado de suscripción a 'activo'.
        """
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        if cliente.estado_suscripcion == "activo":
            raise ValidationError(
                detail=f"El cliente con ID {cliente_id} ya está activo.",
                internal_code="CLIENT_ALREADY_ACTIVE"
            )

        query = """
        UPDATE cliente
        SET estado_suscripcion = 'activo',
            fecha_actualizacion = GETDATE()
        OUTPUT 
            INSERTED.cliente_id,
            INSERTED.codigo_cliente,
            INSERTED.subdominio,
            INSERTED.razon_social,
            INSERTED.nombre_comercial,
            INSERTED.ruc,
            INSERTED.tipo_instalacion,
            INSERTED.servidor_api_local,
            INSERTED.modo_autenticacion,
            INSERTED.logo_url,
            INSERTED.favicon_url,
            INSERTED.color_primario,
            INSERTED.color_secundario,
            INSERTED.tema_personalizado,
            INSERTED.plan_suscripcion,
            INSERTED.estado_suscripcion,
            INSERTED.fecha_inicio_suscripcion,
            INSERTED.fecha_fin_trial,
            INSERTED.contacto_nombre,
            INSERTED.contacto_email,
            INSERTED.contacto_telefono,
            INSERTED.es_activo,
            INSERTED.es_demo,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.fecha_ultimo_acceso
        WHERE cliente_id = ?
        """
        resultado = execute_update(query, (cliente_id,))
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo activar el cliente.",
                internal_code="CLIENT_ACTIVATION_FAILED"
            )
        logger.info(f"Cliente ID {cliente_id} activado exitosamente.")
        return ClienteRead(**resultado)