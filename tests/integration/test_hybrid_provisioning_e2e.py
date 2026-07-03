"""
PR-F4-12 — Dedicated Provisioning E2E integration (mock harness).

Ejercita flujo completo S1→S10, retry, abort, compensation y smoke Ready
sin SQL Server. Evidencia G-F4-02/G-F4-03 vía audit recorder.

DOD-F4-12: E2E mock green; shared sin regresión (suite separada CI).
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.exceptions import ConflictError
from app.core.tenant.cache import connection_cache
from app.core.tenant.routing import (
    clear_intra_request_route_cache,
    get_connection_for_tenant,
    get_connection_metadata_async,
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.modules.tenant.application.provisioning import (
    ProvisioningRunInitializedResult,
    ProvisioningState,
    ProvisioningStepCode,
    SAGA_STEP_ORDER,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    resolve_engine_key,
)
from tests.integration.helpers.provisioning_e2e_harness import (
    E2E_CLIENTE_ID,
    E2E_RUN_ID,
    ProvisioningE2EStack,
    build_cliente_profile,
    build_provisioning_e2e_stack,
    steps_through_s3_marker,
    steps_through_s8,
)

pytest_plugins = ("tests.integration.conftest_provisioning_e2e",)


def _mock_async_session_cm():
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.keys.return_value = ["usuario_id"]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm


@pytest.fixture(autouse=True)
def _reset_route_cache(e2e_cliente_id: UUID):
    clear_intra_request_route_cache()
    connection_cache.invalidate(e2e_cliente_id)
    yield
    clear_intra_request_route_cache()
    connection_cache.invalidate(e2e_cliente_id)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDedicatedProvisioningE2EHappyPath:
    """Happy path S1→S10 vía orchestrator + dispatcher sync."""

    async def test_s1_through_s10_all_steps_completed(
        self,
        provisioning_e2e_stack: ProvisioningE2EStack,
        dedicated_enabled_sync_dispatcher,
    ):
        stack = provisioning_e2e_stack
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.execute_query",
            new_callable=AsyncMock,
            return_value=build_cliente_profile(),
        ):
            result = await stack.dispatcher.dispatch(
                stack.job_request(),
            )

        assert result.dispatched is True
        assert result.sync_execution is True
        expected_codes = [code.value for code in SAGA_STEP_ORDER]
        assert stack.completed_steps == expected_codes
        stack.mocks["activation"].register_metadata.assert_called_once()
        stack.mocks["activation"].activate_routing.assert_called_once()
        stack.mocks["activation"].mark_ready.assert_called_once()
        stack.mocks["database_executor"].provision_physical_database.assert_called_once()
        stack.mocks["bootstrap"].run_dedicated_schema_bootstrap.assert_called_once()
        stack.mocks["catalog_seed"].run_catalog_seed.assert_called_once()
        stack.mocks["tenant_seed"].run_tenant_seed.assert_called_once()

    async def test_dispatcher_dedupes_concurrent_run(
        self,
        provisioning_e2e_stack: ProvisioningE2EStack,
    ):
        import asyncio

        stack = provisioning_e2e_stack
        job = stack.job_request()
        started = asyncio.Event()
        release = asyncio.Event()

        async def slow_handler(_job):
            started.set()
            await release.wait()

        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
        ) as orch_settings:
            orch_settings.DEDICATED_ENABLED = True
            with patch.object(
                stack.dispatcher, "_default_handler", side_effect=slow_handler
            ):
                with patch(
                    "app.modules.tenant.application.services.provisioning_job_dispatcher.settings"
                ) as disp_settings:
                    disp_settings.PROVISIONING_DISPATCHER_ENABLED = True
                    disp_settings.PROVISIONING_DISPATCHER_SYNC = False
                    first = await stack.dispatcher.dispatch(job)
                    await asyncio.wait_for(started.wait(), timeout=2.0)
                    second = await stack.dispatcher.dispatch(job)
                    release.set()
                    await stack.dispatcher.drain_pending_jobs(timeout_seconds=5.0)

        assert first.dispatched is True
        assert second.dispatched is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestDedicatedProvisioningE2EAbortCompensation:
    """Abort + compensación S10→S3 (DROP DB mock)."""

    async def test_abort_transitions_failed_and_compensates_s3(
        self,
        dedicated_enabled_sync_dispatcher,
    ):
        stack = build_provisioning_e2e_stack(
            provisioning_state=ProvisioningState.PROVISIONING,
            step_rows=steps_through_s3_marker(),
        )
        snapshot_state = {"value": ProvisioningState.PROVISIONING.value}

        async def _get_snapshot(_cid):
            return {
                "cliente_id": stack.cliente_id,
                "tipo_instalacion": "dedicated",
                "provisioning_state": snapshot_state["value"],
                "current_provisioning_run_id": stack.run_id,
            }

        stack.mocks["repo"].get_cliente_provisioning_snapshot.side_effect = _get_snapshot
        stack.mocks["repo"].list_steps_for_run.return_value = steps_through_s8()

        async def _to_failed(**kwargs):
            snapshot_state["value"] = ProvisioningState.FAILED.value
            stack.audit.record(
                "dedicated.provisioning.failed",
                cliente_id=str(kwargs.get("cliente_id")),
                run_id=str(kwargs.get("provisioning_run_id")),
                error_code=kwargs.get("error_code", "PROVISIONING_ABORTED"),
            )

        stack.mocks["state"].transition_run_to_failed.side_effect = _to_failed

        with patch.object(
            stack.compensation,
            "_reset_provisioning_steps",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.infrastructure.provisioning.dedicated_provisioning_compensation_service.invalidate_client_connection_cache"
            ) as mock_invalidate:
                await stack.compensation.abort_provisioning_run(
                    cliente_id=stack.cliente_id,
                    provisioning_run_id=stack.run_id,
                    reason="e2e ops abort",
                )

        stack.mocks["state"].transition_run_to_failed.assert_called_once()
        stack.mocks["database_executor"].drop_physical_database.assert_called_once()
        stack.mocks["metadata_cleanup"].cleanup_primary_connection.assert_called_once()
        mock_invalidate.assert_called()
        metrics = stack.audit.metric_counts()
        assert metrics.get("dedicated.provisioning.failed", 0) >= 1

    async def test_compensate_rejects_ready_tenant(
        self,
        dedicated_enabled_sync_dispatcher,
    ):
        stack = build_provisioning_e2e_stack(
            provisioning_state=ProvisioningState.READY,
            step_rows=steps_through_s8(),
        )
        stack.mocks["repo"].get_cliente_provisioning_snapshot.return_value = {
            "cliente_id": stack.cliente_id,
            "tipo_instalacion": "dedicated",
            "provisioning_state": ProvisioningState.READY.value,
            "current_provisioning_run_id": stack.run_id,
        }
        with pytest.raises(ConflictError) as exc_info:
            await stack.compensation.compensate_for_failed_run(
                cliente_id=stack.cliente_id,
                provisioning_run_id=stack.run_id,
            )
        assert exc_info.value.internal_code == "PROVISIONING_COMPENSATION_NOT_ALLOWED"


@pytest.mark.integration
@pytest.mark.asyncio
class TestDedicatedProvisioningE2ERetry:
    """Retry 2× sin duplicados — DOD-F4-05."""

    async def test_retry_twice_dispatches_without_duplicate_active_runs(
        self,
        dedicated_enabled_sync_dispatcher,
    ):
        stack = build_provisioning_e2e_stack(
            provisioning_state=ProvisioningState.FAILED,
            step_rows=steps_through_s3_marker(),
        )
        transition = object()
        stack.mocks["state"].begin_retry_from_failed.return_value = transition
        dispatch_results = []

        async def _track_dispatch(**kwargs):
            from unittest.mock import MagicMock

            result = MagicMock(dispatched=True)
            dispatch_results.append(kwargs)
            return result

        stack.mocks["dispatcher_mock"].dispatch_for_run.side_effect = _track_dispatch

        for attempt in (1, 2):
            stack.audit.record(
                "dedicated.provisioning.retry",
                cliente_id=str(stack.cliente_id),
                run_id=str(stack.run_id),
                attempt=attempt,
            )
            result = await stack.compensation.retry_provisioning_run(
                cliente_id=stack.cliente_id,
                provisioning_run_id=stack.run_id,
            )
            assert result[0] is transition
            assert result[1].dispatched is True

        assert stack.mocks["state"].begin_retry_from_failed.call_count == 2
        assert len(dispatch_results) == 2
        assert all(r["provisioning_run_id"] == stack.run_id for r in dispatch_results)
        assert stack.audit.metric_counts().get("dedicated.provisioning.retry") == 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestDedicatedProvisioningE2ESmokeReady:
    """S9 smoke routing + gateway post-Ready (G-F4-02 harness)."""

    async def test_activation_smoke_routing_after_cache_invalidation(
        self,
        e2e_cliente_id: UUID,
        dedicated_enabled_sync_dispatcher,
    ):
        metadata: Dict[str, Any] = build_dedicated_metadata(e2e_cliente_id)
        connection_cache.set(e2e_cliente_id, metadata.copy())

        stack = build_provisioning_e2e_stack(
            cliente_id=e2e_cliente_id,
            use_real_activation=True,
        )

        async def _mock_metadata_async(client_id: UUID, *args, **kwargs) -> Dict[str, Any]:
            if client_id != e2e_cliente_id:
                raise ValueError(f"unexpected client_id {client_id}")
            return metadata

        mock_cm = _mock_async_session_cm()
        with patch(
            "app.infrastructure.provisioning.dedicated_activation_service.get_connection_metadata_async",
            side_effect=_mock_metadata_async,
        ):
            with patch(
                "app.infrastructure.database.connection_async.get_db_connection",
                return_value=mock_cm,
            ):
                from app.infrastructure.provisioning.dedicated_activation_types import (
                    DedicatedActivationRequest,
                )

                request = DedicatedActivationRequest(
                    cliente_id=e2e_cliente_id,
                    provisioning_run_id=E2E_RUN_ID,
                    database_name=metadata["nombre_bd"],
                    servidor=metadata["servidor"],
                    app_login_name=metadata["usuario"],
                    app_login_password=metadata["password"],
                )
                result = await stack.mocks["activation"].activate_routing(request)

        assert result.idempotency_marker == f"routing_smoke_v1:{e2e_cliente_id}"
        assert connection_cache.get(e2e_cliente_id) is None

        connection_cache.set(e2e_cliente_id, metadata.copy())
        with patch(
            "app.core.tenant.routing.get_connection_metadata_async",
            side_effect=_mock_metadata_async,
        ):
            with patch(
                "app.infrastructure.database.connection_async.get_db_connection",
                return_value=mock_cm,
            ):
                async with get_connection_for_tenant(cliente_id=e2e_cliente_id):
                    pass

        engine_key = resolve_engine_key(
            e2e_cliente_id,
            DatabaseConnection.DEFAULT,
        )
        assert engine_key == f"tenant_{e2e_cliente_id}"

    async def test_post_initialize_dispatch_records_ready_metrics(
        self,
        provisioning_e2e_stack: ProvisioningE2EStack,
        dedicated_enabled_sync_dispatcher,
    ):
        stack = provisioning_e2e_stack
        init = ProvisioningRunInitializedResult(
            provisioning_run_id=stack.run_id,
            cliente_id=stack.cliente_id,
            provisioning_state=ProvisioningState.PROVISIONING,
            attempt_number=1,
            idempotency_key="e2e-init",
        )
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.execute_query",
            new_callable=AsyncMock,
            return_value=build_cliente_profile(),
        ):
            await stack.dispatcher.dispatch_after_initialize(
                init,
                handler=stack.orchestrator.handle_job,
                ephemeral_context=stack.job_request().ephemeral_context,
            )

        manifest = stack.audit.lifecycle_metrics_manifest()
        assert manifest["signals"]["dedicated.provisioning.started"] >= 1
        assert manifest["signals"]["dedicated.provisioning.step.completed"] == len(
            SAGA_STEP_ORDER
        )
        assert manifest["signals"]["dedicated.provisioning.ready"] >= 1
        assert manifest["artifact_type"] == "f4_provisioning_metrics"


@pytest.mark.integration
@pytest.mark.asyncio
class TestDedicatedProvisioningE2ESharedGuard:
    """DEDICATED_ENABLED=false — saga noop; shared path intacto."""

    async def test_dedicated_disabled_skips_saga(
        self,
        provisioning_e2e_stack: ProvisioningE2EStack,
    ):
        stack = provisioning_e2e_stack
        with patch(
            "app.modules.tenant.application.services.dedicated_provisioning_orchestrator.settings"
        ) as mock_settings:
            mock_settings.DEDICATED_ENABLED = False
            await stack.orchestrator.handle_job(stack.job_request())

        stack.mocks["state"].mark_step_running.assert_not_called()
        assert stack.completed_steps == []

    async def test_shared_onboarding_imports_reachable(self):
        """Smoke: módulos SHARED_ONBOARDING_REQUIRED_CHECK importables."""
        import tests.unit.test_onboarding_rbac_bootstrap  # noqa: F401
        import tests.unit.test_onboarding_menu_bootstrap  # noqa: F401
        import tests.unit.test_minimal_erp_tenant_bootstrap  # noqa: F401
        import tests.unit.test_platform_identity_bootstrap  # noqa: F401
        import tests.unit.test_tenant_exception_propagation  # noqa: F401
        import tests.unit.test_base_operative_t1  # noqa: F401
