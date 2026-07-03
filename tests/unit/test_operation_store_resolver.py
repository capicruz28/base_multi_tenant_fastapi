"""F13-1 — OperationStoreResolver unit matrix (F13-B1 §10.5)."""
from __future__ import annotations

from typing import Any, Optional, Tuple
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import DatabaseError, ValidationError
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.operation_store_resolver import (
    OperationStoreResolver,
    get_installation_profile,
    resolve_database_type,
    resolve_operation_store,
)
from app.core.tenant.operation_store_types import (
    EngineKind,
    OperationDescriptor,
    OperationPlane,
    SessionKind,
)
from app.core.tenant.routing import DEDICATED_ROUTE_FAIL_CLOSED
from app.infrastructure.database.connection_async import DatabaseConnection
from app.modules.superadmin.application.platform_global_query_intent import (
    kwargs_control_plane_read,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
)

RESOLVER_MODULE = "app.core.tenant.operation_store_resolver"


def _descriptor(
    *,
    target: UUID | None = None,
    plane: OperationPlane = OperationPlane.TENANT_DATA,
    session_kind: SessionKind = SessionKind.TENANT_SESSION,
    session_target: UUID | None = None,
) -> OperationDescriptor:
    return OperationDescriptor(
        target_cliente_id=target or uuid4(),
        operation_plane=plane,
        session_kind=session_kind,
        session_target_cliente_id=session_target,
    )


def _metadata_catalog_target_from_profile(
    cliente_id: UUID,
    metadata: dict[str, Any],
) -> Tuple[DatabaseConnection, Optional[UUID]]:
    """
    Catálogo permiso/menú con metadata del target (sin TenantContext host).

    Equivalente a la regla corregida F13-2: multi → DEFAULT; single → ADMIN.
    """
    if metadata.get("database_type") == "multi":
        return DatabaseConnection.DEFAULT, cliente_id
    return DatabaseConnection.ADMIN, None


@pytest.fixture
def mock_metadata():
    def _apply(metadata: dict[str, Any]):
        return patch(
            f"{RESOLVER_MODULE}.get_connection_metadata_async",
            new=AsyncMock(return_value=metadata),
        )

    return _apply


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t01_control_plane_returns_admin_engine_scoped():
    descriptor = _descriptor(plane=OperationPlane.CONTROL_PLANE)
    intent = await resolve_operation_store(descriptor)

    assert intent.connection_type == DatabaseConnection.ADMIN
    assert intent.client_id is None
    assert intent.identity_scope == IdentityScope.ENGINE_SCOPED
    assert intent.operation_class == "control_plane"
    assert intent.database_type == "single"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t02_tenant_data_shared_returns_default_row_scoped(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_SHARED
    metadata = build_shared_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    assert intent.connection_type == DatabaseConnection.DEFAULT
    assert intent.client_id == target
    assert intent.identity_scope == IdentityScope.ROW_SCOPED
    assert intent.operation_class == "tenant_data"
    assert intent.engine_kind == EngineKind.SHARED_SINGLE
    assert intent.database_type == "single"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t03_tenant_data_dedicated_returns_default_engine_scoped(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    metadata = build_dedicated_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    assert intent.connection_type == DatabaseConnection.DEFAULT
    assert intent.client_id == target
    assert intent.identity_scope == IdentityScope.ENGINE_SCOPED
    assert intent.operation_class == "tenant_data"
    assert intent.engine_kind == EngineKind.DEDICATED_MULTI
    assert intent.database_type == "multi"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t04_dedicated_incomplete_metadata_raises_fail_closed():
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    incomplete = build_dedicated_metadata(target)
    incomplete["servidor"] = None

    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(return_value=incomplete),
    ):
        with pytest.raises(DatabaseError) as exc_info:
            await resolve_operation_store(
                _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
            )

    assert exc_info.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t05_impersonation_target_mismatch_raises_validation_error():
    target = uuid4()
    other = uuid4()
    descriptor = _descriptor(
        target=target,
        session_kind=SessionKind.IMPERSONATION,
        session_target=other,
    )

    with pytest.raises(ValidationError) as exc_info:
        await resolve_operation_store(descriptor)

    assert exc_info.value.internal_code == "IMPERSONATION_TARGET_MISMATCH"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t06_golden_shared_resolver_matches_f13_a1_algorithm(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_SHARED
    metadata = build_shared_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    catalog_conn, catalog_client = _metadata_catalog_target_from_profile(target, metadata)
    assert intent.connection_type == DatabaseConnection.DEFAULT
    assert intent.client_id == target
    assert catalog_conn == DatabaseConnection.ADMIN
    assert catalog_client is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t07_golden_dedicated_matches_metadata_catalog_target(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    metadata = build_dedicated_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    catalog_conn, catalog_client = _metadata_catalog_target_from_profile(target, metadata)
    assert intent.connection_type == catalog_conn
    assert intent.client_id == catalog_client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_t08_to_execute_query_kwargs_compatible_with_execute_query(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    metadata = build_dedicated_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    kwargs = intent.to_execute_query_kwargs()
    assert set(kwargs.keys()) == {
        "connection_type",
        "client_id",
        "identity_scope",
        "operation_class",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_control_plane_golden_parity_kwargs_control_plane_read():
    intent = await resolve_operation_store(
        _descriptor(plane=OperationPlane.CONTROL_PLANE)
    )
    expected = kwargs_control_plane_read()

    assert intent.to_execute_query_kwargs() == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_control_plane_skips_metadata_lookup():
    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(),
    ) as mocked:
        await resolve_operation_store(_descriptor(plane=OperationPlane.CONTROL_PLANE))

    mocked.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_operation_store_resolver_class_resolve(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_SHARED
    metadata = build_shared_metadata(target)

    with mock_metadata(metadata):
        intent = await OperationStoreResolver.resolve(
            _descriptor(target=target, plane=OperationPlane.TENANT_DATA)
        )

    assert intent.connection_type == DatabaseConnection.DEFAULT


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_installation_profile_delegates_metadata(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    metadata = build_dedicated_metadata(target)

    with mock_metadata(metadata) as metadata_mock:
        profile = await get_installation_profile(target)

    metadata_mock.assert_awaited_once()
    assert profile.cliente_id == target
    assert profile.engine_kind == EngineKind.DEDICATED_MULTI
    assert resolve_database_type(profile) == "multi"


@pytest.mark.unit
def test_resolve_database_type_shared_single():
    from app.core.tenant.operation_store_types import InstallationProfile

    target = HYBRID_FIXTURE_TENANT_SHARED

    shared_profile = InstallationProfile.from_metadata(
        target,
        build_shared_metadata(target),
    )
    assert resolve_database_type(shared_profile) == "single"

    dedicated_profile = InstallationProfile.from_metadata(
        HYBRID_FIXTURE_TENANT_DEDICATED,
        build_dedicated_metadata(HYBRID_FIXTURE_TENANT_DEDICATED),
    )
    assert resolve_database_type(dedicated_profile) == "multi"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_impersonation_matching_session_target_succeeds(mock_metadata):
    target = HYBRID_FIXTURE_TENANT_DEDICATED
    metadata = build_dedicated_metadata(target)

    with mock_metadata(metadata):
        intent = await resolve_operation_store(
            _descriptor(
                target=target,
                session_kind=SessionKind.IMPERSONATION,
                session_target=target,
            )
        )

    assert intent.client_id == target
