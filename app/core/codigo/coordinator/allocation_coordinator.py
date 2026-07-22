"""AllocationCoordinator — consumo transaccional de contador."""

from __future__ import annotations

from app.core.codigo.enums import StoreType
from app.core.codigo.formatter.code_formatter import CodeFormatter
from app.core.codigo.generation_result import AllocationResult
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.codigo.stores.cfg_sequence_store import CfgSequenceStore
from app.core.codigo.stores.fiscal_series_store import FiscalSeriesStore
from sqlalchemy.ext.asyncio import AsyncSession


class AllocationCoordinator:
    @staticmethod
    async def allocate_next(
        session: AsyncSession,
        defn: SequenceDefinition,
        scope_key: ScopeKey,
    ) -> AllocationResult:
        if defn.store_type == StoreType.FISCAL:
            if scope_key.serie_id is None or scope_key.empresa_id is None:
                raise ValueError("serie_id y empresa_id requeridos para fiscal")
            _, numero = await FiscalSeriesStore.increment_and_get(
                session,
                client_id=scope_key.client_id,
                serie_id=scope_key.serie_id,
                empresa_id=scope_key.empresa_id,
            )
            code = CodeFormatter.format(defn, numero)
            return AllocationResult(
                code=code,
                sequence_key=defn.sequence_key,
                consumed=True,
                ultimo_numero=numero,
            )

        row, numero = await CfgSequenceStore.increment_and_get(session, scope_key, defn)
        prefijo = "" if defn.default_prefix == "" else row.prefijo
        code = CodeFormatter.format(
            defn,
            numero,
            prefijo=prefijo,
            separador=row.separador,
            padding=row.longitud_numero,
        )
        return AllocationResult(
            code=code,
            sequence_key=defn.sequence_key,
            consumed=True,
            ultimo_numero=numero,
        )

    @staticmethod
    def accept_manual(defn: SequenceDefinition, manual_code: str) -> AllocationResult:
        return AllocationResult(
            code=manual_code.strip(),
            sequence_key=defn.sequence_key,
            consumed=False,
            ultimo_numero=None,
        )
