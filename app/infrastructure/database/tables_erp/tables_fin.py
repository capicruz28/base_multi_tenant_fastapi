# app/infrastructure/database/tables_erp/tables_fin.py
"""
Tablas SQLAlchemy Core para el módulo FIN (Finanzas y Contabilidad).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección FIN.
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
# TABLA: fin_plan_cuentas
# ============================================================================
FinPlanCuentasTable = Table(
    "fin_plan_cuentas",
    metadata_erp,
    Column("cuenta_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_cuenta", String(20), nullable=False),
    Column("nombre_cuenta", String(200), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("cuenta_padre_id", UNIQUEIDENTIFIER, ForeignKey("fin_plan_cuentas.cuenta_id"), nullable=True),
    Column("nivel", Integer, nullable=True, server_default="1"),
    Column("ruta_jerarquica", String(500), nullable=True),
    Column("tipo_cuenta", String(20), nullable=False),
    Column("categoria", String(30), nullable=True),
    Column("naturaleza", String(10), nullable=False),
    Column("acepta_movimientos", Boolean, nullable=True, server_default="1"),
    Column("requiere_centro_costo", Boolean, nullable=True, server_default="0"),
    Column("requiere_documento_referencia", Boolean, nullable=True, server_default="0"),
    Column("requiere_tercero", Boolean, nullable=True, server_default="0"),
    Column("acepta_moneda_extranjera", Boolean, nullable=True, server_default="1"),
    Column("aparece_balance", Boolean, nullable=True, server_default="1"),
    Column("aparece_pyg", Boolean, nullable=True, server_default="0"),
    Column("codigo_sunat", String(10), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_cuenta", name="UQ_cuenta_codigo"),
)
Index("IDX_cuenta_empresa", FinPlanCuentasTable.c.empresa_id, FinPlanCuentasTable.c.es_activo)
Index("IDX_cuenta_padre", FinPlanCuentasTable.c.cuenta_padre_id)
Index("IDX_cuenta_tipo", FinPlanCuentasTable.c.tipo_cuenta, FinPlanCuentasTable.c.nivel)

# ============================================================================
# TABLA: fin_periodo_contable
# ============================================================================
FinPeriodoContableTable = Table(
    "fin_periodo_contable",
    metadata_erp,
    Column("periodo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("año", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("estado", String(20), nullable=True, server_default="abierto"),
    Column("fecha_cierre", DateTime, nullable=True),
    Column("cerrado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "año", "mes", name="UQ_periodo"),
)
Index("IDX_periodo_empresa", FinPeriodoContableTable.c.empresa_id, FinPeriodoContableTable.c.año.desc(), FinPeriodoContableTable.c.mes.desc())

# ============================================================================
# TABLA: fin_asiento_contable
# ============================================================================
FinAsientoContableTable = Table(
    "fin_asiento_contable",
    metadata_erp,
    Column("asiento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_asiento", String(20), nullable=False),
    Column("fecha_asiento", Date, nullable=False),
    Column("periodo_id", UNIQUEIDENTIFIER, ForeignKey("fin_periodo_contable.periodo_id"), nullable=False),
    Column("tipo_asiento", String(30), nullable=False),
    Column("modulo_origen", String(10), nullable=True),
    Column("documento_origen_tipo", String(30), nullable=True),
    Column("documento_origen_id", UNIQUEIDENTIFIER, nullable=True),
    Column("documento_origen_numero", String(30), nullable=True),
    Column("glosa", String(500), nullable=False),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_cambio", Numeric(10, 4), nullable=True, server_default="1"),
    Column("total_debe", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_haber", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("requiere_aprobacion", Boolean, nullable=True, server_default="0"),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("fecha_anulacion", DateTime, nullable=True),
    Column("motivo_anulacion", String(500), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_asiento", name="UQ_asiento_numero"),
)
Index("IDX_asiento_empresa", FinAsientoContableTable.c.empresa_id, FinAsientoContableTable.c.fecha_asiento.desc())
Index("IDX_asiento_periodo", FinAsientoContableTable.c.periodo_id, FinAsientoContableTable.c.estado)
Index("IDX_asiento_estado", FinAsientoContableTable.c.estado, FinAsientoContableTable.c.fecha_asiento.desc())

# ============================================================================
# TABLA: fin_asiento_detalle
# ============================================================================
FinAsientoDetalleTable = Table(
    "fin_asiento_detalle",
    metadata_erp,
    Column("asiento_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("asiento_id", UNIQUEIDENTIFIER, ForeignKey("fin_asiento_contable.asiento_id", ondelete="CASCADE"), nullable=False),
    Column("item", Integer, nullable=False),
    Column("cuenta_id", UNIQUEIDENTIFIER, ForeignKey("fin_plan_cuentas.cuenta_id"), nullable=False),
    Column("debe", Numeric(18, 2), nullable=True, server_default="0"),
    Column("haber", Numeric(18, 2), nullable=True, server_default="0"),
    Column("debe_me", Numeric(18, 2), nullable=True, server_default="0"),
    Column("haber_me", Numeric(18, 2), nullable=True, server_default="0"),
    Column("glosa", String(500), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("documento_referencia", String(50), nullable=True),
    Column("tercero_tipo", String(20), nullable=True),
    Column("tercero_id", UNIQUEIDENTIFIER, nullable=True),
    Column("tercero_nombre", String(200), nullable=True),
    Column("tercero_documento", String(20), nullable=True),
    Column("fecha_vencimiento", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_asientodet_asiento", FinAsientoDetalleTable.c.asiento_id, FinAsientoDetalleTable.c.item)
Index("IDX_asientodet_cuenta", FinAsientoDetalleTable.c.cuenta_id)
Index("IDX_asientodet_cc", FinAsientoDetalleTable.c.centro_costo_id)
