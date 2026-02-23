# app/modules/hcm/presentation/schemas.py
"""
Schemas Pydantic para el módulo HCM (Planillas y RRHH).
Create/Update no incluyen cliente_id; se asigna desde contexto en backend.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field


# ============================================================================
# EMPLEADO
# ============================================================================
class EmpleadoCreate(BaseModel):
    empresa_id: UUID
    codigo_empleado: str = Field(..., max_length=20)
    tipo_documento: Optional[str] = Field("DNI", max_length=10)
    numero_documento: str = Field(..., max_length=20)
    apellido_paterno: str = Field(..., max_length=100)
    apellido_materno: str = Field(..., max_length=100)
    nombres: str = Field(..., max_length=150)
    fecha_nacimiento: date
    sexo: str = Field(..., max_length=1)
    estado_civil: Optional[str] = Field(None, max_length=20)
    nacionalidad: Optional[str] = Field("Peruana", max_length=50)
    direccion: Optional[str] = Field(None, max_length=255)
    departamento: Optional[str] = Field(None, max_length=50)
    provincia: Optional[str] = Field(None, max_length=50)
    distrito: Optional[str] = Field(None, max_length=50)
    ubigeo: Optional[str] = Field(None, max_length=6)
    telefono_fijo: Optional[str] = Field(None, max_length=20)
    telefono_movil: Optional[str] = Field(None, max_length=20)
    email_personal: Optional[str] = Field(None, max_length=100)
    email_corporativo: Optional[str] = Field(None, max_length=100)
    contacto_emergencia_nombre: Optional[str] = Field(None, max_length=150)
    contacto_emergencia_relacion: Optional[str] = Field(None, max_length=50)
    contacto_emergencia_telefono: Optional[str] = Field(None, max_length=20)
    fecha_ingreso: date
    fecha_cese: Optional[date] = None
    motivo_cese: Optional[str] = Field(None, max_length=500)
    departamento_id: Optional[UUID] = None
    cargo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    jefe_inmediato_empleado_id: Optional[UUID] = None
    jefe_inmediato_nombre: Optional[str] = Field(None, max_length=150)
    tipo_empleado: Optional[str] = Field("empleado", max_length=30)
    categoria: Optional[str] = Field(None, max_length=30)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = Field(None, max_length=20)
    numero_cuenta: Optional[str] = Field(None, max_length=30)
    cci: Optional[str] = Field(None, max_length=20)
    sistema_pensionario: str = Field(..., max_length=10)
    afp_nombre: Optional[str] = Field(None, max_length=50)
    cuspp: Optional[str] = Field(None, max_length=12)
    fecha_afiliacion_afp: Optional[date] = None
    tipo_comision_afp: Optional[str] = Field(None, max_length=20)
    essalud: Optional[bool] = True
    eps_nombre: Optional[str] = Field(None, max_length=100)
    tiene_sctr: Optional[bool] = False
    sctr_pension: Optional[bool] = False
    sctr_salud: Optional[bool] = False
    nivel_educacion: Optional[str] = Field(None, max_length=50)
    profesion: Optional[str] = Field(None, max_length=100)
    tiene_hijos: Optional[bool] = False
    numero_hijos: Optional[int] = 0
    tiene_discapacidad: Optional[bool] = False
    tipo_discapacidad: Optional[str] = Field(None, max_length=100)
    foto_url: Optional[str] = Field(None, max_length=500)
    usuario_id: Optional[UUID] = None
    estado_empleado: Optional[str] = Field("activo", max_length=20)
    es_activo: Optional[bool] = True
    observaciones: Optional[str] = None


class EmpleadoUpdate(BaseModel):
    codigo_empleado: Optional[str] = Field(None, max_length=20)
    tipo_documento: Optional[str] = Field(None, max_length=10)
    numero_documento: Optional[str] = Field(None, max_length=20)
    apellido_paterno: Optional[str] = Field(None, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    nombres: Optional[str] = Field(None, max_length=150)
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = Field(None, max_length=1)
    estado_civil: Optional[str] = Field(None, max_length=20)
    nacionalidad: Optional[str] = Field(None, max_length=50)
    direccion: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    telefono_fijo: Optional[str] = None
    telefono_movil: Optional[str] = None
    email_personal: Optional[str] = None
    email_corporativo: Optional[str] = None
    contacto_emergencia_nombre: Optional[str] = None
    contacto_emergencia_relacion: Optional[str] = None
    contacto_emergencia_telefono: Optional[str] = None
    fecha_cese: Optional[date] = None
    motivo_cese: Optional[str] = None
    departamento_id: Optional[UUID] = None
    cargo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    centro_costo_id: Optional[UUID] = None
    jefe_inmediato_empleado_id: Optional[UUID] = None
    jefe_inmediato_nombre: Optional[str] = None
    tipo_empleado: Optional[str] = None
    categoria: Optional[str] = None
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    numero_cuenta: Optional[str] = None
    cci: Optional[str] = None
    sistema_pensionario: Optional[str] = None
    afp_nombre: Optional[str] = None
    cuspp: Optional[str] = None
    fecha_afiliacion_afp: Optional[date] = None
    tipo_comision_afp: Optional[str] = None
    essalud: Optional[bool] = None
    eps_nombre: Optional[str] = None
    tiene_sctr: Optional[bool] = None
    sctr_pension: Optional[bool] = None
    sctr_salud: Optional[bool] = None
    nivel_educacion: Optional[str] = None
    profesion: Optional[str] = None
    tiene_hijos: Optional[bool] = None
    numero_hijos: Optional[int] = None
    tiene_discapacidad: Optional[bool] = None
    tipo_discapacidad: Optional[str] = None
    foto_url: Optional[str] = None
    usuario_id: Optional[UUID] = None
    estado_empleado: Optional[str] = None
    es_activo: Optional[bool] = None
    observaciones: Optional[str] = None


class EmpleadoRead(BaseModel):
    empleado_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_empleado: str
    tipo_documento: Optional[str]
    numero_documento: str
    apellido_paterno: str
    apellido_materno: str
    nombres: str
    fecha_nacimiento: date
    sexo: str
    estado_civil: Optional[str]
    nacionalidad: Optional[str]
    direccion: Optional[str]
    departamento: Optional[str]
    provincia: Optional[str]
    distrito: Optional[str]
    ubigeo: Optional[str]
    telefono_fijo: Optional[str]
    telefono_movil: Optional[str]
    email_personal: Optional[str]
    email_corporativo: Optional[str]
    contacto_emergencia_nombre: Optional[str]
    contacto_emergencia_relacion: Optional[str]
    contacto_emergencia_telefono: Optional[str]
    fecha_ingreso: date
    fecha_cese: Optional[date]
    motivo_cese: Optional[str]
    departamento_id: Optional[UUID]
    cargo_id: Optional[UUID]
    sucursal_id: Optional[UUID]
    centro_costo_id: Optional[UUID]
    jefe_inmediato_empleado_id: Optional[UUID]
    jefe_inmediato_nombre: Optional[str]
    tipo_empleado: Optional[str]
    categoria: Optional[str]
    banco: Optional[str]
    tipo_cuenta: Optional[str]
    numero_cuenta: Optional[str]
    cci: Optional[str]
    sistema_pensionario: Optional[str]
    afp_nombre: Optional[str]
    cuspp: Optional[str]
    fecha_afiliacion_afp: Optional[date]
    tipo_comision_afp: Optional[str]
    essalud: Optional[bool]
    eps_nombre: Optional[str]
    tiene_sctr: Optional[bool]
    sctr_pension: Optional[bool]
    sctr_salud: Optional[bool]
    nivel_educacion: Optional[str]
    profesion: Optional[str]
    tiene_hijos: Optional[bool]
    numero_hijos: Optional[int]
    tiene_discapacidad: Optional[bool]
    tipo_discapacidad: Optional[str]
    foto_url: Optional[str]
    usuario_id: Optional[UUID]
    estado_empleado: Optional[str]
    es_activo: Optional[bool]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# CONTRATO
# ============================================================================
class ContratoCreate(BaseModel):
    empresa_id: UUID
    empleado_id: UUID
    numero_contrato: str = Field(..., max_length=20)
    tipo_contrato: str = Field(..., max_length=30)
    modalidad_contrato: Optional[str] = Field(None, max_length=50)
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    duracion_meses: Optional[int] = None
    es_contrato_vigente: Optional[bool] = True
    cargo_id: Optional[UUID] = None
    cargo_descripcion: Optional[str] = Field(None, max_length=150)
    remuneracion_basica: Decimal = Field(..., ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    tipo_remuneracion: Optional[str] = Field("mensual", max_length=20)
    horas_semanales: Optional[Decimal] = Field(48, ge=0)
    dias_laborables: Optional[int] = Field(6, ge=1, le=7)
    tiene_periodo_prueba: Optional[bool] = True
    duracion_prueba_meses: Optional[int] = 3
    fecha_fin_prueba: Optional[date] = None
    tiene_cts: Optional[bool] = True
    tiene_gratificacion: Optional[bool] = True
    tiene_asignacion_familiar: Optional[bool] = False
    tiene_movilidad: Optional[bool] = False
    monto_movilidad: Optional[Decimal] = Field(None, ge=0)
    contrato_renovado_desde_id: Optional[UUID] = None
    numero_renovaciones: Optional[int] = 0
    archivo_contrato_url: Optional[str] = Field(None, max_length=500)
    estado_contrato: Optional[str] = Field("vigente", max_length=20)
    fecha_rescision: Optional[date] = None
    motivo_rescision: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = None
    clausulas_especiales: Optional[str] = None


class ContratoUpdate(BaseModel):
    numero_contrato: Optional[str] = Field(None, max_length=20)
    tipo_contrato: Optional[str] = None
    modalidad_contrato: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    duracion_meses: Optional[int] = None
    es_contrato_vigente: Optional[bool] = None
    cargo_id: Optional[UUID] = None
    cargo_descripcion: Optional[str] = None
    remuneracion_basica: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = None
    tipo_remuneracion: Optional[str] = None
    horas_semanales: Optional[Decimal] = None
    dias_laborables: Optional[int] = None
    tiene_periodo_prueba: Optional[bool] = None
    duracion_prueba_meses: Optional[int] = None
    fecha_fin_prueba: Optional[date] = None
    tiene_cts: Optional[bool] = None
    tiene_gratificacion: Optional[bool] = None
    tiene_asignacion_familiar: Optional[bool] = None
    tiene_movilidad: Optional[bool] = None
    monto_movilidad: Optional[Decimal] = None
    estado_contrato: Optional[str] = None
    fecha_rescision: Optional[date] = None
    motivo_rescision: Optional[str] = None
    observaciones: Optional[str] = None
    clausulas_especiales: Optional[str] = None


class ContratoRead(BaseModel):
    contrato_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    empleado_id: UUID
    numero_contrato: str
    tipo_contrato: str
    modalidad_contrato: Optional[str]
    fecha_inicio: date
    fecha_fin: Optional[date]
    duracion_meses: Optional[int]
    es_contrato_vigente: Optional[bool]
    cargo_id: Optional[UUID]
    cargo_descripcion: Optional[str]
    remuneracion_basica: Decimal
    moneda: Optional[str]
    tipo_remuneracion: Optional[str]
    horas_semanales: Optional[Decimal]
    dias_laborables: Optional[int]
    tiene_periodo_prueba: Optional[bool]
    duracion_prueba_meses: Optional[int]
    fecha_fin_prueba: Optional[date]
    tiene_cts: Optional[bool]
    tiene_gratificacion: Optional[bool]
    tiene_asignacion_familiar: Optional[bool]
    tiene_movilidad: Optional[bool]
    monto_movilidad: Optional[Decimal]
    contrato_renovado_desde_id: Optional[UUID]
    numero_renovaciones: Optional[int]
    archivo_contrato_url: Optional[str]
    estado_contrato: Optional[str]
    fecha_rescision: Optional[date]
    motivo_rescision: Optional[str]
    observaciones: Optional[str]
    clausulas_especiales: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# CONCEPTO PLANILLA
# ============================================================================
class ConceptoPlanillaCreate(BaseModel):
    empresa_id: UUID
    codigo_concepto: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    tipo_concepto: str = Field(..., max_length=20)
    categoria: Optional[str] = Field(None, max_length=50)
    es_fijo: Optional[bool] = False
    monto_fijo: Optional[Decimal] = Field(None, ge=0)
    es_porcentaje: Optional[bool] = False
    porcentaje_base: Optional[Decimal] = Field(None, ge=0, le=100)
    base_calculo: Optional[str] = Field(None, max_length=30)
    afecto_renta_quinta: Optional[bool] = True
    afecto_essalud: Optional[bool] = True
    afecto_cts: Optional[bool] = True
    afecto_gratificacion: Optional[bool] = True
    afecto_vacaciones: Optional[bool] = True
    codigo_plame: Optional[str] = Field(None, max_length=10)
    cuenta_contable: Optional[str] = Field(None, max_length=20)
    es_concepto_sistema: Optional[bool] = False
    es_activo: Optional[bool] = True


class ConceptoPlanillaUpdate(BaseModel):
    codigo_concepto: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    tipo_concepto: Optional[str] = None
    categoria: Optional[str] = None
    es_fijo: Optional[bool] = None
    monto_fijo: Optional[Decimal] = None
    es_porcentaje: Optional[bool] = None
    porcentaje_base: Optional[Decimal] = None
    base_calculo: Optional[str] = None
    afecto_renta_quinta: Optional[bool] = None
    afecto_essalud: Optional[bool] = None
    afecto_cts: Optional[bool] = None
    afecto_gratificacion: Optional[bool] = None
    afecto_vacaciones: Optional[bool] = None
    codigo_plame: Optional[str] = None
    cuenta_contable: Optional[str] = None
    es_activo: Optional[bool] = None


class ConceptoPlanillaRead(BaseModel):
    concepto_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_concepto: str
    nombre: str
    descripcion: Optional[str]
    tipo_concepto: str
    categoria: Optional[str]
    es_fijo: Optional[bool]
    monto_fijo: Optional[Decimal]
    es_porcentaje: Optional[bool]
    porcentaje_base: Optional[Decimal]
    base_calculo: Optional[str]
    afecto_renta_quinta: Optional[bool]
    afecto_essalud: Optional[bool]
    afecto_cts: Optional[bool]
    afecto_gratificacion: Optional[bool]
    afecto_vacaciones: Optional[bool]
    codigo_plame: Optional[str]
    cuenta_contable: Optional[str]
    es_concepto_sistema: Optional[bool]
    es_activo: Optional[bool]
    fecha_creacion: datetime
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PLANILLA
# ============================================================================
class PlanillaCreate(BaseModel):
    empresa_id: UUID
    numero_planilla: str = Field(..., max_length=20)
    año: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    periodo_descripcion: Optional[str] = Field(None, max_length=50)
    tipo_planilla: Optional[str] = Field("mensual", max_length=20)
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    fecha_pago: Optional[date] = None
    total_empleados: Optional[int] = 0
    total_ingresos: Optional[Decimal] = Field(0, ge=0)
    total_descuentos: Optional[Decimal] = Field(0, ge=0)
    total_neto: Optional[Decimal] = Field(0, ge=0)
    total_aportes_empleador: Optional[Decimal] = Field(0, ge=0)
    centro_costo_id: Optional[UUID] = None
    estado: Optional[str] = Field("borrador", max_length=20)
    observaciones: Optional[str] = None


class PlanillaUpdate(BaseModel):
    numero_planilla: Optional[str] = Field(None, max_length=20)
    periodo_descripcion: Optional[str] = None
    tipo_planilla: Optional[str] = None
    fecha_inicio_periodo: Optional[date] = None
    fecha_fin_periodo: Optional[date] = None
    fecha_pago: Optional[date] = None
    total_empleados: Optional[int] = None
    total_ingresos: Optional[Decimal] = None
    total_descuentos: Optional[Decimal] = None
    total_neto: Optional[Decimal] = None
    total_aportes_empleador: Optional[Decimal] = None
    centro_costo_id: Optional[UUID] = None
    estado: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class PlanillaRead(BaseModel):
    planilla_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_planilla: str
    año: int
    mes: int
    periodo_descripcion: Optional[str]
    tipo_planilla: Optional[str]
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    fecha_pago: Optional[date]
    total_empleados: Optional[int]
    total_ingresos: Optional[Decimal]
    total_descuentos: Optional[Decimal]
    total_neto: Optional[Decimal]
    total_aportes_empleador: Optional[Decimal]
    centro_costo_id: Optional[UUID]
    estado: Optional[str]
    fecha_aprobacion: Optional[datetime]
    aprobado_por_usuario_id: Optional[UUID]
    generado_plame: Optional[bool]
    fecha_generacion_plame: Optional[datetime]
    archivo_plame_url: Optional[str]
    asiento_contable_generado: Optional[bool]
    asiento_contable_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    usuario_creacion_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# PLANILLA EMPLEADO
# ============================================================================
class PlanillaEmpleadoCreate(BaseModel):
    planilla_id: UUID
    empleado_id: UUID
    cargo_descripcion: Optional[str] = Field(None, max_length=150)
    departamento_nombre: Optional[str] = Field(None, max_length=100)
    dias_laborados: Optional[int] = Field(30, ge=0)
    dias_subsidio: Optional[int] = Field(0, ge=0)
    dias_vacaciones: Optional[int] = Field(0, ge=0)
    dias_faltas: Optional[int] = Field(0, ge=0)
    horas_ordinarias: Optional[Decimal] = Field(0, ge=0)
    horas_extras_25: Optional[Decimal] = Field(0, ge=0)
    horas_extras_35: Optional[Decimal] = Field(0, ge=0)
    horas_extras_100: Optional[Decimal] = Field(0, ge=0)
    remuneracion_basica: Decimal = Field(..., ge=0)
    total_ingresos: Optional[Decimal] = Field(0, ge=0)
    total_descuentos: Optional[Decimal] = Field(0, ge=0)
    total_neto: Optional[Decimal] = Field(0, ge=0)
    total_aportes_empleador: Optional[Decimal] = Field(0, ge=0)
    observaciones: Optional[str] = Field(None, max_length=500)


class PlanillaEmpleadoUpdate(BaseModel):
    cargo_descripcion: Optional[str] = None
    departamento_nombre: Optional[str] = None
    dias_laborados: Optional[int] = None
    dias_subsidio: Optional[int] = None
    dias_vacaciones: Optional[int] = None
    dias_faltas: Optional[int] = None
    horas_ordinarias: Optional[Decimal] = None
    horas_extras_25: Optional[Decimal] = None
    horas_extras_35: Optional[Decimal] = None
    horas_extras_100: Optional[Decimal] = None
    remuneracion_basica: Optional[Decimal] = None
    total_ingresos: Optional[Decimal] = None
    total_descuentos: Optional[Decimal] = None
    total_neto: Optional[Decimal] = None
    total_aportes_empleador: Optional[Decimal] = None
    fecha_pago: Optional[datetime] = None
    pagado: Optional[bool] = None
    metodo_pago: Optional[str] = None
    numero_operacion: Optional[str] = None
    observaciones: Optional[str] = None


class PlanillaEmpleadoRead(BaseModel):
    planilla_empleado_id: UUID
    cliente_id: UUID
    planilla_id: UUID
    empleado_id: UUID
    cargo_descripcion: Optional[str]
    departamento_nombre: Optional[str]
    dias_laborados: Optional[int]
    dias_subsidio: Optional[int]
    dias_vacaciones: Optional[int]
    dias_faltas: Optional[int]
    horas_ordinarias: Optional[Decimal]
    horas_extras_25: Optional[Decimal]
    horas_extras_35: Optional[Decimal]
    horas_extras_100: Optional[Decimal]
    remuneracion_basica: Decimal
    total_ingresos: Optional[Decimal]
    total_descuentos: Optional[Decimal]
    total_neto: Optional[Decimal]
    total_aportes_empleador: Optional[Decimal]
    fecha_pago: Optional[datetime]
    pagado: Optional[bool]
    metodo_pago: Optional[str]
    numero_operacion: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PLANILLA DETALLE
# ============================================================================
class PlanillaDetalleCreate(BaseModel):
    planilla_empleado_id: UUID
    concepto_id: UUID
    tipo_concepto: str = Field(..., max_length=20)
    base_calculo: Optional[Decimal] = Field(None, ge=0)
    cantidad: Optional[Decimal] = Field(1, ge=0)
    tasa_porcentaje: Optional[Decimal] = Field(None, ge=0, le=100)
    monto: Decimal = Field(..., ge=0)
    observaciones: Optional[str] = Field(None, max_length=255)


class PlanillaDetalleUpdate(BaseModel):
    base_calculo: Optional[Decimal] = None
    cantidad: Optional[Decimal] = None
    tasa_porcentaje: Optional[Decimal] = None
    monto: Optional[Decimal] = None
    observaciones: Optional[str] = None


class PlanillaDetalleRead(BaseModel):
    planilla_detalle_id: UUID
    cliente_id: UUID
    planilla_empleado_id: UUID
    concepto_id: UUID
    tipo_concepto: str
    base_calculo: Optional[Decimal]
    cantidad: Optional[Decimal]
    tasa_porcentaje: Optional[Decimal]
    monto: Decimal
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ASISTENCIA
# ============================================================================
class AsistenciaCreate(BaseModel):
    empresa_id: UUID
    empleado_id: UUID
    fecha: date
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    hora_entrada_refrigerio: Optional[time] = None
    hora_salida_refrigerio: Optional[time] = None
    horas_trabajadas: Optional[Decimal] = Field(None, ge=0)
    horas_extras: Optional[Decimal] = Field(0, ge=0)
    tipo_asistencia: Optional[str] = Field("presente", max_length=20)
    minutos_tardanza: Optional[int] = Field(0, ge=0)
    tiene_justificacion: Optional[bool] = False
    justificacion: Optional[str] = Field(None, max_length=500)
    archivo_justificacion_url: Optional[str] = Field(None, max_length=500)
    incidencias: Optional[str] = None
    dispositivo_marcacion: Optional[str] = Field(None, max_length=50)
    observaciones: Optional[str] = Field(None, max_length=500)


class AsistenciaUpdate(BaseModel):
    hora_entrada: Optional[time] = None
    hora_salida: Optional[time] = None
    hora_entrada_refrigerio: Optional[time] = None
    hora_salida_refrigerio: Optional[time] = None
    horas_trabajadas: Optional[Decimal] = None
    horas_extras: Optional[Decimal] = None
    tipo_asistencia: Optional[str] = None
    minutos_tardanza: Optional[int] = None
    tiene_justificacion: Optional[bool] = None
    justificacion: Optional[str] = None
    archivo_justificacion_url: Optional[str] = None
    incidencias: Optional[str] = None
    dispositivo_marcacion: Optional[str] = None
    observaciones: Optional[str] = None


class AsistenciaRead(BaseModel):
    asistencia_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    empleado_id: UUID
    fecha: date
    hora_entrada: Optional[time]
    hora_salida: Optional[time]
    hora_entrada_refrigerio: Optional[time]
    hora_salida_refrigerio: Optional[time]
    horas_trabajadas: Optional[Decimal]
    horas_extras: Optional[Decimal]
    tipo_asistencia: Optional[str]
    minutos_tardanza: Optional[int]
    tiene_justificacion: Optional[bool]
    justificacion: Optional[str]
    archivo_justificacion_url: Optional[str]
    incidencias: Optional[str]
    dispositivo_marcacion: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# VACACIONES
# ============================================================================
class VacacionesCreate(BaseModel):
    empresa_id: UUID
    empleado_id: UUID
    año_periodo: int = Field(..., ge=2000, le=2100)
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    dias_ganados: Optional[int] = Field(30, ge=0)
    dias_tomados: Optional[int] = Field(0, ge=0)
    fecha_inicio_programada: Optional[date] = None
    fecha_fin_programada: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: Optional[str] = Field("pendiente", max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)


class VacacionesUpdate(BaseModel):
    dias_ganados: Optional[int] = None
    dias_tomados: Optional[int] = None
    fecha_inicio_programada: Optional[date] = None
    fecha_fin_programada: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: Optional[str] = None
    fecha_aprobacion: Optional[datetime] = None
    aprobado_por_usuario_id: Optional[UUID] = None
    observaciones: Optional[str] = None


class VacacionesRead(BaseModel):
    vacaciones_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    empleado_id: UUID
    año_periodo: int
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    dias_ganados: Optional[int]
    dias_tomados: Optional[int]
    fecha_inicio_programada: Optional[date]
    fecha_fin_programada: Optional[date]
    fecha_inicio_real: Optional[date]
    fecha_fin_real: Optional[date]
    estado: Optional[str]
    fecha_aprobacion: Optional[datetime]
    aprobado_por_usuario_id: Optional[UUID]
    observaciones: Optional[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRÉSTAMO
# ============================================================================
class PrestamoCreate(BaseModel):
    empresa_id: UUID
    empleado_id: UUID
    numero_prestamo: str = Field(..., max_length=20)
    tipo_prestamo: str = Field(..., max_length=30)
    monto_prestamo: Decimal = Field(..., ge=0)
    moneda: Optional[str] = Field("PEN", max_length=3)
    fecha_prestamo: Optional[date] = None
    numero_cuotas: int = Field(..., ge=1)
    monto_cuota: Decimal = Field(..., ge=0)
    cuotas_pagadas: Optional[int] = Field(0, ge=0)
    saldo_pendiente: Optional[Decimal] = Field(None, ge=0)
    aplica_interes: Optional[bool] = False
    tasa_interes_mensual: Optional[Decimal] = Field(None, ge=0, le=100)
    estado: Optional[str] = Field("activo", max_length=20)
    observaciones: Optional[str] = Field(None, max_length=500)
    motivo_prestamo: Optional[str] = Field(None, max_length=255)


class PrestamoUpdate(BaseModel):
    numero_prestamo: Optional[str] = None
    tipo_prestamo: Optional[str] = None
    monto_prestamo: Optional[Decimal] = None
    moneda: Optional[str] = None
    numero_cuotas: Optional[int] = None
    monto_cuota: Optional[Decimal] = None
    cuotas_pagadas: Optional[int] = None
    saldo_pendiente: Optional[Decimal] = None
    aplica_interes: Optional[bool] = None
    tasa_interes_mensual: Optional[Decimal] = None
    estado: Optional[str] = None
    fecha_pago_completo: Optional[date] = None
    observaciones: Optional[str] = None
    motivo_prestamo: Optional[str] = None


class PrestamoRead(BaseModel):
    prestamo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    empleado_id: UUID
    numero_prestamo: str
    tipo_prestamo: str
    monto_prestamo: Decimal
    moneda: Optional[str]
    fecha_prestamo: date
    numero_cuotas: int
    monto_cuota: Decimal
    cuotas_pagadas: Optional[int]
    saldo_pendiente: Optional[Decimal]
    aplica_interes: Optional[bool]
    tasa_interes_mensual: Optional[Decimal]
    estado: Optional[str]
    fecha_pago_completo: Optional[date]
    observaciones: Optional[str]
    motivo_prestamo: Optional[str]
    fecha_creacion: datetime
    aprobado_por_usuario_id: Optional[UUID]

    class Config:
        from_attributes = True
