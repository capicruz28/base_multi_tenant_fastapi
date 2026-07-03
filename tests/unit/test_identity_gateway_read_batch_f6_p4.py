"""F6-P4 — Identity Gateway batch read methods."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.core.identity.identity_scope import IdentityScope

_CLIENTE_ID = uuid4()
_USUARIO_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_users_by_ids_row_scoped():
    ctx = IdentityContext(cliente_id=_CLIENTE_ID)
    with (
        patch.object(
            IdentityGateway,
            "resolve_identity_scope",
            return_value=IdentityScope.ROW_SCOPED,
        ),
        patch(
            "app.core.identity.identity_gateway.execute_identity_query",
            AsyncMock(
                return_value=[
                    {
                        "usuario_id": _USUARIO_ID,
                        "nombre_usuario": "alice",
                        "nombre": "Alice",
                        "apellido": "A",
                    }
                ]
            ),
        ),
    ):
        result = await IdentityGateway.get_users_by_ids(ctx, [_USUARIO_ID])

    assert result[_USUARIO_ID]["nombre_usuario"] == "alice"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_user_ids_engine_scoped():
    ctx = IdentityContext(cliente_id=_CLIENTE_ID)
    uid2 = uuid4()
    with (
        patch.object(
            IdentityGateway,
            "resolve_identity_scope",
            return_value=IdentityScope.ENGINE_SCOPED,
        ),
        patch(
            "app.core.identity.identity_gateway.execute_identity_query",
            AsyncMock(
                return_value=[
                    {"usuario_id": _USUARIO_ID},
                    {"usuario_id": uid2},
                ]
            ),
        ),
    ):
        ids = await IdentityGateway.search_user_ids(ctx, "ali")

    assert ids == [_USUARIO_ID, uid2]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_users_by_ids_empty_input():
    ctx = IdentityContext(cliente_id=_CLIENTE_ID)
    result = await IdentityGateway.get_users_by_ids(ctx, [])
    assert result == {}
