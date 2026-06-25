"""Motivos canónicos de revocación — capa aplicación IAM Session V2."""
from enum import StrEnum


class RevokedReason(StrEnum):
    """Semántica aplicación; persistencia vía revoked_reason_mappers."""

    USER_LOGOUT = "USER_LOGOUT"
    LOGOUT_ALL = "LOGOUT_ALL"
    ADMIN_REVOKE = "ADMIN_REVOKE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_DELETED = "USER_DELETED"
    IDLE_TIMEOUT = "IDLE_TIMEOUT"
    SESSION_LIMIT = "SESSION_LIMIT"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    ABSOLUTE_TTL = "ABSOLUTE_TTL"
    # V1 legacy — sin mapeo CHECK v3; conservado hasta cleanup F15
    TOKEN_REUSE = "TOKEN_REUSE"
    SESSION_ROTATED = "SESSION_ROTATED"


V1_LEGACY_REVOKED_REASONS: frozenset[RevokedReason] = frozenset(
    {RevokedReason.TOKEN_REUSE, RevokedReason.SESSION_ROTATED}
)

__all__ = ["RevokedReason", "V1_LEGACY_REVOKED_REASONS"]
