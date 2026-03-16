from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MonedaRead(BaseModel):
    moneda_id: UUID
    codigo: str
    nombre: str
    simbolo: str
    decimales: Optional[int] = None
    es_activo: Optional[bool] = None


class PaisRead(BaseModel):
    pais_id: UUID
    codigo_iso2: str
    codigo_iso3: str
    nombre: str
    es_activo: Optional[bool] = None


class DepartamentoRead(BaseModel):
    departamento_id: UUID
    pais_id: UUID
    codigo: str
    nombre: str


class ProvinciaRead(BaseModel):
    provincia_id: UUID
    departamento_id: UUID
    codigo: str
    nombre: str


class DistritoRead(BaseModel):
    distrito_id: UUID
    provincia_id: UUID
    codigo: str
    nombre: str
    ubigeo: str

