"""
Repositorio para cfg_codigo_secuencia (secuencias de códigos por tenant/empresa).

RD-06-E02 / E5-09 §8 + F17C (ADJ-03 — blindaje de escritura):
- Lecturas (``get_*``): Path A ``execute_*`` con ``DatabaseConnection.ADMIN`` (control_plane)
  cuando no se pasa ``session``; o Path B con ``session`` externa (UoW del tenant store).
- Escrituras (``insert_secuencia`` / ``update_*``): **requieren siempre ``session`` explícita**.
  Prohibida la ruta ADMIN sin sesión para escritura: en instalaciones Dedicated escribiría
  accidentalmente en el Control Plane en vez de la BD del tenant. El runtime del motor
  escribe vía ``CfgSequenceStore`` (session-driven), nunca por este repositorio.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codigo.enums import CodePolicy, ScopeType
from app.core.codigo.scope_fingerprint import compute_scope_fingerprint
from app.core.exceptions import ServiceError
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
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

    @staticmethod
    def _assert_write_session(session: Optional[AsyncSession], operation: str) -> None:
        """ADJ-03 — toda escritura exige sesión UoW explícita.

        Sin sesión, la ruta caería a ``DatabaseConnection.ADMIN`` (Control Plane), lo que
        en Dedicated escribiría en la BD equivocada. Se bloquea de forma explícita.
        """
        if session is None:
            raise ServiceError(
                status_code=500,
                detail=(
                    "Escritura en cfg_codigo_secuencia requiere una sesión UoW explícita "
                    f"({operation}). La ruta ADMIN sin sesión está prohibida para no "
                    "escribir en el Control Plane en instalaciones Dedicated."
                ),
                internal_code="CFG_SECUENCIA_WRITE_REQUIRES_SESSION",
            )

    @staticmethod
    def _fingerprint(
        scope_type: ScopeType,
        *,
        empresa_id: Optional[UUID] = None,
        almacen_id: Optional[UUID] = None,
        punto_venta_id: Optional[UUID] = None,
    ) -> str:
        return compute_scope_fingerprint(
            scope_type,
            empresa_id=empresa_id,
            almacen_id=almacen_id,
            punto_venta_id=punto_venta_id,
        )

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
            .order_by(CfgCodigoSecuenciaTable.c.sequence_key)
        )
        if session is not None:
            result = await session.execute(stmt)
            return self._rows_to_dicts(result)
        return await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )

    async def get_by_sequence_key(
        self,
        cliente_id: UUID,
        sequence_key: str,
        scope_type: ScopeType,
        *,
        empresa_id: Optional[UUID] = None,
        almacen_id: Optional[UUID] = None,
        punto_venta_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        fingerprint = self._fingerprint(
            scope_type,
            empresa_id=empresa_id,
            almacen_id=almacen_id,
            punto_venta_id=punto_venta_id,
        )
        stmt = select(CfgCodigoSecuenciaTable).where(
            and_(
                CfgCodigoSecuenciaTable.c.cliente_id == cliente_id,
                CfgCodigoSecuenciaTable.c.sequence_key == sequence_key,
                CfgCodigoSecuenciaTable.c.scope_fingerprint == fingerprint,
            )
        )
        if session is not None:
            result = await session.execute(stmt)
            return self._row_to_dict(result)
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        return rows[0] if rows else None

    async def get_by_entidad(
        self,
        cliente_id: UUID,
        empresa_id: Optional[UUID],
        entidad: str,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """Compatibilidad legacy: entidad → sequence_key, scope EMPRESA o TENANT."""
        scope = ScopeType.TENANT if entidad == "org_empresa" else ScopeType.EMPRESA
        eff_empresa = None if scope == ScopeType.TENANT else empresa_id
        return await self.get_by_sequence_key(
            cliente_id,
            entidad,
            scope,
            empresa_id=eff_empresa,
            session=session,
        )

    async def insert_secuencia(
        self,
        cliente_id: UUID,
        sequence_key: str,
        scope_type: ScopeType,
        prefijo: str,
        longitud_numero: int,
        separador: str,
        *,
        generation_policy: CodePolicy,
        empresa_id: Optional[UUID] = None,
        almacen_id: Optional[UUID] = None,
        punto_venta_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
        ultimo_numero: int = 0,
        numero_inicial: int = 1,
    ) -> Dict[str, Any]:
        """Inserta secuencia idempotente por (cliente_id, sequence_key, scope_fingerprint)."""
        self._assert_write_session(session, "insert_secuencia")
        existing = await self.get_by_sequence_key(
            cliente_id,
            sequence_key,
            scope_type,
            empresa_id=empresa_id,
            almacen_id=almacen_id,
            punto_venta_id=punto_venta_id,
            session=session,
        )
        if existing:
            return existing

        eff_empresa = empresa_id
        eff_almacen = almacen_id
        eff_pv = punto_venta_id
        if scope_type == ScopeType.TENANT:
            eff_empresa = None
            eff_almacen = None
            eff_pv = None
        elif scope_type == ScopeType.EMPRESA:
            eff_almacen = None
            eff_pv = None
        elif scope_type == ScopeType.ALMACEN:
            eff_pv = None
        elif scope_type == ScopeType.PUNTO_VENTA:
            eff_almacen = None

        fingerprint = self._fingerprint(
            scope_type,
            empresa_id=eff_empresa,
            almacen_id=eff_almacen,
            punto_venta_id=eff_pv,
        )
        values = {
            "secuencia_id": uuid4(),
            "cliente_id": cliente_id,
            "sequence_key": sequence_key,
            "scope_type": scope_type.value,
            "scope_fingerprint": fingerprint,
            "empresa_id": eff_empresa,
            "almacen_id": eff_almacen,
            "punto_venta_id": eff_pv,
            "prefijo": prefijo,
            "longitud_numero": longitud_numero,
            "ultimo_numero": ultimo_numero,
            "numero_inicial": numero_inicial,
            "separador": separador if separador is not None else "",
            "es_activo": True,
            "generation_policy": generation_policy.value,
        }
        stmt = insert(CfgCodigoSecuenciaTable).values(**values)

        await session.execute(stmt)
        inserted = await self.get_by_sequence_key(
            cliente_id,
            sequence_key,
            scope_type,
            empresa_id=eff_empresa,
            almacen_id=eff_almacen,
            punto_venta_id=eff_pv,
            session=session,
        )
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
        self._assert_write_session(session, "update_ultimo_numero")
        stmt = (
            update(CfgCodigoSecuenciaTable)
            .where(CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id)
            .values(ultimo_numero=nuevo_numero)
        )
        if cliente_id is not None:
            stmt = stmt.where(CfgCodigoSecuenciaTable.c.cliente_id == cliente_id)

        await session.execute(stmt)
        fetch = select(CfgCodigoSecuenciaTable).where(
            CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id
        )
        result = await session.execute(fetch)
        return self._row_to_dict(result)

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
        self._assert_write_session(session, "update_secuencia")
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

        await session.execute(stmt)
        fetch = select(CfgCodigoSecuenciaTable).where(
            CfgCodigoSecuenciaTable.c.secuencia_id == secuencia_id
        )
        result = await session.execute(fetch)
        return self._row_to_dict(result)
