# app/infrastructure/database/tables_erp/tables_sls.py
"""
Tablas SQLAlchemy Core para el módulo SLS (Ventas).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección SLS.
✅ Campos esenciales incluidos desde el inicio.
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Text, Index, UniqueConstraint, Numeric, MetaData
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

# Usar la misma metadata_erp que tables_org
from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: sls_cliente
# ============================================================================
SlsClienteTable = Table(
    "sls_cliente",
    metadata_erp,
    Column("cliente_venta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_cliente", String(20), nullable=False),
    Column("tipo_cliente", String(20), nullable=True, server_default="empresa"),
    Column("razon_social", String(200), nullable=False),
    Column("nombre_comercial", String(150), nullable=True),
    Column("tipo_documento", String(10), nullable=True, server_default="RUC"),
    Column("numero_documento", String(20), nullable=False),
    Column("categoria_cliente", String(50), nullable=True),
    Column("segmento", String(50), nullable=True),
    Column("canal_venta", String(30), nullable=True),
    Column("direccion", String(255), nullable=True),
    Column("pais", String(50), nullable=True, server_default="Perú"),
    Column("departamento", String(50), nullable=True),
    Column("provincia", String(50), nullable=True),
    Column("distrito", String(50), nullable=True),
    Column("ubigeo", String(6), nullable=True),
    Column("contacto_nombre", String(150), nullable=True),
    Column("contacto_cargo", String(100), nullable=True),
    Column("telefono_principal", String(20), nullable=True),
    Column("telefono_secundario", String(20), nullable=True),
    Column("email_principal", String(100), nullable=True),
    Column("email_facturacion", String(100), nullable=True),
    Column("sitio_web", String(255), nullable=True),
    Column("condicion_pago_defecto", String(50), nullable=True, server_default="contado"),
    Column("dias_credito_defecto", Integer, nullable=True, server_default="0"),
    Column("moneda_preferida", String(3), nullable=True, server_default="PEN"),
    Column("lista_precio_id", UNIQUEIDENTIFIER, nullable=True),
    Column("limite_credito", Numeric(18, 2), nullable=True),
    Column("saldo_pendiente", Numeric(18, 2), nullable=True, server_default="0"),
    Column("saldo_vencido", Numeric(18, 2), nullable=True, server_default="0"),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("banco", String(100), nullable=True),
    Column("numero_cuenta", String(30), nullable=True),
    Column("calificacion", Numeric(3, 2), nullable=True),
    Column("nivel_riesgo", String(20), nullable=True, server_default="bajo"),
    Column("estado", String(20), nullable=True, server_default="activo"),
    Column("motivo_bloqueo", String(255), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("fecha_primera_compra", Date, nullable=True),
    Column("fecha_ultima_compra", Date, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_cliente", name="UQ_cltvta_codigo"),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_documento", "numero_documento", name="UQ_cltvta_documento"),
)
Index("IDX_cltvta_empresa", SlsClienteTable.c.empresa_id, SlsClienteTable.c.es_activo)
Index("IDX_cltvta_documento", SlsClienteTable.c.numero_documento)
Index("IDX_cltvta_razon_social", SlsClienteTable.c.razon_social)
Index("IDX_cltvta_vendedor", SlsClienteTable.c.vendedor_usuario_id)

# ============================================================================
# TABLA: sls_cliente_contacto
# ============================================================================
SlsClienteContactoTable = Table(
    "sls_cliente_contacto",
    metadata_erp,
    Column("contacto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="CASCADE"), nullable=False),
    Column("nombre_completo", String(150), nullable=False),
    Column("cargo", String(100), nullable=True),
    Column("area", String(100), nullable=True),
    Column("telefono", String(20), nullable=True),
    Column("telefono_movil", String(20), nullable=True),
    Column("email", String(100), nullable=True),
    Column("es_contacto_principal", Boolean, nullable=True, server_default="0"),
    Column("es_contacto_comercial", Boolean, nullable=True, server_default="0"),
    Column("es_contacto_cobranzas", Boolean, nullable=True, server_default="0"),
    Column("fecha_nacimiento", Date, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_cltcon_cliente", SlsClienteContactoTable.c.cliente_venta_id, SlsClienteContactoTable.c.es_activo)

# ============================================================================
# TABLA: sls_cliente_direccion
# ============================================================================
SlsClienteDireccionTable = Table(
    "sls_cliente_direccion",
    metadata_erp,
    Column("direccion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_direccion", String(20), nullable=True),
    Column("nombre_direccion", String(100), nullable=False),
    Column("direccion", String(255), nullable=False),
    Column("referencia", String(255), nullable=True),
    Column("pais", String(50), nullable=True, server_default="Perú"),
    Column("departamento", String(50), nullable=True),
    Column("provincia", String(50), nullable=True),
    Column("distrito", String(50), nullable=True),
    Column("ubigeo", String(6), nullable=True),
    Column("codigo_postal", String(10), nullable=True),
    Column("contacto_nombre", String(150), nullable=True),
    Column("contacto_telefono", String(20), nullable=True),
    Column("es_direccion_fiscal", Boolean, nullable=True, server_default="0"),
    Column("es_direccion_entrega_defecto", Boolean, nullable=True, server_default="0"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_cltdir_cliente", SlsClienteDireccionTable.c.cliente_venta_id, SlsClienteDireccionTable.c.es_activo)

# ============================================================================
# TABLA: sls_cotizacion
# ============================================================================
SlsCotizacionTable = Table(
    "sls_cotizacion",
    metadata_erp,
    Column("cotizacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_cotizacion", String(20), nullable=False),
    Column("fecha_cotizacion", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_vencimiento", Date, nullable=False),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id"), nullable=False),
    Column("cliente_razon_social", String(200), nullable=True),
    Column("cliente_ruc", String(20), nullable=True),
    Column("contacto_nombre", String(150), nullable=True),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("oportunidad_id", UNIQUEIDENTIFIER, nullable=True),
    Column("condicion_pago", String(50), nullable=False),
    Column("dias_credito", Integer, nullable=True, server_default="0"),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_cambio", Numeric(10, 4), nullable=True, server_default="1"),
    Column("subtotal", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento_global", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_envio", DateTime, nullable=True),
    Column("fecha_respuesta", DateTime, nullable=True),
    Column("motivo_rechazo", String(500), nullable=True),
    Column("convertida_pedido", Boolean, nullable=True, server_default="0"),
    Column("pedido_venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_conversion", DateTime, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("terminos_condiciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_cotizacion", name="UQ_cotvta_numero"),
)
Index("IDX_cotvta_empresa", SlsCotizacionTable.c.empresa_id, SlsCotizacionTable.c.fecha_cotizacion)
Index("IDX_cotvta_cliente", SlsCotizacionTable.c.cliente_venta_id, SlsCotizacionTable.c.estado)
Index("IDX_cotvta_estado", SlsCotizacionTable.c.estado, SlsCotizacionTable.c.fecha_vencimiento)
Index("IDX_cotvta_vendedor", SlsCotizacionTable.c.vendedor_usuario_id)

# ============================================================================
# TABLA: sls_cotizacion_detalle
# ============================================================================
SlsCotizacionDetalleTable = Table(
    "sls_cotizacion_detalle",
    metadata_erp,
    Column("cotizacion_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cotizacion_id", UNIQUEIDENTIFIER, ForeignKey("sls_cotizacion.cotizacion_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True, server_default="0"),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_cotvtadet_cotizacion", SlsCotizacionDetalleTable.c.cotizacion_id)
Index("IDX_cotvtadet_producto", SlsCotizacionDetalleTable.c.producto_id)

# ============================================================================
# TABLA: sls_pedido
# ============================================================================
SlsPedidoTable = Table(
    "sls_pedido",
    metadata_erp,
    Column("pedido_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_pedido", String(20), nullable=False),
    Column("fecha_pedido", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_entrega_prometida", Date, nullable=False),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id"), nullable=False),
    Column("cliente_razon_social", String(200), nullable=True),
    Column("cliente_ruc", String(20), nullable=True),
    Column("direccion_entrega_id", UNIQUEIDENTIFIER, nullable=True),
    Column("direccion_entrega_texto", String(255), nullable=True),
    Column("cotizacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("orden_compra_cliente", String(30), nullable=True),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("condicion_pago", String(50), nullable=False),
    Column("dias_credito", Integer, nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_cambio", Numeric(10, 4), nullable=True, server_default="1"),
    Column("subtotal", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento_global", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_items", Integer, nullable=True, server_default="0"),
    Column("items_despachados", Integer, nullable=True, server_default="0"),
    Column("porcentaje_despacho", Numeric(5, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_aprobacion", Boolean, nullable=True, server_default="0"),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("prioridad", Integer, nullable=True, server_default="3"),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("instrucciones_despacho", Text, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_pedido", name="UQ_pedido_numero"),
)
Index("IDX_pedido_empresa", SlsPedidoTable.c.empresa_id, SlsPedidoTable.c.fecha_pedido)
Index("IDX_pedido_cliente", SlsPedidoTable.c.cliente_venta_id, SlsPedidoTable.c.estado)
Index("IDX_pedido_estado", SlsPedidoTable.c.estado, SlsPedidoTable.c.fecha_entrega_prometida)
Index("IDX_pedido_vendedor", SlsPedidoTable.c.vendedor_usuario_id)

# ============================================================================
# TABLA: sls_pedido_detalle
# ============================================================================
SlsPedidoDetalleTable = Table(
    "sls_pedido_detalle",
    metadata_erp,
    Column("pedido_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("pedido_id", UNIQUEIDENTIFIER, ForeignKey("sls_pedido.pedido_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_pedida", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True, server_default="0"),
    Column("cantidad_despachada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_facturada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("almacen_origen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id"), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_pedidodet_pedido", SlsPedidoDetalleTable.c.pedido_id)
Index("IDX_pedidodet_producto", SlsPedidoDetalleTable.c.producto_id)
