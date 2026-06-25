"""
Servicio de consulta read-only IAM Session V2 (C08).

Compone C15 + C16 + C17 sin mutaciones ni side effects.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, Optional
from uuid import UUID

from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import (
    get_active_session_by_id_core,
    get_family_by_id_core,
    get_family_by_session_id_core,
    get_refresh_token_by_hash_any_state_core,
    get_refresh_token_by_hash_core,
)
from app.modules.auth.application.session.rotate_result import RotateOutcome
from app.modules.auth.application.session.token_context import TokenContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RotationValidationResult:
    """Resultado read-only de validate_for_rotation (sin mutación)."""

    is_valid: bool
    outcome: RotateOutcome
    context: Optional[TokenContext] = None


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _is_expired(expires_at: Any) -> bool:
    if expires_at is None:
        return False
    if isinstance(expires_at, datetime):
        return expires_at <= datetime.utcnow()
    return False


class SessionQueryService:
    """Queries de sesión/token — read-only."""

    @staticmethod
    def hash_token(plaintext: str) -> str:
        """SHA-256 hex del refresh token en claro."""
        if not plaintext or not plaintext.strip():
            raise ValidationError(
                detail="El token no puede estar vacío",
                internal_code="EMPTY_TOKEN",
            )
        return hashlib.sha256(plaintext.encode()).hexdigest()

    @staticmethod
    async def get_by_hash(
        token_hash: str,
        cliente_id: UUID,
    ) -> Optional[TokenContext]:
        """Token elegible: no usado, no revocado, no expirado."""
        if not token_hash or not token_hash.strip():
            raise ValidationError(
                detail="token_hash no puede estar vacío",
                internal_code="EMPTY_TOKEN_HASH",
            )
        token_row = await get_refresh_token_by_hash_core(token_hash, cliente_id)
        if not token_row:
            return None
        return await SessionQueryService._compose_context(
            token_row,
            cliente_id,
            require_active_session=True,
        )

    @staticmethod
    async def get_by_hash_any_state(
        token_hash: str,
        cliente_id: UUID,
    ) -> Optional[TokenContext]:
        """Token en cualquier estado (probe / diagnóstico)."""
        if not token_hash or not token_hash.strip():
            raise ValidationError(
                detail="token_hash no puede estar vacío",
                internal_code="EMPTY_TOKEN_HASH",
            )
        token_row = await get_refresh_token_by_hash_any_state_core(
            token_hash,
            cliente_id,
        )
        if not token_row:
            return None
        return await SessionQueryService._compose_context(
            token_row,
            cliente_id,
            require_active_session=False,
        )

    @staticmethod
    async def get_session(
        session_id: UUID,
        cliente_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Sesión activa no expirada por session_id + tenant."""
        return await get_active_session_by_id_core(session_id, cliente_id)

    @staticmethod
    async def get_family_for_session(
        session_id: UUID,
        cliente_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Familia activa (no comprometida) de la sesión."""
        return await get_family_by_session_id_core(session_id, cliente_id)

    @staticmethod
    async def get_token_context(
        token_hash: str,
        cliente_id: UUID,
        *,
        any_state: bool = False,
    ) -> Optional[TokenContext]:
        """Alias compuesto session + family + token."""
        if any_state:
            return await SessionQueryService.get_by_hash_any_state(token_hash, cliente_id)
        return await SessionQueryService.get_by_hash(token_hash, cliente_id)

    @staticmethod
    async def validate_for_rotation(
        token_hash: str,
        cliente_id: UUID,
    ) -> RotationValidationResult:
        """
        Checks sin mutación: token usable + familia no comprometida + sesión activa.
        """
        if not token_hash or not token_hash.strip():
            raise ValidationError(
                detail="token_hash no puede estar vacío",
                internal_code="EMPTY_TOKEN_HASH",
            )

        token_row = await get_refresh_token_by_hash_core(token_hash, cliente_id)
        if token_row:
            context = await SessionQueryService._compose_context(
                token_row,
                cliente_id,
                require_active_session=True,
            )
            if context is None:
                return RotationValidationResult(
                    is_valid=False,
                    outcome=RotateOutcome.SESSION_EXPIRED,
                )
            if context.family_row.get("is_compromised"):
                return RotationValidationResult(
                    is_valid=False,
                    outcome=RotateOutcome.COMPROMISED,
                    context=context,
                )
            return RotationValidationResult(
                is_valid=True,
                outcome=RotateOutcome.ROTATED,
                context=context,
            )

        any_row = await get_refresh_token_by_hash_any_state_core(token_hash, cliente_id)
        if not any_row:
            return RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.NOT_FOUND,
            )
        if any_row.get("is_used"):
            return RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.ALREADY_USED,
            )
        if any_row.get("is_revoked"):
            return RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.ALREADY_REVOKED,
            )
        if _is_expired(any_row.get("expires_at")):
            return RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.EXPIRED,
            )

        family_row = await get_family_by_id_core(
            _coerce_uuid(any_row["family_id"]),
            cliente_id,
        )
        if family_row and family_row.get("is_compromised"):
            return RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.COMPROMISED,
            )

        return RotationValidationResult(
            is_valid=False,
            outcome=RotateOutcome.SESSION_EXPIRED,
        )

    @staticmethod
    async def _compose_context(
        token_row: Mapping[str, Any],
        cliente_id: UUID,
        *,
        require_active_session: bool,
    ) -> Optional[TokenContext]:
        session_id = _coerce_uuid(token_row["session_id"])
        family_id = _coerce_uuid(token_row["family_id"])
        token_id = _coerce_uuid(token_row["token_id"])

        family_row = await get_family_by_id_core(family_id, cliente_id)
        if not family_row:
            return None

        session_row = await get_active_session_by_id_core(session_id, cliente_id)
        if session_row is None:
            if require_active_session:
                return None
            session_row = {
                "session_id": session_id,
                "cliente_id": cliente_id,
                "usuario_id": token_row.get("usuario_id"),
                "is_active": False,
            }

        return TokenContext(
            cliente_id=cliente_id,
            session_id=session_id,
            family_id=family_id,
            token_id=token_id,
            session_row=session_row,
            family_row=family_row,
            token_row=dict(token_row),
        )


__all__ = [
    "RotationValidationResult",
    "SessionQueryService",
]
