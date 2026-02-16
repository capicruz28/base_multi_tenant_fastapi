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
        
        # ✅ CORRECCIÓN: Permitir roles con codigo_rol Y cliente_id si son roles estándar por cliente
        # Los roles como 'ADMIN', 'USER' son roles estándar del sistema pero cada cliente tiene su instancia
        # Solo los roles GLOBALES del sistema (como 'SUPER_ADMIN') no deben tener cliente_id
        if self.codigo_rol is not None and cliente_id_valido is not None:
            # Roles globales del sistema que NO deben tener cliente_id
            roles_globales_sistema = {'SUPER_ADMIN', 'SUPERADMIN', 'SYSTEM_ADMIN'}
            
            # Si es un rol global del sistema, no puede tener cliente_id
            if self.codigo_rol.upper() in roles_globales_sistema:
                if not isinstance(self, RolCreate):
                    raise ValueError(
                        f'Un rol global del sistema ({self.codigo_rol}) no puede tener cliente_id asignado. '
                        'Los roles globales del sistema son únicos y no pertenecen a un cliente específico.'
                    )
                # Si es RolCreate y es rol global, eliminar cliente_id
                else:
                    self.cliente_id = None
            # Si es un rol estándar (ADMIN, USER, etc.), permitir que tenga cliente_id
            # Estos roles son estándar pero cada cliente tiene su propia instancia
        
        # Si no tiene código de rol y no tiene cliente_id, es un error, debe ser rol de sistema o de cliente.
        # Pero durante la creación (RolCreate), permitimos que cliente_id sea None ya que el endpoint lo asignará
        if self.codigo_rol is None and self.cliente_id is None:
            # Durante la creación (RolCreate), permitimos que cliente_id sea None
            if not isinstance(self, RolCreate):
                raise ValueError(
                    'El rol debe tener un código de rol (si es rol de sistema) o un cliente_id (si es rol de cliente). '
                    'No puede estar vacío en ambos campos.'
                )
            
        return self

class RolCreate(RolBase):
    """
    Schema para la creación de nuevos roles.
    
    ✅ CORRECCIÓN: Override del model_validator para ser más permisivo durante la creación.
    Permite que codigo_rol esté presente si cliente_id es None, ya que el endpoint asignará
    el cliente_id después de la validación.
    """
    
    @model_validator(mode='after')
    def validar_consistencia_creacion(self) -> 'RolCreate':
        """
        Validación más permisiva para la creación de roles.
        
        Permite que codigo_rol esté presente si cliente_id es None, ya que el endpoint
        asignará el cliente_id después de la validación. Si ambos están presentes,
        elimina codigo_rol para roles de cliente.
        """
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
        
        # ✅ CORRECCIÓN: Si cliente_id está presente y codigo_rol también, eliminar codigo_rol
        # Los roles de cliente NO deben tener codigo_rol
        if self.codigo_rol is not None and cliente_id_valido is not None:
            # En lugar de lanzar error, simplemente eliminar codigo_rol
            # El endpoint ya maneja esto, pero por si acaso lo hacemos aquí también
            self.codigo_rol = None
        
        # Si no tiene código de rol y no tiene cliente_id, es un error, debe ser rol de sistema o de cliente.
        # Pero durante la creación, permitimos que cliente_id sea None ya que el endpoint lo asignará
        # Solo validamos si ambos están None Y codigo_rol también está None (caso inválido)
        if self.codigo_rol is None and self.cliente_id is None:
            # Durante la creación, permitimos que cliente_id sea None ya que el endpoint lo asignará
            # Solo validamos si codigo_rol está presente sin cliente_id (rol del sistema)
            # En este caso, está bien, el endpoint validará si el usuario puede crear roles del sistema
            pass
            
        return self

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
    
    ✅ ACTUALIZADO: Incluye todos los campos de la tabla rol_menu_permiso.
    """
    
    menu_id: UUID = Field(
        ...,
        description="ID del menú al que aplican los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    # ======================================== 
    # PERMISOS GRANULARES (CRUD extendido)
    # ======================================== 
    puede_ver: bool = Field(
        default=True,
        description="Permiso para ver/acceder al menú",
        examples=[True, False]
    )
    
    puede_crear: bool = Field(
        default=False,
        description="Permiso para crear nuevos registros asociados al menú",
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
    
    puede_exportar: bool = Field(
        default=False,
        description="Permiso para exportar datos asociados al menú",
        examples=[True, False]
    )
    
    puede_imprimir: bool = Field(
        default=False,
        description="Permiso para imprimir datos asociados al menú",
        examples=[True, False]
    )
    
    puede_aprobar: bool = Field(
        default=False,
        description="Permiso para aprobar/rechazar acciones asociadas al menú",
        examples=[True, False]
    )
    
    # ======================================== 
    # PERMISOS PERSONALIZADOS POR MÓDULO
    # ======================================== 
    permisos_extra: Optional[str] = Field(
        default=None,
        description="JSON con permisos específicos del módulo/pantalla (NVARCHAR(MAX))",
        examples=['{"puede_cerrar_ruta": true, "puede_reasignar_conductor": false}']
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

class PermisoRead(PermisoBase):
    """
    Schema para lectura de permisos existentes.
    
    ✅ ACTUALIZADO: Incluye todos los campos de la tabla rol_menu_permiso.
    """
    
    permiso_id: UUID = Field(
        ...,
        description="ID único del registro de permiso (UUID) - Primary Key",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    cliente_id: UUID = Field(
        ...,
        description="ID del cliente/tenant al que pertenece el permiso (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440001"]
    )
    
    rol_id: UUID = Field(
        ...,
        description="ID del rol al que pertenece el permiso (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440002"]
    )
    
    fecha_creacion: datetime = Field(
        ...,
        description="Fecha y hora de creación del permiso",
        examples=["2025-12-10T10:00:00"]
    )
    
    fecha_actualizacion: Optional[datetime] = Field(
        default=None,
        description="Fecha y hora de última actualización del permiso",
        examples=["2025-12-10T11:00:00"]
    )
    
    # Alias para compatibilidad con código existente
    @property
    def rol_menu_id(self) -> UUID:
        """Alias para permiso_id para compatibilidad con código existente."""
        return self.permiso_id

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
from datetime import datetime
from uuid import UUID

class RolMenuPermisoBase(BaseModel):
    """
    Schema base para permisos rol-menú con validaciones fundamentales.
    
    ✅ ACTUALIZADO: Incluye todos los campos de la tabla rol_menu_permiso.
    
    Define la estructura básica de un permiso rol-menú y establece 
    las reglas de validación esenciales para mantener la seguridad del sistema.
    """
    
    cliente_id: UUID = Field(
        ...,
        description="ID del cliente/tenant al que pertenece el permiso (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    rol_id: UUID = Field(
        ...,
        description="ID del rol al que se asignan los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440001"]
    )
    
    menu_id: UUID = Field(
        ...,
        description="ID del menú sobre el que se aplican los permisos (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440002"]
    )
    
    # ======================================== 
    # PERMISOS GRANULARES (CRUD extendido)
    # ======================================== 
    puede_ver: bool = Field(
        default=True,
        description="Permiso para visualizar/acceder al menú",
        examples=[True, False]
    )
    
    puede_crear: bool = Field(
        default=False,
        description="Permiso para crear nuevos registros asociados al menú",
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
    
    puede_exportar: bool = Field(
        default=False,
        description="Permiso para exportar datos asociados al menú",
        examples=[True, False]
    )
    
    puede_imprimir: bool = Field(
        default=False,
        description="Permiso para imprimir datos asociados al menú",
        examples=[True, False]
    )
    
    puede_aprobar: bool = Field(
        default=False,
        description="Permiso para aprobar/rechazar acciones asociadas al menú",
        examples=[True, False]
    )
    
    # ======================================== 
    # PERMISOS PERSONALIZADOS POR MÓDULO
    # ======================================== 
    permisos_extra: Optional[str] = Field(
        default=None,
        description="JSON con permisos específicos del módulo/pantalla (NVARCHAR(MAX))",
        examples=['{"puede_cerrar_ruta": true, "puede_reasignar_conductor": false}']
    )

    @model_validator(mode='after')
    def validar_consistencia_permisos(self) -> 'RolMenuPermisoBase':
        """
        Valida consistencias adicionales después de procesar todos los campos.
        
        Realiza validaciones que requieren múltiples campos o que dependen
        de transformaciones realizadas en validadores individuales.
        """
        # Validar que si puede_editar, puede_eliminar, puede_crear, puede_exportar, puede_imprimir o puede_aprobar es True, 
        # entonces puede_ver debe ser True
        permisos_que_requieren_ver = [
            self.puede_editar, 
            self.puede_eliminar, 
            self.puede_crear, 
            self.puede_exportar, 
            self.puede_imprimir, 
            self.puede_aprobar
        ]
        
        if any(permisos_que_requieren_ver) and not self.puede_ver:
            raise ValueError(
                'No se pueden conceder permisos de creación, edición, eliminación, exportación, impresión o aprobación '
                'sin permiso de visualización. El permiso "puede_ver" debe ser True cuando cualquier otro permiso es True.'
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
    
    ✅ ACTUALIZADO: Incluye todos los permisos extendidos de la tabla rol_menu_permiso.
    
    Todos los campos son opcionales y solo se validan los que se proporcionen.
    Diseñado específicamente para operaciones PATCH que actualizan solo
    algunos permisos específicos.
    """
    
    # ======================================== 
    # PERMISOS GRANULARES (CRUD extendido) - Opcionales
    # ======================================== 
    puede_ver: Optional[bool] = Field(
        None,
        description="Nuevo permiso de visualización (opcional)",
        examples=[True, False]
    )
    
    puede_crear: Optional[bool] = Field(
        None,
        description="Nuevo permiso de creación (opcional)",
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
    
    puede_exportar: Optional[bool] = Field(
        None,
        description="Nuevo permiso de exportación (opcional)",
        examples=[True, False]
    )
    
    puede_imprimir: Optional[bool] = Field(
        None,
        description="Nuevo permiso de impresión (opcional)",
        examples=[True, False]
    )
    
    puede_aprobar: Optional[bool] = Field(
        None,
        description="Nuevo permiso de aprobación (opcional)",
        examples=[True, False]
    )
    
    # ======================================== 
    # PERMISOS PERSONALIZADOS POR MÓDULO
    # ======================================== 
    permisos_extra: Optional[str] = Field(
        None,
        description="JSON con permisos específicos del módulo/pantalla (opcional)",
        examples=['{"puede_cerrar_ruta": true, "puede_reasignar_conductor": false}']
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
        puede_crear = self.puede_crear
        puede_editar = self.puede_editar
        puede_eliminar = self.puede_eliminar
        puede_exportar = self.puede_exportar
        puede_imprimir = self.puede_imprimir
        puede_aprobar = self.puede_aprobar
        
        # Si se está actualizando cualquier permiso que requiera ver, verificar que ver sea True
        permisos_que_requieren_ver = [
            puede_crear, puede_editar, puede_eliminar, 
            puede_exportar, puede_imprimir, puede_aprobar
        ]
        
        if any(p is not None and p for p in permisos_que_requieren_ver):
            if puede_ver is not None and not puede_ver:
                raise ValueError(
                    'No se pueden conceder permisos de creación, edición, eliminación, exportación, impresión o aprobación '
                    'sin permiso de visualización. El permiso "puede_ver" debe ser True cuando cualquier otro permiso es True.'
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
    
    ✅ ACTUALIZADO: Incluye todos los campos de la tabla rol_menu_permiso.
    
    Incluye todos los campos de RolMenuPermisoBase más el identificador
    único del registro de permiso en el sistema y campos de auditoría.
    """
    
    permiso_id: UUID = Field(
        ...,
        description="Identificador único del permiso rol-menú en el sistema (UUID) - Primary Key",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    fecha_creacion: datetime = Field(
        ...,
        description="Fecha y hora de creación del permiso",
        examples=["2025-12-10T10:00:00"]
    )
    
    fecha_actualizacion: Optional[datetime] = Field(
        default=None,
        description="Fecha y hora de última actualización del permiso",
        examples=["2025-12-10T11:00:00"]
    )
    
    # Alias para compatibilidad con código existente
    @property
    def rol_menu_id(self) -> UUID:
        """Alias para permiso_id para compatibilidad con código existente."""
        return self.permiso_id

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
