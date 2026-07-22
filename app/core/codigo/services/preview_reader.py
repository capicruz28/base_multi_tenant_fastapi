"""PreviewReader — estimación sin consumo."""

from __future__ import annotations

from app.core.codigo.formatter.code_formatter import CodeFormatter
from app.core.codigo.generation_result import PreviewResult
from app.core.codigo.scope_key import ScopeKey
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.codigo.stores.cfg_sequence_store import CfgSequenceStore
from app.core.exceptions import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class PreviewReader:
    @staticmethod
    async def preview(
        session: AsyncSession,
        defn: SequenceDefinition,
        scope_key: ScopeKey,
    ) -> PreviewResult:
        if not defn.supports_preview:
            raise ValidationError(
                detail="Preview no permitido para esta secuencia.",
                internal_code="PREVIEW_NOT_ALLOWED",
            )
        row = await CfgSequenceStore.read_for_preview(session, scope_key, defn)
        next_num = max(row.ultimo_numero, row.numero_inicial - 1) + 1
        code = CodeFormatter.format(
            defn,
            next_num,
            prefijo=row.prefijo,
            separador=row.separador,
            padding=row.longitud_numero,
        )
        return PreviewResult(code=code, sequence_key=defn.sequence_key)
