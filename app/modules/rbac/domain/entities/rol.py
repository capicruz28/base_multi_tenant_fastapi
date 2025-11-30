# app/modules/rbac/domain/entities/rol.py
"""
Rol: Entidad de dominio para roles.

✅ FASE 3: ARQUITECTURA - Entidad de dominio
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Rol:
    """
    Entidad de dominio Rol.
    
    Representa un rol en el sistema con su lógica de negocio.
    """
    
    def __init__(
        self,
        rol_id: int,
        nombre: str,
        cliente_id: Optional[int] = None,
        codigo_rol: Optional[str] = None,
        descripcion: Optional[str] = None,
        nivel_acceso: int = 1,
        es_activo: bool = True,
        permisos: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Inicializa la entidad Rol.
        
        Args:
            rol_id: ID único del rol
            nombre: Nombre del rol
            cliente_id: ID del cliente (None para roles del sistema)
            codigo_rol: Código único del rol (solo para cliente_id=1)
            descripcion: Descripción del rol
            nivel_acceso: Nivel de acceso (1-5)
            es_activo: Si el rol está activo
            permisos: Lista de permisos asignados
        """
        self.rol_id = rol_id
        self.nombre = nombre
        self.cliente_id = cliente_id
        self.codigo_rol = codigo_rol
        self.descripcion = descripcion
        self.nivel_acceso = nivel_acceso
        self.es_activo = es_activo
        self.permisos = permisos or []
        
        # Validaciones de dominio
        self._validate()
    
    def _validate(self):
        """Valida las reglas de negocio del rol."""
        if not self.nombre or len(self.nombre.strip()) == 0:
            raise ValueError("El nombre del rol no puede estar vacío")
        
        if self.nivel_acceso < 1 or self.nivel_acceso > 5:
            raise ValueError("El nivel de acceso debe estar entre 1 y 5")
        
        # Solo roles del sistema (cliente_id=1) pueden tener codigo_rol
        if self.codigo_rol and self.cliente_id != 1:
            raise ValueError("Solo los roles del sistema pueden tener codigo_rol")
    
    def is_active(self) -> bool:
        """Verifica si el rol está activo."""
        return self.es_activo
    
    def has_permission(self, codigo_permiso: str) -> bool:
        """Verifica si el rol tiene un permiso específico."""
        return any(
            permiso.get('codigo_permiso') == codigo_permiso
            and permiso.get('es_activo', False)
            and permiso.get('asignacion_activa', False)
            for permiso in self.permisos
        )
    
    def get_permission_codes(self) -> List[str]:
        """Obtiene los códigos de todos los permisos activos."""
        return [
            permiso.get('codigo_permiso')
            for permiso in self.permisos
            if permiso.get('es_activo', False) and permiso.get('asignacion_activa', False)
        ]
    
    def is_system_role(self) -> bool:
        """Verifica si es un rol del sistema."""
        return self.cliente_id == 1 or self.cliente_id is None
    
    def deactivate(self):
        """Desactiva el rol."""
        self.es_activo = False
    
    def activate(self):
        """Activa el rol."""
        self.es_activo = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rol':
        """Crea una instancia de Rol desde un diccionario."""
        return cls(
            rol_id=data.get('rol_id'),
            nombre=data.get('nombre', ''),
            cliente_id=data.get('cliente_id'),
            codigo_rol=data.get('codigo_rol'),
            descripcion=data.get('descripcion'),
            nivel_acceso=data.get('nivel_acceso', 1),
            es_activo=data.get('es_activo', True),
            permisos=data.get('permisos', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        return {
            'rol_id': self.rol_id,
            'nombre': self.nombre,
            'cliente_id': self.cliente_id,
            'codigo_rol': self.codigo_rol,
            'descripcion': self.descripcion,
            'nivel_acceso': self.nivel_acceso,
            'es_activo': self.es_activo,
            'permisos': self.permisos
        }

