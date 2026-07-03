"""PR-F4-08 — wiring mínimo cliente_service dedicated."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.tenant.application.provisioning import (
    ProvisioningRunInitializedResult,
    ProvisioningState,
)
from app.modules.tenant.application.services.cliente_service import ClienteService
from app.modules.tenant.presentation.schemas import ClienteCreate

CLIENTE_ID = uuid4()
RUN_ID = uuid4()


def _cliente_create_dedicated() -> ClienteCreate:
    return ClienteCreate(
        codigo_cliente="DED001",
        subdominio="ded001",
        razon_social="Dedicated Corp",
        contacto_email="admin@ded.test",
        tipo_instalacion="dedicated",
        plan_suscripcion="trial",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_crear_cliente_dedicated_dispatches_saga():
    cliente_row = {
        "cliente_id": CLIENTE_ID,
        "codigo_cliente": "DED001",
        "subdominio": "ded001",
        "razon_social": "Dedicated Corp",
        "nombre_comercial": None,
        "ruc": None,
        "plan_suscripcion": "trial",
        "tipo_instalacion": "dedicated",
        "estado_suscripcion": "activo",
        "es_activo": True,
        "fecha_creacion": datetime.utcnow(),
        "fecha_actualizacion": None,
        "contacto_email": "admin@ded.test",
        "contacto_nombre": None,
        "contacto_telefono": None,
        "color_primario": "#1976D2",
        "color_secundario": "#424242",
    }
    init_result = ProvisioningRunInitializedResult(
        provisioning_run_id=RUN_ID,
        cliente_id=CLIENTE_ID,
        provisioning_state=ProvisioningState.PROVISIONING,
        attempt_number=1,
        idempotency_key="ded-key",
    )

    mock_session = AsyncMock()
    mock_begin = MagicMock()
    mock_begin.__aenter__ = AsyncMock(return_value=None)
    mock_begin.__aexit__ = AsyncMock(return_value=None)
    mock_session.begin = MagicMock(return_value=mock_begin)

    with patch(
        "app.modules.tenant.application.services.cliente_service.settings"
    ) as mock_settings:
        mock_settings.DEDICATED_ENABLED = True
        with patch(
            "app.modules.tenant.application.services.cliente_service.ClienteService._validar_subdominio_cliente",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.tenant.application.services.cliente_service.ClienteService._validar_codigo_cliente",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.tenant.application.services.cliente_service.get_db_connection"
                ) as mock_get_db:
                    mock_get_db.return_value.__aenter__ = AsyncMock(
                        return_value=mock_session
                    )
                    mock_get_db.return_value.__aexit__ = AsyncMock(return_value=None)
                    with patch(
                        "app.modules.tenant.application.services.cliente_service.ClienteOnboardingService._insertar_cliente",
                        new_callable=AsyncMock,
                        return_value=cliente_row,
                    ):
                        with patch(
                            "app.modules.tenant.application.services.cliente_service.generar_contrasena_segura",
                            return_value="TempPass123!",
                        ):
                            with patch(
                                "app.modules.tenant.application.services.cliente_service.TenantProvisioningStateService"
                            ) as mock_state_cls:
                                state = AsyncMock()
                                state.initialize_provisioning_run.return_value = init_result
                                mock_state_cls.return_value = state
                                with patch(
                                    "app.modules.tenant.application.services.cliente_service.ProvisioningJobDispatcher"
                                ) as mock_dispatcher_cls:
                                    dispatcher = AsyncMock()
                                    mock_dispatcher_cls.return_value = dispatcher
                                    with patch(
                                        "app.modules.tenant.application.services.cliente_service.ClienteOnboardingService.crear_cliente_con_onboarding",
                                        new_callable=AsyncMock,
                                    ) as mock_shared:
                                        result = await ClienteService.crear_cliente(
                                            _cliente_create_dedicated(),
                                        )

    mock_shared.assert_not_called()
    state.initialize_provisioning_run.assert_called_once_with(cliente_id=CLIENTE_ID)
    dispatcher.dispatch_after_initialize.assert_called_once()
    dispatch_kwargs = dispatcher.dispatch_after_initialize.call_args.kwargs
    assert dispatch_kwargs["trigger_source"] == "post_create_cliente"
    assert dispatch_kwargs["ephemeral_context"].admin_password == "TempPass123!"
    assert result.credenciales.contrasena == "TempPass123!"
    assert result.credenciales.nombre_usuario == "admin"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_08_crear_cliente_dedicated_disabled_uses_shared_onboarding():
    with patch(
        "app.modules.tenant.application.services.cliente_service.settings"
    ) as mock_settings:
        mock_settings.DEDICATED_ENABLED = False
        with patch(
            "app.modules.tenant.application.services.cliente_service.ClienteService._validar_subdominio_cliente",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.tenant.application.services.cliente_service.ClienteService._validar_codigo_cliente",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.tenant.application.services.cliente_service.ClienteOnboardingService.crear_cliente_con_onboarding",
                    new_callable=AsyncMock,
                ) as mock_shared:
                    mock_shared.return_value = MagicMock()
                    await ClienteService.crear_cliente(_cliente_create_dedicated())
                    mock_shared.assert_called_once()
