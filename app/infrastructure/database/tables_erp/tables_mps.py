# app/infrastructure/database/tables_erp/tables_mps.py
"""
Tablas SQLAlchemy Core para el módulo MPS (Plan Maestro de Producción).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección MPS.
✅ Dependencias: ORG, INV (producto, unidad_medida).
"""

from sqlalchemy import (
    Table, Column, Integer, String, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: mps_pronostico_demanda
# Nota: desviacion es calculada en BD; cantidad_real se puede actualizar.
# ============================================================================
MpsPronosticoDemandaTable = Table(
    "mps_pronostico_demanda",
    metadata_erp,
    Column("pronostico_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("año", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("semana", Integer, nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("cantidad_pronosticada", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="NO ACTION"), nullable=False),
    Column("metodo_pronostico", String(30), nullable=True),
    Column("confiabilidad_porcentaje", Numeric(5, 2), nullable=True),
    Column("cantidad_real", Numeric(18, 4), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_pronos_empresa", MpsPronosticoDemandaTable.c.empresa_id, MpsPronosticoDemandaTable.c["año"].desc(), MpsPronosticoDemandaTable.c.mes.desc())
Index("IDX_pronos_producto", MpsPronosticoDemandaTable.c.producto_id, MpsPronosticoDemandaTable.c.fecha_inicio)

# ============================================================================
# TABLA: mps_plan_produccion
# ============================================================================
MpsPlanProduccionTable = Table(
    "mps_plan_produccion",
    metadata_erp,
    Column("plan_produccion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_plan", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_plan", name="UQ_planprod_codigo"),
)
Index("IDX_planprod_empresa", MpsPlanProduccionTable.c.empresa_id, MpsPlanProduccionTable.c.fecha_inicio.desc())
Index("IDX_planprod_estado", MpsPlanProduccionTable.c.estado)

# ============================================================================
# TABLA: mps_plan_produccion_detalle
# Nota: porcentaje_uso_capacidad es calculado en BD; se puede devolver en servicio.
# ============================================================================
MpsPlanProduccionDetalleTable = Table(
    "mps_plan_produccion_detalle",
    metadata_erp,
    Column("plan_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("plan_produccion_id", UNIQUEIDENTIFIER, ForeignKey("mps_plan_produccion.plan_produccion_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="NO ACTION"), nullable=False),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("pronostico_demanda", Numeric(18, 4), nullable=True, server_default="0"),
    Column("pedidos_firmes", Numeric(18, 4), nullable=True, server_default="0"),
    Column("stock_inicial", Numeric(18, 4), nullable=True, server_default="0"),
    Column("stock_seguridad", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_planificada", Numeric(18, 4), nullable=False),
    Column("cantidad_producida", Numeric(18, 4), nullable=True, server_default="0"),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="NO ACTION"), nullable=False),
    Column("capacidad_disponible", Numeric(18, 4), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_planproddet_plan", MpsPlanProduccionDetalleTable.c.plan_produccion_id, MpsPlanProduccionDetalleTable.c.fecha_inicio)
Index("IDX_planproddet_producto", MpsPlanProduccionDetalleTable.c.producto_id, MpsPlanProduccionDetalleTable.c.fecha_inicio)
