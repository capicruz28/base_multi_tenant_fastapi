"""UoW-2 / Empresa Bootstrap V1 — ORG create empresa + cfg EMPRESA en TX única."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.codigo.enums import CodePolicy, ScopeType
from app.core.codigo.onboarding_seed import ONBOARDING_SEQUENCE_SEEDS
from app.core.codigo.platform_initial_policy import platform_initial_generation_policy
from app.core.exceptions import ServiceError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)
from app.modules.org.application.services import empresa_service
from app.modules.org.presentation.schemas import EmpresaCreate
from app.modules.tenant.application.services.empresa_bootstrap_service import (
    EmpresaBootstrapService,
)
from app.modules.tenant.application.services.tenant_bootstrap_orchestrator import (
    TenantBootstrapOrchestrator,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()

EMPRESA_CFG_ROW_COUNT = sum(
    1 for seed in ONBOARDING_SEQUENCE_SEEDS if seed.scope_type == ScopeType.EMPRESA
)


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


def _empresa_row() -> dict:
    return {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "EMP002",
        "razon_social": "ACME SA",
        "nombre_comercial": "ACME",
        "ruc": "20123456789",
        "es_activo": True,
    }


def _empresa_create() -> EmpresaCreate:
    return EmpresaCreate(
        codigo_empresa="EMP002",
        razon_social="ACME SA",
        nombre_comercial="ACME",
        ruc="20123456789",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_seeds_empresa_cfg_rows_via_ebs():
    """EMP002: org_empresa + N filas cfg scope EMPRESA vía insertar_secuencias_codigo."""
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    data = _empresa_create()
    row = _empresa_row()

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
                new_callable=AsyncMock,
                return_value=None,
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="EMP002",
                ) as mock_resolve:
                    with patch(
                        "app.modules.org.application.services.empresa_service.create_empresa",
                        new_callable=AsyncMock,
                        return_value=row,
                    ) as mock_create:
                        with patch.object(
                            CfgCodigoSecuenciaRepository,
                            "insert_secuencia",
                            new_callable=AsyncMock,
                        ) as mock_insert:
                            result = await empresa_service.create_empresa_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_resolve.assert_awaited_once_with(
        "org_empresa",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=None,
        manual_code="EMP002",
    )
    mock_create.assert_awaited_once()
    assert result.codigo_empresa == "EMP002"
    assert mock_insert.await_count == EMPRESA_CFG_ROW_COUNT
    empresa_calls = [
        c for c in mock_insert.await_args_list if c.kwargs["scope_type"] == ScopeType.EMPRESA
    ]
    assert len(empresa_calls) == EMPRESA_CFG_ROW_COUNT
    assert all(c.kwargs["empresa_id"] == EMPRESA_ID for c in empresa_calls)
    assert all(c.kwargs["session"] is session for c in mock_insert.await_args_list)
    tenant_calls = [
        c for c in mock_insert.await_args_list if c.kwargs["scope_type"] == ScopeType.TENANT
    ]
    assert len(tenant_calls) == 0
    for call in mock_insert.await_args_list:
        assert call.kwargs["generation_policy"] == platform_initial_generation_policy()
        assert call.kwargs["generation_policy"] == CodePolicy.AUTO_REQUIRED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_cfg_failure_propagates_and_skips_commit():
    """Fallo en insertar_secuencias_codigo → excepción; create ya invocado dentro de begin."""
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    data = _empresa_create()

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
                new_callable=AsyncMock,
                return_value=None,
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="EMP002",
                ):
                    with patch(
                        "app.modules.org.application.services.empresa_service.create_empresa",
                        new_callable=AsyncMock,
                        return_value=_empresa_row(),
                    ) as mock_create:
                        with patch.object(
                            EmpresaBootstrapService,
                            "insertar_secuencias_codigo",
                            new_callable=AsyncMock,
                            side_effect=ServiceError(
                                status_code=500,
                                detail="cfg seed failed",
                                internal_code="CFG_SEED_FAILED",
                            ),
                        ) as mock_bootstrap:
                            with pytest.raises(ServiceError):
                                await empresa_service.create_empresa_servicio(
                                    client_id=CLIENT_ID, data=data
                                )

    mock_create.assert_awaited_once()
    mock_bootstrap.assert_awaited_once_with(session, CLIENT_ID, EMPRESA_ID)
    session.begin.assert_called_once()
    begin_cm.__aexit__.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_uses_tenant_data_connection_for_shared_and_dedicated():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ) as mock_get_conn:
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
                new_callable=AsyncMock,
                return_value=None,
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="EMP002",
                ):
                    with patch(
                        "app.modules.org.application.services.empresa_service.create_empresa",
                        new_callable=AsyncMock,
                        return_value=_empresa_row(),
                    ):
                        with patch.object(
                            EmpresaBootstrapService,
                            "insertar_secuencias_codigo",
                            new_callable=AsyncMock,
                        ):
                            await empresa_service.create_empresa_servicio(
                                client_id=CLIENT_ID, data=_empresa_create()
                            )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)


@pytest.mark.unit
def test_onboarding_org_empresa_seed_ultimo_numero_one():
    """BR-BOOT-04: cfg TENANT org_empresa siembra ultimo_numero=1 post EMP001."""
    tenant = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.sequence_key == "org_empresa"]
    assert len(tenant) == 1
    assert tenant[0].ultimo_numero == 1
    assert tenant[0].numero_inicial == 1
    assert tenant[0].prefijo == "EMP"
    assert tenant[0].longitud_numero == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_onboarding_seed_codigo_secuencias_unchanged_for_emp001():
    """EMP001/onboarding: TBO sigue seed_cfg_tenant + EBS; ORG no usa ensure_empresa_inicial."""
    session = AsyncMock()
    cliente_id = uuid4()
    empresa_id = uuid4()

    with patch(
        "app.modules.tenant.application.services.tenant_bootstrap_orchestrator.seed_cfg_tenant",
        new_callable=AsyncMock,
    ) as mock_tenant_seed:
        with patch.object(
            EmpresaBootstrapService,
            "insertar_secuencias_codigo",
            new_callable=AsyncMock,
        ) as mock_ebs:
            await TenantBootstrapOrchestrator.run_seed_codigo_secuencias(
                session, cliente_id=cliente_id, empresa_id=empresa_id
            )

    mock_tenant_seed.assert_awaited_once_with(session, cliente_id)
    mock_ebs.assert_awaited_once_with(session, cliente_id, empresa_id)


@pytest.mark.unit
def test_org_create_does_not_call_ensure_empresa_inicial():
    import inspect

    source = inspect.getsource(empresa_service.create_empresa_servicio)
    assert "ensure_empresa_inicial" not in source
    assert "insertar_secuencias_codigo" in source
    assert "seed_cfg_empresa" not in source
