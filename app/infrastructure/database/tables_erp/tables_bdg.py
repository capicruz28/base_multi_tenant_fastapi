# app/infrastructure/database/tables_erp/tables_bdg.py
"""
Tablas SQLAlchemy Core para el módulo BDG (Presupuestos).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección BDG.
✅ Dependencias: ORG (empresa, centro_costo), FIN (plan_cuentas).
"""

from sqlalchemy import (
    Table, Column, Integer, String, DateTime, ForeignKey,
    Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: bdg_presupuesto
# porcentaje_ejecucion se calcula en servicio (monto_total_ejecutado/monto_total_presupuestado*100)
# ============================================================================
BdgPresupuestoTable = Table(
    "bdg_presupuesto",
    metadata_erp,
    Column("presupuesto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_presupuesto", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("año", Integer, nullable=False),
    Column("tipo_presupuesto", String(20), nullable=True, server_default="anual"),
    Column("monto_total_presupuestado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("monto_total_ejecutado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_presupuesto", name="UQ_bdg_codigo"),
)
Index("IDX_bdg_empresa", BdgPresupuestoTable.c.empresa_id, BdgPresupuestoTable.c["año"])

# ============================================================================
# TABLA: bdg_presupuesto_detalle
# monto_disponible se calcula en servicio (monto_presupuestado - monto_ejecutado)
# ============================================================================
BdgPresupuestoDetalleTable = Table(
    "bdg_presupuesto_detalle",
    metadata_erp,
    Column("presupuesto_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("presupuesto_id", UNIQUEIDENTIFIER, ForeignKey("bdg_presupuesto.presupuesto_id", ondelete="CASCADE"), nullable=False),
    Column("cuenta_id", UNIQUEIDENTIFIER, ForeignKey("fin_plan_cuentas.cuenta_id", ondelete="NO ACTION"), nullable=False),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("mes", Integer, nullable=True),
    Column("monto_presupuestado", Numeric(18, 2), nullable=False),
    Column("monto_ejecutado", Numeric(18, 2), nullable=True, server_default="0"),
    Column("observaciones", String(255), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_bdgdet_presupuesto", BdgPresupuestoDetalleTable.c.presupuesto_id)
