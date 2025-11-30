# app/schemas/usuario.py
"""
Esquemas Pydantic para la gestión de usuarios en el sistema.

Este módulo define todos los esquemas de validación, creación, actualización 
y lectura de usuarios, incluyendo validaciones de negocio y seguridad,
adaptados para la arquitectura **multi-tenant** y compatible con la estructura REAL de la BD.

Características principales:
- CRÍTICO: Inclusión del campo cliente_id para aislamiento de datos.
- Compatibilidad TOTAL con la estructura real de la base de datos.
- Validaciones robustas con mensajes de error en español.
- Seguridad en el manejo de contraseñas.
- Documentación clara para desarrolladores.
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import re

# Importar schema de roles para relaciones
from app.modules.rbac.presentation.schemas import RolRead

class UsuarioBase(BaseModel):
    """
    Schema base para usuarios con validaciones fundamentales,
    incluyendo el campo crítico de aislamiento multi-tenant.
    """
    
    # === CRÍTICO: MULTI-TENANT AWARENESS ===
    cliente_id: int = Field(
        ...,
        description="Identificador único del cliente/tenant al que pertenece el usuario. Obligatorio para el aislamiento.",
        examples=[1, 10]
    )
    
    # === DATOS BÁSICOS ===
    nombre_usuario: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nombre único de usuario para identificación en el sistema (único por cliente). Puede ser username, DNI, email o código.",
        examples=["juan_perez", "42799662", "usuario@empresa.com", "EMP001"]
    )
    
    correo: Optional[str] = Field(
        None,
        max_length=150,
        description="Dirección de correo electrónico válida (puede ser diferente de nombre_usuario)",
        examples=["usuario@empresa.com", "nombre.apellido@dominio.org"]
    )
    
    nombre: Optional[str] = Field(
        None,
        max_length=100,
        description="Nombre real del usuario (solo letras y espacios)",
        examples=["Juan", "María José"]
    )
    
    apellido: Optional[str] = Field(
        None, 
        max_length=100,
        description="Apellido del usuario (solo letras y espacios)",
        examples=["Pérez García", "López"]
    )
    
    es_activo: bool = Field(
        True,
        description="Indica si el usuario está activo en el sistema"
    )

    # === CAMPOS DE SEGURIDAD ===
    es_superadmin: bool = Field(
        False,
        description="Indica si el usuario es un superadministrador global del sistema (solo cliente_id=1)."
    )

    # === VALIDATORS REUTILIZADOS ===
    @field_validator('nombre_usuario')
    @classmethod
    def validar_formato_nombre_usuario(cls, valor: str) -> str:
        """Valida que el nombre de usuario tenga un formato válido."""
        if not valor:
            raise ValueError('El nombre de usuario no puede estar vacío')
        
        valor = valor.strip()
        
        if not valor:
            raise ValueError('El nombre de usuario no puede contener solo espacios')
        
        # Validación más flexible para permitir DNI, emails, códigos
        if not re.match(r'^[a-zA-Z0-9@._-]+$', valor):
            raise ValueError(
                'El nombre de usuario solo puede contener letras, números, @, ., _ y -. '
                'No se permiten espacios ni otros caracteres especiales.'
            )
        
        if len(valor) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres')
        
        return valor

    @field_validator('correo')
    @classmethod
    def validar_formato_correo(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida un formato básico de correo electrónico.
        Solo verifica la presencia de un '@' y un punto en la parte del dominio.
        """
        if valor is None or valor == "":
            return None
        
        valor = valor.strip()
        
        if not valor:
            return None
            
        # Validación básica: debe contener '@' y al menos un '.' después del '@'
        if '@' not in valor:
            raise ValueError('El correo debe contener un símbolo "@"')
            
        local, dominio = valor.split('@', 1)
        
        if not local:
            raise ValueError('El correo debe tener una parte local antes del "@"')
            
        if not dominio or '.' not in dominio:
            raise ValueError('El dominio del correo debe contener al menos un punto "."')
        
        return valor.lower()

    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre_apellido(cls, valor: Optional[str]) -> Optional[str]:
        """Valida que nombres y apellidos contengan solo caracteres alfabéticos válidos."""
        if valor is None or valor == "":
            return None
        
        valor = valor.strip()
        
        if not valor:
            return None
        
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', valor):
            raise ValueError(
                'El nombre y apellido solo pueden contener letras, espacios y guiones. '
                'No se permiten números ni caracteres especiales.'
            )
        
        if valor.replace(' ', '').replace('-', '') == '':
            raise ValueError('El nombre no puede contener solo espacios o guiones')
        
        return valor.title()

class UsuarioCreate(UsuarioBase):
    """
    Schema para la creación de nuevos usuarios.
    
    Requiere contraseña y utiliza la validación de UsuarioBase.
    """
    
    contrasena: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Contraseña segura con mínimo 8 caracteres, una mayúscula, una minúscula y un número",
        examples=["MiContraseñaSegura123", "OtraPassword123!"]
    )
    
    # Campos opcionales adicionales de tu BD
    dni: Optional[str] = Field(
        None,
        max_length=8,
        description="DNI del usuario (solo para registro, no para login)",
        examples=["42799662", "12345678"]
    )
    
    telefono: Optional[str] = Field(
        None,
        max_length=20,
        description="Número de teléfono del usuario",
        examples=["+51987654321", "012345678"]
    )
    
    proveedor_autenticacion: str = Field(
        'local',
        max_length=30,
        description="Método de autenticación: 'local', 'azure_ad', 'google', 'okta', 'oidc', 'saml'"
    )

    @field_validator('contrasena')
    @classmethod
    def validar_fortaleza_contrasena(cls, valor: str) -> str:
        """Valida que la contraseña cumpla con las políticas de seguridad."""
        if len(valor) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        errores = []
        
        if not any(c.isupper() for c in valor):
            errores.append('al menos una letra mayúscula')
            
        if not any(c.islower() for c in valor):
            errores.append('al menos una letra minúscula')
            
        if not any(c.isdigit() for c in valor):
            errores.append('al menos un número')
        
        if errores:
            raise ValueError(
                f'La contraseña no cumple con los requisitos de seguridad. '
                f'Debe contener: {", ".join(errores)}.'
            )
            
        return valor

    @field_validator('dni')
    @classmethod
    def validar_dni(cls, valor: Optional[str]) -> Optional[str]:
        """Valida el formato del DNI."""
        if valor is None or valor == "":
            return None
            
        valor = valor.strip()
        
        if not valor.isdigit():
            raise ValueError('El DNI debe contener solo números')
            
        if len(valor) != 8:
            raise ValueError('El DNI debe tener exactamente 8 dígitos')
            
        return valor

class UsuarioUpdate(BaseModel):
    """
    Schema para actualización parcial de usuarios (PATCH).
    
    Todos los campos son opcionales y solo se validan los que se proporcionen.
    """
    
    nombre_usuario: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Nuevo nombre de usuario (opcional)"
    )
    
    correo: Optional[str] = Field(
        None,
        max_length=150,
        description="Nueva dirección de correo electrónico (opcional)"
    )
    
    nombre: Optional[str] = Field(
        None,
        max_length=100,
        description="Nuevo nombre (opcional)"
    )
    
    apellido: Optional[str] = Field(
        None,
        max_length=100, 
        description="Nuevo apellido (opcional)"
    )
    
    es_activo: Optional[bool] = Field(
        None,
        description="Nuevo estado activo/inactivo (opcional)"
    )
    
    dni: Optional[str] = Field(
        None,
        max_length=8,
        description="Nuevo DNI (opcional)"
    )
    
    telefono: Optional[str] = Field(
        None,
        max_length=20,
        description="Nuevo teléfono (opcional)"
    )
    
    # Nuevo campo para actualizar el estado de superadministrador (solo accesible para SUPER_ADMIN)
    es_superadmin: Optional[bool] = Field(
        None,
        description="Nuevo estado de superadministrador (opcional)"
    )

    # Reutilizar validadores específicos para campos opcionales
    _validar_nombre_usuario = field_validator('nombre_usuario')(UsuarioBase.validar_formato_nombre_usuario.__func__)
    _validar_correo = field_validator('correo')(UsuarioBase.validar_formato_correo.__func__)
    _validar_nombre_apellido = field_validator('nombre', 'apellido')(UsuarioBase.validar_nombre_apellido.__func__)
    _validar_dni = field_validator('dni')(UsuarioCreate.validar_dni.__func__)

class UsuarioRead(UsuarioBase):
    """
    Schema para lectura de datos completos de usuario.
    
    Incluye todos los campos de UsuarioBase más metadatos del sistema, seguridad
    y campos de sincronización COMPATIBLES con la estructura REAL de la BD.
    """
    
    usuario_id: int = Field(
        ...,
        description="Identificador único del usuario en el sistema"
    )
    
    fecha_creacion: datetime = Field(
        ...,
        description="Fecha y hora en que se creó el registro del usuario"
    )
    
    fecha_ultimo_acceso: Optional[datetime] = Field(
        None,
        description="Fecha y hora del último acceso del usuario al sistema"
    )
    
    correo_confirmado: Optional[bool] = Field(
        False,
        description="Indica si el usuario ha confirmado su dirección de correo electrónico"
    )
    
    # === CAMPOS DE SEGURIDAD DE TU BD REAL ===
    proveedor_autenticacion: str = Field(
        'local',
        description="Método de autenticación del usuario"
    )
    
    fecha_ultimo_cambio_contrasena: Optional[datetime] = Field(
        None,
        description="Fecha y hora del último cambio de contraseña"
    )
    
    requiere_cambio_contrasena: Optional[bool] = Field(
        False,
        description="Indica si el usuario debe cambiar la contraseña en el próximo login"
    )
    
    intentos_fallidos: Optional[int] = Field(
        0,
        description="Número de intentos de login fallidos consecutivos"
    )
    
    fecha_bloqueo: Optional[datetime] = Field(
        None,
        description="Fecha y hora en que la cuenta fue bloqueada"
    )
    
    # === CAMPOS DE SINCRONIZACIÓN DE TU BD REAL ===
    sincronizado_desde: Optional[str] = Field(
        None,
        description="Origen de la sincronización del usuario"
    )
    
    fecha_ultima_sincronizacion: Optional[datetime] = Field(
        None,
        description="Fecha de la última sincronización"
    )
    
    # === CAMPOS ADICIONALES DE TU BD REAL ===
    dni: Optional[str] = Field(
        None,
        description="DNI del usuario"
    )
    
    telefono: Optional[str] = Field(
        None,
        description="Teléfono del usuario"
    )
    
    referencia_externa_id: Optional[str] = Field(
        None,
        description="ID del usuario en proveedor externo de autenticación"
    )
    
    referencia_externa_email: Optional[str] = Field(
        None,
        description="Email del usuario en proveedor externo"
    )
    
    # === CAMPOS DE AUDITORÍA ===
    es_eliminado: bool = Field(
        False,
        description="Indicador de borrado lógico"
    )
    
    fecha_actualizacion: Optional[datetime] = Field(
        None,
        description="Fecha de última actualización del registro"
    )

    # === CAMPOS COMPATIBILIDAD (para mantener compatibilidad con código existente) ===
    origen_creacion: str = Field(
        default='local',
        description="Método de creación del usuario (compatibilidad)"
    )
    
    ultimo_cambio_contrasena: Optional[datetime] = Field(
        None,
        description="Fecha del último cambio de contraseña (compatibilidad)"
    )

    class Config:
        """Configuración de Pydantic para el schema."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True

class UsuarioReadWithRoles(UsuarioRead):
    """
    Schema extendido para lectura de usuario que incluye sus roles.
    
    Utilizado en endpoints que requieren información completa del usuario
    incluyendo los permisos y roles asignados.
    
    ✅ AHORA INCLUYE: Campos de niveles de acceso para el sistema LBAC
    """
    
    roles: List[RolRead] = Field(
        default_factory=list,
        description="Lista de roles activos asignados al usuario"
    )
    
    # ✅ AGREGAR CAMPOS DE NIVELES DE ACCESO (NUEVO)
    access_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Nivel de acceso máximo del usuario basado en sus roles (1-5)"
    )
    
    is_super_admin: bool = Field(
        default=False,
        description="Indica si el usuario tiene rol de Super Administrador (nivel 5)"
    )
    
    user_type: str = Field(
        default="user",
        description="Tipo de usuario: 'super_admin', 'tenant_admin', 'user'"
    )

    class Config:
        """Configuración de Pydantic para el schema extendido."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True

class PaginatedUsuarioResponse(BaseModel):
    """
    Schema para respuestas paginadas de listas de usuarios.
    
    Utilizado en endpoints que devuelven listas paginadas de usuarios
    con metadatos de paginación.
    """
    
    usuarios: List[UsuarioReadWithRoles] = Field(
        ...,
        description="Lista de usuarios para la página actual"
    )
    
    total_usuarios: int = Field(
        ...,
        ge=0,
        description="Número total de usuarios que coinciden con los filtros"
    )
    
    pagina_actual: int = Field(
        ...,
        ge=1,
        description="Número de la página actual siendo visualizada"
    )
    
    total_paginas: int = Field(
        ...,
        ge=0,
        description="Número total de páginas disponibles"
    )

    class Config:
        """Configuración para respuestas paginadas."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }# app/schemas/usuario_rol.py
"""
Esquemas Pydantic para la gestión de relaciones usuario-rol en el sistema.

Este módulo define todos los esquemas de validación, creación, actualización 
y lectura de las asignaciones entre usuarios y roles.

Las relaciones usuario-rol permiten asignar múltiples roles a un usuario
y gestionar los permisos de manera centralizada a través de los roles.

Características principales:
- Validaciones robustas con mensajes de error en español
- Gestión completa de asignaciones usuario-rol
- Validación de existencia de usuarios y roles
- Documentación clara para desarrolladores
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional

class UsuarioRolBase(BaseModel):
    """
    Schema base para relaciones usuario-rol con validaciones fundamentales.
    
    Define la estructura básica de una asignación usuario-rol y establece 
    las reglas de validación esenciales para mantener la integridad del sistema.
    """
    
    usuario_id: int = Field(
        ...,
        ge=1,
        description="ID del usuario al que se asigna el rol",
        examples=[1, 2, 3]
    )
    
    rol_id: int = Field(
        ...,
        ge=1,
        description="ID del rol que se asigna al usuario",
        examples=[1, 2, 3]
    )
    
    es_activo: bool = Field(
        True,
        description="Indica si la asignación usuario-rol está activa"
    )

    @field_validator('usuario_id')
    @classmethod
    def validar_usuario_id(cls, valor: int) -> int:
        """
        Valida que el ID del usuario sea un valor positivo.
        
        Args:
            valor: ID del usuario a validar
            
        Returns:
            int: ID del usuario validado
            
        Raises:
            ValueError: Cuando el ID no es positivo
        """
        if valor < 1:
            raise ValueError('El ID del usuario debe ser un número positivo mayor a 0')
        
        return valor

    @field_validator('rol_id')
    @classmethod
    def validar_rol_id(cls, valor: int) -> int:
        """
        Valida que el ID del rol sea un valor positivo.
        
        Args:
            valor: ID del rol a validar
            
        Returns:
            int: ID del rol validado
            
        Raises:
            ValueError: Cuando el ID no es positivo
        """
        if valor < 1:
            raise ValueError('El ID del rol debe ser un número positivo mayor a 0')
        
        return valor

    @model_validator(mode='after')
    def validar_consistencia_asignacion(self) -> 'UsuarioRolBase':
        """
        Valida consistencias adicionales después de procesar todos los campos.
        
        Realiza validaciones que requieren múltiples campos o que dependen
        de transformaciones realizadas en validadores individuales.
        """
        # Validar que no se asigne un usuario a sí mismo como rol (si fuera posible)
        # Esta validación es más conceptual ya que usuario_id y rol_id son de diferentes entidades
        
        # Podríamos añadir validaciones específicas de negocio aquí
        # Por ejemplo: verificar que no se asignen roles reservados a usuarios específicos
        
        return self

class UsuarioRolCreate(BaseModel):
    """
    Schema para la creación de nuevas asignaciones usuario-rol.
    
    Diseñado específicamente para operaciones de creación donde los IDs
    se obtienen de la ruta URL en lugar del cuerpo de la solicitud.
    """
    
    # Nota: En la implementación actual, los IDs vienen en la ruta URL
    # Este schema puede estar vacío o contener campos adicionales si es necesario
    
    es_activo: Optional[bool] = Field(
        True,
        description="Estado inicial de la asignación (por defecto activa)",
        examples=[True, False]
    )

class UsuarioRolUpdate(BaseModel):
    """
    Schema para actualización del estado de asignaciones usuario-rol.
    
    Utilizado específicamente para activar/desactivar asignaciones
    existentes sin modificar las relaciones fundamentales.
    """
    
    es_activo: bool = Field(
        ...,
        description="Nuevo estado activo/inactivo de la asignación",
        examples=[True, False]
    )

class UsuarioRolRead(UsuarioRolBase):
    """
    Schema para lectura de datos completos de una asignación usuario-rol.
    
    Incluye todos los campos de UsuarioRolBase más metadatos del sistema
    que se generan automáticamente durante la creación de la asignación.
    """
    
    usuario_rol_id: int = Field(
        ...,
        description="Identificador único de la asignación usuario-rol en el sistema",
        examples=[1, 2, 3]
    )
    
    fecha_asignacion: datetime = Field(
        ...,
        description="Fecha y hora en que se creó la asignación usuario-rol"
    )

    class Config:
        """Configuración de Pydantic para el schema."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True

class UsuarioRolResponse(BaseModel):
    """
    Schema para respuestas de operaciones usuario-rol con metadatos extendidos.
    
    Utilizado en respuestas que requieren información adicional sobre
    la asignación, como nombres de usuario y rol en lugar de solo IDs.
    """
    
    usuario_rol_id: int = Field(
        ...,
        description="ID único de la asignación",
        examples=[1, 2, 3]
    )
    
    usuario_id: int = Field(
        ...,
        description="ID del usuario",
        examples=[1, 2, 3]
    )
    
    nombre_usuario: Optional[str] = Field(
        None,
        description="Nombre de usuario asociado",
        examples=["juan_perez", "maria_garcia"]
    )
    
    rol_id: int = Field(
        ...,
        description="ID del rol",
        examples=[1, 2, 3]
    )
    
    nombre_rol: Optional[str] = Field(
        None,
        description="Nombre del rol asociado",
        examples=["Administrador", "Usuario", "Supervisor"]
    )
    
    es_activo: bool = Field(
        ...,
        description="Estado de la asignación",
        examples=[True, False]
    )
    
    fecha_asignacion: datetime = Field(
        ...,
        description="Fecha de creación de la asignación"
    )

    class Config:
        """Configuración para respuestas extendidas."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UsuarioRolBulkOperation(BaseModel):
    """
    Schema para operaciones masivas sobre asignaciones usuario-rol.
    
    Utilizado en operaciones que afectan múltiples asignaciones
    simultáneamente, como asignaciones/revocaciones por lote.
    """
    
    usuario_ids: list[int] = Field(
        ...,
        description="Lista de IDs de usuarios a afectar",
        examples=[[1, 2, 3], [4, 5, 6]]
    )
    
    rol_ids: list[int] = Field(
        ...,
        description="Lista de IDs de roles a asignar/revocar",
        examples=[[1, 2], [3, 4]]
    )
    
    operacion: str = Field(
        ...,
        description="Tipo de operación a realizar: 'asignar' o 'revocar'",
        examples=["asignar", "revocar"]
    )

    @field_validator('usuario_ids')
    @classmethod
    def validar_usuario_ids(cls, valor: list[int]) -> list[int]:
        """
        Valida que la lista de IDs de usuario contenga valores positivos.
        
        Args:
            valor: Lista de IDs de usuario a validar
            
        Returns:
            list[int]: Lista de IDs validada
            
        Raises:
            ValueError: Cuando algún ID no es válido
        """
        if not valor:
            raise ValueError('La lista de IDs de usuario no puede estar vacía')
        
        for usuario_id in valor:
            if usuario_id < 1:
                raise ValueError('Todos los IDs de usuario deben ser números positivos')
        
        return valor

    @field_validator('rol_ids')
    @classmethod
    def validar_rol_ids(cls, valor: list[int]) -> list[int]:
        """
        Valida que la lista de IDs de rol contenga valores positivos.
        
        Args:
            valor: Lista de IDs de rol a validar
            
        Returns:
            list[int]: Lista de IDs validada
            
        Raises:
            ValueError: Cuando algún ID no es válido
        """
        if not valor:
            raise ValueError('La lista de IDs de rol no puede estar vacía')
        
        for rol_id in valor:
            if rol_id < 1:
                raise ValueError('Todos los IDs de rol deben ser números positivos')
        
        return valor

    @field_validator('operacion')
    @classmethod
    def validar_operacion(cls, valor: str) -> str:
        """
        Valida que la operación sea una de las permitidas.
        
        Args:
            valor: Operación a validar
            
        Returns:
            str: Operación validada y normalizada
            
        Raises:
            ValueError: Cuando la operación no es válida
        """
        operaciones_permitidas = ['asignar', 'revocar']
        if valor not in operaciones_permitidas:
            raise ValueError(f'La operación debe ser una de: {", ".join(operaciones_permitidas)}')
        
        return valor

    class Config:
        """Configuración para operaciones masivas."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True
