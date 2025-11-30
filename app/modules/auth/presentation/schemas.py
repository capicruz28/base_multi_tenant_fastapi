# app/schemas/auth.py
"""
Esquemas Pydantic para la autenticación y autorización en el sistema.

Este módulo define todos los esquemas de validación, creación y lectura
relacionados con la autenticación de usuarios, tokens JWT y datos de sesión.

Características principales:
- Validaciones robustas con mensajes de error en español
- Seguridad en el manejo de tokens y datos de usuario
- Compatibilidad con OAuth2 y JWT
- Documentación clara para desarrolladores
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

class UserDataBase(BaseModel):
    """
    Schema base para datos de usuario en respuestas de autenticación.
    
    Incluye los datos básicos del usuario que se necesitan en el frontend
    para mostrar información y tomar decisiones de UI/UX.
    """
    
    usuario_id: int = Field(
        ...,
        description="Identificador único del usuario en el sistema",
        examples=[1, 2, 3]
    )
    
    nombre_usuario: str = Field(
        ...,
        description="Nombre de usuario único para identificación en el sistema",
        examples=["juan_perez", "maria.garcia"]
    )
    
    correo: str = Field(
        ...,
        description="Dirección de correo electrónico válida del usuario",
        examples=["usuario@empresa.com", "nombre.apellido@dominio.org"]
    )
    
    nombre: Optional[str] = Field(
        None,
        description="Nombre real del usuario",
        examples=["Juan", "María José"]
    )
    
    apellido: Optional[str] = Field(
        None,
        description="Apellido del usuario", 
        examples=["Pérez García", "López"]
    )
    
    es_activo: bool = Field(
        ...,
        description="Indica si el usuario está activo en el sistema",
        examples=[True, False]
    )

    @field_validator('nombre_usuario')
    @classmethod
    def validar_nombre_usuario(cls, valor: str) -> str:
        """
        Valida que el nombre de usuario tenga un formato básico.
        
        Reglas:
        - No puede estar vacío
        - Debe tener al menos 3 caracteres
        - Solo permite letras, números y guiones bajos
        
        Args:
            valor: El nombre de usuario a validar
            
        Returns:
            str: Nombre de usuario validado y normalizado
            
        Raises:
            ValueError: Cuando el formato no es válido
        """
        if not valor:
            raise ValueError('El nombre de usuario no puede estar vacío')
        
        valor = valor.strip()
        
        if len(valor) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres')
        
        if not re.match(r'^[a-zA-Z0-9_]+$', valor):
            raise ValueError(
                'El nombre de usuario solo puede contener letras, números y guiones bajos (_). '
                'No se permiten espacios ni caracteres especiales.'
            )
        
        return valor

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre_apellido(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida que nombres y apellidos contengan solo caracteres alfabéticos válidos.
        
        Permite:
        - Letras del alfabeto español (incluyendo ñ y acentos)
        - Espacios para nombres compuestos
        - Guiones para nombres compuestos
        
        Args:
            valor: El nombre o apellido a validar
            
        Returns:
            Optional[str]: Nombre o apellido validado y formateado
            
        Raises:
            ValueError: Cuando contiene caracteres no permitidos
        """
        if valor is None or valor == "":
            return None
        
        valor = valor.strip()
        
        if not valor:
            return None
        
        # Patrón que permite letras, espacios, guiones y caracteres españoles
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', valor):
            raise ValueError(
                'El nombre y apellido solo pueden contener letras, espacios y guiones. '
                'No se permiten números ni caracteres especiales.'
            )
        
        # Validar que no sea solo espacios o guiones
        if valor.replace(' ', '').replace('-', '') == '':
            raise ValueError('El nombre no puede contener solo espacios o guiones')
        
        # Formatear con capitalización adecuada
        return valor.title()

class RolInfo(BaseModel):
    """
    Schema para información detallada de un rol.
    
    Incluye todos los datos del rol necesarios para el frontend
    y para la toma de decisiones de autorización.
    """
    
    rol_id: int = Field(
        ...,
        description="ID único del rol en el sistema",
        examples=[1, 2, 3]
    )
    
    nombre: str = Field(
        ...,
        description="Nombre único del rol",
        examples=["Administrador", "Usuario", "Reportes"]
    )
    
    descripcion: Optional[str] = Field(
        None,
        description="Descripción detallada del rol y sus permisos",
        examples=["Acceso completo al sistema", "Solo lectura de reportes"]
    )
    
    es_activo: bool = Field(
        ...,
        description="Indica si el rol está activo en el sistema",
        examples=[True, False]
    )
    
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha y hora de creación del rol"
    )
    
    fecha_asignacion: Optional[datetime] = Field(
        None,
        description="Fecha y hora en que se asignó este rol al usuario"
    )

class PermisoInfo(BaseModel):
    """
    Schema para información de permisos individuales.
    
    Representa los permisos específicos que puede tener un usuario
    a través de sus roles asignados.
    """
    
    permiso_id: int = Field(
        ...,
        description="ID único del permiso en el sistema",
        examples=[1, 2, 3]
    )
    
    nombre: str = Field(
        ...,
        description="Nombre único del permiso",
        examples=["usuarios.leer", "reportes.escribir", "configuracion.administrar"]
    )
    
    descripcion: Optional[str] = Field(
        None,
        description="Descripción detallada del permiso",
        examples=["Permite leer información de usuarios", "Permite generar reportes"]
    )
    
    modulo: str = Field(
        ...,
        description="Módulo del sistema al que pertenece el permiso",
        examples=["usuarios", "reportes", "configuracion"]
    )

class ClienteInfo(BaseModel):
    """
    Schema para información del cliente/tenant del usuario.
    
    En arquitectura multi-tenant, cada usuario pertenece a un cliente específico
    que define su ámbito de datos y permisos.
    """
    
    cliente_id: int = Field(
        ...,
        description="ID único del cliente en el sistema",
        examples=[1, 2, 3]
    )
    
    nombre: str = Field(
        ...,
        description="Nombre del cliente o empresa",
        examples=["Empresa ABC", "Corporación XYZ"]
    )
    
    codigo: str = Field(
        ...,
        description="Código único identificador del cliente",
        examples=["EMP_ABC", "CORP_XYZ"]
    )
    
    es_activo: bool = Field(
        ...,
        description="Indica si el cliente está activo en el sistema",
        examples=[True, False]
    )
    
    configuracion: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuración específica del cliente",
        examples=[{"tema": "oscuro", "idioma": "es"}, {"max_usuarios": 50}]
    )

class UserWithRolesAndPermissions(UserDataBase):
    """
    Schema extendido para información completa del usuario autenticado.
    
    🎯 UTILIZADO EN: Endpoint /me extendido
    📋 INCLUYE: Todos los datos necesarios para el frontend
    🔐 SEGURIDAD: Información de roles, permisos y ámbito del usuario
    
    Este schema proporciona toda la información que necesita el frontend
    para:
    - Mostrar la interfaz de usuario adecuada
    - Tomar decisiones de autorización en el cliente
    - Mostrar información del perfil completo
    - Determinar capacidades y restricciones del usuario
    """
    
    # 👤 DATOS PERSONALES EXTENDIDOS
    dni: Optional[str] = Field(
        None,
        description="Documento Nacional de Identidad",
        examples=["12345678A", "87654321B"]
    )
    
    telefono: Optional[str] = Field(
        None,
        description="Número de teléfono de contacto",
        examples=["+34 600 123 456", "955 123 456"]
    )
    
    proveedor_autenticacion: str = Field(
        "local",
        description="Proveedor de autenticación utilizado",
        examples=["local", "ldap", "azure_ad", "google"]
    )
    
    correo_confirmado: bool = Field(
        False,
        description="Indica si el correo electrónico ha sido confirmado",
        examples=[True, False]
    )
    
    # 📅 DATOS TEMPORALES COMPLETOS
    fecha_creacion: datetime = Field(
        ...,
        description="Fecha y hora de creación del usuario en el sistema"
    )
    
    fecha_ultimo_acceso: Optional[datetime] = Field(
        None,
        description="Fecha y hora del último acceso exitoso del usuario"
    )
    
    fecha_actualizacion: Optional[datetime] = Field(
        None,
        description="Fecha y hora de la última actualización del usuario"
    )
    
    # 🎭 INFORMACIÓN DE ROLES Y PERMISOS
    roles: List[RolInfo] = Field(
        default_factory=list,
        description="Lista completa de roles asignados al usuario con toda su información"
    )
    
    permisos: List[PermisoInfo] = Field(
        default_factory=list,
        description="Lista de permisos individuales del usuario (obtenidos a través de sus roles)"
    )
    
    nombres_roles: List[str] = Field(
        default_factory=list,
        description="Lista de nombres de roles (para compatibilidad con versiones anteriores)",
        examples=[["Administrador", "Usuario"], ["Reportes"]]
    )
    
    # 🏢 INFORMACIÓN DEL CLIENTE/TENANT
    cliente: Optional[ClienteInfo] = Field(
        None,
        description="Información completa del cliente al que pertenece el usuario"
    )
    
    # 🔍 DETECCIÓN AUTOMÁTICA DE TIPO DE USUARIO
    es_super_admin: bool = Field(
        False,
        description="Indica si el usuario es Super Administrador del sistema",
        examples=[True, False]
    )
    
    es_tenant_admin: bool = Field(
        False,
        description="Indica si el usuario es Administrador de Tenant/Cliente",
        examples=[True, False]
    )
    
    tipo_usuario: str = Field(
        "usuario_normal",
        description="Tipo de usuario detectado automáticamente",
        examples=["super_admin", "tenant_admin", "usuario_normal"]
    )
    
    # 🎯 PERMISOS AGRUPADOS PARA FÁCIL ACCESO
    permisos_por_modulo: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Permisos agrupados por módulo para fácil acceso en el frontend",
        examples=[{"usuarios": ["leer", "escribir"], "reportes": ["leer"]}]
    )

    @field_validator('dni')
    @classmethod
    def validar_dni(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida el formato básico del DNI.
        
        Args:
            valor: DNI a validar
            
        Returns:
            Optional[str]: DNI validado y normalizado
            
        Raises:
            ValueError: Cuando el formato no es válido
        """
        if valor is None or valor == "":
            return None
        
        valor = valor.strip().upper()
        
        # Validación básica de DNI español (8 números + 1 letra)
        if not re.match(r'^\d{8}[A-Z]$', valor):
            raise ValueError('El DNI debe tener 8 números seguidos de 1 letra')
        
        return valor

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida el formato básico del teléfono.
        
        Args:
            valor: Teléfono a validar
            
        Returns:
            Optional[str]: Teléfono validado y normalizado
            
        Raises:
            ValueError: Cuando el formato no es válido
        """
        if valor is None or valor == "":
            return None
        
        valor = valor.strip()
        
        # Eliminar espacios y caracteres no numéricos para validación
        solo_numeros = re.sub(r'[^\d+]', '', valor)
        
        if len(solo_numeros) < 9:
            raise ValueError('El número de teléfono debe tener al menos 9 dígitos')
        
        return valor

    @field_validator('proveedor_autenticacion')
    @classmethod
    def validar_proveedor_autenticacion(cls, valor: str) -> str:
        """
        Valida que el proveedor de autenticación sea uno de los permitidos.
        
        Args:
            valor: Proveedor de autenticación a validar
            
        Returns:
            str: Proveedor validado
            
        Raises:
            ValueError: Cuando el proveedor no es válido
        """
        proveedores_permitidos = ['local', 'ldap', 'azure_ad', 'google', 'okta']
        
        if valor not in proveedores_permitidos:
            raise ValueError(f'Proveedor de autenticación no válido. Permitidos: {", ".join(proveedores_permitidos)}')
        
        return valor

class UserDataWithRoles(UserDataBase):
    """
    Schema extendido para datos de usuario que incluye roles.
    
    Utilizado en respuestas de login y perfil de usuario donde
    se necesita información completa de roles y permisos.
    
    AHORA INCLUYE: Campos de nivel de acceso para el sistema LBAC
    """
    
    roles: List[str] = Field(
        default_factory=list,
        description="Lista de nombres de roles asignados al usuario",
        examples=[["Administrador", "Usuario"], ["Reportes"]]
    )
    
    # ✅ NUEVOS CAMPOS PARA SISTEMA DE NIVELES
    access_level: int = Field(
        1,
        ge=1,
        le=5,
        description="Nivel de acceso máximo del usuario basado en sus roles (1-5)",
        examples=[1, 3, 5]
    )
    
    is_super_admin: bool = Field(
        False,
        description="Indica si el usuario tiene rol de Super Administrador",
        examples=[True, False]
    )
    
    user_type: str = Field(
        "user",
        description="Tipo de usuario: 'super_admin', 'tenant_admin', 'user'",
        examples=["super_admin", "tenant_admin", "user"]
    )
    
    cliente_id: Optional[int] = Field(
        None,
        description="ID del cliente al que pertenece el usuario",
        examples=[1, 2, 3]
    )

    @field_validator('roles')
    @classmethod
    def validar_roles(cls, valor: List[str]) -> List[str]:
        """
        Valida que la lista de roles contenga solo strings no vacíos.
        
        Args:
            valor: Lista de nombres de roles a validar
            
        Returns:
            List[str]: Lista de roles validada
            
        Raises:
            ValueError: Cuando algún rol no es válido
        """
        if not isinstance(valor, list):
            raise ValueError('Los roles deben ser una lista')
        
        roles_validos = []
        for rol in valor:
            if not isinstance(rol, str):
                raise ValueError('Cada rol debe ser una cadena de texto')
            
            rol_limpio = rol.strip()
            if not rol_limpio:
                raise ValueError('Los nombres de roles no pueden estar vacíos')
            
            roles_validos.append(rol_limpio)
        
        return roles_validos

    @field_validator('access_level')
    @classmethod
    def validar_access_level(cls, valor: int) -> int:
        """
        Valida que el nivel de acceso esté en el rango permitido.
        
        Args:
            valor: Nivel de acceso a validar
            
        Returns:
            int: Nivel de acceso validado
            
        Raises:
            ValueError: Cuando el nivel no está en el rango 1-5
        """
        if valor < 1 or valor > 5:
            raise ValueError('El nivel de acceso debe estar entre 1 y 5')
        
        return valor

    @field_validator('user_type')
    @classmethod
    def validar_user_type(cls, valor: str) -> str:
        """
        Valida que el tipo de usuario sea uno de los permitidos.
        
        Args:
            valor: Tipo de usuario a validar
            
        Returns:
            str: Tipo de usuario validado
            
        Raises:
            ValueError: Cuando el tipo no es válido
        """
        tipos_permitidos = ['super_admin', 'tenant_admin', 'user']
        
        if valor not in tipos_permitidos:
            raise ValueError(f'Tipo de usuario no válido. Permitidos: {", ".join(tipos_permitidos)}')
        
        return valor

class LoginData(BaseModel):
    """
    Schema para datos de inicio de sesión.
    
    Alternativa al uso de OAuth2PasswordRequestForm para casos
    donde se necesite más control sobre la validación.
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre de usuario para autenticación",
        examples=["juan_perez", "maria.garcia"]
    )
    
    password: str = Field(
        ...,
        min_length=1,
        description="Contraseña del usuario",
        examples=["MiContraseñaSegura123", "OtraPassword123!"]
    )

    @field_validator('username')
    @classmethod
    def validar_username_login(cls, valor: str) -> str:
        """
        Valida el formato del nombre de usuario durante el login.
        
        Args:
            valor: Nombre de usuario a validar
            
        Returns:
            str: Nombre de usuario validado
            
        Raises:
            ValueError: Cuando el formato no es válido
        """
        if not valor:
            raise ValueError('El nombre de usuario no puede estar vacío')
        
        valor = valor.strip()
        
        if len(valor) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres')
        
        return valor

    @field_validator('password')
    @classmethod
    def validar_password_login(cls, valor: str) -> str:
        """
        Valida que la contraseña no esté vacía.
        
        Nota: No validamos fortaleza aquí porque eso se hace al crear la cuenta.
        
        Args:
            valor: Contraseña a validar
            
        Returns:
            str: Contraseña validada
            
        Raises:
            ValueError: Cuando la contraseña está vacía
        """
        if not valor:
            raise ValueError('La contraseña no puede estar vacía')
        
        return valor

class Token(BaseModel):
    """
    Schema para respuesta de tokens JWT.
    
    Incluye el token de acceso y opcionalmente los datos del usuario
    para evitar llamadas adicionales al backend después del login.
    
    AHORA INCLUYE: Campos de nivel de acceso en user_data
    """
    
    access_token: str = Field(
        ...,
        description="Token JWT de acceso para autorizar solicitudes",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."]
    )
    
    token_type: str = Field(
        "bearer",
        description="Tipo de token, siempre 'bearer' para JWT",
        examples=["bearer"]
    )
    
    user_data: Optional[UserDataWithRoles] = Field(
        None,
        description="Datos del usuario autenticado (opcional, no se incluye en refresh)"
    )

    @field_validator('access_token')
    @classmethod
    def validar_access_token(cls, valor: str) -> str:
        """
        Valida que el token no esté vacío.
        
        Args:
            valor: Token JWT a validar
            
        Returns:
            str: Token validado
            
        Raises:
            ValueError: Cuando el token está vacío
        """
        if not valor:
            raise ValueError('El token de acceso no puede estar vacío')
        
        return valor

class TokenPayload(BaseModel):
    """
    Schema para el payload de tokens JWT.
    
    Representa la estructura de datos codificada dentro de los tokens JWT
    generados por el sistema.
    
    AHORA INCLUYE: Campos de nivel de acceso para autorización LBAC
    """
    
    sub: Optional[str] = Field(
        None,
        description="Subject (usualmente el nombre de usuario)",
        examples=["juan_perez", "maria.garcia"]
    )
    
    exp: Optional[int] = Field(
        None,
        description="Timestamp de expiración del token",
        examples=[1735689600]
    )
    
    iat: Optional[int] = Field(
        None, 
        description="Timestamp de emisión del token",
        examples=[1735689000]
    )
    
    type: Optional[str] = Field(
        None,
        description="Tipo de token: 'access' o 'refresh'",
        examples=["access", "refresh"]
    )
    
    # ✅ NUEVOS CAMPOS PARA SISTEMA DE NIVELES
    access_level: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Nivel de acceso máximo del usuario (1-5)",
        examples=[1, 3, 5]
    )
    
    is_super_admin: Optional[bool] = Field(
        None,
        description="Indica si el usuario tiene rol de Super Administrador",
        examples=[True, False]
    )
    
    user_type: Optional[str] = Field(
        None,
        description="Tipo de usuario: 'super_admin', 'tenant_admin', 'user'",
        examples=["super_admin", "tenant_admin", "user"]
    )
    
    cliente_id: Optional[int] = Field(
        None,
        description="ID del cliente al que pertenece el usuario",
        examples=[1, 2, 3]
    )

    @field_validator('type')
    @classmethod
    def validar_tipo_token(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida que el tipo de token sea uno de los permitidos.
        
        Args:
            valor: Tipo de token a validar
            
        Returns:
            Optional[str]: Tipo de token validado
            
        Raises:
            ValueError: Cuando el tipo no es válido
        """
        if valor is not None and valor not in ['access', 'refresh']:
            raise ValueError('El tipo de token debe ser "access" o "refresh"')
        
        return valor

    @field_validator('access_level')
    @classmethod
    def validar_access_level_token(cls, valor: Optional[int]) -> Optional[int]:
        """
        Valida que el nivel de acceso esté en el rango permitido.
        
        Args:
            valor: Nivel de acceso a validar
            
        Returns:
            Optional[int]: Nivel de acceso validado
            
        Raises:
            ValueError: Cuando el nivel no está en el rango 1-5
        """
        if valor is not None and (valor < 1 or valor > 5):
            raise ValueError('El nivel de acceso debe estar entre 1 y 5')
        
        return valor

    @field_validator('user_type')
    @classmethod
    def validar_user_type_token(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida que el tipo de usuario sea uno de los permitidos.
        
        Args:
            valor: Tipo de usuario a validar
            
        Returns:
            Optional[str]: Tipo de usuario validado
            
        Raises:
            ValueError: Cuando el tipo no es válido
        """
        if valor is not None and valor not in ['super_admin', 'tenant_admin', 'user']:
            raise ValueError(f'Tipo de usuario no válido. Permitidos: super_admin, tenant_admin, user')
        
        return valor

class RefreshTokenRequest(BaseModel):
    """Schema para recibir refresh token en el body (clientes móviles)"""
    
    refresh_token: str = Field(
        ...,
        description="Refresh token JWT para obtener nuevo access token"
    )

    class Config:
        """Configuración de Pydantic para el schema."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True


# ============================================================================
# SCHEMAS DE CONFIGURACIÓN DE AUTENTICACIÓN
# ============================================================================
"""
Esquemas Pydantic para la entidad AuthConfig en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para la configuración de políticas
de autenticación y seguridad por cliente, incluyendo políticas de contraseñas,
configuración de 2FA, control de sesiones y restricciones de acceso.

Características clave:
- Configuración granular de políticas de seguridad por cliente
- Validación de coherencia entre políticas relacionadas
- Soporte para 2FA, whitelist/blacklist de IPs, horarios de acceso
- Valores por defecto coherentes con mejores prácticas de seguridad
- Total coherencia con la estructura de la tabla cliente_auth_config
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import json
import re


class AuthConfigBase(BaseModel):
    """
    Esquema base para la entidad AuthConfig, alineado con la tabla cliente_auth_config.
    Define las políticas de autenticación y seguridad específicas para cada cliente.
    """
    # ========================================
    # POLÍTICAS DE CONTRASEÑA
    # ========================================
    password_min_length: int = Field(
        8, 
        description="Longitud mínima de contraseña."
    )
    password_require_uppercase: bool = Field(
        True, 
        description="Requiere al menos una letra mayúscula."
    )
    password_require_lowercase: bool = Field(
        True, 
        description="Requiere al menos una letra minúscula."
    )
    password_require_number: bool = Field(
        True, 
        description="Requiere al menos un número."
    )
    password_require_special: bool = Field(
        False, 
        description="Requiere al menos un carácter especial (!@#$%^&*)."
    )
    password_expiry_days: int = Field(
        90, 
        description="Días antes de expirar la contraseña (0 = nunca expira)."
    )
    password_history_count: int = Field(
        3, 
        description="Cuántas contraseñas previas recordar (no permitir reutilizar)."
    )

    # ========================================
    # CONTROL DE ACCESO Y SESIONES
    # ========================================
    max_login_attempts: int = Field(
        5, 
        description="Máximo de intentos fallidos antes de bloquear."
    )
    lockout_duration_minutes: int = Field(
        30, 
        description="Duración del bloqueo en minutos."
    )
    max_active_sessions: int = Field(
        3, 
        description="Máximo de sesiones simultáneas por usuario (0 = ilimitado)."
    )
    session_idle_timeout_minutes: int = Field(
        60, 
        description="Minutos de inactividad antes de cerrar sesión (0 = no expira)."
    )

    # ========================================
    # TOKENS JWT
    # ========================================
    access_token_minutes: int = Field(
        15, 
        description="Duración del access token en minutos."
    )
    refresh_token_days: int = Field(
        30, 
        description="Duración del refresh token en días."
    )

    # ========================================
    # OPCIONES DE LOGIN Y RECUPERACIÓN
    # ========================================
    allow_remember_me: bool = Field(
        True, 
        description="Permitir opción 'Recordar sesión'."
    )
    remember_me_days: int = Field(
        30, 
        description="Duración de sesión si marca 'recordar' (en días)."
    )
    require_email_verification: bool = Field(
        False, 
        description="Requiere verificar email antes de primer login."
    )
    allow_password_reset: bool = Field(
        True, 
        description="Permitir recuperación de contraseña por email."
    )

    # ========================================
    # AUTENTICACIÓN DE DOS FACTORES (2FA)
    # ========================================
    enable_2fa: bool = Field(
        False, 
        description="Habilitar 2FA para el cliente."
    )
    require_2fa_for_admins: bool = Field(
        False, 
        description="Forzar 2FA para usuarios con rol admin."
    )
    metodos_2fa_permitidos: str = Field(
        "email,sms", 
        description="Métodos permitidos separados por coma: 'email', 'sms', 'totp', 'app'."
    )

    # ========================================
    # WHITELIST/BLACKLIST DE IPs
    # ========================================
    ip_whitelist_enabled: bool = Field(
        False, 
        description="Habilitar whitelist de IPs permitidas."
    )
    ip_whitelist: Optional[str] = Field(
        None, 
        description="JSON array de IPs permitidas (ej: [\"192.168.1.0/24\", \"10.0.0.1\"])."
    )
    ip_blacklist: Optional[str] = Field(
        None, 
        description="JSON array de IPs bloqueadas."
    )

    # ========================================
    # HORARIOS DE ACCESO
    # ========================================
    horario_acceso_enabled: bool = Field(
        False, 
        description="Habilitar restricción por horarios."
    )
    horario_acceso_config: Optional[str] = Field(
        None, 
        description="JSON con horarios permitidos (ej: {\"lunes\": \"08:00-18:00\"})."
    )

    # === VALIDADORES ===
    @validator('password_min_length')
    def validar_longitud_minima_password(cls, v):
        """
        Valida que la longitud mínima de contraseña sea segura.
        """
        if v < 6:
            raise ValueError("La longitud mínima de contraseña debe ser al menos 6 caracteres.")
        if v > 128:
            raise ValueError("La longitud mínima de contraseña no puede exceder 128 caracteres.")
        return v

    @validator('password_expiry_days')
    def validar_expiracion_password(cls, v):
        """
        Valida que los días de expiración sean razonables.
        """
        if v < 0:
            raise ValueError("Los días de expiración de contraseña no pueden ser negativos.")
        if v > 365:
            raise ValueError("Los días de expiración de contraseña no pueden exceder 1 año.")
        return v

    @validator('max_login_attempts')
    def validar_intentos_login(cls, v):
        """
        Valida que el número máximo de intentos sea razonable.
        """
        if v < 1:
            raise ValueError("El número máximo de intentos de login debe ser al menos 1.")
        if v > 20:
            raise ValueError("El número máximo de intentos de login no puede exceder 20.")
        return v

    @validator('lockout_duration_minutes')
    def validar_duracion_bloqueo(cls, v):
        """
        Valida que la duración del bloqueo sea razonable.
        """
        if v < 1:
            raise ValueError("La duración del bloqueo debe ser al menos 1 minuto.")
        if v > 1440:  # 24 horas
            raise ValueError("La duración del bloqueo no puede exceder 24 horas.")
        return v

    @validator('access_token_minutes')
    def validar_duracion_access_token(cls, v):
        """
        Valida que la duración del access token sea segura.
        """
        if v < 1:
            raise ValueError("La duración del access token debe ser al menos 1 minuto.")
        if v > 1440:  # 24 horas
            raise ValueError("La duración del access token no puede exceder 24 horas.")
        return v

    @validator('refresh_token_days')
    def validar_duracion_refresh_token(cls, v):
        """
        Valida que la duración del refresh token sea razonable.
        """
        if v < 1:
            raise ValueError("La duración del refresh token debe ser al menos 1 día.")
        if v > 365:
            raise ValueError("La duración del refresh token no puede exceder 1 año.")
        return v

    @validator('metodos_2fa_permitidos')
    def validar_metodos_2fa(cls, v):
        """
        Valida que los métodos 2FA sean soportados.
        """
        metodos_validos = ['email', 'sms', 'totp', 'app']
        metodos_provistos = [m.strip().lower() for m in v.split(',')]
        
        for metodo in metodos_provistos:
            if metodo not in metodos_validos:
                raise ValueError(f"Método 2FA no soportado: {metodo}. Use: {', '.join(metodos_validos)}")
        
        return v

    @validator('ip_whitelist', 'ip_blacklist')
    def validar_json_ips(cls, v):
        """
        Valida que las listas de IPs sean JSON válidos.
        """
        if v is not None:
            try:
                ips = json.loads(v)
                if not isinstance(ips, list):
                    raise ValueError("Debe ser un array JSON de IPs.")
                
                # Validar formato básico de cada IP
                for ip in ips:
                    if not isinstance(ip, str) or not ip.strip():
                        raise ValueError("Cada IP debe ser una cadena no vacía.")
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido en lista de IPs: {str(e)}")
        return v

    @validator('horario_acceso_config')
    def validar_horarios_acceso(cls, v):
        """
        Valida que la configuración de horarios sea JSON válido.
        """
        if v is not None:
            try:
                horarios = json.loads(v)
                if not isinstance(horarios, dict):
                    raise ValueError("Debe ser un objeto JSON con días y horarios.")
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido en horarios de acceso: {str(e)}")
        return v

    @field_validator('max_active_sessions')
    @classmethod
    def validar_sesiones_activas(cls, v: int) -> int:
        """
        Valida que el máximo de sesiones activas sea razonable.
        """
        if v < 0:
            raise ValueError("El máximo de sesiones activas no puede ser negativo.")
        if v > 50:
            raise ValueError("El máximo de sesiones activas no puede exceder 50.")
        return v

    class Config:
        from_attributes = True


class AuthConfigCreate(AuthConfigBase):
    """
    Esquema para la creación de una nueva configuración de autenticación.
    Incluye el ID del cliente al que pertenece la configuración.
    """
    cliente_id: int = Field(..., description="ID del cliente dueño de esta configuración.")


class AuthConfigUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una configuración de autenticación.
    Todos los campos son opcionales para permitir actualizaciones incrementales.
    """
    password_min_length: Optional[int] = None
    password_require_uppercase: Optional[bool] = None
    password_require_lowercase: Optional[bool] = None
    password_require_number: Optional[bool] = None
    password_require_special: Optional[bool] = None
    password_expiry_days: Optional[int] = None
    password_history_count: Optional[int] = None
    max_login_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None
    max_active_sessions: Optional[int] = None
    session_idle_timeout_minutes: Optional[int] = None
    access_token_minutes: Optional[int] = None
    refresh_token_days: Optional[int] = None
    allow_remember_me: Optional[bool] = None
    remember_me_days: Optional[int] = None
    require_email_verification: Optional[bool] = None
    allow_password_reset: Optional[bool] = None
    enable_2fa: Optional[bool] = None
    require_2fa_for_admins: Optional[bool] = None
    metodos_2fa_permitidos: Optional[str] = None
    ip_whitelist_enabled: Optional[bool] = None
    ip_whitelist: Optional[str] = None
    ip_blacklist: Optional[str] = None
    horario_acceso_enabled: Optional[bool] = None
    horario_acceso_config: Optional[str] = None

    class Config:
        from_attributes = True


class AuthConfigRead(AuthConfigBase):
    """
    Esquema de lectura completo de una configuración de autenticación.
    Incluye campos de identificación y auditoría generados por el sistema.
    """
    config_id: int = Field(..., description="Identificador único de la configuración.")
    cliente_id: int = Field(..., description="ID del cliente dueño de esta configuración.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización.")

    class Config:
        from_attributes = True


class AuthConfigConEstadisticas(AuthConfigRead):
    """
    Esquema extendido que incluye estadísticas de seguridad del cliente.
    Útil para dashboards de administración y auditoría de seguridad.
    """
    total_usuarios: int = Field(0, description="Total de usuarios del cliente.")
    usuarios_con_2fa: int = Field(0, description="Usuarios con 2FA habilitado.")
    bloqueos_ultima_semana: int = Field(0, description="Cuentas bloqueadas en la última semana.")
    intentos_fallidos_ultimo_mes: int = Field(0, description="Intentos de login fallidos en el último mes.")
    promedio_sesiones_activas: Optional[float] = Field(
        None, 
        description="Promedio de sesiones activas simultáneas."
    )
    cumplimiento_politicas: Optional[float] = Field(
        None, 
        description="Porcentaje de cumplimiento de políticas de seguridad (0-100)."
    )
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# --- Enumeración de Proveedores SSO ---

class SsoProvider(str, Enum):
    """Proveedores de identidad soportados para la federación."""
    AZURE_AD = "AZURE_AD"
    GOOGLE = "GOOGLE_WORKSPACE"
    OKTA = "OKTA"
    CUSTOM = "CUSTOM_SAML_OIDC"

# --- Sub-Schemas para Configuraciones Específicas SSO ---

class SSOConfigAzure(BaseModel):
    """Configuración específica para Azure Active Directory."""
    tenant_id: str = Field(..., description="ID del Inquilino (Tenant ID) de Azure AD.")
    client_id: str = Field(..., description="ID de la Aplicación (Client ID) registrado en Azure.")
    client_secret: Optional[str] = Field(None, description="Secreto de la Aplicación (Client Secret).")
    scope: str = Field("openid profile email", description="Scopes solicitados (ej: openid profile email).")
    allowed_domains: List[str] = Field([], description="Dominios de correo permitidos para el login.")
    
    class Config:
        from_attributes = True

class SSOConfigGoogle(BaseModel):
    """Configuración específica para Google Workspace/Google Identity Platform."""
    client_id: str = Field(..., description="ID de Cliente de OAuth 2.0 de Google.")
    client_secret: Optional[str] = Field(None, description="Secreto de Cliente de OAuth 2.0.")
    hosted_domain: Optional[str] = Field(None, description="Dominio de Google Workspace para restringir el acceso.")
    allowed_domains: List[str] = Field([], description="Dominios de correo permitidos adicionales.")
    
    class Config:
        from_attributes = True

# --- Esquemas Principales de Federación ---

class FederacionBase(BaseModel):
    """Esquema base para la creación y lectura de una configuración de federación."""
    proveedor: SsoProvider = Field(..., description="Proveedor de identidad.")
    es_activo: bool = Field(True, description="Indica si esta configuración de federación está activa.")
    
    class Config:
        from_attributes = True

class FederacionCreate(FederacionBase):
    """Esquema para crear una nueva configuración de federación."""
    configuracion: dict = Field(..., description="Configuración detallada del proveedor (JSON/dict).")

class FederacionUpdate(FederacionBase):
    """Esquema para actualizar una configuración de federación. Todos los campos son opcionales."""
    proveedor: Optional[SsoProvider] = None
    es_activo: Optional[bool] = None
    configuracion: Optional[dict] = Field(None, description="Configuración detallada (opcional).")

class FederacionRead(FederacionBase):
    """Esquema de lectura para una configuración de federación."""
    federacion_id: int = Field(..., description="ID único de la configuración de federación.")
    cliente_id: int = Field(..., description="ID del cliente al que pertenece esta configuración.")
    configuracion_json: dict = Field(..., alias="configuracion", description="Configuración detallada del proveedor (JSON).") 
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True
