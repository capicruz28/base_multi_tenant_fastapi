"""
Tests unitarios — INV-P0-004: helpers A-01–A-05, servicios A-10–A-17 (cobertura Etapa 5).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import (
    categoria_service,
    inventario_fisico_service,
    movimiento_service,
    producto_service,
)
from app.modules.inv.application.services.inv_audit_context import (
    apply_create_audit,
    apply_producto_update_audit,
)
from app.modules.inv.presentation.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    InventarioFisicoConDetalleCreate,
    InventarioFisicoCreate,
    InventarioFisicoDetalleCreateEmbebido,
    MovimientoConDetalleCreate,
    MovimientoCreate,
    MovimientoDetalleCreateEmbebido,
    ProductoCreate,
    ProductoUpdate,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
USUARIO_ID = uuid4()
OTRO_USUARIO_ID = uuid4()
CATEGORIA_ID = uuid4()
PRODUCTO_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()
MONEDA_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
MOVIMIENTO_ID = uuid4()
ALMACEN_ID = uuid4()
INVENTARIO_FISICO_ID = uuid4()


class _FakeUowContext:
    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


def _set_empresa_ctx(empresa_id):
    return set_current_empresa_id(empresa_id)


@pytest.mark.unit
def test_a01_apply_create_audit_asigna_usuario_creacion_id():
    payload = {"codigo": "CAT-01", "nombre": "Categoría"}
    result = apply_create_audit(payload, USUARIO_ID)
    assert result["usuario_creacion_id"] == USUARIO_ID
    assert "usuario_creacion_id" not in payload


@pytest.mark.unit
def test_a02_apply_create_audit_usuario_id_none_deja_none():
    payload = {"codigo": "CAT-01"}
    result = apply_create_audit(payload, None)
    assert result["usuario_creacion_id"] is None


@pytest.mark.unit
def test_a03_apply_create_audit_sobrescribe_valor_previo_en_payload():
    payload = {"codigo": "CAT-01", "usuario_creacion_id": OTRO_USUARIO_ID}
    result = apply_create_audit(payload, USUARIO_ID)
    assert result["usuario_creacion_id"] == USUARIO_ID
    assert result["usuario_creacion_id"] != OTRO_USUARIO_ID
    assert payload["usuario_creacion_id"] == OTRO_USUARIO_ID


@pytest.mark.unit
def test_a04_apply_producto_update_audit_asigna_usuario_actualizacion_id():
    payload = {"nombre": "Producto actualizado"}
    result = apply_producto_update_audit(payload, USUARIO_ID)
    assert result["usuario_actualizacion_id"] == USUARIO_ID
    assert "usuario_actualizacion_id" not in payload


@pytest.mark.unit
def test_a05_apply_producto_update_audit_usuario_id_none_no_asigna_campo():
    payload = {"nombre": "Producto", "usuario_actualizacion_id": OTRO_USUARIO_ID}
    result = apply_producto_update_audit(payload, None)
    assert "usuario_actualizacion_id" not in result
    assert payload["usuario_actualizacion_id"] == OTRO_USUARIO_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a10_create_categoria_servicio_persiste_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    data = CategoriaCreate(empresa_id=EMPRESA_ID, codigo="CAT-AUD", nombre="Categoría audit")
    row = {
        "categoria_id": CATEGORIA_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT-AUD",
        "nombre": "Categoría audit",
        "es_activo": True,
        "usuario_creacion_id": USUARIO_ID,
    }
    try:
        with patch(
            "app.modules.inv.application.services.categoria_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.categoria_service.create_categoria",
            new=AsyncMock(return_value=row),
        ) as mock_create:
            await categoria_service.create_categoria_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] == USUARIO_ID
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a11_create_producto_servicio_persiste_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    data = ProductoCreate(
        empresa_id=EMPRESA_ID,
        codigo_sku="SKU-AUD",
        nombre="Producto audit",
        tipo_producto="bien",
        unidad_medida_base_id=UNIDAD_MEDIDA_ID,
        moneda_costo=MONEDA_ID,
        moneda_venta=MONEDA_ID,
    )
    row = {
        "producto_id": PRODUCTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo_sku": "SKU-AUD",
        "nombre": "Producto audit",
        "tipo_producto": "bien",
        "unidad_medida_base_id": UNIDAD_MEDIDA_ID,
        "moneda_costo": MONEDA_ID,
        "moneda_venta": MONEDA_ID,
        "es_activo": True,
        "usuario_creacion_id": USUARIO_ID,
    }
    try:
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_sku",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.producto_service.create_producto",
            new=AsyncMock(return_value=row),
        ) as mock_create:
            await producto_service.create_producto_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] == USUARIO_ID
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a12_update_producto_servicio_persiste_usuario_actualizacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    existing = {
        "producto_id": PRODUCTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo_sku": "SKU-AUD",
        "nombre": "Producto audit",
        "tipo_producto": "bien",
        "unidad_medida_base_id": UNIDAD_MEDIDA_ID,
        "moneda_costo": MONEDA_ID,
        "moneda_venta": MONEDA_ID,
        "es_activo": True,
    }
    updated = {**existing, "nombre": "Producto actualizado", "usuario_actualizacion_id": USUARIO_ID}
    try:
        with patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_id",
            new=AsyncMock(return_value=existing),
        ), patch(
            "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.producto_service.update_producto",
            new=AsyncMock(return_value=updated),
        ) as mock_update:
            await producto_service.update_producto_servicio(
                client_id=CLIENT_ID,
                producto_id=PRODUCTO_ID,
                data=ProductoUpdate(nombre="Producto actualizado"),
                usuario_id=USUARIO_ID,
            )
            payload = mock_update.await_args.kwargs["data"]
            assert payload["usuario_actualizacion_id"] == USUARIO_ID
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a16_update_categoria_servicio_no_escribe_usuario_actualizacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    existing = {
        "categoria_id": CATEGORIA_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT-AUD",
        "nombre": "Categoría audit",
        "es_activo": True,
    }
    updated = {**existing, "nombre": "Categoría renombrada"}
    try:
        with patch(
            "app.modules.inv.application.services.categoria_service.get_categoria_by_id",
            new=AsyncMock(return_value=existing),
        ), patch(
            "app.modules.inv.application.services.categoria_service.update_categoria",
            new=AsyncMock(return_value=updated),
        ) as mock_update:
            await categoria_service.update_categoria_servicio(
                client_id=CLIENT_ID,
                categoria_id=CATEGORIA_ID,
                data=CategoriaUpdate(nombre="Categoría renombrada"),
                usuario_id=USUARIO_ID,
            )
            payload = mock_update.await_args.kwargs["data"]
            assert "usuario_actualizacion_id" not in payload
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a13_create_movimiento_servicio_persiste_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    data = MovimientoCreate(
        empresa_id=EMPRESA_ID,
        numero_movimiento="MOV-AUD-001",
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
    )
    row = {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-AUD-001",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": datetime.utcnow(),
        "fecha_contable": date(2026, 6, 12),
        "estado": "borrador",
        "moneda_id": MONEDA_ID,
        "usuario_creacion_id": USUARIO_ID,
    }
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._resolve_moneda_id",
            new=AsyncMock(return_value=MONEDA_ID),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.create_movimiento",
            new=AsyncMock(return_value=row),
        ) as mock_create:
            await movimiento_service.create_movimiento_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] == USUARIO_ID
            assert payload["estado"] == "borrador"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a15_create_movimiento_con_detalles_servicio_cabecera_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    detalle = MovimientoDetalleCreateEmbebido(
        producto_id=PRODUCTO_ID,
        cantidad=Decimal("5"),
        unidad_medida_id=UNIDAD_MEDIDA_ID,
        cantidad_base=Decimal("5"),
        costo_unitario=Decimal("10"),
    )
    data = MovimientoConDetalleCreate(
        empresa_id=EMPRESA_ID,
        numero_movimiento="MOV-AUD-002",
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
        detalles=[detalle],
    )
    cab_row = {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": "MOV-AUD-002",
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": datetime.utcnow(),
        "fecha_contable": date(2026, 6, 12),
        "estado": "borrador",
        "moneda_id": MONEDA_ID,
        "usuario_creacion_id": USUARIO_ID,
    }
    det_row = {
        "movimiento_detalle_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "movimiento_id": MOVIMIENTO_ID,
        "producto_id": PRODUCTO_ID,
        "cantidad": Decimal("5"),
        "unidad_medida_id": UNIDAD_MEDIDA_ID,
        "cantidad_base": Decimal("5"),
        "costo_unitario": Decimal("10"),
        "moneda_id": MONEDA_ID,
    }
    inserted_cabecera: dict = {}

    def _extract_insert_values(stmt) -> dict:
        return {
            key: (param.value if hasattr(param, "value") else param)
            for key, param in stmt._values.items()
        }

    async def _fake_execute(stmt):
        if (
            not inserted_cabecera
            and hasattr(stmt, "table")
            and stmt.table.name == "inv_movimiento"
        ):
            inserted_cabecera.update(_extract_insert_values(stmt))
            return {"rows_affected": 1}
        if hasattr(stmt, "table") and stmt.table.name == "inv_movimiento_detalle":
            return {"rows_affected": 1}
        compiled = str(stmt)
        if "inv_movimiento" in compiled and "inv_movimiento_detalle" not in compiled:
            return [cab_row]
        return [det_row]

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)

    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._validate_detalle_embebido_line",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service._resolve_moneda_id",
            new=AsyncMock(return_value=MONEDA_ID),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await movimiento_service.create_movimiento_con_detalles_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
        assert inserted_cabecera["usuario_creacion_id"] == USUARIO_ID
        assert inserted_cabecera["estado"] == "borrador"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a14_create_inventario_fisico_servicio_persiste_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    data = InventarioFisicoCreate(
        empresa_id=EMPRESA_ID,
        numero_inventario="INV-AUD-001",
        fecha_inventario=date(2026, 6, 12),
        almacen_id=ALMACEN_ID,
        tipo_inventario="total",
    )
    row = {
        "inventario_fisico_id": INVENTARIO_FISICO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-AUD-001",
        "fecha_inventario": date(2026, 6, 12),
        "almacen_id": ALMACEN_ID,
        "tipo_inventario": "total",
        "estado": "en_proceso",
        "usuario_creacion_id": USUARIO_ID,
    }
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.create_inventario_fisico",
            new=AsyncMock(return_value=row),
        ) as mock_create:
            await inventario_fisico_service.create_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] == USUARIO_ID
            assert payload["estado"] == "en_proceso"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a14_create_inventario_fisico_con_detalles_cabecera_usuario_creacion_id():
    token = _set_empresa_ctx(EMPRESA_ID)
    detalle = InventarioFisicoDetalleCreateEmbebido(
        producto_id=PRODUCTO_ID,
        cantidad_sistema=Decimal("10"),
        cantidad_contada=Decimal("9"),
    )
    data = InventarioFisicoConDetalleCreate(
        empresa_id=EMPRESA_ID,
        numero_inventario="INV-AUD-002",
        fecha_inventario=date(2026, 6, 12),
        almacen_id=ALMACEN_ID,
        tipo_inventario="total",
        detalles=[detalle],
    )
    cab_row = {
        "inventario_fisico_id": INVENTARIO_FISICO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-AUD-002",
        "fecha_inventario": date(2026, 6, 12),
        "almacen_id": ALMACEN_ID,
        "tipo_inventario": "total",
        "estado": "en_proceso",
        "usuario_creacion_id": USUARIO_ID,
    }
    det_row = {
        "inventario_fisico_detalle_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "inventario_fisico_id": INVENTARIO_FISICO_ID,
        "producto_id": PRODUCTO_ID,
        "cantidad_sistema": Decimal("10"),
        "cantidad_contada": Decimal("9"),
        "estado_conteo": "pendiente",
    }
    inserted_cabecera: dict = {}

    def _extract_insert_values(stmt) -> dict:
        return {
            key: (param.value if hasattr(param, "value") else param)
            for key, param in stmt._values.items()
        }

    async def _fake_execute(stmt):
        if (
            not inserted_cabecera
            and hasattr(stmt, "table")
            and stmt.table.name == "inv_inventario_fisico"
        ):
            inserted_cabecera.update(_extract_insert_values(stmt))
            return {"rows_affected": 1}
        if hasattr(stmt, "table") and stmt.table.name == "inv_inventario_fisico_detalle":
            return {"rows_affected": 1}
        compiled = str(stmt)
        if "inv_inventario_fisico" in compiled and "inv_inventario_fisico_detalle" not in compiled:
            return [cab_row]
        return [det_row]

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(side_effect=_fake_execute)

    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_cabecera_refs",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_detalle_productos",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            await inventario_fisico_service.create_inventario_fisico_con_detalles_servicio(
                client_id=CLIENT_ID,
                data=data,
                usuario_id=USUARIO_ID,
            )
        assert inserted_cabecera["usuario_creacion_id"] == USUARIO_ID
        assert inserted_cabecera["estado"] == "en_proceso"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_a17_create_categoria_servicio_sin_usuario_id_deja_usuario_creacion_none():
    """Llamada interna sin usuario_id → usuario_creacion_id=None (regresión NULL)."""
    token = _set_empresa_ctx(EMPRESA_ID)
    data = CategoriaCreate(empresa_id=EMPRESA_ID, codigo="CAT-NULL", nombre="Sin usuario")
    row = {
        "categoria_id": CATEGORIA_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT-NULL",
        "nombre": "Sin usuario",
        "es_activo": True,
        "usuario_creacion_id": None,
    }
    try:
        with patch(
            "app.modules.inv.application.services.categoria_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.categoria_service.create_categoria",
            new=AsyncMock(return_value=row),
        ) as mock_create:
            await categoria_service.create_categoria_servicio(
                client_id=CLIENT_ID,
                data=data,
            )
            payload = mock_create.await_args.kwargs["data"]
            assert payload["usuario_creacion_id"] is None
    finally:
        reset_current_empresa_id(token)
