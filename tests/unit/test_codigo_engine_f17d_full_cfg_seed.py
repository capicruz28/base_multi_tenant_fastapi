"""F17D — el bootstrap siembra todas las CFG con scope resoluble (TENANT + EMPRESA).

Criterio (Opción A): se siembran automáticamente las secuencias CFG cuyo
`scope_fingerprint` queda determinado en onboarding (TENANT/EMPRESA). Las de scope
ALMACEN/PUNTO_VENTA quedan lazy; las FISCAL nunca van a cfg_codigo_secuencia.
Nada hardcodeado: todo se deriva del SequenceCatalog.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.codigo.enums import CodePolicy, ScopeType, StoreType
from app.core.codigo.onboarding_seed import (
    EAGER_SEQUENCE_KEYS,
    ONBOARDING_RESOLVABLE_SCOPES,
    ONBOARDING_SEQUENCE_SEEDS,
)
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)
from app.modules.tenant.application.services.cfg_codigo_onboarding_seed import (
    seed_cfg_empresa,
    seed_cfg_tenant,
)


def _catalog_cfg():
    return [d for d in SequenceCatalog.all_definitions() if d.store_type == StoreType.CFG]


@pytest.mark.unit
class TestF17DSeedSelection:
    def test_seed_covers_exactly_resolvable_cfg(self):
        resolvable = {
            d.sequence_key
            for d in _catalog_cfg()
            if d.scope_type in ONBOARDING_RESOLVABLE_SCOPES
        }
        assert set(EAGER_SEQUENCE_KEYS) == resolvable

    def test_seed_excludes_almacen_and_punto_venta(self):
        seeded = set(EAGER_SEQUENCE_KEYS)
        lazy = [
            d
            for d in _catalog_cfg()
            if d.scope_type not in ONBOARDING_RESOLVABLE_SCOPES
        ]
        assert lazy, "debe haber CFG de scope ALMACEN/PUNTO_VENTA que quedan lazy"
        for defn in lazy:
            assert defn.sequence_key not in seeded

    def test_seed_excludes_fiscal(self):
        seeded = set(EAGER_SEQUENCE_KEYS)
        assert "invbill_comprobante" not in seeded
        assert "log_guia_remision" not in seeded

    def test_every_seed_is_cfg_and_resolvable_scope(self):
        for seed in ONBOARDING_SEQUENCE_SEEDS:
            defn = SequenceCatalog.get(seed.sequence_key)
            assert defn.store_type == StoreType.CFG
            assert seed.scope_type in ONBOARDING_RESOLVABLE_SCOPES

    def test_every_seed_carries_platform_initial_generation_policy(self):
        for seed in ONBOARDING_SEQUENCE_SEEDS:
            assert seed.generation_policy == CodePolicy.AUTO_REQUIRED
            # F15A catalog policy remains independent (often AUTO_DEFAULT on F1).
            defn = SequenceCatalog.get(seed.sequence_key)
            assert defn.policy is not None

    def test_seed_count_is_derived_not_fixed(self):
        expected = sum(
            1
            for d in _catalog_cfg()
            if d.scope_type in ONBOARDING_RESOLVABLE_SCOPES
        )
        assert len(ONBOARDING_SEQUENCE_SEEDS) == expected
        assert len(EAGER_SEQUENCE_KEYS) == expected

    def test_single_tenant_scope_is_org_empresa(self):
        tenant = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.scope_type == ScopeType.TENANT]
        assert len(tenant) == 1
        assert tenant[0].sequence_key == "org_empresa"


@pytest.mark.unit
@pytest.mark.asyncio
class TestF17DSeedExecution:
    async def test_seed_cfg_tenant_and_empresa_seeds_all_resolvable_rows(self):
        """Shared y Dedicated usan seed_cfg_tenant + seed_cfg_empresa (TBO paso 8)."""
        session = AsyncMock()
        cliente_id = uuid4()
        empresa_id = uuid4()

        with patch.object(
            CfgCodigoSecuenciaRepository, "insert_secuencia", new_callable=AsyncMock
        ) as mock_ins:
            await seed_cfg_tenant(session, cliente_id)
            await seed_cfg_empresa(session, cliente_id, empresa_id)

        calls = mock_ins.await_args_list
        assert len(calls) == len(ONBOARDING_SEQUENCE_SEEDS)

        tenant_calls = [c for c in calls if c.kwargs["scope_type"] == ScopeType.TENANT]
        empresa_calls = [c for c in calls if c.kwargs["scope_type"] == ScopeType.EMPRESA]

        assert len(tenant_calls) == 1
        assert tenant_calls[0].kwargs["empresa_id"] is None

        assert len(empresa_calls) == len(ONBOARDING_SEQUENCE_SEEDS) - 1
        assert all(c.kwargs["empresa_id"] == empresa_id for c in empresa_calls)

        scopes = {c.kwargs["scope_type"] for c in calls}
        assert ScopeType.ALMACEN not in scopes
        assert ScopeType.PUNTO_VENTA not in scopes

        assert all(c.kwargs["session"] is session for c in calls)

        for seed in ONBOARDING_SEQUENCE_SEEDS:
            matching = [
                c
                for c in calls
                if c.kwargs["sequence_key"] == seed.sequence_key
                and c.kwargs["scope_type"] == seed.scope_type
            ]
            assert len(matching) == 1
            assert matching[0].kwargs["generation_policy"] == seed.generation_policy
