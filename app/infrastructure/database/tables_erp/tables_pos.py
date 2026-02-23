# app/infrastructure/database/tables_erp/tables_pos.py
"""
Tablas SQLAlchemy Core para el módulo POS (Punto de Venta).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección POS.
✅ Dependencias: ORG, INV, SLS, PRC, INV_BILL.
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, Numeric
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: pos_punto_venta
# ============================================================================
PosPuntoVentaTable = Table(
    "pos_punto_venta",
    metadata_erp,
    Column("punto_venta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_punto_venta", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="CASCADE"), nullable=False),
    Column("ubicacion_fisica", String(100), nullable=True),
    Column("tipo_punto_venta", String(30), nullable=True, server_default="caja"),
    Column("serie_factura_id", UNIQUEIDENTIFIER, nullable=True),
    Column("serie_boleta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("serie_nota_credito_id", UNIQUEIDENTIFIER, nullable=True),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="SET NULL"), nullable=True),
    Column("lista_precio_id", UNIQUEIDENTIFIER, ForeignKey("prc_lista_precio.lista_precio_id", ondelete="SET NULL"), nullable=True),
    Column("acepta_efectivo", Boolean, nullable=True, server_default="1"),
    Column("acepta_tarjeta", Boolean, nullable=True, server_default="1"),
    Column("acepta_transferencia", Boolean, nullable=True, server_default="1"),
    Column("acepta_yape_plin", Boolean, nullable=True, server_default="0"),
    Column("codigo_terminal", String(50), nullable=True),
    Column("ip_terminal", String(45), nullable=True),
    Column("estado", String(20), nullable=True, server_default="cerrado"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_punto_venta", name="UQ_pv_codigo"),
)
Index("IDX_pv_empresa", PosPuntoVentaTable.c.empresa_id, PosPuntoVentaTable.c.es_activo)
Index("IDX_pv_sucursal", PosPuntoVentaTable.c.sucursal_id, PosPuntoVentaTable.c.estado)

# ============================================================================
# TABLA: pos_turno_caja
# ============================================================================
PosTurnoCajaTable = Table(
    "pos_turno_caja",
    metadata_erp,
    Column("turno_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("punto_venta_id", UNIQUEIDENTIFIER, ForeignKey("pos_punto_venta.punto_venta_id", ondelete="CASCADE"), nullable=False),
    Column("numero_turno", String(20), nullable=False),
    Column("cajero_usuario_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cajero_nombre", String(150), nullable=True),
    Column("fecha_apertura", DateTime, nullable=False, server_default=func.getdate()),
    Column("monto_apertura", Numeric(18, 2), nullable=False),
    Column("fecha_cierre", DateTime, nullable=True),
    Column("monto_cierre_esperado", Numeric(18, 2), nullable=True),
    Column("monto_cierre_real", Numeric(18, 2), nullable=True),
    Column("total_ventas", Integer, nullable=True, server_default="0"),
    Column("total_ventas_efectivo", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_ventas_tarjeta", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_ventas_transferencia", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_ventas_otros", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_egresos", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_facturas", Integer, nullable=True, server_default="0"),
    Column("total_boletas", Integer, nullable=True, server_default="0"),
    Column("total_notas_credito", Integer, nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="abierto"),
    Column("observaciones_apertura", String(500), nullable=True),
    Column("observaciones_cierre", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("cerrado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "punto_venta_id", "numero_turno", name="UQ_turno_numero"),
)
Index("IDX_turno_empresa", PosTurnoCajaTable.c.empresa_id, PosTurnoCajaTable.c.fecha_apertura.desc())
Index("IDX_turno_pv", PosTurnoCajaTable.c.punto_venta_id, PosTurnoCajaTable.c.estado)
Index("IDX_turno_cajero", PosTurnoCajaTable.c.cajero_usuario_id, PosTurnoCajaTable.c.estado)

# ============================================================================
# TABLA: pos_venta
# ============================================================================
PosVentaTable = Table(
    "pos_venta",
    metadata_erp,
    Column("venta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_venta", String(20), nullable=False),
    Column("fecha_venta", DateTime, nullable=False, server_default=func.getdate()),
    Column("punto_venta_id", UNIQUEIDENTIFIER, ForeignKey("pos_punto_venta.punto_venta_id"), nullable=False),
    Column("turno_caja_id", UNIQUEIDENTIFIER, ForeignKey("pos_turno_caja.turno_id"), nullable=False),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=False),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="SET NULL"), nullable=True),
    Column("cliente_nombre", String(200), nullable=True),
    Column("cliente_documento_tipo", String(10), nullable=True),
    Column("cliente_documento_numero", String(20), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("subtotal", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento_global", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("redondeo", Numeric(18, 2), nullable=True, server_default="0"),
    Column("forma_pago", String(30), nullable=False),
    Column("monto_efectivo", Numeric(18, 2), nullable=True, server_default="0"),
    Column("monto_tarjeta", Numeric(18, 2), nullable=True, server_default="0"),
    Column("monto_transferencia", Numeric(18, 2), nullable=True, server_default="0"),
    Column("monto_otros", Numeric(18, 2), nullable=True, server_default="0"),
    Column("monto_recibido", Numeric(18, 2), nullable=True),
    Column("comprobante_id", UNIQUEIDENTIFIER, ForeignKey("invbill_comprobante.comprobante_id", ondelete="SET NULL"), nullable=True),
    Column("tipo_comprobante", String(2), nullable=True),
    Column("numero_comprobante", String(20), nullable=True),
    Column("estado", String(20), nullable=True, server_default="completada"),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "punto_venta_id", "numero_venta", name="UQ_posvta_numero"),
)
Index("IDX_posvta_empresa", PosVentaTable.c.empresa_id, PosVentaTable.c.fecha_venta.desc())
Index("IDX_posvta_pv", PosVentaTable.c.punto_venta_id, PosVentaTable.c.estado, PosVentaTable.c.fecha_venta.desc())
Index("IDX_posvta_turno", PosVentaTable.c.turno_caja_id)
Index("IDX_posvta_comprobante", PosVentaTable.c.comprobante_id)

# ============================================================================
# TABLA: pos_venta_detalle
# ============================================================================
PosVentaDetalleTable = Table(
    "pos_venta_detalle",
    metadata_erp,
    Column("venta_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("venta_id", UNIQUEIDENTIFIER, ForeignKey("pos_venta.venta_id", ondelete="CASCADE"), nullable=False),
    Column("item", Integer, nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("descripcion", String(200), nullable=True),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True, server_default="0"),
    Column("promocion_id", UNIQUEIDENTIFIER, ForeignKey("prc_promocion.promocion_id", ondelete="SET NULL"), nullable=True),
    Column("lote", String(50), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_posvtadet_venta", PosVentaDetalleTable.c.venta_id, PosVentaDetalleTable.c.item)
Index("IDX_posvtadet_producto", PosVentaDetalleTable.c.producto_id)
