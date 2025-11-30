# app/shared/domain/value_objects/__init__.py
"""
Value Objects compartidos entre módulos.

✅ SHARED KERNEL: Componentes compartidos para evitar duplicación
"""

from app.shared.domain.value_objects.moneda import Moneda, CodigoMoneda
from app.shared.domain.value_objects.direccion import Direccion
from app.shared.domain.value_objects.rango_fechas import RangoFechas
from app.shared.domain.value_objects.monto import Monto

__all__ = [
    'Moneda',
    'CodigoMoneda',
    'Direccion',
    'RangoFechas',
    'Monto'
]

