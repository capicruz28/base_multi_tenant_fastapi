# app/infrastructure/database/tables_erp/tables_svc.py
"""
Tablas SQLAlchemy Core para el modulo SVC (Ordenes de Servicio).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion SVC.
Dependencias: ORG (empresa). Opcional: SLS (cliente_venta_id).
"""

from sqlalchemy import (
    Table, Column, String, DateTime, ForeignKey,
    UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: svc_orden_servicio
# ============================================================================
SvcOrdenServicioTable = Table(
    "svc_orden_servicio",
    metadata_erp,
    Column("orden_servicio_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_os", String(20), nullable=False),
    Column("fecha_solicitud", DateTime, nullable=False, server_default=func.getdate()),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, nullable=True),
    Column("tipo_servicio", String(50), nullable=False),
    Column("descripcion_servicio", Text, nullable=True),
    Column("tecnico_asignado_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_inicio_programada", DateTime, nullable=True),
    Column("fecha_inicio_real", DateTime, nullable=True),
    Column("fecha_fin_real", DateTime, nullable=True),
    Column("estado", String(20), nullable=True, server_default="solicitada"),
    Column("monto_servicio", Numeric(18, 2), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "numero_os", name="UQ_os_numero"),
)
