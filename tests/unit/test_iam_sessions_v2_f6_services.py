"""F6 — tests unitarios C08 SessionQueryService + C10 SessionProbeService."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.auth.application.services.session_probe_service import SessionProbeService
from app.modules.auth.application.services.session_query_service import SessionQueryService
from app.modules.auth.application.session.rotate_result import RotateOutcome

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
TOKEN_HASH = "a" * 64
PLAINTEXT = "refresh-secret-token"

TOKEN_ROW_ACTIVE = {
    "token_id": TOKEN_ID,
    "session_id": SESSION_ID,
    "family_id": FAMILY_ID,
    "usuario_id": USUARIO_ID,
    "cliente_id": CLIENTE_ID,
    "token_hash": TOKEN_HASH,
    "is_used": False,
    "is_revoked": False,
    "expires_at": datetime.utcnow() + timedelta(days=7),
}
SESSION_ROW_ACTIVE = {
    "session_id": SESSION_ID,
    "cliente_id": CLIENTE_ID,
    "usuario_id": USUARIO_ID,
    "is_active": True,
    "expires_at": datetime.utcnow() + timedelta(days=7),
}
FAMILY_ROW_ACTIVE = {
    "family_id": FAMILY_ID,
    "session_id": SESSION_ID,
    "is_compromised": False,
    "current_token_id": TOKEN_ID,
}

_Q = "app.modules.auth.application.services.session_query_service"


@pytest.mark.unit
def test_f6_hash_token_deterministic():
    h1 = SessionQueryService.hash_token(PLAINTEXT)
    h2 = SessionQueryService.hash_token(PLAINTEXT)
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.unit
def test_f6_hash_token_rejects_empty():
    with pytest.raises(ValidationError):
        SessionQueryService.hash_token("")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_get_by_hash_builds_token_context():
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock) as mock_token,
        patch(f"{_Q}.get_family_by_id_core", new_callable=AsyncMock) as mock_family,
        patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock) as mock_session,
    ):
        mock_token.return_value = TOKEN_ROW_ACTIVE
        mock_family.return_value = FAMILY_ROW_ACTIVE
        mock_session.return_value = SESSION_ROW_ACTIVE
        ctx = await SessionQueryService.get_by_hash(TOKEN_HASH, CLIENTE_ID)
    assert ctx is not None
    assert ctx.session_id == SESSION_ID
    assert ctx.family_id == FAMILY_ID
    assert ctx.token_id == TOKEN_ID
    mock_token.assert_awaited_once_with(TOKEN_HASH, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_get_by_hash_returns_none_when_token_missing():
    with patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=None):
        ctx = await SessionQueryService.get_by_hash(TOKEN_HASH, CLIENTE_ID)
    assert ctx is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_get_by_hash_any_state_includes_revoked_token():
    revoked_row = {**TOKEN_ROW_ACTIVE, "is_revoked": True}
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_any_state_core", new_callable=AsyncMock) as mock_token,
        patch(f"{_Q}.get_family_by_id_core", new_callable=AsyncMock, return_value=FAMILY_ROW_ACTIVE),
        patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock, return_value=None),
    ):
        mock_token.return_value = revoked_row
        ctx = await SessionQueryService.get_by_hash_any_state(TOKEN_HASH, CLIENTE_ID)
    assert ctx is not None
    assert ctx.token_row["is_revoked"] is True
    assert ctx.session_row["is_active"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_success():
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=TOKEN_ROW_ACTIVE),
        patch(f"{_Q}.get_family_by_id_core", new_callable=AsyncMock, return_value=FAMILY_ROW_ACTIVE),
        patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock, return_value=SESSION_ROW_ACTIVE),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.is_valid is True
    assert result.outcome == RotateOutcome.ROTATED
    assert result.context is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_detects_compromised_family():
    compromised_family = {**FAMILY_ROW_ACTIVE, "is_compromised": True}
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=TOKEN_ROW_ACTIVE),
        patch(f"{_Q}.get_family_by_id_core", new_callable=AsyncMock, return_value=compromised_family),
        patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock, return_value=SESSION_ROW_ACTIVE),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.is_valid is False
    assert result.outcome == RotateOutcome.COMPROMISED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_detects_used_token():
    used_row = {**TOKEN_ROW_ACTIVE, "is_used": True}
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=None),
        patch(f"{_Q}.get_refresh_token_by_hash_any_state_core", new_callable=AsyncMock, return_value=used_row),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.is_valid is False
    assert result.outcome == RotateOutcome.ALREADY_USED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_detects_revoked_token():
    revoked_row = {**TOKEN_ROW_ACTIVE, "is_revoked": True}
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=None),
        patch(f"{_Q}.get_refresh_token_by_hash_any_state_core", new_callable=AsyncMock, return_value=revoked_row),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.outcome == RotateOutcome.ALREADY_REVOKED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_detects_expired_token():
    expired_row = {
        **TOKEN_ROW_ACTIVE,
        "expires_at": datetime.utcnow() - timedelta(hours=1),
    }
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=None),
        patch(f"{_Q}.get_refresh_token_by_hash_any_state_core", new_callable=AsyncMock, return_value=expired_row),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.outcome == RotateOutcome.EXPIRED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_validate_for_rotation_closed_session():
    with (
        patch(f"{_Q}.get_refresh_token_by_hash_core", new_callable=AsyncMock, return_value=TOKEN_ROW_ACTIVE),
        patch(f"{_Q}.get_family_by_id_core", new_callable=AsyncMock, return_value=FAMILY_ROW_ACTIVE),
        patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock, return_value=None),
    ):
        result = await SessionQueryService.validate_for_rotation(TOKEN_HASH, CLIENTE_ID)
    assert result.is_valid is False
    assert result.outcome == RotateOutcome.SESSION_EXPIRED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_get_session_delegates_to_c15():
    with patch(f"{_Q}.get_active_session_by_id_core", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = SESSION_ROW_ACTIVE
        row = await SessionQueryService.get_session(SESSION_ID, CLIENTE_ID)
    assert row == SESSION_ROW_ACTIVE
    mock_get.assert_awaited_once_with(SESSION_ID, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_probe_from_refresh_valid_session():
    with (
        patch.object(SessionQueryService, "hash_token", return_value=TOKEN_HASH),
        patch.object(SessionQueryService, "get_by_hash_any_state", new_callable=AsyncMock) as mock_ctx,
    ):
        from app.modules.auth.application.session.token_context import TokenContext

        mock_ctx.return_value = TokenContext(
            cliente_id=CLIENTE_ID,
            session_id=SESSION_ID,
            family_id=FAMILY_ID,
            token_id=TOKEN_ID,
            session_row=SESSION_ROW_ACTIVE,
            family_row=FAMILY_ROW_ACTIVE,
            token_row=TOKEN_ROW_ACTIVE,
        )
        result = await SessionProbeService.resolve_context(
            CLIENTE_ID,
            refresh_token=PLAINTEXT,
        )
    assert result.current_session_id == SESSION_ID
    assert result.current_token_id == TOKEN_ID
    assert result.is_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_probe_from_refresh_revoked_exposes_token_id():
    with (
        patch.object(SessionQueryService, "hash_token", return_value=TOKEN_HASH),
        patch.object(SessionQueryService, "get_by_hash_any_state", new_callable=AsyncMock) as mock_ctx,
    ):
        from app.modules.auth.application.session.token_context import TokenContext

        mock_ctx.return_value = TokenContext(
            cliente_id=CLIENTE_ID,
            session_id=SESSION_ID,
            family_id=FAMILY_ID,
            token_id=TOKEN_ID,
            session_row={"session_id": SESSION_ID, "is_active": False},
            family_row=FAMILY_ROW_ACTIVE,
            token_row={**TOKEN_ROW_ACTIVE, "is_revoked": True},
        )
        result = await SessionProbeService.resolve_context(
            CLIENTE_ID,
            refresh_token=PLAINTEXT,
        )
    assert result.current_token_id == TOKEN_ID
    assert result.is_active is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_probe_prefers_refresh_over_sid():
    with (
        patch.object(SessionProbeService, "_resolve_from_refresh", new_callable=AsyncMock) as mock_refresh,
        patch.object(SessionProbeService, "_resolve_from_session_id", new_callable=AsyncMock) as mock_sid,
    ):
        mock_refresh.return_value = mock_sid.return_value = None
        await SessionProbeService.resolve_context(
            CLIENTE_ID,
            refresh_token=PLAINTEXT,
            access_session_id=SESSION_ID,
        )
    mock_refresh.assert_awaited_once()
    mock_sid.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_probe_from_sid_without_refresh():
    with (
        patch.object(SessionQueryService, "get_session", new_callable=AsyncMock, return_value=SESSION_ROW_ACTIVE),
        patch.object(SessionQueryService, "get_family_for_session", new_callable=AsyncMock, return_value=FAMILY_ROW_ACTIVE),
        patch(
            "app.modules.auth.application.services.session_probe_service._get_token_by_id_core",
            new_callable=AsyncMock,
            return_value=TOKEN_ROW_ACTIVE,
        ),
    ):
        result = await SessionProbeService.resolve_context(
            CLIENTE_ID,
            access_session_id=SESSION_ID,
        )
    assert result.current_session_id == SESSION_ID
    assert result.current_token_id == TOKEN_ID
    assert result.is_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_probe_fail_soft_returns_empty():
    with patch.object(
        SessionQueryService,
        "hash_token",
        side_effect=RuntimeError("unexpected"),
    ):
        result = await SessionProbeService.resolve_context(
            CLIENTE_ID,
            refresh_token=PLAINTEXT,
        )
    assert result.current_session_id is None
    assert result.current_token_id is None
    assert result.is_active is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_query_service_has_no_side_effect_writes():
    import app.modules.auth.application.services.session_query_service as mod

    source = open(mod.__file__, encoding="utf-8").read()
    assert "UnitOfWork" not in source
    assert "SessionRedisBridge" not in source
    assert "SessionAuditEmitter" not in source
    assert "execute_insert" not in source
    assert "execute_update" not in source


@pytest.mark.unit
def test_f6_services_package_exports():
    from app.modules.auth.application.services import __all__ as exports

    assert "SessionQueryService" in exports
    assert "SessionProbeService" in exports
