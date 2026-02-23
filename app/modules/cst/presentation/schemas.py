# app/modules/cst/presentation/schemas.py
"""Schemas Pydantic para el módulo CST (Costeo de Productos). Create/Update no incluyen cliente_id."""
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ========== Centro de Costo Tipo ==========
class CentroCostoTipoCreate(BaseModel):
    empresa_id: UUID
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    tipo_clasificacion: str = Field(..., max_length=30)
    base_distribucion: Optional[str] = Field(None, max_length=30)
    es_activo: Optional[bool] = True


class CentroCostoTipoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    tipo_clasificacion: Optional[str] = None
    base_distribucion: Optional[str] = None
    es_activo: Optional[bool] = None


class CentroCostoTipoRead(BaseModel):
    cc_tipo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    codigo: str
    nombre: str
    tipo_clasificacion: Optional[str]
    base_distribucion: Optional[str]
    es_activo: Optional[bool]
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# ========== Producto Costo ==========
# API usa "anio"; BD usa "año". Conversión en servicio.
class ProductoCostoCreate(BaseModel):
    empresa_id: UUID
    producto_id: UUID
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    costo_material_directo: Optional[Decimal] = Field(0, ge=0)
    costo_mano_obra_directa: Optional[Decimal] = Field(0, ge=0)
    costo_indirecto_fabricacion: Optional[Decimal] = Field(0, ge=0)
    cantidad_producida: Optional[Decimal] = Field(0, ge=0)
    orden_produccion_id: Optional[UUID] = None
    metodo_costeo: Optional[str] = Field("real", max_length=20)
    observaciones: Optional[str] = None


class ProductoCostoUpdate(BaseModel):
    costo_material_directo: Optional[Decimal] = None
    costo_mano_obra_directa: Optional[Decimal] = None
    costo_indirecto_fabricacion: Optional[Decimal] = None
    cantidad_producida: Optional[Decimal] = None
    orden_produccion_id: Optional[UUID] = None
    metodo_costeo: Optional[str] = None
    observaciones: Optional[str] = None


class ProductoCostoRead(BaseModel):
    producto_costo_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    producto_id: UUID
    anio: int
    mes: int
    costo_material_directo: Optional[Decimal]
    costo_mano_obra_directa: Optional[Decimal]
    costo_indirecto_fabricacion: Optional[Decimal]
    costo_total: Optional[Decimal] = None
    cantidad_producida: Optional[Decimal]
    costo_unitario: Optional[Decimal] = None
    orden_produccion_id: Optional[UUID]
    metodo_costeo: Optional[str]
    observaciones: Optional[str]
    fecha_creacion: datetime
    fecha_calculo: Optional[datetime]

    class Config:
        from_attributes = True
