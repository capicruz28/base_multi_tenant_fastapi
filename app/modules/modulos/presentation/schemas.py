# app/modules/modulos/presentation/schemas.py
"""
Esquemas Pydantic para la gestión de módulos ERP, secciones y menús.

Este módulo define todos los esquemas de validación, creación, actualización 
y lectura para el sistema refactorizado de módulos y menús.

Características principales:
- Validaciones robustas con mensajes de error en español
- Gestión completa de módulos ERP con secciones y menús jerárquicos
- Soporte para plantillas de roles
- Validación de JSON para configuraciones y permisos
- Documentación clara para desarrolladores
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import re
import json

# ============================================================================
# SCHEMAS DE MÓDULO
# ============================================================================

class ModuloBase(BaseModel):
    """Schema base para módulos ERP."""
    codigo: str = Field(..., max_length=30, description="Código único del módulo (ej: 'LOGISTICA', 'ALMACEN')")
    nombre: str = Field(..., max_length=100, description="Nombre descriptivo del módulo")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción detallada")
    icono: Optional[str] = Field(None, max_length=50, description="Icono representativo")
    color: str = Field('#1976D2', max_length=7, description="Color principal en HEX")
    categoria: str = Field('operaciones', max_length=30, description="Categoría: 'operaciones', 'finanzas', 'rrhh', 'produccion'")
    es_core: bool = Field(False, description="True = Módulo esencial (siempre disponible)")
    requiere_licencia: bool = Field(True, description="True = Requiere contratación/pago adicional")
    precio_mensual: Optional[float] = Field(None, ge=0, description="Precio mensual del módulo")
    modulos_requeridos: Optional[str] = Field(None, description="JSON array con códigos de módulos requeridos")
    orden: int = Field(0, ge=0, description="Orden de visualización")
    es_activo: bool = Field(True, description="Habilitar/deshabilitar módulo")
    configuracion_defecto: Optional[str] = Field(None, description="JSON con configuración por defecto")

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        """Valida que el código sea en mayúsculas y único."""
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError("El código debe contener solo letras mayúsculas, números y guiones bajos")
        return v.upper()

    @field_validator('modulos_requeridos')
    @classmethod
    def validar_modulos_requeridos_json(cls, v: Optional[str]) -> Optional[str]:
        """Valida que modulos_requeridos sea un JSON array válido."""
        if v is None:
            return None
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("modulos_requeridos debe ser un array JSON")
            for item in parsed:
                if not isinstance(item, str):
                    raise ValueError("Todos los elementos del array deben ser strings")
            return v
        except json.JSONDecodeError:
            raise ValueError("modulos_requeridos debe ser un JSON válido")

    @field_validator('configuracion_defecto')
    @classmethod
    def validar_configuracion_json(cls, v: Optional[str]) -> Optional[str]:
        """Valida que configuracion_defecto sea un JSON válido."""
        if v is None:
            return None
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError("configuracion_defecto debe ser un JSON válido")

    class Config:
        from_attributes = True


class ModuloCreate(ModuloBase):
    """Schema para crear un nuevo módulo."""
    pass


class ModuloUpdate(BaseModel):
    """Schema para actualizar un módulo (campos opcionales)."""
    codigo: Optional[str] = Field(None, max_length=30)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    icono: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    categoria: Optional[str] = Field(None, max_length=30)
    es_core: Optional[bool] = None
    requiere_licencia: Optional[bool] = None
    precio_mensual: Optional[float] = Field(None, ge=0)
    modulos_requeridos: Optional[str] = None
    orden: Optional[int] = Field(None, ge=0)
    es_activo: Optional[bool] = None
    configuracion_defecto: Optional[str] = None
    fecha_actualizacion: Optional[datetime] = None

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError("El código debe contener solo letras mayúsculas, números y guiones bajos")
        return v.upper()


class ModuloRead(ModuloBase):
    """Schema para leer un módulo."""
    modulo_id: UUID
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None


# ============================================================================
# SCHEMAS DE RESPUESTA PARA ENDPOINTS
# ============================================================================

class PaginationMetadata(BaseModel):
    """Metadata de paginación para respuestas paginadas."""
    total: int = Field(..., description="Total de registros disponibles")
    skip: int = Field(..., description="Número de registros saltados")
    limit: int = Field(..., description="Límite de registros por página")
    total_pages: int = Field(..., description="Total de páginas")
    current_page: int = Field(..., description="Página actual")
    has_next: bool = Field(..., description="Indica si hay página siguiente")
    has_prev: bool = Field(..., description="Indica si hay página anterior")

    class Config:
        from_attributes = True


class ModuloResponse(BaseModel):
    """
    Respuesta estándar para operaciones sobre un módulo individual.
    Usado en endpoints de creación, actualización y consulta de un solo módulo.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: Optional[ModuloRead] = Field(None, description="Datos del módulo.")

    class Config:
        from_attributes = True


class PaginatedModuloResponse(BaseModel):
    """
    Respuesta estándar para listas paginadas de módulos.
    Incluye metadata de paginación para facilitar la navegación en el frontend.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloRead] = Field(default_factory=list, description="Lista de módulos de la página actual.")
    pagination: PaginationMetadata = Field(..., description="Metadata de paginación.")

    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS DE SECCIÓN
# ============================================================================

class ModuloSeccionBase(BaseModel):
    """Schema base para secciones de módulos."""
    codigo: str = Field(..., max_length=30, description="Código único dentro del módulo")
    nombre: str = Field(..., max_length=100, description="Nombre descriptivo")
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    orden: int = Field(0, ge=0, description="Orden dentro del módulo")
    es_seccion_sistema: bool = Field(True, description="True = Sección predefinida (no editable)")
    es_activo: bool = Field(True, description="Habilitar/deshabilitar sección")

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        """Valida que el código sea en mayúsculas."""
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError("El código debe contener solo letras mayúsculas, números y guiones bajos")
        return v.upper()

    class Config:
        from_attributes = True


class ModuloSeccionCreate(ModuloSeccionBase):
    """Schema para crear una nueva sección."""
    modulo_id: UUID = Field(..., description="ID del módulo al que pertenece")


class ModuloSeccionUpdate(BaseModel):
    """Schema para actualizar una sección."""
    codigo: Optional[str] = Field(None, max_length=30)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    orden: Optional[int] = Field(None, ge=0)
    es_seccion_sistema: Optional[bool] = None
    es_activo: Optional[bool] = None


class ModuloSeccionRead(ModuloSeccionBase):
    """Schema para leer una sección."""
    seccion_id: UUID
    modulo_id: UUID
    fecha_creacion: datetime


# ============================================================================
# SCHEMAS DE MENÚ
# ============================================================================

class ModuloMenuBase(BaseModel):
    """Schema base para menús de módulos."""
    codigo: Optional[str] = Field(None, max_length=50, description="Código único (solo menús del sistema)")
    nombre: str = Field(..., max_length=100, description="Nombre para mostrar en UI")
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    ruta: Optional[str] = Field(None, max_length=255, description="Path en el frontend")
    menu_padre_id: Optional[UUID] = Field(None, description="ID del menú padre (para submenús)")
    nivel: int = Field(1, ge=1, le=3, description="Nivel de profundidad (1=raíz, 2=hijo, 3=nieto)")
    tipo_menu: str = Field('pantalla', max_length=20, description="'pantalla', 'accion', 'enlace_externo', 'separador'")
    orden: Optional[int] = Field(0, ge=0, description="Orden de visualización (puede ser NULL en BD, se normaliza a 0)")
    requiere_autenticacion: bool = Field(True)
    es_visible: bool = Field(True, description="FALSE = Ruta accesible pero no se muestra en menú")
    es_menu_sistema: bool = Field(True, description="True = Menú del sistema (no editable)")
    es_activo: bool = Field(True)
    configuracion_json: Optional[str] = Field(None, description="JSON con configuración adicional")

    @field_validator('tipo_menu')
    @classmethod
    def validar_tipo_menu(cls, v: str) -> str:
        """Valida que el tipo de menú sea válido."""
        tipos_validos = ['pantalla', 'accion', 'enlace_externo', 'separador']
        if v not in tipos_validos:
            raise ValueError(f"tipo_menu debe ser uno de: {', '.join(tipos_validos)}")
        return v

    @field_validator('configuracion_json')
    @classmethod
    def validar_configuracion_json(cls, v: Optional[str]) -> Optional[str]:
        """Valida que configuracion_json sea un JSON válido."""
        if v is None:
            return None
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError:
            raise ValueError("configuracion_json debe ser un JSON válido")

    class Config:
        from_attributes = True


class ModuloMenuCreate(ModuloMenuBase):
    """Schema para crear un nuevo menú."""
    modulo_id: UUID = Field(..., description="ID del módulo (obligatorio)")
    seccion_id: Optional[UUID] = Field(None, description="ID de la sección (opcional)")
    cliente_id: Optional[UUID] = Field(None, description="NULL = Menú global, UUID = Menú personalizado")


class ModuloMenuUpdate(BaseModel):
    """Schema para actualizar un menú."""
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    ruta: Optional[str] = Field(None, max_length=255)
    menu_padre_id: Optional[UUID] = None
    nivel: Optional[int] = Field(None, ge=1, le=3)
    tipo_menu: Optional[str] = Field(None, max_length=20)
    orden: Optional[int] = Field(None, ge=0)
    requiere_autenticacion: Optional[bool] = None
    es_visible: Optional[bool] = None
    es_menu_sistema: Optional[bool] = None
    es_activo: Optional[bool] = None
    configuracion_json: Optional[str] = None
    fecha_actualizacion: Optional[datetime] = None


class ModuloMenuRead(ModuloMenuBase):
    """Schema para leer un menú."""
    menu_id: UUID
    modulo_id: UUID
    seccion_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None


# ============================================================================
# SCHEMAS DE CLIENTE-MÓDULO (ACTIVACIÓN)
# ============================================================================

class ClienteModuloBase(BaseModel):
    """Schema base para activación de módulos por cliente."""
    esta_activo: bool = Field(True, description="Control on/off del módulo")
    fecha_vencimiento: Optional[datetime] = Field(None, description="NULL = licencia ilimitada")
    modo_prueba: bool = Field(False, description="True = Cliente en modo trial")
    fecha_fin_prueba: Optional[datetime] = Field(None, description="Fecha límite del periodo de prueba")
    configuracion_json: Optional[Dict[str, Any]] = Field(None, description="Configuración personalizada (JSON)")
    limite_usuarios: Optional[int] = Field(None, ge=0, description="NULL = ilimitado")
    limite_registros: Optional[int] = Field(None, ge=0, description="NULL = ilimitado")
    limite_transacciones_mes: Optional[int] = Field(None, ge=0, description="NULL = ilimitado")

    class Config:
        from_attributes = True


class ClienteModuloCreate(ClienteModuloBase):
    """Schema para activar un módulo para un cliente."""
    cliente_id: UUID = Field(..., description="ID del cliente")
    modulo_id: UUID = Field(..., description="ID del módulo a activar")
    activado_por_usuario_id: Optional[UUID] = Field(None, description="ID del usuario que activa")


class ClienteModuloUpdate(BaseModel):
    """Schema para actualizar configuración de módulo activo."""
    esta_activo: Optional[bool] = None
    fecha_vencimiento: Optional[datetime] = None
    modo_prueba: Optional[bool] = None
    fecha_fin_prueba: Optional[datetime] = None
    configuracion_json: Optional[Dict[str, Any]] = None
    limite_usuarios: Optional[int] = Field(None, ge=0)
    limite_registros: Optional[int] = Field(None, ge=0)
    limite_transacciones_mes: Optional[int] = Field(None, ge=0)


class ClienteModuloRead(ClienteModuloBase):
    """Schema para leer activación de módulo."""
    cliente_modulo_id: UUID
    cliente_id: UUID
    modulo_id: UUID
    fecha_activacion: datetime
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    activado_por_usuario_id: Optional[UUID] = None
    # Información del módulo (join)
    modulo_nombre: Optional[str] = None
    modulo_codigo: Optional[str] = None


# ============================================================================
# SCHEMAS DE PLANTILLA DE ROLES
# ============================================================================

class ModuloRolPlantillaBase(BaseModel):
    """Schema base para plantillas de roles."""
    nombre_rol: str = Field(..., max_length=50, description="Nombre del rol (ej: 'Administrador Logística')")
    descripcion: Optional[str] = Field(None, max_length=255)
    nivel_acceso: int = Field(1, ge=1, le=5, description="1=Básico, 2=Intermedio, 3=Avanzado, 4=Administrador, 5=Super Admin")
    permisos_json: Optional[str] = Field(None, description="JSON con estructura de permisos por menú")
    es_activo: bool = Field(True)
    orden: int = Field(0, ge=0)

    @field_validator('permisos_json')
    @classmethod
    def validar_permisos_json(cls, v: Optional[str]) -> Optional[str]:
        """
        Valida que permisos_json tenga la estructura correcta.
        
        Estructura esperada: { "MENU_CODIGO": { "ver": true, "crear": true, ... } }
        También acepta estructuras con flags booleanos directos para compatibilidad.
        """
        if v is None:
            return None
        
        # Si ya es un dict (viene parseado), convertirlo a string primero
        if isinstance(v, dict):
            v = json.dumps(v)
        
        # Si no es string, intentar convertirlo
        if not isinstance(v, str):
            try:
                v = json.dumps(v)
            except (TypeError, ValueError):
                raise ValueError("permisos_json debe ser un string JSON válido o un objeto")
        
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, dict):
                raise ValueError("permisos_json debe ser un objeto JSON")
            
            # Validar estructura: { "MENU_CODIGO": { "ver": true, "crear": true, ... } }
            # O estructuras con flags booleanos directos para compatibilidad
            for menu_codigo, permisos in parsed.items():
                if not isinstance(menu_codigo, str):
                    raise ValueError("Las claves de permisos_json deben ser strings (códigos de menú)")
                
                # Si permisos es un dict, validar estructura de permisos
                if isinstance(permisos, dict):
                    # Validar permisos básicos
                    permisos_validos = ['ver', 'crear', 'editar', 'eliminar', 'exportar', 'imprimir', 'aprobar']
                    for permiso, valor in permisos.items():
                        if permiso not in permisos_validos:
                            # Permitir permisos adicionales pero loguear advertencia
                            pass
                        if not isinstance(valor, bool):
                            raise ValueError(f"El valor del permiso '{permiso}' debe ser booleano")
                # Si permisos es un booleano (estructura antigua/compatibilidad), aceptarlo pero loguear
                elif isinstance(permisos, bool):
                    # Estructura antigua: { "MENU_CODIGO": true }
                    # Esto es válido pero se recomienda migrar a la estructura nueva
                    pass
                else:
                    raise ValueError(f"Los permisos para '{menu_codigo}' deben ser un objeto o un booleano")
            
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"permisos_json debe ser un JSON válido: {str(e)}")

    class Config:
        from_attributes = True


class ModuloRolPlantillaCreate(ModuloRolPlantillaBase):
    """Schema para crear una nueva plantilla."""
    modulo_id: UUID = Field(..., description="ID del módulo")


class ModuloRolPlantillaUpdate(BaseModel):
    """Schema para actualizar una plantilla."""
    nombre_rol: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=255)
    nivel_acceso: Optional[int] = Field(None, ge=1, le=5)
    permisos_json: Optional[str] = None
    es_activo: Optional[bool] = None
    orden: Optional[int] = Field(None, ge=0)


class ModuloRolPlantillaRead(ModuloRolPlantillaBase):
    """Schema para leer una plantilla."""
    plantilla_id: UUID
    modulo_id: UUID
    fecha_creacion: datetime


# ============================================================================
# SCHEMAS DE RESPUESTA ESPECIALES
# ============================================================================

class PermisosMenu(BaseModel):
    """Schema para permisos de un menú."""
    ver: bool = True
    crear: bool = False
    editar: bool = False
    eliminar: bool = False
    exportar: bool = False
    imprimir: bool = False
    aprobar: bool = False


class MenuItem(BaseModel):
    """Schema para un ítem de menú en la estructura jerárquica."""
    menu_id: UUID
    codigo: Optional[str] = None
    nombre: str
    icono: Optional[str] = None
    ruta: Optional[str] = None
    nivel: int
    tipo_menu: str
    orden: int
    permisos: PermisosMenu
    submenus: List['MenuItem'] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SeccionMenu(BaseModel):
    """Schema para una sección con sus menús."""
    seccion_id: UUID
    codigo: str
    nombre: str
    icono: Optional[str] = None
    orden: int
    menus: List[MenuItem] = Field(default_factory=list)


class ModuloMenuResponse(BaseModel):
    """Schema para un módulo con sus secciones y menús."""
    modulo_id: UUID
    codigo: str
    nombre: str
    icono: Optional[str] = None
    color: str
    categoria: str
    orden: int
    secciones: List[SeccionMenu] = Field(default_factory=list)


class MenuUsuarioResponse(BaseModel):
    """Schema de respuesta para el menú completo del usuario."""
    modulos: List[ModuloMenuResponse] = Field(default_factory=list)


# Permitir referencias forward
MenuItem.model_rebuild()

