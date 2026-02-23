# app/modules/dms/presentation/schemas.py
"""Schemas Pydantic para el modulo DMS. API usa tamano_bytes; BD usa tamaño_bytes."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentoCreate(BaseModel):
    empresa_id: UUID
    codigo_documento: Optional[str] = Field(None, max_length=20)
    nombre_archivo: str = Field(..., max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_documento: str = Field(..., max_length=50)
    categoria: Optional[str] = Field(None, max_length=50)
    ruta_archivo: str = Field(..., max_length=500)
    tamano_bytes: Optional[int] = Field(None, ge=0)
    extension: Optional[str] = Field(None, max_length=10)
    mime_type: Optional[str] = Field(None, max_length=100)
    carpeta: Optional[str] = Field(None, max_length=255)
    tags: Optional[str] = None
    entidad_tipo: Optional[str] = Field(None, max_length=30)
    entidad_id: Optional[UUID] = None
    version: Optional[str] = Field("1.0", max_length=10)
    documento_padre_id: Optional[UUID] = None
    es_confidencial: Optional[bool] = False
    nivel_acceso: Optional[str] = Field("general", max_length=20)
    estado: Optional[str] = Field("activo", max_length=20)
    subido_por_usuario_id: Optional[UUID] = None


class DocumentoUpdate(BaseModel):
    codigo_documento: Optional[str] = None
    nombre_archivo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_documento: Optional[str] = None
    categoria: Optional[str] = None
    ruta_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    carpeta: Optional[str] = None
    tags: Optional[str] = None
    entidad_tipo: Optional[str] = None
    entidad_id: Optional[UUID] = None
    version: Optional[str] = None
    documento_padre_id: Optional[UUID] = None
    es_confidencial: Optional[bool] = None
    nivel_acceso: Optional[str] = None
    estado: Optional[str] = None
    subido_por_usuario_id: Optional[UUID] = None


class DocumentoRead(BaseModel):
    documento_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo_documento: Optional[str]
    nombre_archivo: str
    descripcion: Optional[str]
    tipo_documento: str
    categoria: Optional[str]
    ruta_archivo: str
    tamano_bytes: Optional[int]
    extension: Optional[str]
    mime_type: Optional[str]
    carpeta: Optional[str]
    tags: Optional[str]
    entidad_tipo: Optional[str]
    entidad_id: Optional[UUID]
    version: Optional[str]
    documento_padre_id: Optional[UUID]
    es_confidencial: Optional[bool]
    nivel_acceso: Optional[str]
    estado: Optional[str]
    fecha_creacion: datetime
    fecha_modificacion: Optional[datetime]
    subido_por_usuario_id: Optional[UUID]

    class Config:
        from_attributes = True
