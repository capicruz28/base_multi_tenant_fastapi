"""CodeParser — extracción de parte numérica para high-water."""

from __future__ import annotations

import re

from app.core.codigo.enums import ParserProfile
from app.core.codigo.generation_result import ParseResult
from app.core.codigo.sequence_definition import SequenceDefinition

_DIGITS_TAIL = re.compile(r"(\d+)\s*$")


class CodeParser:
    @staticmethod
    def parse(
        defn: SequenceDefinition,
        code: str,
        *,
        prefijo: str | None = None,
    ) -> ParseResult:
        if not code or not code.strip():
            return ParseResult(parseable=False)

        profile = defn.parser_profile
        if profile == ParserProfile.PAR_NONE:
            return ParseResult(parseable=False)

        normalized = code.strip()
        prefix = defn.default_prefix if prefijo is None else prefijo

        if profile == ParserProfile.PAR_NUM_ONLY:
            if normalized.isdigit():
                return ParseResult(parseable=True, numeric_part=int(normalized))
            return ParseResult(parseable=False)

        if profile == ParserProfile.PAR_PREFIX_NUM:
            if defn.parser_partial:
                match = _DIGITS_TAIL.search(normalized)
                if match:
                    return ParseResult(parseable=True, numeric_part=int(match.group(1)))
                return ParseResult(parseable=False)

            if prefix:
                upper_code = normalized.upper()
                upper_prefix = prefix.upper()
                if not upper_code.startswith(upper_prefix):
                    return ParseResult(parseable=False)
                suffix = normalized[len(prefix) :]
                if defn.default_separator and suffix.startswith(defn.default_separator):
                    suffix = suffix[len(defn.default_separator) :]
                match = _DIGITS_TAIL.search(suffix)
                if match and suffix.strip() == match.group(1):
                    return ParseResult(parseable=True, numeric_part=int(match.group(1)))
                return ParseResult(parseable=False)

            if normalized.isdigit():
                return ParseResult(parseable=True, numeric_part=int(normalized))
            match = _DIGITS_TAIL.search(normalized)
            if match and normalized == match.group(1):
                return ParseResult(parseable=True, numeric_part=int(match.group(1)))
            return ParseResult(parseable=False)

        return ParseResult(parseable=False)
