"""F7 — tests unitarios C04 SessionPolicyService + C01 SessionCreationService."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.auth.application.services.session_creation_service import (
    DeviceContext,
    SessionCreationService,
)
from app.modules.auth.application.services.session_policy_service import (
    DEFAULT_MAX_ACTIVE_SESSIONS,
    SessionLimitDecision,
    SessionPolicyService,
)
from app.modules.auth.application.session.session_creation_result import SessionCreationResult

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
EVICT_SESSION_ID = uuid4()
EVICT_FAMILY_ID = uuid4()
TOKEN_HASH = "b" * 64
ACCESS_JTI = "access-jti-f7"
ACCESS_EXP = 4_000_000_000
SESSION_EXPIRES = datetime(2026, 12, 31, 12, 0, 0)
TOKEN_EXPIRES = datetime(2026, 6, 30, 12, 0, 0)

_DEVICE = DeviceContext(
    platform="web",
    device_name="Chrome",
    device_id="device-1",
    device_fingerprint='{"os":"win"}',
    user_agent="Mozilla/5.0",
    login_ip="192.168.1.10",
)

_POLICY = "app.modules.auth.application.services.session_policy_service"
_CREATE = "app.modules.auth.application.services.session_creation_service"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_no_eviction_when_under_limit():
    with (
        patch(f"{_POLICY}.leer_max_active_sessions", new_callable=AsyncMock, return_value=3),
        patch(f"{_POLICY}.usq.count_active_sessions_core", new_callable=AsyncMock, return_value=2),
        patch(f"{_POLICY}.usq.list_active_sessions_oldest_first_core", new_callable=AsyncMock),
    ):
        decision = await SessionPolicyService.plan_session_limit_evictions(
            USUARIO_ID,
            CLIENTE_ID,
        )
    assert decision.active_count == 2
    assert decision.sessions_to_evict == ()
    assert await SessionPolicyService.enforce_limit(USUARIO_ID, CLIENTE_ID) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_evicts_oldest_when_at_limit():
    oldest = {"session_id": EVICT_SESSION_ID, "created_at": datetime(2026, 1, 1)}
    with (
        patch(f"{_POLICY}.leer_max_active_sessions", new_callable=AsyncMock, return_value=2),
        patch(f"{_POLICY}.usq.count_active_sessions_core", new_callable=AsyncMock, return_value=2),
        patch(
            f"{_POLICY}.usq.list_active_sessions_oldest_first_core",
            new_callable=AsyncMock,
            return_value=[oldest],
        ) as mock_list,
    ):
        decision = await SessionPolicyService.plan_session_limit_evictions(
            USUARIO_ID,
            CLIENTE_ID,
        )
        count = await SessionPolicyService.enforce_limit(USUARIO_ID, CLIENTE_ID)
    assert count == 1
    assert len(decision.sessions_to_evict) == 1
    assert decision.sessions_to_evict[0]["session_id"] == EVICT_SESSION_ID
    mock_list.assert_awaited_with(USUARIO_ID, CLIENTE_ID, limit=1)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_default_max_when_config_null():
    with patch(
        f"{_POLICY}.leer_max_active_sessions",
        new_callable=AsyncMock,
        return_value=None,
    ):
        limit = await SessionPolicyService.resolve_max_sessions(CLIENTE_ID)
    assert limit == DEFAULT_MAX_ACTIVE_SESSIONS


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_check_idle_respects_disabled():
    with patch(
        f"{_POLICY}.leer_session_idle_timeout_minutos",
        new_callable=AsyncMock,
        return_value=None,
    ):
        expired = await SessionPolicyService.check_idle(SESSION_ID, CLIENTE_ID)
    assert expired is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_check_idle_delegates_to_query():
    with (
        patch(
            f"{_POLICY}.leer_session_idle_timeout_minutos",
            new_callable=AsyncMock,
            return_value=60,
        ),
        patch(
            f"{_POLICY}.usq.is_session_idle_expired_core",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_idle,
    ):
        expired = await SessionPolicyService.check_idle(SESSION_ID, CLIENTE_ID)
    assert expired is True
    mock_idle.assert_awaited_once_with(SESSION_ID, CLIENTE_ID, 60)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_check_absolute_ttl():
    with patch(
        f"{_POLICY}.usq.is_session_absolute_expired_core",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_abs:
        expired = await SessionPolicyService.check_absolute_ttl(SESSION_ID, CLIENTE_ID)
    assert expired is True
    mock_abs.assert_awaited_once_with(SESSION_ID, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_remember_me_disabled_when_not_allowed():
    with patch.object(
        SessionPolicyService,
        "_read_session_ttl_config",
        new_callable=AsyncMock,
        return_value={"allow_remember_me": False, "remember_me_days": 30},
    ):
        effective = await SessionPolicyService.evaluate_remember_me(CLIENTE_ID, True)
    assert effective is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_session_expires_remember_me_vs_short():
    fixed_now = datetime(2026, 6, 1, 10, 0, 0)
    with (
        patch(f"{_POLICY}.datetime") as mock_dt,
        patch.object(
            SessionPolicyService,
            "_read_session_ttl_config",
            new_callable=AsyncMock,
            return_value={
                "allow_remember_me": True,
                "remember_me_days": 30,
                "session_timeout_minutes": 480,
            },
        ),
    ):
        mock_dt.utcnow.return_value = fixed_now
        remember_exp = await SessionPolicyService.compute_session_expires_at(
            CLIENTE_ID,
            remember_me=True,
        )
        short_exp = await SessionPolicyService.compute_session_expires_at(
            CLIENTE_ID,
            remember_me=False,
        )
    assert remember_exp == fixed_now + timedelta(days=30)
    assert short_exp == fixed_now + timedelta(minutes=480)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_create_normal_session_atomic():
    tx_result = {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "token_id": TOKEN_ID,
        "expires_at": SESSION_EXPIRES,
    }
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(
            SessionPolicyService,
            "plan_session_limit_evictions",
            new_callable=AsyncMock,
            return_value=SessionLimitDecision(3, 1, ()),
        ),
        patch.object(
            SessionPolicyService,
            "compute_session_expires_at",
            new_callable=AsyncMock,
            return_value=SESSION_EXPIRES,
        ),
        patch(f"{_CREATE}.UnitOfWork", return_value=mock_uow),
        patch(f"{_CREATE}.stx.create_session_with_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_CREATE}.SessionRedisBridge.link_access", new_callable=AsyncMock) as mock_redis,
        patch(f"{_CREATE}.SessionAuditEmitter.emit_login_success", new_callable=AsyncMock) as mock_audit,
    ):
        mock_tx.return_value = tx_result
        result = await SessionCreationService.create(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            device_context=_DEVICE,
            remember_me=False,
            token_expires_at=TOKEN_EXPIRES,
            access_jti=ACCESS_JTI,
            access_exp=ACCESS_EXP,
        )

    assert isinstance(result, SessionCreationResult)
    assert result.session_id == SESSION_ID
    assert result.family_id == FAMILY_ID
    assert result.token_id == TOKEN_ID
    assert result.expires_at == SESSION_EXPIRES
    mock_tx.assert_awaited_once()
    call_kwargs = mock_tx.await_args.kwargs
    assert call_kwargs["token_hash"] == TOKEN_HASH
    assert call_kwargs["session_expires_at"] == SESSION_EXPIRES
    assert call_kwargs["device_fingerprint"] is not None
    assert len(call_kwargs["device_fingerprint"]) == 64
    mock_redis.assert_awaited_once_with(
        SESSION_ID,
        ACCESS_JTI,
        ACCESS_EXP,
        token_id=TOKEN_ID,
    )
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_create_with_remember_me_passes_policy():
    with (
        patch.object(
            SessionPolicyService,
            "plan_session_limit_evictions",
            new_callable=AsyncMock,
            return_value=SessionLimitDecision(3, 0, ()),
        ),
        patch.object(
            SessionPolicyService,
            "compute_session_expires_at",
            new_callable=AsyncMock,
            return_value=SESSION_EXPIRES,
        ) as mock_exp,
        patch(f"{_CREATE}.UnitOfWork") as mock_uow_cls,
        patch(f"{_CREATE}.stx.create_session_with_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_CREATE}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_CREATE}.SessionAuditEmitter.emit_login_success", new_callable=AsyncMock),
    ):
        mock_uow = MagicMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=False)
        mock_uow_cls.return_value = mock_uow
        mock_tx.return_value = {
            "session_id": SESSION_ID,
            "family_id": FAMILY_ID,
            "token_id": TOKEN_ID,
            "expires_at": SESSION_EXPIRES,
        }
        await SessionCreationService.create(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            device_context=_DEVICE,
            remember_me=True,
            token_expires_at=TOKEN_EXPIRES,
        )
    mock_exp.assert_awaited_once_with(CLIENTE_ID, True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_create_evicts_oldest_before_create():
    oldest = {"session_id": EVICT_SESSION_ID}
    with (
        patch.object(
            SessionPolicyService,
            "plan_session_limit_evictions",
            new_callable=AsyncMock,
            return_value=SessionLimitDecision(2, 2, (oldest,)),
        ),
        patch(
            f"{_CREATE}.SessionQueryService.get_family_for_session",
            new_callable=AsyncMock,
            return_value={"family_id": EVICT_FAMILY_ID},
        ),
        patch.object(
            SessionCreationService,
            "_evict_session_for_limit",
            new_callable=AsyncMock,
        ) as mock_evict,
        patch.object(
            SessionPolicyService,
            "compute_session_expires_at",
            new_callable=AsyncMock,
            return_value=SESSION_EXPIRES,
        ),
        patch(f"{_CREATE}.UnitOfWork") as mock_uow_cls,
        patch(f"{_CREATE}.stx.create_session_with_token_tx", new_callable=AsyncMock) as mock_tx,
        patch(f"{_CREATE}.SessionRedisBridge.link_access", new_callable=AsyncMock),
        patch(f"{_CREATE}.SessionAuditEmitter.emit_login_success", new_callable=AsyncMock),
    ):
        mock_uow = MagicMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=False)
        mock_uow_cls.return_value = mock_uow
        mock_tx.return_value = {
            "session_id": SESSION_ID,
            "family_id": FAMILY_ID,
            "token_id": TOKEN_ID,
            "expires_at": SESSION_EXPIRES,
        }
        await SessionCreationService.create(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            device_context=_DEVICE,
            token_expires_at=TOKEN_EXPIRES,
        )
    mock_evict.assert_awaited_once_with(
        session_id=EVICT_SESSION_ID,
        family_id=EVICT_FAMILY_ID,
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
    )
    mock_tx.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_create_rollback_no_redis_audit_on_tx_failure():
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(
            SessionPolicyService,
            "plan_session_limit_evictions",
            new_callable=AsyncMock,
            return_value=SessionLimitDecision(3, 0, ()),
        ),
        patch.object(
            SessionPolicyService,
            "compute_session_expires_at",
            new_callable=AsyncMock,
            return_value=SESSION_EXPIRES,
        ),
        patch(f"{_CREATE}.UnitOfWork", return_value=mock_uow),
        patch(
            f"{_CREATE}.stx.create_session_with_token_tx",
            new_callable=AsyncMock,
            side_effect=RuntimeError("tx failed"),
        ),
        patch(f"{_CREATE}.SessionRedisBridge.link_access", new_callable=AsyncMock) as mock_redis,
        patch(f"{_CREATE}.SessionAuditEmitter.emit_login_success", new_callable=AsyncMock) as mock_audit,
    ):
        with pytest.raises(RuntimeError, match="tx failed"):
            await SessionCreationService.create(
                usuario_id=USUARIO_ID,
                cliente_id=CLIENTE_ID,
                token_hash=TOKEN_HASH,
                device_context=_DEVICE,
                token_expires_at=TOKEN_EXPIRES,
                access_jti=ACCESS_JTI,
                access_exp=ACCESS_EXP,
            )
    mock_redis.assert_not_awaited()
    mock_audit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_evict_uses_revoke_tx_redis_and_audit():
    mock_uow = MagicMock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=False)

    with (
        patch(f"{_CREATE}.UnitOfWork", return_value=mock_uow),
        patch(f"{_CREATE}.stx.revoke_session_tx", new_callable=AsyncMock) as mock_revoke,
        patch(f"{_CREATE}.SessionRedisBridge.blacklist_session", new_callable=AsyncMock) as mock_bl,
        patch(
            f"{_CREATE}.SessionAuditEmitter.emit_session_limit_evicted",
            new_callable=AsyncMock,
        ) as mock_audit,
    ):
        await SessionCreationService._evict_session_for_limit(
            session_id=EVICT_SESSION_ID,
            family_id=EVICT_FAMILY_ID,
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
        )
    mock_revoke.assert_awaited_once()
    revoke_kwargs = mock_revoke.await_args.kwargs
    assert revoke_kwargs["session_revoked_reason"] == "admin_force"
    assert revoke_kwargs["family_invalidation_reason"] == "session_revoked"
    assert revoke_kwargs["token_revoked_reason"] == "family_compromised"
    mock_bl.assert_awaited_once_with(EVICT_SESSION_ID)
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_create_rejects_invalid_device_context():
    with pytest.raises(ValidationError):
        await SessionCreationService.create(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            device_context=DeviceContext(platform="invalid"),
            token_expires_at=TOKEN_EXPIRES,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_update_empresa_delegates_to_query():
    with patch(
        f"{_CREATE}.usq.update_session_empresa_core",
        new_callable=AsyncMock,
        return_value=1,
    ) as mock_update:
        await SessionCreationService.update_empresa(
            session_id=SESSION_ID,
            cliente_id=CLIENTE_ID,
            empresa_id=uuid4(),
            selection_token_completed=True,
        )
    mock_update.assert_awaited_once()
    assert mock_update.await_args.kwargs["selection_token_completed"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f7_policy_service_has_no_side_effect_imports():
    import inspect

    source = inspect.getsource(SessionPolicyService)
    forbidden = ("Redis", "AuditEmitter", "create_session", "revoke_session", "jwt")
    for token in forbidden:
        assert token not in source
