# app/infrastructure/database/tables_erp/tables_hcm.py
"""
Tablas SQLAlchemy Core para el módulo HCM (Human Capital Management - Planillas y RRHH).

✅ Multi-tenant: Todas las tablas tienen cliente_id (sin FK a cliente para BD dedicada).
✅ Alineado con TABLAS_BD_ERP_COMPLETO.sql sección HCM.
✅ Dependencias: ORG (empresa, departamento, cargo, sucursal, centro_costo).
"""

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date, Time,
    ForeignKey, Index, UniqueConstraint, Numeric, Text
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.sql import func

from app.infrastructure.database.tables_erp.tables_org import metadata_erp

# ============================================================================
# TABLA: hcm_empleado
# ============================================================================
HcmEmpleadoTable = Table(
    "hcm_empleado",
    metadata_erp,
    Column("empleado_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_empleado", String(20), nullable=False),
    Column("tipo_documento", String(10), nullable=True, server_default="DNI"),
    Column("numero_documento", String(20), nullable=False),
    Column("apellido_paterno", String(100), nullable=False),
    Column("apellido_materno", String(100), nullable=False),
    Column("nombres", String(150), nullable=False),
    Column("fecha_nacimiento", Date, nullable=False),
    Column("sexo", String(1), nullable=False),
    Column("estado_civil", String(20), nullable=True),
    Column("nacionalidad", String(50), nullable=True, server_default="Peruana"),
    Column("direccion", String(255), nullable=True),
    Column("departamento", String(50), nullable=True),
    Column("provincia", String(50), nullable=True),
    Column("distrito", String(50), nullable=True),
    Column("ubigeo", String(6), nullable=True),
    Column("telefono_fijo", String(20), nullable=True),
    Column("telefono_movil", String(20), nullable=True),
    Column("email_personal", String(100), nullable=True),
    Column("email_corporativo", String(100), nullable=True),
    Column("contacto_emergencia_nombre", String(150), nullable=True),
    Column("contacto_emergencia_relacion", String(50), nullable=True),
    Column("contacto_emergencia_telefono", String(20), nullable=True),
    Column("fecha_ingreso", Date, nullable=False),
    Column("fecha_cese", Date, nullable=True),
    Column("motivo_cese", String(500), nullable=True),
    Column("departamento_id", UNIQUEIDENTIFIER, ForeignKey("org_departamento.departamento_id", ondelete="SET NULL"), nullable=True),
    Column("cargo_id", UNIQUEIDENTIFIER, ForeignKey("org_cargo.cargo_id", ondelete="SET NULL"), nullable=True),
    Column("sucursal_id", UNIQUEIDENTIFIER, ForeignKey("org_sucursal.sucursal_id", ondelete="SET NULL"), nullable=True),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("jefe_inmediato_empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id"), nullable=True),
    Column("jefe_inmediato_nombre", String(150), nullable=True),
    Column("tipo_empleado", String(30), nullable=True, server_default="empleado"),
    Column("categoria", String(30), nullable=True),
    Column("banco", String(100), nullable=True),
    Column("tipo_cuenta", String(20), nullable=True),
    Column("numero_cuenta", String(30), nullable=True),
    Column("cci", String(20), nullable=True),
    Column("sistema_pensionario", String(10), nullable=False),
    Column("afp_nombre", String(50), nullable=True),
    Column("cuspp", String(12), nullable=True),
    Column("fecha_afiliacion_afp", Date, nullable=True),
    Column("tipo_comision_afp", String(20), nullable=True),
    Column("essalud", Boolean, nullable=True, server_default="1"),
    Column("eps_nombre", String(100), nullable=True),
    Column("tiene_sctr", Boolean, nullable=True, server_default="0"),
    Column("sctr_pension", Boolean, nullable=True, server_default="0"),
    Column("sctr_salud", Boolean, nullable=True, server_default="0"),
    Column("nivel_educacion", String(50), nullable=True),
    Column("profesion", String(100), nullable=True),
    Column("tiene_hijos", Boolean, nullable=True, server_default="0"),
    Column("numero_hijos", Integer, nullable=True, server_default="0"),
    Column("tiene_discapacidad", Boolean, nullable=True, server_default="0"),
    Column("tipo_discapacidad", String(100), nullable=True),
    Column("foto_url", String(500), nullable=True),
    Column("usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("estado_empleado", String(20), nullable=True, server_default="activo"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_empleado", name="UQ_emp_codigo"),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_documento", "numero_documento", name="UQ_emp_documento"),
)
Index("IDX_emp_empresa", HcmEmpleadoTable.c.empresa_id, HcmEmpleadoTable.c.es_activo)
Index("IDX_emp_documento", HcmEmpleadoTable.c.numero_documento)
Index("IDX_emp_nombre", HcmEmpleadoTable.c.apellido_paterno, HcmEmpleadoTable.c.apellido_materno, HcmEmpleadoTable.c.nombres)
Index("IDX_emp_estado", HcmEmpleadoTable.c.estado_empleado, HcmEmpleadoTable.c.fecha_ingreso)

# ============================================================================
# TABLA: hcm_contrato
# ============================================================================
HcmContratoTable = Table(
    "hcm_contrato",
    metadata_erp,
    Column("contrato_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id", ondelete="CASCADE"), nullable=False),
    Column("numero_contrato", String(20), nullable=False),
    Column("tipo_contrato", String(30), nullable=False),
    Column("modalidad_contrato", String(50), nullable=True),
    Column("fecha_inicio", Date, nullable=False),
    Column("fecha_fin", Date, nullable=True),
    Column("duracion_meses", Integer, nullable=True),
    Column("es_contrato_vigente", Boolean, nullable=True, server_default="1"),
    Column("cargo_id", UNIQUEIDENTIFIER, ForeignKey("org_cargo.cargo_id", ondelete="SET NULL"), nullable=True),
    Column("cargo_descripcion", String(150), nullable=True),
    Column("remuneracion_basica", Numeric(12, 2), nullable=False),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("tipo_remuneracion", String(20), nullable=True, server_default="mensual"),
    Column("horas_semanales", Numeric(5, 2), nullable=True, server_default="48"),
    Column("dias_laborables", Integer, nullable=True, server_default="6"),
    Column("tiene_periodo_prueba", Boolean, nullable=True, server_default="1"),
    Column("duracion_prueba_meses", Integer, nullable=True, server_default="3"),
    Column("fecha_fin_prueba", Date, nullable=True),
    Column("tiene_cts", Boolean, nullable=True, server_default="1"),
    Column("tiene_gratificacion", Boolean, nullable=True, server_default="1"),
    Column("tiene_asignacion_familiar", Boolean, nullable=True, server_default="0"),
    Column("tiene_movilidad", Boolean, nullable=True, server_default="0"),
    Column("monto_movilidad", Numeric(10, 2), nullable=True),
    Column("contrato_renovado_desde_id", UNIQUEIDENTIFIER, ForeignKey("hcm_contrato.contrato_id"), nullable=True),
    Column("numero_renovaciones", Integer, nullable=True, server_default="0"),
    Column("archivo_contrato_url", String(500), nullable=True),
    Column("estado_contrato", String(20), nullable=True, server_default="vigente"),
    Column("fecha_rescision", Date, nullable=True),
    Column("motivo_rescision", String(500), nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("clausulas_especiales", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_contrato", name="UQ_contrato_numero"),
)
Index("IDX_contrato_empresa", HcmContratoTable.c.empresa_id, HcmContratoTable.c.fecha_inicio.desc())
Index("IDX_contrato_empleado", HcmContratoTable.c.empleado_id, HcmContratoTable.c.es_contrato_vigente)
Index("IDX_contrato_vigencia", HcmContratoTable.c.fecha_inicio, HcmContratoTable.c.fecha_fin, HcmContratoTable.c.estado_contrato)

# ============================================================================
# TABLA: hcm_concepto_planilla
# ============================================================================
HcmConceptoPlanillaTable = Table(
    "hcm_concepto_planilla",
    metadata_erp,
    Column("concepto_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("codigo_concepto", String(20), nullable=False),
    Column("nombre", String(100), nullable=False),
    Column("descripcion", String(255), nullable=True),
    Column("tipo_concepto", String(20), nullable=False),
    Column("categoria", String(50), nullable=True),
    Column("es_fijo", Boolean, nullable=True, server_default="0"),
    Column("monto_fijo", Numeric(12, 2), nullable=True),
    Column("es_porcentaje", Boolean, nullable=True, server_default="0"),
    Column("porcentaje_base", Numeric(5, 2), nullable=True),
    Column("base_calculo", String(30), nullable=True),
    Column("afecto_renta_quinta", Boolean, nullable=True, server_default="1"),
    Column("afecto_essalud", Boolean, nullable=True, server_default="1"),
    Column("afecto_cts", Boolean, nullable=True, server_default="1"),
    Column("afecto_gratificacion", Boolean, nullable=True, server_default="1"),
    Column("afecto_vacaciones", Boolean, nullable=True, server_default="1"),
    Column("codigo_plame", String(10), nullable=True),
    Column("cuenta_contable", String(20), nullable=True),
    Column("es_concepto_sistema", Boolean, nullable=True, server_default="0"),
    Column("es_activo", Boolean, nullable=False, server_default="1"),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "codigo_concepto", name="UQ_concepto_codigo"),
)
Index("IDX_concepto_empresa", HcmConceptoPlanillaTable.c.empresa_id, HcmConceptoPlanillaTable.c.es_activo)
Index("IDX_concepto_tipo", HcmConceptoPlanillaTable.c.tipo_concepto, HcmConceptoPlanillaTable.c.categoria)

# ============================================================================
# TABLA: hcm_planilla
# ============================================================================
HcmPlanillaTable = Table(
    "hcm_planilla",
    metadata_erp,
    Column("planilla_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("numero_planilla", String(20), nullable=False),
    Column("año", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("periodo_descripcion", String(50), nullable=True),
    Column("tipo_planilla", String(20), nullable=True, server_default="mensual"),
    Column("fecha_inicio_periodo", Date, nullable=False),
    Column("fecha_fin_periodo", Date, nullable=False),
    Column("fecha_pago", Date, nullable=True),
    Column("total_empleados", Integer, nullable=True, server_default="0"),
    Column("total_ingresos", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_descuentos", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_neto", Numeric(18, 2), nullable=True, server_default="0"),
    Column("total_aportes_empleador", Numeric(18, 2), nullable=True, server_default="0"),
    Column("centro_costo_id", UNIQUEIDENTIFIER, ForeignKey("org_centro_costo.centro_costo_id", ondelete="SET NULL"), nullable=True),
    Column("estado", String(20), nullable=True, server_default="borrador"),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("generado_plame", Boolean, nullable=True, server_default="0"),
    Column("fecha_generacion_plame", DateTime, nullable=True),
    Column("archivo_plame_url", String(500), nullable=True),
    Column("asiento_contable_generado", Boolean, nullable=True, server_default="0"),
    Column("asiento_contable_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", Text, nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    Column("usuario_creacion_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_planilla", name="UQ_planilla_numero"),
    UniqueConstraint("cliente_id", "empresa_id", "tipo_planilla", "año", "mes", name="UQ_planilla_periodo"),
)
Index("IDX_planilla_empresa", HcmPlanillaTable.c.empresa_id, HcmPlanillaTable.c.año.desc(), HcmPlanillaTable.c.mes.desc())
Index("IDX_planilla_estado", HcmPlanillaTable.c.estado, HcmPlanillaTable.c.fecha_pago)

# ============================================================================
# TABLA: hcm_planilla_empleado
# ============================================================================
HcmPlanillaEmpleadoTable = Table(
    "hcm_planilla_empleado",
    metadata_erp,
    Column("planilla_empleado_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("planilla_id", UNIQUEIDENTIFIER, ForeignKey("hcm_planilla.planilla_id", ondelete="CASCADE"), nullable=False),
    Column("empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id"), nullable=False),
    Column("cargo_descripcion", String(150), nullable=True),
    Column("departamento_nombre", String(100), nullable=True),
    Column("dias_laborados", Integer, nullable=True, server_default="30"),
    Column("dias_subsidio", Integer, nullable=True, server_default="0"),
    Column("dias_vacaciones", Integer, nullable=True, server_default="0"),
    Column("dias_faltas", Integer, nullable=True, server_default="0"),
    Column("horas_ordinarias", Numeric(10, 2), nullable=True, server_default="0"),
    Column("horas_extras_25", Numeric(10, 2), nullable=True, server_default="0"),
    Column("horas_extras_35", Numeric(10, 2), nullable=True, server_default="0"),
    Column("horas_extras_100", Numeric(10, 2), nullable=True, server_default="0"),
    Column("remuneracion_basica", Numeric(12, 2), nullable=False),
    Column("total_ingresos", Numeric(12, 2), nullable=True, server_default="0"),
    Column("total_descuentos", Numeric(12, 2), nullable=True, server_default="0"),
    Column("total_neto", Numeric(12, 2), nullable=True, server_default="0"),
    Column("total_aportes_empleador", Numeric(12, 2), nullable=True, server_default="0"),
    Column("fecha_pago", DateTime, nullable=True),
    Column("pagado", Boolean, nullable=True, server_default="0"),
    Column("metodo_pago", String(30), nullable=True),
    Column("numero_operacion", String(50), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "planilla_id", "empleado_id", name="UQ_planemp"),
)
Index("IDX_planemp_planilla", HcmPlanillaEmpleadoTable.c.planilla_id)
Index("IDX_planemp_empleado", HcmPlanillaEmpleadoTable.c.empleado_id)

# ============================================================================
# TABLA: hcm_planilla_detalle
# ============================================================================
HcmPlanillaDetalleTable = Table(
    "hcm_planilla_detalle",
    metadata_erp,
    Column("planilla_detalle_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("planilla_empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_planilla_empleado.planilla_empleado_id", ondelete="CASCADE"), nullable=False),
    Column("concepto_id", UNIQUEIDENTIFIER, ForeignKey("hcm_concepto_planilla.concepto_id"), nullable=False),
    Column("tipo_concepto", String(20), nullable=False),
    Column("base_calculo", Numeric(12, 2), nullable=True),
    Column("cantidad", Numeric(10, 2), nullable=True, server_default="1"),
    Column("tasa_porcentaje", Numeric(5, 2), nullable=True),
    Column("monto", Numeric(12, 2), nullable=False),
    Column("observaciones", String(255), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
)
Index("IDX_plandet_planemp", HcmPlanillaDetalleTable.c.planilla_empleado_id, HcmPlanillaDetalleTable.c.tipo_concepto)
Index("IDX_plandet_concepto", HcmPlanillaDetalleTable.c.concepto_id)

# ============================================================================
# TABLA: hcm_asistencia
# ============================================================================
HcmAsistenciaTable = Table(
    "hcm_asistencia",
    metadata_erp,
    Column("asistencia_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id", ondelete="CASCADE"), nullable=False),
    Column("fecha", Date, nullable=False),
    Column("hora_entrada", Time, nullable=True),
    Column("hora_salida", Time, nullable=True),
    Column("hora_entrada_refrigerio", Time, nullable=True),
    Column("hora_salida_refrigerio", Time, nullable=True),
    Column("horas_trabajadas", Numeric(5, 2), nullable=True),
    Column("horas_extras", Numeric(5, 2), nullable=True, server_default="0"),
    Column("tipo_asistencia", String(20), nullable=True, server_default="presente"),
    Column("minutos_tardanza", Integer, nullable=True, server_default="0"),
    Column("tiene_justificacion", Boolean, nullable=True, server_default="0"),
    Column("justificacion", String(500), nullable=True),
    Column("archivo_justificacion_url", String(500), nullable=True),
    Column("incidencias", Text, nullable=True),
    Column("dispositivo_marcacion", String(50), nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("fecha_actualizacion", DateTime, nullable=True),
    UniqueConstraint("cliente_id", "empleado_id", "fecha", name="UQ_asist_empleado_fecha"),
)
Index("IDX_asist_empresa", HcmAsistenciaTable.c.empresa_id, HcmAsistenciaTable.c.fecha.desc())
Index("IDX_asist_empleado", HcmAsistenciaTable.c.empleado_id, HcmAsistenciaTable.c.fecha.desc())
Index("IDX_asist_fecha", HcmAsistenciaTable.c.fecha.desc())
Index("IDX_asist_tipo", HcmAsistenciaTable.c.tipo_asistencia, HcmAsistenciaTable.c.fecha)

# ============================================================================
# TABLA: hcm_vacaciones
# ============================================================================
HcmVacacionesTable = Table(
    "hcm_vacaciones",
    metadata_erp,
    Column("vacaciones_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id", ondelete="CASCADE"), nullable=False),
    Column("año_periodo", Integer, nullable=False),
    Column("fecha_inicio_periodo", Date, nullable=False),
    Column("fecha_fin_periodo", Date, nullable=False),
    Column("dias_ganados", Integer, nullable=True, server_default="30"),
    Column("dias_tomados", Integer, nullable=True, server_default="0"),
    Column("fecha_inicio_programada", Date, nullable=True),
    Column("fecha_fin_programada", Date, nullable=True),
    Column("fecha_inicio_real", Date, nullable=True),
    Column("fecha_fin_real", Date, nullable=True),
    Column("estado", String(20), nullable=True, server_default="pendiente"),
    Column("fecha_aprobacion", DateTime, nullable=True),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    UniqueConstraint("cliente_id", "empleado_id", "año_periodo", name="UQ_vac_empleado_periodo"),
)
Index("IDX_vac_empresa", HcmVacacionesTable.c.empresa_id, HcmVacacionesTable.c.año_periodo.desc())
Index("IDX_vac_empleado", HcmVacacionesTable.c.empleado_id, HcmVacacionesTable.c.estado)

# ============================================================================
# TABLA: hcm_prestamo
# ============================================================================
HcmPrestamoTable = Table(
    "hcm_prestamo",
    metadata_erp,
    Column("prestamo_id", UNIQUEIDENTIFIER, primary_key=True),
    Column("cliente_id", UNIQUEIDENTIFIER, nullable=False),
    Column("empresa_id", UNIQUEIDENTIFIER, ForeignKey("org_empresa.empresa_id", ondelete="CASCADE"), nullable=False),
    Column("empleado_id", UNIQUEIDENTIFIER, ForeignKey("hcm_empleado.empleado_id", ondelete="CASCADE"), nullable=False),
    Column("numero_prestamo", String(20), nullable=False),
    Column("tipo_prestamo", String(30), nullable=False),
    Column("monto_prestamo", Numeric(12, 2), nullable=False),
    Column("moneda", String(3), nullable=True, server_default="PEN"),
    Column("fecha_prestamo", Date, nullable=False, server_default=func.getdate()),
    Column("numero_cuotas", Integer, nullable=False),
    Column("monto_cuota", Numeric(12, 2), nullable=False),
    Column("cuotas_pagadas", Integer, nullable=True, server_default="0"),
    Column("saldo_pendiente", Numeric(12, 2), nullable=True),
    Column("aplica_interes", Boolean, nullable=True, server_default="0"),
    Column("tasa_interes_mensual", Numeric(5, 2), nullable=True),
    Column("estado", String(20), nullable=True, server_default="activo"),
    Column("fecha_pago_completo", Date, nullable=True),
    Column("observaciones", String(500), nullable=True),
    Column("motivo_prestamo", String(255), nullable=True),
    Column("fecha_creacion", DateTime, nullable=False, server_default=func.getdate()),
    Column("aprobado_por_usuario_id", UNIQUEIDENTIFIER, nullable=True),
    UniqueConstraint("cliente_id", "empresa_id", "numero_prestamo", name="UQ_prestamo_numero"),
)
Index("IDX_prestamo_empresa", HcmPrestamoTable.c.empresa_id, HcmPrestamoTable.c.fecha_prestamo.desc())
Index("IDX_prestamo_empleado", HcmPrestamoTable.c.empleado_id, HcmPrestamoTable.c.estado)
