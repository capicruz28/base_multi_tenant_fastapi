"""
Repositorio para cfg_codigo_secuencia (secuencias de códigos por tenant/empresa).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_insert, execute_query, execute_update
from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.tables import CfgCodigoSecuenciaTable

logger = logging.getLogger(__name__)


class CfgCodigoSecuenciaRepository(BaseRepository):
    """Acceso a datos de secuencias de códigos (BD central / ADMIN)."""

    def __init__(self) -> None:
        super().__init__(
            table_name="cfg_codigo_secuencia",
            id_column="secuencia_id",
            tenant_column="cliente_id",
            connection_type=DatabaseConnection.ADMIN,
        )

    def _empresa_filter(self, empresa_id: Optional[UUID]):
        if empresa_id is None:
            return CfgCodigoSecuenciaTable.c.empresa_id.is_(None)
        return CfgCodigoSecuenciaTable.c.empresa_id == empresa_id

    @staticmethod
    def _rows_to_dicts(result) -> List[Dict[str, Any]]:
        rows = result.fetchall()
        if not rows:
            return []
        keys = result.keys()
        return [dict(zip(keys, row)) for row in rows]

    @staticmethod
    def _row_to_dict(result) -> Optional[Dict[str, Any]]:
        row = result.fetchone()
        if not row:
            return None
        return dict(zip(result.keys(), row))

    async def get_by_cliente(
        self,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """Lista todas las secuencias de un cliente."""
        stmt = (
            select(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.cliente_id == cliente_id)
            .order_by(CfgCodigoSecuenciaTable.c.entidad)
        )
        if session is not None:
            result = await session.execute(stmt)
            return self._rows_to_dicts(result)
        return await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
            skip_tenant_validation=True,
        )

    async def get_by_entidad(
        self,
        cliente_id: UUID,
        empresa_id: Optional[UUID],
        entidad: str,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una secuencia por cliente, empresa (opcional) y entidad."""
        stmt = select(CfgCodigoSecuenciaTable).where(
            and_(
                CfgCodigoSecuenciaTable.c.cliente_id == cliente_id,
                self._empresa_filter(empresa_id),
                CfgCodigoSecuenciaTable.c.entidad == entidad,
            )
        )
        if session is not None:
            result = await session.execute(stmt)
            return self._row_to_dict(result)
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
            skip_tenant_validation=True,
        )
        return rows[0] if rows else None

    async def insert_secuencia(
        self,
        cliente_id: UUID,
        empresa_id: Optional[UUID],
        entidad: str,
        prefijo: str,
        longitud_numero: int,
        separador: str,
        *,
        session: Optional[AsyncSession] = None,
        ultimo_numero: int = 0,
    ) -> Dict[str, Any]:
        """
        Inserta una secuencia y devuelve el registro.
        Idempotente: si ya existe para (cliente_id, empresa_id, entidad), devuelve la existente.
        """
        existing = await self.get_by_entidad(
            cliente_id, empresa_id, entidad, session=session
        )
        if existing:
            return existing

        values = {
            "secuencia_id": uuid4(),
            "cliente_id": cliente_id,
            "empresa_id": empresa_id,
            "entidad": entidad,
            "prefijo": prefijo,
            "longitud_numero": longitud_numero,
            "ultimo_numero": ultimo_numero,
            "separador": separador if separador is not None else "",
            "es_activo": True,
        }
        stmt = insert(CfgCodigoSecuenciaTable).values(**values)

        if session is not None:
            await session.execute(stmt)
            inserted = await self.get_by_entidad(
                cliente_id, empresa_id, entidad, session=session
            )
            if inserted:
                return inserted
            return values

        await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        inserted = await self.get_by_entidad(cliente_id, empresa_id, entidad)
        if inserted:
            return inserted
        return values

    async def update_ultimo_numero(
        self,
        secuencia_id: UUID,
        nuevo_numero: int,
        *,
        cliente_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Actualiza el contador ultimo_numero de una secuencia."""
        stmt = (
            update(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id)
            .values(ultimo_numero=nuevo_numero)
        )
        if cliente_id is not None:
            stmt = stmt.where(CfgCodigoSecuenciaTable.c.cliente_id == cliente_id)

        if session is not None:
            await session.execute(stmt)
            fetch = select(CfgCodigoSecuenciaTable).where(
                CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id
            )
            result = await session.execute(fetch)
            return self._row_to_dict(result)

        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        return await self.find_by_id(secuencia_id, client_id=cliente_id)

    async def update_secuencia(
        self,
        secuencia_id: UUID,
        prefijo: str,
        longitud_numero: int,
        separador: str,
        es_activo: bool,
        *,
        cliente_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Actualización general de una secuencia (CRUD)."""
        stmt = (
            update(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id)
            .values(
                prefijo=prefijo,
                longitud_numero=longitud_numero,
                separador=separador if separador is not None else "",
                es_activo=es_activo,
            )
        )
        if cliente_id is not None:
            stmt = stmt.where(CfgCodigoSecuenciaTable.c.cliente_id == cliente_id)

        if session is not None:
            await session.execute(stmt)
            fetch = select(CfgCodigoSecuenciaTable).where(
                CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id
            )
            result = await session.execute(fetch)
            return self._row_to_dict(result)

        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        return await self.find_by_id(secuencia_id, client_id=cliente_id)
