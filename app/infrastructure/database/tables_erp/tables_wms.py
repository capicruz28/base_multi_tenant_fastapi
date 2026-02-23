# app/infrastructure/database/tables_erp/tables_wms.py
"""
Tablas SQLAlchemy Core para el módulo WMS (Warehouse Management System).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección WMS.
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
# TABLA: wms_zona_almacen
# ============================================================================
WmsZonaAlmacenTable = Table(
    "wms_zona_almacen",
    metadata_erp,
    Column("zona_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_zona", String(30), nullable=False),
    Column("temperatura_min", Numeric(5, 2), nullable=True),
    Column("temperatura_max", Numeric(5, 2), nullable=True),
    Column("requiere_control_temperatura", Boolean, nullable=True, server_default="0"),
    Column("capacidad_m3", Numeric(12, 2), nullable=True),
    Column("capacidad_kg", Numeric(12, 2), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "almacen_id", "codigo", name="UQ_zona_codigo"),
)
Index("IDX_zona_almacen", WmsZonaAlmacenTable.c.almacen_id, WmsZonaAlmacenTable.c.es_activo)
Index("IDX_zona_tipo", WmsZonaAlmacenTable.c.tipo_zona)

# ============================================================================
# TABLA: wms_ubicacion
# ============================================================================
WmsUbicacionTable = Table(
    "wms_ubicacion",
    metadata_erp,
    Column("ubicacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="CASCADE"), nullable=False),
    Column("zona_id", UNIQUEIDENTIFIER, ForeignKey("wms_zona_almacen.zona_id", ondelete="SET NULL"), nullable=True),
    Column("codigo_ubicacion", String(30), nullable=False),
    Column("pasillo", String(10), nullable=True),
    Column("rack", String(10), nullable=True),
    Column("nivel", Integer, nullable=True),
    Column("posicion", String(10), nullable=True),
    Column("nombre", String(100), nullable=True),
    Column("tipo_ubicacion", String(30), nullable=True, server_default="rack"),
    Column("capacidad_kg", Numeric(12, 2), nullable=True),
    Column("capacidad_m3", Numeric(12, 4), nullable=True),
    Column("capacidad_pallets", Integer, nullable=True),
    Column("alto_cm", Numeric(10, 2), nullable=True),
    Column("ancho_cm", Numeric(10, 2), nullable=True),
    Column("profundidad_cm", Numeric(10, 2), nullable=True),
    Column("permite_multiples_productos", Boolean, nullable=True, server_default="1"),
    Column("permite_multiples_lotes", Boolean, nullable=True, server_default="1"),
    Column("es_ubicacion_picking", Boolean, nullable=True, server_default="0"),
    Column("estado_ubicacion", String(20), nullable=True, server_default="disponible"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "almacen_id", "codigo_ubicacion", name="UQ_ubic_codigo"),
)
Index("IDX_ubic_almacen", WmsUbicacionTable.c.almacen_id, WmsUbicacionTable.c.es_activo)
Index("IDX_ubic_zona", WmsUbicacionTable.c.zona_id)
Index("IDX_ubic_estado", WmsUbicacionTable.c.estado_ubicacion)
Index("IDX_ubic_pasillo_rack", WmsUbicacionTable.c.almacen_id, WmsUbicacionTable.c.pasillo, WmsUbicacionTable.c.rack, WmsUbicacionTable.c.nivel)

# ============================================================================
# TABLA: wms_stock_ubicacion
# ============================================================================
WmsStockUbicacionTable = Table(
    "wms_stock_ubicacion",
    metadata_erp,
    Column("stock_ubicacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="CASCADE"), nullable=False),
    Column("ubicacion_id", UNIQUEIDENTIFIER, ForeignKey("wms_ubicacion.ubicacion_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("lote", String(50), nullable=True),
    Column("numero_serie", String(100), nullable=True),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("estado_stock", String(20), nullable=True, server_default="disponible"),
    Column("motivo_bloqueo", String(255), nullable=True),
    Column("fecha_ingreso", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
)
Index("IDX_stockubic_ubicacion", WmsStockUbicacionTable.c.ubicacion_id)
Index("IDX_stockubic_producto", WmsStockUbicacionTable.c.producto_id, WmsStockUbicacionTable.c.almacen_id)
Index("IDX_stockubic_lote", WmsStockUbicacionTable.c.lote)
Index("IDX_stockubic_disponible", WmsStockUbicacionTable.c.estado_stock)

# ============================================================================
# TABLA: wms_tarea
# ============================================================================
WmsTareaTable = Table(
    "wms_tarea",
    metadata_erp,
    Column("tarea_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="CASCADE"), nullable=False),
    Column("numero_tarea", String(20), nullable=False),
    Column("tipo_tarea", String(30), nullable=False),
    Column("prioridad", Integer, nullable=True, server_default="3"),
    Column("ubicacion_origen_id", UNIQUEIDENTIFIER, ForeignKey("wms_ubicacion.ubicacion_id"), nullable=True),
    Column("ubicacion_destino_id", UNIQUEIDENTIFIER, ForeignKey("wms_ubicacion.ubicacion_id"), nullable=True),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=True),
    Column("cantidad_planeada", Numeric(18, 4), nullable=True),
    Column("cantidad_completada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, nullable=True),
    Column("documento_referencia_tipo", String(30), nullable=True),
    Column("documento_referencia_id", UNIQUEIDENTIFIER, nullable=True),
    Column("asignado_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("asignado_nombre", String(150), nullable=True),
    Column("fecha_asignacion", DateTime, nullable=True),
    Column("estado", String(20), nullable=True, server_default="pendiente"),
    Column("fecha_inicio", DateTime, nullable=True),
    Column("fecha_completado", DateTime, nullable=True),
    Column("instrucciones", Text, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "almacen_id", "numero_tarea", name="UQ_tarea_numero"),
)
Index("IDX_tarea_almacen", WmsTareaTable.c.almacen_id, WmsTareaTable.c.estado, WmsTareaTable.c.prioridad)
Index("IDX_tarea_asignado", WmsTareaTable.c.asignado_usuario_id, WmsTareaTable.c.estado)
Index("IDX_tarea_estado", WmsTareaTable.c.estado, WmsTareaTable.c.fecha_creacion.desc())
Index("IDX_tarea_tipo", WmsTareaTable.c.tipo_tarea, WmsTareaTable.c.estado)
