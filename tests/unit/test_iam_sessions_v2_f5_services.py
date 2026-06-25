"""F5 — tests unitarios C06 SessionRedisBridge + C07 SessionAuditEmitter."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.session_audit_emitter import SessionAuditEmitter
from app.modules.auth.application.services.session_redis_bridge import (
    SessionRedisBridge,
    _session_access_key_v1,
    _session_access_key_v2,
)

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
TOKEN_ID = uuid4()
FAMILY_ID = uuid4()
JTI = "test-jti-123"
EXP = 4_000_000_000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_link_access_writes_v2_and_v1_dual_key():
    with patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.get_json",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_get, patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.set_json",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_set:
        ok = await SessionRedisBridge.link_access(
            SESSION_ID,
            JTI,
            EXP,
            token_id=TOKEN_ID,
        )
    assert ok is True
    assert mock_set.await_count == 2
    v2_key = _session_access_key_v2(SESSION_ID)
    v1_key = _session_access_key_v1(TOKEN_ID)
    keys = [call.args[0] for call in mock_set.await_args_list]
    assert v2_key in keys
    assert v1_key in keys
    v2_payload = mock_set.await_args_list[keys.index(v2_key)].args[1]
    assert v2_payload["jti"] == JTI
    assert v2_payload["token_id"] == str(TOKEN_ID).lower()
    mock_get.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_link_access_blacklists_previous_jti_on_rotation():
    with patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.get_json",
        new_callable=AsyncMock,
        return_value={"jti": "old-jti", "exp": EXP},
    ), patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.set_json",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.set_token_blacklist",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_blacklist:
        await SessionRedisBridge.link_access(SESSION_ID, JTI, EXP, token_id=TOKEN_ID)
    mock_blacklist.assert_awaited_once()
    assert mock_blacklist.await_args.args[0] == "old-jti"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_link_access_fail_soft_when_redis_raises():
    with patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.get_json",
        new_callable=AsyncMock,
        side_effect=RuntimeError("redis down"),
    ):
        ok = await SessionRedisBridge.link_access(SESSION_ID, JTI, EXP)
    assert ok is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_get_session_access_mapping_v2_then_v1_fallback():
    with patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.get_json",
        new_callable=AsyncMock,
        side_effect=[None, {"jti": JTI, "exp": EXP}],
    ) as mock_get:
        payload = await SessionRedisBridge.get_session_access_mapping(
            SESSION_ID,
            token_id=TOKEN_ID,
        )
    assert payload["jti"] == JTI
    assert mock_get.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_blacklist_session_reads_mapping_and_deletes_keys():
    with patch.object(
        SessionRedisBridge,
        "get_session_access_mapping",
        new_callable=AsyncMock,
        return_value={"jti": JTI, "exp": EXP, "token_id": str(TOKEN_ID).lower()},
    ), patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.set_token_blacklist",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_blacklist, patch(
        "app.modules.auth.application.services.session_redis_bridge.RedisService.delete_key",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_delete:
        ok = await SessionRedisBridge.blacklist_session(SESSION_ID, token_id=TOKEN_ID)
    assert ok is True
    mock_blacklist.assert_awaited_once()
    assert mock_delete.await_count >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_blacklist_session_no_mapping_is_noop_success():
    with patch.object(
        SessionRedisBridge,
        "get_session_access_mapping",
        new_callable=AsyncMock,
        return_value=None,
    ):
        ok = await SessionRedisBridge.blacklist_session(SESSION_ID)
    assert ok is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_blacklist_all_user_sessions_iterates_active_sessions():
    sid_a, sid_b = uuid4(), uuid4()
    with patch(
        "app.modules.auth.application.services.session_redis_bridge.list_active_sessions_oldest_first_core",
        new_callable=AsyncMock,
        return_value=[{"session_id": sid_a}, {"session_id": sid_b}],
    ) as mock_list, patch.object(
        SessionRedisBridge,
        "blacklist_session",
        new_callable=AsyncMock,
        side_effect=[True, False],
    ) as mock_blacklist:
        count = await SessionRedisBridge.blacklist_all_user_sessions(USUARIO_ID, CLIENTE_ID)
    assert count == 1
    mock_list.assert_awaited_once_with(USUARIO_ID, CLIENTE_ID)
    assert mock_blacklist.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_session_access_keys_use_lowercase_uuid():
    assert _session_access_key_v2(SESSION_ID) == f"session:access_jti:{str(SESSION_ID).lower()}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_emit_login_success_calls_audit_with_metadata():
    with patch(
        "app.modules.auth.application.services.session_audit_emitter.AuditService.registrar_auth_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await SessionAuditEmitter.emit_login_success(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
            platform="web",
            login_method="password",
            device_id="device-1",
        )
    mock_audit.assert_awaited_once()
    kwargs = mock_audit.await_args.kwargs
    assert kwargs["evento"] == "login_success"
    assert kwargs["exito"] is True
    assert kwargs["metadata"]["session_id"] == str(SESSION_ID)
    assert kwargs["metadata"]["platform"] == "web"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_emit_replay_detected_always_exito_false():
    with patch(
        "app.modules.auth.application.services.session_audit_emitter.AuditService.registrar_auth_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await SessionAuditEmitter.emit_replay_detected(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
            family_id=FAMILY_ID,
            token_id=TOKEN_ID,
        )
    assert mock_audit.await_args.kwargs["exito"] is False
    assert mock_audit.await_args.kwargs["evento"] == "replay_detected"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_emit_refresh_success_includes_rtr_ids():
    with patch(
        "app.modules.auth.application.services.session_audit_emitter.AuditService.registrar_auth_event",
        new_callable=AsyncMock,
    ) as mock_audit:
        await SessionAuditEmitter.emit_refresh_success(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
            token_id=TOKEN_ID,
            family_id=FAMILY_ID,
        )
    meta = mock_audit.await_args.kwargs["metadata"]
    assert meta["token_id"] == str(TOKEN_ID)
    assert meta["family_id"] == str(FAMILY_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f5_audit_fail_soft_does_not_propagate():
    with patch(
        "app.modules.auth.application.services.session_audit_emitter.AuditService.registrar_auth_event",
        new_callable=AsyncMock,
        side_effect=RuntimeError("audit db down"),
    ):
        await SessionAuditEmitter.emit_logout(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            session_id=SESSION_ID,
        )


@pytest.mark.unit
def test_f5_services_package_exports():
    from app.modules.auth.application.services import __all__ as exports

    assert "SessionAuditEmitter" in exports
    assert "SessionRedisBridge" in exports
