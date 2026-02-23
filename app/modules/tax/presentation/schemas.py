# app/modules/tax/presentation/schemas.py
"""Schemas Pydantic para el módulo TAX (Libros Electrónicos). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# ========== Libro Electrónico ==========
# API usa "anio"; BD usa "año". Conversión en servicio.
class LibroElectronicoCreate(BaseModel):
    empresa_id: UUID
    tipo_libro: str = Field(..., max_length=30)
    periodo_id: UUID
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    nombre_archivo: Optional[str] = Field(None, max_length=255)
    ruta_archivo: Optional[str] = Field(None, max_length=500)
    estado: Optional[str] = Field("generado", max_length=20)
    fecha_envio_sunat: Optional[datetime] = None
    codigo_respuesta_sunat: Optional[str] = Field(None, max_length=10)
    total_registros: Optional[int] = Field(0, ge=0)
    observaciones: Optional[str] = None
    generado_por_usuario_id: Optional[UUID] = None


class LibroElectronicoUpdate(BaseModel):
    nombre_archivo: Optional[str] = None
    ruta_archivo: Optional[str] = None
    estado: Optional[str] = None
    fecha_envio_sunat: Optional[datetime] = None
    codigo_respuesta_sunat: Optional[str] = None
    total_registros: Optional[int] = None
    observaciones: Optional[str] = None


class LibroElectronicoRead(BaseModel):
    libro_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    tipo_libro: str
    periodo_id: UUID
    anio: int
    mes: int
    fecha_generacion: datetime
    nombre_archivo: Optional[str]
    ruta_archivo: Optional[str]
    estado: Optional[str]
    fecha_envio_sunat: Optional[datetime]
    codigo_respuesta_sunat: Optional[str]
    total_registros: Optional[int]
    observaciones: Optional[str]
    fecha_creacion: datetime
    generado_por_usuario_id: Optional[UUID]

    class Config:
        from_attributes = True
