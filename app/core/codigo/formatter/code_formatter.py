"""CodeFormatter — ensambla valor final según perfil."""

from __future__ import annotations

from app.core.codigo.enums import FormatterProfile, NormalizeCase
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.exceptions import ConflictError, ValidationError


class CodeFormatter:
    @staticmethod
    def format(
        defn: SequenceDefinition,
        numero: int,
        *,
        prefijo: str | None = None,
        separador: str | None = None,
        padding: int | None = None,
    ) -> str:
        prefix = defn.default_prefix if prefijo is None else prefijo
        sep = defn.default_separator if separador is None else (separador or "")
        pad = defn.default_padding if padding is None else padding

        if defn.formatter_profile == FormatterProfile.FMT_FISCAL_8:
            code = f"{numero:08d}"
        elif defn.formatter_profile == FormatterProfile.FMT_NUMERIC_ONLY:
            code = f"{numero:0{pad}d}" if pad > 0 else str(numero)
        else:
            numeric = f"{numero:0{pad}d}" if pad > 0 else str(numero)
            code = f"{prefix}{sep}{numeric}" if prefix else numeric

        if defn.normalize_case == NormalizeCase.UPPER:
            code = code.upper()

        if len(code) > defn.max_output_length:
            raise ConflictError(
                detail="Secuencia agotada: el código excede la longitud máxima permitida.",
                internal_code="CODE_LENGTH_EXCEEDED",
            )
        if not code:
            raise ValidationError(
                detail="No se pudo formatear el código.",
                internal_code="FORMAT_EMPTY",
            )
        return code
