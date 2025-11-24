# app/schemas/modulo.py
"""
Esquemas Pydantic para la entidad Modulo en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para el catálogo de módulos del sistema,
incluyendo validación de códigos únicos, configuración de módulos core y opcionales,
y gestión del ciclo de vida de módulos.

Características clave:
- Validación estricta de códigos de módulo únicos
- Soporte para módulos core (esenciales) y módulos con licencia
- Configuración de ordenamiento y visibilidad
- Total coherencia con la estructura de la tabla cliente_modulo
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import re


class ModuloBase(BaseModel):
    """
    Esquema base para la entidad Modulo, alineado con la tabla cliente_modulo.
    Define el catálogo central de módulos disponibles en el sistema multi-tenant.
    """
    # ========================================
    # IDENTIFICACIÓN Y DESCRIPCIÓN
    # ========================================
    codigo_modulo: str = Field(
        ..., 
        max_length=30, 
        description="Código único para referencia en código (ej: 'PLANILLAS', 'CONTABILIDAD')."
    )
    nombre: str = Field(
        ..., 
        max_length=100, 
        description="Nombre descriptivo del módulo."
    )
    descripcion: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Descripción detallada de la funcionalidad del módulo."
    )
    icono: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Nombre del icono representativo (depende de librería UI usada)."
    )

    # ========================================
    # CONFIGURACIÓN DEL MÓDULO
    # ========================================
    es_modulo_core: bool = Field(
        False, 
        description="True = Módulo esencial del sistema (siempre disponible)."
    )
    requiere_licencia: bool = Field(
        False, 
        description="True = Requiere licencia/pago adicional."
    )
    orden: int = Field(
        0, 
        description="Orden de visualización en UI (menor = primero)."
    )
    es_activo: bool = Field(
        True, 
        description="Indica si el módulo está disponible para activación."
    )

    # === VALIDADORES ===
    @validator('codigo_modulo')
    def validar_codigo_modulo(cls, v):
        """
        Valida que el código de módulo tenga formato válido (solo mayúsculas, números y guiones bajos).
        """
        if not re.match(r"^[A-Z][A-Z0-9_]*$", v):
            raise ValueError(
                "El código de módulo debe contener solo letras mayúsculas, números y guiones bajos, "
                "y debe comenzar con una letra."
            )
        if len(v) < 3 or len(v) > 30:
            raise ValueError("El código de módulo debe tener entre 3 y 30 caracteres.")
        return v

    @validator('orden')
    def validar_orden_positivo(cls, v):
        """
        Valida que el orden sea un número positivo.
        """
        if v < 0:
            raise ValueError("El orden debe ser un número positivo o cero.")
        return v

    @field_validator('nombre')
    @classmethod
    def validar_nombre_no_vacio(cls, v: str) -> str:
        """
        Valida que el nombre no esté vacío.
        """
        if not v or not v.strip():
            raise ValueError("El nombre del módulo no puede estar vacío.")
        return v.strip()

    class Config:
        from_attributes = True


class ModuloCreate(ModuloBase):
    """
    Esquema para la creación de un nuevo módulo en el catálogo del sistema.
    Hereda todos los campos de ModuloBase.
    """
    pass


class ModuloUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un módulo.
    Todos los campos son opcionales para permitir actualizaciones incrementales.
    """
    codigo_modulo: Optional[str] = Field(None, max_length=30)
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    icono: Optional[str] = Field(None, max_length=50)
    es_modulo_core: Optional[bool] = None
    requiere_licencia: Optional[bool] = None
    orden: Optional[int] = None
    es_activo: Optional[bool] = None

    class Config:
        from_attributes = True


class ModuloRead(ModuloBase):
    """
    Esquema de lectura completo de un módulo.
    Incluye los campos de identificación y auditoría generados por el sistema.
    """
    modulo_id: int = Field(..., description="Identificador único del módulo.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")

    class Config:
        from_attributes = True


class ModuloConInfoActivacion(ModuloRead):
    """
    Esquema extendido que incluye información de activación para un cliente específico.
    Útil para endpoints de administración que muestran el estado de módulos por cliente.
    """
    activo_en_cliente: bool = Field(..., description="Indica si el módulo está activo para el cliente.")
    cliente_modulo_activo_id: Optional[int] = Field(None, description="ID del registro de activación.")
    fecha_activacion: Optional[datetime] = Field(None, description="Fecha de activación para el cliente.")
    fecha_vencimiento: Optional[datetime] = Field(None, description="Fecha de vencimiento de la licencia (NULL = ilimitado).")
    configuracion_json: Optional[str] = Field(None, description="Configuración específica para el cliente (JSON string).")
    limite_usuarios: Optional[int] = Field(None, description="Límite de usuarios para este módulo.")
    limite_registros: Optional[int] = Field(None, description="Límite de registros para este módulo.")


# ============================================================================
# SCHEMAS DE RESPUESTA ESTÁNDAR
# Estos schemas estandarizan el formato de respuesta de todos los endpoints
# para facilitar el consumo desde el frontend
# ============================================================================

class PaginationMetadata(BaseModel):
    """
    Metadata de paginación para respuestas paginadas.
    Proporciona toda la información necesaria para implementar paginación en el frontend.
    """
    total: int = Field(..., description="Total de registros disponibles.")
    skip: int = Field(..., description="Número de registros saltados.")
    limit: int = Field(..., description="Límite de registros por página.")
    total_pages: int = Field(..., description="Total de páginas disponibles.")
    current_page: int = Field(..., description="Página actual (1-indexed).")
    has_next: bool = Field(..., description="Indica si existe una página siguiente.")
    has_prev: bool = Field(..., description="Indica si existe una página anterior.")

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


class ModuloListResponse(BaseModel):
    """
    Respuesta estándar para listas de módulos sin paginación.
    Usado cuando se retorna una lista completa de módulos.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloRead] = Field(default_factory=list, description="Lista de módulos.")

    class Config:
        from_attributes = True


class ModuloConInfoActivacionListResponse(BaseModel):
    """
    Respuesta estándar para listas de módulos con información de activación.
    Usado en endpoints que muestran módulos con su estado de activación por cliente.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    data: List[ModuloConInfoActivacion] = Field(default_factory=list, description="Lista de módulos con información de activación.")

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


class ModuloDeleteResponse(BaseModel):
    """
    Respuesta estándar para operaciones de eliminación de módulos.
    Confirma la eliminación exitosa del módulo.
    """
    success: bool = Field(True, description="Indica si la operación fue exitosa.")
    message: str = Field(..., description="Mensaje descriptivo de la operación.")
    modulo_id: int = Field(..., description="ID del módulo eliminado.")

    class Config:
        from_attributes = True