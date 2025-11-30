# app/shared/domain/value_objects/moneda.py
"""
Moneda: Value Object para representar monedas.

✅ SHARED KERNEL: Compartido entre módulos (Planillas, Contabilidad, Logística, etc.)
"""

from typing import Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CodigoMoneda(str, Enum):
    """Códigos de moneda ISO 4217."""
    USD = "USD"  # Dólar estadounidense
    PEN = "PEN"  # Sol peruano
    EUR = "EUR"  # Euro
    MXN = "MXN"  # Peso mexicano
    ARS = "ARS"  # Peso argentino
    CLP = "CLP"  # Peso chileno
    COP = "COP"  # Peso colombiano
    BRL = "BRL"  # Real brasileño


class Moneda:
    """
    Value Object para representar una moneda.
    
    Inmutable y compartido entre módulos.
    """
    
    def __init__(self, codigo: str, simbolo: Optional[str] = None, nombre: Optional[str] = None):
        """
        Inicializa una moneda.
        
        Args:
            codigo: Código ISO 4217 (ej: "USD", "PEN")
            simbolo: Símbolo de la moneda (ej: "$", "S/")
            nombre: Nombre completo (ej: "Dólar estadounidense")
        """
        self._codigo = codigo.upper()
        self._simbolo = simbolo or self._get_default_symbol()
        self._nombre = nombre or self._get_default_name()
        
        self._validate()
    
    def _validate(self):
        """Valida que el código de moneda sea válido."""
        try:
            CodigoMoneda(self._codigo)
        except ValueError:
            raise ValueError(f"Código de moneda inválido: {self._codigo}")
    
    def _get_default_symbol(self) -> str:
        """Obtiene el símbolo por defecto según el código."""
        symbols = {
            "USD": "$",
            "PEN": "S/",
            "EUR": "€",
            "MXN": "$",
            "ARS": "$",
            "CLP": "$",
            "COP": "$",
            "BRL": "R$"
        }
        return symbols.get(self._codigo, "")
    
    def _get_default_name(self) -> str:
        """Obtiene el nombre por defecto según el código."""
        names = {
            "USD": "Dólar estadounidense",
            "PEN": "Sol peruano",
            "EUR": "Euro",
            "MXN": "Peso mexicano",
            "ARS": "Peso argentino",
            "CLP": "Peso chileno",
            "COP": "Peso colombiano",
            "BRL": "Real brasileño"
        }
        return names.get(self._codigo, self._codigo)
    
    @property
    def codigo(self) -> str:
        """Código ISO 4217 de la moneda."""
        return self._codigo
    
    @property
    def simbolo(self) -> str:
        """Símbolo de la moneda."""
        return self._simbolo
    
    @property
    def nombre(self) -> str:
        """Nombre completo de la moneda."""
        return self._nombre
    
    def __eq__(self, other):
        """Compara dos monedas por código."""
        if not isinstance(other, Moneda):
            return False
        return self._codigo == other._codigo
    
    def __hash__(self):
        """Hash basado en código."""
        return hash(self._codigo)
    
    def __str__(self):
        return f"{self._codigo} ({self._simbolo})"
    
    def __repr__(self):
        return f"Moneda(codigo='{self._codigo}', simbolo='{self._simbolo}', nombre='{self._nombre}')"
    
    @classmethod
    def from_code(cls, codigo: str) -> 'Moneda':
        """Crea una moneda desde su código."""
        return cls(codigo)
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "codigo": self._codigo,
            "simbolo": self._simbolo,
            "nombre": self._nombre
        }

