from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update

from app.core.application.base_service import BaseService
from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.infrastructure.database.tables_erp import (
    CatMonedaTable,
    CatPaisTable,
    CatDepartamentoTable,
    CatProvinciaTable,
    CatDistritoTable,
)


class CatalogosGlobalesService(BaseService):
    """
    Operaciones CRUD sobre catálogos globales (cat_*) en BD dedicada del tenant.
    Solo accesible por Superadmin (la capa de endpoints aplica la restricción).
    """

    # -------------------------
    # cat_moneda
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_monedas(*, client_id: UUID, solo_activos: bool = True) -> List[Dict[str, Any]]:
        q = select(CatMonedaTable)
        if solo_activos:
            q = q.where(CatMonedaTable.c.es_activo == True)
        q = q.order_by(CatMonedaTable.c.codigo)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def get_moneda(*, client_id: UUID, moneda_id: UUID) -> Dict[str, Any]:
        q = select(CatMonedaTable).where(CatMonedaTable.c.moneda_id == moneda_id)
        rows = await execute_query(q, client_id=client_id)
        if not rows:
            raise NotFoundError(detail="Moneda no encontrada")
        return rows[0]

    @staticmethod
    @BaseService.handle_service_errors
    async def create_moneda(*, client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        moneda_id = uuid4()
        payload = {
            "moneda_id": moneda_id,
            "codigo": (data.get("codigo") or "").upper(),
            "nombre": data.get("nombre"),
            "simbolo": data.get("simbolo"),
            "decimales": data.get("decimales", 2),
            "es_activo": data.get("es_activo", True),
        }
        if not payload["codigo"] or len(payload["codigo"]) != 3:
            raise ValidationError(detail="codigo debe tener 3 caracteres")
        stmt = insert(CatMonedaTable).values(**payload)
        await execute_insert(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_moneda(client_id=client_id, moneda_id=moneda_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def update_moneda(*, client_id: UUID, moneda_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        await CatalogosGlobalesService.get_moneda(client_id=client_id, moneda_id=moneda_id)
        payload = {k: v for k, v in data.items() if k in {"nombre", "simbolo", "decimales", "es_activo"}}
        if not payload:
            return await CatalogosGlobalesService.get_moneda(client_id=client_id, moneda_id=moneda_id)
        stmt = update(CatMonedaTable).where(CatMonedaTable.c.moneda_id == moneda_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_moneda(client_id=client_id, moneda_id=moneda_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def deactivate_moneda(*, client_id: UUID, moneda_id: UUID) -> None:
        await CatalogosGlobalesService.get_moneda(client_id=client_id, moneda_id=moneda_id)
        stmt = update(CatMonedaTable).where(CatMonedaTable.c.moneda_id == moneda_id).values(es_activo=False)
        await execute_update(stmt, client_id=client_id)

    # -------------------------
    # cat_pais
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_paises(*, client_id: UUID, solo_activos: bool = True) -> List[Dict[str, Any]]:
        q = select(CatPaisTable)
        if solo_activos:
            q = q.where(CatPaisTable.c.es_activo == True)
        q = q.order_by(CatPaisTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def get_pais(*, client_id: UUID, pais_id: UUID) -> Dict[str, Any]:
        q = select(CatPaisTable).where(CatPaisTable.c.pais_id == pais_id)
        rows = await execute_query(q, client_id=client_id)
        if not rows:
            raise NotFoundError(detail="País no encontrado")
        return rows[0]

    @staticmethod
    @BaseService.handle_service_errors
    async def create_pais(*, client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        pais_id = uuid4()
        payload = {
            "pais_id": pais_id,
            "codigo_iso2": (data.get("codigo_iso2") or "").upper(),
            "codigo_iso3": (data.get("codigo_iso3") or "").upper(),
            "nombre": data.get("nombre"),
            "es_activo": data.get("es_activo", True),
        }
        if not payload["codigo_iso2"] or len(payload["codigo_iso2"]) != 2:
            raise ValidationError(detail="codigo_iso2 debe tener 2 caracteres")
        if not payload["codigo_iso3"] or len(payload["codigo_iso3"]) != 3:
            raise ValidationError(detail="codigo_iso3 debe tener 3 caracteres")
        stmt = insert(CatPaisTable).values(**payload)
        await execute_insert(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_pais(client_id=client_id, pais_id=pais_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def update_pais(*, client_id: UUID, pais_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        await CatalogosGlobalesService.get_pais(client_id=client_id, pais_id=pais_id)
        payload = {}
        for key in ("codigo_iso2", "codigo_iso3", "nombre", "es_activo"):
            if key in data and data[key] is not None:
                payload[key] = data[key]
        if "codigo_iso2" in payload:
            payload["codigo_iso2"] = str(payload["codigo_iso2"]).upper()
        if "codigo_iso3" in payload:
            payload["codigo_iso3"] = str(payload["codigo_iso3"]).upper()
        if not payload:
            return await CatalogosGlobalesService.get_pais(client_id=client_id, pais_id=pais_id)
        stmt = update(CatPaisTable).where(CatPaisTable.c.pais_id == pais_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_pais(client_id=client_id, pais_id=pais_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def deactivate_pais(*, client_id: UUID, pais_id: UUID) -> None:
        await CatalogosGlobalesService.get_pais(client_id=client_id, pais_id=pais_id)
        stmt = update(CatPaisTable).where(CatPaisTable.c.pais_id == pais_id).values(es_activo=False)
        await execute_update(stmt, client_id=client_id)

    # -------------------------
    # cat_departamento
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_departamentos(*, client_id: UUID, pais_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        q = select(CatDepartamentoTable)
        if pais_id:
            q = q.where(CatDepartamentoTable.c.pais_id == pais_id)
        q = q.order_by(CatDepartamentoTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def get_departamento(*, client_id: UUID, departamento_id: UUID) -> Dict[str, Any]:
        q = select(CatDepartamentoTable).where(CatDepartamentoTable.c.departamento_id == departamento_id)
        rows = await execute_query(q, client_id=client_id)
        if not rows:
            raise NotFoundError(detail="Departamento no encontrado")
        return rows[0]

    @staticmethod
    @BaseService.handle_service_errors
    async def create_departamento(*, client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        departamento_id = uuid4()
        payload = {
            "departamento_id": departamento_id,
            "pais_id": data.get("pais_id"),
            "codigo": data.get("codigo"),
            "nombre": data.get("nombre"),
        }
        if not payload["pais_id"]:
            raise ValidationError(detail="pais_id es obligatorio")
        stmt = insert(CatDepartamentoTable).values(**payload)
        await execute_insert(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_departamento(client_id=client_id, departamento_id=departamento_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def update_departamento(*, client_id: UUID, departamento_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        await CatalogosGlobalesService.get_departamento(client_id=client_id, departamento_id=departamento_id)
        payload = {k: v for k, v in data.items() if k in {"pais_id", "codigo", "nombre"} and v is not None}
        if not payload:
            return await CatalogosGlobalesService.get_departamento(client_id=client_id, departamento_id=departamento_id)
        stmt = (
            update(CatDepartamentoTable)
            .where(CatDepartamentoTable.c.departamento_id == departamento_id)
            .values(**payload)
        )
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_departamento(client_id=client_id, departamento_id=departamento_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def delete_departamento(*, client_id: UUID, departamento_id: UUID) -> None:
        await CatalogosGlobalesService.get_departamento(client_id=client_id, departamento_id=departamento_id)
        stmt = delete(CatDepartamentoTable).where(CatDepartamentoTable.c.departamento_id == departamento_id)
        await execute_query(stmt, client_id=client_id)

    # -------------------------
    # cat_provincia
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_provincias(*, client_id: UUID, departamento_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        q = select(CatProvinciaTable)
        if departamento_id:
            q = q.where(CatProvinciaTable.c.departamento_id == departamento_id)
        q = q.order_by(CatProvinciaTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def get_provincia(*, client_id: UUID, provincia_id: UUID) -> Dict[str, Any]:
        q = select(CatProvinciaTable).where(CatProvinciaTable.c.provincia_id == provincia_id)
        rows = await execute_query(q, client_id=client_id)
        if not rows:
            raise NotFoundError(detail="Provincia no encontrada")
        return rows[0]

    @staticmethod
    @BaseService.handle_service_errors
    async def create_provincia(*, client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        provincia_id = uuid4()
        payload = {
            "provincia_id": provincia_id,
            "departamento_id": data.get("departamento_id"),
            "codigo": data.get("codigo"),
            "nombre": data.get("nombre"),
        }
        if not payload["departamento_id"]:
            raise ValidationError(detail="departamento_id es obligatorio")
        stmt = insert(CatProvinciaTable).values(**payload)
        await execute_insert(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def update_provincia(*, client_id: UUID, provincia_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)
        payload = {k: v for k, v in data.items() if k in {"departamento_id", "codigo", "nombre"} and v is not None}
        if not payload:
            return await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)
        stmt = update(CatProvinciaTable).where(CatProvinciaTable.c.provincia_id == provincia_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def delete_provincia(*, client_id: UUID, provincia_id: UUID) -> None:
        await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)
        stmt = delete(CatProvinciaTable).where(CatProvinciaTable.c.provincia_id == provincia_id)
        await execute_query(stmt, client_id=client_id)

    # -------------------------
    # cat_distrito
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_distritos(
        *,
        client_id: UUID,
        provincia_id: Optional[UUID] = None,
        ubigeo: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = select(CatDistritoTable)
        if provincia_id:
            q = q.where(CatDistritoTable.c.provincia_id == provincia_id)
        if ubigeo:
            q = q.where(CatDistritoTable.c.ubigeo == ubigeo)
        q = q.order_by(CatDistritoTable.c.nombre)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def get_distrito(*, client_id: UUID, distrito_id: UUID) -> Dict[str, Any]:
        q = select(CatDistritoTable).where(CatDistritoTable.c.distrito_id == distrito_id)
        rows = await execute_query(q, client_id=client_id)
        if not rows:
            raise NotFoundError(detail="Distrito no encontrado")
        return rows[0]

    @staticmethod
    @BaseService.handle_service_errors
    async def create_distrito(*, client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        distrito_id = uuid4()
        payload = {
            "distrito_id": distrito_id,
            "provincia_id": data.get("provincia_id"),
            "codigo": data.get("codigo"),
            "nombre": data.get("nombre"),
            "ubigeo": data.get("ubigeo"),
        }
        if not payload["provincia_id"]:
            raise ValidationError(detail="provincia_id es obligatorio")
        if not payload["ubigeo"]:
            raise ValidationError(detail="ubigeo es obligatorio")
        stmt = insert(CatDistritoTable).values(**payload)
        await execute_insert(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def update_distrito(*, client_id: UUID, distrito_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)
        payload = {k: v for k, v in data.items() if k in {"provincia_id", "codigo", "nombre", "ubigeo"} and v is not None}
        if not payload:
            return await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)
        stmt = update(CatDistritoTable).where(CatDistritoTable.c.distrito_id == distrito_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def delete_distrito(*, client_id: UUID, distrito_id: UUID) -> None:
        await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)
        stmt = delete(CatDistritoTable).where(CatDistritoTable.c.distrito_id == distrito_id)
        await execute_query(stmt, client_id=client_id)

