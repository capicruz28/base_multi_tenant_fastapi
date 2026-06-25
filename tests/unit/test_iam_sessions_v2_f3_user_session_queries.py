"""F3A — tests unitarios C15 user_session_queries_core."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import user_session_queries_core as usq

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
EMPRESA_ID = uuid4()
EXPIRES_AT = datetime(2026, 12, 31, 23, 59, 59)

_EXEC_QUERY = "app.infrastructure.database.queries_async.execute_query"
_EXEC_INSERT = "app.infrastructure.database.queries_async.execute_insert"
_EXEC_UPDATE = "app.infrastructure.database.queries_async.execute_update"


def _compiled_has_cliente_id(query) -> bool:
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    return "cliente_id" in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_insert_user_session_validates_platform():
    with pytest.raises(ValidationError, match="platform"):
        await usq.insert_user_session_core(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            expires_at=EXPIRES_AT,
            platform="invalid",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_insert_user_session_calls_insert_and_readback():
    row = {"session_id": SESSION_ID, "cliente_id": CLIENTE_ID, "is_active": True}
    with (
        patch(_EXEC_INSERT, new_callable=AsyncMock) as mock_insert,
        patch.object(usq, "get_active_session_by_id_core", new_callable=AsyncMock) as mock_get,
    ):
        mock_insert.return_value = {"rows_affected": 1}
        mock_get.return_value = row
        result = await usq.insert_user_session_core(
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            expires_at=EXPIRES_AT,
            platform="web",
            session_id=SESSION_ID,
        )
    assert result == row
    mock_insert.assert_awaited_once()
    mock_get.assert_awaited_once_with(SESSION_ID, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_update_session_empresa_filters_tenant():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await usq.update_session_empresa_core(
            SESSION_ID,
            CLIENTE_ID,
            empresa_id=EMPRESA_ID,
            selection_token_completed=True,
        )
    assert affected == 1
    query = mock_update.await_args.args[0]
    assert _compiled_has_cliente_id(query)
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "login_ip" not in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_update_session_on_refresh_sets_last_refresh_at():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await usq.update_session_on_refresh_core(
            SESSION_ID,
            CLIENTE_ID,
            last_seen_ip="10.0.0.1",
        )
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "last_refresh_at" in compiled
    assert "last_seen_ip" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_touch_business_activity_updates_column():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await usq.touch_business_activity_core(SESSION_ID, CLIENTE_ID)
    assert affected == 1
    compiled = str(
        mock_update.await_args.args[0].compile(compile_kwargs={"literal_binds": True})
    ).lower()
    assert "last_business_activity_at" in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_close_session_rejects_invalid_revoked_reason():
    with pytest.raises(ValidationError, match="revoked_reason"):
        await usq.close_session_core(
            SESSION_ID,
            CLIENTE_ID,
            revoked_reason="not_valid",
        )


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["logout", "security", "expired"])
async def test_f3a_close_session_accepts_check_reasons(reason: str):
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await usq.close_session_core(
            SESSION_ID,
            CLIENTE_ID,
            revoked_reason=reason,
        )
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_active" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_close_session_idempotent_zero_rows():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 0}
        affected = await usq.close_session_core(
            SESSION_ID,
            CLIENTE_ID,
            revoked_reason="logout",
        )
    assert affected == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_close_all_user_sessions_bulk():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 3}
        affected = await usq.close_all_user_sessions_core(
            USUARIO_ID,
            CLIENTE_ID,
            revoked_reason="logout",
        )
    assert affected == 3
    assert _compiled_has_cliente_id(mock_update.await_args.args[0])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_get_active_session_by_id_filters_active_and_tenant():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"session_id": SESSION_ID}]
        row = await usq.get_active_session_by_id_core(SESSION_ID, CLIENTE_ID)
    assert row["session_id"] == SESSION_ID
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_active" in compiled
    assert "expires_at" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_count_active_sessions_returns_total():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"total": 2}]
        count = await usq.count_active_sessions_core(USUARIO_ID, CLIENTE_ID)
    assert count == 2
    assert _compiled_has_cliente_id(mock_query.await_args.args[0])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_list_active_sessions_oldest_first_orders_by_created_at():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = []
        await usq.list_active_sessions_oldest_first_core(
            USUARIO_ID,
            CLIENTE_ID,
            limit=5,
        )
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "order by" in compiled
    assert "created_at" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_is_session_idle_expired_disabled_when_timeout_zero():
    assert (
        await usq.is_session_idle_expired_core(SESSION_ID, CLIENTE_ID, 0) is False
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_is_session_idle_expired_sql_uses_tenant_filter():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"idle_expired": 1}]
        expired = await usq.is_session_idle_expired_core(
            SESSION_ID,
            CLIENTE_ID,
            30,
        )
    assert expired is True
    query = mock_query.await_args.args[0]
    assert "cliente_id" in str(query).lower()
    assert "last_refresh_at" in str(query).lower() or "created_at" in str(query).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_is_session_absolute_expired_sql():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"absolute_expired": 1}]
        expired = await usq.is_session_absolute_expired_core(SESSION_ID, CLIENTE_ID)
    assert expired is True
    assert "expires_at" in str(mock_query.await_args.args[0]).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_find_session_by_device_empty_device_returns_none():
    assert (
        await usq.find_session_by_device_core(
            USUARIO_ID,
            CLIENTE_ID,
            device_id="  ",
        )
        is None
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_find_session_by_device_filters_device_and_tenant():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"device_id": "dev-1"}]
        row = await usq.find_session_by_device_core(
            USUARIO_ID,
            CLIENTE_ID,
            device_id="dev-1",
        )
    assert row["device_id"] == "dev-1"
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "device_id" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_purge_closed_sessions_applies_retention_and_si_exclusion():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"rows_affected": 4}]
        deleted = await usq.purge_closed_sessions_core(
            CLIENTE_ID,
            retention_days=90,
            compromised_retention_days=365,
        )
    assert deleted == 4
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_active" in compiled
    assert "revoked_at" in compiled
    assert "is_compromised" in compiled
    assert "refresh_tokens" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3a_purge_closed_sessions_rejects_invalid_retention():
    with pytest.raises(ValidationError, match="retention_days"):
        await usq.purge_closed_sessions_core(CLIENTE_ID, retention_days=0)


@pytest.mark.unit
def test_f3a_session_package_exports_c15_functions():
    from app.infrastructure.database.queries.auth.session import __all__ as session_exports

    expected = {
        "insert_user_session_core",
        "update_session_empresa_core",
        "update_session_on_refresh_core",
        "touch_business_activity_core",
        "close_session_core",
        "close_all_user_sessions_core",
        "get_active_session_by_id_core",
        "count_active_sessions_core",
        "list_active_sessions_oldest_first_core",
        "is_session_idle_expired_core",
        "is_session_absolute_expired_core",
        "find_session_by_device_core",
        "purge_closed_sessions_core",
    }
    assert expected.issubset(set(session_exports))


@pytest.mark.unit
def test_f3a_auth_queries_exports_c15_functions():
    from app.infrastructure.database.queries.auth import __all__ as auth_exports

    assert "insert_user_session_core" in auth_exports
    assert "close_session_core" in auth_exports
