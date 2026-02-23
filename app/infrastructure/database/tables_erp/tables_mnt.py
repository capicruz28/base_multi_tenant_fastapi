# app/infrastructure/database/tables_erp/tables_mnt.py
"""
Tablas SQLAlchemy Core para el módulo MNT (Mantenimiento de Activos).

✅ Multi-tenant: Todas las tablas tienen cliente_id.
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección MNT.
✅ Dependencias: ORG (empresa, sucursal), MFG (centro_trabajo), LOG (vehiculo opcional), PUR (proveedor opcional).
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: mnt_activo
# ============================================================================
MntActivoTable = Table(
    "mnt_activo",
    metadata_erp,
    Column("activo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_activo", String(20), nullable=False),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_activo", String(30), nullable=False),
    Column("categoria", String(50), nullable=True),
    Column("marca", String(50), nullable=True),
    Column("modelo", String(50), nullable=True),
    Column("numero_serie", String(50), nullable=True),
    Column("año_fabricacion", Integer, nullable=True),
    Column("sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="SET NULL"), nullable=True),
    Column("centro_trabajo_id", UNIQUEIDENTIFIER, ForeignKey("mfg_centro_trabajo.centro_trabajo_id", ondelete="SET NULL"), nullable=True),
    Column("ubicacion_detalle", String(100), nullable=True),
    Column("vehiculo_id", UNIQUEIDENTIFIER, ForeignKey("log_vehiculo.vehiculo_id", ondelete="SET NULL"), nullable=True),
    Column("especificaciones_tecnicas", Text, nullable=True),
    Column("capacidad", String(100), nullable=True),
    Column("potencia", String(50), nullable=True),
    Column("fabricante", String(100), nullable=True),
    Column("proveedor_id", UNIQUEIDENTIFIER, ForeignKey("pur_proveedor.proveedor_id", ondelete="SET NULL"), nullable=True),
    Column("fecha_adquisicion", Date, nullable=True),
    Column("fecha_puesta_operacion", Date, nullable=True),
    Column("vida_util_años", Integer, nullable=True),
    Column("criticidad", String(20), nullable=True, server_default="media"),
    Column("valor_adquisicion", Numeric(18, 2), nullable=True),
    Column("valor_actual", Numeric(18, 2), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("estado_activo", String(20), nullable=True, server_default="operativo"),
    Column("observaciones", Text, nullable=True),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_activo", name="UQ_activo_codigo"),
)
Index("IDX_activo_empresa", MntActivoTable.c.empresa_id, MntActivoTable.c.es_activo)
Index("IDX_activo_tipo", MntActivoTable.c.tipo_activo, MntActivoTable.c.estado_activo)
Index("IDX_activo_criticidad", MntActivoTable.c.criticidad)

# ============================================================================
# TABLA: mnt_plan_mantenimiento
# ============================================================================
MntPlanMantenimientoTable = Table(
    "mnt_plan_mantenimiento",
    metadata_erp,
    Column("plan_mantenimiento_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("activo_id", UNIQUEIDENTIFIER, ForeignKey("mnt_activo.activo_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_plan", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(500), nullable=True),
    Column("tipo_mantenimiento", String(20), nullable=False),
    Column("frecuencia_tipo", String(20), nullable=False),
    Column("frecuencia_valor", Integer, nullable=False),
    Column("fecha_ultimo_mantenimiento", Date, nullable=True),
    Column("fecha_proximo_mantenimiento", Date, nullable=True),
    Column("horas_uso_ultimo", Numeric(12, 2), nullable=True),
    Column("horas_uso_proximo", Numeric(12, 2), nullable=True),
    Column("responsable_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("responsable_nombre", String(150), nullable=True),
    Column("tareas_mantenimiento", Text, nullable=True),
    Column("costo_estimado", Numeric(18, 2), nullable=True),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "codigo_plan", name="UQ_planmnt_codigo"),
)
Index("IDX_planmnt_activo", MntPlanMantenimientoTable.c.activo_id, MntPlanMantenimientoTable.c.es_activo)

# ============================================================================
# TABLA: mnt_orden_trabajo
# Nota: duracion_horas y costo_total son calculados en BD; se pueden devolver en servicio.
# ============================================================================
MntOrdenTrabajoTable = Table(
    "mnt_orden_trabajo",
    metadata_erp,
    Column("orden_trabajo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_ot", String(20), nullable=False),
    Column("fecha_solicitud", DateTime, nullable=False, server_default=func.getdate()),
    Column("activo_id", UNIQUEIDENTIFIER, ForeignKey("mnt_activo.activo_id", ondelete="NO ACTION"), nullable=False),
    Column("plan_mantenimiento_id", UNIQUEIDENTIFIER, ForeignKey("mnt_plan_mantenimiento.plan_mantenimiento_id", ondelete="SET NULL"), nullable=True),
    Column("tipo_mantenimiento", String(20), nullable=False),
    Column("prioridad", String(20), nullable=True, server_default="media"),
    Column("problema_detectado", Text, nullable=True),
    Column("trabajo_a_realizar", Text, nullable=False),
    Column("tecnico_asignado_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("tecnico_nombre", String(150), nullable=True),
    Column("fecha_programada", DateTime, nullable=True),
    Column("fecha_inicio_real", DateTime, nullable=True),
    Column("fecha_fin_real", DateTime, nullable=True),
    Column("trabajo_realizado", Text, nullable=True),
    Column("repuestos_utilizados", Text, nullable=True),
    Column("costo_mano_obra", Numeric(18, 2), nullable=True, server_default="0"),
    Column("costo_repuestos", Numeric(18, 2), nullable=True, server_default="0"),
    Column("costo_servicios_terceros", Numeric(18, 2), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("estado", String(20), nullable=True, server_default="solicitada"),
    Column("fecha_cierre", DateTime, nullable=True),
    Column("cerrado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("calificacion_trabajo", Numeric(3, 2), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_ot", name="UQ_ot_numero"),
)
Index("IDX_ot_empresa", MntOrdenTrabajoTable.c.empresa_id, MntOrdenTrabajoTable.c.fecha_solicitud.desc())
Index("IDX_ot_activo", MntOrdenTrabajoTable.c.activo_id, MntOrdenTrabajoTable.c.estado)
Index("IDX_ot_estado", MntOrdenTrabajoTable.c.estado, MntOrdenTrabajoTable.c.prioridad)

# ============================================================================
# TABLA: mnt_historial_mantenimiento
# ============================================================================
MntHistorialMantenimientoTable = Table(
    "mnt_historial_mantenimiento",
    metadata_erp,
    Column("historial_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("activo_id", UNIQUEIDENTIFIER, ForeignKey("mnt_activo.activo_id", ondelete="CASCADE"), nullable=False),
    Column("orden_trabajo_id", UNIQUEIDENTIFIER, ForeignKey("mnt_orden_trabajo.orden_trabajo_id", ondelete="SET NULL"), nullable=True),
    Column("fecha_mantenimiento", Date, nullable=False),
    Column("tipo_mantenimiento", String(20), nullable=False),
    Column("descripcion_trabajo", Text, nullable=True),
    Column("tecnico_nombre", String(150), nullable=True),
    Column("horas_uso_activo", Numeric(12, 2), nullable=True),
    Column("kilometraje", Numeric(12, 2), nullable=True),
    Column("costo_total", Numeric(18, 2), nullable=True, server_default="0"),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_histmnt_activo", MntHistorialMantenimientoTable.c.activo_id, MntHistorialMantenimientoTable.c.fecha_mantenimiento.desc())
Index("IDX_histmnt_fecha", MntHistorialMantenimientoTable.c.fecha_mantenimiento.desc())
