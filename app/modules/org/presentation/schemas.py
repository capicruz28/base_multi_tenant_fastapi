# app/modules/org/presentation/schemas.py
"""
Schemas Pydantic para el módulo ORG (Organización).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ----- Empresa -----
class EmpresaCreate(BaseModel):
    codigo_empresa: str = Field(..., max_length=20)
    razon_social: str = Field(..., max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=150)
    ruc: str = Field(..., max_length=11)
    tipo_documento_tributario: Optional[str] = Field("RUC", max_length=10)
    actividad_economica: Optional[str] = None
    codigo_ciiu: Optional[str] = None
    rubro: Optional[str] = None
    tipo_empresa: Optional[str] = None
    direccion_fiscal: Optional[str] = None
    pais: Optional[str] = "Perú"
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    codigo_postal: Optional[str] = None
    ubigeo: Optional[str] = None
    telefono_principal: Optional[str] = None
    telefono_secundario: Optional[str] = None
    email_principal: Optional[str] = None
    email_facturacion: Optional[str] = None
    sitio_web: Optional[str] = None
    representante_legal_nombre: Optional[str] = None
    representante_legal_dni: Optional[str] = None
    representante_legal_cargo: Optional[str] = None
    moneda_base: Optional[str] = "PEN"
    zona_horaria: Optional[str] = "America/Lima"
    idioma_sistema: Optional[str] = "es-PE"
    formato_fecha: Optional[str] = "dd/MM/yyyy"
    separador_miles: Optional[str] = ","
    separador_decimales: Optional[str] = "."
    decimales_moneda: Optional[int] = 2
    logo_url: Optional[str] = None
    logo_secundario_url: Optional[str] = None
    favicon_url: Optional[str] = None
    es_activo: Optional[bool] = True
    fecha_constitucion: Optional[date] = None
    fecha_inicio_operaciones: Optional[date] = None


class EmpresaUpdate(BaseModel):
    codigo_empresa: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    tipo_documento_tributario: Optional[str] = None
    actividad_economica: Optional[str] = None
    direccion_fiscal: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    telefono_principal: Optional[str] = None
    telefono_secundario: Optional[str] = None
    email_principal: Optional[str] = None
    email_facturacion: Optional[str] = None
    sitio_web: Optional[str] = None
    representante_legal_nombre: Optional[str] = None
    moneda_base: Optional[str] = None
    zona_horaria: Optional[str] = None
    es_activo: Optional[bool] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None


class EmpresaRead(BaseModel):
    empresa_id: UUID
    cliente_id: UUID
    codigo_empresa: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    ruc: str
    tipo_documento_tributario: Optional[str] = None
    actividad_economica: Optional[str] = None
    codigo_ciiu: Optional[str] = None
    rubro: Optional[str] = None
    tipo_empresa: Optional[str] = None
    direccion_fiscal: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    codigo_postal: Optional[str] = None
    ubigeo: Optional[str] = None
    telefono_principal: Optional[str] = None
    telefono_secundario: Optional[str] = None
    email_principal: Optional[str] = None
    email_facturacion: Optional[str] = None
    sitio_web: Optional[str] = None
    representante_legal_nombre: Optional[str] = None
    representante_legal_dni: Optional[str] = None
    representante_legal_cargo: Optional[str] = None
    moneda_base: Optional[str] = None
    zona_horaria: Optional[str] = None
    idioma_sistema: Optional[str] = None
    formato_fecha: Optional[str] = None
    separador_miles: Optional[str] = None
    separador_decimales: Optional[str] = None
    decimales_moneda: Optional[int] = None
    logo_url: Optional[str] = None
    logo_secundario_url: Optional[str] = None
    favicon_url: Optional[str] = None
    es_activo: bool
    fecha_constitucion: Optional[date] = None
    fecha_inicio_operaciones: Optional[date] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Centro de costo -----
class CentroCostoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    centro_costo_padre_id: Optional[UUID] = None
    nivel: Optional[int] = 1
    tipo_centro_costo: str = Field(..., max_length=30)
    categoria: Optional[str] = None
    tiene_presupuesto: Optional[bool] = False
    permite_imputacion_directa: Optional[bool] = True
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    es_activo: Optional[bool] = True
    fecha_inicio_vigencia: Optional[date] = None
    fecha_fin_vigencia: Optional[date] = None


class CentroCostoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    centro_costo_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    tipo_centro_costo: Optional[str] = None
    categoria: Optional[str] = None
    tiene_presupuesto: Optional[bool] = None
    permite_imputacion_directa: Optional[bool] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    es_activo: Optional[bool] = None
    fecha_inicio_vigencia: Optional[date] = None
    fecha_fin_vigencia: Optional[date] = None


class CentroCostoRead(BaseModel):
    centro_costo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    centro_costo_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    ruta_jerarquica: Optional[str] = None
    tipo_centro_costo: str
    categoria: Optional[str] = None
    tiene_presupuesto: Optional[bool] = None
    permite_imputacion_directa: Optional[bool] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    es_activo: bool
    fecha_inicio_vigencia: Optional[date] = None
    fecha_fin_vigencia: Optional[date] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Sucursal -----
class SucursalCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    tipo_sucursal: Optional[str] = "sede"
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    pais: Optional[str] = "Perú"
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    es_casa_matriz: Optional[bool] = False
    es_punto_venta: Optional[bool] = False
    es_almacen: Optional[bool] = False
    es_planta_produccion: Optional[bool] = False
    horario_atencion: Optional[str] = None
    zona_horaria: Optional[str] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: Optional[bool] = True
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None


class SucursalUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_sucursal: Optional[str] = None
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    es_casa_matriz: Optional[bool] = None
    es_punto_venta: Optional[bool] = None
    es_almacen: Optional[bool] = None
    es_planta_produccion: Optional[bool] = None
    horario_atencion: Optional[str] = None
    zona_horaria: Optional[str] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: Optional[bool] = None
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None


class SucursalRead(BaseModel):
    sucursal_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_sucursal: Optional[str] = None
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    ubigeo: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    es_casa_matriz: Optional[bool] = None
    es_punto_venta: Optional[bool] = None
    es_almacen: Optional[bool] = None
    es_planta_produccion: Optional[bool] = None
    horario_atencion: Optional[str] = None
    zona_horaria: Optional[str] = None
    responsable_usuario_id: Optional[UUID] = None
    responsable_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    es_activo: bool
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Departamento -----
class DepartamentoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    departamento_padre_id: Optional[UUID] = None
    nivel: Optional[int] = 1
    tipo_departamento: Optional[str] = None
    jefe_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    es_activo: Optional[bool] = True


class DepartamentoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    departamento_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    tipo_departamento: Optional[str] = None
    jefe_departamento_usuario_id: Optional[UUID] = None
    jefe_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    es_activo: Optional[bool] = None


class DepartamentoRead(BaseModel):
    departamento_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    departamento_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    ruta_jerarquica: Optional[str] = None
    tipo_departamento: Optional[str] = None
    jefe_departamento_usuario_id: Optional[UUID] = None
    jefe_nombre: Optional[str] = None
    centro_costo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Cargo -----
class CargoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    nivel_jerarquico: Optional[int] = 1
    categoria: Optional[str] = None
    area_funcional: Optional[str] = None
    departamento_id: Optional[UUID] = None
    cargo_jefe_id: Optional[UUID] = None
    rango_salarial_min: Optional[Decimal] = None
    rango_salarial_max: Optional[Decimal] = None
    moneda_salarial: Optional[str] = "PEN"
    nivel_educacion_minimo: Optional[str] = None
    experiencia_minima_meses: Optional[int] = None
    requisitos_especificos: Optional[str] = None
    es_activo: Optional[bool] = True


class CargoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    nivel_jerarquico: Optional[int] = None
    categoria: Optional[str] = None
    area_funcional: Optional[str] = None
    departamento_id: Optional[UUID] = None
    cargo_jefe_id: Optional[UUID] = None
    rango_salarial_min: Optional[Decimal] = None
    rango_salarial_max: Optional[Decimal] = None
    moneda_salarial: Optional[str] = None
    nivel_educacion_minimo: Optional[str] = None
    experiencia_minima_meses: Optional[int] = None
    requisitos_especificos: Optional[str] = None
    es_activo: Optional[bool] = None


class CargoRead(BaseModel):
    cargo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    nivel_jerarquico: Optional[int] = None
    categoria: Optional[str] = None
    area_funcional: Optional[str] = None
    departamento_id: Optional[UUID] = None
    cargo_jefe_id: Optional[UUID] = None
    rango_salarial_min: Optional[Decimal] = None
    rango_salarial_max: Optional[Decimal] = None
    moneda_salarial: Optional[str] = None
    nivel_educacion_minimo: Optional[str] = None
    experiencia_minima_meses: Optional[int] = None
    requisitos_especificos: Optional[str] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----- Parámetro sistema -----
class ParametroCreate(BaseModel):
    empresa_id: Optional[UUID] = None
    modulo_codigo: str = Field(..., max_length=10)
    codigo_parametro: str = Field(..., max_length=50)
    nombre_parametro: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    tipo_dato: str = Field(..., max_length=20)
    valor_texto: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    valor_booleano: Optional[bool] = None
    valor_fecha: Optional[date] = None
    valor_json: Optional[str] = None
    valor_defecto: Optional[str] = None
    es_editable: Optional[bool] = True
    es_obligatorio: Optional[bool] = False
    opciones_validas: Optional[str] = None
    es_activo: Optional[bool] = True


class ParametroUpdate(BaseModel):
    nombre_parametro: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_dato: Optional[str] = None
    valor_texto: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    valor_booleano: Optional[bool] = None
    valor_fecha: Optional[date] = None
    valor_json: Optional[str] = None
    valor_defecto: Optional[str] = None
    es_editable: Optional[bool] = None
    es_obligatorio: Optional[bool] = None
    opciones_validas: Optional[str] = None
    expresion_validacion: Optional[str] = None
    mensaje_validacion: Optional[str] = None
    es_activo: Optional[bool] = None


class ParametroRead(BaseModel):
    parametro_id: UUID
    cliente_id: UUID
    empresa_id: Optional[UUID] = None
    modulo_codigo: str
    codigo_parametro: str
    nombre_parametro: str
    descripcion: Optional[str] = None
    tipo_dato: str
    valor_texto: Optional[str] = None
    valor_numerico: Optional[Decimal] = None
    valor_booleano: Optional[bool] = None
    valor_fecha: Optional[date] = None
    valor_json: Optional[str] = None
    valor_defecto: Optional[str] = None
    es_editable: Optional[bool] = None
    es_obligatorio: Optional[bool] = None
    opciones_validas: Optional[str] = None
    expresion_validacion: Optional[str] = None
    mensaje_validacion: Optional[str] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True
