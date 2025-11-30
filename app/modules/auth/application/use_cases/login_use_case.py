# app/modules/auth/application/use_cases/login_use_case.py
"""
LoginUseCase: Caso de uso para autenticación de usuarios.

✅ FASE 3: ARQUITECTURA - Use Case para Login
- Encapsula la lógica de negocio de autenticación
- Separa la lógica de negocio de los endpoints
- Facilita testing y reutilización
"""

from typing import Optional, Dict, Any
import logging

from app.modules.auth.domain.entities.usuario import Usuario
from app.modules.auth.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.core.security.password import verify_password
from app.core.exceptions import ValidationError, NotFoundError
from app.core.tenant.context import get_current_client_id

logger = logging.getLogger(__name__)


class LoginUseCase:
    """
    Caso de uso para autenticación de usuarios.
    
    Maneja la lógica de negocio para:
    - Validar credenciales
    - Verificar estado del usuario
    - Obtener información del usuario con roles
    """
    
    def __init__(self, usuario_repository: Optional[UsuarioRepository] = None):
        """
        Inicializa el caso de uso.
        
        Args:
            usuario_repository: Repositorio de usuarios (opcional, se crea uno nuevo si no se proporciona)
        """
        self.usuario_repository = usuario_repository or UsuarioRepository()
    
    def execute(
        self,
        username_or_email: str,
        password: str,
        client_id: Optional[int] = None
    ) -> Usuario:
        """
        Ejecuta el caso de uso de login.
        
        Args:
            username_or_email: Username o email del usuario
            password: Contraseña del usuario
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        
        Returns:
            Entidad Usuario autenticada
        
        Raises:
            ValidationError: Si las credenciales son inválidas
            NotFoundError: Si el usuario no existe
        """
        # 1. Validar que se proporcionaron credenciales
        if not username_or_email or not password:
            raise ValidationError(
                detail="Username/email y contraseña son requeridos",
                internal_code="MISSING_CREDENTIALS"
            )
        
        # 2. Obtener cliente_id del contexto si no se proporciona
        target_client_id = client_id
        if target_client_id is None:
            try:
                target_client_id = get_current_client_id()
            except RuntimeError:
                # Sin contexto, no se puede autenticar
                raise ValidationError(
                    detail="No se pudo determinar el contexto de cliente",
                    internal_code="MISSING_CLIENT_CONTEXT"
                )
        
        # 3. Buscar usuario
        usuario_data = self.usuario_repository.find_by_username_or_email(
            username_or_email,
            client_id=target_client_id
        )
        
        if not usuario_data:
            logger.warning(f"Intento de login con usuario inexistente: {username_or_email}")
            raise NotFoundError(
                detail="Usuario o contraseña incorrectos",
                internal_code="INVALID_CREDENTIALS"
            )
        
        # 4. Verificar contraseña
        stored_password_hash = usuario_data.get('contraseña_hash')
        if not stored_password_hash or not verify_password(password, stored_password_hash):
            logger.warning(f"Intento de login con contraseña incorrecta para usuario: {username_or_email}")
            raise ValidationError(
                detail="Usuario o contraseña incorrectos",
                internal_code="INVALID_CREDENTIALS"
            )
        
        # 5. Verificar que el usuario esté activo
        if not usuario_data.get('es_activo', False):
            logger.warning(f"Intento de login con usuario inactivo: {username_or_email}")
            raise ValidationError(
                detail="El usuario está inactivo. Contacte al administrador.",
                internal_code="USER_INACTIVE"
            )
        
        # 6. Obtener usuario con roles
        usuario_data = self.usuario_repository.find_with_roles(
            usuario_data['usuario_id'],
            client_id=target_client_id
        )
        
        # 7. Crear entidad de dominio
        usuario = Usuario.from_dict(usuario_data)
        
        # 8. Verificar reglas de negocio de dominio
        if not usuario.can_login():
            raise ValidationError(
                detail="El usuario no puede iniciar sesión en este momento",
                internal_code="USER_CANNOT_LOGIN"
            )
        
        # 9. Actualizar último acceso
        self.usuario_repository.update_last_login(
            usuario.usuario_id,
            client_id=target_client_id
        )
        usuario.mark_last_access()
        
        logger.info(f"Login exitoso para usuario: {usuario.nombre_usuario} (ID: {usuario.usuario_id})")
        
        return usuario

