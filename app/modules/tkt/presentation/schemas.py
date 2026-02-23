# app/modules/tkt/presentation/schemas.py
"""Schemas Pydantic para el modulo TKT (Mesa de Ayuda). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    empresa_id: UUID
    numero_ticket: str = Field(..., max_length=20)
    solicitante_usuario_id: Optional[UUID] = None
    solicitante_nombre: Optional[str] = Field(None, max_length=150)
    solicitante_email: Optional[str] = Field(None, max_length=100)
    asunto: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    categoria: Optional[str] = Field(None, max_length=50)
    prioridad: Optional[str] = Field("media", max_length=20)
    asignado_usuario_id: Optional[UUID] = None
    fecha_asignacion: Optional[datetime] = None
    estado: Optional[str] = Field("abierto", max_length=20)
    fecha_resolucion: Optional[datetime] = None
    solucion: Optional[str] = None


class TicketUpdate(BaseModel):
    numero_ticket: Optional[str] = None
    solicitante_usuario_id: Optional[UUID] = None
    solicitante_nombre: Optional[str] = None
    solicitante_email: Optional[str] = None
    asunto: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    prioridad: Optional[str] = None
    asignado_usuario_id: Optional[UUID] = None
    fecha_asignacion: Optional[datetime] = None
    estado: Optional[str] = None
    fecha_resolucion: Optional[datetime] = None
    solucion: Optional[str] = None


class TicketRead(BaseModel):
    ticket_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_ticket: str
    fecha_creacion: datetime
    solicitante_usuario_id: Optional[UUID]
    solicitante_nombre: Optional[str]
    solicitante_email: Optional[str]
    asunto: str
    descripcion: Optional[str]
    categoria: Optional[str]
    prioridad: Optional[str]
    asignado_usuario_id: Optional[UUID]
    fecha_asignacion: Optional[datetime]
    estado: Optional[str]
    fecha_resolucion: Optional[datetime]
    tiempo_resolucion_horas: Optional[float] = None
    solucion: Optional[str]

    class Config:
        from_attributes = True
