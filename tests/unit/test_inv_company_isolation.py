"""
Tests de aislamiento multi-empresa (INV — fase 0, 1 y 2).

Valida company_scope y servicios INV con aislamiento por empresa de sesión.
"""
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    reject_client_empresa_override,
    assert_row_empresa,
)
from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id
from app.modules.inv.application.services import (
    categoria_service,
    unidad_medida_service,
    tipo_movimiento_service,
    almacen_service,
    producto_service,
    stock_service,
    movimiento_service,
    movimiento_detalle_service,
    movimiento_proceso_service,
    inventario_fisico_service,
    inventario_fisico_detalle_service,
    inventario_fisico_aprobacion_service,
    kardex_service,
)
from app.modules.inv.presentation.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    UnidadMedidaCreate,
    TipoMovimientoCreate,
    AlmacenCreate,
    AlmacenUpdate,
    ProductoUpdate,
    StockCreate,
    MovimientoDetalleCreate,
    MovimientoDetalleUpdate,
)


EMPRESA_A = uuid4()
EMPRESA_B = uuid4()
CLIENT_ID = uuid4()
CATEGORIA_B = uuid4()
ALMACEN_B = uuid4()
PRODUCTO_B = uuid4()
STOCK_B = uuid4()
PRODUCTO_A = uuid4()
ALMACEN_A = uuid4()
ALMACEN_B_OTHER = uuid4()
MOVIMIENTO_B = uuid4()
MOVIMIENTO_DETALLE_B = uuid4()
MOVIMIENTO_A = uuid4()
INVENTARIO_FISICO_A = uuid4()
INVENTARIO_FISICO_B = uuid4()
INVENTARIO_FISICO_DETALLE_B = uuid4()


def _set_empresa_ctx(empresa_id):
    return set_current_empresa_id(empresa_id)


@pytest.mark.unit
def test_require_session_empresa_id_missing():
  with pytest.raises(AuthorizationError) as exc:
    require_session_empresa_id()
  assert exc.value.status_code == 403
  assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
def test_require_session_empresa_id_ok():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    assert require_session_empresa_id() == EMPRESA_A
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
def test_enforce_body_empresa_mismatch():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with pytest.raises(AuthorizationError) as exc:
      enforce_body_empresa_matches_session(EMPRESA_B)
    assert exc.value.internal_code == "EMPRESA_MISMATCH"
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
def test_reject_client_empresa_override():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with pytest.raises(AuthorizationError) as exc:
      reject_client_empresa_override(EMPRESA_B, source="query")
    assert exc.value.internal_code == "EMPRESA_MISMATCH"
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
def test_assert_row_empresa_cross_company_404():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with pytest.raises(NotFoundError):
      assert_row_empresa(
        {"empresa_id": EMPRESA_B, "categoria_id": CATEGORIA_B},
        EMPRESA_A,
        not_found_detail="Categoría no encontrada",
      )
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_categoria_cross_company_returns_404():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with patch(
      "app.modules.inv.application.services.categoria_service.get_categoria_by_id",
      new=AsyncMock(return_value=None),
    ) as mock_get:
      with pytest.raises(NotFoundError):
        await categoria_service.get_categoria_servicio(
          client_id=CLIENT_ID,
          categoria_id=CATEGORIA_B,
        )
      mock_get.assert_called_once_with(
        client_id=CLIENT_ID,
        categoria_id=CATEGORIA_B,
        empresa_id=EMPRESA_A,
      )
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_categorias_uses_session_empresa_only():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with patch(
      "app.modules.inv.application.services.categoria_service.list_categorias",
      new=AsyncMock(return_value=[]),
    ) as mock_list:
      await categoria_service.list_categorias_servicio(client_id=CLIENT_ID)
      mock_list.assert_called_once_with(
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_A,
        solo_activos=True,
      )
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_categoria_body_mismatch_403():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    data = CategoriaCreate(
      empresa_id=EMPRESA_B,
      codigo="CAT01",
      nombre="Test",
    )
    with pytest.raises(AuthorizationError) as exc:
      await categoria_service.create_categoria_servicio(client_id=CLIENT_ID, data=data)
    assert exc.value.internal_code == "EMPRESA_MISMATCH"
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_categoria_cross_company_404():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with patch(
      "app.modules.inv.application.services.categoria_service.get_categoria_by_id",
      new=AsyncMock(return_value=None),
    ):
      with pytest.raises(NotFoundError):
        await categoria_service.update_categoria_servicio(
          client_id=CLIENT_ID,
          categoria_id=CATEGORIA_B,
          data=CategoriaUpdate(nombre="X"),
        )
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_unidades_medida_without_session_403():
  with pytest.raises(AuthorizationError) as exc:
    await unidad_medida_service.list_unidades_medida_servicio(client_id=CLIENT_ID)
  assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_unidad_medida_passes_empresa_to_query():
  um_id = uuid4()
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    with patch(
      "app.modules.inv.application.services.unidad_medida_service.get_unidad_medida_by_id",
      new=AsyncMock(return_value=None),
    ) as mock_get:
      with pytest.raises(NotFoundError):
        await unidad_medida_service.get_unidad_medida_servicio(
          client_id=CLIENT_ID,
          unidad_medida_id=um_id,
        )
      mock_get.assert_called_once_with(
        client_id=CLIENT_ID,
        unidad_medida_id=um_id,
        empresa_id=EMPRESA_A,
      )
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_tipo_movimiento_enforces_session_empresa():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    data = TipoMovimientoCreate(
      empresa_id=EMPRESA_A,
      codigo="ENT",
      nombre="Entrada",
      clase_movimiento="entrada",
    )
    with patch(
      "app.modules.inv.application.services.tipo_movimiento_service.ensure_empresa_in_tenant",
      new=AsyncMock(),
    ), patch(
      "app.modules.inv.application.services.tipo_movimiento_service.create_tipo_movimiento",
      new=AsyncMock(
        return_value={
          "tipo_movimiento_id": uuid4(),
          "cliente_id": CLIENT_ID,
          "empresa_id": EMPRESA_A,
          "codigo": "ENT",
          "nombre": "Entrada",
          "clase_movimiento": "entrada",
          "es_activo": True,
        }
      ),
    ) as mock_create:
      await tipo_movimiento_service.create_tipo_movimiento_servicio(
        client_id=CLIENT_ID,
        data=data,
      )
      call_payload = mock_create.call_args.kwargs["data"]
      assert call_payload["empresa_id"] == EMPRESA_A
  finally:
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_unidad_medida_body_mismatch_403():
  token = _set_empresa_ctx(EMPRESA_A)
  try:
    data = UnidadMedidaCreate(
      empresa_id=EMPRESA_B,
      codigo="UND",
      nombre="Unidad",
      tipo_unidad="cantidad",
    )
    with pytest.raises(AuthorizationError):
      await unidad_medida_service.create_unidad_medida_servicio(
        client_id=CLIENT_ID,
        data=data,
      )
  finally:
    reset_current_empresa_id(token)


# --- Fase 2: almacenes y productos ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_almacen_cross_company_returns_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.almacen_service.get_almacen_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await almacen_service.get_almacen_servicio(
                    client_id=CLIENT_ID,
                    almacen_id=ALMACEN_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                almacen_id=ALMACEN_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_almacenes_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.almacen_service.list_almacenes",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await almacen_service.list_almacenes_servicio(client_id=CLIENT_ID)
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                sucursal_id=None,
                solo_activos=True,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_body_mismatch_403():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = AlmacenCreate(
            empresa_id=EMPRESA_B,
            codigo="ALM01",
            nombre="Almacén B",
            tipo_almacen="fisico",
        )
        with pytest.raises(AuthorizationError) as exc:
            await almacen_service.create_almacen_servicio(client_id=CLIENT_ID, data=data)
        assert exc.value.internal_code == "EMPRESA_MISMATCH"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_almacen_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.almacen_service.get_almacen_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await almacen_service.update_almacen_servicio(
                    client_id=CLIENT_ID,
                    almacen_id=ALMACEN_B,
                    data=AlmacenUpdate(nombre="X"),
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_almacenes_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await almacen_service.list_almacenes_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_producto_cross_company_returns_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await producto_service.get_producto_servicio(
                    client_id=CLIENT_ID,
                    producto_id=PRODUCTO_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                producto_id=PRODUCTO_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_productos_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.producto_service.list_productos",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await producto_service.list_productos_servicio(client_id=CLIENT_ID, buscar="sku")
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                categoria_id=None,
                tipo_producto=None,
                solo_activos=True,
                buscar="sku",
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_producto_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await producto_service.update_producto_servicio(
                    client_id=CLIENT_ID,
                    producto_id=PRODUCTO_B,
                    data=ProductoUpdate(nombre="X"),
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_productos_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await producto_service.list_productos_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_producto_validates_unidad_medida_same_empresa():
    um_id = uuid4()
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        from app.modules.inv.presentation.schemas import ProductoCreate

        data = ProductoCreate(
            empresa_id=EMPRESA_A,
            codigo_sku="SKU-001",
            nombre="Producto test",
            tipo_producto="bien",
            unidad_medida_base_id=um_id,
            moneda_costo=uuid4(),
            moneda_venta=uuid4(),
        )
        with patch(
            "app.modules.inv.application.services.producto_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_sku",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.producto_service.get_unidad_medida_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_um:
            with pytest.raises(NotFoundError) as exc:
                await producto_service.create_producto_servicio(
                    client_id=CLIENT_ID,
                    data=data,
                )
            assert "Unidad de medida base" in exc.value.detail
            mock_um.assert_called_with(
                client_id=CLIENT_ID,
                unidad_medida_id=um_id,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


# --- Fase 3: stock y alertas ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_stock_cross_company_returns_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.stock_service.get_stock_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await stock_service.get_stock_servicio(
                    client_id=CLIENT_ID,
                    stock_id=STOCK_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                stock_id=STOCK_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stocks_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.stock_service._validate_optional_filtro_empresa",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.stock_service.list_stocks",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await stock_service.list_stocks_servicio(client_id=CLIENT_ID)
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                producto_id=None,
                almacen_id=None,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stocks_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await stock_service.list_stocks_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lookup_stock_producto_almacen_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.stock_service.get_producto_by_id",
            new=AsyncMock(
                return_value={
                    "producto_id": PRODUCTO_A,
                    "empresa_id": EMPRESA_A,
                }
            ),
        ), patch(
            "app.modules.inv.application.services.stock_service.get_almacen_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError) as exc:
                await stock_service.get_stock_by_producto_almacen_servicio(
                    client_id=CLIENT_ID,
                    producto_id=PRODUCTO_A,
                    almacen_id=ALMACEN_B_OTHER,
                )
            assert "Almacén" in exc.value.detail
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_stock_producto_e1_almacen_e2_rejected():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = StockCreate(
            empresa_id=EMPRESA_A,
            producto_id=PRODUCTO_A,
            almacen_id=ALMACEN_B_OTHER,
            moneda_id=uuid4(),
        )
        with patch(
            "app.modules.inv.application.services.stock_service.ensure_empresa_in_tenant",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.stock_service.get_producto_by_id",
            new=AsyncMock(return_value={"empresa_id": EMPRESA_A}),
        ), patch(
            "app.modules.inv.application.services.stock_service.get_almacen_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await stock_service.create_stock_servicio(
                    client_id=CLIENT_ID,
                    data=data,
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_stock_body_empresa_mismatch_403():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = StockCreate(
            empresa_id=EMPRESA_B,
            producto_id=PRODUCTO_A,
            almacen_id=ALMACEN_A,
            moneda_id=uuid4(),
        )
        with pytest.raises(AuthorizationError) as exc:
            await stock_service.create_stock_servicio(client_id=CLIENT_ID, data=data)
        assert exc.value.internal_code == "EMPRESA_MISMATCH"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stock_alertas_uses_session_empresa():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.stock_service.list_stock_alertas_bajo_minimo",
            new=AsyncMock(return_value=[]),
        ) as mock_alertas:
            await stock_service.list_stock_alertas_servicio(client_id=CLIENT_ID)
            mock_alertas.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                almacen_id=None,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_stock_alertas_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await stock_service.list_stock_alertas_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lookup_stock_passes_empresa_to_query():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.stock_service._validate_producto_almacen_empresa",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.stock_service.get_stock_by_producto_almacen",
            new=AsyncMock(return_value=None),
        ) as mock_lookup:
            result = await stock_service.get_stock_by_producto_almacen_servicio(
                client_id=CLIENT_ID,
                producto_id=PRODUCTO_A,
                almacen_id=ALMACEN_A,
            )
            assert result is None
            mock_lookup.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                producto_id=PRODUCTO_A,
                almacen_id=ALMACEN_A,
            )
    finally:
        reset_current_empresa_id(token)


# --- Fase 4: movimientos y detalle ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_movimiento_cross_company_returns_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await movimiento_service.get_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_movimientos_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service._validate_optional_list_filtros",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.movimiento_service.list_movimientos",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await movimiento_service.list_movimientos_servicio(client_id=CLIENT_ID)
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                tipo_movimiento_id=None,
                almacen_id=None,
                estado=None,
                fecha_desde=None,
                fecha_hasta=None,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_movimientos_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await movimiento_service.list_movimientos_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_movimiento_con_detalles_filters_empresa():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_con_detalles",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await movimiento_service.get_movimiento_con_detalles_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_A,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_A,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_movimiento_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        from app.modules.inv.presentation.schemas import MovimientoUpdate

        with patch(
            "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await movimiento_service.update_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_B,
                    data=MovimientoUpdate(observaciones="x"),
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_movimiento_detalle_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_detalle_service.get_movimiento_detalle_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await movimiento_detalle_service.get_movimiento_detalle_servicio(
                    client_id=CLIENT_ID,
                    movimiento_detalle_id=MOVIMIENTO_DETALLE_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                movimiento_detalle_id=MOVIMIENTO_DETALLE_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_detalle_cross_company_movimiento_404():
    from decimal import Decimal

    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = MovimientoDetalleCreate(
            empresa_id=EMPRESA_A,
            movimiento_id=MOVIMIENTO_B,
            producto_id=PRODUCTO_A,
            cantidad=Decimal("1"),
            unidad_medida_id=uuid4(),
            cantidad_base=Decimal("1"),
        )
        with patch(
            "app.modules.inv.application.services.movimiento_detalle_service.get_movimiento_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await movimiento_detalle_service.create_movimiento_detalle_servicio(
                    client_id=CLIENT_ID,
                    data=data,
                )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_detalle_body_empresa_mismatch_403():
    from decimal import Decimal

    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = MovimientoDetalleCreate(
            empresa_id=EMPRESA_B,
            movimiento_id=MOVIMIENTO_A,
            producto_id=PRODUCTO_A,
            cantidad=Decimal("1"),
            unidad_medida_id=uuid4(),
            cantidad_base=Decimal("1"),
        )
        with pytest.raises(AuthorizationError) as exc:
            await movimiento_detalle_service.create_movimiento_detalle_servicio(
                client_id=CLIENT_ID,
                data=data,
            )
        assert exc.value.internal_code == "EMPRESA_MISMATCH"
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_movimientos_detalle_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await movimiento_detalle_service.list_movimientos_detalle_servicio(
            client_id=CLIENT_ID
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


# --- Fase 5: procesamiento de movimientos (runtime / stock) ---


class _FakeUowContext:
    """Context manager falso para unit_of_work en tests de proceso."""

    def __init__(self, uow):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, *args):
        return False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_procesar_movimiento_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await movimiento_proceso_service.procesar_movimiento_servicio(
            client_id=CLIENT_ID,
            movimiento_id=MOVIMIENTO_A,
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_procesar_movimiento_cross_company_not_found_no_stock_mutation():
    """Token empresa A + movimiento B: 404 y una sola lectura (sin mutar stock)."""
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        mock_uow = AsyncMock()
        mock_uow.execute = AsyncMock(return_value=[])

        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ):
            with pytest.raises(NotFoundError):
                await movimiento_proceso_service.procesar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_B,
                )
            assert mock_uow.execute.call_count == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_autorizar_movimiento_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get, patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(NotFoundError):
                await movimiento_proceso_service.autorizar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_B,
                empresa_id=EMPRESA_A,
            )
            mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_anular_movimiento_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get, patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(NotFoundError):
                await movimiento_proceso_service.anular_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_B,
                    motivo="test",
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_B,
                empresa_id=EMPRESA_A,
            )
            mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_autorizar_movimiento_passes_empresa_to_update():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        mov = {
            "movimiento_id": MOVIMIENTO_A,
            "empresa_id": EMPRESA_A,
            "estado": "borrador",
        }
        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_movimiento_by_id",
            new=AsyncMock(return_value=mov),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.update_movimiento",
            new=AsyncMock(return_value={**mov, "estado": "autorizado"}),
        ) as mock_update:
            await movimiento_proceso_service.autorizar_movimiento_servicio(
                client_id=CLIENT_ID,
                movimiento_id=MOVIMIENTO_A,
            )
            mock_update.assert_called_once()
            assert mock_update.call_args.kwargs["empresa_id"] == EMPRESA_A
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_procesar_validates_producto_empresa_before_stock():
    """Si el producto no pertenece a la sesión, falla antes de tocar stock."""
    from decimal import Decimal

    token = _set_empresa_ctx(EMPRESA_A)
    try:
        mov = {
            "movimiento_id": MOVIMIENTO_A,
            "empresa_id": EMPRESA_A,
            "estado": "borrador",
            "requiere_autorizacion": False,
            "tipo_movimiento_id": uuid4(),
            "almacen_destino_id": ALMACEN_A,
            "moneda_id": uuid4(),
        }
        tm = {"clase_movimiento": "entrada"}
        det = {
            "producto_id": PRODUCTO_B,
            "cantidad_base": Decimal("1"),
        }

        call_idx = {"n": 0}

        async def _execute_side_effect(*args, **kwargs):
            call_idx["n"] += 1
            if call_idx["n"] == 1:
                return [mov]
            if call_idx["n"] == 2:
                return [tm]
            if call_idx["n"] == 3:
                return [det]
            return []

        mock_uow = AsyncMock()
        mock_uow.execute = AsyncMock(side_effect=_execute_side_effect)

        with patch(
            "app.modules.inv.application.services.movimiento_proceso_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_almacen_by_id",
            new=AsyncMock(return_value={"almacen_id": ALMACEN_A}),
        ), patch(
            "app.modules.inv.application.services.movimiento_proceso_service.get_producto_by_id",
            new=AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFoundError):
                await movimiento_proceso_service.procesar_movimiento_servicio(
                    client_id=CLIENT_ID,
                    movimiento_id=MOVIMIENTO_A,
                )
            assert call_idx["n"] == 3
    finally:
        reset_current_empresa_id(token)


# --- Fase 6: inventario físico + aprobación ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_inventario_fisico_cross_company_returns_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await inventario_fisico_service.get_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_FISICO_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_inventarios_fisicos_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service._validate_optional_list_filtros",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.list_inventarios_fisicos",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await inventario_fisico_service.list_inventarios_fisicos_servicio(
                client_id=CLIENT_ID
            )
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                almacen_id=None,
                estado=None,
                fecha_desde=None,
                fecha_hasta=None,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_inventarios_fisicos_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await inventario_fisico_service.list_inventarios_fisicos_servicio(
            client_id=CLIENT_ID
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_inventario_fisico_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        from app.modules.inv.presentation.schemas import InventarioFisicoUpdate

        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(NotFoundError):
                await inventario_fisico_service.update_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_B,
                    data=InventarioFisicoUpdate(observaciones="x"),
                )
            mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_anular_inventario_fisico_cross_company_no_mutation():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(NotFoundError):
                await inventario_fisico_service.anular_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_B,
                )
            mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_finalizar_inventario_fisico_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
            new=AsyncMock(),
        ) as mock_update:
            with pytest.raises(NotFoundError):
                await inventario_fisico_service.finalizar_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_B,
                )
            mock_update.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aprobar_inventario_fisico_cross_company_no_mutation():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        mock_uow = AsyncMock()
        mock_uow.execute = AsyncMock(return_value=[])

        with patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.unit_of_work",
            return_value=_FakeUowContext(mock_uow),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.get_tipo_movimiento_by_id",
            new=AsyncMock(return_value={"clase_movimiento": "ajuste"}),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_aprobacion_service.procesar_movimiento_servicio",
            new=AsyncMock(),
        ) as mock_procesar:
            with pytest.raises(NotFoundError):
                await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_id=INVENTARIO_FISICO_B,
                    tipo_movimiento_id=uuid4(),
                )
            mock_procesar.assert_not_called()
            assert mock_uow.execute.call_count == 1
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_aprobar_inventario_fisico_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_FISICO_A,
            tipo_movimiento_id=uuid4(),
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_inventario_fisico_detalle_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.inventario_fisico_detalle_service.get_inventario_fisico_detalle_by_id",
            new=AsyncMock(return_value=None),
        ) as mock_get:
            with pytest.raises(NotFoundError):
                await inventario_fisico_detalle_service.get_inventario_fisico_detalle_servicio(
                    client_id=CLIENT_ID,
                    inventario_fisico_detalle_id=INVENTARIO_FISICO_DETALLE_B,
                )
            mock_get.assert_called_once_with(
                client_id=CLIENT_ID,
                inventario_fisico_detalle_id=INVENTARIO_FISICO_DETALLE_B,
                empresa_id=EMPRESA_A,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_inventario_fisico_detalle_cross_company_cabecera_404():
    from decimal import Decimal
    from app.modules.inv.presentation.schemas import InventarioFisicoDetalleCreate

    token = _set_empresa_ctx(EMPRESA_A)
    try:
        data = InventarioFisicoDetalleCreate(
            empresa_id=EMPRESA_A,
            inventario_fisico_id=INVENTARIO_FISICO_B,
            producto_id=PRODUCTO_A,
            cantidad_sistema=Decimal("0"),
            cantidad_contada=Decimal("1"),
        )
        with patch(
            "app.modules.inv.application.services.inventario_fisico_detalle_service.get_inventario_fisico_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.inventario_fisico_detalle_service.create_inventario_fisico_detalle",
            new=AsyncMock(),
        ) as mock_create:
            with pytest.raises(NotFoundError):
                await inventario_fisico_detalle_service.create_inventario_fisico_detalle_servicio(
                    client_id=CLIENT_ID,
                    data=data,
                )
            mock_create.assert_not_called()
    finally:
        reset_current_empresa_id(token)


# --- Fase 7: kardex (consulta / trazabilidad) ---


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_kardex_without_session_403():
    with pytest.raises(AuthorizationError) as exc:
        await kardex_service.list_kardex_servicio(client_id=CLIENT_ID)
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_kardex_uses_session_empresa_only():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.kardex_service._validate_optional_filtros_kardex",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.kardex_service.list_kardex",
            new=AsyncMock(return_value=[]),
        ) as mock_list:
            await kardex_service.list_kardex_servicio(client_id=CLIENT_ID)
            mock_list.assert_called_once_with(
                client_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
                producto_id=None,
                almacen_id=None,
                fecha_desde=None,
                fecha_hasta=None,
            )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_kardex_producto_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.kardex_service.get_producto_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.kardex_service.list_kardex",
            new=AsyncMock(),
        ) as mock_list:
            with pytest.raises(NotFoundError):
                await kardex_service.list_kardex_servicio(
                    client_id=CLIENT_ID,
                    producto_id=PRODUCTO_B,
                )
            mock_list.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_kardex_almacen_cross_company_404():
    token = _set_empresa_ctx(EMPRESA_A)
    try:
        with patch(
            "app.modules.inv.application.services.kardex_service.get_almacen_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.modules.inv.application.services.kardex_service.list_kardex",
            new=AsyncMock(),
        ) as mock_list:
            with pytest.raises(NotFoundError):
                await kardex_service.list_kardex_servicio(
                    client_id=CLIENT_ID,
                    almacen_id=ALMACEN_B,
                )
            mock_list.assert_not_called()
    finally:
        reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_kardex_results_scoped_to_session_empresa():
    """El servicio consulta solo con empresa_id de sesión (sin mezclar B)."""
    from datetime import datetime
    from decimal import Decimal

    token = _set_empresa_ctx(EMPRESA_A)
    try:
        row_a = {
            "movimiento_id": uuid4(),
            "movimiento_detalle_id": uuid4(),
            "empresa_id": EMPRESA_A,
            "fecha_movimiento": datetime.utcnow(),
            "tipo_movimiento_id": uuid4(),
            "producto_id": PRODUCTO_A,
            "almacen_origen_id": None,
            "almacen_destino_id": ALMACEN_A,
            "cantidad_base": Decimal("1"),
            "costo_unitario": Decimal("0"),
            "moneda_id": uuid4(),
            "lote": None,
            "numero_serie": None,
            "observaciones": None,
        }
        with patch(
            "app.modules.inv.application.services.kardex_service._validate_optional_filtros_kardex",
            new=AsyncMock(),
        ), patch(
            "app.modules.inv.application.services.kardex_service.list_kardex",
            new=AsyncMock(return_value=[row_a]),
        ) as mock_list:
            result = await kardex_service.list_kardex_servicio(client_id=CLIENT_ID)
            assert len(result) == 1
            assert result[0].empresa_id == EMPRESA_A
            assert mock_list.call_args.kwargs["empresa_id"] == EMPRESA_A
    finally:
        reset_current_empresa_id(token)
