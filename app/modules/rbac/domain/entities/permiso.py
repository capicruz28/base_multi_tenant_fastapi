# app/modules/rbac/domain/entities/permiso.py
"""
Permiso: Entidad de dominio para permisos.

✅ FASE 3: ARQUITECTURA - Entidad de dominio
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Permiso:
    """
    Entidad de dominio Permiso.
    
    Representa un permiso en el sistema con su lógica de negocio.
    """
    
    def __init__(
        self,
        permiso_id: int,
        codigo_permiso: str,
        nombre: str,
        descripcion: Optional[str] = None,
        es_activo: bool = True
    ):
        """
        Inicializa la entidad Permiso.
        
        Args:
            permiso_id: ID único del permiso
            codigo_permiso: Código único del permiso
            nombre: Nombre del permiso
            descripcion: Descripción del permiso
            es_activo: Si el permiso está activo
        """
        self.permiso_id = permiso_id
        self.codigo_permiso = codigo_permiso
        self.nombre = nombre
        self.descripcion = descripcion
        self.es_activo = es_activo
        
        # Validaciones de dominio
        self._validate()
    
    def _validate(self):
        """Valida las reglas de negocio del permiso."""
        if not self.codigo_permiso or len(self.codigo_permiso.strip()) == 0:
            raise ValueError("El código del permiso no puede estar vacío")
        
        if not self.nombre or len(self.nombre.strip()) == 0:
            raise ValueError("El nombre del permiso no puede estar vacío")
    
    def is_active(self) -> bool:
        """Verifica si el permiso está activo."""
        return self.es_activo
    
    def deactivate(self):
        """Desactiva el permiso."""
        self.es_activo = False
    
    def activate(self):
        """Activa el permiso."""
        self.es_activo = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Permiso':
        """Crea una instancia de Permiso desde un diccionario."""
        return cls(
            permiso_id=data.get('permiso_id'),
            codigo_permiso=data.get('codigo_permiso', ''),
            nombre=data.get('nombre', ''),
            descripcion=data.get('descripcion'),
            es_activo=data.get('es_activo', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        return {
            'permiso_id': self.permiso_id,
            'codigo_permiso': self.codigo_permiso,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'es_activo': self.es_activo
        }

