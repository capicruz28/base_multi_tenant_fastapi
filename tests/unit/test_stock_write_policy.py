"""
Tests unitarios — INV-P0-002: política de escritura directa inv_stock (S-01 a S-10).
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import stock_service
from app.modules.inv.application.services.inv_stock_write_policy import (
    STOCK_DERIVED_WRITE_FORBIDDEN_CODE,
    assert_stock_direct_write_allowed,
    is_stock_direct_write_allowed,
)
from app.modules.inv.presentation.schemas import StockCreate, StockUpdate

_POLICY_MODULE = "app.modules.inv.application.services.inv_stock_write_policy.settings"
_STOCK_SVC = "app.modules.inv.application.services.stock_service"

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
STOCK_ID = uuid4()
PRODUCTO_ID = uuid4()
ALMACEN_ID = uuid4()
MONEDA_ID = uuid4()


def _stock_create() -> StockCreate:
    return StockCreate(
        empresa_id=EMPRESA_ID,
        producto_id=PRODUCTO_ID,
        almacen_id=ALMACEN_ID,
        moneda_id=MONEDA_ID,
    )


def _stock_row() -> dict:
    return {
        "stock_id": STOCK_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "producto_id": PRODUCTO_ID,
        "almacen_id": ALMACEN_ID,
        "cantidad_actual": Decimal("10"),
        "costo_promedio": Decimal("5"),
        "moneda_id": MONEDA_ID,
    }


@pytest.mark.unit
def test_s01_is_stock_direct_write_allowed_false_when_flag_off():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
        assert is_stock_direct_write_allowed() is False


@pytest.mark.unit
def test_s02_is_stock_direct_write_allowed_true_when_flag_on():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = True
        assert is_stock_direct_write_allowed() is True


@pytest.mark.unit
def test_s03_assert_stock_direct_write_allowed_raises_conflict_when_flag_off():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
        with pytest.raises(ConflictError) as exc:
            assert_stock_direct_write_allowed()
        assert exc.value.status_code == 409
        assert exc.value.internal_code == STOCK_DERIVED_WRITE_FORBIDDEN_CODE
        assert "movimientos de inventario procesados" in exc.value.detail


@pytest.mark.unit
def test_s04_assert_stock_direct_write_allowed_noop_when_flag_on():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = True
        assert_stock_direct_write_allowed()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s05_create_stock_servicio_blocked_without_downstream_calls():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
        with (
            patch(f"{_STOCK_SVC}.create_stock", new_callable=AsyncMock) as mock_create,
            patch(f"{_STOCK_SVC}.enforce_body_empresa_matches_session") as mock_enforce,
            patch(f"{_STOCK_SVC}.ensure_empresa_in_tenant", new_callable=AsyncMock) as mock_ensure,
            patch(
                f"{_STOCK_SVC}._validate_producto_almacen_empresa",
                new_callable=AsyncMock,
            ) as mock_validate,
            patch(f"{_STOCK_SVC}.get_producto_by_id", new_callable=AsyncMock) as mock_prod,
            patch(f"{_STOCK_SVC}.get_almacen_by_id", new_callable=AsyncMock) as mock_alm,
        ):
            with pytest.raises(ConflictError) as exc:
                await stock_service.create_stock_servicio(
                    client_id=CLIENT_ID,
                    data=_stock_create(),
                )

            assert exc.value.internal_code == STOCK_DERIVED_WRITE_FORBIDDEN_CODE
            mock_create.assert_not_called()
            mock_enforce.assert_not_called()
            mock_ensure.assert_not_called()
            mock_validate.assert_not_called()
            mock_prod.assert_not_called()
            mock_alm.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s06_update_stock_servicio_blocked_without_downstream_calls():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
        with (
            patch(f"{_STOCK_SVC}.update_stock", new_callable=AsyncMock) as mock_update,
            patch(f"{_STOCK_SVC}.get_stock_by_id", new_callable=AsyncMock) as mock_get,
            patch(f"{_STOCK_SVC}.require_session_empresa_id") as mock_empresa,
        ):
            with pytest.raises(ConflictError) as exc:
                await stock_service.update_stock_servicio(
                    client_id=CLIENT_ID,
                    stock_id=STOCK_ID,
                    data=StockUpdate(cantidad_actual=Decimal("99")),
                )

            assert exc.value.internal_code == STOCK_DERIVED_WRITE_FORBIDDEN_CODE
            mock_update.assert_not_called()
            mock_get.assert_not_called()
            mock_empresa.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s07_create_stock_servicio_allowed_delegates_to_create_stock_when_flag_on():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = True
        row = _stock_row()
        with (
            patch(f"{_STOCK_SVC}.create_stock", new_callable=AsyncMock, return_value=row) as mock_create,
            patch(
                f"{_STOCK_SVC}.enforce_body_empresa_matches_session",
                return_value=EMPRESA_ID,
            ),
            patch(f"{_STOCK_SVC}.ensure_empresa_in_tenant", new_callable=AsyncMock),
            patch(f"{_STOCK_SVC}._validate_producto_almacen_empresa", new_callable=AsyncMock),
        ):
            result = await stock_service.create_stock_servicio(
                client_id=CLIENT_ID,
                data=_stock_create(),
            )

            mock_create.assert_called_once()
            assert result.stock_id == STOCK_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s08_update_stock_servicio_allowed_delegates_to_update_stock_when_flag_on():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = True
        row = _stock_row()
        updated = {**row, "cantidad_actual": Decimal("20")}
        with (
            patch(f"{_STOCK_SVC}.update_stock", new_callable=AsyncMock, return_value=updated) as mock_update,
            patch(f"{_STOCK_SVC}.get_stock_by_id", new_callable=AsyncMock, return_value=row),
            patch(f"{_STOCK_SVC}.require_session_empresa_id", return_value=EMPRESA_ID),
        ):
            result = await stock_service.update_stock_servicio(
                client_id=CLIENT_ID,
                stock_id=STOCK_ID,
                data=StockUpdate(cantidad_actual=Decimal("20")),
            )

            mock_update.assert_called_once()
            assert result.cantidad_actual == Decimal("20")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s09_update_stock_minimo_only_blocked_option_a():
    with patch(_POLICY_MODULE) as mock_settings:
        mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
        with (
            patch(f"{_STOCK_SVC}.update_stock", new_callable=AsyncMock) as mock_update,
            patch(f"{_STOCK_SVC}.get_stock_by_id", new_callable=AsyncMock) as mock_get,
            patch(f"{_STOCK_SVC}.require_session_empresa_id") as mock_empresa,
        ):
            with pytest.raises(ConflictError) as exc:
                await stock_service.update_stock_servicio(
                    client_id=CLIENT_ID,
                    stock_id=STOCK_ID,
                    data=StockUpdate(stock_minimo=Decimal("5")),
                )

            assert exc.value.internal_code == STOCK_DERIVED_WRITE_FORBIDDEN_CODE
            mock_update.assert_not_called()
            mock_get.assert_not_called()
            mock_empresa.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_s10_list_stocks_servicio_unaffected_when_flag_off():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(_POLICY_MODULE) as mock_settings:
            mock_settings.INV_ALLOW_STOCK_DIRECT_WRITE = False
            with patch(
                f"{_STOCK_SVC}.list_stocks",
                new_callable=AsyncMock,
                return_value=[_stock_row()],
            ) as mock_list:
                result = await stock_service.list_stocks_servicio(client_id=CLIENT_ID)

                mock_list.assert_called_once_with(
                    client_id=CLIENT_ID,
                    empresa_id=EMPRESA_ID,
                    producto_id=None,
                    almacen_id=None,
                )
                assert len(result) == 1
                assert result[0].stock_id == STOCK_ID
    finally:
        reset_current_empresa_id(token)
