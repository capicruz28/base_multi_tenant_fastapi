# app/infrastructure/database/tables_erp/tables_bi.py
"""
Tablas SQLAlchemy Core para el modulo BI (Business Intelligence / Reportes).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion BI.
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
# TABLA: bi_reporte
# ============================================================================
BiReporteTable = Table(
    "bi_reporte",
    metadata_erp,
    Column("reporte_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_reporte", String(20), nullable=False),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("modulo_origen", String(10), nullable=True),
    Column("categoria", String(50), nullable=True),
    Column("tipo_reporte", String(20), nullable=True, server_default="sql"),
    Column("query_sql", Text, nullable=True),
    Column("configuracion_json", Text, nullable=True),
    Column("es_publico", Boolean, nullable=True, server_default="0"),
    Column("creado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_reporte", name="UQ_bi_codigo"),
)
