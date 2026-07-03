# app/services/auth_config_service.py
"""
Servicio para la gestión de configuraciones de autenticación por cliente en arquitectura multi-tenant.
Delega I/O de cliente_auth_config en AuthConfigGateway (ADR-012).
"""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from app.core.auth.auth_config_gateway import AuthConfigGateway
from app.core.exceptions import (
    ValidationError,
    ConflictError,
    NotFoundError,
    ServiceError,
)
from app.core.application.base_service import BaseService
from app.modules.auth.presentation.schemas import AuthConfigCreate, AuthConfigUpdate, AuthConfigRead

logger = logging.getLogger(__name__)

_SYSTEM_TEMPLATE_UUID = UUID("00000000-0000-0000-0000-000000000000")
_NULLABLE_AUTH_CONFIG_FIELDS = frozenset({
    "fecha_actualizacion",
    "ip_whitelist",
    "ip_blacklist",
    "horario_acceso_config",
})

_CREATE_FIELDS = (
    "cliente_id",
    "password_min_length",
    "password_require_uppercase",
    "password_require_lowercase",
    "password_require_number",
    "password_require_special",
    "password_expiry_days",
    "password_history_count",
    "max_login_attempts",
    "lockout_duration_minutes",
    "max_active_sessions",
    "session_idle_timeout_minutes",
    "access_token_minutes",
    "refresh_token_days",
    "allow_remember_me",
    "remember_me_days",
    "require_email_verification",
    "allow_password_reset",
    "enable_2fa",
    "require_2fa_for_admins",
    "metodos_2fa_permitidos",
    "ip_whitelist_enabled",
    "ip_whitelist",
    "ip_blacklist",
    "horario_acceso_enabled",
    "horario_acceso_config",
)


async def leer_expiracion_tokens_cliente(cliente_id: UUID) -> Dict[str, int]:
    """Wrapper retrocompatible — delega en AuthConfigGateway."""
    return await AuthConfigGateway.get_token_expiration(cliente_id)


async def leer_session_idle_timeout_minutos(cliente_id: UUID) -> Optional[int]:
    """Wrapper retrocompatible — delega en AuthConfigGateway."""
    return await AuthConfigGateway.get_session_idle_timeout_minutes(cliente_id)


async def leer_max_active_sessions(cliente_id: UUID) -> Optional[int]:
    """Wrapper retrocompatible — delega en AuthConfigGateway."""
    return await AuthConfigGateway.get_max_active_sessions(cliente_id)


class AuthConfigService(BaseService):
    """
    Servicio central para la administración de configuraciones de autenticación por cliente.
    """

    @staticmethod
    def _build_auth_config_read(row: Dict[str, Any]) -> AuthConfigRead:
        """Normaliza filas BD (NULL en columnas con default) para AuthConfigRead."""
        payload = dict(row)
        for key in list(payload.keys()):
            if payload[key] is None and key not in _NULLABLE_AUTH_CONFIG_FIELDS:
                payload.pop(key)
        if not payload.get("fecha_creacion"):
            payload["fecha_creacion"] = datetime.utcnow()
        return AuthConfigRead(**payload)

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_config_cliente(cliente_id: UUID) -> AuthConfigRead:
        """
        Obtiene la configuración de autenticación para un cliente específico.
        Si no existe, crea una configuración por defecto.
        """
        logger.info(f"Obteniendo configuración de autenticación para cliente ID: {cliente_id}")

        resultado = await AuthConfigGateway.get_config_by_cliente_id(cliente_id)

        if resultado:
            return AuthConfigService._build_auth_config_read(resultado)

        logger.info(f"Creando configuración por defecto para cliente ID: {cliente_id}")
        return await AuthConfigService.crear_config_default(cliente_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_config_default(cliente_id: UUID) -> AuthConfigRead:
        """
        Crea una configuración de autenticación por defecto para un cliente.
        """
        config_default = AuthConfigCreate.model_construct(
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
            horario_acceso_config=None,
        )

        return await AuthConfigService.crear_config_cliente(config_default)

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_config_cliente(config_data: AuthConfigCreate) -> AuthConfigRead:
        """
        Crea una nueva configuración de autenticación para un cliente.
        """
        logger.info(f"Creando configuración de autenticación para cliente ID: {config_data.cliente_id}")

        if await AuthConfigGateway.config_exists(config_data.cliente_id):
            raise ConflictError(
                detail=f"El cliente ID {config_data.cliente_id} ya tiene una configuración de autenticación.",
                internal_code="AUTH_CONFIG_ALREADY_EXISTS",
            )

        await AuthConfigService._validar_configuracion(config_data)

        payload = {field: getattr(config_data, field) for field in _CREATE_FIELDS}
        resultado = await AuthConfigGateway.insert_config(payload)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear la configuración de autenticación.",
                internal_code="AUTH_CONFIG_CREATION_FAILED",
            )

        logger.info(f"Configuración de autenticación creada exitosamente con ID: {resultado['config_id']}")
        return AuthConfigService._build_auth_config_read(resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def actualizar_config_cliente(cliente_id: UUID, config_data: AuthConfigUpdate) -> AuthConfigRead:
        """
        Actualiza la configuración de autenticación para un cliente.
        """
        logger.info(f"Actualizando configuración de autenticación para cliente ID: {cliente_id}")

        config_existente = await AuthConfigService.obtener_config_cliente(cliente_id)
        if not config_existente:
            raise NotFoundError(
                detail=f"Configuración de autenticación para cliente ID {cliente_id} no encontrada.",
                internal_code="AUTH_CONFIG_NOT_FOUND",
            )

        config_actualizada = config_existente.copy(update=config_data.dict(exclude_unset=True))
        await AuthConfigService._validar_configuracion(config_actualizada)

        update_values = {
            field: value
            for field, value in config_data.dict(exclude_unset=True).items()
            if value is not None
        }
        if not update_values:
            raise ValidationError(
                detail="No se proporcionaron campos para actualizar.",
                internal_code="NO_UPDATE_FIELDS",
            )

        resultado = await AuthConfigGateway.update_config(cliente_id, update_values)
        if not resultado:
            raise ServiceError(
                status_code=500,
                detail="No se pudo actualizar la configuración de autenticación.",
                internal_code="AUTH_CONFIG_UPDATE_FAILED",
            )

        logger.info(f"Configuración de autenticación para cliente ID {cliente_id} actualizada exitosamente.")
        return AuthConfigService._build_auth_config_read(resultado)

    @staticmethod
    @BaseService.handle_service_errors
    async def _validar_configuracion(config_data: AuthConfigRead) -> None:
        """
        Valida la coherencia de la configuración de autenticación.
        """
        if config_data.password_min_length < 6:
            raise ValidationError(
                detail="La longitud mínima de contraseña debe ser al menos 6 caracteres.",
                internal_code="PASSWORD_MIN_LENGTH_INVALID",
            )

        if config_data.password_expiry_days < 0:
            raise ValidationError(
                detail="Los días de expiración de contraseña no pueden ser negativos.",
                internal_code="PASSWORD_EXPIRY_INVALID",
            )

        if config_data.max_login_attempts < 1:
            raise ValidationError(
                detail="El número máximo de intentos de login debe ser al menos 1.",
                internal_code="MAX_LOGIN_ATTEMPTS_INVALID",
            )

        if config_data.lockout_duration_minutes < 1:
            raise ValidationError(
                detail="La duración del bloqueo debe ser al menos 1 minuto.",
                internal_code="LOCKOUT_DURATION_INVALID",
            )

        if config_data.access_token_minutes < 1:
            raise ValidationError(
                detail="La duración del access token debe ser al menos 1 minuto.",
                internal_code="ACCESS_TOKEN_DURATION_INVALID",
            )

        if config_data.refresh_token_days < 1:
            raise ValidationError(
                detail="La duración del refresh token debe ser al menos 1 día.",
                internal_code="REFRESH_TOKEN_DURATION_INVALID",
            )

        if config_data.enable_2fa and not config_data.metodos_2fa_permitidos:
            raise ValidationError(
                detail="Debe especificar al menos un método de 2FA permitido.",
                internal_code="2FA_METHODS_REQUIRED",
            )

        if config_data.horario_acceso_enabled and not config_data.horario_acceso_config:
            raise ValidationError(
                detail="Debe proporcionar la configuración de horarios de acceso.",
                internal_code="ACCESS_SCHEDULE_CONFIG_REQUIRED",
            )

    @staticmethod
    @BaseService.handle_service_errors
    async def obtener_config_global() -> AuthConfigRead:
        """
        Obtiene la configuración de autenticación por defecto del sistema.
        """
        logger.info("Obteniendo configuración de autenticación global por defecto")

        return AuthConfigService._build_auth_config_read({
            "config_id": _SYSTEM_TEMPLATE_UUID,
            "cliente_id": _SYSTEM_TEMPLATE_UUID,
            "password_min_length": 8,
            "password_require_uppercase": True,
            "password_require_lowercase": True,
            "password_require_number": True,
            "password_require_special": False,
            "password_expiry_days": 90,
            "password_history_count": 3,
            "max_login_attempts": 5,
            "lockout_duration_minutes": 30,
            "max_active_sessions": 3,
            "session_idle_timeout_minutes": 60,
            "access_token_minutes": 15,
            "refresh_token_days": 30,
            "allow_remember_me": True,
            "remember_me_days": 30,
            "require_email_verification": False,
            "allow_password_reset": True,
            "enable_2fa": False,
            "require_2fa_for_admins": False,
            "metodos_2fa_permitidos": "email,sms",
            "ip_whitelist_enabled": False,
            "ip_whitelist": None,
            "ip_blacklist": None,
            "horario_acceso_enabled": False,
            "horario_acceso_config": None,
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": None,
        })
