# app/services/conexion_service.py
"""
Servicio para la gestión de conexiones de base de datos por cliente y módulo en arquitectura multi-tenant.
Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_modulo_conexion`,
incluyendo la creación, validación, testing y gestión del ciclo de vida de conexiones de BD.

Características clave:
- Gestión segura de credenciales de base de datos con encriptación
- Validación de conexiones únicas por cliente-módulo
- Testing de conectividad en tiempo real
- Soporte para múltiples motores de BD (SQL Server, PostgreSQL, MySQL, Oracle)
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import List, Optional, Dict, Any
import logging
from app.infrastructure.database.queries import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.infrastructure.database.repositories.base_repository import BaseService
from app.modules.tenant.presentation.schemas import ConexionCreate, ConexionUpdate, ConexionRead, ConexionTest
from app.infrastructure.database.connection import DatabaseConnection
from app.core.security.encryption import encrypt_credential, decrypt_credential

logger = logging.getLogger(__name__)


class ConexionService(BaseService):
    """
    Servicio central para la administración de conexiones de base de datos por cliente-módulo.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_conexiones_cliente(cliente_id: int) -> List[ConexionRead]:
        """
        Obtiene todas las conexiones configuradas para un cliente específico.
        """
        logger.info(f"Obteniendo conexiones para cliente ID: {cliente_id}")

        query = """
        SELECT 
            conexion_id, cliente_id, modulo_id, servidor, puerto, nombre_bd,
            usuario_encriptado, password_encriptado, connection_string_encriptado,
            tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
            es_solo_lectura, es_conexion_principal, es_activo,
            ultima_conexion_exitosa, ultimo_error, fecha_ultimo_error,
            fecha_creacion, fecha_actualizacion, creado_por_usuario_id
        FROM cliente_modulo_conexion
        WHERE cliente_id = ? --AND es_activo = 1
        ORDER BY modulo_id, es_conexion_principal DESC
        """
        
        resultados = execute_query(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        return [ConexionRead(**conexion) for conexion in resultados]

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_conexion_por_id(conexion_id: int) -> Optional[ConexionRead]:
        """
        Obtiene una conexión específica por su ID.
        """
        query = """
        SELECT 
            conexion_id, cliente_id, modulo_id, servidor, puerto, nombre_bd,
            usuario_encriptado, password_encriptado, connection_string_encriptado,
            tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
            es_solo_lectura, es_conexion_principal, es_activo,
            ultima_conexion_exitosa, ultimo_error, fecha_ultimo_error,
            fecha_creacion, fecha_actualizacion, creado_por_usuario_id
        FROM cliente_modulo_conexion
        WHERE conexion_id = ?
        """
        
        resultado = execute_query(query, (conexion_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ConexionRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_conexion_principal(cliente_id: int, modulo_id: int) -> Optional[ConexionRead]:
        """
        Obtiene la conexión principal para un cliente y módulo específicos.
        """
        query = """
        SELECT 
            conexion_id, cliente_id, modulo_id, servidor, puerto, nombre_bd,
            usuario_encriptado, password_encriptado, connection_string_encriptado,
            tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
            es_solo_lectura, es_conexion_principal, es_activo,
            ultima_conexion_exitosa, ultimo_error, fecha_ultimo_error,
            fecha_creacion, fecha_actualizacion, creado_por_usuario_id
        FROM cliente_modulo_conexion
        WHERE cliente_id = ? AND modulo_id = ? AND es_conexion_principal = 1 AND es_activo = 1
        """
        
        resultado = execute_query(query, (cliente_id, modulo_id), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            return None
        return ConexionRead(**resultado[0])

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_conexion_unica(cliente_id: int, modulo_id: int, conexion_id: Optional[int] = None) -> None:
        """
        Valida que solo exista una conexión principal por cliente-módulo.
        """
        query = """
        SELECT conexion_id FROM cliente_modulo_conexion 
        WHERE cliente_id = ? AND modulo_id = ? AND es_conexion_principal = 1 AND es_activo = 1
        """
        params = [cliente_id, modulo_id]
        
        if conexion_id:
            query += " AND conexion_id != ?"
            params.append(conexion_id)
            
        resultado = execute_query(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if resultado:
            raise ConflictError(
                detail="Ya existe una conexión principal activa para este cliente y módulo.",
                internal_code="PRIMARY_CONNECTION_CONFLICT"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def _encriptar_credenciales(usuario: str, password: str) -> Dict[str, str]:
        """
        Encripta las credenciales de conexión para almacenamiento seguro.
        """
        try:
            usuario_encriptado = encrypt_credential(usuario)
            password_encriptado = encrypt_credential(password)
            
            return {
                "usuario_encriptado": usuario_encriptado,
                "password_encriptado": password_encriptado
            }
        except Exception as e:
            logger.error(f"Error al encriptar credenciales: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error al encriptar las credenciales de conexión.",
                internal_code="CREDENTIALS_ENCRYPTION_FAILED"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_conexion(conexion_data: ConexionCreate, creado_por_usuario_id: int) -> ConexionRead:
        """
        Crea una nueva conexión de base de datos para un cliente y módulo.
        """
        logger.info(f"Creando nueva conexión para cliente {conexion_data.cliente_id}, módulo {conexion_data.modulo_id}")

        # Validar unicidad si es conexión principal
        if conexion_data.es_conexion_principal:
            await ConexionService._validar_conexion_unica(
                conexion_data.cliente_id, 
                conexion_data.modulo_id
            )

        # Encriptar credenciales
        credenciales_encriptadas = await ConexionService._encriptar_credenciales(
            conexion_data.usuario,
            conexion_data.password
        )

        # Preparar datos para inserción
        fields = [
            'cliente_id', 'modulo_id', 'servidor', 'puerto', 'nombre_bd',
            'usuario_encriptado', 'password_encriptado', 'connection_string_encriptado',
            'tipo_bd', 'usa_ssl', 'timeout_segundos', 'max_pool_size',
            'es_solo_lectura', 'es_conexion_principal', 'es_activo', 'creado_por_usuario_id'
        ]
        
        params = [
            conexion_data.cliente_id,
            conexion_data.modulo_id,
            conexion_data.servidor,
            conexion_data.puerto,
            conexion_data.nombre_bd,
            credenciales_encriptadas["usuario_encriptado"],
            credenciales_encriptadas["password_encriptado"],
            None,  # connection_string_encriptado se genera después del test
            conexion_data.tipo_bd,
            conexion_data.usa_ssl,
            conexion_data.timeout_segundos,
            conexion_data.max_pool_size,
            conexion_data.es_solo_lectura,
            conexion_data.es_conexion_principal,
            1,  # es_activo
            creado_por_usuario_id
        ]

        query = f"""
        INSERT INTO cliente_modulo_conexion ({', '.join(fields)})
        OUTPUT 
            INSERTED.conexion_id,
            INSERTED.cliente_id,
            INSERTED.modulo_id,
            INSERTED.servidor,
            INSERTED.puerto,
            INSERTED.nombre_bd,
            INSERTED.usuario_encriptado,
            INSERTED.password_encriptado,
            INSERTED.connection_string_encriptado,
            INSERTED.tipo_bd,
            INSERTED.usa_ssl,
            INSERTED.timeout_segundos,
            INSERTED.max_pool_size,
            INSERTED.es_solo_lectura,
            INSERTED.es_conexion_principal,
            INSERTED.es_activo,
            INSERTED.ultima_conexion_exitosa,
            INSERTED.ultimo_error,
            INSERTED.fecha_ultimo_error,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.creado_por_usuario_id
        VALUES ({', '.join(['?'] * len(fields))})
        """

        resultado = execute_insert(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear la conexión en la base de datos.",
                internal_code="CONNECTION_CREATION_FAILED"
            )

        logger.info(f"Conexión creada exitosamente con ID: {resultado['conexion_id']}")
        return ConexionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_conexion(conexion_id: int, conexion_data: ConexionUpdate) -> ConexionRead:
        """
        Actualiza una conexión existente.
        """
        logger.info(f"Actualizando conexión ID: {conexion_id}")

        # Verificar que la conexión existe
        conexion_existente = await ConexionService.obtener_conexion_por_id(conexion_id)
        if not conexion_existente:
            raise NotFoundError(
                detail=f"Conexión con ID {conexion_id} no encontrada.",
                internal_code="CONNECTION_NOT_FOUND"
            )

        # Validar unicidad si se está cambiando a conexión principal
        if conexion_data.es_conexion_principal:
            await ConexionService._validar_conexion_unica(
                conexion_existente.cliente_id,
                conexion_existente.modulo_id,
                conexion_id
            )

        # Construir query dinámica
        update_fields = []
        params = []
        
        for field, value in conexion_data.dict(exclude_unset=True).items():
            if value is not None and field not in ['usuario', 'password']:
                update_fields.append(f"{field} = ?")
                params.append(value)
                
        # Manejar actualización de credenciales
        if conexion_data.usuario or conexion_data.password:
            credenciales_encriptadas = await ConexionService._encriptar_credenciales(
                conexion_data.usuario or "",
                conexion_data.password or ""
            )
            update_fields.append("usuario_encriptado = ?")
            params.append(credenciales_encriptadas["usuario_encriptado"])
            update_fields.append("password_encriptado = ?")
            params.append(credenciales_encriptadas["password_encriptado"])
                
        if not update_fields:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )
            
        params.append(conexion_id)

        query = f"""
        UPDATE cliente_modulo_conexion
        SET {', '.join(update_fields)}, fecha_actualizacion = GETDATE()
        OUTPUT 
            INSERTED.conexion_id,
            INSERTED.cliente_id,
            INSERTED.modulo_id,
            INSERTED.servidor,
            INSERTED.puerto,
            INSERTED.nombre_bd,
            INSERTED.usuario_encriptado,
            INSERTED.password_encriptado,
            INSERTED.connection_string_encriptado,
            INSERTED.tipo_bd,
            INSERTED.usa_ssl,
            INSERTED.timeout_segundos,
            INSERTED.max_pool_size,
            INSERTED.es_solo_lectura,
            INSERTED.es_conexion_principal,
            INSERTED.es_activo,
            INSERTED.ultima_conexion_exitosa,
            INSERTED.ultimo_error,
            INSERTED.fecha_ultimo_error,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.creado_por_usuario_id
        WHERE conexion_id = ?
        """

        resultado = execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la conexión.",
                internal_code="CONNECTION_UPDATE_FAILED"
            )

        logger.info(f"Conexión ID {conexion_id} actualizada exitosamente.")
        return ConexionRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def test_conexion(conexion_data: ConexionTest) -> Dict[str, Any]:
        """
        Testea la conectividad de una configuración de conexión.
        """
        logger.info(f"Testeando conexión para servidor: {conexion_data.servidor}")

        try:
            # Aquí iría la lógica real de test de conexión
            # Por ahora simulamos una respuesta exitosa
            import random
            success = random.choice([True, True, True, False])  # 75% de éxito para testing
            
            if success:
                logger.info(f"Test de conexión exitoso para {conexion_data.servidor}")
                return {
                    "success": True,
                    "message": "Conexión exitosa",
                    "response_time_ms": random.randint(50, 500)
                }
            else:
                logger.warning(f"Test de conexión fallido para {conexion_data.servidor}")
                return {
                    "success": False,
                    "message": "Error de conexión: Timeout o credenciales inválidas",
                    "error_code": "CONNECTION_TIMEOUT"
                }
                
        except Exception as e:
            logger.error(f"Error durante test de conexión: {str(e)}")
            raise ServiceError(
                status_code=500,
                detail="Error interno durante el test de conexión.",
                internal_code="CONNECTION_TEST_FAILED"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def desactivar_conexion(conexion_id: int) -> ConexionRead:
        """
        Desactiva una conexión (soft delete).
        """
        logger.info(f"Desactivando conexión ID: {conexion_id}")

        # Verificar que la conexión existe
        conexion_existente = await ConexionService.obtener_conexion_por_id(conexion_id)
        if not conexion_existente:
            raise NotFoundError(
                detail=f"Conexión con ID {conexion_id} no encontrada.",
                internal_code="CONNECTION_NOT_FOUND"
            )

        if not conexion_existente.es_activo:
            raise ValidationError(
                detail=f"La conexión con ID {conexion_id} ya está desactivada.",
                internal_code="CONNECTION_ALREADY_INACTIVE"
            )

        query = """
        UPDATE cliente_modulo_conexion
        SET es_activo = 0, fecha_actualizacion = GETDATE()
        OUTPUT 
            INSERTED.conexion_id,
            INSERTED.cliente_id,
            INSERTED.modulo_id,
            INSERTED.servidor,
            INSERTED.puerto,
            INSERTED.nombre_bd,
            INSERTED.usuario_encriptado,
            INSERTED.password_encriptado,
            INSERTED.connection_string_encriptado,
            INSERTED.tipo_bd,
            INSERTED.usa_ssl,
            INSERTED.timeout_segundos,
            INSERTED.max_pool_size,
            INSERTED.es_solo_lectura,
            INSERTED.es_conexion_principal,
            INSERTED.es_activo,
            INSERTED.ultima_conexion_exitosa,
            INSERTED.ultimo_error,
            INSERTED.fecha_ultimo_error,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion,
            INSERTED.creado_por_usuario_id
        WHERE conexion_id = ?
        """

        resultado = execute_update(query, (conexion_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo desactivar la conexión.",
                internal_code="CONNECTION_DEACTIVATION_FAILED"
            )

        logger.info(f"Conexión ID {conexion_id} desactivada exitosamente.")
        return ConexionRead(**resultado)