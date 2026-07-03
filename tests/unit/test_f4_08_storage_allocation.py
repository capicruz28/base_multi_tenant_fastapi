"""PR-F4-08 — tests unitarios StorageAllocationService."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.tenant.application.services.storage_allocation_service import (
    StorageAllocationService,
)
from app.modules.tenant.application.services.storage_allocation_types import (
    StorageAllocationRequest,
    parse_storage_allocation_marker,
    serialize_storage_allocation_marker,
)


@pytest.mark.unit
def test_f4_08_storage_allocation_deterministic(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "PROVISIONING_DDL_SERVER", "sql-staging.local")

    cliente_id = uuid4()
    service = StorageAllocationService()
    result = service.allocate(
        StorageAllocationRequest(cliente_id=cliente_id, codigo_cliente="ACME001"),
    )
    assert result.servidor == "sql-staging.local"
    assert result.database_name == "erp_acme001"
    assert result.app_login_name == "erpapp_acme001"


@pytest.mark.unit
def test_f4_08_storage_allocation_marker_roundtrip():
    from app.modules.tenant.application.services.storage_allocation_types import (
        StorageAllocationResult,
    )

    result = StorageAllocationResult(
        servidor="srv1",
        database_name="erp_demo",
        app_login_name="erpapp_demo",
    )
    marker = serialize_storage_allocation_marker(result)
    parsed = parse_storage_allocation_marker(marker)
    assert parsed == result
