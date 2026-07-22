"""T-D01 — get_cfg_session_client_id impersonación-safe."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Request

from app.modules.cfg.presentation.cfg_deps import get_cfg_session_client_id
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

TENANT_ID = uuid4()
SYSTEM_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_td01_impersonacion_usa_cliente_jwt_tenant():
    request = MagicMock(spec=Request)
    request.state.cliente_id = None
    request.scope = {"route": MagicMock(path="/cfg/secuencias")}
    request.url.path = "/cfg/secuencias"
    request.method = "GET"

    payload = {
        "cliente_id": str(TENANT_ID),
        "is_impersonation": True,
    }
    current_user = MagicMock(spec=UsuarioReadWithRoles)
    current_user.cliente_id = SYSTEM_ID  # operador SYSTEM

    with patch(
        "app.modules.cfg.presentation.cfg_deps.require_session_cliente_id",
        return_value=TENANT_ID,
    ) as mock_req:
        result = await get_cfg_session_client_id(
            request=request,
            payload=payload,
            current_user=current_user,
        )

    assert result == TENANT_ID
    mock_req.assert_called_once()
    assert mock_req.call_args.kwargs["user_cliente_id"] == SYSTEM_ID
    assert mock_req.call_args.kwargs["payload"] is payload
