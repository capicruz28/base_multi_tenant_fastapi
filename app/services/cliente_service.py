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
from typing import Optional, Dict, Any, List
import re
import logging
from datetime import datetime
from app.db.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.services.base_service import BaseService
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteRead, ClienteStatsResponse, BrandingRead
from app.db.connection import DatabaseConnection

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
            'es_activo', 'es_demo', 'metadata_json',
            'api_key_sincronizacion', 'sincronizacion_habilitada', 'ultima_sincronizacion'
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
            INSERTED.metadata_json,
            INSERTED.api_key_sincronizacion,
            INSERTED.sincronizacion_habilitada,
            INSERTED.ultima_sincronizacion,
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
            es_activo, es_demo, metadata_json,
            api_key_sincronizacion, sincronizacion_habilitada, ultima_sincronizacion,
            fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        WHERE cliente_id = ?
        """
        resultado = execute_query(query, (cliente_id,),connection_type=DatabaseConnection.ADMIN)
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
            INSERTED.metadata_json,
            INSERTED.api_key_sincronizacion,
            INSERTED.sincronizacion_habilitada,
            INSERTED.ultima_sincronizacion,
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
            INSERTED.metadata_json,
            INSERTED.api_key_sincronizacion,
            INSERTED.sincronizacion_habilitada,
            INSERTED.ultima_sincronizacion,
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
    
    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_cliente(cliente_id: int, cliente_data: ClienteUpdate) -> ClienteRead:
        """
        Actualiza un cliente existente con validaciones.
        """
        logger.info(f"Actualizando cliente ID: {cliente_id}")
        
        # Verificar que el cliente existe
        cliente_existente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente_existente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        
        # Validar unicidad si se actualiza subdominio o código
        update_dict = cliente_data.dict(exclude_unset=True)
        
        if 'subdominio' in update_dict:
            # Validar que el nuevo subdominio no esté en uso por otro cliente
            query = """
            SELECT cliente_id FROM cliente 
            WHERE LOWER(subdominio) = LOWER(?) 
            AND cliente_id != ? 
            AND es_activo = 1
            """
            resultado = execute_query(query, (update_dict['subdominio'], cliente_id), connection_type=DatabaseConnection.ADMIN)
            if resultado:
                raise ConflictError(
                    detail=f"El subdominio '{update_dict['subdominio']}' ya está en uso por otro cliente.",
                    internal_code="SUBDOMAIN_CONFLICT"
                )
        
        if 'codigo_cliente' in update_dict:
            # Validar que el nuevo código no esté en uso por otro cliente
            query = """
            SELECT cliente_id FROM cliente 
            WHERE LOWER(codigo_cliente) = LOWER(?) 
            AND cliente_id != ? 
            AND es_activo = 1
            """
            resultado = execute_query(query, (update_dict['codigo_cliente'], cliente_id), connection_type=DatabaseConnection.ADMIN)
            if resultado:
                raise ConflictError(
                    detail=f"El código de cliente '{update_dict['codigo_cliente']}' ya está en uso.",
                    internal_code="CLIENT_CODE_CONFLICT"
                )
        
        # Construir query de actualización dinámica
        campos_actualizables = [
            'codigo_cliente', 'subdominio', 'razon_social', 'nombre_comercial', 'ruc',
            'tipo_instalacion', 'servidor_api_local', 'modo_autenticacion', 'logo_url',
            'favicon_url', 'color_primario', 'color_secundario', 'tema_personalizado',
            'plan_suscripcion', 'estado_suscripcion', 'fecha_inicio_suscripcion',
            'fecha_fin_trial', 'contacto_nombre', 'contacto_email', 'contacto_telefono',
            'es_activo', 'es_demo', 'metadata_json',
            'api_key_sincronizacion', 'sincronizacion_habilitada', 'ultima_sincronizacion'
        ]
        
        set_clauses = []
        params = []
        
        for campo in campos_actualizables:
            if campo in update_dict:
                set_clauses.append(f"{campo} = ?")
                params.append(update_dict[campo])
        
        if not set_clauses:
            # No hay campos para actualizar
            logger.warning(f"No hay campos para actualizar en cliente {cliente_id}")
            return cliente_existente
        
        # Agregar fecha_actualizacion
        set_clauses.append("fecha_actualizacion = GETDATE()")
        
        # Agregar cliente_id al final para el WHERE
        params.append(cliente_id)
        
        query = f"""
        UPDATE cliente
        SET {', '.join(set_clauses)}
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
            INSERTED.metadata_json,
            INSERTED.api_key_sincronizacion,
            INSERTED.sincronizacion_habilitada,
            INSERTED.ultima_sincronizacion,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.fecha_ultimo_acceso
        WHERE cliente_id = ?
        """
        
        resultado = execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado or resultado.get('rows_affected', 0) == 0:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar el cliente.",
                internal_code="CLIENT_UPDATE_FAILED"
            )
        
        logger.info(f"Cliente ID {cliente_id} actualizado exitosamente.")
        return ClienteRead(**resultado)
    
    @staticmethod
    @BaseService.handle_service_errors
    async def eliminar_cliente(cliente_id: int) -> bool:
        """
        Elimina un cliente (eliminación lógica - marca como inactivo).
        """
        logger.info(f"Eliminando cliente ID: {cliente_id}")
        
        # Verificar que el cliente existe
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        
        # No permitir eliminar el cliente SYSTEM
        from app.core.config import settings
        if cliente_id == settings.SUPERADMIN_CLIENTE_ID:
            raise ValidationError(
                detail="No se puede eliminar el cliente SYSTEM.",
                internal_code="CANNOT_DELETE_SYSTEM_CLIENT"
            )
        
        # Eliminación lógica: marcar como inactivo
        query = """
        UPDATE cliente
        SET es_activo = 0,
            estado_suscripcion = 'cancelado',
            fecha_actualizacion = GETDATE()
        WHERE cliente_id = ?
        """
        
        resultado = execute_update(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado or resultado.get('rows_affected', 0) == 0:
            raise ServiceError(
                status_code=500,
                detail="No se pudo eliminar el cliente.",
                internal_code="CLIENT_DELETE_FAILED"
            )
        
        logger.info(f"Cliente ID {cliente_id} eliminado exitosamente (marcado como inactivo).")
        return True
    
    @staticmethod
    @BaseService.handle_service_errors
    async def listar_clientes(
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True,
        buscar: Optional[str] = None
    ) -> tuple[List[ClienteRead], int]:
        """
        Lista clientes con paginación y búsqueda.
        
        Returns:
            Tuple[List[ClienteRead], int]: (lista de clientes, total de registros)
        """
        logger.info(f"Listando clientes - skip: {skip}, limit: {limit}, solo_activos: {solo_activos}, buscar: {buscar}")
        
        # Construir WHERE clause
        where_conditions = []
        params = []
        
        if solo_activos:
            where_conditions.append("es_activo = 1")
        
        if buscar:
            where_conditions.append("""
                (LOWER(razon_social) LIKE LOWER(?) OR 
                 LOWER(nombre_comercial) LIKE LOWER(?) OR 
                 LOWER(codigo_cliente) LIKE LOWER(?) OR 
                 LOWER(subdominio) LIKE LOWER(?))
            """)
            search_pattern = f"%{buscar}%"
            params.extend([search_pattern] * 4)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Query para contar total
        count_query = f"SELECT COUNT(*) as total FROM cliente {where_clause}"
        count_result = execute_query(count_query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        total = count_result[0]['total'] if count_result else 0
        
        # Query para obtener datos
        query = f"""
        SELECT 
            cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
            tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
            favicon_url, color_primario, color_secundario, tema_personalizado,
            plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
            fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
            es_activo, es_demo, metadata_json,
            api_key_sincronizacion, sincronizacion_habilitada, ultima_sincronizacion,
            fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
        FROM cliente
        {where_clause}
        ORDER BY razon_social
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        
        params.extend([skip, limit])
        resultados = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        
        clientes = [ClienteRead(**row) for row in resultados]
        logger.info(f"Listados {len(clientes)} clientes de {total} totales")
        
        return clientes, total
    
    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_estadisticas(cliente_id: int) -> ClienteStatsResponse:
        """
        Obtiene estadísticas completas de un cliente.
        """
        logger.info(f"Obteniendo estadísticas para cliente ID: {cliente_id}")
        
        # Verificar que el cliente existe
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        
        # Estadísticas de usuarios
        usuarios_query = """
        SELECT 
            COUNT(CASE WHEN es_activo = 1 THEN 1 END) as total_activos,
            COUNT(CASE WHEN es_activo = 0 THEN 1 END) as total_inactivos
        FROM usuario
        WHERE cliente_id = ? AND es_eliminado = 0
        """
        usuarios_result = execute_query(usuarios_query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        usuarios_stats = usuarios_result[0] if usuarios_result else {'total_activos': 0, 'total_inactivos': 0}
        
        # Estadísticas de módulos
        modulos_query = """
        SELECT 
            COUNT(CASE WHEN esta_activo = 1 THEN 1 END) as modulos_activos,
            COUNT(*) as modulos_contratados
        FROM cliente_modulo_activo
        WHERE cliente_id = ?
        """
        modulos_result = execute_query(modulos_query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        modulos_stats = modulos_result[0] if modulos_result else {'modulos_activos': 0, 'modulos_contratados': 0}
        
        # Estadísticas de conexiones BD
        conexiones_query = """
        SELECT COUNT(*) as total_conexiones
        FROM cliente_modulo_conexion
        WHERE cliente_id = ? AND es_activo = 1
        """
        conexiones_result = execute_query(conexiones_query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        conexiones_count = conexiones_result[0]['total_conexiones'] if conexiones_result else 0
        
        # Calcular días activo
        dias_activo = 0
        if cliente.fecha_creacion:
            delta = datetime.now() - cliente.fecha_creacion
            dias_activo = delta.days
        
        stats = ClienteStatsResponse(
            cliente_id=cliente.cliente_id,
            razon_social=cliente.razon_social,
            total_usuarios=usuarios_stats.get('total_activos', 0),
            total_usuarios_inactivos=usuarios_stats.get('total_inactivos', 0),
            modulos_activos=modulos_stats.get('modulos_activos', 0),
            modulos_contratados=modulos_stats.get('modulos_contratados', 0),
            ultimo_acceso=cliente.fecha_ultimo_acceso,
            estado_suscripcion=cliente.estado_suscripcion,
            plan_actual=cliente.plan_suscripcion,
            fecha_creacion=cliente.fecha_creacion,
            dias_activo=dias_activo,
            conexiones_bd=conexiones_count,
            tipo_instalacion=cliente.tipo_instalacion
        )
        
        logger.info(f"Estadísticas obtenidas para cliente {cliente_id}")
        return stats

    @staticmethod
    @BaseService.handle_service_errors
    async def get_branding_by_cliente(cliente_id: int) -> BrandingRead:
        """
        Obtiene la configuración de branding de un cliente.
        
        Optimizado para solo leer los campos de branding sin cargar
        relaciones innecesarias. Este método es utilizado por el endpoint
        de branding del tenant actual.
        
        Args:
            cliente_id: ID del cliente (del tenant context)
            
        Returns:
            BrandingRead con la configuración de branding
            
        Raises:
            NotFoundError: Si el cliente no existe o está inactivo
            ServiceError: Si hay error en la consulta
        """
        logger.info(f"Solicitando branding para cliente_id={cliente_id}")
        
        # Query optimizada: solo campos de branding
        query = """
        SELECT 
            logo_url,
            favicon_url,
            color_primario,
            color_secundario,
            tema_personalizado,
            es_activo
        FROM cliente
        WHERE cliente_id = ?
        """
        
        resultado = execute_query(query, (cliente_id,))
        
        if not resultado or len(resultado) == 0:
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} no encontrado.",
                internal_code="CLIENT_NOT_FOUND"
            )
        
        row = resultado[0]
        
        # Validar que el cliente esté activo
        if not row.get('es_activo', False):
            raise NotFoundError(
                detail=f"Cliente con ID {cliente_id} está inactivo.",
                internal_code="CLIENT_INACTIVE"
            )
        
        # Parsear tema_personalizado de JSON string a dict
        tema_personalizado = None
        if row.get('tema_personalizado'):
            try:
                import json
                tema_personalizado = json.loads(row['tema_personalizado'])
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Error parseando tema_personalizado para cliente {cliente_id}: {e}")
                tema_personalizado = None
        
        # Construir respuesta
        branding = BrandingRead(
            logo_url=row.get('logo_url'),
            favicon_url=row.get('favicon_url'),
            color_primario=row.get('color_primario', '#1976D2'),
            color_secundario=row.get('color_secundario', '#424242'),
            tema_personalizado=tema_personalizado
        )
        
        logger.info(f"Branding obtenido exitosamente para cliente_id={cliente_id}")
        return branding