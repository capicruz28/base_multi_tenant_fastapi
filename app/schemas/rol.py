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
import re

class RolBase(BaseModel):
    """
    Schema base para roles con validaciones fundamentales,
    adaptado a la estructura multi-tenant.
    """
    
    # === CRÍTICO: MULTI-TENANT AWARENESS ===
    cliente_id: Optional[int] = Field(
        None,
        description="Identificador único del cliente/tenant. NULL para roles de sistema globales e inmutables."
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
        if self.codigo_rol is not None and self.cliente_id is not None:
             if self.cliente_id != 1: # Permitir codigo_rol para el cliente SUPER ADMIN (ID=1)
                raise ValueError(
                    'Un rol con codigo_rol (rol de sistema) solo puede pertenecer al cliente SUPER ADMIN (cliente_id=1). '
                    'Para otros clientes, cree un rol de cliente (codigo_rol=NULL).'
                )
        elif self.codigo_rol is None and self.cliente_id is None:
            # Si no tiene código de rol y no tiene cliente_id, es un error, debe ser rol de sistema o de cliente.
            # Asumimos que si no hay cliente_id, es un rol global que *debería* tener un codigo_rol.
            # Permitimos la creación de roles de cliente sin codigo_rol (cliente_id != NULL).
            pass
            
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
    
    rol_id: int = Field(
        ...,
        description="Identificador único del rol en el sistema",
        examples=[1, 2, 3]
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
    
    menu_id: int = Field(
        ...,
        description="ID del menú al que aplican los permisos",
        examples=[1, 2, 3]
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

    @field_validator('menu_id')
    @classmethod
    def validar_menu_id(cls, valor: int) -> int:
        """Valida que el ID del menú sea un valor positivo."""
        if valor < 1:
            raise ValueError('El ID del menú debe ser un número positivo')
        
        return valor

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

class PermisoRead(PermisoBase):
    """
    Schema para lectura de permisos existentes.
    """
    
    rol_menu_id: int = Field(
        ...,
        description="ID único del registro de permiso en la tabla de relación",
        examples=[1, 2, 3]
    )
    
    rol_id: int = Field(
        ...,
        description="ID del rol al que pertenece el permiso",
        examples=[1, 2, 3]
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
    )