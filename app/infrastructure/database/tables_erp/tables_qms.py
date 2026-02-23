# app/infrastructure/database/tables_erp/tables_qms.py
"""
Tablas SQLAlchemy Core para el módulo QMS (Quality Management System).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección QMS.
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
# TABLA: qms_parametro_calidad
# ============================================================================
QmsParametroCalidadTable = Table(
    "qms_parametro_calidad",
    metadata_erp,
    Column("parametro_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_parametro", String(30), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id", ondelete="SET NULL"), nullable=True),
    Column("valor_minimo", Numeric(18, 4), nullable=True),
    Column("valor_maximo", Numeric(18, 4), nullable=True),
    Column("valor_objetivo", Numeric(18, 4), nullable=True),
    Column("opciones_permitidas", Text, nullable=True),
    Column("metodo_inspeccion", String(255), nullable=True),
    Column("requiere_equipo", String(100), nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_qms_param_codigo"),
)
Index("IDX_qms_param_empresa", QmsParametroCalidadTable.c.empresa_id, QmsParametroCalidadTable.c.es_activo)
Index("IDX_qms_param_tipo", QmsParametroCalidadTable.c.tipo_parametro)

# ============================================================================
# TABLA: qms_plan_inspeccion
# ============================================================================
QmsPlanInspeccionTable = Table(
    "qms_plan_inspeccion",
    metadata_erp,
    Column("plan_inspeccion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("aplica_a", String(20), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="CASCADE"), nullable=True),
    Column("categoria_id", UNIQUEIDENTIFIER, ForeignKey("inv_categoria_producto.categoria_id", ondelete="CASCADE"), nullable=True),
    Column("tipo_inspeccion", String(30), nullable=False),
    Column("tipo_muestreo", String(30), nullable=True, server_default="total"),
    Column("porcentaje_muestreo", Numeric(5, 2), nullable=True),
    Column("tabla_muestreo", String(50), nullable=True),
    Column("nivel_aceptacion_criticos", Numeric(5, 2), nullable=True, server_default="0"),
    Column("nivel_aceptacion_mayores", Numeric(5, 2), nullable=True, server_default="2.5"),
    Column("nivel_aceptacion_menores", Numeric(5, 2), nullable=True, server_default="4.0"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_vigencia_desde", Date, nullable=True),
    Column("fecha_vigencia_hasta", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo", name="UQ_qms_plan_codigo"),
)
Index("IDX_qms_plan_empresa", QmsPlanInspeccionTable.c.empresa_id, QmsPlanInspeccionTable.c.es_activo)
Index("IDX_qms_plan_producto", QmsPlanInspeccionTable.c.producto_id)
Index("IDX_qms_plan_categoria", QmsPlanInspeccionTable.c.categoria_id)

# ============================================================================
# TABLA: qms_plan_inspeccion_detalle
# ============================================================================
QmsPlanInspeccionDetalleTable = Table(
    "qms_plan_inspeccion_detalle",
    metadata_erp,
    Column("plan_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("plan_inspeccion_id", UNIQUEIDENTIFIER, ForeignKey("qms_plan_inspeccion.plan_inspeccion_id", ondelete="CASCADE"), nullable=False),
    Column("parametro_calidad_id", UNIQUEIDENTIFIER, ForeignKey("qms_parametro_calidad.parametro_id"), nullable=False),
    Column("orden", Integer, nullable=True, server_default="0"),
    Column("es_obligatorio", Boolean, nullable=True, server_default="1"),
    Column("criticidad", String(20), nullable=True, server_default="menor"),
    Column("valor_minimo_plan", Numeric(18, 4), nullable=True),
    Column("valor_maximo_plan", Numeric(18, 4), nullable=True),
    Column("valor_objetivo_plan", Numeric(18, 4), nullable=True),
    Column("instrucciones_especificas", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_qms_plandet_plan", QmsPlanInspeccionDetalleTable.c.plan_inspeccion_id, QmsPlanInspeccionDetalleTable.c.orden)

# ============================================================================
# TABLA: qms_inspeccion
# ============================================================================
QmsInspeccionTable = Table(
    "qms_inspeccion",
    metadata_erp,
    Column("inspeccion_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_inspeccion", String(20), nullable=False),
    Column("fecha_inspeccion", DateTime, nullable=False, server_default=func.getdate()),
    Column("plan_inspeccion_id", UNIQUEIDENTIFIER, ForeignKey("qms_plan_inspeccion.plan_inspeccion_id"), nullable=False),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id"), nullable=False),
    Column("lote", String(50), nullable=True),
    Column("tipo_documento_origen", String(30), nullable=True),
    Column("documento_origen_id", UNIQUEIDENTIFIER, nullable=True),
    Column("almacen_id", UNIQUEIDENTIFIER, ForeignKey("inv_almacen.almacen_id", ondelete="SET NULL"), nullable=True),
    Column("ubicacion_almacen", String(50), nullable=True),
    Column("cantidad_total", Numeric(18, 4), nullable=False),
    Column("cantidad_inspeccionada", Numeric(18, 4), nullable=False),
    Column("unidad_medida_id", UNIQUEIDENTIFIER, ForeignKey("inv_unidad_medida.unidad_medida_id"), nullable=False),
    Column("cantidad_aprobada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_rechazada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("cantidad_observada", Numeric(18, 4), nullable=True, server_default="0"),
    Column("defectos_criticos", Integer, nullable=True, server_default="0"),
    Column("defectos_mayores", Integer, nullable=True, server_default="0"),
    Column("defectos_menores", Integer, nullable=True, server_default="0"),
    Column("resultado", String(20), nullable=True, server_default="pendiente"),
    Column("inspector_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("inspector_nombre", String(150), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("acciones_correctivas", Text, nullable=True),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_inspeccion", name="UQ_qms_insp_numero"),
)
Index("IDX_qms_insp_empresa", QmsInspeccionTable.c.empresa_id, QmsInspeccionTable.c.fecha_inspeccion.desc())
Index("IDX_qms_insp_producto", QmsInspeccionTable.c.producto_id, QmsInspeccionTable.c.resultado)
Index("IDX_qms_insp_resultado", QmsInspeccionTable.c.resultado, QmsInspeccionTable.c.fecha_inspeccion.desc())
Index("IDX_qms_insp_lote", QmsInspeccionTable.c.lote)

# ============================================================================
# TABLA: qms_inspeccion_detalle
# ============================================================================
QmsInspeccionDetalleTable = Table(
    "qms_inspeccion_detalle",
    metadata_erp,
    Column("inspeccion_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("inspeccion_id", UNIQUEIDENTIFIER, ForeignKey("qms_inspeccion.inspeccion_id", ondelete="CASCADE"), nullable=False),
    Column("parametro_calidad_id", UNIQUEIDENTIFIER, ForeignKey("qms_parametro_calidad.parametro_id"), nullable=False),
    Column("valor_medido", Numeric(18, 4), nullable=True),
    Column("valor_cualitativo", String(50), nullable=True),
    Column("resultado_pasa_no_pasa", Boolean, nullable=True),
    Column("cumple_especificacion", Boolean, nullable=True, server_default="1"),
    Column("criticidad_defecto", String(20), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_qms_inspdet_insp", QmsInspeccionDetalleTable.c.inspeccion_id)
Index("IDX_qms_inspdet_no_conforme", QmsInspeccionDetalleTable.c.inspeccion_id)

# ============================================================================
# TABLA: qms_no_conformidad
# ============================================================================
QmsNoConformidadTable = Table(
    "qms_no_conformidad",
    metadata_erp,
    Column("no_conformidad_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_nc", String(20), nullable=False),
    Column("fecha_deteccion", DateTime, nullable=False, server_default=func.getdate()),
    Column("origen", String(30), nullable=False),
    Column("inspeccion_id", UNIQUEIDENTIFIER, ForeignKey("qms_inspeccion.inspeccion_id", ondelete="SET NULL"), nullable=True),
    Column("documento_referencia", String(50), nullable=True),
    Column("producto_id", UNIQUEIDENTIFIER, ForeignKey("inv_producto.producto_id", ondelete="SET NULL"), nullable=True),
    Column("lote", String(50), nullable=True),
    Column("cantidad_afectada", Numeric(18, 4), nullable=True),
    Column("descripcion_nc", Text, nullable=False),
    Column("tipo_nc", String(30), nullable=False),
    Column("area_responsable", String(100), nullable=True),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("analisis_causa_raiz", Text, nullable=True),
    Column("causa_raiz_identificada", String(500), nullable=True),
    Column("accion_inmediata", Text, nullable=True),
    Column("accion_correctiva", Text, nullable=True),
    Column("accion_preventiva", Text, nullable=True),
    Column("responsable_accion_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("fecha_compromiso_cierre", Date, nullable=True),
    Column("estado", String(20), nullable=True, server_default="abierta"),
    Column("fecha_cierre", DateTime, nullable=True),
    Column("cerrado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("verificacion_eficacia", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_nc", name="UQ_qms_nc_numero"),
)
Index("IDX_qms_nc_empresa", QmsNoConformidadTable.c.empresa_id, QmsNoConformidadTable.c.fecha_deteccion.desc())
Index("IDX_qms_nc_estado", QmsNoConformidadTable.c.estado, QmsNoConformidadTable.c.fecha_deteccion.desc())
Index("IDX_qms_nc_tipo", QmsNoConformidadTable.c.tipo_nc)
Index("IDX_qms_nc_producto", QmsNoConformidadTable.c.producto_id)
