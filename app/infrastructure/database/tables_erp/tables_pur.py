# app/infrastructure/database/tables_erp/tables_pur.py
"""
Tablas SQLAlchemy Core para el módulo PUR (Compras).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección PUR.
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
# TABLA: pur_proveedor
# ============================================================================
PurProveedorTable = Table(
    "pur_proveedor",
    metadata_erp,
    Column("proveedor_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_proveedor", String(20), nullable=False),
    Column("razon_social", String(200), nullable=False),
    Column("nombre_comercial", String(150), nullable=True),
    Column("tipo_documento", String(10), nullable=True, server_default="RUC"),
    Column("numero_documento", String(20), nullable=False),
    Column("tipo_proveedor", String(30), nullable=True, server_default="bienes"),
    Column("categoria_proveedor", String(50), nullable=True),
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
    Column("email_cotizaciones", String(100), nullable=True),
    Column("sitio_web", String(255), nullable=True),
    Column("condicion_pago_defecto", String(50), nullable=True),
    Column("dias_credito_defecto", Integer, nullable=True, server_default="0"),
    Column("moneda_preferida", String(3), nullable=True, server_default="PEN"),
    Column("banco", String(100), nullable=True),
    Column("numero_cuenta", String(30), nullable=True),
    Column("tipo_cuenta", String(20), nullable=True),
    Column("cci", String(20), nullable=True),
    Column("calificacion", Numeric(3, 2), nullable=True),
    Column("nivel_confianza", String(20), nullable=True, server_default="medio"),
    Column("es_proveedor_homologado", Boolean, nullable=True, server_default="0"),
    Column("fecha_homologacion", Date, nullable=True),
    Column("limite_credito", Numeric(18, 2), nullable=True),
    Column("saldo_pendiente", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="activo"),
    Column("motivo_bloqueo", String(255), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_actualizacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_proveedor", name="UQ_prov_codigo"),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_documento", "numero_documento", name="UQ_prov_documento"),
)
Index("IDX_prov_empresa", PurProveedorTable.c.empresa_id, PurProveedorTable.c.es_activo)
Index("IDX_prov_documento", PurProveedorTable.c.numero_documento)
Index("IDX_prov_razon_social", PurProveedorTable.c.razon_social)
Index("IDX_prov_categoria", PurProveedorTable.c.categoria_proveedor)

# ============================================================================
# TABLA: pur_proveedor_contacto
# ============================================================================
PurProveedorContactoTable = Table(
    "pur_proveedor_contacto",
    metadata_erp,
    Column("contacto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id", ondelete="CASCADE"), nullable=False),
    Column("nombre_completo", String(150), nullable=False),
    Column("cargo", String(100), nullable=True),
    Column("area", String(100), nullable=True),
    Column("telefono", String(20), nullable=True),
    Column("telefono_movil", String(20), nullable=True),
    Column("email", String(100), nullable=True),
    Column("es_contacto_principal", Boolean, nullable=True, server_default="0"),
    Column("es_contacto_cotizaciones", Boolean, nullable=True, server_default="0"),
    Column("es_contacto_cobranzas", Boolean, nullable=True, server_default="0"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_provcon_proveedor", PurProveedorContactoTable.c.proveedor_id, PurProveedorContactoTable.c.es_activo)

# ============================================================================
# TABLA: pur_producto_proveedor
# ============================================================================
PurProductoProveedorTable = Table(
    "pur_producto_proveedor",
    metadata_erp,
    Column("producto_proveedor_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_proveedor", String(50), nullable=True),
    Column("descripcion_proveedor", String(200), nullable=True),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cantidad_minima", Numeric(18, 4), nullable=True),
    Column("multiplo_compra", Numeric(18, 4), nullable=True),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("fecha_vigencia_desde", Date, nullable=True),
    Column("fecha_vigencia_hasta", Date, nullable=True),
    Column("es_proveedor_preferido", Boolean, nullable=True, server_default="0"),
    Column("prioridad", Integer, nullable=True, server_default="3"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    UniqueConstraint("cliente_id", "proveedor_id", "producto_id", name="UQ_prodprov"),
)
Index("IDX_prodprov_proveedor", PurProductoProveedorTable.c.proveedor_id, PurProductoProveedorTable.c.es_activo)
Index("IDX_prodprov_producto", PurProductoProveedorTable.c.producto_id, PurProductoProveedorTable.c.es_activo)
Index("IDX_prodprov_preferido", PurProductoProveedorTable.c.producto_id, PurProductoProveedorTable.c.es_proveedor_preferido)

# ============================================================================
# TABLA: pur_solicitud_compra
# ============================================================================
PurSolicitudCompraTable = Table(
    "pur_solicitud_compra",
    metadata_erp,
    Column("solicitud_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_solicitud", String(20), nullable=False),
    Column("fecha_solicitud", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_requerida", Date, nullable=False),
    Column("departamento_solicitante_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_solicitante_id", UNIQUEIDENTIFIER, nullable=False),
    Column("solicitante_nombre", String(150), nullable=True),
    Column("almacen_destino_id", UNIQUEIDENTIFIER, nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("tipo_solicitud", String(30), nullable=True, server_default="normal"),
    Column("motivo_solicitud", String(30), nullable=True),
    Column("total_items", Integer, nullable=True, server_default="0"),
    Column("total_estimado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_aprobacion", Boolean, nullable=True, server_default="1"),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("orden_compra_generada", Boolean, nullable=True, server_default="0"),
    Column("observaciones", Text, nullable=True),
    Column("motivo_rechazo", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_solicitud", name="UQ_solcomp_numero"),
)
Index("IDX_solcomp_empresa", PurSolicitudCompraTable.c.empresa_id, PurSolicitudCompraTable.c.fecha_solicitud)
Index("IDX_solcomp_estado", PurSolicitudCompraTable.c.estado, PurSolicitudCompraTable.c.fecha_solicitud)
Index("IDX_solcomp_solicitante", PurSolicitudCompraTable.c.usuario_solicitante_id)

# ============================================================================
# TABLA: pur_solicitud_compra_detalle
# ============================================================================
PurSolicitudCompraDetalleTable = Table(
    "pur_solicitud_compra_detalle",
    metadata_erp,
    Column("solicitud_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("solicitud_id", UNIQUEIDENTIFIER, ForeignKey("pur_solicitud_compra.solicitud_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_solicitada", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("precio_referencial", Numeric(18, 4), nullable=True),
    Column("cantidad_atendida", Numeric(18, 4), nullable=True, server_default="0"),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_solcompdet_solicitud", PurSolicitudCompraDetalleTable.c.solicitud_id)
Index("IDX_solcompdet_producto", PurSolicitudCompraDetalleTable.c.producto_id)

# ============================================================================
# TABLA: pur_cotizacion
# ============================================================================
PurCotizacionTable = Table(
    "pur_cotizacion",
    metadata_erp,
    Column("cotizacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_cotizacion", String(20), nullable=False),
    Column("fecha_cotizacion", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id"), nullable=False),
    Column("solicitud_compra_id", UNIQUEIDENTIFIER, nullable=True),
    Column("condicion_pago", String(50), nullable=True),
    Column("dias_credito", Integer, nullable=True),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("lugar_entrega", String(255), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("subtotal", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="pendiente"),
    Column("es_ganadora", Boolean, nullable=True, server_default="0"),
    Column("observaciones", Text, nullable=True),
    Column("motivo_rechazo", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_cotizacion", name="UQ_cotiz_numero"),
)
Index("IDX_cotiz_empresa", PurCotizacionTable.c.empresa_id, PurCotizacionTable.c.fecha_cotizacion)
Index("IDX_cotiz_proveedor", PurCotizacionTable.c.proveedor_id, PurCotizacionTable.c.estado)
Index("IDX_cotiz_estado", PurCotizacionTable.c.estado)
Index("IDX_cotiz_ganadora", PurCotizacionTable.c.es_ganadora)

# ============================================================================
# TABLA: pur_cotizacion_detalle
# ============================================================================
PurCotizacionDetalleTable = Table(
    "pur_cotizacion_detalle",
    metadata_erp,
    Column("cotizacion_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cotizacion_id", UNIQUEIDENTIFIER, ForeignKey("pur_cotizacion.cotizacion_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True, server_default="0"),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_cotizdet_cotizacion", PurCotizacionDetalleTable.c.cotizacion_id)
Index("IDX_cotizdet_producto", PurCotizacionDetalleTable.c.producto_id)

# ============================================================================
# TABLA: pur_orden_compra
# ============================================================================
PurOrdenCompraTable = Table(
    "pur_orden_compra",
    metadata_erp,
    Column("orden_compra_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_oc", String(20), nullable=False),
    Column("fecha_emision", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_requerida", Date, nullable=False),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id"), nullable=False),
    Column("proveedor_razon_social", String(200), nullable=True),
    Column("proveedor_ruc", String(20), nullable=True),
    Column("almacen_destino_id", UNIQUEIDENTIFIER, nullable=True),
    Column("direccion_entrega", String(255), nullable=True),
    Column("solicitud_compra_id", UNIQUEIDENTIFIER, nullable=True),
    Column("cotizacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("condicion_pago", String(50), nullable=False),
    Column("dias_credito", Integer, nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_cambio", Numeric(10, 4), nullable=True, server_default="1"),
    Column("subtotal", Numeric(18, 2), nullable=True, server_default="0"),
    Column("descuento_global", Numeric(18, 2), nullable=True, server_default="0"),
    Column("igv", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_items", Integer, nullable=True, server_default="0"),
    Column("items_recepcionados", Integer, nullable=True, server_default="0"),
    Column("porcentaje_recepcion", Numeric(5, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_aprobacion", Boolean, nullable=True, server_default="1"),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("terminos_condiciones", Text, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_aprobacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_oc", name="UQ_oc_numero"),
)
Index("IDX_oc_empresa", PurOrdenCompraTable.c.empresa_id, PurOrdenCompraTable.c.fecha_emision)
Index("IDX_oc_proveedor", PurOrdenCompraTable.c.proveedor_id, PurOrdenCompraTable.c.estado)
Index("IDX_oc_estado", PurOrdenCompraTable.c.estado, PurOrdenCompraTable.c.fecha_emision)
Index("IDX_oc_fecha_requerida", PurOrdenCompraTable.c.fecha_requerida, PurOrdenCompraTable.c.estado)

# ============================================================================
# TABLA: pur_orden_compra_detalle
# ============================================================================
PurOrdenCompraDetalleTable = Table(
    "pur_orden_compra_detalle",
    metadata_erp,
    Column("orden_compra_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("orden_compra_id", UNIQUEIDENTIFIER, ForeignKey("pur_orden_compra.orden_compra_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_ordenada", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True, server_default="0"),
    Column("cantidad_recepcionada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("observaciones", String(500), nullable=True),
    Column("especificaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_ocdet_oc", PurOrdenCompraDetalleTable.c.orden_compra_id)
Index("IDX_ocdet_producto", PurOrdenCompraDetalleTable.c.producto_id)

# ============================================================================
# TABLA: pur_recepcion
# ============================================================================
PurRecepcionTable = Table(
    "pur_recepcion",
    metadata_erp,
    Column("recepcion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_recepcion", String(20), nullable=False),
    Column("fecha_recepcion", DateTime, nullable=False, server_default=func.getdate()),
    Column("orden_compra_id", UNIQUEIDENTIFIER, ForeignKey("pur_orden_compra.orden_compra_id"), nullable=False),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id"), nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id"), nullable=False),
    Column("guia_remision_numero", String(30), nullable=True),
    Column("guia_remision_fecha", Date, nullable=True),
    Column("transportista", String(150), nullable=True),
    Column("placa_vehiculo", String(15), nullable=True),
    Column("recepcionado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("recepcionado_por_nombre", String(150), nullable=True),
    Column("total_items", Integer, nullable=True, server_default="0"),
    Column("total_cantidad", Numeric(18, 4), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_inspeccion", Boolean, nullable=True, server_default="0"),
    Column("inspeccion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("movimiento_inventario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("incidencias", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_procesado", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_procesado_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_recepcion", name="UQ_recep_numero"),
)
Index("IDX_recep_empresa", PurRecepcionTable.c.empresa_id, PurRecepcionTable.c.fecha_recepcion)
Index("IDX_recep_oc", PurRecepcionTable.c.orden_compra_id)
Index("IDX_recep_estado", PurRecepcionTable.c.estado)
Index("IDX_recep_almacen", PurRecepcionTable.c.almacen_id)

# ============================================================================
# TABLA: pur_recepcion_detalle
# ============================================================================
PurRecepcionDetalleTable = Table(
    "pur_recepcion_detalle",
    metadata_erp,
    Column("recepcion_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("recepcion_id", UNIQUEIDENTIFIER, ForeignKey("pur_recepcion.recepcion_id", ondelete="CASCADE"), nullable=False),
    Column("orden_compra_detalle_id", UNIQUEIDENTIFIER, ForeignKey("pur_orden_compra_detalle.orden_compra_detalle_id"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_ordenada", Numeric(18, 4), nullable=False),
    Column("cantidad_recepcionada", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("lote", String(50), nullable=True),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("precio_unitario", Numeric(18, 4), nullable=True, server_default="0"),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("motivo_diferencia", String(255), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_recepdet_recepcion", PurRecepcionDetalleTable.c.recepcion_id)
Index("IDX_recepdet_producto", PurRecepcionDetalleTable.c.producto_id)
Index("IDX_recepdet_ocdet", PurRecepcionDetalleTable.c.orden_compra_detalle_id)
