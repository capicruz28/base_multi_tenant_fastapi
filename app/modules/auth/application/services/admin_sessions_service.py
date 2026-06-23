"""Deprecated — usar ActiveSessionsReadService (IAM-SESSIONS-V1).

Mantiene re-export de compatibilidad para imports legacy; no contiene lógica de mapeo.
"""
from __future__ import annotations

from app.modules.auth.application.services.active_sessions_read_service import (
    ADMIN_SESSIONS_SORT_COLUMNS,
    ActiveSessionsReadService,
)


class AdminSessionsService:
    """@deprecated Usar ActiveSessionsReadService.list_admin_sessions."""

    list_admin_active_sessions = staticmethod(
        ActiveSessionsReadService.list_admin_sessions
    )


__all__ = ["ADMIN_SESSIONS_SORT_COLUMNS", "AdminSessionsService", "ActiveSessionsReadService"]
