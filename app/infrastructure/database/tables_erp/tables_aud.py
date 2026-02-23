# app/infrastructure/database/tables_erp/tables_aud.py
"""
Tablas SQLAlchemy Core para el modulo AUD (Auditoría y Trazabilidad).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion AUD.
Dependencias: ORG (empresa).
"""

from sqlalchemy import Table, Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: aud_log_auditoria
# ============================================================================
AudLogAuditoriaTable = Table(
    "aud_log_auditoria",
    metadata_erp,
    Column("log_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("fecha_evento", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("usuario_nombre", String(150), nullable=True),
    Column("modulo", String(10), nullable=False),
    Column("tabla", String(100), nullable=False),
    Column("accion", String(20), nullable=False),
    Column("registro_id", UNIQUEIDENTIFIER, nullable=True),
    Column("registro_descripcion", String(255), nullable=True),
    Column("valores_anteriores", Text, nullable=True),
    Column("valores_nuevos", Text, nullable=True),
    Column("ip_address", String(45), nullable=True),
    Column("user_agent", String(500), nullable=True),
    Column("observaciones", String(500), nullable=True),
)
