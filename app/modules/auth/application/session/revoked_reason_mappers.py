"""Mapeo RevokedReason aplicación → valores CHECK DB v3 (DESIGN-01 §10.3)."""
from __future__ import annotations

from typing import Optional

from app.modules.auth.application.session.revoked_reason import (
    RevokedReason,
    V1_LEGACY_REVOKED_REASONS,
)

_SESSION_REASON: dict[RevokedReason, str] = {
    RevokedReason.USER_LOGOUT: "logout",
    RevokedReason.LOGOUT_ALL: "logout",
    RevokedReason.ADMIN_REVOKE: "admin_force",
    RevokedReason.PASSWORD_CHANGE: "password_reset",
    RevokedReason.REPLAY_DETECTED: "security",
    RevokedReason.IDLE_TIMEOUT: "expired",
    RevokedReason.SESSION_LIMIT: "admin_force",
    RevokedReason.USER_DEACTIVATED: "admin_force",
    RevokedReason.USER_DELETED: "admin_force",
    RevokedReason.ABSOLUTE_TTL: "expired",
}

_TOKEN_REASON: dict[RevokedReason, Optional[str]] = {
    RevokedReason.USER_LOGOUT: "logout",
    RevokedReason.LOGOUT_ALL: "logout",
    RevokedReason.ADMIN_REVOKE: "logout",
    RevokedReason.PASSWORD_CHANGE: "password_reset",
    RevokedReason.REPLAY_DETECTED: "replay_detected",
    RevokedReason.IDLE_TIMEOUT: None,
    RevokedReason.SESSION_LIMIT: "family_compromised",
    RevokedReason.USER_DEACTIVATED: "logout",
    RevokedReason.USER_DELETED: "logout",
    RevokedReason.ABSOLUTE_TTL: None,
}

_FAMILY_REASON: dict[RevokedReason, str] = {
    RevokedReason.USER_LOGOUT: "session_revoked",
    RevokedReason.LOGOUT_ALL: "session_revoked",
    RevokedReason.ADMIN_REVOKE: "admin_force",
    RevokedReason.PASSWORD_CHANGE: "password_reset",
    RevokedReason.REPLAY_DETECTED: "replay_detected",
    RevokedReason.IDLE_TIMEOUT: "session_revoked",
    RevokedReason.SESSION_LIMIT: "session_revoked",
    RevokedReason.USER_DEACTIVATED: "admin_force",
    RevokedReason.USER_DELETED: "admin_force",
    RevokedReason.ABSOLUTE_TTL: "session_revoked",
}


def _assert_v2_mappable(reason: RevokedReason) -> None:
    if reason in V1_LEGACY_REVOKED_REASONS:
        raise ValueError(
            f"RevokedReason {reason!s} es legacy V1 y no tiene mapeo CHECK v3"
        )


def to_session_reason(reason: RevokedReason) -> str:
    """Valor para user_session.revoked_reason."""
    _assert_v2_mappable(reason)
    return _SESSION_REASON[reason]


def to_token_reason(reason: RevokedReason) -> Optional[str]:
    """Valor para refresh_tokens.revoked_reason; None = no actualizar tokens."""
    _assert_v2_mappable(reason)
    return _TOKEN_REASON[reason]


def to_family_reason(reason: RevokedReason) -> str:
    """Valor para token_family.invalidation_reason."""
    _assert_v2_mappable(reason)
    return _FAMILY_REASON[reason]


__all__ = ["to_session_reason", "to_token_reason", "to_family_reason"]
