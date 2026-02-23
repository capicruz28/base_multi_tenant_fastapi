# app/infrastructure/database/tables_erp/tables_mfg.py
"""
Tablas SQLAlchemy Core para el módulo MFG (Manufactura y Producción).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección MFG.
✅ Dependencias: ORG, INV (productos, almacenes, unidad_medida). Opcional: QMS (plan_inspeccion).
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: mfg_centro_trabajo
# ============================================================================
MfgCentroTrabajoTable = Table(
    "mfg_centro_trabajo",
    metadata_erp,
    Column("centro_trabajo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="SET NULL"), nullable=True),
    Column("ubicacion_fisica", String(100), nullable=True),
    Column("tipo_centro", String(30), nullable=False),
    Column("capacidad_horas_dia", Numeric(8, 2), nullable=True),
    Column("capacidad_unidades_hora", Numeric(12, 2), nullable=True),
    Column("eficiencia_promedio", Numeric(5, 2), nullable=True, server_default="85"),
    Column("costo_hora_maquina", Numeric(12, 2), nullable=True),
    Column("costo_setup", Numeric(12, 2), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("requiere_mantenimiento", Boolean, nullable=True, server_default="1"),
    Column("frecuencia_mantenimiento_dias", Integer, nullable=True),
    Column("ultima_fecha_mantenimiento", Date, nullable=True),
    Column("estado_centro", String(20), nullable=True, server_default="disponible"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_ct_codigo"),
)
Index("IDX_ct_empresa", MfgCentroTrabajoTable.c.empresa_id, MfgCentroTrabajoTable.c.es_activo)
Index("IDX_ct_estado", MfgCentroTrabajoTable.c.estado_centro)

# ============================================================================
# TABLA: mfg_operacion
# ============================================================================
MfgOperacionTable = Table(
    "mfg_operacion",
    metadata_erp,
    Column("operacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("centro_trabajo_id", UNIQUEIDENTIFIER, ForeignKey("mfg_centro_trabajo.centro_trabajo_id", ondelete="SET NULL"), nullable=True),
    Column("tiempo_setup_minutos", Numeric(10, 2), nullable=True),
    Column("tiempo_operacion_minutos", Numeric(10, 2), nullable=True),
    Column("requiere_herramientas", Text, nullable=True),
    Column("requiere_habilidad", String(100), nullable=True),
    Column("requiere_inspeccion", Boolean, nullable=True, server_default="0"),
    Column("plan_inspeccion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_oper_codigo"),
)
Index("IDX_oper_empresa", MfgOperacionTable.c.empresa_id, MfgOperacionTable.c.es_activo)
Index("IDX_oper_ct", MfgOperacionTable.c.centro_trabajo_id)

# ============================================================================
# TABLA: mfg_lista_materiales (BOM)
# ============================================================================
MfgListaMaterialesTable = Table(
    "mfg_lista_materiales",
    metadata_erp,
    Column("bom_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_bom", String(20), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("version", String(10), nullable=True, server_default="1.0"),
    Column("fecha_vigencia_desde", Date, nullable=False),
    Column("fecha_vigencia_hasta", Date, nullable=True),
    Column("cantidad_base", Numeric(18, 4), nullable=True, server_default="1"),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("tipo_bom", String(20), nullable=True, server_default="produccion"),
    Column("porcentaje_desperdicio", Numeric(5, 2), nullable=True, server_default="0"),
    Column("es_bom_activa", Boolean, nullable=True, server_default="1"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", Date, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_bom", name="UQ_bom_codigo"),
)
Index("IDX_bom_empresa", MfgListaMaterialesTable.c.empresa_id, MfgListaMaterialesTable.c.es_bom_activa)
Index("IDX_bom_producto", MfgListaMaterialesTable.c.producto_id, MfgListaMaterialesTable.c.es_bom_activa)

# ============================================================================
# TABLA: mfg_lista_materiales_detalle
# ============================================================================
MfgListaMaterialesDetalleTable = Table(
    "mfg_lista_materiales_detalle",
    metadata_erp,
    Column("bom_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("bom_id", UNIQUEIDENTIFIER, ForeignKey("mfg_lista_materiales.bom_id", ondelete="CASCADE"), nullable=False),
    Column("producto_componente_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("tipo_componente", String(20), nullable=True, server_default="material"),
    Column("es_critico", Boolean, nullable=True, server_default="0"),
    Column("porcentaje_desperdicio", Numeric(5, 2), nullable=True, server_default="0"),
    Column("tiene_sustitutos", Boolean, nullable=True, server_default="0"),
    Column("productos_sustitutos", Text, nullable=True),
    Column("secuencia", Integer, nullable=True, server_default="0"),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_bomdet_bom", MfgListaMaterialesDetalleTable.c.bom_id, MfgListaMaterialesDetalleTable.c.secuencia)
Index("IDX_bomdet_componente", MfgListaMaterialesDetalleTable.c.producto_componente_id)

# ============================================================================
# TABLA: mfg_ruta_fabricacion
# ============================================================================
MfgRutaFabricacionTable = Table(
    "mfg_ruta_fabricacion",
    metadata_erp,
    Column("ruta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_ruta", String(20), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("bom_id", UNIQUEIDENTIFIER, ForeignKey("mfg_lista_materiales.bom_id", ondelete="SET NULL"), nullable=True),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("version", String(10), nullable=True, server_default="1.0"),
    Column("tiempo_total_setup_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("tiempo_total_operacion_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("es_ruta_activa", Boolean, nullable=True, server_default="1"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_ruta", name="UQ_ruta_codigo"),
)
Index("IDX_ruta_empresa", MfgRutaFabricacionTable.c.empresa_id, MfgRutaFabricacionTable.c.es_ruta_activa)
Index("IDX_ruta_producto", MfgRutaFabricacionTable.c.producto_id, MfgRutaFabricacionTable.c.es_ruta_activa)

# ============================================================================
# TABLA: mfg_ruta_fabricacion_detalle
# ============================================================================
MfgRutaFabricacionDetalleTable = Table(
    "mfg_ruta_fabricacion_detalle",
    metadata_erp,
    Column("ruta_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("ruta_id", UNIQUEIDENTIFIER, ForeignKey("mfg_ruta_fabricacion.ruta_id", ondelete="CASCADE"), nullable=False),
    Column("secuencia", Integer, nullable=False),
    Column("operacion_id", UNIQUEIDENTIFIER, ForeignKey("mfg_operacion.operacion_id"), nullable=False),
    Column("centro_trabajo_id", UNIQUEIDENTIFIER, ForeignKey("mfg_centro_trabajo.centro_trabajo_id"), nullable=False),
    Column("tiempo_setup_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("tiempo_operacion_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("es_operacion_critica", Boolean, nullable=True, server_default="0"),
    Column("permite_operaciones_paralelas", Boolean, nullable=True, server_default="0"),
    Column("instrucciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_rutadet_ruta", MfgRutaFabricacionDetalleTable.c.ruta_id, MfgRutaFabricacionDetalleTable.c.secuencia)

# ============================================================================
# TABLA: mfg_orden_produccion
# ============================================================================
MfgOrdenProduccionTable = Table(
    "mfg_orden_produccion",
    metadata_erp,
    Column("orden_produccion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_op", String(20), nullable=False),
    Column("fecha_emision", Date, nullable=False, server_default=func.getdate()),
    Column("fecha_inicio_programada", Date, nullable=False),
    Column("fecha_fin_programada", Date, nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("bom_id", UNIQUEIDENTIFIER, ForeignKey("mfg_lista_materiales.bom_id"), nullable=False),
    Column("ruta_fabricacion_id", UNIQUEIDENTIFIER, ForeignKey("mfg_ruta_fabricacion.ruta_id", ondelete="SET NULL"), nullable=True),
    Column("cantidad_planeada", Numeric(18, 4), nullable=False),
    Column("cantidad_producida", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_defectuosa", Numeric(18, 4), nullable=True, server_default="0"),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("almacen_destino_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="SET NULL"), nullable=True),
    Column("prioridad", Integer, nullable=True, server_default="3"),
    Column("tipo_orden", String(20), nullable=True, server_default="normal"),
    Column("documento_origen_tipo", String(30), nullable=True),
    Column("documento_origen_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_inicio_real", DateTime, nullable=True),
    Column("fecha_fin_real", DateTime, nullable=True),
    Column("costo_materiales", Numeric(18, 2), nullable=True, server_default="0"),
    Column("costo_mano_obra", Numeric(18, 2), nullable=True, server_default="0"),
    Column("costo_cif", Numeric(18, 2), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_op", name="UQ_op_numero"),
)
Index("IDX_op_empresa", MfgOrdenProduccionTable.c.empresa_id, MfgOrdenProduccionTable.c.fecha_emision.desc())
Index("IDX_op_producto", MfgOrdenProduccionTable.c.producto_id, MfgOrdenProduccionTable.c.estado)
Index("IDX_op_estado", MfgOrdenProduccionTable.c.estado, MfgOrdenProduccionTable.c.fecha_inicio_programada)
Index("IDX_op_fecha_programada", MfgOrdenProduccionTable.c.fecha_inicio_programada, MfgOrdenProduccionTable.c.estado)

# ============================================================================
# TABLA: mfg_orden_produccion_operacion
# ============================================================================
MfgOrdenProduccionOperacionTable = Table(
    "mfg_orden_produccion_operacion",
    metadata_erp,
    Column("op_operacion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("orden_produccion_id", UNIQUEIDENTIFIER, ForeignKey("mfg_orden_produccion.orden_produccion_id", ondelete="CASCADE"), nullable=False),
    Column("ruta_detalle_id", UNIQUEIDENTIFIER, ForeignKey("mfg_ruta_fabricacion_detalle.ruta_detalle_id", ondelete="SET NULL"), nullable=True),
    Column("operacion_id", UNIQUEIDENTIFIER, ForeignKey("mfg_operacion.operacion_id"), nullable=False),
    Column("centro_trabajo_id", UNIQUEIDENTIFIER, ForeignKey("mfg_centro_trabajo.centro_trabajo_id"), nullable=False),
    Column("secuencia", Integer, nullable=False),
    Column("tiempo_setup_planificado_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("tiempo_operacion_planificado_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("tiempo_setup_real_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("tiempo_operacion_real_minutos", Numeric(10, 2), nullable=True, server_default="0"),
    Column("fecha_inicio_programada", DateTime, nullable=True),
    Column("fecha_fin_programada", DateTime, nullable=True),
    Column("fecha_inicio_real", DateTime, nullable=True),
    Column("fecha_fin_real", DateTime, nullable=True),
    Column("cantidad_procesada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_aprobada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_rechazada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("operario_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("operario_nombre", String(150), nullable=True),
    Column("estado", String(20), nullable=True, server_default="pendiente"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_opoper_op", MfgOrdenProduccionOperacionTable.c.orden_produccion_id, MfgOrdenProduccionOperacionTable.c.secuencia)
Index("IDX_opoper_estado", MfgOrdenProduccionOperacionTable.c.estado, MfgOrdenProduccionOperacionTable.c.fecha_inicio_programada)
Index("IDX_opoper_ct", MfgOrdenProduccionOperacionTable.c.centro_trabajo_id, MfgOrdenProduccionOperacionTable.c.estado)

# ============================================================================
# TABLA: mfg_consumo_materiales
# ============================================================================
MfgConsumoMaterialesTable = Table(
    "mfg_consumo_materiales",
    metadata_erp,
    Column("consumo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("orden_produccion_id", UNIQUEIDENTIFIER, ForeignKey("mfg_orden_produccion.orden_produccion_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("cantidad_planificada", Numeric(18, 4), nullable=False),
    Column("cantidad_consumida", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("lote", String(50), nullable=True),
    Column("almacen_origen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="SET NULL"), nullable=True),
    Column("costo_unitario", Numeric(18, 4), nullable=True, server_default="0"),
    Column("movimiento_inventario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_consumo", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_registro_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_consumo_op", MfgConsumoMaterialesTable.c.orden_produccion_id)
Index("IDX_consumo_producto", MfgConsumoMaterialesTable.c.producto_id, MfgConsumoMaterialesTable.c.fecha_consumo.desc())
