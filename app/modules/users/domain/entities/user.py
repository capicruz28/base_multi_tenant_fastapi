# app/modules/users/domain/entities/user.py
"""
User: Entidad de dominio para usuarios del módulo Users.

✅ FASE 3: ARQUITECTURA - Entidad de dominio
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class User:
    """
    Entidad de dominio User (módulo Users).
    
    Representa un usuario completo del sistema con toda su información.
    """
    
    def __init__(
        self,
        usuario_id: int,
        nombre_usuario: str,
        cliente_id: int,
        correo: Optional[str] = None,
        nombre: Optional[str] = None,
        apellido: Optional[str] = None,
        dni: Optional[str] = None,
        telefono: Optional[str] = None,
        es_activo: bool = True,
        es_superadmin: bool = False,
        fecha_creacion: Optional[datetime] = None,
        fecha_ultimo_acceso: Optional[datetime] = None,
        roles: Optional[List[Dict[str, Any]]] = None,
        permisos: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Inicializa la entidad User.
        
        Args:
            usuario_id: ID único del usuario
            nombre_usuario: Nombre de usuario (único)
            cliente_id: ID del cliente/tenant
            correo: Email del usuario
            nombre: Nombre del usuario
            apellido: Apellido del usuario
            dni: DNI del usuario
            telefono: Teléfono del usuario
            es_activo: Si el usuario está activo
            es_superadmin: Si es superadmin
            fecha_creacion: Fecha de creación
            fecha_ultimo_acceso: Fecha del último acceso
            roles: Lista de roles asignados
            permisos: Lista de permisos del usuario
        """
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.cliente_id = cliente_id
        self.correo = correo
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.telefono = telefono
        self.es_activo = es_activo
        self.es_superadmin = es_superadmin
        self.fecha_creacion = fecha_creacion
        self.fecha_ultimo_acceso = fecha_ultimo_acceso
        self.roles = roles or []
        self.permisos = permisos or []
        
        # Validaciones de dominio
        self._validate()
    
    def _validate(self):
        """Valida las reglas de negocio del usuario."""
        if not self.nombre_usuario or len(self.nombre_usuario.strip()) == 0:
            raise ValueError("El nombre de usuario no puede estar vacío")
        
        if self.cliente_id is None or self.cliente_id <= 0:
            raise ValueError("El cliente_id debe ser un número positivo")
        
        if self.correo and "@" not in self.correo:
            raise ValueError("El email debe tener un formato válido")
    
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.es_activo
    
    def get_full_name(self) -> str:
        """Obtiene el nombre completo del usuario."""
        if self.nombre and self.apellido:
            return f"{self.nombre} {self.apellido}"
        elif self.nombre:
            return self.nombre
        elif self.apellido:
            return self.apellido
        else:
            return self.nombre_usuario
    
    def has_role(self, codigo_rol: str) -> bool:
        """Verifica si el usuario tiene un rol específico."""
        return any(
            rol.get('codigo_rol') == codigo_rol 
            and rol.get('es_activo', False)
            and rol.get('asignacion_activa', False)
            for rol in self.roles
        )
    
    def has_permission(self, codigo_permiso: str) -> bool:
        """Verifica si el usuario tiene un permiso específico."""
        return any(
            permiso.get('codigo_permiso') == codigo_permiso
            and permiso.get('es_activo', False)
            for permiso in self.permisos
        )
    
    def get_role_codes(self) -> List[str]:
        """Obtiene los códigos de todos los roles activos."""
        return [
            rol.get('codigo_rol')
            for rol in self.roles
            if rol.get('es_activo', False) and rol.get('asignacion_activa', False)
        ]
    
    def get_permission_codes(self) -> List[str]:
        """Obtiene los códigos de todos los permisos activos."""
        return [
            permiso.get('codigo_permiso')
            for permiso in self.permisos
            if permiso.get('es_activo', False)
        ]
    
    def deactivate(self):
        """Desactiva el usuario."""
        self.es_activo = False
    
    def activate(self):
        """Activa el usuario."""
        self.es_activo = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Crea una instancia de User desde un diccionario."""
        return cls(
            usuario_id=data.get('usuario_id'),
            nombre_usuario=data.get('nombre_usuario', ''),
            cliente_id=data.get('cliente_id'),
            correo=data.get('correo'),
            nombre=data.get('nombre'),
            apellido=data.get('apellido'),
            dni=data.get('dni'),
            telefono=data.get('telefono'),
            es_activo=data.get('es_activo', True),
            es_superadmin=data.get('es_superadmin', False),
            fecha_creacion=data.get('fecha_creacion'),
            fecha_ultimo_acceso=data.get('fecha_ultimo_acceso'),
            roles=data.get('roles', []),
            permisos=data.get('permisos', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a diccionario."""
        return {
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.nombre_usuario,
            'cliente_id': self.cliente_id,
            'correo': self.correo,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'dni': self.dni,
            'telefono': self.telefono,
            'es_activo': self.es_activo,
            'es_superadmin': self.es_superadmin,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_ultimo_acceso': self.fecha_ultimo_acceso.isoformat() if self.fecha_ultimo_acceso else None,
            'roles': self.roles,
            'permisos': self.permisos
        }

