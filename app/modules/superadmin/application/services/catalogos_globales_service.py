from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func as sql_func, insert, or_, select, update

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

    @staticmethod
    def _normalizar_buscar(buscar: Optional[str]) -> Optional[str]:
        if buscar is None:
            return None
        trimmed = buscar.strip()
        return trimmed if trimmed else None

    @staticmethod
    def _extract_count(resultado: List[Dict[str, Any]]) -> int:
        if not resultado:
            return 0
        row = resultado[0]
        return int(row.get("count_1") or row.get("count") or next(iter(row.values()), 0))

    @staticmethod
    async def _contar_registros(*, client_id: UUID, table, conditions: list) -> int:
        query = select(sql_func.count()).select_from(table)
        if conditions:
            query = query.where(and_(*conditions))
        resultado = await execute_query(query, client_id=client_id)
        return CatalogosGlobalesService._extract_count(resultado)

    @staticmethod
    def _condiciones_listado_cat_moneda(
        solo_activos: bool,
        buscar: Optional[str] = None,
    ) -> list:
        conditions = []
        if solo_activos:
            conditions.append(CatMonedaTable.c.es_activo == True)
        termino = CatalogosGlobalesService._normalizar_buscar(buscar)
        if termino:
            pattern = f"%{termino.lower()}%"
            conditions.append(
                or_(
                    sql_func.lower(CatMonedaTable.c.codigo).like(pattern),
                    sql_func.lower(CatMonedaTable.c.nombre).like(pattern),
                    sql_func.lower(CatMonedaTable.c.simbolo).like(pattern),
                )
            )
        return conditions

    @staticmethod
    def _condiciones_listado_cat_pais(
        solo_activos: bool,
        buscar: Optional[str] = None,
    ) -> list:
        conditions = []
        if solo_activos:
            conditions.append(CatPaisTable.c.es_activo == True)
        termino = CatalogosGlobalesService._normalizar_buscar(buscar)
        if termino:
            pattern = f"%{termino.lower()}%"
            conditions.append(
                or_(
                    sql_func.lower(CatPaisTable.c.codigo_iso2).like(pattern),
                    sql_func.lower(CatPaisTable.c.codigo_iso3).like(pattern),
                    sql_func.lower(CatPaisTable.c.nombre).like(pattern),
                )
            )
        return conditions

    @staticmethod
    def _condiciones_listado_cat_departamento(
        solo_activos: bool,
        pais_id: Optional[UUID] = None,
        buscar: Optional[str] = None,
    ) -> list:
        conditions = []
        if pais_id:
            conditions.append(CatDepartamentoTable.c.pais_id == pais_id)
        if solo_activos:
            conditions.append(CatDepartamentoTable.c.es_activo == True)
        termino = CatalogosGlobalesService._normalizar_buscar(buscar)
        if termino:
            pattern = f"%{termino.lower()}%"
            conditions.append(
                or_(
                    sql_func.lower(CatDepartamentoTable.c.codigo).like(pattern),
                    sql_func.lower(CatDepartamentoTable.c.nombre).like(pattern),
                )
            )
        return conditions

    @staticmethod
    def _condiciones_listado_cat_provincia(
        solo_activos: bool,
        departamento_id: Optional[UUID] = None,
        buscar: Optional[str] = None,
    ) -> list:
        conditions = []
        if departamento_id:
            conditions.append(CatProvinciaTable.c.departamento_id == departamento_id)
        if solo_activos:
            conditions.append(CatProvinciaTable.c.es_activo == True)
        termino = CatalogosGlobalesService._normalizar_buscar(buscar)
        if termino:
            pattern = f"%{termino.lower()}%"
            conditions.append(
                or_(
                    sql_func.lower(CatProvinciaTable.c.codigo).like(pattern),
                    sql_func.lower(CatProvinciaTable.c.nombre).like(pattern),
                )
            )
        return conditions

    @staticmethod
    def _aplicar_joins_listado_cat_distrito(
        query,
        *,
        pais_id: Optional[UUID] = None,
        departamento_id: Optional[UUID] = None,
    ):
        if pais_id or departamento_id:
            query = query.join(
                CatProvinciaTable,
                CatDistritoTable.c.provincia_id == CatProvinciaTable.c.provincia_id,
            )
        if pais_id:
            query = query.join(
                CatDepartamentoTable,
                CatProvinciaTable.c.departamento_id == CatDepartamentoTable.c.departamento_id,
            )
        return query

    @staticmethod
    def _condiciones_listado_cat_distrito(
        solo_activos: bool,
        provincia_id: Optional[UUID] = None,
        departamento_id: Optional[UUID] = None,
        pais_id: Optional[UUID] = None,
        ubigeo: Optional[str] = None,
        buscar: Optional[str] = None,
    ) -> list:
        conditions = []
        if provincia_id:
            conditions.append(CatDistritoTable.c.provincia_id == provincia_id)
        if departamento_id:
            conditions.append(CatProvinciaTable.c.departamento_id == departamento_id)
        if pais_id:
            conditions.append(CatDepartamentoTable.c.pais_id == pais_id)
        if ubigeo:
            conditions.append(CatDistritoTable.c.ubigeo == ubigeo)
        if solo_activos:
            conditions.append(CatDistritoTable.c.es_activo == True)
        termino = CatalogosGlobalesService._normalizar_buscar(buscar)
        if termino:
            pattern = f"%{termino.lower()}%"
            conditions.append(
                or_(
                    sql_func.lower(CatDistritoTable.c.codigo).like(pattern),
                    sql_func.lower(CatDistritoTable.c.nombre).like(pattern),
                    sql_func.lower(CatDistritoTable.c.ubigeo).like(pattern),
                )
            )
        return conditions

    # -------------------------
    # cat_moneda
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_monedas(
        *,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_moneda(
            solo_activos, buscar
        )
        q = select(CatMonedaTable)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(CatMonedaTable.c.codigo).offset(skip).limit(limit)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_monedas(
        *,
        client_id: UUID,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> int:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_moneda(
            solo_activos, buscar
        )
        return await CatalogosGlobalesService._contar_registros(
            client_id=client_id,
            table=CatMonedaTable,
            conditions=conditions,
        )

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
    async def list_paises(
        *,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_pais(
            solo_activos, buscar
        )
        q = select(CatPaisTable)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(CatPaisTable.c.nombre).offset(skip).limit(limit)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_paises(
        *,
        client_id: UUID,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> int:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_pais(
            solo_activos, buscar
        )
        return await CatalogosGlobalesService._contar_registros(
            client_id=client_id,
            table=CatPaisTable,
            conditions=conditions,
        )

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
    async def list_departamentos(
        *,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100,
        pais_id: Optional[UUID] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_departamento(
            solo_activos, pais_id, buscar
        )
        q = select(CatDepartamentoTable)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(CatDepartamentoTable.c.nombre).offset(skip).limit(limit)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_departamentos(
        *,
        client_id: UUID,
        pais_id: Optional[UUID] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> int:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_departamento(
            solo_activos, pais_id, buscar
        )
        return await CatalogosGlobalesService._contar_registros(
            client_id=client_id,
            table=CatDepartamentoTable,
            conditions=conditions,
        )

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
            "es_activo": data.get("es_activo", True),
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
        payload = {k: v for k, v in data.items() if k in {"pais_id", "codigo", "nombre", "es_activo"} and v is not None}
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
        stmt = (
            update(CatDepartamentoTable)
            .where(CatDepartamentoTable.c.departamento_id == departamento_id)
            .values(es_activo=False)
        )
        await execute_update(stmt, client_id=client_id)

    # -------------------------
    # cat_provincia
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_provincias(
        *,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100,
        departamento_id: Optional[UUID] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_provincia(
            solo_activos, departamento_id, buscar
        )
        q = select(CatProvinciaTable)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(CatProvinciaTable.c.nombre).offset(skip).limit(limit)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_provincias(
        *,
        client_id: UUID,
        departamento_id: Optional[UUID] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> int:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_provincia(
            solo_activos, departamento_id, buscar
        )
        return await CatalogosGlobalesService._contar_registros(
            client_id=client_id,
            table=CatProvinciaTable,
            conditions=conditions,
        )

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
            "es_activo": data.get("es_activo", True),
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
        payload = {k: v for k, v in data.items() if k in {"departamento_id", "codigo", "nombre", "es_activo"} and v is not None}
        if not payload:
            return await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)
        stmt = update(CatProvinciaTable).where(CatProvinciaTable.c.provincia_id == provincia_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def delete_provincia(*, client_id: UUID, provincia_id: UUID) -> None:
        await CatalogosGlobalesService.get_provincia(client_id=client_id, provincia_id=provincia_id)
        stmt = update(CatProvinciaTable).where(CatProvinciaTable.c.provincia_id == provincia_id).values(es_activo=False)
        await execute_update(stmt, client_id=client_id)

    # -------------------------
    # cat_distrito
    # -------------------------
    @staticmethod
    @BaseService.handle_service_errors
    async def list_distritos(
        *,
        client_id: UUID,
        skip: int = 0,
        limit: int = 100,
        pais_id: Optional[UUID] = None,
        departamento_id: Optional[UUID] = None,
        provincia_id: Optional[UUID] = None,
        ubigeo: Optional[str] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_distrito(
            solo_activos, provincia_id, departamento_id, pais_id, ubigeo, buscar
        )
        q = select(CatDistritoTable)
        q = CatalogosGlobalesService._aplicar_joins_listado_cat_distrito(
            q, pais_id=pais_id, departamento_id=departamento_id
        )
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(CatDistritoTable.c.nombre).offset(skip).limit(limit)
        return await execute_query(q, client_id=client_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def contar_distritos(
        *,
        client_id: UUID,
        pais_id: Optional[UUID] = None,
        departamento_id: Optional[UUID] = None,
        provincia_id: Optional[UUID] = None,
        ubigeo: Optional[str] = None,
        solo_activos: bool = True,
        buscar: Optional[str] = None,
    ) -> int:
        conditions = CatalogosGlobalesService._condiciones_listado_cat_distrito(
            solo_activos, provincia_id, departamento_id, pais_id, ubigeo, buscar
        )
        q = select(sql_func.count()).select_from(CatDistritoTable)
        q = CatalogosGlobalesService._aplicar_joins_listado_cat_distrito(
            q, pais_id=pais_id, departamento_id=departamento_id
        )
        if conditions:
            q = q.where(and_(*conditions))
        resultado = await execute_query(q, client_id=client_id)
        return CatalogosGlobalesService._extract_count(resultado)

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
            "es_activo": data.get("es_activo", True),
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
        payload = {
            k: v
            for k, v in data.items()
            if k in {"provincia_id", "codigo", "nombre", "ubigeo", "es_activo"} and v is not None
        }
        if not payload:
            return await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)
        stmt = update(CatDistritoTable).where(CatDistritoTable.c.distrito_id == distrito_id).values(**payload)
        await execute_update(stmt, client_id=client_id)
        return await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)

    @staticmethod
    @BaseService.handle_service_errors
    async def delete_distrito(*, client_id: UUID, distrito_id: UUID) -> None:
        await CatalogosGlobalesService.get_distrito(client_id=client_id, distrito_id=distrito_id)
        stmt = update(CatDistritoTable).where(CatDistritoTable.c.distrito_id == distrito_id).values(es_activo=False)
        await execute_update(stmt, client_id=client_id)

