# app/infrastructure/database/tables_erp/tables_wfl.py
"""
Tablas SQLAlchemy Core para el modulo WFL (Flujos de Trabajo / Workflow).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion WFL.
Dependencias: ORG (empresa).
"""

from sqlalchemy import (
    Table, Column, String, DateTime, ForeignKey,
    Boolean, Text, UniqueConstraint
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: wfl_flujo_trabajo
# ============================================================================
WflFlujoTrabajoTable = Table(
    "wfl_flujo_trabajo",
    metadata_erp,
    Column("flujo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_flujo", String(20), nullable=False),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_flujo", String(30), nullable=False),
    Column("modulo_aplicable", String(10), nullable=True),
    Column("definicion_pasos", Text, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_flujo", name="UQ_wfl_codigo"),
)
