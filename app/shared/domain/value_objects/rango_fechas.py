# app/shared/domain/value_objects/rango_fechas.py
"""
RangoFechas: Value Object para representar rangos de fechas.

✅ SHARED KERNEL: Compartido entre módulos (Planillas, Contabilidad, Reportes, etc.)
"""

from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RangoFechas:
    """
    Value Object para representar un rango de fechas.
    
    Inmutable y compartido entre módulos.
    """
    
    def __init__(self, fecha_inicio: date, fecha_fin: date):
        """
        Inicializa un rango de fechas.
        
        Args:
            fecha_inicio: Fecha de inicio del rango
            fecha_fin: Fecha de fin del rango
        
        Raises:
            ValueError: Si fecha_inicio > fecha_fin
        """
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        if isinstance(fecha_fin, datetime):
            fecha_fin = fecha_fin.date()
        
        self._fecha_inicio = fecha_inicio
        self._fecha_fin = fecha_fin
        
        self._validate()
    
    def _validate(self):
        """Valida que el rango sea válido."""
        if self._fecha_inicio > self._fecha_fin:
            raise ValueError(
                f"La fecha de inicio ({self._fecha_inicio}) no puede ser mayor "
                f"que la fecha de fin ({self._fecha_fin})"
            )
    
    @property
    def fecha_inicio(self) -> date:
        """Fecha de inicio."""
        return self._fecha_inicio
    
    @property
    def fecha_fin(self) -> date:
        """Fecha de fin."""
        return self._fecha_fin
    
    def contiene_fecha(self, fecha: date) -> bool:
        """
        Verifica si una fecha está dentro del rango.
        
        Args:
            fecha: Fecha a verificar
        
        Returns:
            True si la fecha está en el rango, False en caso contrario
        """
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        return self._fecha_inicio <= fecha <= self._fecha_fin
    
    def contiene_rango(self, otro_rango: 'RangoFechas') -> bool:
        """
        Verifica si otro rango está completamente contenido en este.
        
        Args:
            otro_rango: Rango a verificar
        
        Returns:
            True si el otro rango está contenido, False en caso contrario
        """
        return (
            self._fecha_inicio <= otro_rango._fecha_inicio and
            self._fecha_fin >= otro_rango._fecha_fin
        )
    
    def se_superpone_con(self, otro_rango: 'RangoFechas') -> bool:
        """
        Verifica si este rango se superpone con otro.
        
        Args:
            otro_rango: Rango a verificar
        
        Returns:
            True si hay superposición, False en caso contrario
        """
        return (
            self._fecha_inicio <= otro_rango._fecha_fin and
            self._fecha_fin >= otro_rango._fecha_inicio
        )
    
    def dias_duracion(self) -> int:
        """
        Calcula la duración del rango en días.
        
        Returns:
            Número de días en el rango (inclusive)
        """
        delta = self._fecha_fin - self._fecha_inicio
        return delta.days + 1  # +1 para incluir ambos extremos
    
    def __eq__(self, other):
        """Compara dos rangos de fechas."""
        if not isinstance(other, RangoFechas):
            return False
        return (
            self._fecha_inicio == other._fecha_inicio and
            self._fecha_fin == other._fecha_fin
        )
    
    def __hash__(self):
        """Hash basado en fechas."""
        return hash((self._fecha_inicio, self._fecha_fin))
    
    def __str__(self):
        return f"{self._fecha_inicio} - {self._fecha_fin}"
    
    def __repr__(self):
        return f"RangoFechas(fecha_inicio={self._fecha_inicio}, fecha_fin={self._fecha_fin})"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RangoFechas':
        """Crea un rango desde un diccionario."""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.fromisoformat(fecha_inicio).date()
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.fromisoformat(fecha_fin).date()
        
        return cls(fecha_inicio, fecha_fin)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "fecha_inicio": self._fecha_inicio.isoformat(),
            "fecha_fin": self._fecha_fin.isoformat(),
            "dias_duracion": self.dias_duracion()
        }

