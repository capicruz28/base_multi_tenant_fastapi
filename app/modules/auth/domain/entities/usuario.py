# app/modules/auth/domain/entities/usuario.py
"""
Usuario: Entidad de dominio para usuarios.

✅ FASE 3: ARQUITECTURA - Entidad de dominio
- Encapsula lógica de negocio relacionada con usuarios
- Validaciones de dominio
- Inmutabilidad donde sea apropiado
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Usuario:
    """
    Entidad de dominio Usuario.
    
    Representa un usuario en el sistema con su lógica de negocio.
    """
    
    def __init__(
        self,
        usuario_id: int,
        nombre_usuario: str,
        email: str,
        cliente_id: int,
        es_activo: bool = True,
        es_superadmin: bool = False,
        nombre_completo: Optional[str] = None,
        telefono: Optional[str] = None,
        fecha_creacion: Optional[datetime] = None,
        ultimo_acceso: Optional[datetime] = None,
        roles: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Inicializa la entidad Usuario.
        
        Args:
            usuario_id: ID único del usuario
            nombre_usuario: Nombre de usuario (único)
            email: Email del usuario (único)
            cliente_id: ID del cliente/tenant
            es_activo: Si el usuario está activo
            es_superadmin: Si es superadmin
            nombre_completo: Nombre completo del usuario
            telefono: Teléfono del usuario
            fecha_creacion: Fecha de creación
            ultimo_acceso: Fecha del último acceso
            roles: Lista de roles asignados
        """
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.email = email
        self.cliente_id = cliente_id
        self.es_activo = es_activo
        self.es_superadmin = es_superadmin
        self.nombre_completo = nombre_completo
        self.telefono = telefono
        self.fecha_creacion = fecha_creacion
        self.ultimo_acceso = ultimo_acceso
        self.roles = roles or []
        
        # Validaciones de dominio
        self._validate()
    
    def _validate(self):
        """Valida las reglas de negocio del usuario."""
        if not self.nombre_usuario or len(self.nombre_usuario.strip()) == 0:
            raise ValueError("El nombre de usuario no puede estar vacío")
        
        if not self.email or len(self.email.strip()) == 0:
            raise ValueError("El email no puede estar vacío")
        
        if "@" not in self.email:
            raise ValueError("El email debe tener un formato válido")
        
        if self.cliente_id is None or self.cliente_id <= 0:
            raise ValueError("El cliente_id debe ser un número positivo")
    
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.es_activo
    
    def can_login(self) -> bool:
        """
        Verifica si el usuario puede iniciar sesión.
        
        Reglas de negocio:
        - Debe estar activo
        - No debe estar bloqueado (si implementamos bloqueo)
        """
        return self.is_active()
    
    def has_role(self, codigo_rol: str) -> bool:
        """
        Verifica si el usuario tiene un rol específico.
        
        Args:
            codigo_rol: Código del rol a verificar
        
        Returns:
            True si tiene el rol, False en caso contrario
        """
        return any(
            rol.get('codigo_rol') == codigo_rol 
            and rol.get('es_activo', False)
            and rol.get('asignacion_activa', False)
            for rol in self.roles
        )
    
    def get_role_codes(self) -> List[str]:
        """
        Obtiene los códigos de todos los roles activos del usuario.
        
        Returns:
            Lista de códigos de roles
        """
        return [
            rol.get('codigo_rol')
            for rol in self.roles
            if rol.get('es_activo', False) and rol.get('asignacion_activa', False)
        ]
    
    def mark_last_access(self):
        """Marca el último acceso del usuario."""
        self.ultimo_acceso = datetime.now()
    
    def deactivate(self):
        """Desactiva el usuario."""
        self.es_activo = False
    
    def activate(self):
        """Activa el usuario."""
        self.es_activo = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Usuario':
        """
        Crea una instancia de Usuario desde un diccionario.
        
        Args:
            data: Diccionario con los datos del usuario
        
        Returns:
            Instancia de Usuario
        """
        return cls(
            usuario_id=data.get('usuario_id'),
            nombre_usuario=data.get('nombre_usuario', ''),
            email=data.get('email', ''),
            cliente_id=data.get('cliente_id'),
            es_activo=data.get('es_activo', True),
            es_superadmin=data.get('es_superadmin', False),
            nombre_completo=data.get('nombre_completo'),
            telefono=data.get('telefono'),
            fecha_creacion=data.get('fecha_creacion'),
            ultimo_acceso=data.get('ultimo_acceso'),
            roles=data.get('roles', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la entidad a diccionario.
        
        Returns:
            Diccionario con los datos del usuario
        """
        return {
            'usuario_id': self.usuario_id,
            'nombre_usuario': self.nombre_usuario,
            'email': self.email,
            'cliente_id': self.cliente_id,
            'es_activo': self.es_activo,
            'es_superadmin': self.es_superadmin,
            'nombre_completo': self.nombre_completo,
            'telefono': self.telefono,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'roles': self.roles
        }

