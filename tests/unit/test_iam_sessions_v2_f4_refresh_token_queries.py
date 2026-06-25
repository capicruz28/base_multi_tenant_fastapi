"""F4A — tests unitarios C17 refresh_token_queries_core (session v3)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import refresh_token_queries_core as rtq

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
PARENT_TOKEN_ID = uuid4()
TOKEN_HASH = "a" * 64
EXPIRES_AT = datetime(2026, 12, 31, tzinfo=timezone.utc)

_EXEC_QUERY = "app.infrastructure.database.queries_async.execute_query"
_EXEC_INSERT = "app.infrastructure.database.queries_async.execute_insert"
_EXEC_UPDATE = "app.infrastructure.database.queries_async.execute_update"


def _compiled_has_cliente_id(query) -> bool:
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    return "cliente_id" in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_insert_refresh_token_sets_rtr_hierarchy():
    row = {
        "token_id": TOKEN_ID,
        "family_id": FAMILY_ID,
        "session_id": SESSION_ID,
        "parent_token_id": PARENT_TOKEN_ID,
        "cliente_id": CLIENTE_ID,
        "usuario_id": USUARIO_ID,
        "token_hash": TOKEN_HASH,
        "is_used": False,
        "is_revoked": False,
    }
    with (
        patch(_EXEC_INSERT, new_callable=AsyncMock) as mock_insert,
        patch.object(rtq, "_get_token_by_id_core", new_callable=AsyncMock) as mock_get,
    ):
        mock_insert.return_value = {"rows_affected": 1}
        mock_get.return_value = row
        result = await rtq.insert_refresh_token_core(
            family_id=FAMILY_ID,
            session_id=SESSION_ID,
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            expires_at=EXPIRES_AT,
            parent_token_id=PARENT_TOKEN_ID,
            token_id=TOKEN_ID,
        )
    assert result == row
    assert result["parent_token_id"] == PARENT_TOKEN_ID
    mock_insert.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_insert_first_token_allows_null_parent():
    row = {"token_id": TOKEN_ID, "parent_token_id": None}
    with (
        patch(_EXEC_INSERT, new_callable=AsyncMock),
        patch.object(rtq, "_get_token_by_id_core", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = row
        result = await rtq.insert_refresh_token_core(
            family_id=FAMILY_ID,
            session_id=SESSION_ID,
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            token_hash=TOKEN_HASH,
            expires_at=EXPIRES_AT,
            token_id=TOKEN_ID,
        )
    assert result["parent_token_id"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_get_by_hash_excludes_used_revoked_expired():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"token_id": TOKEN_ID}]
        row = await rtq.get_refresh_token_by_hash_core(TOKEN_HASH, CLIENTE_ID)
    assert row["token_id"] == TOKEN_ID
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_used" in compiled
    assert "is_revoked" in compiled
    assert "expires_at" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_get_by_hash_any_state_only_filters_tenant_and_hash():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"token_id": TOKEN_ID, "is_used": True, "is_revoked": True}]
        row = await rtq.get_refresh_token_by_hash_any_state_core(TOKEN_HASH, CLIENTE_ID)
    assert row["is_used"] is True
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "token_hash" in compiled
    assert _compiled_has_cliente_id(query)
    assert " is_used = " not in compiled
    assert " is_revoked = " not in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_mark_token_used_sets_timestamps_and_filters_usable():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await rtq.mark_token_used_core(TOKEN_ID, CLIENTE_ID)
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_used" in compiled
    assert "used_at" in compiled
    assert "last_used_at" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_mark_token_used_returns_zero_when_already_used():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 0}
        affected = await rtq.mark_token_used_core(TOKEN_ID, CLIENTE_ID)
    assert affected == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_revoke_token_rejects_invalid_reason():
    with pytest.raises(ValidationError, match="revoked_reason"):
        await rtq.revoke_token_core(TOKEN_ID, CLIENTE_ID, revoked_reason="session_rotated")


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason",
    ["logout", "replay_detected", "admin_force", "password_reset", "family_compromised"],
)
async def test_f4a_revoke_token_accepts_check_reasons(reason: str):
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await rtq.revoke_token_core(TOKEN_ID, CLIENTE_ID, revoked_reason=reason)
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_revoked" in compiled
    assert "revoked_at" in compiled
    assert "revoked_reason" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_revoke_tokens_by_session_bulk():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 3}
        affected = await rtq.revoke_tokens_by_session_core(
            SESSION_ID,
            CLIENTE_ID,
            revoked_reason="logout",
        )
    assert affected == 3
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "session_id" in compiled
    assert "is_revoked" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_purge_expired_tokens_applies_retention_policy():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"rows_affected": 5}]
        deleted = await rtq.purge_expired_tokens_core(CLIENTE_ID, retention_days=90)
    assert deleted == 5
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "dateadd" in compiled
    assert "is_used" in compiled
    assert "is_revoked" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4a_purge_expired_tokens_rejects_invalid_retention():
    with pytest.raises(ValidationError, match="retention_days"):
        await rtq.purge_expired_tokens_core(CLIENTE_ID, retention_days=0)


@pytest.mark.unit
def test_f4a_session_package_exports_c17_functions():
    from app.infrastructure.database.queries.auth.session import __all__ as session_exports

    expected = {
        "insert_refresh_token_core",
        "get_refresh_token_by_hash_core",
        "get_refresh_token_by_hash_any_state_core",
        "mark_token_used_core",
        "revoke_token_core",
        "revoke_tokens_by_session_core",
        "purge_expired_tokens_core",
    }
    assert expected.issubset(set(session_exports))


@pytest.mark.unit
def test_f4a_auth_queries_exports_c17_v3_only_functions():
    from app.infrastructure.database.queries.auth import __all__ as auth_exports

    assert "mark_token_used_core" in auth_exports
    assert "purge_expired_tokens_core" in auth_exports
    assert "revoke_token_core" in auth_exports
    assert "revoke_tokens_by_session_core" in auth_exports
