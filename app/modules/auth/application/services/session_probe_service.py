"""

Servicio probe read-only IAM Session V2 (C10).



Resuelve contexto /me sin side effects. Consume C08 únicamente.

"""

from __future__ import annotations



import logging

from datetime import datetime

from typing import Any, Mapping, Optional

from uuid import UUID



from app.infrastructure.database.queries.auth.session.refresh_token_queries_core import (

    _get_token_by_id_core,

)

from app.modules.auth.application.services.session_query_service import SessionQueryService

from app.modules.auth.application.session.session_probe_result import SessionProbeResult



logger = logging.getLogger(__name__)





def _coerce_uuid(value: Any) -> Optional[UUID]:

    if value is None:

        return None

    if isinstance(value, UUID):

        return value

    try:

        return UUID(str(value))

    except (ValueError, TypeError, AttributeError):

        return None





def _is_expired(expires_at: Any) -> bool:

    if expires_at is None:

        return False

    if isinstance(expires_at, datetime):

        return expires_at <= datetime.utcnow()

    return False





def _token_row_usable(token_row: Optional[Mapping[str, Any]]) -> bool:

    if not token_row:

        return False

    if token_row.get("is_used") or token_row.get("is_revoked"):

        return False

    return not _is_expired(token_row.get("expires_at"))





class SessionProbeService:

    """Probe fail-soft para GET /me — sin mutaciones."""



    @staticmethod

    async def resolve_context(

        cliente_id: UUID,

        *,

        refresh_token: Optional[str] = None,

        access_session_id: Optional[UUID] = None,

    ) -> SessionProbeResult:

        """

        Preferir refresh token sobre claim sid si ambos están presentes.

        Fail-soft: retorna SessionProbeResult vacío ante errores.

        """

        try:

            if refresh_token:

                return await SessionProbeService._resolve_from_refresh(

                    refresh_token,

                    cliente_id,

                )

            if access_session_id:

                return await SessionProbeService._resolve_from_session_id(

                    access_session_id,

                    cliente_id,

                )

            return SessionProbeResult()

        except Exception as exc:

            logger.warning(

                "[SESSION-PROBE] resolve_context fail-soft cliente_id=%s: %s",

                cliente_id,

                exc,

            )

            return SessionProbeResult()



    @staticmethod

    async def _resolve_from_refresh(

        refresh_token: str,

        cliente_id: UUID,

    ) -> SessionProbeResult:

        token_hash = SessionQueryService.hash_token(refresh_token)

        context = await SessionQueryService.get_by_hash_any_state(

            token_hash,

            cliente_id,

        )

        if context is None:

            return SessionProbeResult()



        session_active = bool(context.session_row.get("is_active"))

        if session_active and _is_expired(context.session_row.get("expires_at")):

            session_active = False

        token_usable = _token_row_usable(context.token_row)

        family_ok = not context.family_row.get("is_compromised")

        is_active = session_active and token_usable and family_ok



        return SessionProbeResult(

            current_session_id=context.session_id,

            current_token_id=context.token_id,

            is_active=is_active,

        )



    @staticmethod

    async def _resolve_from_session_id(

        session_id: UUID,

        cliente_id: UUID,

    ) -> SessionProbeResult:

        session_row = await SessionQueryService.get_session(session_id, cliente_id)

        if not session_row:

            return SessionProbeResult()



        family_row = await SessionQueryService.get_family_for_session(

            session_id,

            cliente_id,

        )

        if not family_row or family_row.get("is_compromised"):

            return SessionProbeResult(

                current_session_id=session_id,

                is_active=False,

            )



        current_token_id = _coerce_uuid(family_row.get("current_token_id"))

        if current_token_id is None:

            return SessionProbeResult(

                current_session_id=session_id,

                is_active=False,

            )



        token_row = await _get_token_by_id_core(current_token_id, cliente_id)

        is_active = _token_row_usable(token_row)



        return SessionProbeResult(

            current_session_id=session_id,

            current_token_id=current_token_id,

            is_active=is_active,

        )





__all__ = ["SessionProbeService"]


