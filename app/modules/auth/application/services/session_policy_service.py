"""
Políticas de administración de sesiones IAM V2 (C04).

Evalúa límites, idle, TTL absoluto y remember_me. Solo devuelve decisiones;
no persiste, no audita, no interactúa con Redis ni JWT.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries.auth.session import user_session_queries_core as usq
from app.infrastructure.database.queries_async import execute_query
from app.modules.auth.application.services.auth_config_service import (
    leer_max_active_sessions,
    leer_session_idle_timeout_minutos,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_ACTIVE_SESSIONS = 3
DEFAULT_REMEMBER_ME_DAYS = 30
DEFAULT_SESSION_TIMEOUT_MINUTES = 480


@dataclass(frozen=True)
class SessionLimitDecision:
    """Plan de evicción por límite de sesiones — sin efectos secundarios."""

    max_sessions: int
    active_count: int
    sessions_to_evict: tuple[Dict[str, Any], ...]


class SessionPolicyService:
    """Reglas de política tenant — read-only + decisiones puras."""

    @staticmethod
    async def resolve_max_sessions(cliente_id: UUID) -> int:
        """
        Resuelve límite efectivo. NULL/<=0 en config → default 3 (COMPONENT-SPEC §17).
        """
        limit = await leer_max_active_sessions(cliente_id)
        if limit is None:
            return DEFAULT_MAX_ACTIVE_SESSIONS
        return limit

    @staticmethod
    async def plan_session_limit_evictions(
        usuario_id: UUID,
        cliente_id: UUID,
    ) -> SessionLimitDecision:
        """
        Determina sesiones a evictar (oldest first) si el login excedería el límite.
        No ejecuta revocación.
        """
        max_sessions = await SessionPolicyService.resolve_max_sessions(cliente_id)
        active_count = await usq.count_active_sessions_core(usuario_id, cliente_id)
        if active_count < max_sessions:
            return SessionLimitDecision(
                max_sessions=max_sessions,
                active_count=active_count,
                sessions_to_evict=(),
            )
        to_evict_count = active_count - max_sessions + 1
        oldest = await usq.list_active_sessions_oldest_first_core(
            usuario_id,
            cliente_id,
            limit=to_evict_count,
        )
        return SessionLimitDecision(
            max_sessions=max_sessions,
            active_count=active_count,
            sessions_to_evict=tuple(oldest[:to_evict_count]),
        )

    @staticmethod
    async def enforce_limit(
        usuario_id: UUID,
        cliente_id: UUID,
    ) -> int:
        """
        Retorna cantidad de sesiones que deben evictarse antes de crear una nueva.
        La ejecución de la evicción es responsabilidad del caller (C01).
        """
        decision = await SessionPolicyService.plan_session_limit_evictions(
            usuario_id,
            cliente_id,
        )
        return len(decision.sessions_to_evict)

    @staticmethod
    async def check_idle(
        session_id: UUID,
        cliente_id: UUID,
    ) -> bool:
        """True si la sesión excedió session_idle_timeout_minutes (idle auth)."""
        idle_minutes = await leer_session_idle_timeout_minutos(cliente_id)
        if idle_minutes is None:
            return False
        return await usq.is_session_idle_expired_core(
            session_id,
            cliente_id,
            idle_minutes,
        )

    @staticmethod
    async def check_idle_for_row(
        session_row: Mapping[str, Any],
        cliente_id: UUID,
    ) -> bool:
        """Evalúa idle usando session_id de la fila."""
        session_id = session_row.get("session_id")
        if not session_id:
            return False
        return await SessionPolicyService.check_idle(
            UUID(str(session_id)),
            cliente_id,
        )

    @staticmethod
    async def check_absolute_ttl(
        session_id: UUID,
        cliente_id: UUID,
    ) -> bool:
        """True si user_session.expires_at <= now."""
        return await usq.is_session_absolute_expired_core(session_id, cliente_id)

    @staticmethod
    async def evaluate_remember_me(
        cliente_id: UUID,
        remember_me: bool,
    ) -> bool:
        """remember_me efectivo tras validar allow_remember_me del tenant."""
        if not remember_me:
            return False
        config = await SessionPolicyService._read_session_ttl_config(cliente_id)
        return bool(config.get("allow_remember_me", True))

    @staticmethod
    async def compute_session_expires_at(
        cliente_id: UUID,
        remember_me: bool,
    ) -> datetime:
        """
        TTL absoluto de user_session.expires_at según remember_me y config tenant.
        remember_me=true → now + remember_me_days.
        remember_me=false → now + session_timeout_minutes (default 8h si no hay columna).
        """
        now = datetime.utcnow()
        effective_remember = await SessionPolicyService.evaluate_remember_me(
            cliente_id,
            remember_me,
        )
        config = await SessionPolicyService._read_session_ttl_config(cliente_id)
        if effective_remember:
            days = int(config.get("remember_me_days") or DEFAULT_REMEMBER_ME_DAYS)
            return now + timedelta(days=max(days, 1))
        timeout_minutes = int(
            config.get("session_timeout_minutes") or DEFAULT_SESSION_TIMEOUT_MINUTES
        )
        return now + timedelta(minutes=max(timeout_minutes, 1))

    @staticmethod
    async def _read_session_ttl_config(cliente_id: UUID) -> Dict[str, Any]:
        """Lee políticas TTL sesión desde cliente_auth_config (solo lectura)."""
        defaults: Dict[str, Any] = {
            "allow_remember_me": True,
            "remember_me_days": DEFAULT_REMEMBER_ME_DAYS,
            "session_timeout_minutes": DEFAULT_SESSION_TIMEOUT_MINUTES,
        }
        try:
            query = text(
                """
                SELECT allow_remember_me, remember_me_days, access_token_minutes
                FROM cliente_auth_config
                WHERE cliente_id = :cliente_id
                """
            )
            rows = await execute_query(
                query.bindparams(cliente_id=cliente_id),
                connection_type=DatabaseConnection.ADMIN,
                client_id=None,
            )
            if not rows:
                return defaults
            row = rows[0]
            if row.get("allow_remember_me") is not None:
                defaults["allow_remember_me"] = bool(row["allow_remember_me"])
            if row.get("remember_me_days") is not None:
                defaults["remember_me_days"] = int(row["remember_me_days"])
            access_minutes = row.get("access_token_minutes")
            if access_minutes is not None and int(access_minutes) > 0:
                defaults["session_timeout_minutes"] = int(access_minutes) * 32
        except Exception as exc:
            logger.warning(
                "[SESSION-POLICY] No se pudo leer TTL sesión cliente=%s: %s",
                cliente_id,
                exc,
            )
        return defaults


__all__ = [
    "DEFAULT_MAX_ACTIVE_SESSIONS",
    "SessionLimitDecision",
    "SessionPolicyService",
]
