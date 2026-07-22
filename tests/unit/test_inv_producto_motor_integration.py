"""Fase A — inv_producto integración con motor de códigos (codigo_sku)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.inv.application.services import producto_service
from app.modules.inv.presentation.schemas import ProductoCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
PRODUCTO_ID = uuid4()
USUARIO_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()
MONEDA_ID = uuid4()


def _producto_create(*, codigo_sku: str | None = "P00001") -> ProductoCreate:
    return ProductoCreate(
        empresa_id=EMPRESA_ID,
        codigo_sku=codigo_sku,
        nombre="Producto test",
        tipo_producto="bien",
        unidad_medida_base_id=UNIDAD_MEDIDA_ID,
        moneda_costo=MONEDA_ID,
        moneda_venta=MONEDA_ID,
    )


def _producto_row(codigo_sku: str) -> dict:
    return {
        "producto_id": PRODUCTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo_sku": codigo_sku,
        "nombre": "Producto test",
        "tipo_producto": "BIEN",
        "unidad_medida_base_id": UNIDAD_MEDIDA_ID,
        "moneda_costo": MONEDA_ID,
        "moneda_venta": MONEDA_ID,
        "es_activo": True,
        "usuario_creacion_id": USUARIO_ID,
    }


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_auto_generate_without_codigo_sku():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku=None)

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ) as mock_get_conn:
                    with patch(
                        "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        return_value="P00001",
                    ) as mock_resolve:
                        with patch(
                            "app.modules.inv.application.services.producto_service.create_producto",
                            new_callable=AsyncMock,
                            return_value=_producto_row("P00001"),
                        ) as mock_create:
                            result = await producto_service.create_producto_servicio(
                                client_id=CLIENT_ID,
                                data=data,
                                usuario_id=USUARIO_ID,
                            )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    session.begin.assert_called_once()
    mock_resolve.assert_awaited_once_with(
        "inv_producto",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["codigo_sku"] == "P00001"
    assert mock_create.await_args.kwargs["data"]["usuario_creacion_id"] == USUARIO_ID
    assert result.codigo_sku == "P00001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_manual_codigo_sku_accepted():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku="SKU999")

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ):
                    with patch(
                        "app.modules.inv.application.services.producto_service.get_producto_by_sku",
                        new_callable=AsyncMock,
                        return_value=None,
                    ) as mock_dup:
                        with patch(
                            "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                            new_callable=AsyncMock,
                            return_value="SKU999",
                        ) as mock_resolve:
                            with patch(
                                "app.modules.inv.application.services.producto_service.create_producto",
                                new_callable=AsyncMock,
                                return_value=_producto_row("SKU999"),
                            ):
                                result = await producto_service.create_producto_servicio(
                                    client_id=CLIENT_ID, data=data
                                )

    mock_dup.assert_awaited_once_with(
        CLIENT_ID, EMPRESA_ID, "SKU999", session=session
    )
    mock_resolve.assert_awaited_once_with(
        "inv_producto",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code="SKU999",
    )
    assert result.codigo_sku == "SKU999"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_duplicate_manual_raises_conflict():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku="P00001")

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ):
                    with patch(
                        "app.modules.inv.application.services.producto_service.get_producto_by_sku",
                        new_callable=AsyncMock,
                        return_value=_producto_row("P00001"),
                    ):
                        with patch(
                            "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                            new_callable=AsyncMock,
                        ) as mock_resolve:
                            with pytest.raises(ConflictError):
                                await producto_service.create_producto_servicio(
                                    client_id=CLIENT_ID, data=data
                                )

    mock_resolve.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_cfg_missing_propagates():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku=None)

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ):
                    with patch(
                        "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        side_effect=NotFoundError(
                            detail="Configuración de secuencia no encontrada.",
                            internal_code="CFG_SEQUENCE_NOT_FOUND",
                        ),
                    ):
                        with patch(
                            "app.modules.inv.application.services.producto_service.create_producto",
                            new_callable=AsyncMock,
                        ) as mock_create:
                            with pytest.raises(NotFoundError):
                                await producto_service.create_producto_servicio(
                                    client_id=CLIENT_ID, data=data
                                )

    mock_create.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_single_transaction_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku=None)

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ):
                    with patch(
                        "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        return_value="P00002",
                    ):
                        with patch(
                            "app.modules.inv.application.services.producto_service.create_producto",
                            new_callable=AsyncMock,
                            return_value=_producto_row("P00002"),
                        ):
                            await producto_service.create_producto_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    session.begin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _producto_create(codigo_sku="P00001")

    with patch(
        "app.modules.inv.application.services.producto_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.get_connection_for_tenant",
                    return_value=_session_context_manager(session),
                ):
                    with patch(
                        "app.modules.inv.application.services.producto_service.get_producto_by_sku",
                        new_callable=AsyncMock,
                        return_value=_producto_row("P00001"),
                    ):
                        with patch(
                            "app.modules.inv.application.services.producto_service.create_producto",
                            new_callable=AsyncMock,
                        ) as mock_create:
                            with pytest.raises(ConflictError):
                                await producto_service.create_producto_servicio(
                                    client_id=CLIENT_ID, data=data
                                )

    session.begin.assert_called_once()
    mock_create.assert_not_called()


@pytest.mark.unit
def test_producto_create_schema_accepts_missing_codigo_sku():
    data = ProductoCreate(
        empresa_id=EMPRESA_ID,
        nombre="Producto test",
        tipo_producto="bien",
        unidad_medida_base_id=UNIDAD_MEDIDA_ID,
        moneda_costo=MONEDA_ID,
        moneda_venta=MONEDA_ID,
    )
    assert data.codigo_sku is None
