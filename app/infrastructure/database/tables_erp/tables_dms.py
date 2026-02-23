# app/infrastructure/database/tables_erp/tables_dms.py
"""
Tablas SQLAlchemy Core para el modulo DMS (Gestion Documental).

Multi-tenant: Todas las tablas tienen cliente_id.
Alineado con TABLAS_BD_ERP_COMPLETO.sql seccion DMS.
Dependencias: ORG (empresa).
"""

from sqlalchemy import (
    Table, Column, String, DateTime, ForeignKey,
    Text, BigInteger, Boolean, Index
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: dms_documento
# ============================================================================
DmsDocumentoTable = Table(
    "dms_documento",
    metadata_erp,
    Column("documento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_documento", String(20), nullable=True),
    Column("nombre_archivo", String(255), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_documento", String(50), nullable=False),
    Column("categoria", String(50), nullable=True),
    Column("ruta_archivo", String(500), nullable=False),
    Column("tamaño_bytes", BigInteger, nullable=True),
    Column("extension", String(10), nullable=True),
    Column("mime_type", String(100), nullable=True),
    Column("carpeta", String(255), nullable=True),
    Column("tags", Text, nullable=True),
    Column("entidad_tipo", String(30), nullable=True),
    Column("entidad_id", UNIQUEIDENTIFIER, nullable=True),
    Column("version", String(10), nullable=True, server_default="1.0"),
    Column("documento_padre_id", UNIQUEIDENTIFIER, ForeignKey("dms_documento.documento_id", ondelete="NO ACTION"), nullable=True),
    Column("es_confidencial", Boolean, nullable=True, server_default="0"),
    Column("nivel_acceso", String(20), nullable=True, server_default="general"),
    Column("estado", String(20), nullable=True, server_default="activo"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_modificacion", DateTime, nullable=True),
    Column("subido_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_dms_empresa", DmsDocumentoTable.c.empresa_id, DmsDocumentoTable.c.fecha_creacion.desc())
Index("IDX_dms_tipo", DmsDocumentoTable.c.tipo_documento, DmsDocumentoTable.c.categoria)
