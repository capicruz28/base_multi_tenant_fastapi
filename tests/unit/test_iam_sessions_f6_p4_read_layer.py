"""F6-P4 — Session Store read layer: gateways + enriquecimiento sin JOIN Data Plane."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.auth.application.services.active_sessions_read_service import (
    ActiveSessionsReadService,
)
from app.modules.auth.application.services.session_read_enrichment_service import (
    SessionReadEnrichmentService,
)
from app.shared.pagination.params import ErpPaginationParams

_CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
_USUARIO_ID = uuid4()
_EMPRESA_ID = uuid4()
_TOKEN_ID = uuid4()
_NOW = datetime(2026, 6, 18, 12, 0, 0)
_READ = "app.modules.auth.application.services.active_sessions_read_service"
_ENRICH = "app.modules.auth.application.services.session_read_enrichment_service"
_FEATURE = f"{_READ}.is_session_v2_enabled"


def _session_only_row(**overrides) -> dict:
    base = {
        "token_id": _TOKEN_ID,
        "session_id": uuid4(),
        "usuario_id": _USUARIO_ID,
        "cliente_id": _CLIENTE_ID,
        "empresa_id": _EMPRESA_ID,
        "created_at": _NOW,
        "last_used_at": _NOW,
        "expires_at": _NOW + timedelta(days=7),
        "device_name": "Chrome",
        "device_id": "dev-1",
        "ip_address": "10.0.0.1",
        "user_agent": "Mozilla/5.0",
        "client_type": "web",
    }
    base.update(overrides)
    return base


def _enriched_row(**overrides) -> dict:
    return _session_only_row(
        nombre_usuario="admin",
        nombre="Admin",
        apellido="User",
        empresa_nombre="ACME SA",
        **overrides,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_p4_admin_list_enriches_via_gateway():
    session_row = _session_only_row()
    with (
        patch(_FEATURE, return_value=False),
        patch(
            f"{_ENRICH}.SessionReadEnrichmentService.resolve_search_user_ids",
            AsyncMock(return_value=None),
        ),
        patch(
            f"{_READ}.execute_query",
            AsyncMock(return_value=[session_row]),
        ),
        patch(
            f"{_ENRICH}.IdentityGateway.get_users_by_ids",
            AsyncMock(
                return_value={
                    _USUARIO_ID: {
                        "nombre_usuario": "admin",
                        "nombre": "Admin",
                        "apellido": "User",
                    }
                }
            ),
        ),
        patch(
            f"{_ENRICH}.OrgReadGateway.get_empresa_display_names_by_ids",
            AsyncMock(return_value={_EMPRESA_ID: "ACME SA"}),
        ),
    ):
        result = await ActiveSessionsReadService.list_admin_sessions(
            _CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
        )

    assert isinstance(result, list)
    assert result[0].nombre_usuario == "admin"
    assert result[0].empresa_nombre == "ACME SA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_p4_search_resolves_user_ids_via_identity_gateway():
    search_user_ids = [_USUARIO_ID]
    with (
        patch(_FEATURE, return_value=False),
        patch(
            f"{_ENRICH}.SessionReadEnrichmentService.resolve_search_user_ids",
            AsyncMock(return_value=search_user_ids),
        ) as mock_search,
        patch(
            f"{_READ}.execute_query",
            AsyncMock(return_value=[_enriched_row()]),
        ),
        patch(
            f"{_ENRICH}.SessionReadEnrichmentService.enrich_admin_rows",
            AsyncMock(side_effect=lambda _cid, rows: rows),
        ),
    ):
        await ActiveSessionsReadService.list_admin_sessions(
            _CLIENTE_ID,
            pagination=ErpPaginationParams(page=None, limit=50),
            search="admin",
        )

    mock_search.assert_awaited_once_with(_CLIENTE_ID, "admin")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f6_p4_enrichment_service_merges_identity_and_org():
    row = _session_only_row()
    with (
        patch(
            f"{_ENRICH}.IdentityGateway.get_users_by_ids",
            AsyncMock(
                return_value={
                    _USUARIO_ID: {
                        "nombre_usuario": "bob",
                        "nombre": "Bob",
                        "apellido": "Lee",
                    }
                }
            ),
        ),
        patch(
            f"{_ENRICH}.OrgReadGateway.get_empresa_display_names_by_ids",
            AsyncMock(return_value={_EMPRESA_ID: "Empresa X"}),
        ),
    ):
        enriched = await SessionReadEnrichmentService.enrich_admin_rows(
            _CLIENTE_ID,
            [row],
        )

    assert enriched[0]["nombre_usuario"] == "bob"
    assert enriched[0]["empresa_nombre"] == "Empresa X"


@pytest.mark.unit
def test_f6_p4_no_data_plane_joins_in_read_service_source():
    from pathlib import Path

    source = Path(
        "app/modules/auth/application/services/active_sessions_read_service.py"
    ).read_text(encoding="utf-8")
    assert "UsuarioTable" not in source
    assert "OrgEmpresaTable" not in source
