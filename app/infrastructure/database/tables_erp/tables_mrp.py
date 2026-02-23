# app/infrastructure/database/tables_erp/tables_mrp.py
"""
Tablas SQLAlchemy Core para el módulo MRP (Planeamiento de Materiales).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección MRP.
✅ Dependencias: ORG, INV (producto, unidad_medida), PUR (proveedor opcional).
"""

from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: mrp_plan_maestro
# ============================================================================
MrpPlanMaestroTable = Table(
    "mrp_plan_maestro",
    metadata_erp,
    Column("plan_maestro_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_plan", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("tipo_periodo", String(20), nullable=True, server_default="semanal"),
    Column("horizonte_planificacion_dias", Integer, nullable=True, server_default="90"),
    Column("punto_reorden_dias", Integer, nullable=True, server_default="15"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_calculo", DateTime, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("total_productos_planificados", Integer, nullable=True, server_default="0"),
    Column("total_requisiciones_generadas", Integer, nullable=True, server_default="0"),
    Column("total_ordenes_sugeridas", Integer, nullable=True, server_default="0"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_plan", name="UQ_planmrp_codigo"),
)
Index("IDX_planmrp_empresa", MrpPlanMaestroTable.c.empresa_id, MrpPlanMaestroTable.c.fecha_inicio.desc())
Index("IDX_planmrp_estado", MrpPlanMaestroTable.c.estado)

# ============================================================================
# TABLA: mrp_necesidad_bruta
# ============================================================================
MrpNecesidadBrutaTable = Table(
    "mrp_necesidad_bruta",
    metadata_erp,
    Column("necesidad_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("plan_maestro_id", UNIQUEIDENTIFIER, ForeignKey("mrp_plan_maestro.plan_maestro_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("fecha_requerida", Date, nullable=False),
    Column("cantidad_requerida", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="NO ACTION"), nullable=False),
    Column("origen", String(30), nullable=False),
    Column("documento_origen_id", UNIQUEIDENTIFIER, nullable=True),
    Column("documento_origen_numero", String(30), nullable=True),
    Column("prioridad", Integer, nullable=True, server_default="3"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_necbruta_plan", MrpNecesidadBrutaTable.c.plan_maestro_id, MrpNecesidadBrutaTable.c.fecha_requerida)
Index("IDX_necbruta_producto", MrpNecesidadBrutaTable.c.producto_id, MrpNecesidadBrutaTable.c.fecha_requerida)

# ============================================================================
# TABLA: mrp_explosion_materiales
# Nota: stock_disponible y cantidad_a_ordenar son calculados en BD (PERSISTED);
# en lectura se pueden obtener o calcular en servicio.
# ============================================================================
MrpExplosionMaterialesTable = Table(
    "mrp_explosion_materiales",
    metadata_erp,
    Column("explosion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("plan_maestro_id", UNIQUEIDENTIFIER, ForeignKey("mrp_plan_maestro.plan_maestro_id", ondelete="CASCADE"), nullable=False),
    Column("producto_padre_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("necesidad_padre_id", UNIQUEIDENTIFIER, nullable=True),
    Column("producto_componente_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("bom_detalle_id", UNIQUEIDENTIFIER, nullable=True),
    Column("nivel_bom", Integer, nullable=True, server_default="1"),
    Column("cantidad_necesaria", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="NO ACTION"), nullable=False),
    Column("fecha_requerida", Date, nullable=False),
    Column("stock_actual", Numeric(18, 4), nullable=True, server_default="0"),
    Column("stock_reservado", Numeric(18, 4), nullable=True, server_default="0"),
    Column("stock_transito", Numeric(18, 4), nullable=True, server_default="0"),
    Column("fecha_calculo", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_explosion_plan", MrpExplosionMaterialesTable.c.plan_maestro_id, MrpExplosionMaterialesTable.c.nivel_bom)
Index("IDX_explosion_componente", MrpExplosionMaterialesTable.c.producto_componente_id, MrpExplosionMaterialesTable.c.fecha_requerida)

# ============================================================================
# TABLA: mrp_orden_sugerida
# ============================================================================
MrpOrdenSugeridaTable = Table(
    "mrp_orden_sugerida",
    metadata_erp,
    Column("orden_sugerida_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("plan_maestro_id", UNIQUEIDENTIFIER, ForeignKey("mrp_plan_maestro.plan_maestro_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("tipo_orden", String(20), nullable=False),
    Column("cantidad_sugerida", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="NO ACTION"), nullable=False),
    Column("fecha_requerida", Date, nullable=False),
    Column("fecha_orden_sugerida", Date, nullable=False),
    Column("explosion_materiales_id", UNIQUEIDENTIFIER, nullable=True),
    Column("proveedor_sugerido_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id", ondelete="SET NULL"), nullable=True),
    Column("lead_time_dias", Integer, nullable=True),
    Column("estado", String(20), nullable=True, server_default="sugerida"),
    Column("documento_generado_tipo", String(20), nullable=True),
    Column("documento_generado_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_conversion", DateTime, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_ordsug_plan", MrpOrdenSugeridaTable.c.plan_maestro_id, MrpOrdenSugeridaTable.c.estado)
Index("IDX_ordsug_producto", MrpOrdenSugeridaTable.c.producto_id, MrpOrdenSugeridaTable.c.fecha_requerida)
Index("IDX_ordsug_estado", MrpOrdenSugeridaTable.c.estado, MrpOrdenSugeridaTable.c.tipo_orden)
