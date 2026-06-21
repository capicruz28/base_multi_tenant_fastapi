"""IAM-BE-SESSIONS-P1-04-HOTFIX-01: USER_MISMATCH comparación UUID normalizada."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.infrastructure.database.queries.auth.refresh_token_rotate_queries_core import (
    _coerce_usuario_id_uuid,
    _refresh_token_user_mismatch,
    rotate_refresh_token_core,
)
from app.modules.auth.application.session.rotate_result import RotateOutcome

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
OTHER_USUARIO_ID = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()
USUARIO_ID_STR = str(USUARIO_ID)


def _locked_row(*, usuario_id=USUARIO_ID):
    return {
        "token_id": OLD_TOKEN_ID,
        "usuario_id": usuario_id,
        "token_hash": "old-hash",
        "expires_at": datetime.utcnow() + timedelta(days=7),
        "is_revoked": False,
        "revoked_reason": None,
        "created_at": datetime.utcnow(),
        "last_used_at": None,
        "client_type": "web",
        "cliente_id": CLIENTE_ID,
        "empresa_id": None,
        "idle_expired": 0,
        "is_expired": 0,
    }


class TestCoerceUsuarioIdUuid:
    def test_uuid_passthrough(self):
        assert _coerce_usuario_id_uuid(USUARIO_ID) == USUARIO_ID

    def test_str_valid(self):
        assert _coerce_usuario_id_uuid(USUARIO_ID_STR) == USUARIO_ID

    def test_none(self):
        assert _coerce_usuario_id_uuid(None) is None

    def test_invalid_str(self):
        assert _coerce_usuario_id_uuid("not-a-uuid") is None


class TestRefreshTokenUserMismatch:
    def test_uuid_vs_uuid_match(self):
        row = {"usuario_id": USUARIO_ID}
        assert _refresh_token_user_mismatch(row, USUARIO_ID) is False

    def test_str_row_vs_uuid_param_match(self):
        row = {"usuario_id": USUARIO_ID_STR}
        assert _refresh_token_user_mismatch(row, USUARIO_ID) is False

    def test_uuid_row_vs_str_param_match(self):
        row = {"usuario_id": USUARIO_ID}
        assert _refresh_token_user_mismatch(row, USUARIO_ID_STR) is False

    def test_str_vs_str_match(self):
        row = {"usuario_id": USUARIO_ID_STR}
        assert _refresh_token_user_mismatch(row, USUARIO_ID_STR) is False

    def test_none_param_mismatch(self):
        row = {"usuario_id": USUARIO_ID_STR}
        assert _refresh_token_user_mismatch(row, None) is True

    def test_invalid_param_mismatch(self):
        row = {"usuario_id": USUARIO_ID_STR}
        assert _refresh_token_user_mismatch(row, "invalid-uuid") is True

    def test_distinct_values_mismatch(self):
        row = {"usuario_id": USUARIO_ID_STR}
        assert _refresh_token_user_mismatch(row, str(OTHER_USUARIO_ID)) is True

    def test_empty_row_usuario_id_skips_mismatch(self):
        assert _refresh_token_user_mismatch({"usuario_id": None}, USUARIO_ID) is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "row_usuario_id,param_usuario_id",
    [
        (USUARIO_ID, USUARIO_ID),
        (USUARIO_ID_STR, USUARIO_ID),
        (USUARIO_ID, USUARIO_ID_STR),
        (USUARIO_ID_STR, USUARIO_ID_STR),
    ],
    ids=["uuid-uuid", "str-uuid", "uuid-str", "str-str"],
)
async def test_core_rotates_when_usuario_id_types_differ_but_same_value(
    row_usuario_id, param_usuario_id,
):
    """Regresión staging: mismos UUID con distintos tipos → ROTATED, no USER_MISMATCH."""
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            [_locked_row(usuario_id=row_usuario_id)],
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
        usuario_id=param_usuario_id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.ROTATED
    assert mock_uow.execute.await_count == 4


@pytest.mark.asyncio
async def test_core_user_mismatch_when_none_param():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(return_value=[_locked_row(usuario_id=USUARIO_ID_STR)])

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="old-hash",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id=None,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.USER_MISMATCH
    mock_uow.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_core_user_mismatch_when_invalid_param():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(return_value=[_locked_row(usuario_id=USUARIO_ID_STR)])

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="old-hash",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id="not-a-valid-uuid",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.USER_MISMATCH
    mock_uow.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_core_user_mismatch_when_distinct_uuids():
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(return_value=[_locked_row(usuario_id=USUARIO_ID_STR)])

    result = await rotate_refresh_token_core(
        mock_uow,
        old_token_hash="old-hash",
        new_token_hash="new-hash",
        cliente_id=CLIENTE_ID,
        usuario_id=str(OTHER_USUARIO_ID),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.USER_MISMATCH
    mock_uow.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_staging_regression_str_row_str_param_same_uuid():
    """
    Caso reproducido en staging (ROOTCAUSE-03):
    old_row[usuario_id] type=str, param_usuario_id type=str, mismo UUID.
    Antes: USER_MISMATCH falso; después: ROTATED.
    """
    mock_uow = MagicMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            [_locked_row(usuario_id=USUARIO_ID_STR)],
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
        usuario_id=USUARIO_ID_STR,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )

    assert result["outcome"] == RotateOutcome.ROTATED
    assert result["new_token_id"] == NEW_TOKEN_ID
