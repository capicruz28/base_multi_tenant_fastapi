"""PR-F4-09 — tests unitarios DedicatedStorageMetadataService."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.infrastructure.provisioning.dedicated_storage_metadata_service import (
    DedicatedStorageMetadataService,
)
from app.infrastructure.provisioning.dedicated_storage_metadata_types import (
    DedicatedStorageMetadataRequest,
)
from app.modules.tenant.presentation.schemas import ConexionRead

CLIENTE_ID = uuid4()
RUN_ID = uuid4()
CONEXION_ID = uuid4()


def _request() -> DedicatedStorageMetadataRequest:
    return DedicatedStorageMetadataRequest(
        cliente_id=CLIENTE_ID,
        provisioning_run_id=RUN_ID,
        servidor="sql.local",
        database_name="erp_acme001",
        app_login_name="erpapp_acme001",
        app_login_password="Secret123!",
        puerto=1433,
    )


def _conexion_read(**overrides) -> ConexionRead:
    base = {
        "conexion_id": CONEXION_ID,
        "cliente_id": CLIENTE_ID,
        "servidor": "sql.local",
        "puerto": 1433,
        "nombre_bd": "erp_acme001",
        "tipo_bd": "sqlserver",
        "usa_ssl": False,
        "timeout_segundos": 30,
        "max_pool_size": 100,
        "es_solo_lectura": False,
        "es_conexion_principal": True,
        "es_activo": True,
        "ultima_conexion_exitosa": None,
        "ultimo_error": None,
        "fecha_ultimo_error": None,
        "fecha_creacion": "2026-01-01T00:00:00",
        "fecha_actualizacion": None,
        "creado_por_usuario_id": None,
        "usuario_encriptado": "enc_user",
        "password_encriptado": "enc_pass",
    }
    base.update(overrides)
    return ConexionRead(**base)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s8_creates_primary_connection_when_missing():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_get:
        with patch(
            "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.crear_conexion",
            new_callable=AsyncMock,
            return_value=_conexion_read(),
        ) as mock_create:
            result = await service.register_primary_connection(_request())

    mock_get.assert_called_once_with(CLIENTE_ID)
    mock_create.assert_called_once()
    assert result.created is True
    assert result.idempotent is False
    assert result.conexion_id == CONEXION_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s8_idempotent_when_principal_exists():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=_conexion_read(),
    ):
        with patch(
            "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.crear_conexion",
            new_callable=AsyncMock,
        ) as mock_create:
            result = await service.register_primary_connection(_request())

    mock_create.assert_not_called()
    assert result.idempotent is True
    assert result.created is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s8_rejects_mismatched_existing_principal():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=_conexion_read(nombre_bd="erp_other"),
    ):
        with pytest.raises(ConflictError) as exc_info:
            await service.register_primary_connection(_request())
    assert exc_info.value.internal_code == "PROVISIONING_METADATA_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_09_s8_race_primary_conflict_recovers_idempotently():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        side_effect=[None, _conexion_read()],
    ):
        with patch(
            "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.crear_conexion",
            new_callable=AsyncMock,
            side_effect=ConflictError(
                detail="Ya existe principal",
                internal_code="PRIMARY_CONNECTION_CONFLICT",
            ),
        ):
            result = await service.register_primary_connection(_request())

    assert result.idempotent is True
    assert result.conexion_id == CONEXION_ID
