"""
Servicios de aplicación para sls_cotizacion.
Maneja la lógica de negocio y llama a las queries.

Reglas transaccionales:
- Solo editable en estado 'borrador'
- Transiciones de estado explícitas (enviar/aceptar/rechazar/convertir)
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime

from app.infrastructure.database.queries.sls import (
    list_cotizaciones as _list_cotizaciones,
    get_cotizacion_by_id as _get_cotizacion_by_id,
    create_cotizacion as _create_cotizacion,
    update_cotizacion as _update_cotizacion,
    list_detalle_by_cotizacion_id as _list_detalle_by_cotizacion_id,
    replace_detalle_cotizacion as _replace_detalle_cotizacion,
    create_pedido as _create_pedido,
)
from app.modules.sls.presentation.schemas import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionRead,
    CotizacionDetalleCreate,
    CotizacionDetalleRead,
    PedidoCreate,
)
from app.core.exceptions import NotFoundError, ServiceError


async def list_cotizaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
) -> List[CotizacionRead]:
    """Lista cotizaciones del tenant."""
    rows = await _list_cotizaciones(
        client_id=client_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [CotizacionRead(**row) for row in rows]


async def get_cotizacion_by_id(client_id: UUID, cotizacion_id: UUID) -> CotizacionRead:
    """Obtiene una cotizacion por id. Lanza NotFoundError si no existe."""
    row = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not row:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    return CotizacionRead(**row)


async def create_cotizacion(client_id: UUID, data: CotizacionCreate) -> CotizacionRead:
    """Crea una cotizacion."""
    row = await _create_cotizacion(client_id, data.model_dump(exclude_none=True))
    return CotizacionRead(**row)


async def update_cotizacion(
    client_id: UUID, cotizacion_id: UUID, data: CotizacionUpdate
) -> CotizacionRead:
    """Actualiza una cotizacion. Solo permitido en estado 'borrador'."""
    current = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not current:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (current.get("estado") or "").lower() != "borrador":
        raise ServiceError(
            status_code=409,
            detail="La cotización solo puede editarse en estado borrador",
            internal_code="SLS_COTIZACION_NOT_EDITABLE",
        )
    row = await _update_cotizacion(
        client_id, cotizacion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    return CotizacionRead(**row)


async def get_detalle_cotizacion(
    client_id: UUID, cotizacion_id: UUID
) -> List[CotizacionDetalleRead]:
    """Lista el detalle embebido de una cotización."""
    # Validar existencia (y tenant) por cabecera
    _ = await get_cotizacion_by_id(client_id, cotizacion_id)
    rows = await _list_detalle_by_cotizacion_id(client_id=client_id, cotizacion_id=cotizacion_id)
    return [CotizacionDetalleRead(**row) for row in rows]


async def put_detalle_cotizacion(
    client_id: UUID,
    cotizacion_id: UUID,
    items: List[CotizacionDetalleCreate],
) -> List[CotizacionDetalleRead]:
    """Reemplaza el detalle completo. Solo permitido en estado 'borrador'."""
    cot = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not cot:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (cot.get("estado") or "").lower() != "borrador":
        raise ServiceError(
            status_code=409,
            detail="El detalle solo puede editarse en estado borrador",
            internal_code="SLS_COTIZACION_DET_NOT_EDITABLE",
        )
    empresa_id = cot["empresa_id"]
    payload_items = [i.model_dump(exclude_none=True) for i in items]
    rows = await _replace_detalle_cotizacion(
        client_id=client_id,
        empresa_id=empresa_id,
        cotizacion_id=cotizacion_id,
        items=payload_items,
    )
    return [CotizacionDetalleRead(**row) for row in rows]


async def enviar_cotizacion(client_id: UUID, cotizacion_id: UUID) -> CotizacionRead:
    cot = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not cot:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (cot.get("estado") or "").lower() != "borrador":
        raise ServiceError(409, "Solo se puede enviar una cotización en borrador", "SLS_COTIZACION_ESTADO_INVALIDO")
    row = await _update_cotizacion(
        client_id,
        cotizacion_id,
        {"estado": "enviada", "fecha_envio": datetime.utcnow()},
    )
    return CotizacionRead(**row)


async def aceptar_cotizacion(client_id: UUID, cotizacion_id: UUID) -> CotizacionRead:
    cot = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not cot:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (cot.get("estado") or "").lower() not in ("enviada", "borrador"):
        raise ServiceError(409, "Solo se puede aceptar una cotización enviada", "SLS_COTIZACION_ESTADO_INVALIDO")
    row = await _update_cotizacion(
        client_id,
        cotizacion_id,
        {"estado": "aceptada", "fecha_respuesta": datetime.utcnow()},
    )
    return CotizacionRead(**row)


async def rechazar_cotizacion(client_id: UUID, cotizacion_id: UUID, motivo: str = "") -> CotizacionRead:
    cot = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not cot:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (cot.get("estado") or "").lower() not in ("enviada", "borrador"):
        raise ServiceError(409, "Solo se puede rechazar una cotización enviada", "SLS_COTIZACION_ESTADO_INVALIDO")
    row = await _update_cotizacion(
        client_id,
        cotizacion_id,
        {"estado": "rechazada", "fecha_respuesta": datetime.utcnow(), "motivo_rechazo": motivo or None},
    )
    return CotizacionRead(**row)


async def convertir_cotizacion_a_pedido(client_id: UUID, cotizacion_id: UUID) -> Dict[str, Any]:
    """
    Convierte una cotización aceptada en pedido.
    Retorna: {cotizacion, pedido}
    """
    cot = await _get_cotizacion_by_id(client_id, cotizacion_id)
    if not cot:
        raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
    if (cot.get("estado") or "").lower() != "aceptada":
        raise ServiceError(409, "La cotización debe estar aceptada para convertir", "SLS_COTIZACION_ESTADO_INVALIDO")
    if bool(cot.get("convertida_pedido")):
        raise ServiceError(409, "La cotización ya fue convertida a pedido", "SLS_COTIZACION_YA_CONVERTIDA")

    # Crear pedido en borrador con campos comunes.
    pedido_data = PedidoCreate(
        empresa_id=cot["empresa_id"],
        numero_pedido=f"PED-{cot['numero_cotizacion']}",
        fecha_entrega_prometida=cot["fecha_vencimiento"],
        cliente_venta_id=cot["cliente_venta_id"],
        cliente_razon_social=cot.get("cliente_razon_social"),
        cliente_ruc=cot.get("cliente_ruc"),
        direccion_entrega_id=None,
        direccion_entrega_texto=None,
        cotizacion_id=cot["cotizacion_id"],
        orden_compra_cliente=None,
        vendedor_usuario_id=cot.get("vendedor_usuario_id"),
        vendedor_nombre=cot.get("vendedor_nombre"),
        condicion_pago=cot["condicion_pago"],
        dias_credito=cot.get("dias_credito") or 0,
        moneda_id=cot["moneda_id"],
        tipo_cambio=cot.get("tipo_cambio") or 1,
        subtotal=cot.get("subtotal") or 0,
        descuento_global=cot.get("descuento_global") or 0,
        igv=cot.get("igv") or 0,
        total=cot.get("total") or 0,
        total_items=0,
        items_despachados=0,
        porcentaje_despacho=0,
        estado="borrador",
        requiere_aprobacion=False,
        prioridad=3,
    )
    pedido_row = await _create_pedido(client_id, pedido_data.model_dump(exclude_none=True))

    # Marcar cotización como convertida
    cot_row = await _update_cotizacion(
        client_id,
        cotizacion_id,
        {
            "estado": "convertida",
            "convertida_pedido": True,
            "pedido_venta_id": pedido_row["pedido_id"],
            "fecha_conversion": datetime.utcnow(),
        },
    )
    return {"cotizacion": CotizacionRead(**cot_row), "pedido": pedido_row}
