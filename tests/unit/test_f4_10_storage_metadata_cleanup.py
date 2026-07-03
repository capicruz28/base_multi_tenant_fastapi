"""PR-F4-10 — cleanup metadata S8."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.infrastructure.provisioning.dedicated_storage_metadata_service import (
    DedicatedStorageMetadataService,
)
from app.modules.tenant.presentation.schemas import ConexionRead

CLIENTE_ID = uuid4()
CONEXION_ID = uuid4()


def _conexion_read(*, active: bool = True) -> ConexionRead:
    return ConexionRead(
        conexion_id=CONEXION_ID,
        cliente_id=CLIENTE_ID,
        servidor="sql.local",
        puerto=1433,
        nombre_bd="erp_acme001",
        tipo_bd="sqlserver",
        usa_ssl=False,
        timeout_segundos=30,
        max_pool_size=100,
        es_solo_lectura=False,
        es_conexion_principal=True,
        es_activo=active,
        ultima_conexion_exitosa=None,
        ultimo_error=None,
        fecha_ultimo_error=None,
        fecha_creacion="2026-01-01T00:00:00",
        fecha_actualizacion=None,
        creado_por_usuario_id=None,
        usuario_encriptado="enc_u",
        password_encriptado="enc_p",
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_cleanup_deactivates_primary_connection():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=_conexion_read(),
    ):
        with patch(
            "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.desactivar_conexion",
            new_callable=AsyncMock,
            return_value=_conexion_read(active=False),
        ) as mock_deactivate:
            result = await service.cleanup_primary_connection(CLIENTE_ID)

    assert result is True
    mock_deactivate.assert_called_once_with(CONEXION_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_cleanup_idempotent_when_missing():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await service.cleanup_primary_connection(CLIENTE_ID)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_cleanup_idempotent_when_already_inactive():
    service = DedicatedStorageMetadataService()
    with patch(
        "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.obtener_conexion_principal",
        new_callable=AsyncMock,
        return_value=_conexion_read(),
    ):
        with patch(
            "app.infrastructure.provisioning.dedicated_storage_metadata_service.ConexionService.desactivar_conexion",
            new_callable=AsyncMock,
            side_effect=ValidationError(
                detail="ya desactivada",
                internal_code="CONNECTION_ALREADY_INACTIVE",
            ),
        ):
            result = await service.cleanup_primary_connection(CLIENTE_ID)
    assert result is False
