# app/schemas/rol.py
"""
Esquemas Pydantic para la gestión de roles y permisos del sistema,
adaptados para la arquitectura **multi-tenant**.

Este módulo define todos los esquemas de validación, creación, actualización 
y lectura de roles y sus permisos asociados sobre menús.

Características principales:
- CRÍTICO: Inclusión del campo cliente_id (opcional) para roles de sistema vs cliente.
- Campo codigo_rol para identificar roles inmutables del sistema.
- Validaciones robustas con mensajes de error en español
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

class RolBase(BaseModel):
    """
    Schema base para roles con validaciones fundamentales,
    adaptado a la estructura multi-tenant.
    """
    
    # === CRÍTICO: MULTI-TENANT AWARENESS ===
    cliente_id: Optional[UUID] = Field(
        None,
        description="Identificador único del cliente/tenant (UUID). NULL para roles de sistema globales e inmutables."
    )
    
    codigo_rol: Optional[str] = Field(
        None,
        max_length=50,
        description="Código único en MAYÚSCULAS para roles predefinidos por el sistema (ej: 'SUPER_ADMIN', 'ADMIN'). NULL para roles definidos por el cliente."
    )
    
    # === DATOS BÁSICOS ===
    nombre: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre único del rol para identificación en el sistema (único por cliente_id)",
        examples=["Administrador", "Usuario", "Supervisor", "Reportes"]
    )
    
    descripcion: Optional[str] = Field(
        None,
        max_length=255,
        description="Descripción detallada del propósito y permisos del rol",
        examples=["Acceso completo al sistema", "Usuario estándar con permisos básicos"]
    )
    
    es_activo: bool = Field(
        True,
        description="Indica si el rol está activo y disponible para asignación"
    )

    # === VALIDATORS ===
    @field_validator('codigo_rol')
    @classmethod
    def validar_formato_codigo_rol(cls, valor: Optional[str]) -> Optional[str]:
        """
        Valida que el código del rol (si existe) esté en mayúsculas y contenga solo letras y guiones bajos.
        """
        if valor is None:
            return None
            
        valor = valor.strip().upper()
        
        if not valor:
            return None
        
        # Validar formato: solo letras, números y guiones bajos
        if not re.match(r'^[A-Z0-9_]+$', valor):
            raise ValueError(
                'El código del rol solo puede contener letras mayúsculas, números y guiones bajos (_). '
                'No se permiten espacios ni caracteres especiales.'
            )
            
        if len(valor) < 3:
            raise ValueError('El código del rol debe tener al menos 3 caracteres')
            
        return valor

    @field_validator('nombre')
    @classmethod
    def validar_formato_nombre_rol(cls, valor: str) -> str:
        """Valida que el nombre del rol tenga un formato válido."""
        if not valor:
            raise ValueError('El nombre del rol no puede estar vacío')
        
        valor = valor.strip()
        
        if not valor:
            raise ValueError('El nombre del rol no puede contener solo espacios')
        
        if len(valor) < 3 or len(valor) > 50:
            raise ValueError(f'El nombre del rol debe tener entre 3 y 50 caracteres (actual: {len(valor)})')
        
        patron_permitido = r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.,\-_()/!?@#$%&*+:=;'\"»«]+$"
        
        if not re.match(patron_permitido, valor):
            raise ValueError(
                'El nombre del rol contiene caracteres no permitidos. '
                'Solo se permiten letras, números, espacios y los siguientes caracteres especiales: '
                '.,-_()/!?@#$%&*+:=;\'"»«'
            )
        
        if re.match(r"^[\s\.,\-_()/!?@#$%&*+:=;'\"]+$", valor):
            raise ValueError('El nombre del rol debe contener texto significativo, no solo caracteres especiales')
        
        return valor.title()

    @field_validator('descripcion')
    @classmethod
    def validar_descripcion_rol(cls, valor: Optional[str]) -> Optional[str]:
        """Valida el formato y contenido de la descripción del rol."""
        if valor is None:
            return None
        
        valor = valor.strip()
        
        if not valor:
            return None
        
        if len(valor) > 255:
            raise ValueError('La descripción no puede exceder los 255 caracteres')
        
        patron_descripcion = r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.,;:\-\_\(\)\!\?\@\#\$\%\&\*\+\=\[\]\{\}\"\'»«]+$"
        
        if not re.match(patron_descripcion, valor):
            raise ValueError(
                'La descripción contiene caracteres no permitidos. '
                'Solo se permiten letras, números, espacios y signos de puntuación comunes.'
            )
        
        return valor

    @model_validator(mode='after')
    def validar_consistencia_nombre_rol(self) -> 'RolBase':
        """
        Valida consistencias adicionales después de procesar todos los campos.
        
        CRÍTICO: Validar que un rol de sistema (con codigo_rol) NO tenga cliente_id asignado, o viceversa.
        """
        # ⚠️ Nota: La validación de cliente_id=1 para SUPER ADMIN debe hacerse en el servicio
        # ya que ahora cliente_id es UUID y no podemos comparar directamente con 1
        
        # ✅ CORRECCIÓN: En BD dedicadas, los roles pueden tener codigo_rol pero cliente_id NULL o UUID nulo
        # Validar que un rol de sistema (con codigo_rol) NO tenga cliente_id asignado (excepto NULL o UUID nulo)
        from uuid import UUID
        
        cliente_id_valido = self.cliente_id
        if cliente_id_valido is not None:
            # Convertir a UUID si es string para comparar
            if isinstance(cliente_id_valido, str):
                try:
                    cliente_id_valido = UUID(cliente_id_valido)
                except (ValueError, AttributeError):
                    cliente_id_valido = None
            elif not isinstance(cliente_id_valido, UUID):
                cliente_id_valido = None
            
            # Verificar si es UUID nulo
            if isinstance(cliente_id_valido, UUID) and cliente_id_valido == UUID('00000000-0000-0000-0000-000000000000'):
                cliente_id_valido = None
        
        # Solo validar si cliente_id no es None y no es UUID nulo
        if self.codigo_rol is not None and cliente_id_valido is not None:
            raise ValueError(
                'Un rol de sistema (con código de rol) no puede tener cliente_id asignado. '
                'Los roles de sistema son globales y no pertenecen a un cliente específico.'
            )
        
        # Si no tiene código de rol y no tiene cliente_id, es un error, debe ser rol de sistema o de cliente.
        # Asumimos que si no hay cliente_id, es un rol global que *debería* tener un codigo_rol.
        # Permitimos la creación de roles de cliente sin codigo_rol (cliente_id != NULL).
        if self.codigo_rol is None and self.cliente_id is None:
            raise ValueError(
                'El rol debe tener un código de rol (si es rol de sistema) o un cliente_id (si es rol de cliente). '
                'No puede estar vacío en ambos campos.'
            )
            
        return self

class RolCreate(RolBase):
    """
    Schema para la creación de nuevos roles.
    """
    pass

class RolUpdate(BaseModel):
    """
    Schema para actualización parcial de roles.
    
    Todos los campos son opcionales.
    """
    
    nombre: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="Nuevo nombre del rol (opcional)"
    )
    
    descripcion: Optional[str] = Field(
        None,
        max_length=255,
        description="Nueva descripción del rol (opcional)"
    )
    
    es_activo: Optional[bool] = Field(
        None,
        description="Nuevo estado activo/inactivo del rol (opcional)"
    )
    
    # Nota: cliente_id y codigo_rol generalmente no se actualizan en un PATCH normal
    # Sin embargo, se incluyen aquí como referencia si fuera necesario por lógica de negocio específica.
    codigo_rol: Optional[str] = Field(
        None,
        max_length=50,
        description="Código del rol (solo actualizable por SUPER_ADMIN en roles de sistema)."
    )

    # Reutilizar validadores específicos para campos opcionales
    _validar_nombre_rol = field_validator('nombre')(RolBase.validar_formato_nombre_rol.__func__)
    _validar_descripcion = field_validator('descripcion')(RolBase.validar_descripcion_rol.__func__)

class RolRead(RolBase):
    """
    Schema para lectura de datos básicos de un rol, incluyendo la identificación
    multi-tenant.
    """
    
    rol_id: UUID = Field(
        ...,
        description="Identificador único del rol en el sistema (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    fecha_creacion: datetime = Field(
        ...,
        description="Fecha y hora en que se creó el registro del rol"
    )
    
    es_eliminado: bool = Field(
        False,
        description="Indicador de borrado lógico."
    )

    class Config:
        """Configuración de Pydantic para el schema."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True

# Los siguientes esquemas no requieren cambios, pero se incluyen para el código completo

class PaginatedRolResponse(BaseModel):
    """
    Schema para respuestas paginadas de listas de roles.
    """
    
    roles: List[RolRead] = Field(
        ...,
        description="Lista de roles para la página actual"
    )
    
    total_roles: int = Field(
        ...,
        ge=0,
        description="Número total de roles que coinciden con los filtros aplicados"
    )
    
    pagina_actual: int = Field(
        ...,
        ge=1,
        description="Número de la página actual siendo visualizada"
    )
    
    total_paginas: int = Field(
        ...,
        ge=0,
        description="Número total de páginas disponibles con los filtros actuales"
    )

    class Config:
        """Configuración para respuestas paginadas."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PermisoBase(BaseModel):
    """
    Schema base para permisos de roles sobre menús.
    """
    
    menu_id: UUID = Field(
        ...,
        description="ID del menú al que aplican los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    puede_ver: bool = Field(
        default=True,
        description="Permiso para ver/acceder al menú",
        examples=[True, False]
    )
    
    puede_editar: bool = Field(
        default=False,
        description="Permiso para editar contenido asociado al menú",
        examples=[True, False]
    )
    
    puede_eliminar: bool = Field(
        default=False,
        description="Permiso para eliminar contenido asociado al menú",
        examples=[True, False]
    )
    
    # ⚠️ UUID no requiere validación de positivos, Pydantic valida formato automáticamente

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

class PermisoRead(PermisoBase):
    """
    Schema para lectura de permisos existentes.
    """
    
    rol_menu_id: UUID = Field(
        ...,
        description="ID único del registro de permiso en la tabla de relación (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    rol_id: UUID = Field(
        ...,
        description="ID del rol al que pertenece el permiso (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440001"]
    )

class PermisoUpdatePayload(BaseModel):
    """
    Schema para actualización masiva de permisos de un rol.
    """
    
    permisos: List[PermisoBase] = Field(
        ...,
        description="Lista completa de permisos para asignar al rol",
        examples=[[
            {"menu_id": 1, "puede_ver": True, "puede_editar": False, "puede_eliminar": False},
            {"menu_id": 2, "puede_ver": True, "puede_editar": True, "puede_eliminar": False}
        ]]
    )

    @field_validator('permisos')
    @classmethod
    def validar_permisos_no_vacios(cls, valor: List[PermisoBase]) -> List[PermisoBase]:
        """Valida que la lista de permisos no esté vacía cuando se proporciona."""
        if not valor:
            raise ValueError('La lista de permisos no puede estar vacía')
        
        return valor

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )# app/schemas/rol_menu_permiso.py
"""
Esquemas Pydantic para la gestión de permisos de roles sobre menús en el sistema.

Este módulo define todos los esquemas de validación, creación, actualización 
y lectura de los permisos específicos que los roles tienen sobre los menús.

Los permisos rol-menú permiten controlar granularmente qué acciones puede realizar
cada rol sobre cada menú del sistema, proporcionando un control de acceso detallado.

Características principales:
- Validaciones robustas con mensajes de error en español
- Gestión completa de permisos rol-menú
- Validación de existencia de roles y menús
- Control granular de permisos (ver, editar, eliminar)
- Documentación clara para desarrolladores
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any

class RolMenuPermisoBase(BaseModel):
    """
    Schema base para permisos rol-menú con validaciones fundamentales.
    
    Define la estructura básica de un permiso rol-menú y establece 
    las reglas de validación esenciales para mantener la seguridad del sistema.
    """
    
    rol_id: UUID = Field(
        ...,
        description="ID del rol al que se asignan los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    menu_id: UUID = Field(
        ...,
        description="ID del menú sobre el que se aplican los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440001"]
    )
    
    puede_ver: bool = Field(
        True,
        description="Permiso para visualizar/acceder al menú",
        examples=[True, False]
    )
    
    puede_editar: bool = Field(
        False,
        description="Permiso para editar contenido asociado al menú",
        examples=[True, False]
    )
    
    puede_eliminar: bool = Field(
        False,
        description="Permiso para eliminar contenido asociado al menú",
        examples=[True, False]
    )
    
    # ⚠️ UUID no requiere validación de positivos, Pydantic valida formato automáticamente

    @model_validator(mode='after')
    def validar_consistencia_permisos(self) -> 'RolMenuPermisoBase':
        """
        Valida consistencias adicionales después de procesar todos los campos.
        
        Realiza validaciones que requieren múltiples campos o que dependen
        de transformaciones realizadas en validadores individuales.
        """
        # Validar que si puede_editar o puede_eliminar es True, entonces puede_ver debe ser True
        if (self.puede_editar or self.puede_eliminar) and not self.puede_ver:
            raise ValueError(
                'No se pueden conceder permisos de edición o eliminación sin permiso de visualización. '
                'El permiso "puede_ver" debe ser True cuando "puede_editar" o "puede_eliminar" son True.'
            )
        
        # Validar lógica de permisos: no debería poder eliminar sin poder editar
        if self.puede_eliminar and not self.puede_editar:
            raise ValueError(
                'No se puede conceder permiso de eliminación sin permiso de edición. '
                'El permiso "puede_editar" debe ser True cuando "puede_eliminar" es True.'
            )
        
        return self

class RolMenuPermisoCreate(RolMenuPermisoBase):
    """
    Schema para la creación de nuevos permisos rol-menú.
    
    Extiende RolMenuPermisoBase sin agregar campos adicionales, pero se utiliza
    para documentar específicamente la operación de creación.
    """
    pass

class RolMenuPermisoUpdate(BaseModel):
    """
    Schema para actualización parcial de permisos rol-menú.
    
    Todos los campos son opcionales y solo se validan los que se proporcionen.
    Diseñado específicamente para operaciones PATCH que actualizan solo
    algunos permisos específicos.
    """
    
    puede_ver: Optional[bool] = Field(
        None,
        description="Nuevo permiso de visualización (opcional)",
        examples=[True, False]
    )
    
    puede_editar: Optional[bool] = Field(
        None,
        description="Nuevo permiso de edición (opcional)",
        examples=[True, False]
    )
    
    puede_eliminar: Optional[bool] = Field(
        None,
        description="Nuevo permiso de eliminación (opcional)",
        examples=[True, False]
    )

    @model_validator(mode='after')
    def validar_consistencia_permisos_parciales(self) -> 'RolMenuPermisoUpdate':
        """
        Valida consistencias en actualizaciones parciales de permisos.
        
        Aplica las mismas reglas de negocio que el validador base, pero
        considerando que algunos campos pueden ser None (no actualizados).
        """
        # Solo validar si todos los campos relevantes están presentes
        puede_ver = self.puede_ver
        puede_editar = self.puede_editar
        puede_eliminar = self.puede_eliminar
        
        # Si se está actualizando editar o eliminar, verificar que ver sea True
        if (puede_editar is not None and puede_editar) or (puede_eliminar is not None and puede_eliminar):
            if puede_ver is not None and not puede_ver:
                raise ValueError(
                    'No se pueden conceder permisos de edición o eliminación sin permiso de visualización. '
                    'El permiso "puede_ver" debe ser True cuando "puede_editar" o "puede_eliminar" son True.'
                )
        
        # Si se está actualizando eliminar, verificar que editar sea True
        if puede_eliminar is not None and puede_eliminar:
            if puede_editar is not None and not puede_editar:
                raise ValueError(
                    'No se puede conceder permiso de eliminación sin permiso de edición. '
                    'El permiso "puede_editar" debe ser True cuando "puede_eliminar" es True.'
                )
        
        return self

class RolMenuPermisoRead(RolMenuPermisoBase):
    """
    Schema para lectura de datos completos de un permiso rol-menú.
    
    Incluye todos los campos de RolMenuPermisoBase más el identificador
    único del registro de permiso en el sistema.
    """
    
    rol_menu_id: UUID = Field(
        ...,
        description="Identificador único del permiso rol-menú en el sistema (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    class Config:
        """Configuración de Pydantic para el schema."""
        from_attributes = True
        str_strip_whitespace = True
        validate_assignment = True

class RolMenuPermisoReadWithDetails(RolMenuPermisoRead):
    """
    Schema extendido para lectura de permisos rol-menú con detalles adicionales.
    
    Incluye información descriptiva del rol y menú para facilitar
    la comprensión en interfaces de administración.
    """
    
    rol_nombre: Optional[str] = Field(
        None,
        description="Nombre del rol asociado",
        examples=["Administrador", "Usuario", "Supervisor"]
    )
    
    rol_descripcion: Optional[str] = Field(
        None,
        description="Descripción del rol asociado",
        examples=["Acceso completo al sistema", "Usuario con permisos básicos"]
    )
    
    menu_nombre: Optional[str] = Field(
        None,
        description="Nombre del menú asociado",
        examples=["Dashboard", "Usuarios", "Configuración"]
    )
    
    menu_ruta: Optional[str] = Field(
        None,
        description="Ruta del menú asociado",
        examples=["/dashboard", "/usuarios", "/configuracion"]
    )
    
    menu_icono: Optional[str] = Field(
        None,
        description="Icono del menú asociado",
        examples=["dashboard", "users", "settings"]
    )

    class Config:
        """Configuración para respuestas extendidas."""
        from_attributes = True

class RolMenuPermisoBulkUpdate(BaseModel):
    """
    Schema para actualización masiva de permisos rol-menú.
    
    Utilizado en operaciones que actualizan múltiples permisos
    simultáneamente para un rol específico.
    """
    
    permisos: dict[UUID, Dict[str, bool]] = Field(
        ...,
        description="Diccionario donde las claves son menu_id (UUID) y los valores son diccionarios de permisos",
        examples=[{
            "550e8400-e29b-41d4-a716-446655440000": {"puede_ver": True, "puede_editar": False, "puede_eliminar": False},
            "550e8400-e29b-41d4-a716-446655440001": {"puede_ver": True, "puede_editar": True, "puede_eliminar": False},
            "550e8400-e29b-41d4-a716-446655440002": {"puede_ver": False, "puede_editar": False, "puede_eliminar": False}
        }]
    )

    @field_validator('permisos')
    @classmethod
    def validar_permisos_masivos(cls, valor: dict[UUID, Dict[str, bool]]) -> dict[UUID, Dict[str, bool]]:
        """
        Valida la estructura y consistencia de los permisos masivos.
        
        Args:
            valor: Diccionario de permisos a validar
            
        Returns:
            dict: Diccionario de permisos validado
            
        Raises:
            ValueError: Cuando la estructura o valores no son válidos
        """
        if not valor:
            raise ValueError('El diccionario de permisos no puede estar vacío')
        
        for menu_id, permisos in valor.items():
            # ⚠️ UUID no requiere validación de positivos, Pydantic valida formato automáticamente
            
            # Validar estructura de permisos
            permisos_requeridos = {'puede_ver', 'puede_editar', 'puede_eliminar'}
            if not all(permiso in permisos for permiso in permisos_requeridos):
                raise ValueError(f'Faltan permisos requeridos para el menú {menu_id}')
            
            # Validar tipos de permisos
            for permiso_nombre, permiso_valor in permisos.items():
                if not isinstance(permiso_valor, bool):
                    raise ValueError(f'El permiso {permiso_nombre} para el menú {menu_id} debe ser booleano')
            
            # Validar lógica de permisos
            puede_ver = permisos.get('puede_ver', False)
            puede_editar = permisos.get('puede_editar', False)
            puede_eliminar = permisos.get('puede_eliminar', False)
            
            if (puede_editar or puede_eliminar) and not puede_ver:
                raise ValueError(
                    f'No se pueden conceder permisos de edición o eliminación sin permiso de '
                    f'visualización para el menú {menu_id}'
                )
            
            if puede_eliminar and not puede_editar:
                raise ValueError(
                    f'No se puede conceder permiso de eliminación sin permiso de edición '
                    f'para el menú {menu_id}'
                )
        
        return valor

    class Config:
        """Configuración para actualizaciones masivas."""
        from_attributes = True

class RolMenuPermisoSummary(BaseModel):
    """
    Schema para resumen de permisos de un rol.
    
    Utilizado en respuestas que requieren un resumen rápido de los permisos
    de un rol específico sin todos los detalles.
    """
    
    rol_id: UUID = Field(
        ...,
        description="ID del rol (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    rol_nombre: str = Field(
        ...,
        description="Nombre del rol",
        examples=["Administrador", "Usuario", "Supervisor"]
    )
    
    total_permisos: int = Field(
        ...,
        description="Número total de permisos asignados al rol",
        examples=[5, 10, 15]
    )
    
    permisos_activos: int = Field(
        ...,
        description="Número de permisos con al menos puede_ver=True",
        examples=[3, 8, 12]
    )
    
    puede_editar_count: int = Field(
        ...,
        description="Número de permisos con puede_editar=True",
        examples=[2, 5, 8]
    )
    
    puede_eliminar_count: int = Field(
        ...,
        description="Número de permisos con puede_eliminar=True",
        examples=[1, 3, 5]
    )

    class Config:
        """Configuración para resúmenes."""
        from_attributes = True
