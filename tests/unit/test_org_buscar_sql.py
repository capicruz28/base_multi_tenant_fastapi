"""Tests P1 — buscar SQL ORG (sin filtro in-memory en services)."""
from __future__ import annotations

from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.org.application.services import (
    cargo_service,
    empresa_service,
    sucursal_service,
    departamento_service,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_mod,list_fn,list_servicio",
    [
        ("cargo_service", "list_cargos", cargo_service.list_cargos_servicio),
        ("sucursal_service", "list_sucursales", sucursal_service.list_sucursales_servicio),
        ("departamento_service", "list_departamentos", departamento_service.list_departamentos_servicio),
    ],
)
async def test_org_company_scoped_buscar_forwarded(service_mod, list_fn, list_servicio):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        patch_target = f"app.modules.org.application.services.{service_mod}.{list_fn}"
        with patch(patch_target, new_callable=AsyncMock, return_value=[]) as mock_list:
            await list_servicio(client_id=CLIENT_ID, buscar="adm")
        assert mock_list.await_args.kwargs.get("buscar") == "adm"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
async def test_empresa_buscar_forwarded_to_query():
    with patch(
        "app.modules.org.application.services.empresa_service.list_empresas",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_list:
        await empresa_service.list_empresas_servicio(client_id=CLIENT_ID, buscar="acme")
    mock_list.assert_awaited_once_with(
        client_id=CLIENT_ID,
        solo_activos=True,
        buscar="acme",
    )
