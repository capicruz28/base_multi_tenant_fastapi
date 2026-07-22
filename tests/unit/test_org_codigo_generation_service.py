"""Ola 1.1 — OrgCodigoGenerationService (infra ORG → CodigoGeneracionGateway)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.codigo.enums import GenerationOperation
from app.core.codigo.generation_context import GenerationContext
from app.core.codigo.generation_result import AllocationResult
from app.core.exceptions import ValidationError
from app.modules.org.application.services.org_codigo_generation_service import (
    OrgCodigoGenerationService,
    _normalize_manual_input,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


@pytest.mark.unit
class TestNormalizeManualInput:
    def test_none_returns_none(self):
        assert _normalize_manual_input(None) is None

    def test_empty_string_returns_none(self):
        assert _normalize_manual_input("") is None

    def test_whitespace_returns_none(self):
        assert _normalize_manual_input("   ") is None

    def test_strips_value(self):
        assert _normalize_manual_input("  CAR001  ") == "CAR001"


@pytest.mark.unit
class TestBuildContext:
    def test_build_tenant_context_without_manual(self):
        ctx = OrgCodigoGenerationService.build_tenant_context(CLIENT_ID)
        assert ctx.client_id == CLIENT_ID
        assert ctx.empresa_id is None
        assert ctx.manual_code is None
        assert ctx.operation == GenerationOperation.CREATE

    def test_build_tenant_context_with_manual(self):
        ctx = OrgCodigoGenerationService.build_tenant_context(
            CLIENT_ID, manual_code=" EMP001 "
        )
        assert ctx.manual_code == "EMP001"
        assert ctx.empresa_id is None

    def test_build_empresa_context(self):
        ctx = OrgCodigoGenerationService.build_empresa_context(
            CLIENT_ID, EMPRESA_ID, manual_code="SUC001"
        )
        assert ctx.client_id == CLIENT_ID
        assert ctx.empresa_id == EMPRESA_ID
        assert ctx.manual_code == "SUC001"

    def test_build_context_omits_blank_manual(self):
        ctx = OrgCodigoGenerationService.build_context(
            CLIENT_ID, empresa_id=EMPRESA_ID, manual_code="\t"
        )
        assert ctx.manual_code is None

    def test_build_context_import_operation(self):
        ctx = OrgCodigoGenerationService.build_context(
            CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="DEP001",
            operation=GenerationOperation.IMPORT,
        )
        assert ctx.operation == GenerationOperation.IMPORT


@pytest.mark.unit
class TestResolveCodigoForCreate:
    @pytest.mark.asyncio
    async def test_auto_allocate_returns_gateway_code(self):
        session = AsyncMock()
        with patch(
            "app.modules.org.application.services.org_codigo_generation_service.CodigoGeneracionGateway.allocate",
            new_callable=AsyncMock,
            return_value=AllocationResult(
                code="CAR001",
                sequence_key="org_cargo",
                consumed=True,
                ultimo_numero=1,
            ),
        ) as mock_allocate:
            code = await OrgCodigoGenerationService.resolve_codigo_for_create(
                "org_cargo",
                session=session,
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_ID,
            )

        assert code == "CAR001"
        mock_allocate.assert_awaited_once()
        call_args = mock_allocate.await_args
        assert call_args.args[0] == "org_cargo"
        assert call_args.args[1] == GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.CREATE,
            manual_code=None,
        )
        assert call_args.args[2] is session

    @pytest.mark.asyncio
    async def test_manual_code_passed_in_context(self):
        session = AsyncMock()
        with patch(
            "app.modules.org.application.services.org_codigo_generation_service.CodigoGeneracionGateway.allocate",
            new_callable=AsyncMock,
            return_value=AllocationResult(
                code="CAR999",
                sequence_key="org_cargo",
                consumed=False,
            ),
        ) as mock_allocate:
            code = await OrgCodigoGenerationService.resolve_codigo_for_create(
                "org_cargo",
                session=session,
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_ID,
                manual_code="CAR999",
            )

        assert code == "CAR999"
        ctx = mock_allocate.await_args.args[1]
        assert ctx.manual_code == "CAR999"

    @pytest.mark.asyncio
    async def test_omitted_manual_treated_as_auto(self):
        session = AsyncMock()
        with patch(
            "app.modules.org.application.services.org_codigo_generation_service.CodigoGeneracionGateway.allocate",
            new_callable=AsyncMock,
            return_value=AllocationResult(
                code="EMP002",
                sequence_key="org_empresa",
                consumed=True,
            ),
        ) as mock_allocate:
            await OrgCodigoGenerationService.resolve_codigo_for_create(
                "org_empresa",
                session=session,
                client_id=CLIENT_ID,
                manual_code="   ",
            )

        ctx = mock_allocate.await_args.args[1]
        assert ctx.manual_code is None
        assert ctx.empresa_id is None

    @pytest.mark.asyncio
    async def test_gateway_validation_error_propagates(self):
        session = AsyncMock()
        with patch(
            "app.modules.org.application.services.org_codigo_generation_service.CodigoGeneracionGateway.allocate",
            new_callable=AsyncMock,
            side_effect=ValidationError(
                detail="sequence_key desconocido: x",
                internal_code="SEQUENCE_KEY_UNKNOWN",
            ),
        ):
            with pytest.raises(ValidationError):
                await OrgCodigoGenerationService.resolve_codigo_for_create(
                    "x",
                    session=session,
                    client_id=CLIENT_ID,
                )

    @pytest.mark.asyncio
    async def test_does_not_reference_entity_services(self):
        import inspect

        source = inspect.getsource(OrgCodigoGenerationService)
        for token in (
            "cargo",
            "sucursal",
            "departamento",
            "centro_costo",
            "empresa_service",
        ):
            assert token not in source.lower()
