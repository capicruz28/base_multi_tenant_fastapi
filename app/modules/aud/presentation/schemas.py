# app/modules/aud/presentation/schemas.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class LogAuditoriaCreate(BaseModel):
    empresa_id: UUID
    usuario_id: Optional[UUID] = None
    usuario_nombre: Optional[str] = Field(None, max_length=150)
    modulo: str = Field(..., max_length=10)
    tabla: str = Field(..., max_length=100)
    accion: str = Field(..., max_length=20)
    registro_id: Optional[UUID] = None
    registro_descripcion: Optional[str] = Field(None, max_length=255)
    valores_anteriores: Optional[str] = None
    valores_nuevos: Optional[str] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    observaciones: Optional[str] = Field(None, max_length=500)


class LogAuditoriaRead(BaseModel):
    log_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    fecha_evento: datetime
    usuario_id: Optional[UUID]
    usuario_nombre: Optional[str]
    modulo: str
    tabla: str
    accion: str
    registro_id: Optional[UUID]
    registro_descripcion: Optional[str]
    valores_anteriores: Optional[str]
    valores_nuevos: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    observaciones: Optional[str]

    class Config:
        from_attributes = True
