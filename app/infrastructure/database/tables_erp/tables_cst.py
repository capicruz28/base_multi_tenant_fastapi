# app/infrastructure/database/tables_erp/tables_cst.py
"""
Tablas SQLAlchemy Core para el módulo CST (Costeo de Productos).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección CST.
✅ Dependencias: ORG (empresa), INV (producto). Opcional: MFG (orden_produccion).
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, Numeric
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: cst_centro_costo_tipo
# ============================================================================
CstCentroCostoTipoTable = Table(
    "cst_centro_costo_tipo",
    metadata_erp,
    Column("cc_tipo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("tipo_clasificacion", String(30), nullable=False),
    Column("base_distribucion", String(30), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_cctipo_codigo"),
)
Index("IDX_cctipo_empresa", CstCentroCostoTipoTable.c.empresa_id, CstCentroCostoTipoTable.c.es_activo)

# ============================================================================
# TABLA: cst_producto_costo
# Nota: costo_total y costo_unitario son calculados en BD; se devuelven en servicio.
# ============================================================================
CstProductoCostoTable = Table(
    "cst_producto_costo",
    metadata_erp,
    Column("producto_costo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("año", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("costo_material_directo", Numeric(18, 4), nullable=True, server_default="0"),
    Column("costo_mano_obra_directa", Numeric(18, 4), nullable=True, server_default="0"),
    Column("costo_indirecto_fabricacion", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_producida", Numeric(18, 4), nullable=True, server_default="0"),
    Column("orden_produccion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("metodo_costeo", String(20), nullable=True, server_default="real"),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_calculo", DateTime, nullable=True, server_default=func.getdate()),
)
Index("IDX_prodcst_producto", CstProductoCostoTable.c.producto_id, CstProductoCostoTable.c["año"].desc(), CstProductoCostoTable.c.mes.desc())
