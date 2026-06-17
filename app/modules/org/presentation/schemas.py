# app/modules/org/presentation/schemas.py
"""
Schemas Pydantic para el módulo ORG (Organización).
Todos los Create/Update excluyen cliente_id; se asigna desde contexto en backend.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.shared.validators import normalize_upper, normalize_lower, normalize_strip


# ----- Mixins de normalización (solo Create / Update) -----

class _EmpresaWriteMixin:
    @field_validator(
        "codigo_empresa",
        "razon_social",
        "ruc",
        "direccion_fiscal",
        "tipo_documento_tributario",
        "codigo_ciiu",
        "codigo_postal",
        "ubigeo",
        "representante_legal_dni",
        mode="before",
    )
    @classmethod
    def _upper_empresa(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "email_principal",
        "email_facturacion",
        "sitio_web",
        "logo_url",
        "logo_secundario_url",
        "favicon_url",
        mode="before",
    )
    @classmethod
    def _lower_empresa(cls, v: Optional[str]) -> Optional[str]:
        return normalize_lower(v)

    @field_validator(
        "nombre_comercial",
        "actividad_economica",
        "rubro",
        "tipo_empresa",
        "telefono_principal",
        "telefono_secundario",
        "representante_legal_nombre",
        "representante_legal_cargo",
        "zona_horaria",
        "idioma_sistema",
        "formato_fecha",
        "separador_miles",
        "separador_decimales",
        mode="before",
    )
    @classmethod
    def _strip_empresa(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _CentroCostoWriteMixin:
    @field_validator("codigo", "tipo_centro_costo", "ruta_jerarquica", mode="before")
    @classmethod
    def _upper_centro_costo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("nombre", "descripcion", "categoria", "responsable_nombre", mode="before")
    @classmethod
    def _strip_centro_costo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _SucursalWriteMixin:
    @field_validator("codigo", "ubigeo", "codigo_postal", "tipo_sucursal", mode="before")
    @classmethod
    def _upper_sucursal(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator("email", mode="before")
    @classmethod
    def _lower_sucursal(cls, v: Optional[str]) -> Optional[str]:
        return normalize_lower(v)

    @field_validator(
        "nombre",
        "descripcion",
        "direccion",
        "referencia",
        "telefono",
        "horario_atencion",
        "zona_horaria",
        "responsable_nombre",
        mode="before",
    )
    @classmethod
    def _strip_sucursal(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _DepartamentoWriteMixin:
    @field_validator("codigo", "ruta_jerarquica", mode="before")
    @classmethod
    def _upper_departamento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "nombre",
        "descripcion",
        "tipo_departamento",
        "jefe_nombre",
        mode="before",
    )
    @classmethod
    def _strip_departamento(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


class _CargoWriteMixin:
    @field_validator("codigo", mode="before")
    @classmethod
    def _upper_cargo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_upper(v)

    @field_validator(
        "nombre",
        "descripcion",
        "categoria",
        "area_funcional",
        "nivel_educacion_minimo",
        "requisitos_especificos",
        mode="before",
    )
    @classmethod
    def _strip_cargo(cls, v: Optional[str]) -> Optional[str]:
        return normalize_strip(v)


# ----- Empresa -----
class EmpresaCreate(_EmpresaWriteMixin, BaseModel):
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
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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
    moneda_base_id: Optional[UUID] = None
    maneja_multimoneda: Optional[bool] = False
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


class EmpresaUpdate(_EmpresaWriteMixin, BaseModel):
    codigo_empresa: Optional[str] = Field(None, max_length=20)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    tipo_documento_tributario: Optional[str] = None
    actividad_economica: Optional[str] = None
    codigo_ciiu: Optional[str] = None
    rubro: Optional[str] = None
    tipo_empresa: Optional[str] = None
    direccion_fiscal: Optional[str] = None
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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
    moneda_base_id: Optional[UUID] = None
    maneja_multimoneda: Optional[bool] = None
    zona_horaria: Optional[str] = None
    idioma_sistema: Optional[str] = None
    formato_fecha: Optional[str] = None
    separador_miles: Optional[str] = None
    separador_decimales: Optional[str] = None
    decimales_moneda: Optional[int] = None
    es_activo: Optional[bool] = None
    logo_url: Optional[str] = None
    logo_secundario_url: Optional[str] = None
    favicon_url: Optional[str] = None
    fecha_constitucion: Optional[date] = None
    fecha_inicio_operaciones: Optional[date] = None


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
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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
    moneda_base_id: Optional[UUID] = None
    maneja_multimoneda: Optional[bool] = None
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
    usuario_creacion_id: Optional[UUID] = None
    usuario_actualizacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ----- Centro de costo -----
class CentroCostoCreate(_CentroCostoWriteMixin, BaseModel):
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
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    es_activo: Optional[bool] = True
    fecha_inicio_vigencia: Optional[date] = None
    fecha_fin_vigencia: Optional[date] = None


class CentroCostoUpdate(_CentroCostoWriteMixin, BaseModel):
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
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
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
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ----- Sucursal -----
class SucursalCreate(_SucursalWriteMixin, BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    tipo_sucursal: Optional[str] = "sede"
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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


class SucursalUpdate(_SucursalWriteMixin, BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_sucursal: Optional[str] = None
    direccion: Optional[str] = None
    referencia: Optional[str] = None
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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
    pais_id: Optional[UUID] = None
    departamento_id: Optional[UUID] = None
    provincia_id: Optional[UUID] = None
    distrito_id: Optional[UUID] = None
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
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ----- Departamento -----
class DepartamentoCreate(_DepartamentoWriteMixin, BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    departamento_padre_id: Optional[UUID] = None
    nivel: Optional[int] = 1
    tipo_departamento: Optional[str] = None
    jefe_departamento_usuario_id: Optional[UUID] = None
    jefe_nombre: Optional[str] = None
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
    centro_costo_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    es_activo: Optional[bool] = True


class DepartamentoUpdate(_DepartamentoWriteMixin, BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    departamento_padre_id: Optional[UUID] = None
    nivel: Optional[int] = None
    tipo_departamento: Optional[str] = None
    jefe_departamento_usuario_id: Optional[UUID] = None
    jefe_nombre: Optional[str] = None
    ruta_jerarquica: Optional[str] = Field(None, max_length=500)
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
    usuario_creacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ----- Cargo -----
class CargoCreate(_CargoWriteMixin, BaseModel):
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
    moneda_salarial: UUID
    nivel_educacion_minimo: Optional[str] = None
    experiencia_minima_meses: Optional[int] = None
    requisitos_especificos: Optional[str] = None
    es_activo: Optional[bool] = True


class CargoUpdate(_CargoWriteMixin, BaseModel):
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
    moneda_salarial: Optional[UUID] = None
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
    moneda_salarial: UUID
    nivel_educacion_minimo: Optional[str] = None
    experiencia_minima_meses: Optional[int] = None
    requisitos_especificos: Optional[str] = None
    es_activo: bool
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    usuario_creacion_id: Optional[UUID] = None

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
    expresion_validacion: Optional[str] = Field(None, max_length=500)
    mensaje_validacion: Optional[str] = Field(None, max_length=255)
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
    usuario_actualizacion_id: Optional[UUID] = None

    class Config:
        from_attributes = True


from app.shared.pagination.schemas import ErpPaginatedResponse


class PaginatedCentroCostoResponse(ErpPaginatedResponse[CentroCostoRead]):
    """Listado paginado de centros de costo."""


class PaginatedParametroResponse(ErpPaginatedResponse[ParametroRead]):
    """Listado paginado de parámetros."""
