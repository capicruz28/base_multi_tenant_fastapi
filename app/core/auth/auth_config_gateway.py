"""F10-B / ADR-012 — AuthConfigGateway: SSOT CP para cliente_auth_config."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.queries.auth.auth_config_queries_core import (
    insert_config_core,
    select_config_by_cliente_id_core,
    select_config_id_by_cliente_id_core,
    update_config_core,
)

logger = logging.getLogger(__name__)

DEFAULT_REMEMBER_ME_DAYS = 30
DEFAULT_SESSION_TIMEOUT_MINUTES = 480


class AuthConfigGateway:
    """Único punto de I/O para cliente_auth_config (Control Plane)."""

    @staticmethod
    async def get_config_by_cliente_id(cliente_id: UUID) -> Optional[Dict[str, Any]]:
        return await select_config_by_cliente_id_core(cliente_id)

    @staticmethod
    async def config_exists(
        cliente_id: UUID,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        config_id = await select_config_id_by_cliente_id_core(cliente_id, session=session)
        return config_id is not None

    @staticmethod
    async def insert_config(
        values: Dict[str, Any],
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        return await insert_config_core(values, session=session)

    @staticmethod
    async def update_config(
        cliente_id: UUID,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await update_config_core(cliente_id, values)

    @staticmethod
    async def get_token_expiration(cliente_id: UUID) -> Dict[str, int]:
        """
        access_token_minutes y refresh_token_days con fallback a settings globales.
        No crea filas por defecto.
        """
        from app.core.config import settings

        access_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        refresh_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

        try:
            row = await select_config_by_cliente_id_core(cliente_id)
            if row:
                if row.get("access_token_minutes") is not None:
                    access_minutes = int(row["access_token_minutes"])
                if row.get("refresh_token_days") is not None:
                    refresh_days = int(row["refresh_token_days"])
        except Exception as exc:
            logger.warning(
                "[AUTH_CONFIG_GATEWAY] No se pudo leer expiración tokens cliente=%s: %s. "
                "Usando settings globales.",
                cliente_id,
                exc,
            )

        return {
            "access_token_minutes": access_minutes,
            "refresh_token_days": refresh_days,
        }

    @staticmethod
    async def get_session_idle_timeout_minutes(cliente_id: UUID) -> Optional[int]:
        """NULL/<=0 o ausencia de fila → idle deshabilitado."""
        try:
            row = await select_config_by_cliente_id_core(cliente_id)
            if not row:
                return None
            value = row.get("session_idle_timeout_minutes")
            if value is None:
                return None
            minutes = int(value)
            if minutes <= 0:
                return None
            return minutes
        except Exception as exc:
            logger.warning(
                "[AUTH_CONFIG_GATEWAY] No se pudo leer session_idle_timeout_minutes "
                "cliente=%s: %s. Idle timeout deshabilitado.",
                cliente_id,
                exc,
            )
            return None

    @staticmethod
    async def get_max_active_sessions(cliente_id: UUID) -> Optional[int]:
        """NULL/<=0 o ausencia de fila → límite deshabilitado (caller aplica default)."""
        try:
            row = await select_config_by_cliente_id_core(cliente_id)
            if not row:
                return None
            value = row.get("max_active_sessions")
            if value is None:
                return None
            limit = int(value)
            if limit <= 0:
                return None
            return limit
        except Exception as exc:
            logger.warning(
                "[AUTH_CONFIG_GATEWAY] No se pudo leer max_active_sessions "
                "cliente=%s: %s. Límite deshabilitado.",
                cliente_id,
                exc,
            )
            return None

    @staticmethod
    async def get_session_ttl_config(cliente_id: UUID) -> Dict[str, Any]:
        """Políticas TTL sesión para SessionPolicyService."""
        defaults: Dict[str, Any] = {
            "allow_remember_me": True,
            "remember_me_days": DEFAULT_REMEMBER_ME_DAYS,
            "session_timeout_minutes": DEFAULT_SESSION_TIMEOUT_MINUTES,
        }
        try:
            row = await select_config_by_cliente_id_core(cliente_id)
            if not row:
                return defaults
            if row.get("allow_remember_me") is not None:
                defaults["allow_remember_me"] = bool(row["allow_remember_me"])
            if row.get("remember_me_days") is not None:
                defaults["remember_me_days"] = int(row["remember_me_days"])
            access_minutes = row.get("access_token_minutes")
            if access_minutes is not None and int(access_minutes) > 0:
                defaults["session_timeout_minutes"] = int(access_minutes) * 32
        except Exception as exc:
            logger.warning(
                "[AUTH_CONFIG_GATEWAY] No se pudo leer TTL sesión cliente=%s: %s",
                cliente_id,
                exc,
            )
        return defaults


__all__ = ["AuthConfigGateway"]
