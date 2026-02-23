# app/infrastructure/database/tables_erp/tables_pm.py
"""
Tablas SQLAlchemy Core para el modulo PM (Gestion de Proyectos).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion PM.
Dependencias: ORG (empresa). Opcional: SLS (cliente_venta_id).
"""

from sqlalchemy import (
    Table, Column, String, DateTime, ForeignKey,
    UniqueConstraint, Numeric, Text, Date
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: pm_proyecto
# ============================================================================
PmProyectoTable = Table(
    "pm_proyecto",
    metadata_erp,
    Column("proyecto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_proyecto", String(20), nullable=False),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin_estimada", Date, nullable=True),
    Column("fecha_fin_real", Date, nullable=True),
    Column("presupuesto", Numeric(18, 2), nullable=True),
    Column("costo_real", Numeric(18, 2), nullable=True, server_default="0"),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("estado", String(20), nullable=True, server_default="planificado"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_proyecto", name="UQ_proy_codigo"),
)
