"""Definición de una entrada del SequenceCatalog (F16A `18`)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.codigo.enums import (
    AlignmentMode,
    CodePolicy,
    FormatterProfile,
    NormalizeCase,
    ParserProfile,
    ScopeType,
    SequenceFamily,
    StoreType,
    ValidatorProfile,
)


@dataclass(frozen=True, slots=True)
class SequenceDefinition:
    sequence_key: str
    table_name: str
    code_column: str
    modulo_codigo: str
    catalog_version: str
    policy: CodePolicy
    sequence_family: SequenceFamily
    scope_type: ScopeType
    store_type: StoreType
    formatter_profile: FormatterProfile
    parser_profile: ParserProfile
    validator_profile: ValidatorProfile
    supports_preview: bool
    allow_manual: bool
    alignment_mode: AlignmentMode
    supports_import: bool
    default_prefix: str
    default_separator: str
    default_padding: int
    numero_inicial: int
    max_output_length: int
    normalize_case: NormalizeCase
    parser_partial: bool = False
    documentation: str = ""

    @property
    def align_on_manual(self) -> bool:
        return self.alignment_mode in (AlignmentMode.YES, AlignmentMode.PARTIAL)

    @property
    def supports_high_water(self) -> bool:
        return self.alignment_mode in (
            AlignmentMode.YES,
            AlignmentMode.PARTIAL,
            AlignmentMode.IMPORT,
        )

    @property
    def consumes_counter_on_allocate(self) -> bool:
        return self.policy == CodePolicy.AUTO_REQUIRED
