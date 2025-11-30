# app/shared/domain/value_objects/monto.py
"""
Monto: Value Object para representar montos monetarios.

✅ SHARED KERNEL: Compartido entre módulos (Planillas, Contabilidad, Ventas, etc.)
"""

from typing import Optional, TYPE_CHECKING
from decimal import Decimal
import logging

if TYPE_CHECKING:
    from app.shared.domain.value_objects.moneda import Moneda

logger = logging.getLogger(__name__)


class Monto:
    """
    Value Object para representar un monto monetario.
    
    Inmutable y compartido entre módulos.
    Usa Decimal para precisión en cálculos financieros.
    """
    
    def __init__(self, valor: Decimal, moneda: 'Moneda'):
        """
        Inicializa un monto.
        
        Args:
            valor: Valor del monto (usar Decimal para precisión)
            moneda: Moneda del monto
        
        Raises:
            ValueError: Si el valor es negativo
        """
        if isinstance(valor, (int, float)):
            valor = Decimal(str(valor))
        
        self._valor = valor
        self._moneda = moneda
        
        self._validate()
    
    def _validate(self):
        """Valida que el monto sea válido."""
        if self._valor < 0:
            raise ValueError("El monto no puede ser negativo")
    
    @property
    def valor(self) -> Decimal:
        """Valor del monto."""
        return self._valor
    
    @property
    def moneda(self) -> 'Moneda':
        """Moneda del monto."""
        return self._moneda
    
    def es_cero(self) -> bool:
        """Verifica si el monto es cero."""
        return self._valor == Decimal('0')
    
    def es_positivo(self) -> bool:
        """Verifica si el monto es positivo."""
        return self._valor > Decimal('0')
    
    def sumar(self, otro: 'Monto') -> 'Monto':
        """
        Suma otro monto a este.
        
        Args:
            otro: Monto a sumar
        
        Returns:
            Nuevo monto con la suma
        
        Raises:
            ValueError: Si las monedas no coinciden
        """
        if self._moneda != otro._moneda:
            raise ValueError(
                f"No se pueden sumar montos de diferentes monedas: "
                f"{self._moneda.codigo} y {otro._moneda.codigo}"
            )
        return Monto(self._valor + otro._valor, self._moneda)
    
    def restar(self, otro: 'Monto') -> 'Monto':
        """
        Resta otro monto de este.
        
        Args:
            otro: Monto a restar
        
        Returns:
            Nuevo monto con la resta
        
        Raises:
            ValueError: Si las monedas no coinciden o si el resultado es negativo
        """
        if self._moneda != otro._moneda:
            raise ValueError(
                f"No se pueden restar montos de diferentes monedas: "
                f"{self._moneda.codigo} y {otro._moneda.codigo}"
            )
        resultado = self._valor - otro._valor
        if resultado < 0:
            raise ValueError("El resultado de la resta no puede ser negativo")
        return Monto(resultado, self._moneda)
    
    def multiplicar(self, factor: Decimal) -> 'Monto':
        """
        Multiplica el monto por un factor.
        
        Args:
            factor: Factor de multiplicación
        
        Returns:
            Nuevo monto multiplicado
        """
        return Monto(self._valor * factor, self._moneda)
    
    def dividir(self, divisor: Decimal) -> 'Monto':
        """
        Divide el monto por un divisor.
        
        Args:
            divisor: Divisor
        
        Returns:
            Nuevo monto dividido
        
        Raises:
            ValueError: Si el divisor es cero
        """
        if divisor == 0:
            raise ValueError("No se puede dividir por cero")
        return Monto(self._valor / divisor, self._moneda)
    
    def formatear(self, incluir_simbolo: bool = True) -> str:
        """
        Formatea el monto como string.
        
        Args:
            incluir_simbolo: Si incluir el símbolo de la moneda
        
        Returns:
            String formateado (ej: "S/ 1,234.56" o "1234.56")
        """
        # Formatear valor con 2 decimales
        valor_str = f"{self._valor:,.2f}"
        
        if incluir_simbolo:
            return f"{self._moneda.simbolo} {valor_str}"
        else:
            return valor_str
    
    def __eq__(self, other):
        """Compara dos montos."""
        if not isinstance(other, Monto):
            return False
        return self._valor == other._valor and self._moneda == other._moneda
    
    def __lt__(self, other):
        """Compara si este monto es menor que otro."""
        if not isinstance(other, Monto):
            return NotImplemented
        if self._moneda != other._moneda:
            raise ValueError("No se pueden comparar montos de diferentes monedas")
        return self._valor < other._valor
    
    def __le__(self, other):
        """Compara si este monto es menor o igual que otro."""
        if not isinstance(other, Monto):
            return NotImplemented
        if self._moneda != other._moneda:
            raise ValueError("No se pueden comparar montos de diferentes monedas")
        return self._valor <= other._valor
    
    def __gt__(self, other):
        """Compara si este monto es mayor que otro."""
        if not isinstance(other, Monto):
            return NotImplemented
        if self._moneda != other._moneda:
            raise ValueError("No se pueden comparar montos de diferentes monedas")
        return self._valor > other._valor
    
    def __ge__(self, other):
        """Compara si este monto es mayor o igual que otro."""
        if not isinstance(other, Monto):
            return NotImplemented
        if self._moneda != other._moneda:
            raise ValueError("No se pueden comparar montos de diferentes monedas")
        return self._valor >= other._valor
    
    def __hash__(self):
        """Hash basado en valor y moneda."""
        return hash((self._valor, self._moneda))
    
    def __str__(self):
        return self.formatear()
    
    def __repr__(self):
        return f"Monto(valor={self._valor}, moneda={self._moneda.codigo})"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Monto':
        """Crea un monto desde un diccionario."""
        valor = Decimal(str(data.get('valor', 0)))
        moneda_codigo = data.get('moneda', 'PEN')
        moneda = Moneda.from_code(moneda_codigo)
        return cls(valor, moneda)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "valor": float(self._valor),
            "moneda": self._moneda.codigo,
            "moneda_simbolo": self._moneda.simbolo,
            "formateado": self.formatear()
        }

