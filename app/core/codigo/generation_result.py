"""Resultados del motor de generación de códigos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllocationResult:
    code: str
    sequence_key: str
    consumed: bool
    ultimo_numero: int | None = None


@dataclass(frozen=True, slots=True)
class PreviewResult:
    code: str
    sequence_key: str
    disclaimer: str = (
        "Estimación no vinculante. El código definitivo se asigna al crear el registro."
    )


@dataclass(frozen=True, slots=True)
class ParseResult:
    parseable: bool
    numeric_part: int | None = None
