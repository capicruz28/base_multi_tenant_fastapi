# app/infrastructure/database/tables_erp/tables_crm.py
"""
Tablas SQLAlchemy Core para el módulo CRM (Customer Relationship Management).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección CRM.
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
# TABLA: crm_campana
# ============================================================================
CrmCampanaTable = Table(
    "crm_campana",
    metadata_erp,
    Column("campana_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_campana", String(20), nullable=False),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_campana", String(30), nullable=False),
    Column("objetivo", String(500), nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=True),
    Column("presupuesto", Numeric(18, 2), nullable=True),
    Column("gasto_real", Numeric(18, 2), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("total_contactos", Integer, nullable=True, server_default="0"),
    Column("total_leads_generados", Integer, nullable=True, server_default="0"),
    Column("total_oportunidades", Integer, nullable=True, server_default="0"),
    Column("total_ventas_cerradas", Integer, nullable=True, server_default="0"),
    Column("monto_ventas_cerradas", Numeric(18, 2), nullable=True, server_default="0"),
    Column("estado", String(20), nullable=True, server_default="planificada"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_campana", name="UQ_campana_codigo"),
)
Index("IDX_campana_empresa", CrmCampanaTable.c.empresa_id, CrmCampanaTable.c.estado)
Index("IDX_campana_fecha", CrmCampanaTable.c.fecha_inicio.desc())

# ============================================================================
# TABLA: crm_lead
# ============================================================================
CrmLeadTable = Table(
    "crm_lead",
    metadata_erp,
    Column("lead_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("nombre_completo", String(200), nullable=False),
    Column("empresa_nombre", String(200), nullable=True),
    Column("cargo", String(100), nullable=True),
    Column("telefono", String(20), nullable=True),
    Column("telefono_movil", String(20), nullable=True),
    Column("email", String(100), nullable=True),
    Column("direccion", String(255), nullable=True),
    Column("ciudad", String(100), nullable=True),
    Column("pais", String(50), nullable=True, server_default="Perú"),
    Column("origen_lead", String(30), nullable=False),
    Column("campana_id", UNIQUEIDENTIFIER, ForeignKey("crm_campana.campana_id", ondelete="SET NULL"), nullable=True),
    Column("referido_por", String(150), nullable=True),
    Column("calificacion", String(20), nullable=True, server_default="frio"),
    Column("puntuacion", Integer, nullable=True, server_default="0"),
    Column("asignado_vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("asignado_vendedor_nombre", String(150), nullable=True),
    Column("fecha_asignacion", DateTime, nullable=True),
    Column("estado", String(20), nullable=True, server_default="nuevo"),
    Column("fecha_primer_contacto", DateTime, nullable=True),
    Column("fecha_ultimo_contacto", DateTime, nullable=True),
    Column("convertido_cliente", Boolean, nullable=True, server_default="0"),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="SET NULL"), nullable=True),
    Column("fecha_conversion", DateTime, nullable=True),
    Column("motivo_descarte", String(500), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_lead_empresa", CrmLeadTable.c.empresa_id, CrmLeadTable.c.estado)
Index("IDX_lead_vendedor", CrmLeadTable.c.asignado_vendedor_usuario_id, CrmLeadTable.c.estado)
Index("IDX_lead_calificacion", CrmLeadTable.c.calificacion, CrmLeadTable.c.puntuacion.desc())

# ============================================================================
# TABLA: crm_oportunidad
# ============================================================================
CrmOportunidadTable = Table(
    "crm_oportunidad",
    metadata_erp,
    Column("oportunidad_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_oportunidad", String(20), nullable=False),
    Column("nombre", String(200), nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="SET NULL"), nullable=True),
    Column("lead_id", UNIQUEIDENTIFIER, ForeignKey("crm_lead.lead_id", ondelete="SET NULL"), nullable=True),
    Column("nombre_cliente_prospecto", String(200), nullable=True),
    Column("vendedor_usuario_id", UNIQUEIDENTIFIER, nullable=False),
    Column("vendedor_nombre", String(150), nullable=True),
    Column("campana_id", UNIQUEIDENTIFIER, ForeignKey("crm_campana.campana_id", ondelete="SET NULL"), nullable=True),
    Column("monto_estimado", Numeric(18, 2), nullable=False),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("probabilidad_cierre", Numeric(5, 2), nullable=True, server_default="50"),
    Column("fecha_apertura", Date, nullable=False, server_default=func.cast(func.getdate(), Date)),
    Column("fecha_cierre_estimada", Date, nullable=True),
    Column("fecha_cierre_real", Date, nullable=True),
    Column("etapa", String(30), nullable=False),
    Column("etapa_anterior", String(30), nullable=True),
    Column("fecha_cambio_etapa", DateTime, nullable=True),
    Column("tipo_oportunidad", String(30), nullable=True),
    Column("productos_interes", Text, nullable=True),
    Column("estado", String(20), nullable=True, server_default="abierta"),
    Column("motivo_ganada", String(500), nullable=True),
    Column("motivo_perdida", String(500), nullable=True),
    Column("competidor", String(150), nullable=True),
    Column("cotizacion_generada", Boolean, nullable=True, server_default="0"),
    Column("cotizacion_id", UNIQUEIDENTIFIER, nullable=True),
    Column("pedido_generado", Boolean, nullable=True, server_default="0"),
    Column("pedido_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("proxima_accion", String(500), nullable=True),
    Column("fecha_proxima_accion", Date, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_oportunidad", name="UQ_opor_numero"),
)
Index("IDX_opor_empresa", CrmOportunidadTable.c.empresa_id, CrmOportunidadTable.c.estado)
Index("IDX_opor_vendedor", CrmOportunidadTable.c.vendedor_usuario_id, CrmOportunidadTable.c.estado)
Index("IDX_opor_etapa", CrmOportunidadTable.c.etapa, CrmOportunidadTable.c.estado)
Index("IDX_opor_cierre", CrmOportunidadTable.c.fecha_cierre_estimada, CrmOportunidadTable.c.estado)

# ============================================================================
# TABLA: crm_actividad
# ============================================================================
CrmActividadTable = Table(
    "crm_actividad",
    metadata_erp,
    Column("actividad_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("tipo_actividad", String(30), nullable=False),
    Column("asunto", String(200), nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("lead_id", UNIQUEIDENTIFIER, ForeignKey("crm_lead.lead_id", ondelete="CASCADE"), nullable=True),
    Column("oportunidad_id", UNIQUEIDENTIFIER, ForeignKey("crm_oportunidad.oportunidad_id", ondelete="CASCADE"), nullable=True),
    Column("cliente_venta_id", UNIQUEIDENTIFIER, ForeignKey("sls_cliente.cliente_venta_id", ondelete="CASCADE"), nullable=True),
    Column("fecha_actividad", DateTime, nullable=False),
    Column("duracion_minutos", Integer, nullable=True),
    Column("usuario_responsable_id", UNIQUEIDENTIFIER, nullable=False),
    Column("responsable_nombre", String(150), nullable=True),
    Column("resultado", String(30), nullable=True),
    Column("requiere_seguimiento", Boolean, nullable=True, server_default="0"),
    Column("fecha_seguimiento", Date, nullable=True),
    Column("estado", String(20), nullable=True, server_default="planificada"),
    Column("fecha_completado", DateTime, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
)
Index("IDX_activ_empresa", CrmActividadTable.c.empresa_id, CrmActividadTable.c.fecha_actividad.desc())
Index("IDX_activ_responsable", CrmActividadTable.c.usuario_responsable_id, CrmActividadTable.c.estado, CrmActividadTable.c.fecha_actividad)
Index("IDX_activ_lead", CrmActividadTable.c.lead_id)
Index("IDX_activ_opor", CrmActividadTable.c.oportunidad_id)
