"""
Bridge Redis para sesiones IAM V2 (C06).

Centraliza mapping access jti ↔ sesión y blacklist por session_id.
Dual-write V1 (`token_id`) + V2 (`session_id`) durante transición (plan §8.3).
Fail-soft en todas las operaciones.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.config import settings
from app.infrastructure.database.queries.auth.session import (
    list_active_sessions_oldest_first_core,
)
from app.infrastructure.redis.client import RedisService

logger = logging.getLogger(__name__)

SESSION_ACCESS_JTI_PREFIX = "session:access_jti:"
_MIN_TTL_SECONDS = 60


def _normalize_uuid(value: UUID) -> str:
    return str(value).lower()


def _session_access_key_v2(session_id: UUID) -> str:
    return f"{SESSION_ACCESS_JTI_PREFIX}{_normalize_uuid(session_id)}"


def _session_access_key_v1(token_id: UUID) -> str:
    return f"{SESSION_ACCESS_JTI_PREFIX}{_normalize_uuid(token_id)}"


def _compute_ttl_seconds(exp: Optional[int]) -> int:
    now_ts = int(datetime.utcnow().timestamp())
    if exp is not None:
        return max(int(exp) - now_ts, _MIN_TTL_SECONDS)
    return max(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, _MIN_TTL_SECONDS)


def _is_exp_still_active(exp: Optional[int]) -> bool:
    if exp is None:
        return True
    return int(exp) > int(datetime.utcnow().timestamp())


def _mapping_payload(
    *,
    jti: str,
    exp: Optional[int],
    token_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"jti": jti, "exp": exp}
    if token_id is not None:
        payload["token_id"] = _normalize_uuid(token_id)
    return payload


async def _blacklist_jti(jti: str, exp: Optional[int]) -> bool:
    if not jti or not _is_exp_still_active(exp):
        return False
    ttl = _compute_ttl_seconds(exp)
    return await RedisService.set_token_blacklist(jti, ttl)


class SessionRedisBridge:
    """Adaptador Redis sesión — sin reglas de negocio."""

    @staticmethod
    async def link_access(
        session_id: UUID,
        jti: str,
        exp: Optional[int],
        *,
        token_id: Optional[UUID] = None,
    ) -> bool:
        """
        Vincula access jti a sesión. Escribe key V2 y, si token_id, key V1 (dual-write).
        Opcionalmente blacklistea jti anterior del mapping previo.
        """
        if not session_id or not jti:
            return False
        try:
            ttl = _compute_ttl_seconds(exp)
            v2_key = _session_access_key_v2(session_id)

            previous = await RedisService.get_json(v2_key)
            if isinstance(previous, dict):
                prev_jti = previous.get("jti")
                if prev_jti and prev_jti != jti:
                    await _blacklist_jti(str(prev_jti), previous.get("exp"))

            payload = _mapping_payload(jti=jti, exp=exp, token_id=token_id)
            ok_v2 = await RedisService.set_json(v2_key, payload, ttl)

            ok_v1 = True
            if token_id is not None:
                ok_v1 = await RedisService.set_json(
                    _session_access_key_v1(token_id),
                    _mapping_payload(jti=jti, exp=exp),
                    ttl,
                )

            return bool(ok_v2 or ok_v1)
        except Exception as exc:
            logger.warning(
                "[SESSION-REDIS] link_access fail-soft session_id=%s: %s",
                session_id,
                exc,
            )
            return False

    @staticmethod
    async def get_session_access_mapping(
        session_id: UUID,
        *,
        token_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Lee mapping V2; fallback V1 si token_id provisto."""
        try:
            payload = await RedisService.get_json(_session_access_key_v2(session_id))
            if payload:
                return payload
            if token_id is not None:
                return await RedisService.get_json(_session_access_key_v1(token_id))
            return None
        except Exception as exc:
            logger.warning(
                "[SESSION-REDIS] get_session_access_mapping fail-soft session_id=%s: %s",
                session_id,
                exc,
            )
            return None

    @staticmethod
    async def blacklist_session(
        session_id: UUID,
        *,
        token_id: Optional[UUID] = None,
    ) -> bool:
        """
        Blacklistea jti del mapping (prioridad V2, fallback V1).
        Elimina claves de mapping tras blacklist.
        """
        if not session_id:
            return False
        try:
            payload = await SessionRedisBridge.get_session_access_mapping(
                session_id,
                token_id=token_id,
            )
            if not payload or not payload.get("jti"):
                return True

            blacklisted = await _blacklist_jti(
                str(payload["jti"]),
                payload.get("exp"),
            )
            await RedisService.delete_key(_session_access_key_v2(session_id))
            if token_id is not None:
                await RedisService.delete_key(_session_access_key_v1(token_id))
            elif payload.get("token_id"):
                try:
                    legacy_token_id = UUID(str(payload["token_id"]))
                    await RedisService.delete_key(_session_access_key_v1(legacy_token_id))
                except (ValueError, TypeError, AttributeError):
                    pass
            return blacklisted
        except Exception as exc:
            logger.warning(
                "[SESSION-REDIS] blacklist_session fail-soft session_id=%s: %s",
                session_id,
                exc,
            )
            return False

    @staticmethod
    async def blacklist_all_user_sessions(
        usuario_id: UUID,
        cliente_id: UUID,
    ) -> int:
        """Itera sesiones activas (C15) y blacklistea access por session_id."""
        blacklisted = 0
        try:
            sessions = await list_active_sessions_oldest_first_core(
                usuario_id,
                cliente_id,
            )
            for session in sessions:
                session_id = session.get("session_id")
                if not session_id:
                    continue
                if await SessionRedisBridge.blacklist_session(session_id):
                    blacklisted += 1
        except Exception as exc:
            logger.warning(
                "[SESSION-REDIS] blacklist_all_user_sessions fail-soft usuario=%s: %s",
                usuario_id,
                exc,
            )
        return blacklisted


__all__ = [
    "SESSION_ACCESS_JTI_PREFIX",
    "SessionRedisBridge",
]
