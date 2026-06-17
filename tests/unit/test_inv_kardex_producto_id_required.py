"""Tests P0 — kardex producto_id obligatorio y paginación."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import configure_exception_handlers
from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.shared.pagination.params import ErpPaginationParams
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.modules.inv.application.services import kardex_service
from app.modules.inv.presentation.endpoints_kardex import router
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
PRODUCTO_ID = uuid4()
USUARIO_ID = uuid4()


def _usuario():
    return UsuarioReadWithRoles(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENT_ID,
        nombre_usuario="kardex_test",
        fecha_creacion=datetime.utcnow(),
        permisos=["inv.movimiento.leer"],
    )


def _kardex_row():
    return {
        "movimiento_id": uuid4(),
        "movimiento_detalle_id": uuid4(),
        "empresa_id": EMPRESA_ID,
        "fecha_movimiento": datetime.utcnow(),
        "tipo_movimiento_id": uuid4(),
        "producto_id": PRODUCTO_ID,
        "almacen_origen_id": None,
        "almacen_destino_id": uuid4(),
        "cantidad_base": Decimal("1"),
        "costo_unitario": Decimal("0"),
        "moneda_id": uuid4(),
        "lote": None,
        "numero_serie": None,
        "observaciones": None,
    }


@pytest.fixture
def kardex_client():
    from app.api.deps import get_current_active_user

    app = FastAPI()
    configure_exception_handlers(app)
    app.include_router(router, prefix="/kardex")
    app.dependency_overrides[get_current_active_user] = lambda: _usuario()
    return TestClient(app)


def test_kardex_endpoint_without_producto_id_returns_422(kardex_client):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        resp = kardex_client.get("/kardex")
        assert resp.status_code == 422
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_kardex_legacy_with_producto_id():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with (
            patch(
                "app.modules.inv.application.services.kardex_service._validate_optional_filtros_kardex",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.kardex_service.list_kardex",
                new_callable=AsyncMock,
                return_value=[_kardex_row()],
            ) as mock_list,
            patch(
                "app.modules.inv.application.services.kardex_service.count_kardex",
                new_callable=AsyncMock,
            ) as mock_count,
        ):
            result = await kardex_service.list_kardex_servicio(
                client_id=CLIENT_ID,
                producto_id=PRODUCTO_ID,
            )
            assert isinstance(result, list)
            assert len(result) == 1
            mock_list.assert_awaited_once()
            mock_count.assert_not_awaited()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_list_kardex_paginated_envelope():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        pagination = ErpPaginationParams(page=2, limit=10)
        with (
            patch(
                "app.modules.inv.application.services.kardex_service._validate_optional_filtros_kardex",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.inv.application.services.kardex_service.count_kardex",
                new_callable=AsyncMock,
                return_value=25,
            ),
            patch(
                "app.modules.inv.application.services.kardex_service.list_kardex",
                new_callable=AsyncMock,
                return_value=[_kardex_row()],
            ) as mock_list,
        ):
            result = await kardex_service.list_kardex_servicio(
                client_id=CLIENT_ID,
                producto_id=PRODUCTO_ID,
                pagination=pagination,
            )
            assert isinstance(result, ErpPaginatedResponse)
            assert result.pagina_actual == 2
            assert result.total == 25
            assert mock_list.await_args.kwargs.get("pagination") == pagination
    finally:
        reset_current_empresa_id(token)
