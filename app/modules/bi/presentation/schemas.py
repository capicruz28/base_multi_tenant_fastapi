# app/modules/bi/presentation/schemas.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ReporteCreate(BaseModel):
    empresa_id: UUID
    codigo_reporte: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=150)
    descripcion: Optional[str] = Field(None, max_length=500)
    modulo_origen: Optional[str] = Field(None, max_length=10)
    categoria: Optional[str] = Field(None, max_length=50)
    tipo_reporte: Optional[str] = Field("sql", max_length=20)
    query_sql: Optional[str] = None
    configuracion_json: Optional[str] = None
    es_publico: Optional[bool] = False
    creado_por_usuario_id: Optional[UUID] = None
    es_activo: Optional[bool] = True


class ReporteUpdate(BaseModel):
    codigo_reporte: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    modulo_origen: Optional[str] = None
    categoria: Optional[str] = None
    tipo_reporte: Optional[str] = None
    query_sql: Optional[str] = None
    configuracion_json: Optional[str] = None
    es_publico: Optional[bool] = None
    es_activo: Optional[bool] = None


class ReporteRead(BaseModel):
    reporte_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_reporte: str
    nombre: str
    descripcion: Optional[str]
    modulo_origen: Optional[str]
    categoria: Optional[str]
    tipo_reporte: Optional[str]
    query_sql: Optional[str]
    configuracion_json: Optional[str]
    es_publico: Optional[bool]
    creado_por_usuario_id: Optional[UUID]
    es_activo: Optional[bool]
    fecha_creacion: datetime

    class Config:
        from_attributes = True
