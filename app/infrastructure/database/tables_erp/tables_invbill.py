# app/infrastructure/database/tables_erp/tables_invbill.py
"""
Tablas SQLAlchemy Core para el módulo INV_BILL (Facturación Electrónica).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección INV_BILL.
✅ Campos esenciales incluidos desde el inicio.
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date, Time,
    ForeignKey, Text, Index, UniqueConstraint, Numeric, MetaData
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

# Usar la misma metadata_erp que tables_org
from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: invbill_serie_comprobante
# ============================================================================
InvbillSerieComprobanteTable = Table(
    "invbill_serie_comprobante",
    metadata_erp,
    Column("serie_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("tipo_comprobante", String(2), nullable=False),
    Column("serie", String(4), nullable=False),
    Column("numero_actual", Integer, nullable=True, server_default="0"),
    Column("numero_inicial", Integer, nullable=True, server_default="1"),
    Column("numero_final", Integer, nullable=True),
    Column("sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id"), nullable=True),
    Column("punto_venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_electronica", Boolean, nullable=True, server_default="1"),
    Column("requiere_autorizacion_sunat", Boolean, nullable=True, server_default="1"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_activacion", Date, nullable=True),
    Column("fecha_baja", Date, nullable=True),
    Column("motivo_baja", String(255), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_comprobante", "serie", name="UQ_serie"),
)
Index("IDX_serie_empresa", InvbillSerieComprobanteTable.c.empresa_id, InvbillSerieComprobanteTable.c.es_activo)
Index("IDX_serie_tipo", InvbillSerieComprobanteTable.c.tipo_comprobante, InvbillSerieComprobanteTable.c.serie)

# ============================================================================
# TABLA: invbill_comprobante
# ============================================================================
InvbillComprobanteTable = Table(
    "invbill_comprobante",
    metadata_erp,
    Column("comprobante_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("tipo_comprobante", String(2), nullable=False),
    Column("serie", String(4), nullable=False),
    Column("numero", String(10), nullable=False),
    Column("fecha_emision", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("hora_emision", Time, nullable=True, server_default=func.cast(func.getdate(), Time)),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id"), nullable=True),
    Column("cliente_tipo_documento", String(2), nullable=False),
    Column("cliente_numero_documento", String(20), nullable=False),
    Column("cliente_razon_social", String(200), nullable=False),
    Column("cliente_direccion", String(255), nullable=True),
    Column("pedido_id", UNIQUEIDENTIFIER, ForeignKey("sls_pedido.pedido_id"), nullable=True),
    Column("venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("guia_remision_id", UNIQUEIDENTIFIER, nullable=True),
    Column("comprobante_referencia_id", UNIQUEIDENTIFIER, ForeignKey("invbill_comprobante.comprobante_id"), nullable=True),
    Column("tipo_nota", String(2), nullable=True),
    Column("motivo_nota", String(500), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_cambio", Numeric(10, 4), nullable=True, server_default="1"),
    Column("subtotal_gravado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("subtotal_exonerado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("subtotal_inafecto", Numeric(18, 2), nullable=True, server_default="0"),
    Column("subtotal_gratuito", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento_global", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("aplica_detraccion", Boolean, nullable=True, server_default="0"),
    Column("porcentaje_detraccion", Numeric(5, 2), nullable=True),
    Column("monto_detraccion", Numeric(18, 2), nullable=True),
    Column("aplica_retencion", Boolean, nullable=True, server_default="0"),
    Column("monto_retencion", Numeric(18, 2), nullable=True),
    Column("aplica_percepcion", Boolean, nullable=True, server_default="0"),
    Column("monto_percepcion", Numeric(18, 2), nullable=True),
    Column("condicion_pago", String(50), nullable=True),
    Column("forma_pago", String(30), nullable=True, server_default="contado"),
    Column("codigo_hash", String(100), nullable=True),
    Column("firma_digital", Text, nullable=True),
    Column("codigo_qr", Text, nullable=True),
    Column("estado_sunat", String(20), nullable=True, server_default="pendiente"),
    Column("codigo_respuesta_sunat", String(10), nullable=True),
    Column("mensaje_respuesta_sunat", String(500), nullable=True),
    Column("fecha_envio_sunat", DateTime, nullable=True),
    Column("fecha_respuesta_sunat", DateTime, nullable=True),
    Column("cdr_xml", Text, nullable=True),
    Column("cdr_fecha", DateTime, nullable=True),
    Column("xml_comprobante", Text, nullable=True),
    Column("pdf_url", String(500), nullable=True),
    Column("estado", String(20), nullable=True, server_default="emitido"),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_comprobante", "serie", "numero", name="UQ_comp_numero"),
)
Index("IDX_comp_empresa", InvbillComprobanteTable.c.empresa_id, InvbillComprobanteTable.c.fecha_emision)
Index("IDX_comp_cliente", InvbillComprobanteTable.c.cliente_venta_id, InvbillComprobanteTable.c.estado)
Index("IDX_comp_estado_sunat", InvbillComprobanteTable.c.estado_sunat)
Index("IDX_comp_fecha", InvbillComprobanteTable.c.fecha_emision)

# ============================================================================
# TABLA: invbill_comprobante_detalle
# ============================================================================
InvbillComprobanteDetalleTable = Table(
    "invbill_comprobante_detalle",
    metadata_erp,
    Column("comprobante_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("comprobante_id", UNIQUEIDENTIFIER, ForeignKey("invbill_comprobante.comprobante_id", ondelete="CASCADE"), nullable=False),
    Column("item", Integer, nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, nullable=True),
    Column("codigo_producto", String(50), nullable=True),
    Column("descripcion", String(500), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_codigo", String(10), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=True),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_unitario", Numeric(18, 4), nullable=True, server_default="0"),
    Column("tipo_afectacion_igv", String(2), nullable=False),
    Column("porcentaje_igv", Numeric(5, 2), nullable=True, server_default="18"),
    Column("codigo_producto_sunat", String(10), nullable=True),
    Column("lote", String(50), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_compdet_comprobante", InvbillComprobanteDetalleTable.c.comprobante_id, InvbillComprobanteDetalleTable.c.item)
Index("IDX_compdet_producto", InvbillComprobanteDetalleTable.c.producto_id)
