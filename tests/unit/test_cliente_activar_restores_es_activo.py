"""F-001: activar_cliente restores es_activo after soft delete."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.tenant.application.services.cliente_service import ClienteService


def _cliente_stub(*, cliente_id, es_activo: bool, estado_suscripcion: str) -> MagicMock:
    stub = MagicMock()
    stub.cliente_id = cliente_id
    stub.es_activo = es_activo
    stub.estado_suscripcion = estado_suscripcion
    return stub


@pytest.mark.asyncio
async def test_activar_cliente_sets_es_activo_after_cancelado():
    cliente_id = uuid4()
    row_after = {
        "cliente_id": cliente_id,
        "codigo_cliente": "T001",
        "subdominio": "t001",
        "razon_social": "Tenant QA",
        "nombre_comercial": None,
        "ruc": None,
        "tipo_instalacion": "shared",
        "servidor_api_local": None,
        "modo_autenticacion": "local",
        "logo_url": None,
        "favicon_url": None,
        "color_primario": "#1976D2",
        "color_secundario": "#424242",
        "tema_personalizado": None,
        "plan_suscripcion": "trial",
        "estado_suscripcion": "activo",
        "fecha_inicio_suscripcion": None,
        "fecha_fin_trial": None,
        "contacto_nombre": None,
        "contacto_email": "a@b.com",
        "contacto_telefono": None,
        "es_activo": True,
        "es_demo": False,
        "metadata_json": None,
        "api_key_sincronizacion": None,
        "sincronizacion_habilitada": False,
        "ultima_sincronizacion": None,
        "fecha_creacion": datetime.now(timezone.utc),
        "fecha_actualizacion": datetime.now(timezone.utc),
        "fecha_ultimo_acceso": None,
    }
    with (
        patch.object(
            ClienteService,
            "obtener_cliente_por_id",
            new_callable=AsyncMock,
            return_value=_cliente_stub(
                cliente_id=cliente_id,
                es_activo=False,
                estado_suscripcion="cancelado",
            ),
        ),
        patch(
            "app.modules.tenant.application.services.cliente_service.execute_update",
            new_callable=AsyncMock,
            return_value=row_after,
        ) as mock_update,
    ):
        result = await ClienteService.activar_cliente(cliente_id)

    assert result.es_activo is True
    assert result.estado_suscripcion == "activo"
    sql = mock_update.await_args[0][0]
    assert "es_activo = 1" in sql
    assert "estado_suscripcion = 'activo'" in sql


@pytest.mark.asyncio
async def test_activar_cliente_suspendido_not_already_active():
    """Suspendido (es_activo=1) debe poder activarse sin CLIENT_ALREADY_ACTIVE."""
    cliente_id = uuid4()
    stub = _cliente_stub(
        cliente_id=cliente_id,
        es_activo=True,
        estado_suscripcion="suspendido",
    )
    with patch.object(
        ClienteService,
        "obtener_cliente_por_id",
        new_callable=AsyncMock,
        return_value=stub,
    ):
        with patch(
            "app.modules.tenant.application.services.cliente_service.execute_update",
            new_callable=AsyncMock,
        ) as mock_update:
            mock_update.return_value = {"cliente_id": cliente_id, "es_activo": True, "estado_suscripcion": "activo"}
            with patch(
                "app.modules.tenant.application.services.cliente_service.ClienteRead",
                return_value=MagicMock(es_activo=True, estado_suscripcion="activo"),
            ):
                await ClienteService.activar_cliente(cliente_id)
    mock_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_activar_cliente_already_active_raises():
    cliente_id = uuid4()
    with patch.object(
        ClienteService,
        "obtener_cliente_por_id",
        new_callable=AsyncMock,
        return_value=_cliente_stub(
            cliente_id=cliente_id,
            es_activo=True,
            estado_suscripcion="activo",
        ),
    ):
        with pytest.raises(ValidationError) as exc:
            await ClienteService.activar_cliente(cliente_id)

    assert exc.value.internal_code == "CLIENT_ALREADY_ACTIVE"
