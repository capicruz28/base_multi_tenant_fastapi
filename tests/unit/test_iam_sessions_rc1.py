"""ERP-IAM-SESSIONS-BE-RC1 — hotfixes HF-02/HF-03 (self-revoke, audit)."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.presentation.endpoints import (
    admin_revoke_session_by_id,
    revoke_own_session_by_id,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
USUARIO_ID = uuid4()
OTHER_USUARIO_ID = uuid4()
TOKEN_ID = uuid4()
NOW_ROW = {
    "token_id": TOKEN_ID,
    "usuario_id": USUARIO_ID,
    "cliente_id": CLIENTE_ID,
    "empresa_id": uuid4(),
    "created_at": "2026-06-18T12:00:00",
    "last_used_at": "2026-06-18T12:00:00",
    "expires_at": "2026-06-25T12:00:00",
    "device_name": "Chrome",
    "device_id": "dev-1",
    "ip_address": "10.0.0.1",
    "user_agent": "Mozilla/5.0 Chrome/120.0.0.0",
    "client_type": "web",
}


def _current_user(**overrides) -> UsuarioReadWithRoles:
    base = {
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "nombre_usuario": "testuser",
        "correo": "test@test.com",
        "nombre": "Test",
        "apellido": "User",
        "es_activo": True,
        "fecha_creacion": "2026-01-01T00:00:00",
        "roles": [],
        "permisos": [],
    }
    base.update(overrides)
    return UsuarioReadWithRoles(**base)


def _request() -> MagicMock:
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get.return_value = "TestAgent/1.0"
    return req


@pytest.mark.asyncio
async def test_self_revoke_success():
    mock_owned = AsyncMock(return_value=NOW_ROW)
    mock_active = AsyncMock(return_value=NOW_ROW)
    mock_blacklist = AsyncMock()
    mock_revoke = AsyncMock(return_value=True)
    mock_audit = AsyncMock()

    with patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_owned_session_row_for_user",
        mock_owned,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_active_session_row_for_user",
        mock_active,
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.blacklist_access_for_token_id",
        mock_blacklist,
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
        mock_revoke,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        mock_audit,
    ):
        result = await revoke_own_session_by_id(
            _request(), TOKEN_ID, _current_user()
        )

    assert "revocada exitosamente" in result["message"]
    assert result["token_id"] == str(TOKEN_ID)
    mock_blacklist.assert_awaited_once_with(TOKEN_ID)
    mock_revoke.assert_awaited_once()
    mock_audit.assert_awaited_once()
    assert mock_audit.await_args.kwargs["evento"] == "session_self_revoked"


@pytest.mark.asyncio
async def test_self_revoke_ownership_404():
    with patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_owned_session_row_for_user",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(HTTPException) as exc:
            await revoke_own_session_by_id(
                _request(), TOKEN_ID, _current_user()
            )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_self_revoke_idempotent_already_closed():
    mock_owned = AsyncMock(return_value=NOW_ROW)
    mock_active = AsyncMock(return_value=None)
    mock_blacklist = AsyncMock()
    mock_revoke = AsyncMock()
    mock_audit = AsyncMock()

    with patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_owned_session_row_for_user",
        mock_owned,
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_active_session_row_for_user",
        mock_active,
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.blacklist_access_for_token_id",
        mock_blacklist,
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
        mock_revoke,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        mock_audit,
    ):
        result = await revoke_own_session_by_id(
            _request(), TOKEN_ID, _current_user()
        )

    assert "ya estaba cerrada" in result["message"]
    mock_blacklist.assert_not_awaited()
    mock_revoke.assert_not_awaited()
    mock_audit.assert_not_awaited()


@pytest.mark.asyncio
async def test_self_revoke_audit_session_self_revoked():
    mock_audit = AsyncMock()

    with patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_owned_session_row_for_user",
        AsyncMock(return_value=NOW_ROW),
    ), patch(
        "app.modules.auth.presentation.endpoints.ActiveSessionsReadService.get_active_session_row_for_user",
        AsyncMock(return_value=NOW_ROW),
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.blacklist_access_for_token_id",
        AsyncMock(),
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
        AsyncMock(return_value=True),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        mock_audit,
    ):
        await revoke_own_session_by_id(_request(), TOKEN_ID, _current_user())

    kwargs = mock_audit.await_args.kwargs
    assert kwargs["evento"] == "session_self_revoked"
    assert kwargs["metadata"]["actor_type"] == "self"
    assert kwargs["metadata"]["token_id"] == str(TOKEN_ID)


@pytest.mark.asyncio
async def test_admin_revoke_audit_session_admin_revoked():
    mock_audit = AsyncMock()
    admin_user = _current_user(nombre_usuario="admin")

    with patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.blacklist_access_for_token_id",
        AsyncMock(),
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_refresh_token_by_id",
        AsyncMock(return_value=True),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        mock_audit,
    ):
        result = await admin_revoke_session_by_id(
            _request(), TOKEN_ID, admin_user
        )

    assert "revocada exitosamente" in result["message"]
    mock_audit.assert_awaited_once()
    assert mock_audit.await_args.kwargs["evento"] == "session_admin_revoked"
    assert mock_audit.await_args.kwargs["metadata"]["actor_type"] == "admin"
