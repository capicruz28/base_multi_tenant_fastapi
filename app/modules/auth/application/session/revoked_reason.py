"""Motivos canónicos de revocación de sesiones (refresh_tokens.revoked_reason)."""
from enum import StrEnum


class RevokedReason(StrEnum):
    USER_LOGOUT = "USER_LOGOUT"
    LOGOUT_ALL = "LOGOUT_ALL"
    ADMIN_REVOKE = "ADMIN_REVOKE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_DELETED = "USER_DELETED"
    TOKEN_REUSE = "TOKEN_REUSE"
    SESSION_ROTATED = "SESSION_ROTATED"
    IDLE_TIMEOUT = "IDLE_TIMEOUT"
    SESSION_LIMIT = "SESSION_LIMIT"


__all__ = ["RevokedReason"]
