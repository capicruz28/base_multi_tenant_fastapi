# app/infrastructure/database/tables_erp/tables_tkt.py
"""
Tablas SQLAlchemy Core para el modulo TKT (Mesa de Ayuda / Ticketing).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion TKT.
Dependencias: ORG (empresa).
"""

from sqlalchemy import (
    Table, Column, String, DateTime, ForeignKey,
    UniqueConstraint, Text, Index
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: tkt_ticket
# tiempo_resolucion_horas se calcula en servicio (diferencia fecha_resolucion - fecha_creacion)
# ============================================================================
TktTicketTable = Table(
    "tkt_ticket",
    metadata_erp,
    Column("ticket_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_ticket", String(20), nullable=False),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("solicitante_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("solicitante_nombre", String(150), nullable=True),
    Column("solicitante_email", String(100), nullable=True),
    Column("asunto", String(200), nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("categoria", String(50), nullable=True),
    Column("prioridad", String(20), nullable=True, server_default="media"),
    Column("asignado_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_asignacion", DateTime, nullable=True),
    Column("estado", String(20), nullable=True, server_default="abierto"),
    Column("fecha_resolucion", DateTime, nullable=True),
    Column("solucion", Text, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_ticket", name="UQ_tkt_numero"),
)
Index("IDX_tkt_empresa", TktTicketTable.c.empresa_id, TktTicketTable.c.fecha_creacion.desc())
Index("IDX_tkt_estado", TktTicketTable.c.estado, TktTicketTable.c.prioridad)
