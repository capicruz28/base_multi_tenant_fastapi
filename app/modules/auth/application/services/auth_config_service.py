# app/services/auth_config_service.py
"""
Servicio para la gestión de configuraciones de autenticación por cliente en arquitectura multi-tenant.
Este servicio implementa la lógica de negocio para operaciones sobre la entidad `cliente_auth_config`,
incluyendo la configuración de políticas de seguridad, validación de reglas de negocio,
y aplicación de configuraciones por defecto.

Características clave:
- Gestión centralizada de políticas de seguridad por cliente
- Validación de configuraciones de autenticación
- Aplicación de valores por defecto coherentes
- Soporte para políticas de contraseña, 2FA, control de sesiones
- Total coherencia con los patrones de BaseService y manejo de excepciones del sistema
"""
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from sqlalchemy import text
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
    DatabaseError
)
from app.core.application.base_service import BaseService
from app.modules.auth.presentation.schemas import AuthConfigCreate, AuthConfigUpdate, AuthConfigRead
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)


class AuthConfigService(BaseService):
    """
    Servicio central para la administración de configuraciones de autenticación por cliente.
    """

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_config_cliente(cliente_id: UUID) -> AuthConfigRead:
        """
        Obtiene la configuración de autenticación para un cliente específico.
        Si no existe, crea una configuración por defecto.
        """
        logger.info(f"Obteniendo configuración de autenticación para cliente ID: {cliente_id}")

        query = """
        SELECT 
            config_id, cliente_id, password_min_length, password_require_uppercase,
            password_require_lowercase, password_require_number, password_require_special,
            password_expiry_days, password_history_count, max_login_attempts,
            lockout_duration_minutes, max_active_sessions, session_idle_timeout_minutes,
            access_token_minutes, refresh_token_days, allow_remember_me,
            remember_me_days, require_email_verification, allow_password_reset,
            enable_2fa, require_2fa_for_admins, metodos_2fa_permitidos,
            ip_whitelist_enabled, ip_whitelist, ip_blacklist,
            horario_acceso_enabled, horario_acceso_config,
            fecha_creacion, fecha_actualizacion
        FROM cliente_auth_config
        WHERE cliente_id = :cliente_id
        """
        
        # ✅ FASE 2: Usar await
        resultado = await execute_query(
            text(query).bindparams(cliente_id=cliente_id),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        if resultado:
            return AuthConfigRead(**resultado[0])
        else:
            # Crear configuración por defecto si no existe
            logger.info(f"Creando configuración por defecto para cliente ID: {cliente_id}")
            return await AuthConfigService.crear_config_default(cliente_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_config_default(cliente_id: UUID) -> AuthConfigRead:
        """
        Crea una configuración de autenticación por defecto para un cliente.
        """
        config_default = AuthConfigCreate(
            cliente_id=cliente_id,
            password_min_length=8,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_number=True,
            password_require_special=False,
            password_expiry_days=90,
            password_history_count=3,
            max_login_attempts=5,
            lockout_duration_minutes=30,
            max_active_sessions=3,
            session_idle_timeout_minutes=60,
            access_token_minutes=15,
            refresh_token_days=30,
            allow_remember_me=True,
            remember_me_days=30,
            require_email_verification=False,
            allow_password_reset=True,
            enable_2fa=False,
            require_2fa_for_admins=False,
            metodos_2fa_permitidos="email,sms",
            ip_whitelist_enabled=False,
            ip_whitelist=None,
            ip_blacklist=None,
            horario_acceso_enabled=False,
            horario_acceso_config=None
        )

        return await AuthConfigService.crear_config_cliente(config_default)

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_config_cliente(config_data: AuthConfigCreate) -> AuthConfigRead:
        """
        Crea una nueva configuración de autenticación para un cliente.
        """
        logger.info(f"Creando configuración de autenticación para cliente ID: {config_data.cliente_id}")

        # Validar que el cliente existe y no tiene configuración
        query_check = "SELECT config_id FROM cliente_auth_config WHERE cliente_id = :cliente_id"
        # ✅ FASE 2: Usar await
        resultado_existente = await execute_query(
            text(query_check).bindparams(cliente_id=config_data.cliente_id),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None
        )
        
        if resultado_existente:
            raise ConflictError(
                detail=f"El cliente ID {config_data.cliente_id} ya tiene una configuración de autenticación.",
                internal_code="AUTH_CONFIG_ALREADY_EXISTS"
            )

        # Validar configuraciones
        await AuthConfigService._validar_configuracion(config_data)

        # Preparar datos para inserción
        fields = [
            'cliente_id', 'password_min_length', 'password_require_uppercase',
            'password_require_lowercase', 'password_require_number', 'password_require_special',
            'password_expiry_days', 'password_history_count', 'max_login_attempts',
            'lockout_duration_minutes', 'max_active_sessions', 'session_idle_timeout_minutes',
            'access_token_minutes', 'refresh_token_days', 'allow_remember_me',
            'remember_me_days', 'require_email_verification', 'allow_password_reset',
            'enable_2fa', 'require_2fa_for_admins', 'metodos_2fa_permitidos',
            'ip_whitelist_enabled', 'ip_whitelist', 'ip_blacklist',
            'horario_acceso_enabled', 'horario_acceso_config'
        ]
        params = [getattr(config_data, field) for field in fields]

        query = f"""
        INSERT INTO cliente_auth_config ({', '.join(fields)})
        OUTPUT 
            INSERTED.config_id,
            INSERTED.cliente_id,
            INSERTED.password_min_length,
            INSERTED.password_require_uppercase,
            INSERTED.password_require_lowercase,
            INSERTED.password_require_number,
            INSERTED.password_require_special,
            INSERTED.password_expiry_days,
            INSERTED.password_history_count,
            INSERTED.max_login_attempts,
            INSERTED.lockout_duration_minutes,
            INSERTED.max_active_sessions,
            INSERTED.session_idle_timeout_minutes,
            INSERTED.access_token_minutes,
            INSERTED.refresh_token_days,
            INSERTED.allow_remember_me,
            INSERTED.remember_me_days,
            INSERTED.require_email_verification,
            INSERTED.allow_password_reset,
            INSERTED.enable_2fa,
            INSERTED.require_2fa_for_admins,
            INSERTED.metodos_2fa_permitidos,
            INSERTED.ip_whitelist_enabled,
            INSERTED.ip_whitelist,
            INSERTED.ip_blacklist,
            INSERTED.horario_acceso_enabled,
            INSERTED.horario_acceso_config,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion
        VALUES ({', '.join(['?'] * len(fields))})
        """

        # ✅ FASE 2: Usar await
        resultado = await execute_insert(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear la configuración de autenticación.",
                internal_code="AUTH_CONFIG_CREATION_FAILED"
            )

        logger.info(f"Configuración de autenticación creada exitosamente con ID: {resultado['config_id']}")
        return AuthConfigRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_config_cliente(cliente_id: UUID, config_data: AuthConfigUpdate) -> AuthConfigRead:
        """
        Actualiza la configuración de autenticación para un cliente.
        """
        logger.info(f"Actualizando configuración de autenticación para cliente ID: {cliente_id}")

        # Verificar que la configuración existe
        config_existente = await AuthConfigService.obtener_config_cliente(cliente_id)
        if not config_existente:
            raise NotFoundError(
                detail=f"Configuración de autenticación para cliente ID {cliente_id} no encontrada.",
                internal_code="AUTH_CONFIG_NOT_FOUND"
            )

        # Validar configuraciones actualizadas
        config_actualizada = config_existente.copy(update=config_data.dict(exclude_unset=True))
        await AuthConfigService._validar_configuracion(config_actualizada)

        # Construir query dinámica
        update_fields = []
        params = []
        
        for field, value in config_data.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                params.append(value)
                
        if not update_fields:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS"
            )
            
        params.append(cliente_id)

        query = f"""
        UPDATE cliente_auth_config
        SET {', '.join(update_fields)}, fecha_actualizacion = GETDATE()
        OUTPUT 
            INSERTED.config_id,
            INSERTED.cliente_id,
            INSERTED.password_min_length,
            INSERTED.password_require_uppercase,
            INSERTED.password_require_lowercase,
            INSERTED.password_require_number,
            INSERTED.password_require_special,
            INSERTED.password_expiry_days,
            INSERTED.password_history_count,
            INSERTED.max_login_attempts,
            INSERTED.lockout_duration_minutes,
            INSERTED.max_active_sessions,
            INSERTED.session_idle_timeout_minutes,
            INSERTED.access_token_minutes,
            INSERTED.refresh_token_days,
            INSERTED.allow_remember_me,
            INSERTED.remember_me_days,
            INSERTED.require_email_verification,
            INSERTED.allow_password_reset,
            INSERTED.enable_2fa,
            INSERTED.require_2fa_for_admins,
            INSERTED.metodos_2fa_permitidos,
            INSERTED.ip_whitelist_enabled,
            INSERTED.ip_whitelist,
            INSERTED.ip_blacklist,
            INSERTED.horario_acceso_enabled,
            INSERTED.horario_acceso_config,
            INSERTED.fecha_creacion,
            INSERTED.fecha_actualizacion
        WHERE cliente_id = ?
        """

        # ✅ FASE 2: Usar await
        resultado = await execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la configuración de autenticación.",
                internal_code="AUTH_CONFIG_UPDATE_FAILED"
            )

        logger.info(f"Configuración de autenticación para cliente ID {cliente_id} actualizada exitosamente.")
        return AuthConfigRead(**resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_configuracion(config_data: AuthConfigRead) -> None:
        """
        Valida la coherencia de la configuración de autenticación.
        """
        # Validar políticas de contraseña
        if config_data.password_min_length < 6:
            raise ValidationError(
                detail="La longitud mínima de contraseña debe ser al menos 6 caracteres.",
                internal_code="PASSWORD_MIN_LENGTH_INVALID"
            )

        if config_data.password_expiry_days < 0:
            raise ValidationError(
                detail="Los días de expiración de contraseña no pueden ser negativos.",
                internal_code="PASSWORD_EXPIRY_INVALID"
            )

        if config_data.max_login_attempts < 1:
            raise ValidationError(
                detail="El número máximo de intentos de login debe ser al menos 1.",
                internal_code="MAX_LOGIN_ATTEMPTS_INVALID"
            )

        if config_data.lockout_duration_minutes < 1:
            raise ValidationError(
                detail="La duración del bloqueo debe ser al menos 1 minuto.",
                internal_code="LOCKOUT_DURATION_INVALID"
            )

        if config_data.access_token_minutes < 1:
            raise ValidationError(
                detail="La duración del access token debe ser al menos 1 minuto.",
                internal_code="ACCESS_TOKEN_DURATION_INVALID"
            )

        if config_data.refresh_token_days < 1:
            raise ValidationError(
                detail="La duración del refresh token debe ser al menos 1 día.",
                internal_code="REFRESH_TOKEN_DURATION_INVALID"
            )

        # Validar 2FA
        if config_data.enable_2fa and not config_data.metodos_2fa_permitidos:
            raise ValidationError(
                detail="Debe especificar al menos un método de 2FA permitido.",
                internal_code="2FA_METHODS_REQUIRED"
            )

        # Validar horarios de acceso si están habilitados
        if config_data.horario_acceso_enabled and not config_data.horario_acceso_config:
            raise ValidationError(
                detail="Debe proporcionar la configuración de horarios de acceso.",
                internal_code="ACCESS_SCHEDULE_CONFIG_REQUIRED"
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_config_global() -> AuthConfigRead:
        """
        Obtiene la configuración de autenticación por defecto del sistema.
        """
        logger.info("Obteniendo configuración de autenticación global por defecto")

        # Retornar configuración por defecto sin cliente específico
        return AuthConfigRead(
            config_id=0,
            cliente_id=0,
            password_min_length=8,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_number=True,
            password_require_special=False,
            password_expiry_days=90,
            password_history_count=3,
            max_login_attempts=5,
            lockout_duration_minutes=30,
            max_active_sessions=3,
            session_idle_timeout_minutes=60,
            access_token_minutes=15,
            refresh_token_days=30,
            allow_remember_me=True,
            remember_me_days=30,
            require_email_verification=False,
            allow_password_reset=True,
            enable_2fa=False,
            require_2fa_for_admins=False,
            metodos_2fa_permitidos="email,sms",
            ip_whitelist_enabled=False,
            ip_whitelist=None,
            ip_blacklist=None,
            horario_acceso_enabled=False,
            horario_acceso_config=None,
            fecha_creacion=None,
            fecha_actualizacion=None
        )