"""Enumeraciones oficiales del motor de generación de códigos (F16/F16A)."""

from __future__ import annotations

from enum import Enum


class CodePolicy(str, Enum):
    AUTO_REQUIRED = "AUTO_REQUIRED"
    AUTO_DEFAULT = "AUTO_DEFAULT"
    MANUAL_ONLY = "MANUAL_ONLY"
    EXTERNAL = "EXTERNAL"


class ScopeType(str, Enum):
    TENANT = "TENANT"
    EMPRESA = "EMPRESA"
    ALMACEN = "ALMACEN"
    PUNTO_VENTA = "PUNTO_VENTA"
    SERIE_FISCAL = "SERIE_FISCAL"


class SequenceFamily(str, Enum):
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"


class StoreType(str, Enum):
    CFG = "CFG"
    FISCAL = "FISCAL"


class FormatterProfile(str, Enum):
    FMT_STANDARD = "FMT_STANDARD"
    FMT_FISCAL_8 = "FMT_FISCAL_8"
    FMT_NUMERIC_ONLY = "FMT_NUMERIC_ONLY"


class ParserProfile(str, Enum):
    PAR_PREFIX_NUM = "PAR_PREFIX_NUM"
    PAR_NUM_ONLY = "PAR_NUM_ONLY"
    PAR_NONE = "PAR_NONE"


class ValidatorProfile(str, Enum):
    VAL_MASTER = "VAL_MASTER"
    VAL_DOCUMENT = "VAL_DOCUMENT"
    VAL_FISCAL_NUM = "VAL_FISCAL_NUM"
    VAL_UBICACION = "VAL_UBICACION"


class AlignmentMode(str, Enum):
    YES = "yes"
    NO = "no"
    PARTIAL = "partial"
    IMPORT = "import"


class GenerationOperation(str, Enum):
    CREATE = "create"
    IMPORT = "import"
    PREVIEW = "preview"
    ALIGN = "align"


class PolicyMode(str, Enum):
    AUTO_GENERATE = "AUTO_GENERATE"
    ACCEPT_MANUAL = "ACCEPT_MANUAL"
    REJECT_MANUAL = "REJECT_MANUAL"
    IMPORT_HISTORICAL = "IMPORT_HISTORICAL"


class NormalizeCase(str, Enum):
    UPPER = "UPPER"
    AS_IS = "AS_IS"
