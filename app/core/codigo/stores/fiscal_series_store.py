"""FiscalSeriesStore — contador en invbill_serie_comprobante."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.database.tables_erp import InvbillSerieComprobanteTable


@dataclass(frozen=True, slots=True)
class FiscalSeriesRow:
    serie_id: UUID
    cliente_id: UUID
    empresa_id: UUID
    numero_actual: int
    numero_inicial: int
    numero_final: int | None
    es_activo: bool

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> FiscalSeriesRow:
        return cls(
            serie_id=UUID(str(row["serie_id"])),
            cliente_id=UUID(str(row["cliente_id"])),
            empresa_id=UUID(str(row["empresa_id"])),
            numero_actual=int(row.get("numero_actual") or 0),
            numero_inicial=int(row.get("numero_inicial") or 1),
            numero_final=int(row["numero_final"]) if row.get("numero_final") is not None else None,
            es_activo=bool(row.get("es_activo", True)),
        )


def _row_to_dict(result) -> dict[str, Any] | None:
    row = result.fetchone()
    if not row:
        return None
    return dict(zip(result.keys(), row))


class FiscalSeriesStore:
    @classmethod
    async def get_by_serie_id(
        cls,
        session: AsyncSession,
        *,
        client_id: UUID,
        serie_id: UUID,
        empresa_id: UUID | None = None,
    ) -> FiscalSeriesRow | None:
        conds = [
            InvbillSerieComprobanteTable.c.cliente_id == client_id,
            InvbillSerieComprobanteTable.c.serie_id == serie_id,
        ]
        if empresa_id is not None:
            conds.append(InvbillSerieComprobanteTable.c.empresa_id == empresa_id)
        stmt = select(InvbillSerieComprobanteTable).where(and_(*conds))
        result = await session.execute(stmt)
        row = _row_to_dict(result)
        return FiscalSeriesRow.from_dict(row) if row else None

    @classmethod
    async def increment_and_get(
        cls,
        session: AsyncSession,
        *,
        client_id: UUID,
        serie_id: UUID,
        empresa_id: UUID,
    ) -> tuple[FiscalSeriesRow, int]:
        row = await cls.get_by_serie_id(
            session, client_id=client_id, serie_id=serie_id, empresa_id=empresa_id
        )
        if not row:
            raise NotFoundError(detail="Serie fiscal no encontrada.")
        if not row.es_activo:
            raise ConflictError(
                detail="La serie fiscal está inactiva.",
                internal_code="FISCAL_SERIE_INACTIVE",
            )
        nuevo = max(row.numero_actual, row.numero_inicial - 1) + 1
        if row.numero_final is not None and nuevo > row.numero_final:
            raise ConflictError(
                detail="Secuencia fiscal agotada.",
                internal_code="FISCAL_SEQUENCE_EXHAUSTED",
            )
        stmt = (
            update(InvbillSerieComprobanteTable)
            .where(InvbillSerieComprobanteTable.c.serie_id == serie_id)
            .values(numero_actual=nuevo)
        )
        await session.execute(stmt)
        updated = await cls.get_by_serie_id(
            session, client_id=client_id, serie_id=serie_id, empresa_id=empresa_id
        )
        if not updated:
            raise NotFoundError(detail="Serie fiscal no encontrada tras incremento.")
        return updated, nuevo
