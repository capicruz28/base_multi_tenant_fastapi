"""Regression: eliminar_cliente must await execute_update (soft-delete)."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.tenant.application.services.cliente_service import ClienteService


def _cliente_stub(cliente_id: UUID) -> MagicMock:
    stub = MagicMock()
    stub.cliente_id = cliente_id
    stub.estado_suscripcion = "activo"
    return stub


@pytest.mark.asyncio
async def test_eliminar_cliente_awaits_execute_update():
    cliente_id = uuid4()
    with (
        patch.object(
            ClienteService,
            "obtener_cliente_por_id",
            new_callable=AsyncMock,
            return_value=_cliente_stub(cliente_id),
        ),
        patch(
            "app.modules.tenant.application.services.cliente_service.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 1},
        ) as mock_update,
        patch(
            "app.core.config.settings",
            MagicMock(SUPERADMIN_CLIENTE_ID=str(uuid4())),
        ),
    ):
        result = await ClienteService.eliminar_cliente(cliente_id)

    assert result is True
    mock_update.assert_awaited_once()
    call = mock_update.await_args
    assert "es_activo = 0" in call[0][0]
    assert "estado_suscripcion = 'cancelado'" in call[0][0]


@pytest.mark.asyncio
async def test_eliminar_cliente_not_found_raises_404():
    cliente_id = uuid4()
    with patch.object(
        ClienteService,
        "obtener_cliente_por_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(NotFoundError) as exc:
            await ClienteService.eliminar_cliente(cliente_id)

    assert exc.value.status_code == 404
    assert exc.value.internal_code == "CLIENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_eliminar_cliente_system_raises_400():
    system_id = UUID("00000000-0000-0000-0000-000000000001")
    with (
        patch.object(
            ClienteService,
            "obtener_cliente_por_id",
            new_callable=AsyncMock,
            return_value=_cliente_stub(system_id),
        ),
        patch(
            "app.core.config.settings",
            MagicMock(SUPERADMIN_CLIENTE_ID=str(system_id)),
        ),
    ):
        with pytest.raises(ValidationError) as exc:
            await ClienteService.eliminar_cliente(system_id)

    assert exc.value.status_code == 400
    assert exc.value.internal_code == "CANNOT_DELETE_SYSTEM_CLIENT"
