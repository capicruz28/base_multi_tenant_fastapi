# app/shared/domain/value_objects/direccion.py
"""
Direccion: Value Object para representar direcciones.

✅ SHARED KERNEL: Compartido entre módulos (Clientes, Proveedores, Empleados, etc.)
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Direccion:
    """
    Value Object para representar una dirección física.
    
    Inmutable y compartido entre módulos.
    """
    
    def __init__(
        self,
        calle: str,
        ciudad: str,
        numero: Optional[str] = None,
        provincia: Optional[str] = None,
        codigo_postal: Optional[str] = None,
        pais: str = "Perú",
        referencia: Optional[str] = None
    ):
        """
        Inicializa una dirección.
        
        Args:
            calle: Nombre de la calle
            numero: Número de la dirección
            ciudad: Ciudad
            provincia: Provincia o estado
            codigo_postal: Código postal
            pais: País (default: "Perú")
            referencia: Referencia adicional (ej: "Frente al parque")
        """
        self._calle = calle.strip()
        self._numero = numero.strip() if numero else None
        self._ciudad = ciudad.strip()
        self._provincia = provincia.strip() if provincia else None
        self._codigo_postal = codigo_postal.strip() if codigo_postal else None
        self._pais = pais.strip()
        self._referencia = referencia.strip() if referencia else None
        
        self._validate()
    
    def _validate(self):
        """Valida los datos de la dirección."""
        if not self._calle or len(self._calle) < 3:
            raise ValueError("La calle debe tener al menos 3 caracteres")
        
        if not self._ciudad or len(self._ciudad) < 2:
            raise ValueError("La ciudad debe tener al menos 2 caracteres")
        
        if not self._pais or len(self._pais) < 2:
            raise ValueError("El país debe tener al menos 2 caracteres")
    
    @property
    def calle(self) -> str:
        """Calle."""
        return self._calle
    
    @property
    def numero(self) -> Optional[str]:
        """Número."""
        return self._numero
    
    @property
    def ciudad(self) -> str:
        """Ciudad."""
        return self._ciudad
    
    @property
    def provincia(self) -> Optional[str]:
        """Provincia o estado."""
        return self._provincia
    
    @property
    def codigo_postal(self) -> Optional[str]:
        """Código postal."""
        return self._codigo_postal
    
    @property
    def pais(self) -> str:
        """País."""
        return self._pais
    
    @property
    def referencia(self) -> Optional[str]:
        """Referencia adicional."""
        return self._referencia
    
    def get_direccion_completa(self) -> str:
        """Obtiene la dirección completa formateada."""
        parts = []
        
        # Calle y número
        if self._numero:
            parts.append(f"{self._calle} {self._numero}")
        else:
            parts.append(self._calle)
        
        # Ciudad
        parts.append(self._ciudad)
        
        # Provincia
        if self._provincia:
            parts.append(self._provincia)
        
        # Código postal
        if self._codigo_postal:
            parts.append(f"CP: {self._codigo_postal}")
        
        # País
        parts.append(self._pais)
        
        return ", ".join(parts)
    
    def __eq__(self, other):
        """Compara dos direcciones."""
        if not isinstance(other, Direccion):
            return False
        return (
            self._calle == other._calle and
            self._numero == other._numero and
            self._ciudad == other._ciudad and
            self._provincia == other._provincia and
            self._codigo_postal == other._codigo_postal and
            self._pais == other._pais
        )
    
    def __hash__(self):
        """Hash basado en componentes."""
        return hash((
            self._calle,
            self._numero,
            self._ciudad,
            self._provincia,
            self._codigo_postal,
            self._pais
        ))
    
    def __str__(self):
        return self.get_direccion_completa()
    
    def __repr__(self):
        return f"Direccion(calle='{self._calle}', ciudad='{self._ciudad}', pais='{self._pais}')"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Direccion':
        """Crea una dirección desde un diccionario."""
        return cls(
            calle=data.get('calle', ''),
            numero=data.get('numero'),
            ciudad=data.get('ciudad', ''),
            provincia=data.get('provincia'),
            codigo_postal=data.get('codigo_postal'),
            pais=data.get('pais', 'Perú'),
            referencia=data.get('referencia')
        )
    
    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "calle": self._calle,
            "numero": self._numero,
            "ciudad": self._ciudad,
            "provincia": self._provincia,
            "codigo_postal": self._codigo_postal,
            "pais": self._pais,
            "referencia": self._referencia,
            "direccion_completa": self.get_direccion_completa()
        }

