# app/infrastructure/database/tables_erp/tables_prc.py
"""
Tablas SQLAlchemy Core para el módulo PRC (Gestión de Precios y Promociones).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección PRC.
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
# TABLA: prc_lista_precio
# ============================================================================
PrcListaPrecioTable = Table(
    "prc_lista_precio",
    metadata_erp,
    Column("lista_precio_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_lista", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_lista", String(30), nullable=True, server_default="general"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("fecha_vigencia_desde", Date, nullable=False),
    Column("fecha_vigencia_hasta", Date, nullable=True),
    Column("incluye_igv", Boolean, nullable=True, server_default="1"),
    Column("permite_descuentos", Boolean, nullable=True, server_default="1"),
    Column("descuento_maximo_porcentaje", Numeric(5, 2), nullable=True, server_default="10"),
    Column("es_lista_defecto", Boolean, nullable=True, server_default="0"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_lista", name="UQ_listaprc_codigo"),
)
Index("IDX_listaprc_empresa", PrcListaPrecioTable.c.empresa_id, PrcListaPrecioTable.c.es_activo)
Index("IDX_listaprc_vigencia", PrcListaPrecioTable.c.fecha_vigencia_desde, PrcListaPrecioTable.c.fecha_vigencia_hasta)

# ============================================================================
# TABLA: prc_lista_precio_detalle
# ============================================================================
PrcListaPrecioDetalleTable = Table(
    "prc_lista_precio_detalle",
    metadata_erp,
    Column("lista_precio_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("lista_precio_id", UNIQUEIDENTIFIER, ForeignKey("prc_lista_precio.lista_precio_id", ondelete="CASCADE"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=False),
    Column("precio_unitario", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("cantidad_minima", Numeric(18, 4), nullable=True, server_default="1"),
    Column("cantidad_maxima", Numeric(18, 4), nullable=True),
    Column("descuento_maximo_porcentaje", Numeric(5, 2), nullable=True),
    Column("fecha_vigencia_desde", Date, nullable=True),
    Column("fecha_vigencia_hasta", Date, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
)
Index("IDX_listadet_lista", PrcListaPrecioDetalleTable.c.lista_precio_id, PrcListaPrecioDetalleTable.c.es_activo)
Index("IDX_listadet_producto", PrcListaPrecioDetalleTable.c.producto_id, PrcListaPrecioDetalleTable.c.lista_precio_id)

# ============================================================================
# TABLA: prc_promocion
# ============================================================================
PrcPromocionTable = Table(
    "prc_promocion",
    metadata_erp,
    Column("promocion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_promocion", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_promocion", String(30), nullable=False),
    Column("aplica_a", String(20), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, nullable=True),
    Column("categoria_id", UNIQUEIDENTIFIER, nullable=True),
    Column("marca", String(100), nullable=True),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=True),
    Column("descuento_monto", Numeric(18, 2), nullable=True),
    Column("reglas_aplicacion", Text, nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=False),
    Column("cantidad_maxima_usos", Integer, nullable=True),
    Column("cantidad_usos_actuales", Integer, nullable=True, server_default="0"),
    Column("monto_maximo_descuento", Numeric(18, 2), nullable=True),
    Column("es_combinable", Boolean, nullable=True, server_default="0"),
    Column("aplica_canal_venta", Text, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("requiere_codigo_cupon", Boolean, nullable=True, server_default="0"),
    Column("codigo_cupon", String(30), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_promocion", name="UQ_promo_codigo"),
)
Index("IDX_promo_empresa", PrcPromocionTable.c.empresa_id, PrcPromocionTable.c.es_activo)
Index("IDX_promo_vigencia", PrcPromocionTable.c.fecha_inicio, PrcPromocionTable.c.fecha_fin, PrcPromocionTable.c.es_activo)
Index("IDX_promo_producto", PrcPromocionTable.c.producto_id)
