from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select

from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables_erp import (
    CatMonedaTable,
    CatPaisTable,
    CatDepartamentoTable,
    CatProvinciaTable,
    CatDistritoTable,
)


class CatalogosService:
    """
    Lectura de catálogos globales (cat_*) para consumo del ERP (tenants).
    Nota: La administración/CRUD es exclusiva de Superadmin.
    """

    @staticmethod
    async def list_monedas(*, client_id: UUID, solo_activos: bool = True) -> List[Dict[str, Any]]:
        q = select(CatMonedaTable)
        if solo_activos:
            q = q.where(CatMonedaTable.c.es_activo == True)
        q = q.order_by(CatMonedaTable.c.codigo)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    async def list_paises(*, client_id: UUID, solo_activos: bool = True) -> List[Dict[str, Any]]:
        q = select(CatPaisTable)
        if solo_activos:
            q = q.where(CatPaisTable.c.es_activo == True)
        q = q.order_by(CatPaisTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    async def list_departamentos(
        *,
        client_id: UUID,
        pais_id: Optional[UUID] = None,
        solo_activos: bool = True,
    ) -> List[Dict[str, Any]]:
        q = select(CatDepartamentoTable)
        if pais_id:
            q = q.where(CatDepartamentoTable.c.pais_id == pais_id)
        if solo_activos:
            q = q.where(CatDepartamentoTable.c.es_activo == True)
        q = q.order_by(CatDepartamentoTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    async def list_provincias(
        *,
        client_id: UUID,
        departamento_id: Optional[UUID] = None,
        solo_activos: bool = True,
    ) -> List[Dict[str, Any]]:
        q = select(CatProvinciaTable)
        if departamento_id:
            q = q.where(CatProvinciaTable.c.departamento_id == departamento_id)
        if solo_activos:
            q = q.where(CatProvinciaTable.c.es_activo == True)
        q = q.order_by(CatProvinciaTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    async def list_distritos(
        *,
        client_id: UUID,
        provincia_id: Optional[UUID] = None,
        ubigeo: Optional[str] = None,
        solo_activos: bool = True,
    ) -> List[Dict[str, Any]]:
        q = select(CatDistritoTable)
        if provincia_id:
            q = q.where(CatDistritoTable.c.provincia_id == provincia_id)
        if ubigeo:
            q = q.where(CatDistritoTable.c.ubigeo == ubigeo)
        if solo_activos:
            q = q.where(CatDistritoTable.c.es_activo == True)
        q = q.order_by(CatDistritoTable.c.nombre)
        return await execute_query(q, client_id=client_id)

