"""Feature flag IAM Session Management V2 — gobernanza F0."""
from __future__ import annotations

import logging
from typing import FrozenSet, Optional
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)


def _parse_tenant_allowlist(raw: str) -> FrozenSet[UUID]:
    if not raw or not raw.strip():
        return frozenset()
    ids: set[UUID] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            ids.add(UUID(token))
        except ValueError:
            logger.warning(
                "[IAM-SESSION-V2] UUID inválido en IAM_SESSION_V2_TENANT_ALLOWLIST ignorado: %s",
                token,
            )
    return frozenset(ids)


def is_session_v2_enabled(cliente_id: Optional[UUID]) -> bool:
    """
    Indica si el flujo Session Management V2 está activo para un tenant.

    True cuando el flag global está activo Y (allowlist vacía O cliente_id en allowlist).
    False si el flag global está desactivado o cliente_id es None.
    """
    if not settings.IAM_SESSION_MANAGEMENT_V2_ENABLED:
        return False
    if cliente_id is None:
        return False

    allowlist = _parse_tenant_allowlist(settings.IAM_SESSION_V2_TENANT_ALLOWLIST)
    if not allowlist:
        return True
    return cliente_id in allowlist


__all__ = ["is_session_v2_enabled"]
