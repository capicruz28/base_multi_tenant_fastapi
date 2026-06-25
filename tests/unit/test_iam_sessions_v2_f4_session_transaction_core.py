"""F4B — tests unitarios C18 session_transaction_core."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.infrastructure.database.queries.auth.session import session_transaction_core as stx
from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()
OLD_TOKEN_HASH = "old" * 16
NEW_TOKEN_HASH = "new" * 16
EXPIRES_AT = datetime(2026, 12, 31, tzinfo=timezone.utc)


def _mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.execute = AsyncMock()
    return uow


def _is_insert(table: str, query) -> bool:
    return query.__class__.__name__ == "Insert" and query.table.name == table


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_create_session_executes_four_writes_in_order():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
    ])
    result = await stx.create_session_with_token_tx(
        uow,
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        session_expires_at=EXPIRES_AT,
        token_hash=OLD_TOKEN_HASH,
        token_expires_at=EXPIRES_AT,
        platform="web",
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
    )
    assert result == {
        "session_id": SESSION_ID,
        "family_id": FAMILY_ID,
        "token_id": TOKEN_ID,
        "expires_at": EXPIRES_AT,
    }
    assert uow.execute.await_count == 4
    tables = [call.args[0].table.name for call in uow.execute.await_args_list]
    assert tables == ["user_session", "token_family", "refresh_tokens", "token_family"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_create_session_first_insert_sets_rtr_fields():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
    ])
    await stx.create_session_with_token_tx(
        uow,
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        session_expires_at=EXPIRES_AT,
        token_hash=OLD_TOKEN_HASH,
        token_expires_at=EXPIRES_AT,
        platform="web",
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
    )
    family_insert = uow.execute.await_args_list[1].args[0]
    token_insert = uow.execute.await_args_list[2].args[0]
    assert _is_insert("token_family", family_insert)
    assert _is_insert("refresh_tokens", token_insert)
    family_params = family_insert.compile().params
    token_params = token_insert.compile().params
    assert family_params.get("current_token_id") is None
    assert token_params.get("parent_token_id") is None
    assert token_params.get("session_id") == SESSION_ID
    assert token_params.get("family_id") == FAMILY_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_create_session_rollback_if_family_update_fails():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 0},
    ])
    with pytest.raises(RuntimeError, match="current_token_id"):
        await stx.create_session_with_token_tx(
            uow,
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            session_expires_at=EXPIRES_AT,
            token_hash=OLD_TOKEN_HASH,
            token_expires_at=EXPIRES_AT,
            platform="web",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_rotate_follows_rtr_order_and_sets_parent_chain():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        [{
            "token_id": TOKEN_ID,
            "family_id": FAMILY_ID,
            "session_id": SESSION_ID,
            "usuario_id": USUARIO_ID,
            "empresa_id": None,
            "is_used": 0,
            "is_revoked": 0,
            "expires_at": EXPIRES_AT,
        }],
        [{"family_id": FAMILY_ID, "is_compromised": 0}],
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
    ])
    result = await stx.rotate_refresh_token_tx(
        uow,
        old_token_hash=OLD_TOKEN_HASH,
        new_token_hash=NEW_TOKEN_HASH,
        cliente_id=CLIENTE_ID,
        token_expires_at=EXPIRES_AT,
        new_token_id=NEW_TOKEN_ID,
    )
    assert result["old_token_id"] == TOKEN_ID
    assert result["new_token_id"] == NEW_TOKEN_ID
    assert result["family_id"] == FAMILY_ID
    assert result["session_id"] == SESSION_ID
    lock_sql = uow.execute.await_args_list[0].args[0]
    assert "updlock" in str(lock_sql).lower()
    family_lock_sql = uow.execute.await_args_list[1].args[0]
    assert "updlock" in str(family_lock_sql).lower()
    token_insert = uow.execute.await_args_list[2].args[0]
    assert token_insert.compile().params.get("parent_token_id") == TOKEN_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_rotate_rollback_when_mark_used_returns_zero():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        [{
            "token_id": TOKEN_ID,
            "family_id": FAMILY_ID,
            "session_id": SESSION_ID,
            "usuario_id": USUARIO_ID,
            "empresa_id": None,
            "is_used": 0,
            "is_revoked": 0,
            "expires_at": EXPIRES_AT,
        }],
        [{"family_id": FAMILY_ID, "is_compromised": 0}],
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 0},
    ])
    with pytest.raises(RuntimeError, match="MARK token used"):
        await stx.rotate_refresh_token_tx(
            uow,
            old_token_hash=OLD_TOKEN_HASH,
            new_token_hash=NEW_TOKEN_HASH,
            cliente_id=CLIENTE_ID,
            token_expires_at=EXPIRES_AT,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_revoke_session_updates_three_tables():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 2},
    ])
    result = await stx.revoke_session_tx(
        uow,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        cliente_id=CLIENTE_ID,
        session_revoked_reason="logout",
        family_invalidation_reason="session_revoked",
        token_revoked_reason="logout",
    )
    assert result == {"session_rows": 1, "family_rows": 1, "token_rows": 2}
    tables = {call.args[0].table.name for call in uow.execute.await_args_list}
    assert tables == {"user_session", "token_family", "refresh_tokens"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_revoke_all_lists_then_bulk_close_and_per_session():
    uow = _mock_uow()
    sid_a, sid_b = uuid4(), uuid4()
    uow.execute = AsyncMock(side_effect=[
        [{"session_id": sid_a}, {"session_id": sid_b}],
        {"rows_affected": 2},
        {"rows_affected": 2},
        {"rows_affected": 3},
    ])
    result = await stx.revoke_all_user_sessions_tx(
        uow,
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        session_revoked_reason="logout",
        family_invalidation_reason="session_revoked",
        token_revoked_reason="logout",
    )
    assert result["sessions_closed"] == 2
    assert result["families_compromised"] == 2
    assert result["tokens_revoked"] == 3
    assert result["session_count"] == 2
    assert uow.execute.await_count == 4
    bulk_family_update = uow.execute.await_args_list[2].args[0]
    bulk_token_update = uow.execute.await_args_list[3].args[0]
    assert bulk_family_update.table.name == "token_family"
    assert bulk_token_update.table.name == "refresh_tokens"
    family_sql = str(bulk_family_update.compile(compile_kwargs={"literal_binds": True})).lower()
    token_sql = str(bulk_token_update.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "usuario_id" in family_sql
    assert "usuario_id" in token_sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_handle_replay_locks_family_then_three_updates():
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        [{"family_id": FAMILY_ID}],
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 3},
    ])
    result = await stx.handle_replay_attack_tx(
        uow,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        token_id=TOKEN_ID,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
    )
    assert result["session_id"] == SESSION_ID
    assert result["family_id"] == FAMILY_ID
    assert result["token_id"] == TOKEN_ID
    lock_sql = uow.execute.await_args_list[0].args[0]
    assert "updlock" in str(lock_sql).lower()
    assert uow.execute.await_count == 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_all_writes_include_cliente_id_filter():
    uow = _mock_uow()
    uow.execute = AsyncMock(return_value={"rows_affected": 1})
    await stx.revoke_session_tx(
        uow,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        cliente_id=CLIENTE_ID,
        session_revoked_reason="logout",
        family_invalidation_reason="session_revoked",
        token_revoked_reason="logout",
    )
    for call in uow.execute.await_args_list:
        query = call.args[0]
        if hasattr(query, "compile"):
            compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
            assert "cliente_id" in compiled


@pytest.mark.unit
def test_f4b_session_package_exports_c18_functions():
    from app.infrastructure.database.queries.auth.session import __all__ as session_exports

    expected = {
        "create_session_with_token_tx",
        "rotate_refresh_token_tx",
        "revoke_session_tx",
        "revoke_all_user_sessions_tx",
        "handle_replay_attack_tx",
    }
    assert expected.issubset(set(session_exports))


@pytest.mark.unit
def test_f4b_auth_queries_exports_c18_functions():
    from app.infrastructure.database.queries.auth import __all__ as auth_exports

    assert "create_session_with_token_tx" in auth_exports
    assert "rotate_refresh_token_tx" in auth_exports
    assert "handle_replay_attack_tx" in auth_exports


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_rotate_rejects_already_used_token_post_lock():
    uow = _mock_uow()
    uow.execute = AsyncMock(return_value=[{
        "token_id": TOKEN_ID,
        "family_id": FAMILY_ID,
        "session_id": SESSION_ID,
        "usuario_id": USUARIO_ID,
        "is_used": 1,
        "is_revoked": 0,
        "expires_at": EXPIRES_AT,
    }])
    with pytest.raises(RuntimeError, match="TOKEN_ALREADY_USED"):
        await stx.rotate_refresh_token_tx(
            uow,
            old_token_hash=OLD_TOKEN_HASH,
            new_token_hash=NEW_TOKEN_HASH,
            cliente_id=CLIENTE_ID,
            token_expires_at=EXPIRES_AT,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4b_rotate_applies_explicit_empresa_id_to_successor_and_session():
    empresa_id = uuid4()
    uow = _mock_uow()
    uow.execute = AsyncMock(side_effect=[
        [{
            "token_id": TOKEN_ID,
            "family_id": FAMILY_ID,
            "session_id": SESSION_ID,
            "usuario_id": USUARIO_ID,
            "empresa_id": None,
            "is_used": 0,
            "is_revoked": 0,
            "expires_at": EXPIRES_AT,
        }],
        [{"family_id": FAMILY_ID, "is_compromised": 0}],
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
        {"rows_affected": 1},
    ])
    result = await stx.rotate_refresh_token_tx(
        uow,
        old_token_hash=OLD_TOKEN_HASH,
        new_token_hash=NEW_TOKEN_HASH,
        cliente_id=CLIENTE_ID,
        token_expires_at=EXPIRES_AT,
        new_token_id=NEW_TOKEN_ID,
        empresa_id=empresa_id,
    )
    assert result["empresa_id"] == empresa_id
    token_insert = uow.execute.await_args_list[2].args[0]
    session_update = uow.execute.await_args_list[5].args[0]
    assert token_insert.compile().params.get("empresa_id") == empresa_id
    assert session_update.compile().params.get("empresa_id") == empresa_id
