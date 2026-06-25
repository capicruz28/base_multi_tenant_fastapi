"""F8 — tests unitarios C02 SessionRotationService."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.auth.application.services.session_query_service import RotationValidationResult
from app.modules.auth.application.services.session_rotation_service import SessionRotationService
from app.modules.auth.application.session.replay_detection_result import ReplayDetectionResult
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.application.session.token_context import TokenContext

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()
OLD_REFRESH = "old-refresh-token-value"
NEW_REFRESH = "new-refresh-token-value"
OLD_HASH = "c" * 64
NEW_HASH = "d" * 64
TOKEN_EXPIRES = datetime(2026, 12, 31, 12, 0, 0)
ACCESS_JTI = "access-jti-f8"
ACCESS_EXP = 4_000_000_000

_ROT = "app.modules.auth.application.services.session_rotation_service"

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
    "current_token_id": OLD_TOKEN_ID,
}
_TOKEN_ROW = {
    "token_id": OLD_TOKEN_ID,
    "session_id": SESSION_ID,
    "family_id": FAMILY_ID,
    "usuario_id": USUARIO_ID,
    "is_used": False,
    "is_revoked": False,
    "expires_at": datetime.utcnow() + timedelta(days=7),
}


def _context(*, family_compromised: bool = False, token_used: bool = False) -> TokenContext:
    family = dict(_FAMILY_ROW)
    token = dict(_TOKEN_ROW)
    if family_compromised:
        family["is_compromised"] = True
    if token_used:
        token["is_used"] = True
    return TokenContext(
        cliente_id=CLIENTE_ID,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=OLD_TOKEN_ID,
        session_row=_SESSION_ROW,
        family_row=family,
        token_row=token,
    )


def _valid_validation() -> RotationValidationResult:
    return RotationValidationResult(
        is_valid=True,
        outcome=RotateOutcome.ROTATED,
        context=_context(),
    )


def _mock_uow():
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    return uow


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_rotate_success():
    tx_result = {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "old_token_id": OLD_TOKEN_ID,
        "new_token_id": NEW_TOKEN_ID,
    }
    mock_uow = _mock_uow()

    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock) as mock_redis,
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock) as mock_audit,
    ):
        mock_tx.return_value = tx_result
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=USUARIO_ID,
            request_ip="10.0.0.1",
            access_jti=ACCESS_JTI,
            access_exp=ACCESS_EXP,
        )

    assert isinstance(result, RotateResult)
    assert result.success is True
    assert result.outcome == RotateOutcome.ROTATED
    assert result.session_id == SESSION_ID
    assert result.family_id == FAMILY_ID
    assert result.old_token_id == OLD_TOKEN_ID
    assert result.new_token_id == NEW_TOKEN_ID
    mock_tx.assert_awaited_once()
    tx_kwargs = mock_tx.await_args.kwargs
    assert tx_kwargs["old_token_hash"] == OLD_HASH
    assert tx_kwargs["new_token_hash"] == NEW_HASH
    assert tx_kwargs["token_expires_at"] == TOKEN_EXPIRES
    mock_redis.assert_awaited_once_with(
        SESSION_ID,
        ACCESS_JTI,
        ACCESS_EXP,
        token_id=NEW_TOKEN_ID,
    )
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_replay_attack_on_already_used():
    replay = ReplayDetectionResult(
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=OLD_TOKEN_ID,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.ALREADY_USED,
            ),
        ),
        patch.object(
            SessionRotationService,
            "handle_replay",
            new_callable=AsyncMock,
            return_value=replay,
        ) as mock_replay,
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )

    assert result.outcome == RotateOutcome.COMPROMISED
    assert result.session_id == SESSION_ID
    assert result.old_token_id == OLD_TOKEN_ID
    mock_replay.assert_awaited_once()
    mock_tx.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome",),
    [
        (RotateOutcome.NOT_FOUND,),
        (RotateOutcome.EXPIRED,),
        (RotateOutcome.ALREADY_REVOKED,),
        (RotateOutcome.SESSION_EXPIRED,),
    ],
)
async def test_f8_rotate_rejects_invalid_token_states(outcome):
    ctx = _context() if outcome != RotateOutcome.NOT_FOUND else None
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=RotationValidationResult(
                is_valid=False,
                outcome=outcome,
                context=ctx,
            ),
        ),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )
    assert result.outcome == outcome
    assert result.success is False
    mock_tx.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_family_compromised():
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=RotationValidationResult(
                is_valid=False,
                outcome=RotateOutcome.COMPROMISED,
                context=_context(family_compromised=True),
            ),
        ),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
        patch.object(SessionRotationService, "handle_replay", new_callable=AsyncMock) as mock_replay,
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )
    assert result.outcome == RotateOutcome.COMPROMISED
    mock_tx.assert_not_awaited()
    mock_replay.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_user_mismatch():
    other_user = uuid4()
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=other_user,
        )
    assert result.outcome == RotateOutcome.USER_MISMATCH
    mock_tx.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_rotate_rollback_no_redis_audit_on_tx_failure():
    mock_uow = _mock_uow()
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_ROT}.stx.rotate_refresh_token_tx",
            new_callable=AsyncMock,
            side_effect=RuntimeError("UPDATE token_family.current_token_id falló"),
        ),
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock) as mock_redis,
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock) as mock_audit,
        patch.object(SessionRotationService, "handle_replay", new_callable=AsyncMock) as mock_replay,
    ):
        with pytest.raises(RuntimeError, match="current_token_id"):
            await SessionRotationService.rotate(
                refresh_token=OLD_REFRESH,
                new_refresh_token=NEW_REFRESH,
                cliente_id=CLIENTE_ID,
                new_token_expires_at=TOKEN_EXPIRES,
                access_jti=ACCESS_JTI,
            )
    mock_redis.assert_not_awaited()
    mock_audit.assert_not_awaited()
    mock_replay.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_concurrent_refresh_second_triggers_replay():
    """Dos refresh simultáneos: el segundo falla en MARK used → replay."""
    replay = ReplayDetectionResult(
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=OLD_TOKEN_ID,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    tx_result = {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "old_token_id": OLD_TOKEN_ID,
        "new_token_id": NEW_TOKEN_ID,
    }
    mock_uow = _mock_uow()
    rotate_side_effects = [
        tx_result,
        RuntimeError("MARK token used retornó 0 filas token_id=..."),
    ]

    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH] * 2),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_ROT}.stx.rotate_refresh_token_tx",
            new_callable=AsyncMock,
            side_effect=rotate_side_effects,
        ),
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock),
        patch.object(
            SessionRotationService,
            "handle_replay",
            new_callable=AsyncMock,
            return_value=replay,
        ) as mock_replay,
    ):
        first = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=USUARIO_ID,
        )
        second = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=USUARIO_ID,
        )

    assert first.outcome == RotateOutcome.ROTATED
    assert second.outcome == RotateOutcome.COMPROMISED
    mock_replay.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_handle_replay_executes_tx_redis_audit():
    context = _context(token_used=True)
    mock_uow = _mock_uow()

    with (
        patch(
            f"{_ROT}.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=context,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(f"{_ROT}.stx.handle_replay_attack_tx", new_callable=AsyncMock) as mock_replay_tx,
        patch(f"{_ROT}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(f"{_ROT}.SessionAuditEmitter.emit_replay_detected", new_callable=AsyncMock) as mock_audit,
    ):
        result = await SessionRotationService.handle_replay(
            token_hash=OLD_HASH,
            cliente_id=CLIENTE_ID,
            request_ip="10.0.0.2",
            user_agent="test-agent",
        )

    assert isinstance(result, ReplayDetectionResult)
    assert result.session_id == SESSION_ID
    assert result.family_id == FAMILY_ID
    assert result.token_id == OLD_TOKEN_ID
    assert result.usuario_id == USUARIO_ID
    mock_replay_tx.assert_awaited_once()
    replay_kwargs = mock_replay_tx.await_args.kwargs
    assert replay_kwargs["session_id"] == SESSION_ID
    assert replay_kwargs["family_id"] == FAMILY_ID
    mock_bl.assert_awaited_once_with(SESSION_ID)
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_handle_replay_raises_when_token_missing():
    with patch(
        f"{_ROT}.SessionQueryService.get_by_hash_any_state",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(ValidationError, match="no encontrado"):
            await SessionRotationService.handle_replay(
                token_hash=OLD_HASH,
                cliente_id=CLIENTE_ID,
            )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_probe_invoked_before_validate():
    call_order: list[str] = []

    async def _probe(*_a, **_k):
        call_order.append("probe")

    async def _validate(*_a, **_k):
        call_order.append("validate")
        return _valid_validation()

    async def _idle(*_a, **_k):
        call_order.append("idle")
        return False

    mock_uow = _mock_uow()
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", side_effect=_probe),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(f"{_ROT}.SessionQueryService.validate_for_rotation", side_effect=_validate),
        patch(f"{_ROT}.SessionPolicyService.check_idle", side_effect=_idle),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_ROT}.stx.rotate_refresh_token_tx",
            new_callable=AsyncMock,
            return_value={
                "session_id": SESSION_ID,
                "family_id": FAMILY_ID,
                "old_token_id": OLD_TOKEN_ID,
                "new_token_id": NEW_TOKEN_ID,
            },
        ),
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock),
    ):
        await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )
    assert call_order == ["probe", "validate", "idle"]


@pytest.mark.unit
def test_f8_service_has_no_forbidden_dependencies():
    import inspect

    source = inspect.getsource(SessionRotationService)
    forbidden = (
        "auth_service",
        "create_session",
        "jwt",
        "endpoints",
    )
    for token in forbidden:
        assert token not in source


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_idle_timeout_revokes_via_c03_and_returns_idle_outcome():
    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            f"{_ROT}.SessionRevocationService.revoke_session",
            new_callable=AsyncMock,
        ) as mock_revoke,
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=USUARIO_ID,
        )

    assert result.outcome == RotateOutcome.IDLE_TIMEOUT
    assert result.success is False
    mock_revoke.assert_awaited_once()
    revoke_kwargs = mock_revoke.await_args.kwargs
    assert revoke_kwargs["session_id"] == SESSION_ID
    assert revoke_kwargs["cliente_id"] == CLIENTE_ID
    mock_tx.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_rotate_passes_explicit_empresa_id_to_tx():
    empresa_id = uuid4()
    tx_result = {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "old_token_id": OLD_TOKEN_ID,
        "new_token_id": NEW_TOKEN_ID,
        "empresa_id": empresa_id,
    }
    mock_uow = _mock_uow()

    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock),
    ):
        mock_tx.return_value = tx_result
        await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
            usuario_id=USUARIO_ID,
            empresa_id=empresa_id,
        )

    assert mock_tx.await_args.kwargs["empresa_id"] == empresa_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_rotate_v1_compat_omits_empresa_id_when_unresolved():
    tx_result = {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "old_token_id": OLD_TOKEN_ID,
        "new_token_id": NEW_TOKEN_ID,
    }
    mock_uow = _mock_uow()
    ctx = _context()
    ctx.session_row["empresa_id"] = None
    ctx.token_row["empresa_id"] = None

    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=RotationValidationResult(
                is_valid=True,
                outcome=RotateOutcome.ROTATED,
                context=ctx,
            ),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(f"{_ROT}.stx.rotate_refresh_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock),
    ):
        mock_tx.return_value = tx_result
        await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )

    assert "empresa_id" not in mock_tx.await_args.kwargs


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f8_token_already_used_post_lock_triggers_replay():
    replay = ReplayDetectionResult(
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=OLD_TOKEN_ID,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    mock_uow = _mock_uow()

    with (
        patch(f"{_ROT}.SessionProbeService.resolve_context", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionQueryService.hash_token", side_effect=[OLD_HASH, NEW_HASH]),
        patch(
            f"{_ROT}.SessionQueryService.validate_for_rotation",
            new_callable=AsyncMock,
            return_value=_valid_validation(),
        ),
        patch(
            f"{_ROT}.SessionPolicyService.check_idle",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(f"{_ROT}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_ROT}.stx.rotate_refresh_token_tx",
            new_callable=AsyncMock,
            side_effect=RuntimeError("TOKEN_ALREADY_USED token_id=..."),
        ),
        patch.object(
            SessionRotationService,
            "handle_replay",
            new_callable=AsyncMock,
            return_value=replay,
        ) as mock_replay,
        patch(f"{_ROT}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_ROT}.SessionAuditEmitter.emit_refresh_success", new_callable=AsyncMock),
    ):
        result = await SessionRotationService.rotate(
            refresh_token=OLD_REFRESH,
            new_refresh_token=NEW_REFRESH,
            cliente_id=CLIENTE_ID,
            new_token_expires_at=TOKEN_EXPIRES,
        )

    assert result.outcome == RotateOutcome.COMPROMISED
    mock_replay.assert_awaited_once()
