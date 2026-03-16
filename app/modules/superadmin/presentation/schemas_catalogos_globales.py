from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CatMonedaBase(BaseModel):
    codigo: str = Field(..., max_length=3)
    nombre: str = Field(..., max_length=50)
    simbolo: str = Field(..., max_length=5)
    decimales: Optional[int] = 2
    es_activo: Optional[bool] = True


class CatMonedaCreate(CatMonedaBase):
    pass


class CatMonedaUpdate(BaseModel):
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    decimales: Optional[int] = None
    es_activo: Optional[bool] = None


class CatMonedaRead(CatMonedaBase):
    moneda_id: UUID

    class Config:
        from_attributes = True


class CatPaisBase(BaseModel):
    codigo_iso2: str = Field(..., max_length=2)
    codigo_iso3: str = Field(..., max_length=3)
    nombre: str = Field(..., max_length=100)
    es_activo: Optional[bool] = True


class CatPaisCreate(CatPaisBase):
    pass


class CatPaisUpdate(BaseModel):
    codigo_iso2: Optional[str] = None
    codigo_iso3: Optional[str] = None
    nombre: Optional[str] = None
    es_activo: Optional[bool] = None


class CatPaisRead(CatPaisBase):
    pais_id: UUID

    class Config:
        from_attributes = True


class CatDepartamentoBase(BaseModel):
    pais_id: UUID
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)


class CatDepartamentoCreate(CatDepartamentoBase):
    pass


class CatDepartamentoUpdate(BaseModel):
    pais_id: Optional[UUID] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None


class CatDepartamentoRead(CatDepartamentoBase):
    departamento_id: UUID

    class Config:
        from_attributes = True


class CatProvinciaBase(BaseModel):
    departamento_id: UUID
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)


class CatProvinciaCreate(CatProvinciaBase):
    pass


class CatProvinciaUpdate(BaseModel):
    departamento_id: Optional[UUID] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None


class CatProvinciaRead(CatProvinciaBase):
    provincia_id: UUID

    class Config:
        from_attributes = True


class CatDistritoBase(BaseModel):
    provincia_id: UUID
    codigo: str = Field(..., max_length=10)
    nombre: str = Field(..., max_length=100)
    ubigeo: str = Field(..., max_length=6)


class CatDistritoCreate(CatDistritoBase):
    pass


class CatDistritoUpdate(BaseModel):
    provincia_id: Optional[UUID] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    ubigeo: Optional[str] = None


class CatDistritoRead(CatDistritoBase):
    distrito_id: UUID

    class Config:
        from_attributes = True

