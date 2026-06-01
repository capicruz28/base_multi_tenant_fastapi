"""Unit tests — minimal ERP tenant bootstrap."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    CODIGO_EMPRESA_INICIAL,
    MinimalErpTenantBootstrapService,
    _normalize_ruc,
)
from app.modules.tenant.presentation.schemas import ClienteCreate


def _cliente_data(**kwargs) -> ClienteCreate:
    base = {
        "codigo_cliente": "T001",
        "subdominio": "testerp",
        "razon_social": "Test ERP SA",
        "contacto_email": "a@test.local",
        "ruc": "20123456789",
    }
    base.update(kwargs)
    return ClienteCreate(**base)


@pytest.mark.asyncio
async def test_ensure_empresa_inicial_idempotent_when_exists():
    session = AsyncMock()
    cid = uuid4()
    eid = uuid4()
    session.execute = AsyncMock(
        return_value=MagicMock(
            fetchone=MagicMock(return_value=(eid, CODIGO_EMPRESA_INICIAL, "Test"))
        )
    )
    out = await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
        session, cliente_id=cid, cliente_data=_cliente_data()
    )
    assert out["created"] is False
    assert out["codigo_empresa"] == CODIGO_EMPRESA_INICIAL


@pytest.mark.asyncio
async def test_ensure_empresa_inicial_creates_when_empty():
    session = AsyncMock()
    cid = uuid4()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(),
        ]
    )
    out = await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
        session, cliente_id=cid, cliente_data=_cliente_data()
    )
    assert out["created"] is True
    assert out["codigo_empresa"] == CODIGO_EMPRESA_INICIAL


def test_normalize_ruc_from_cliente():
    cid = uuid4()
    ruc = _normalize_ruc(_cliente_data(ruc="20555123456"), cid)
    assert len(ruc) == 11
    assert ruc.isdigit()


def test_normalize_ruc_synthetic_when_missing():
    cid = uuid4()
    ruc = _normalize_ruc(_cliente_data(ruc=None), cid)
    assert len(ruc) == 11
