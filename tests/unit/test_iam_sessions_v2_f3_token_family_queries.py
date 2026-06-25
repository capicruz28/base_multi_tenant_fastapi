"""F3B — tests unitarios C16 token_family_queries_core."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.infrastructure.database.queries.auth.session import token_family_queries_core as tfq

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
TOKEN_ID = uuid4()

_EXEC_QUERY = "app.infrastructure.database.queries_async.execute_query"
_EXEC_INSERT = "app.infrastructure.database.queries_async.execute_insert"
_EXEC_UPDATE = "app.infrastructure.database.queries_async.execute_update"


def _compiled_has_cliente_id(query) -> bool:
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    return "cliente_id" in compiled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_insert_token_family_sets_null_current_token():
    row = {
        "family_id": FAMILY_ID,
        "session_id": SESSION_ID,
        "cliente_id": CLIENTE_ID,
        "current_token_id": None,
        "is_compromised": False,
    }
    with (
        patch(_EXEC_INSERT, new_callable=AsyncMock) as mock_insert,
        patch.object(tfq, "get_family_by_id_core", new_callable=AsyncMock) as mock_get,
    ):
        mock_insert.return_value = {"rows_affected": 1}
        mock_get.return_value = row
        result = await tfq.insert_token_family_core(
            session_id=SESSION_ID,
            usuario_id=USUARIO_ID,
            cliente_id=CLIENTE_ID,
            family_id=FAMILY_ID,
        )
    assert result == row
    assert result["current_token_id"] is None
    mock_insert.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_update_current_token_id_filters_tenant_and_non_compromised():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await tfq.update_current_token_id_core(
            FAMILY_ID,
            CLIENTE_ID,
            current_token_id=TOKEN_ID,
        )
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "current_token_id" in compiled
    assert "is_compromised" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_mark_family_compromised_rejects_invalid_reason():
    with pytest.raises(ValidationError, match="invalidation_reason"):
        await tfq.mark_family_compromised_core(
            FAMILY_ID,
            CLIENTE_ID,
            invalidation_reason="invalid",
        )


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason",
    ["replay_detected", "session_revoked", "admin_force", "password_reset", "security_policy"],
)
async def test_f3b_mark_family_compromised_accepts_check_reasons(reason: str):
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 1}
        affected = await tfq.mark_family_compromised_core(
            FAMILY_ID,
            CLIENTE_ID,
            invalidation_reason=reason,
        )
    assert affected == 1
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "is_compromised" in compiled
    assert "compromised_at" in compiled
    assert "invalidation_reason" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_mark_family_compromised_idempotent_when_already_compromised():
    with patch(_EXEC_UPDATE, new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"rows_affected": 0}
        affected = await tfq.mark_family_compromised_core(
            FAMILY_ID,
            CLIENTE_ID,
            invalidation_reason="replay_detected",
        )
    assert affected == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_get_family_by_id_includes_compromised_state():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"family_id": FAMILY_ID, "is_compromised": True}]
        row = await tfq.get_family_by_id_core(FAMILY_ID, CLIENTE_ID)
    assert row["is_compromised"] is True
    assert _compiled_has_cliente_id(mock_query.await_args.args[0])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_get_family_by_session_id_filters_non_compromised():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"family_id": FAMILY_ID}]
        row = await tfq.get_family_by_session_id_core(SESSION_ID, CLIENTE_ID)
    assert row["family_id"] == FAMILY_ID
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "session_id" in compiled
    assert "is_compromised" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f3b_get_family_by_current_token_id_lookup():
    with patch(_EXEC_QUERY, new_callable=AsyncMock) as mock_query:
        mock_query.return_value = [{"family_id": FAMILY_ID, "current_token_id": TOKEN_ID}]
        row = await tfq.get_family_by_current_token_id_core(TOKEN_ID, CLIENTE_ID)
    assert row["current_token_id"] == TOKEN_ID
    query = mock_query.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "current_token_id" in compiled
    assert _compiled_has_cliente_id(query)


@pytest.mark.unit
def test_f3b_session_package_exports_c16_functions():
    from app.infrastructure.database.queries.auth.session import __all__ as session_exports

    expected = {
        "insert_token_family_core",
        "update_current_token_id_core",
        "mark_family_compromised_core",
        "get_family_by_id_core",
        "get_family_by_session_id_core",
        "get_family_by_current_token_id_core",
    }
    assert expected.issubset(set(session_exports))


@pytest.mark.unit
def test_f3b_auth_queries_exports_c16_functions():
    from app.infrastructure.database.queries.auth import __all__ as auth_exports

    assert "insert_token_family_core" in auth_exports
    assert "mark_family_compromised_core" in auth_exports
