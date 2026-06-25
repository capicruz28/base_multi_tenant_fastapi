"""F9 — tests unitarios C03 SessionRevocationService."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.modules.auth.application.services.session_revocation_service import (
    SessionRevocationService,
    _NULL_SESSION_ID,
)
from app.modules.auth.application.session.revoke_result import RevokeResult
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.token_context import TokenContext

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
ADMIN_ID = uuid4()
OTHER_USER = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
TOKEN_HASH = "e" * 64
REFRESH_TOKEN = "refresh-token-f9"

_REV = "app.modules.auth.application.services.session_revocation_service"

_SESSION_ROW = {
    "session_id": SESSION_ID,
    "cliente_id": CLIENTE_ID,
    "usuario_id": USUARIO_ID,
    "is_active": True,
    "expires_at": datetime.utcnow() + timedelta(days=7),
}
_FAMILY_ROW = {
    "family_id": FAMILY_ID,
    "session_id": SESSION_ID,
    "is_compromised": False,
}
_TOKEN_ROW = {
    "token_id": TOKEN_ID,
    "session_id": SESSION_ID,
    "family_id": FAMILY_ID,
    "usuario_id": USUARIO_ID,
    "is_used": False,
    "is_revoked": False,
}


def _context(*, active: bool = True) -> TokenContext:
    session = dict(_SESSION_ROW)
    if not active:
        session["is_active"] = False
    return TokenContext(
        cliente_id=CLIENTE_ID,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
        session_row=session,
        family_row=_FAMILY_ROW,
        token_row=_TOKEN_ROW,
    )


def _mock_uow():
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_session_success():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.SessionQueryService.get_session", new_callable=AsyncMock) as mock_sess,
        patch(f"{_REV}.SessionQueryService.get_family_for_session", new_callable=AsyncMock) as mock_fam,
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(f"{_REV}.SessionAuditEmitter.emit_session_revoked", new_callable=AsyncMock) as mock_audit,
    ):
        mock_sess.return_value = _SESSION_ROW
        mock_fam.return_value = _FAMILY_ROW
        result = await SessionRevocationService.revoke_session(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            reason=RevokedReason.USER_DEACTIVATED,
            usuario_id=USUARIO_ID,
        )

    assert isinstance(result, RevokeResult)
    assert result.session_id == SESSION_ID
    assert result.was_active is True
    assert result.already_revoked is False
    mock_tx.assert_awaited_once()
    tx_kwargs = mock_tx.await_args.kwargs
    assert tx_kwargs["session_revoked_reason"] == "admin_force"
    mock_bl.assert_awaited_once_with(SESSION_ID)
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_current_session_logout():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_REV}.SessionQueryService.hash_token", return_value=TOKEN_HASH),
        patch(
            f"{_REV}.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=_context(),
        ),
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock),
        patch(f"{_REV}.SessionAuditEmitter.emit_logout", new_callable=AsyncMock) as mock_audit,
    ):
        result = await SessionRevocationService.revoke_current_session(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            refresh_token=REFRESH_TOKEN,
            ip_address="10.0.0.1",
        )

    assert result.was_active is True
    mock_tx.assert_awaited_once()
    tx_kwargs = mock_tx.await_args.kwargs
    assert tx_kwargs["session_revoked_reason"] == "logout"
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_all_sessions():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_REV}.stx.revoke_all_user_sessions_tx",
            new_callable=AsyncMock,
            return_value={"sessions_closed": 3},
        ) as mock_tx,
        patch(
            f"{_REV}.SessionRedisBridge.blacklist_all_user_sessions",
            new_callable=AsyncMock,
        ) as mock_bl,
        patch(f"{_REV}.SessionAuditEmitter.emit_logout_all", new_callable=AsyncMock) as mock_audit,
    ):
        count = await SessionRevocationService.revoke_all_sessions(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
        )

    assert count == 3
    mock_tx.assert_awaited_once()
    mock_bl.assert_awaited_once_with(USUARIO_ID, CLIENTE_ID)
    mock_audit.assert_awaited_once()
    assert mock_audit.await_args.kwargs["sessions_revoked_count"] == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_by_admin():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.SessionQueryService.get_session", new_callable=AsyncMock, return_value=_SESSION_ROW),
        patch(f"{_REV}.SessionQueryService.get_family_for_session", new_callable=AsyncMock, return_value=_FAMILY_ROW),
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock),
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock),
        patch(f"{_REV}.SessionAuditEmitter.emit_session_admin_revoked", new_callable=AsyncMock) as mock_audit,
    ):
        result = await SessionRevocationService.revoke_by_admin(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            admin_usuario_id=ADMIN_ID,
            target_usuario_id=USUARIO_ID,
        )

    assert result.was_active is True
    mock_audit.assert_awaited_once()
    assert mock_audit.await_args.kwargs["admin_usuario_id"] == ADMIN_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_due_to_password_change():
    with patch.object(
        SessionRevocationService,
        "revoke_all_sessions",
        new_callable=AsyncMock,
        return_value=2,
    ) as mock_all:
        count = await SessionRevocationService.revoke_due_to_password_change(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
        )
    assert count == 2
    mock_all.assert_awaited_once_with(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        reason=RevokedReason.PASSWORD_CHANGE,
        ip_address=None,
        user_agent=None,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_due_to_session_limit():
    with patch.object(
        SessionRevocationService,
        "revoke_session",
        new_callable=AsyncMock,
        return_value=RevokeResult(SESSION_ID, was_active=True),
    ) as mock_revoke:
        result = await SessionRevocationService.revoke_due_to_session_limit(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
        )
    assert result.session_id == SESSION_ID
    mock_revoke.assert_awaited_once_with(
        session_id=SESSION_ID,
        cliente_id=CLIENTE_ID,
        reason=RevokedReason.SESSION_LIMIT,
        usuario_id=USUARIO_ID,
        idempotent=False,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_family_validates_family_id():
    mock_uow = _mock_uow()
    with (
        patch(
            f"{_REV}.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=_context(),
        ),
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock),
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock),
        patch(f"{_REV}.SessionAuditEmitter.emit_session_admin_revoked", new_callable=AsyncMock),
    ):
        result = await SessionRevocationService.revoke_family(
            family_id=FAMILY_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            reason=RevokedReason.ADMIN_REVOKE,
        )
    assert result.was_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_session_not_found_raises():
    with patch(
        f"{_REV}.SessionQueryService.get_session",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(NotFoundError):
            await SessionRevocationService.revoke_session(
                session_id=SESSION_ID,
                cliente_id=CLIENTE_ID,
                reason=RevokedReason.ADMIN_REVOKE,
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_session_idempotent_already_revoked():
    with (
        patch(f"{_REV}.SessionQueryService.get_session", new_callable=AsyncMock, return_value=None),
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRevocationService.revoke_session(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            reason=RevokedReason.USER_LOGOUT,
            idempotent=True,
        )
    assert result.already_revoked is True
    assert result.was_active is False
    mock_tx.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_current_idempotent_inactive_session():
    with (
        patch(f"{_REV}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_REV}.SessionQueryService.hash_token", return_value=TOKEN_HASH),
        patch(
            f"{_REV}.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=_context(active=False),
        ),
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRevocationService.revoke_current_session(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            token_hash=TOKEN_HASH,
        )
    assert result.already_revoked is True
    mock_tx.assert_not_awaited()
    mock_bl.assert_awaited_once_with(SESSION_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_current_no_token_idempotent():
    result = await SessionRevocationService.revoke_current_session(
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    assert result.already_revoked is True
    assert result.session_id == _NULL_SESSION_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_current_ownership_mismatch():
    with (
        patch(f"{_REV}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_REV}.SessionQueryService.hash_token", return_value=TOKEN_HASH),
        patch(
            f"{_REV}.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=_context(),
        ),
    ):
        with pytest.raises(AuthorizationError):
            await SessionRevocationService.revoke_current_session(
                cliente_id=CLIENTE_ID,
                usuario_id=OTHER_USER,
                refresh_token=REFRESH_TOKEN,
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_rollback_no_redis_on_tx_failure():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.SessionQueryService.get_session", new_callable=AsyncMock, return_value=_SESSION_ROW),
        patch(f"{_REV}.SessionQueryService.get_family_for_session", new_callable=AsyncMock, return_value=_FAMILY_ROW),
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_REV}.stx.revoke_session_tx",
            new_callable=AsyncMock,
            side_effect=RuntimeError("tx failed"),
        ),
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(f"{_REV}.SessionAuditEmitter.emit_logout", new_callable=AsyncMock) as mock_audit,
    ):
        with pytest.raises(RuntimeError, match="tx failed"):
            await SessionRevocationService.revoke_session(
                session_id=SESSION_ID,
                cliente_id=CLIENTE_ID,
                reason=RevokedReason.USER_LOGOUT,
            )
    mock_bl.assert_not_awaited()
    mock_audit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_session_idempotent_inactive_session():
    inactive_row = dict(_SESSION_ROW)
    inactive_row["is_active"] = False
    with (
        patch(f"{_REV}.SessionQueryService.get_session", new_callable=AsyncMock, return_value=inactive_row),
        patch(f"{_REV}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(f"{_REV}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_REV}.SessionAuditEmitter.emit_session_revoked", new_callable=AsyncMock) as mock_audit,
    ):
        result = await SessionRevocationService.revoke_session(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            reason=RevokedReason.USER_DEACTIVATED,
            idempotent=True,
        )
    assert result.already_revoked is True
    assert result.was_active is False
    mock_tx.assert_not_awaited()
    mock_audit.assert_not_awaited()
    mock_bl.assert_awaited_once_with(SESSION_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_all_sessions_user_lifecycle_reason():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_REV}.stx.revoke_all_user_sessions_tx",
            new_callable=AsyncMock,
            return_value={"sessions_closed": 2},
        ) as mock_tx,
        patch(
            f"{_REV}.SessionRedisBridge.blacklist_all_user_sessions",
            new_callable=AsyncMock,
        ) as mock_bl,
        patch(f"{_REV}.SessionAuditEmitter.emit_session_revoked", new_callable=AsyncMock) as mock_audit,
    ):
        count = await SessionRevocationService.revoke_all_sessions(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            reason=RevokedReason.USER_DEACTIVATED,
        )

    assert count == 2
    mock_tx.assert_awaited_once()
    mock_bl.assert_awaited_once_with(USUARIO_ID, CLIENTE_ID)
    mock_audit.assert_awaited_once()
    tx_kwargs = mock_tx.await_args.kwargs
    assert tx_kwargs["session_revoked_reason"] == "admin_force"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_all_sessions_invalid_reason_raises():
    with pytest.raises(ValidationError):
        await SessionRevocationService.revoke_all_sessions(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            reason=RevokedReason.SESSION_LIMIT,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f9_revoke_all_bulk_tx_failure_no_redis_no_audit():
    mock_uow = _mock_uow()
    with (
        patch(f"{_REV}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_REV}.stx.revoke_all_user_sessions_tx",
            new_callable=AsyncMock,
            side_effect=RuntimeError("bulk tx failed"),
        ),
        patch(
            f"{_REV}.SessionRedisBridge.blacklist_all_user_sessions",
            new_callable=AsyncMock,
        ) as mock_bl,
        patch(f"{_REV}.SessionAuditEmitter.emit_logout_all", new_callable=AsyncMock) as mock_audit,
    ):
        with pytest.raises(RuntimeError, match="bulk tx failed"):
            await SessionRevocationService.revoke_all_sessions(
                usuario_id=USUARIO_ID,
                cliente_id=CLIENTE_ID,
            )
    mock_bl.assert_not_awaited()
    mock_audit.assert_not_awaited()


@pytest.mark.unit
def test_f9_service_has_no_forbidden_dependencies():
    import inspect

    source = inspect.getsource(SessionRevocationService)
    forbidden = (
        "auth_service",
        "SessionCreationService",
        "SessionRotationService",
        "create_session",
        "rotate_refresh",
        "handle_replay",
        "jwt",
    )
    for token in forbidden:
        assert token not in source
