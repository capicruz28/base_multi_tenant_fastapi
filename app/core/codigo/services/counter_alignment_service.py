"""CounterAlignmentService — high-water mark."""

from __future__ import annotations

from app.core.codigo.enums import StoreType
from app.core.codigo.parser.code_parser import CodeParser
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.codigo.stores.cfg_sequence_store import CfgSequenceStore
from sqlalchemy.ext.asyncio import AsyncSession


class CounterAlignmentService:
    @staticmethod
    async def maybe_align(
        session: AsyncSession,
        defn: SequenceDefinition,
        scope_key: ScopeKey,
        manual_code: str,
        *,
        prefijo: str | None = None,
    ) -> int | None:
        if not defn.align_on_manual or defn.store_type != StoreType.CFG:
            return None

        parse_result = CodeParser.parse(defn, manual_code, prefijo=prefijo)
        if not parse_result.parseable or parse_result.numeric_part is None:
            return None

        row = await CfgSequenceStore.get_by_scope(session, scope_key)
        current = row.ultimo_numero if row else 0
        if parse_result.numeric_part <= current:
            return current

        return await CfgSequenceStore.align_counter(
            session,
            scope_key,
            defn,
            parse_result.numeric_part,
        )
