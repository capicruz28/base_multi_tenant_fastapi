"""F17 Ola 0 — pruebas unitarias del motor de generación de códigos."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.codigo.enums import (
    CodePolicy,
    GenerationOperation,
    ScopeType,
    SequenceFamily,
    StoreType,
)
from app.core.codigo.formatter.code_formatter import CodeFormatter
from app.core.codigo.gateway.codigo_generacion_gateway import CodigoGeneracionGateway
from app.core.codigo.generation_context import GenerationContext
from app.core.codigo.onboarding_seed import ONBOARDING_SEQUENCE_SEEDS, SECUENCIAS_CODIGO
from app.core.codigo.parser.code_parser import CodeParser
from app.core.codigo.resolvers.policy_resolver import PolicyResolver
from app.core.codigo.resolvers.scope_resolver import ScopeResolver
from app.core.codigo.scope_fingerprint import compute_scope_fingerprint
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.codigo.services.counter_alignment_service import CounterAlignmentService
from app.core.codigo.validator.code_validator import CodeValidator
from app.core.exceptions import NotFoundError, ValidationError

CLIENT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
EMPRESA_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
ALMACEN_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
PV_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
SERIE_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")


@pytest.mark.unit
class TestSequenceCatalog:
    def test_count_63_entries(self):
        assert SequenceCatalog.count() == 63

    def test_no_duplicate_keys(self):
        keys = SequenceCatalog.all_keys()
        assert len(keys) == len(set(keys))

    def test_inv_categoria_producto_present(self):
        defn = SequenceCatalog.get("inv_categoria_producto")
        assert defn.policy == CodePolicy.AUTO_DEFAULT
        assert defn.sequence_family == SequenceFamily.F1

    def test_excludes_manual_only_entities(self):
        assert not SequenceCatalog.contains("dms_documento")
        assert not SequenceCatalog.contains("invbill_serie_comprobante")

    def test_fiscal_entries_use_fiscal_store(self):
        invbill = SequenceCatalog.get("invbill_comprobante")
        assert invbill.store_type == StoreType.FISCAL
        assert invbill.scope_type == ScopeType.SERIE_FISCAL


@pytest.mark.unit
class TestOnboardingSeed:
    def test_inc02_inv_categoria_producto(self):
        keys = [s.sequence_key for s in ONBOARDING_SEQUENCE_SEEDS]
        assert "inv_categoria_producto" in keys
        assert "inv_categoria" not in keys

    def test_inc01_empresa_scope_for_empresa_entries(self):
        tenant = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.scope_type == ScopeType.TENANT]
        empresa = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.scope_type == ScopeType.EMPRESA]
        assert len(tenant) == 1
        assert tenant[0].sequence_key == "org_empresa"
        # F17D: la cantidad EMPRESA se deriva del catálogo (CFG scope EMPRESA), sin hardcode.
        expected_empresa = sum(
            1
            for d in SequenceCatalog.all_definitions()
            if d.store_type == StoreType.CFG and d.scope_type == ScopeType.EMPRESA
        )
        assert len(empresa) == expected_empresa

    def test_secuencias_codigo_compat_tuple(self):
        assert len(SECUENCIAS_CODIGO) == len(ONBOARDING_SEQUENCE_SEEDS)


@pytest.mark.unit
class TestScopeFingerprint:
    def test_tenant_fingerprint_stable(self):
        fp1 = compute_scope_fingerprint(ScopeType.TENANT)
        fp2 = compute_scope_fingerprint(ScopeType.TENANT)
        assert fp1 == fp2
        assert len(fp1) == 64

    def test_empresa_differs_from_tenant(self):
        fp_t = compute_scope_fingerprint(ScopeType.TENANT)
        fp_e = compute_scope_fingerprint(ScopeType.EMPRESA, empresa_id=EMPRESA_ID)
        assert fp_t != fp_e


@pytest.mark.unit
class TestPolicyResolver:
    def test_auto_required_rejects_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="MOV000001",
        )
        mode = PolicyResolver.resolve(CodePolicy.AUTO_REQUIRED, ctx)
        from app.core.codigo.enums import PolicyMode

        assert mode.name == "REJECT_MANUAL"

    def test_auto_default_accepts_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="CLI999",
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_DEFAULT, ctx) == PolicyMode.ACCEPT_MANUAL

    def test_auto_default_autogenerate_when_empty(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_DEFAULT, ctx) == PolicyMode.AUTO_GENERATE

    def test_auto_required_autogenerate_when_empty(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_REQUIRED, ctx) == PolicyMode.AUTO_GENERATE

    def test_auto_required_import_without_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.IMPORT,
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_REQUIRED, ctx) == PolicyMode.IMPORT_HISTORICAL

    def test_auto_required_import_with_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.IMPORT,
            manual_code="MOV000001",
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_REQUIRED, ctx) == PolicyMode.IMPORT_HISTORICAL

    def test_auto_default_import_with_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.IMPORT,
            manual_code="CLI999",
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.AUTO_DEFAULT, ctx) == PolicyMode.IMPORT_HISTORICAL

    def test_manual_only_rejects_without_manual(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.MANUAL_ONLY, ctx) == PolicyMode.REJECT_MANUAL

    def test_manual_only_accepts_with_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="CAR001",
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.MANUAL_ONLY, ctx) == PolicyMode.ACCEPT_MANUAL

    def test_manual_only_create_without_manual_rejects(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.CREATE,
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.MANUAL_ONLY, ctx) == PolicyMode.REJECT_MANUAL

    def test_manual_only_import_with_manual_accepts(self):
        """MANUAL_ONLY no tiene rama IMPORT_HISTORICAL; manual presente → ACCEPT_MANUAL."""
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.IMPORT,
            manual_code="CAR001",
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.MANUAL_ONLY, ctx) == PolicyMode.ACCEPT_MANUAL

    def test_manual_only_import_without_manual_rejects(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            operation=GenerationOperation.IMPORT,
        )
        from app.core.codigo.enums import PolicyMode

        assert PolicyResolver.resolve(CodePolicy.MANUAL_ONLY, ctx) == PolicyMode.REJECT_MANUAL

    def test_unsupported_policy_raises(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        with pytest.raises(ValueError, match="Política no soportada"):
            PolicyResolver.resolve(CodePolicy.EXTERNAL, ctx)


@pytest.mark.unit
class TestScopeResolver:
    def test_empresa_requires_empresa_id(self):
        defn = SequenceCatalog.get("inv_movimiento")
        ctx = GenerationContext(client_id=CLIENT_ID)
        with pytest.raises(ValidationError):
            ScopeResolver.resolve(defn, ctx)

    def test_almacen_requires_almacen_id(self):
        defn = SequenceCatalog.get("wms_tarea")
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        with pytest.raises(ValidationError):
            ScopeResolver.resolve(defn, ctx)

    def test_punto_venta_scope(self):
        defn = SequenceCatalog.get("pos_turno_caja")
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            punto_venta_id=PV_ID,
        )
        key = ScopeResolver.resolve(defn, ctx)
        assert key.scope_type == ScopeType.PUNTO_VENTA
        assert key.punto_venta_id == PV_ID


@pytest.mark.unit
class TestCodeFormatter:
    def test_standard_format(self):
        defn = SequenceCatalog.get("sls_cliente")
        code = CodeFormatter.format(defn, 21, prefijo="CLI", separador="", padding=4)
        assert code == "CLI0021"

    def test_fiscal_8_digits(self):
        defn = SequenceCatalog.get("invbill_comprobante")
        code = CodeFormatter.format(defn, 42)
        assert code == "00000042"


@pytest.mark.unit
class TestCodeParser:
    def test_prefix_num_parse(self):
        defn = SequenceCatalog.get("sls_cliente")
        result = CodeParser.parse(defn, "CLI999", prefijo="CLI")
        assert result.parseable
        assert result.numeric_part == 999

    def test_high_water_scenario_cli999(self):
        defn = SequenceCatalog.get("sls_cliente")
        result = CodeParser.parse(defn, "CLI999", prefijo="CLI")
        assert result.numeric_part == 999

    def test_non_parseable_alpha(self):
        defn = SequenceCatalog.get("sls_cliente")
        result = CodeParser.parse(defn, "X-ALPHA", prefijo="CLI")
        assert not result.parseable


@pytest.mark.unit
class TestCodeValidator:
    def test_valid_master(self):
        defn = SequenceCatalog.get("org_sucursal")
        CodeValidator.validate(defn, "SUC001")

    def test_rejects_too_long(self):
        defn = SequenceCatalog.get("org_sucursal")
        with pytest.raises(ValidationError):
            CodeValidator.validate(defn, "X" * 25)

    def test_fiscal_digits_only(self):
        defn = SequenceCatalog.get("invbill_comprobante")
        CodeValidator.validate(defn, "00000001")
        with pytest.raises(ValidationError):
            CodeValidator.validate(defn, "ABC")


@pytest.mark.unit
class TestCfgSequenceStore:
    @pytest.mark.asyncio
    async def test_increment_and_get(self):
        from app.core.codigo.coordinator.allocation_coordinator import AllocationCoordinator
        from app.core.codigo.scope_key import ScopeKey

        defn = SequenceCatalog.get("sls_cliente")
        scope_key = ScopeKey(
            sequence_key="sls_cliente",
            scope_type=ScopeType.EMPRESA,
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
        )
        session = AsyncMock()

        with patch(
            "app.core.codigo.stores.cfg_sequence_store.CfgSequenceStore.increment_and_get",
            new_callable=AsyncMock,
            return_value=(
                MagicMock(
                    prefijo="CLI",
                    separador="",
                    longitud_numero=4,
                    ultimo_numero=1,
                ),
                1,
            ),
        ):
            result = await AllocationCoordinator.allocate_next(session, defn, scope_key)
        assert result.consumed is True
        assert result.code == "CLI0001"


@pytest.mark.unit
class TestFiscalSeriesStore:
    @pytest.mark.asyncio
    async def test_increment_fiscal(self):
        from app.core.codigo.stores.fiscal_series_store import FiscalSeriesRow, FiscalSeriesStore

        session = AsyncMock()
        row = {
            "serie_id": str(SERIE_ID),
            "cliente_id": str(CLIENT_ID),
            "empresa_id": str(EMPRESA_ID),
            "numero_actual": 5,
            "numero_inicial": 1,
            "numero_final": None,
            "es_activo": True,
        }

        with patch.object(
            FiscalSeriesStore,
            "get_by_serie_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.side_effect = [
                FiscalSeriesRow.from_dict(row),
                FiscalSeriesRow.from_dict({**row, "numero_actual": 6}),
            ]
            session.execute = AsyncMock()
            _updated, numero = await FiscalSeriesStore.increment_and_get(
                session,
                client_id=CLIENT_ID,
                serie_id=SERIE_ID,
                empresa_id=EMPRESA_ID,
            )
        assert numero == 6


@pytest.mark.unit
class TestCounterAlignment:
    @pytest.mark.asyncio
    async def test_align_on_manual_high_water(self):
        defn = SequenceCatalog.get("sls_cliente")
        from app.core.codigo.scope_key import ScopeKey

        scope_key = ScopeKey(
            sequence_key="sls_cliente",
            scope_type=ScopeType.EMPRESA,
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
        )
        session = AsyncMock()
        with patch(
            "app.core.codigo.services.counter_alignment_service.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=MagicMock(ultimo_numero=20),
        ), patch(
            "app.core.codigo.services.counter_alignment_service.CfgSequenceStore.align_counter",
            new_callable=AsyncMock,
            return_value=999,
        ) as mock_align:
            result = await CounterAlignmentService.maybe_align(
                session, defn, scope_key, "CLI999", prefijo="CLI"
            )
        assert result == 999
        mock_align.assert_awaited_once()


@pytest.mark.unit
class TestPreviewReader:
    @pytest.mark.asyncio
    async def test_preview_not_allowed_for_auto_required(self):
        defn = SequenceCatalog.get("inv_movimiento")
        from app.core.codigo.scope_key import ScopeKey
        from app.core.codigo.services.preview_reader import PreviewReader

        scope_key = ScopeKey(
            sequence_key="inv_movimiento",
            scope_type=ScopeType.EMPRESA,
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
        )
        session = AsyncMock()
        with pytest.raises(ValidationError):
            await PreviewReader.preview(session, defn, scope_key)


@pytest.mark.unit
class TestCodigoGeneracionGateway:
    @staticmethod
    def _cfg_row(generation_policy: CodePolicy):
        return MagicMock(generation_policy=generation_policy, es_activo=True)

    @pytest.mark.asyncio
    async def test_allocate_auto_required(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.AUTO_REQUIRED),
        ):
            with patch(
                "app.core.codigo.gateway.codigo_generacion_gateway.AllocationCoordinator.allocate_next",
                new_callable=AsyncMock,
            ) as mock_alloc:
                from app.core.codigo.generation_result import AllocationResult

                mock_alloc.return_value = AllocationResult(
                    code="MOV000001",
                    sequence_key="inv_movimiento",
                    consumed=True,
                    ultimo_numero=1,
                )
                result = await CodigoGeneracionGateway.allocate(
                    "inv_movimiento", ctx, session
                )
        assert result.code == "MOV000001"
        assert result.consumed is True

    @pytest.mark.asyncio
    async def test_allocate_manual_auto_default(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="CLI999",
        )
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.AUTO_DEFAULT),
        ):
            with patch(
                "app.core.codigo.gateway.codigo_generacion_gateway.CounterAlignmentService.maybe_align",
                new_callable=AsyncMock,
                return_value=999,
            ):
                result = await CodigoGeneracionGateway.allocate(
                    "sls_cliente", ctx, session
                )
        assert result.code == "CLI999"
        assert result.consumed is False

    @pytest.mark.asyncio
    async def test_allocate_uses_cfg_policy_not_catalog(self):
        """Runtime authority: cfg policy prevalece sobre catálogo."""
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="CLI999",
        )
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.AUTO_REQUIRED),
        ):
            with pytest.raises(ValidationError) as exc:
                await CodigoGeneracionGateway.allocate("sls_cliente", ctx, session)
        assert exc.value.internal_code == "MANUAL_NOT_ALLOWED"

    @pytest.mark.asyncio
    async def test_allocate_empresa_scope_requires_cfg_row(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(NotFoundError) as exc:
                await CodigoGeneracionGateway.allocate("sls_cliente", ctx, session)
        assert exc.value.internal_code == "CFG_SEQUENCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_allocate_lazy_scope_uses_ensure_row(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            almacen_id=ALMACEN_ID,
        )
        session = AsyncMock()
        cfg_row = self._cfg_row(CodePolicy.AUTO_DEFAULT)
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.ensure_row",
            new_callable=AsyncMock,
            return_value=cfg_row,
        ) as mock_ensure:
            with patch(
                "app.core.codigo.gateway.codigo_generacion_gateway.AllocationCoordinator.allocate_next",
                new_callable=AsyncMock,
            ) as mock_alloc:
                from app.core.codigo.generation_result import AllocationResult

                mock_alloc.return_value = AllocationResult(
                    code="WMS0001",
                    sequence_key="wms_tarea",
                    consumed=True,
                    ultimo_numero=1,
                )
                result = await CodigoGeneracionGateway.allocate("wms_tarea", ctx, session)
        mock_ensure.assert_awaited_once()
        assert result.consumed is True

    @pytest.mark.asyncio
    async def test_unknown_sequence_key(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with pytest.raises(ValidationError):
            await CodigoGeneracionGateway.allocate("tabla_inexistente", ctx, session)

    @pytest.mark.asyncio
    async def test_allocate_manual_only_rejects_without_manual(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.MANUAL_ONLY),
        ):
            with pytest.raises(ValidationError) as exc:
                await CodigoGeneracionGateway.allocate("org_cargo", ctx, session)
        assert exc.value.internal_code == "MANUAL_NOT_ALLOWED"

    @pytest.mark.asyncio
    async def test_allocate_manual_only_accepts_with_manual(self):
        ctx = GenerationContext(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            manual_code="CAR001",
        )
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.MANUAL_ONLY),
        ):
            with patch(
                "app.core.codigo.gateway.codigo_generacion_gateway.CounterAlignmentService.maybe_align",
                new_callable=AsyncMock,
                return_value=1,
            ):
                result = await CodigoGeneracionGateway.allocate("org_cargo", ctx, session)
        assert result.code == "CAR001"
        assert result.consumed is False

    @pytest.mark.asyncio
    async def test_validate_manual_manual_only_accepts_code(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.MANUAL_ONLY),
        ):
            await CodigoGeneracionGateway.validate_manual(
                "org_cargo",
                "CAR001",
                ctx,
                session,
            )

    @pytest.mark.asyncio
    async def test_validate_manual_manual_only_rejects_empty(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.MANUAL_ONLY),
        ):
            with pytest.raises(ValidationError) as exc:
                await CodigoGeneracionGateway.validate_manual(
                    "org_cargo",
                    "",
                    ctx,
                    session,
                )
        assert exc.value.internal_code == "MANUAL_NOT_ALLOWED"

    @pytest.mark.asyncio
    async def test_validate_manual_auto_required_rejects(self):
        ctx = GenerationContext(client_id=CLIENT_ID, empresa_id=EMPRESA_ID)
        session = AsyncMock()
        with patch(
            "app.core.codigo.gateway.codigo_generacion_gateway.CfgSequenceStore.get_by_scope",
            new_callable=AsyncMock,
            return_value=self._cfg_row(CodePolicy.AUTO_REQUIRED),
        ):
            with pytest.raises(ValidationError) as exc:
                await CodigoGeneracionGateway.validate_manual(
                    "inv_movimiento",
                    "MOV000001",
                    ctx,
                    session,
                )
        assert exc.value.internal_code == "MANUAL_NOT_ALLOWED"

    def test_rollback_conceptual_no_double_consume_on_manual(self):
        """Manual aceptado no marca consumed=True (TD-MAN-01)."""
        from app.core.codigo.coordinator.allocation_coordinator import AllocationCoordinator

        defn = SequenceCatalog.get("sls_cliente")
        result = AllocationCoordinator.accept_manual(defn, "CLI999")
        assert result.consumed is False


@pytest.mark.unit
class TestDependencyGraph:
    def test_no_fastapi_imports_in_core_codigo(self):
        import app.core.codigo.gateway.codigo_generacion_gateway as gw

        source = open(gw.__file__, encoding="utf-8").read()
        assert "fastapi" not in source.lower()

    def test_catalog_is_static(self):
        keys_before = SequenceCatalog.all_keys()
        assert SequenceCatalog.count() == 63
        assert SequenceCatalog.all_keys() == keys_before
