"""
PR-F0-02 — Hybrid wrong-route adversarial tests.

Assert RI-39 fail-closed spec via harness (PR-F0-01). Sin BD, sin routing prod.
"""
from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

import pytest

from app.infrastructure.database.connection_async import DatabaseConnection
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
    resolve_engine_key,
)

pytest_plugins = ("tests.integration.conftest_hybrid",)


class WrongRouteViolation(AssertionError):
    """
    Violación del contrato de routing Hybrid.

    Representa la especificación funcional normativa — no replica routing.py:
    - RI-39: dedicated explícito nunca fallback silencioso a shared
    - RD-08: fallback shared solo legacy/shared; dedicated + metadata inválida → fail
    - BL-P07: fail-closed dedicated
    """


def assert_dedicated_tenant_route_compliant(
    metadata: Dict[str, Any],
    *,
    client_id: UUID,
) -> None:
    """
    Valida metadata de ruta para un tenant cuyo modo esperado es dedicated.

    Reglas spec (RI-39 / RD-08 / BL-P07), no lógica interna de routing.py.
    """
    database_type = metadata.get("database_type")
    if database_type == "single":
        raise WrongRouteViolation(
            f"RI-39: tenant {client_id} dedicated no debe enrutar con database_type=single"
        )

    installation_mode = metadata.get("tipo_instalacion")
    if installation_mode == "shared":
        raise WrongRouteViolation(
            f"RI-39: tenant {client_id} dedicated no debe usar metadata shared "
            f"(simulación stale cache)"
        )


def assert_shared_tenant_route_compliant(
    metadata: Dict[str, Any],
    *,
    client_id: UUID,
) -> None:
    """
    Valida metadata de ruta para tenant shared/legacy (RD-08).

    Permite database_type=single — no aplica reglas fail-closed dedicated.
    """
    database_type = metadata.get("database_type")
    installation_mode = metadata.get("tipo_instalacion")
    if installation_mode == "dedicated" and database_type == "single":
        raise WrongRouteViolation(
            f"RD-08/RI-39: metadata inconsistente para tenant {client_id}"
        )


class TestHybridEngineKeyContract:
    """S1 — contrato engine key del harness (DOD-F0-02)."""

    def test_dedicated_engine_key_matches_tenant_id(
        self,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        key = resolve_engine_key(
            hybrid_dedicated_client_id,
            DatabaseConnection.DEFAULT,
        )
        assert key == f"tenant_{hybrid_dedicated_client_id}"

    def test_shared_and_dedicated_engine_keys_are_distinct(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_dedicated_client_id: UUID,
        mock_hybrid_async_engine,
    ) -> None:
        shared_key = resolve_engine_key(
            hybrid_shared_client_id,
            DatabaseConnection.DEFAULT,
        )
        dedicated_key = resolve_engine_key(
            hybrid_dedicated_client_id,
            DatabaseConnection.DEFAULT,
        )
        assert shared_key != dedicated_key

        from app.infrastructure.database import connection_async

        shared_engine = connection_async._get_async_engine(
            DatabaseConnection.DEFAULT,
            client_id=hybrid_shared_client_id,
        )
        dedicated_engine = connection_async._get_async_engine(
            DatabaseConnection.DEFAULT,
            client_id=hybrid_dedicated_client_id,
        )
        assert mock_hybrid_async_engine[shared_key] is shared_engine
        assert mock_hybrid_async_engine[dedicated_key] is dedicated_engine
        assert shared_engine is not dedicated_engine

    def test_admin_engine_key_isolated(
        self,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        admin_key = resolve_engine_key(None, DatabaseConnection.ADMIN)
        tenant_key = resolve_engine_key(
            hybrid_dedicated_client_id,
            DatabaseConnection.DEFAULT,
        )
        assert admin_key == "admin"
        assert admin_key != tenant_key


class TestDedicatedRouteCompliance:
    """S2 — dedicated válido vs violación RI-39; RD-08 shared legacy."""

    def test_valid_dedicated_metadata_passes_ri39(
        self,
        hybrid_dedicated_client_id: UUID,
        hybrid_dedicated_metadata: Dict[str, Any],
    ) -> None:
        assert_dedicated_tenant_route_compliant(
            hybrid_dedicated_metadata,
            client_id=hybrid_dedicated_client_id,
        )

    def test_valid_shared_metadata_allowed_rd08(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_shared_metadata: Dict[str, Any],
    ) -> None:
        assert_shared_tenant_route_compliant(
            hybrid_shared_metadata,
            client_id=hybrid_shared_client_id,
        )

    def test_dedicated_with_single_database_type_raises_violation(
        self,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        missing_metadata_adversarial = build_dedicated_metadata(
            hybrid_dedicated_client_id,
        )
        missing_metadata_adversarial["database_type"] = "single"

        with pytest.raises(WrongRouteViolation, match="database_type=single"):
            assert_dedicated_tenant_route_compliant(
                missing_metadata_adversarial,
                client_id=hybrid_dedicated_client_id,
            )


class TestWrongRouteAdversarialStaleCache:
    """S3 — stale cache sim: metadata adversarial directa (M-01, sin connection_cache)."""

    def test_stale_shared_shaped_metadata_for_dedicated_client_raises_violation(
        self,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        stale_cache_metadata = build_shared_metadata(hybrid_dedicated_client_id)

        with pytest.raises(WrongRouteViolation, match="database_type=single"):
            assert_dedicated_tenant_route_compliant(
                stale_cache_metadata,
                client_id=hybrid_dedicated_client_id,
            )
