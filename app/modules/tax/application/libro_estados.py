"""Estados y transiciones válidas para tax_libro_electronico (solo constantes y conjuntos)."""

BORRADOR = "borrador"
GENERADO = "generado"
ENVIADO = "enviado"
ACEPTADO = "aceptado"
RECHAZADO = "rechazado"
ANULADO = "anulado"

# Desde estos estados se puede anular (no aceptado SUNAT ni ya anulado).
ESTADOS_ANULABLES = frozenset({BORRADOR, GENERADO, ENVIADO, RECHAZADO})
