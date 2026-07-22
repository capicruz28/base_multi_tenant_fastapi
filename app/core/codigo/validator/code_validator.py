"""CodeValidator — formato, longitud y charset."""

from __future__ import annotations

import re

from app.core.codigo.enums import NormalizeCase, ValidatorProfile
from app.core.codigo.sequence_definition import SequenceDefinition
from app.core.exceptions import ValidationError

_MASTER_PATTERN = re.compile(r"^[A-Z0-9_-]+$")
_DOCUMENT_PATTERN = re.compile(r"^[A-Z0-9_-]+$")
_UBICACION_PATTERN = re.compile(r"^[A-Z0-9_-]+$")
_FISCAL_PATTERN = re.compile(r"^\d+$")


class CodeValidator:
    @staticmethod
    def validate(
        defn: SequenceDefinition,
        code: str,
        *,
        prefijo: str | None = None,
    ) -> None:
        if code is None or not str(code).strip():
            raise ValidationError(
                detail="El código no puede estar vacío.",
                internal_code="CODE_EMPTY",
            )

        value = code.strip()
        if defn.normalize_case == NormalizeCase.UPPER:
            value = value.upper()

        if len(value) > defn.max_output_length:
            raise ValidationError(
                detail=f"El código excede la longitud máxima ({defn.max_output_length}).",
                internal_code="CODE_TOO_LONG",
            )

        profile = defn.validator_profile
        if profile == ValidatorProfile.VAL_FISCAL_NUM:
            if not _FISCAL_PATTERN.match(value):
                raise ValidationError(
                    detail="El número fiscal debe contener solo dígitos.",
                    internal_code="FISCAL_NUM_INVALID",
                )
            return

        pattern = _MASTER_PATTERN
        if profile == ValidatorProfile.VAL_UBICACION:
            pattern = _UBICACION_PATTERN
        elif profile == ValidatorProfile.VAL_DOCUMENT:
            pattern = _DOCUMENT_PATTERN

        if not pattern.match(value):
            raise ValidationError(
                detail="El código contiene caracteres no permitidos.",
                internal_code="CODE_CHARSET_INVALID",
            )

        prefix = defn.default_prefix if prefijo is None else prefijo
        if prefix and defn.allow_manual and profile != ValidatorProfile.VAL_UBICACION:
            if not value.upper().startswith(prefix.upper()) and value.isdigit() is False:
                pass
