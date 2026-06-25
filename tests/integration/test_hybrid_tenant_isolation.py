"""
PR-F0-03 — Hybrid tenant isolation harness tests.

Assert G-20 tenant filter en shared path vía harness (PR-F0-01). Sin BD.
"""
from __future__ import annotations

from typing import Set
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import Select, select
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping

from app.core.exceptions import ValidationError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.query_helpers import apply_tenant_filter
from app.infrastructure.database.tables import ClienteTable, UsuarioTable
from tests.integration.helpers.hybrid_mock_metadata import (
    build_tenant_context,
)

pytest_plugins = ("tests.integration.conftest_hybrid",)


class TenantIsolationViolation(AssertionError):
    """
    Violación del contrato de aislamiento tenant en shared path.

    Especificación funcional normativa — no replica query_helpers.py:
    - G-20: aislamiento tenant y tenant filter vigentes
    - RI-11: ninguna operación tenant-data accede datos de otro tenant
    - RI-40: tenant filter en tenant-data shared (enforce cliente_id)
    """


def _client_ids_in_where(whereclause) -> Set[UUID]:
    """Extrae UUIDs comparados en condiciones cliente_id == value."""
    ids: Set[UUID] = set()
    if whereclause is None:
        return ids
    if isinstance(whereclause, BooleanClauseList):
        for clause in whereclause.clauses:
            ids |= _client_ids_in_where(clause)
    elif isinstance(whereclause, Grouping):
        ids |= _client_ids_in_where(whereclause.element)
    elif isinstance(whereclause, BinaryExpression):
        left_key = getattr(whereclause.left, "key", None)
        right_key = getattr(whereclause.right, "key", None)
        if left_key == "cliente_id":
            value = _coerce_uuid_operand(whereclause.right)
            if value is not None:
                ids.add(value)
        if right_key == "cliente_id":
            value = _coerce_uuid_operand(whereclause.left)
            if value is not None:
                ids.add(value)
    return ids


def _coerce_uuid_operand(operand) -> UUID | None:
    value = getattr(operand, "value", None)
    if isinstance(value, UUID):
        return value
    effective = getattr(operand, "effective_value", None)
    if isinstance(effective, UUID):
        return effective
    return None


def assert_query_filters_client_id(query: Select, client_id: UUID) -> None:
    """
    Verifica RI-40 / G-20: query incluye filtro cliente_id == client_id esperado.
    """
    bound_ids = _client_ids_in_where(query.whereclause)
    if client_id not in bound_ids:
        raise TenantIsolationViolation(
            f"RI-40/G-20: se esperaba filtro cliente_id={client_id}, "
            f"encontrado={bound_ids or 'ninguno'}"
        )


def assert_query_excludes_client_id(query: Select, forbidden_client_id: UUID) -> None:
    """Verifica RI-11: query no filtra por otro tenant."""
    bound_ids = _client_ids_in_where(query.whereclause)
    if forbidden_client_id in bound_ids:
        raise TenantIsolationViolation(
            f"RI-11: filtro no debe usar cliente_id={forbidden_client_id}, "
            f"encontrado={bound_ids}"
        )


class TestHybridSharedTenantFilter:
    """S1 — shared path: apply_tenant_filter enforce cliente_id."""

    def test_apply_tenant_filter_enforces_cliente_id_shared_path(
        self,
        hybrid_shared_tenant_context,
        hybrid_shared_client_id: UUID,
    ) -> None:
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))
        filtered = apply_tenant_filter(query, table_name="usuario")
        assert_query_filters_client_id(filtered, hybrid_shared_client_id)


class TestHybridCrossTenantNegative:
    """S2 — cross-tenant negativo: contexto activo delimita el filtro."""

    def test_filter_bound_to_active_context_not_other_tenant(
        self,
        hybrid_shared_tenant_context,
        hybrid_shared_client_id: UUID,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        query = select(UsuarioTable)
        filtered = apply_tenant_filter(query, table_name="usuario")
        assert_query_filters_client_id(filtered, hybrid_shared_client_id)
        assert_query_excludes_client_id(filtered, hybrid_dedicated_client_id)

    def test_context_switch_changes_filter_binding(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_dedicated_client_id: UUID,
        hybrid_shared_metadata,
        hybrid_dedicated_metadata,
    ) -> None:
        shared_query = select(UsuarioTable)
        shared_ctx = build_tenant_context(
            hybrid_shared_client_id,
            hybrid_shared_metadata,
            subdominio="hybrid-shared-mock",
            codigo_cliente="HYBRID_SHARED",
        )
        shared_tokens = set_tenant_context(shared_ctx)
        try:
            shared_filtered = apply_tenant_filter(shared_query, table_name="usuario")
            assert_query_filters_client_id(shared_filtered, hybrid_shared_client_id)
        finally:
            reset_tenant_context(shared_tokens)

        dedicated_query = select(UsuarioTable)
        dedicated_ctx = build_tenant_context(
            hybrid_dedicated_client_id,
            hybrid_dedicated_metadata,
            subdominio="hybrid-dedicated-mock",
            codigo_cliente="HYBRID_DEDICATED",
        )
        dedicated_tokens = set_tenant_context(dedicated_ctx)
        try:
            dedicated_filtered = apply_tenant_filter(dedicated_query, table_name="usuario")
            assert_query_filters_client_id(dedicated_filtered, hybrid_dedicated_client_id)
        finally:
            reset_tenant_context(dedicated_tokens)


class TestHybridTenantFilterBoundaries:
    """S3 — límites G-20: global tables y missing context."""

    def test_global_table_skips_tenant_filter(self) -> None:
        query = select(ClienteTable)
        where_before = query.whereclause
        filtered = apply_tenant_filter(query, table_name="cliente")
        assert filtered.whereclause == where_before

    def test_missing_context_raises_on_tenant_table(self) -> None:
        query = select(UsuarioTable)
        with patch("app.infrastructure.database.query_helpers.settings") as mock_settings:
            mock_settings.ALLOW_TENANT_FILTER_BYPASS = False
            with pytest.raises(ValidationError) as exc_info:
                apply_tenant_filter(query, table_name="usuario")
        assert exc_info.value.internal_code == "MISSING_TENANT_CONTEXT"
