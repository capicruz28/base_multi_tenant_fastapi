# app/infrastructure/database/tables_erp/tables_tax.py
"""
Tablas SQLAlchemy Core para el módulo TAX (Gestión Tributaria / Libros Electrónicos).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección TAX.
✅ Dependencias: ORG (empresa), FIN (periodo_contable).
"""

from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: tax_libro_electronico
# ============================================================================
TaxLibroElectronicoTable = Table(
    "tax_libro_electronico",
    metadata_erp,
    Column("libro_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("tipo_libro", String(30), nullable=False),
    Column("periodo_id", UNIQUEIDENTIFIER, ForeignKey("fin_periodo_contable.periodo_id", ondelete="NO ACTION"), nullable=False),
    Column("año", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("fecha_generacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("nombre_archivo", String(255), nullable=True),
    Column("ruta_archivo", String(500), nullable=True),
    Column("estado", String(20), nullable=True, server_default="generado"),
    Column("fecha_envio_sunat", DateTime, nullable=True),
    Column("codigo_respuesta_sunat", String(10), nullable=True),
    Column("total_registros", Integer, nullable=True, server_default="0"),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("generado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_libro_empresa", TaxLibroElectronicoTable.c.empresa_id, TaxLibroElectronicoTable.c["año"], TaxLibroElectronicoTable.c.mes)
Index("IDX_libro_tipo", TaxLibroElectronicoTable.c.tipo_libro, TaxLibroElectronicoTable.c["año"], TaxLibroElectronicoTable.c.mes)
