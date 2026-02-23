# app/infrastructure/database/tables_erp/tables_inv.py
"""
Tablas SQLAlchemy Core para el módulo INV (Inventarios).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección INV.
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
# TABLA: inv_categoria_producto
# ============================================================================
InvCategoriaProductoTable = Table(
    "inv_categoria_producto",
    metadata_erp,
    Column("categoria_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("categoria_padre_id", UNIQUEIDENTIFIER, nullable=True),
    Column("nivel", Integer, nullable=True, server_default="1"),
    Column("ruta_jerarquica", String(500), nullable=True),
    Column("cuenta_contable_inventario", String(20), nullable=True),
    Column("cuenta_contable_costo_venta", String(20), nullable=True),
    Column("metodo_costeo_defecto", String(20), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_cat_codigo"),
)
Index("IDX_cat_empresa", InvCategoriaProductoTable.c.empresa_id, InvCategoriaProductoTable.c.es_activo)
Index("IDX_cat_padre", InvCategoriaProductoTable.c.categoria_padre_id)

# ============================================================================
# TABLA: inv_unidad_medida
# ============================================================================
InvUnidadMedidaTable = Table(
    "inv_unidad_medida",
    metadata_erp,
    Column("unidad_medida_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(10), nullable=False),
    Column("nombre", String(50), nullable=False),
    Column("simbolo", String(10), nullable=True),
    Column("tipo_unidad", String(20), nullable=False),
    Column("es_unidad_base", Boolean, nullable=True, server_default="0"),
    Column("factor_conversion_base", Numeric(18, 6), nullable=True),
    Column("decimales_permitidos", Integer, nullable=True, server_default="2"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_um_codigo"),
)
Index("IDX_um_empresa", InvUnidadMedidaTable.c.empresa_id, InvUnidadMedidaTable.c.es_activo)
Index("IDX_um_tipo", InvUnidadMedidaTable.c.tipo_unidad)

# ============================================================================
# TABLA: inv_producto
# ============================================================================
InvProductoTable = Table(
    "inv_producto",
    metadata_erp,
    Column("producto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_sku", String(50), nullable=False),
    Column("codigo_barra", String(50), nullable=True),
    Column("codigo_interno", String(30), nullable=True),
    Column("codigo_fabricante", String(50), nullable=True),
    Column("nombre", String(200), nullable=False),
    Column("nombre_corto", String(100), nullable=True),
    Column("descripcion", Text, nullable=True),
    Column("descripcion_corta", String(500), nullable=True),
    Column("categoria_id", UNIQUEIDENTIFIER, nullable=True),
    Column("subcategoria_id", UNIQUEIDENTIFIER, nullable=True),
    Column("marca", String(100), nullable=True),
    Column("modelo", String(100), nullable=True),
    Column("linea_producto", String(100), nullable=True),
    Column("tipo_producto", String(30), nullable=False),
    Column("subtipo_producto", String(50), nullable=True),
    Column("unidad_medida_base_id", UNIQUEIDENTIFIER, nullable=False),
    Column("unidad_medida_compra_id", UNIQUEIDENTIFIER, nullable=True),
    Column("unidad_medida_venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("factor_conversion_compra", Numeric(18, 6), nullable=True, server_default="1"),
    Column("factor_conversion_venta", Numeric(18, 6), nullable=True, server_default="1"),
    Column("peso_kg", Numeric(12, 4), nullable=True),
    Column("volumen_m3", Numeric(12, 6), nullable=True),
    Column("largo_cm", Numeric(10, 2), nullable=True),
    Column("ancho_cm", Numeric(10, 2), nullable=True),
    Column("alto_cm", Numeric(10, 2), nullable=True),
    Column("color", String(50), nullable=True),
    Column("talla", String(20), nullable=True),
    Column("atributos_personalizados", Text, nullable=True),
    Column("especificaciones_tecnicas", Text, nullable=True),
    Column("maneja_inventario", Boolean, nullable=True, server_default="1"),
    Column("maneja_lotes", Boolean, nullable=True, server_default="0"),
    Column("maneja_series", Boolean, nullable=True, server_default="0"),
    Column("maneja_vencimiento", Boolean, nullable=True, server_default="0"),
    Column("dias_vida_util", Integer, nullable=True),
    Column("requiere_refrigeracion", Boolean, nullable=True, server_default="0"),
    Column("es_perecible", Boolean, nullable=True, server_default="0"),
    Column("stock_minimo", Numeric(18, 4), nullable=True),
    Column("stock_maximo", Numeric(18, 4), nullable=True),
    Column("punto_reorden", Numeric(18, 4), nullable=True),
    Column("es_comprable", Boolean, nullable=True, server_default="1"),
    Column("tiempo_entrega_dias", Integer, nullable=True),
    Column("cantidad_minima_compra", Numeric(18, 4), nullable=True),
    Column("multiplo_compra", Numeric(18, 4), nullable=True),
    Column("es_vendible", Boolean, nullable=True, server_default="1"),
    Column("requiere_autorizacion_venta", Boolean, nullable=True, server_default="0"),
    Column("es_fabricable", Boolean, nullable=True, server_default="0"),
    Column("tiene_lista_materiales", Boolean, nullable=True, server_default="0"),
    Column("metodo_costeo", String(20), nullable=True, server_default="promedio"),
    Column("costo_estandar", Numeric(18, 4), nullable=True),
    Column("costo_ultima_compra", Numeric(18, 4), nullable=True),
    Column("costo_promedio", Numeric(18, 4), nullable=True),
    Column("moneda_costo", String(3), nullable=True, server_default="PEN"),
    Column("precio_base_venta", Numeric(18, 4), nullable=True),
    Column("moneda_venta", String(3), nullable=True, server_default="PEN"),
    Column("afecto_igv", Boolean, nullable=True, server_default="1"),
    Column("porcentaje_igv", Numeric(5, 2), nullable=True, server_default="18.00"),
    Column("codigo_sunat", String(10), nullable=True),
    Column("tipo_afectacion_igv", String(2), nullable=True),
    Column("imagen_principal_url", String(500), nullable=True),
    Column("imagenes_adicionales", Text, nullable=True),
    Column("ficha_tecnica_url", String(500), nullable=True),
    Column("proveedor_habitual_id", UNIQUEIDENTIFIER, nullable=True),
    Column("estado", String(20), nullable=True, server_default="activo"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_actualizacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_sku", name="UQ_prod_sku"),
)
Index("IDX_prod_empresa", InvProductoTable.c.empresa_id, InvProductoTable.c.es_activo)
Index("IDX_prod_categoria", InvProductoTable.c.categoria_id)
Index("IDX_prod_tipo", InvProductoTable.c.tipo_producto, InvProductoTable.c.es_activo)
Index("IDX_prod_codigo_barra", InvProductoTable.c.codigo_barra)
Index("IDX_prod_nombre", InvProductoTable.c.nombre)

# ============================================================================
# TABLA: inv_almacen
# ============================================================================
InvAlmacenTable = Table(
    "inv_almacen",
    metadata_erp,
    Column("almacen_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("sucursal_id", UNIQUEIDENTIFIER, nullable=True),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_almacen", String(30), nullable=False),
    Column("direccion", String(255), nullable=True),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("es_almacen_principal", Boolean, nullable=True, server_default="0"),
    Column("permite_ventas", Boolean, nullable=True, server_default="0"),
    Column("permite_compras", Boolean, nullable=True, server_default="1"),
    Column("permite_produccion", Boolean, nullable=True, server_default="0"),
    Column("capacidad_m3", Numeric(12, 2), nullable=True),
    Column("capacidad_kg", Numeric(12, 2), nullable=True),
    Column("capacidad_unidades", Integer, nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_alm_codigo"),
)
Index("IDX_alm_empresa", InvAlmacenTable.c.empresa_id, InvAlmacenTable.c.es_activo)
Index("IDX_alm_sucursal", InvAlmacenTable.c.sucursal_id)
Index("IDX_alm_tipo", InvAlmacenTable.c.tipo_almacen)

# ============================================================================
# TABLA: inv_stock
# ============================================================================
InvStockTable = Table(
    "inv_stock",
    metadata_erp,
    Column("stock_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="CASCADE"), nullable=False),
    Column("cantidad_actual", Numeric(18, 4), nullable=False, server_default="0"),
    Column("cantidad_reservada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_transito", Numeric(18, 4), nullable=True, server_default="0"),
    Column("costo_promedio", Numeric(18, 4), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("stock_minimo", Numeric(18, 4), nullable=True),
    Column("stock_maximo", Numeric(18, 4), nullable=True),
    Column("punto_reorden", Numeric(18, 4), nullable=True),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("fecha_ultimo_movimiento", DateTime, nullable=True),
    Column("fecha_ultima_compra", DateTime, nullable=True),
    Column("fecha_ultima_venta", DateTime, nullable=True),
    Column("fecha_actualizacion", DateTime, nullable=True, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "producto_id", "almacen_id", name="UQ_stock_prod_alm"),
)
Index("IDX_stock_producto", InvStockTable.c.producto_id)
Index("IDX_stock_almacen", InvStockTable.c.almacen_id)

# ============================================================================
# TABLA: inv_tipo_movimiento
# ============================================================================
InvTipoMovimientoTable = Table(
    "inv_tipo_movimiento",
    metadata_erp,
    Column("tipo_movimiento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("clase_movimiento", String(20), nullable=False),
    Column("afecta_costo", Boolean, nullable=True, server_default="1"),
    Column("requiere_autorizacion", Boolean, nullable=True, server_default="0"),
    Column("genera_asiento_contable", Boolean, nullable=True, server_default="0"),
    Column("cuenta_contable_debito", String(20), nullable=True),
    Column("cuenta_contable_credito", String(20), nullable=True),
    Column("requiere_documento_referencia", Boolean, nullable=True, server_default="0"),
    Column("tipo_documento_referencia", String(50), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("es_tipo_sistema", Boolean, nullable=True, server_default="0"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_tm_codigo"),
)
Index("IDX_tm_empresa", InvTipoMovimientoTable.c.empresa_id, InvTipoMovimientoTable.c.es_activo)
Index("IDX_tm_clase", InvTipoMovimientoTable.c.clase_movimiento)

# ============================================================================
# TABLA: inv_movimiento
# ============================================================================
InvMovimientoTable = Table(
    "inv_movimiento",
    metadata_erp,
    Column("movimiento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_movimiento", String(20), nullable=False),
    Column("tipo_movimiento_id", UNIQUEIDENTIFIER, ForeignKey("inv_tipo_movimiento.tipo_movimiento_id"), nullable=False),
    Column("fecha_movimiento", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_contable", Date, nullable=False),
    Column("almacen_origen_id", UNIQUEIDENTIFIER, nullable=True),
    Column("almacen_destino_id", UNIQUEIDENTIFIER, nullable=True),
    Column("modulo_origen", String(10), nullable=True),
    Column("documento_referencia_tipo", String(20), nullable=True),
    Column("documento_referencia_id", UNIQUEIDENTIFIER, nullable=True),
    Column("documento_referencia_numero", String(30), nullable=True),
    Column("tercero_tipo", String(20), nullable=True),
    Column("tercero_id", UNIQUEIDENTIFIER, nullable=True),
    Column("tercero_nombre", String(200), nullable=True),
    Column("total_items", Integer, nullable=True, server_default="0"),
    Column("total_cantidad", Numeric(18, 4), nullable=True, server_default="0"),
    Column("total_costo", Numeric(18, 4), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_autorizacion", Boolean, nullable=True, server_default="0"),
    Column("autorizado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_autorizacion", DateTime, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("fecha_procesado", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_procesado_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_movimiento", name="UQ_mov_numero"),
)
Index("IDX_mov_empresa", InvMovimientoTable.c.empresa_id, InvMovimientoTable.c.estado)
Index("IDX_mov_tipo", InvMovimientoTable.c.tipo_movimiento_id)
Index("IDX_mov_fecha", InvMovimientoTable.c.fecha_movimiento)

# ============================================================================
# TABLA: inv_movimiento_detalle
# ============================================================================
InvMovimientoDetalleTable = Table(
    "inv_movimiento_detalle",
    metadata_erp,
    Column("movimiento_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("movimiento_id", UNIQUEIDENTIFIER, ForeignKey("inv_movimiento.movimiento_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=False),
    Column("cantidad_base", Numeric(18, 4), nullable=False),
    Column("costo_unitario", Numeric(18, 4), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("lote", String(50), nullable=True),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("numero_serie", String(100), nullable=True),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_movdet_movimiento", InvMovimientoDetalleTable.c.movimiento_id)
Index("IDX_movdet_producto", InvMovimientoDetalleTable.c.producto_id)
Index("IDX_movdet_lote", InvMovimientoDetalleTable.c.lote)

# ============================================================================
# TABLA: inv_inventario_fisico
# ============================================================================
InvInventarioFisicoTable = Table(
    "inv_inventario_fisico",
    metadata_erp,
    Column("inventario_fisico_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_inventario", String(20), nullable=False),
    Column("fecha_inventario", Date, nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id"), nullable=False),
    Column("tipo_inventario", String(20), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("categoria_id", UNIQUEIDENTIFIER, nullable=True),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("estado", String(20), nullable=True, server_default="en_proceso"),
    Column("supervisor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("supervisor_nombre", String(150), nullable=True),
    Column("total_productos_contados", Integer, nullable=True, server_default="0"),
    Column("total_diferencias", Integer, nullable=True, server_default="0"),
    Column("valor_diferencias", Numeric(18, 4), nullable=True, server_default="0"),
    Column("movimiento_ajuste_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_finalizacion", DateTime, nullable=True),
    Column("fecha_ajuste", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_inventario", name="UQ_invfis_numero"),
)
Index("IDX_invfis_empresa", InvInventarioFisicoTable.c.empresa_id, InvInventarioFisicoTable.c.fecha_inventario)
Index("IDX_invfis_almacen", InvInventarioFisicoTable.c.almacen_id, InvInventarioFisicoTable.c.estado)
Index("IDX_invfis_estado", InvInventarioFisicoTable.c.estado)

# ============================================================================
# TABLA: inv_inventario_fisico_detalle
# ============================================================================
InvInventarioFisicoDetalleTable = Table(
    "inv_inventario_fisico_detalle",
    metadata_erp,
    Column("inventario_fisico_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("inventario_fisico_id", UNIQUEIDENTIFIER, ForeignKey("inv_inventario_fisico.inventario_fisico_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_sistema", Numeric(18, 4), nullable=False),
    Column("cantidad_contada", Numeric(18, 4), nullable=True),
    Column("lote", String(50), nullable=True),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("costo_unitario", Numeric(18, 4), nullable=True, server_default="0"),
    Column("estado_conteo", String(20), nullable=True, server_default="pendiente"),
    Column("contador_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("contador_nombre", String(150), nullable=True),
    Column("fecha_conteo", DateTime, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("motivo_diferencia", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_invfisdet_invfis", InvInventarioFisicoDetalleTable.c.inventario_fisico_id)
Index("IDX_invfisdet_producto", InvInventarioFisicoDetalleTable.c.producto_id)
