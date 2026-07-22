"""PolicyResolver — modo de operación según política F15A."""

from __future__ import annotations

from app.core.codigo.enums import CodePolicy, GenerationOperation, PolicyMode
from app.core.codigo.generation_context import GenerationContext


class PolicyResolver:
    @staticmethod
    def resolve(generation_policy: CodePolicy, context: GenerationContext) -> PolicyMode:
        manual = (context.manual_code or "").strip()
        if generation_policy == CodePolicy.AUTO_REQUIRED:
            if manual and context.operation != GenerationOperation.IMPORT:
                return PolicyMode.REJECT_MANUAL
            if context.operation == GenerationOperation.IMPORT:
                return PolicyMode.IMPORT_HISTORICAL
            return PolicyMode.AUTO_GENERATE

        if generation_policy == CodePolicy.AUTO_DEFAULT:
            if context.operation == GenerationOperation.IMPORT and manual:
                return PolicyMode.IMPORT_HISTORICAL
            if manual:
                return PolicyMode.ACCEPT_MANUAL
            return PolicyMode.AUTO_GENERATE

        if generation_policy == CodePolicy.MANUAL_ONLY:
            if manual:
                return PolicyMode.ACCEPT_MANUAL
            return PolicyMode.REJECT_MANUAL

        raise ValueError(f"Política no soportada en cfg: {generation_policy}")
