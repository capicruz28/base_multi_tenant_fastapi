"""IAM-BE-SESSIONS-P1-04: rotación atómica (dark code, sin endpoints)."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import DatabaseError
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.application.services.rotate_refresh_token_service import (
    build_rotate_result,
    rotate_refresh_token_service,
)
from app.infrastructure.database.queries.auth.refresh_token_rotate_queries_core import (
    SQL_INSERT_ROTATED_REFRESH_TOKEN,
    SQL_LOCK_REFRESH_TOKEN_BY_HASH,
    SQL_REVOKE_OLD_FOR_ROTATION,
    SQL_RECORD_ACTIVITY_IN_TX,
    rotate_refresh_token_core,
)

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()


def _active_locked_row(*, idle_expired: int = 0, is_expired: int = 0):
    return {
        "token_id": OLD_TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "token_hash": "old-hash",
        "expires_at": datetime.utcnow() + timedelta(days=7),
        "is_revoked": False,
        "revoked_reason": None,
        "created_at": datetime.utcnow(),
        "last_used_at": None,
        "client_type": "web",
        "cliente_id": CLIENTE_ID,
        "empresa_id": None,
        "idle_expired": idle_expired,
        "is_expired": is_expired,
    }


class TestRotateResult:
    def test_build_rotate_result_rotated_success(self):
        core = {
            "outcome": RotateOutcome.ROTATED,
            "old_token_id": OLD_TOKEN_ID,
            "new_token_id": NEW_TOKEN_ID,
            "revoked_reason": RevokedReason.SESSION_ROTATED,
            "old_token_row": {"usuario_id": USUARIO_ID},
            "new_token_row": {"token_id": NEW_TOKEN_ID, "usuario_id": USUARIO_ID},
        }
        result = build_rotate_result(cliente_id=CLIENTE_ID, core_result=core)
        assert isinstance(result, RotateResult)
        assert result.success is True
        assert result.outcome == RotateOutcome.ROTATED
        assert result.new_token_id == NEW_TOKEN_ID
        assert result.old_token_id == OLD_TOKEN_ID
        assert result.idle_expired is False

    def test_build_rotate_result_idle_timeout(self):
        core = {
            "outcome": RotateOutcome.IDLE_TIMEOUT,
            "old_token_id": OLD_TOKEN_ID,
            "revoked_reason": RevokedReason.IDLE_TIMEOUT,
            "old_token_row": {"usuario_id": USUARIO_ID},
        }
        result = build_rotate_result(cliente_id=CLIENTE_ID, core_result=core)
        assert result.outcome == RotateOutcome.IDLE_TIMEOUT
        assert result.idle_expired is True
        assert result.success is False


def test_lock_sql_contains_updlock_rowlock_and_getdate():
    sql = SQL_LOCK_REFRESH_TOKEN_BY_HASH.upper()
    assert "UPDLOCK" in sql
    assert "ROWLOCK" in sql
    assert "GETDATE()" in sql
    assert "DATEDIFF" in sql
    assert "COALESCE" in sql


def test_rotation_sql_statements_present():
    assert "INSERT INTO refresh_tokens" in SQL_INSERT_ROTATED_REFRESH_TOKEN
    assert "OUTPUT" in SQL_INSERT_ROTATED_REFRESH_TOKEN
    assert ":revoked_reason" in SQL_REVOKE_OLD_FOR_ROTATION
    assert "GETDATE()" in SQL_RECORD_ACTIVITY_IN_TX


@pytest.mark.asyncio
async def test_rotate_refresh_token_core_success_flow():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            [_active_locked_row()],
            {"rows_affected": 1},
            [{"token_id": NEW_TOKEN_ID, "usuario_id": USUARIO_ID, "cliente_id": CLIENTE_ID}],
            [{"token_id": OLD_TOKEN_ID, "is_revoked": True}],
        ]
    )

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="old-hash",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        expires_at=datetime.utcnow() + timedelta(days=7),
        idle_timeout_minutes=60,
    )

    assert result["outcome"] == RotateOutcome.ROTATED
    assert result["new_token_id"] == NEW_TOKEN_ID
    assert mock_uow.execute.await_count == 4
    first_call_sql = str(mock_uow.execute.await_args_list[0].args[0]).upper()
    assert "UPDLOCK" in first_call_sql


@pytest.mark.asyncio
async def test_rotate_refresh_token_core_idle_revokes_in_tx():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            [_active_locked_row(idle_expired=1)],
            [{"token_id": OLD_TOKEN_ID, "is_revoked": True}],
        ]
    )

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="old-hash",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        expires_at=datetime.utcnow() + timedelta(days=7),
        idle_timeout_minutes=60,
    )

    assert result["outcome"] == RotateOutcome.IDLE_TIMEOUT
    assert result["revoked_reason"] == RevokedReason.IDLE_TIMEOUT
    assert mock_uow.execute.await_count == 2
    idle_revoke_sql = str(mock_uow.execute.await_args_list[1].args[0]).upper()
    assert "UPDATE" in idle_revoke_sql


@pytest.mark.asyncio
async def test_rotate_refresh_token_core_not_found():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(return_value=[])

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="missing",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.NOT_FOUND
    mock_uow.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_rotate_refresh_token_core_raises_on_failed_revoke_triggers_uow_rollback():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            [_active_locked_row()],
            {"rows_affected": 1},
            [{"token_id": NEW_TOKEN_ID, "usuario_id": USUARIO_ID}],
            [],
        ]
    )

    with pytest.raises(RuntimeError, match="No se pudo revocar token antiguo"):
        await rotate_refresh_token_core(
            mock_uow,
            old_token_hash="old-hash",
            new_token_hash="new-hash",
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )


@pytest.mark.asyncio
async def test_rotate_refresh_token_service_uses_unit_of_work_and_commits():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock()
    mock_uow.get_operations_count = MagicMock(return_value=3)
    mock_uow.is_committed = MagicMock(return_value=False)

    core_result = {
        "outcome": RotateOutcome.ROTATED,
        "old_token_id": OLD_TOKEN_ID,
        "new_token_id": NEW_TOKEN_ID,
        "revoked_reason": RevokedReason.SESSION_ROTATED,
        "old_token_row": {"usuario_id": USUARIO_ID},
        "new_token_row": {"token_id": NEW_TOKEN_ID, "usuario_id": USUARIO_ID},
    }

    mock_uow_cm = MagicMock()
    mock_uow_cm.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow_cm.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.UnitOfWork",
        return_value=mock_uow_cm,
    ), patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.rotate_refresh_token_core",
        AsyncMock(return_value=core_result),
    ) as mock_core, patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.leer_session_idle_timeout_minutos",
        AsyncMock(return_value=60),
    ):
        result = await rotate_refresh_token_service(
            old_refresh_token="old-jwt",
            new_refresh_token="new-jwt",
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
        )

    assert result.success is True
    mock_uow_cm.__aenter__.assert_awaited_once()
    mock_uow_cm.__aexit__.assert_awaited_once()
    mock_core.assert_awaited_once()
    assert mock_core.await_args.kwargs["cliente_id"] == CLIENTE_ID


@pytest.mark.asyncio
async def test_rotate_refresh_token_service_rollback_on_core_exception():
    mock_uow = MagicMock()
    mock_uow_cm = MagicMock()
    mock_uow_cm.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow_cm.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.UnitOfWork",
        return_value=mock_uow_cm,
    ), patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.rotate_refresh_token_core",
        AsyncMock(side_effect=RuntimeError("txn failed")),
    ), patch(
        "app.modules.auth.application.services.rotate_refresh_token_service.leer_session_idle_timeout_minutos",
        AsyncMock(return_value=60),
    ):
        with pytest.raises(DatabaseError) as exc_info:
            await rotate_refresh_token_service(
                old_refresh_token="old-jwt",
                new_refresh_token="new-jwt",
                cliente_id=CLIENTE_ID,
                usuario_id=USUARIO_ID,
            )

    assert exc_info.value.internal_code == "REFRESH_TOKEN_ROTATE_ATOMIC_ERROR"
    mock_uow_cm.__aexit__.assert_awaited_once()


def test_legacy_refresh_service_unchanged_no_atomic_import():
    """El servicio legacy no importa la rotación atómica."""
    import app.modules.auth.application.services.refresh_token_service as rts

    source = open(rts.__file__, encoding="utf-8").read()
    assert "rotate_refresh_token" not in source


def test_refresh_endpoint_wires_atomic_rotation():
    import app.modules.auth.presentation.endpoints as endpoints

    source = open(endpoints.__file__, encoding="utf-8").read()
    assert "rotate_refresh_token_service" in source
    assert "get_current_user_for_refresh_endpoint" in source
