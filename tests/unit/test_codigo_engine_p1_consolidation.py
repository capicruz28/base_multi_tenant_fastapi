"""F17C — validación de los ajustes P1 de consolidación del motor de códigos.

Cubre:
- ADJ-01: onboarding_seed deriva del SequenceCatalog (sin drift de metadatos).
- ADJ-05: EAGER_SEQUENCE_KEYS es la única fuente del subconjunto eager.
- ADJ-03: blindaje de escritura del CfgCodigoSecuenciaRepository (session obligatoria).
- ADJ-06: tenant_seed_profiles deriva el conteo de len(EAGER_SEQUENCE_KEYS).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.core.codigo.onboarding_seed import (
    EAGER_SEQUENCE_KEYS,
    ONBOARDING_SEQUENCE_SEEDS,
    SECUENCIAS_CODIGO,
    OnboardingSequenceSeed,
)
from app.core.codigo.sequence_catalog import SequenceCatalog
from app.core.exceptions import ServiceError
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)
from app.core.codigo.enums import CodePolicy, ScopeType

CLIENT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


@pytest.mark.unit
class TestAdj01OnboardingDerivesFromCatalog:
    def test_every_seed_matches_catalog_definition(self):
        """Ningún valor del seed se re-declara: todo proviene del catálogo."""
        for seed in ONBOARDING_SEQUENCE_SEEDS:
            defn = SequenceCatalog.get(seed.sequence_key)
            assert seed.prefijo == defn.default_prefix
            assert seed.longitud_numero == defn.default_padding
            assert seed.separador == defn.default_separator
            assert seed.scope_type == defn.scope_type
            assert seed.numero_inicial == defn.numero_inicial
            assert seed.generation_policy == CodePolicy.AUTO_REQUIRED

    def test_from_definition_roundtrip(self):
        defn = SequenceCatalog.get("inv_producto")
        seed = OnboardingSequenceSeed.from_definition(defn)
        assert seed.sequence_key == "inv_producto"
        assert seed.prefijo == defn.default_prefix
        assert seed.longitud_numero == defn.default_padding
        assert seed.ultimo_numero == 0
        assert seed.generation_policy == CodePolicy.AUTO_REQUIRED

    def test_no_hardcoded_values_drift(self):
        """El seed reconstruido desde el catálogo es idéntico al materializado."""
        rebuilt = tuple(
            OnboardingSequenceSeed.from_definition(SequenceCatalog.get(k))
            for k in EAGER_SEQUENCE_KEYS
        )
        assert rebuilt == ONBOARDING_SEQUENCE_SEEDS


@pytest.mark.unit
class TestAdj05EagerSequenceKeysSingleSource:
    def test_all_eager_keys_exist_in_catalog(self):
        for key in EAGER_SEQUENCE_KEYS:
            assert SequenceCatalog.contains(key), f"{key} no está en el catálogo"

    def test_seeds_length_and_order_follow_eager_keys(self):
        assert len(ONBOARDING_SEQUENCE_SEEDS) == len(EAGER_SEQUENCE_KEYS)
        assert tuple(s.sequence_key for s in ONBOARDING_SEQUENCE_SEEDS) == EAGER_SEQUENCE_KEYS

    def test_legacy_tuple_derives_from_same_source(self):
        assert len(SECUENCIAS_CODIGO) == len(EAGER_SEQUENCE_KEYS)

    def test_no_duplicate_eager_keys(self):
        assert len(EAGER_SEQUENCE_KEYS) == len(set(EAGER_SEQUENCE_KEYS))

    def test_org_empresa_tenant_seed_ultimo_numero_one(self):
        tenant = [
            s for s in ONBOARDING_SEQUENCE_SEEDS if s.sequence_key == "org_empresa"
        ]
        assert len(tenant) == 1
        seed = tenant[0]
        assert seed.ultimo_numero == 1
        assert seed.numero_inicial == 1
        assert seed.prefijo == "EMP"
        assert seed.longitud_numero == 3
        assert seed.generation_policy == CodePolicy.AUTO_REQUIRED

    def test_non_org_empresa_seeds_keep_ultimo_numero_zero(self):
        for seed in ONBOARDING_SEQUENCE_SEEDS:
            if seed.sequence_key == "org_empresa":
                continue
            assert seed.ultimo_numero == 0

    def test_scope_split_preserved(self):
        tenant = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.scope_type == ScopeType.TENANT]
        empresa = [s for s in ONBOARDING_SEQUENCE_SEEDS if s.scope_type == ScopeType.EMPRESA]
        assert len(tenant) == 1 and tenant[0].sequence_key == "org_empresa"
        assert len(empresa) == len(EAGER_SEQUENCE_KEYS) - 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestAdj03RepositoryWriteHardening:
    async def test_insert_secuencia_without_session_raises(self):
        repo = CfgCodigoSecuenciaRepository()
        with pytest.raises(ServiceError) as exc:
            await repo.insert_secuencia(
                CLIENT_ID,
                "org_empresa",
                ScopeType.TENANT,
                "EMP",
                3,
                "",
                generation_policy=CodePolicy.AUTO_DEFAULT,
            )
        assert exc.value.internal_code == "CFG_SECUENCIA_WRITE_REQUIRES_SESSION"

    async def test_update_ultimo_numero_without_session_raises(self):
        repo = CfgCodigoSecuenciaRepository()
        with pytest.raises(ServiceError) as exc:
            await repo.update_ultimo_numero(uuid4(), 5, cliente_id=CLIENT_ID)
        assert exc.value.internal_code == "CFG_SECUENCIA_WRITE_REQUIRES_SESSION"

    async def test_update_secuencia_without_session_raises(self):
        repo = CfgCodigoSecuenciaRepository()
        with pytest.raises(ServiceError) as exc:
            await repo.update_secuencia(
                uuid4(), "EMP", 3, "", True, cliente_id=CLIENT_ID
            )
        assert exc.value.internal_code == "CFG_SECUENCIA_WRITE_REQUIRES_SESSION"


@pytest.mark.unit
@pytest.mark.asyncio
class TestP1AGenerationPolicyPersistence:
    async def test_ensure_row_writes_generation_policy_explicitly(self):
        from unittest.mock import AsyncMock, patch
        from uuid import uuid4

        from app.core.codigo.scope_key import ScopeKey
        from app.core.codigo.stores.cfg_sequence_store import CfgSequenceRow, CfgSequenceStore
        from app.core.codigo.sequence_catalog import SequenceCatalog

        defn = SequenceCatalog.get("inv_almacen")
        scope_key = ScopeKey(
            sequence_key=defn.sequence_key,
            scope_type=defn.scope_type,
            client_id=CLIENT_ID,
            empresa_id=uuid4(),
            almacen_id=uuid4(),
        )
        session = AsyncMock()
        row_dict = {
            "secuencia_id": str(uuid4()),
            "cliente_id": str(CLIENT_ID),
            "sequence_key": defn.sequence_key,
            "scope_type": defn.scope_type.value,
            "scope_fingerprint": scope_key.fingerprint,
            "empresa_id": str(scope_key.empresa_id),
            "almacen_id": str(scope_key.almacen_id),
            "punto_venta_id": None,
            "prefijo": defn.default_prefix,
            "separador": defn.default_separator,
            "longitud_numero": defn.default_padding,
            "ultimo_numero": 0,
            "numero_inicial": defn.numero_inicial,
            "es_activo": True,
            "generation_policy": CodePolicy.AUTO_REQUIRED.value,
        }

        with patch.object(CfgSequenceStore, "get_by_scope", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [None, CfgSequenceRow.from_dict(row_dict)]
            await CfgSequenceStore.ensure_row(session, scope_key, defn)

        insert_stmt = session.execute.await_args.args[0]
        assert insert_stmt.compile().params["generation_policy"] == CodePolicy.AUTO_REQUIRED.value


@pytest.mark.unit
def test_repository_has_no_adminless_write_path():
    """El repo no debe conservar escrituras vía execute_insert/execute_update sin sesión."""
    from pathlib import Path

    source = Path(
        "app/infrastructure/database/repositories/cfg_codigo_secuencia_repository.py"
    ).read_text(encoding="utf-8")
    assert "execute_insert(" not in source
    assert "execute_update(" not in source


@pytest.mark.unit
def test_adj06_row_expectations_derive_from_eager_keys():
    from app.infrastructure.provisioning.tenant_seed_profiles import (
        resolve_tenant_seed_profile,
    )

    profile = resolve_tenant_seed_profile("trial")
    cfg = dict(profile.row_expectations)["cfg_codigo_secuencia"]
    assert cfg == len(EAGER_SEQUENCE_KEYS)
