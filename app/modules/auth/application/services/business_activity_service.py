"""C05 — actualización throttled de last_business_activity_at (IAM Session V2)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.infrastructure.database.queries.auth.session import (
    get_active_session_by_id_core,
    touch_business_activity_core,
)
from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled

logger = logging.getLogger(__name__)

BUSINESS_ACTIVITY_THROTTLE_MINUTES = 5


class BusinessActivityService:
    """Touch fail-soft de actividad ERP — solo telemetría, sin autorización."""

    @staticmethod
    def _is_throttled(
        last_business_activity_at: Optional[datetime],
        *,
        now: Optional[datetime] = None,
    ) -> bool:
        if last_business_activity_at is None:
            return False
        now = now or datetime.utcnow()
        last = last_business_activity_at
        if last.tzinfo is not None:
            last = last.replace(tzinfo=None)
        return now - last < timedelta(minutes=BUSINESS_ACTIVITY_THROTTLE_MINUTES)

    @staticmethod
    async def touch(
        session_id: UUID,
        cliente_id: UUID,
        *,
        last_business_activity_at: Optional[datetime] = None,
    ) -> None:
        """
        Actualiza last_business_activity_at si pasó el throttle (5 min).
        Fail-soft: nunca propaga excepciones al caller.
        """
        if not is_session_v2_enabled(cliente_id):
            return

        try:
            if last_business_activity_at is not None:
                if BusinessActivityService._is_throttled(last_business_activity_at):
                    return
            else:
                session_row = await get_active_session_by_id_core(session_id, cliente_id)
                if not session_row:
                    return
                if BusinessActivityService._is_throttled(
                    session_row.get("last_business_activity_at")
                ):
                    return

            await touch_business_activity_core(session_id, cliente_id)
        except Exception as exc:
            logger.warning(
                "[BUSINESS-ACTIVITY] touch fail-soft session_id=%s cliente_id=%s: %s",
                session_id,
                cliente_id,
                exc,
            )


__all__ = ["BUSINESS_ACTIVITY_THROTTLE_MINUTES", "BusinessActivityService"]
