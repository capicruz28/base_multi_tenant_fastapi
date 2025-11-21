# app/schemas/modulo_activo.py
"""
Esquemas Pydantic para la entidad ModuloActivo en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para la activación y configuración
de módulos específicos por cliente, incluyendo límites de uso, configuraciones
personalizadas y gestión del ciclo de vida de licencias.

Características clave:
- Gestión de activación/desactivación de módulos por cliente
- Configuración de límites de usuarios y registros
- Soporte para configuraciones JSON personalizadas por módulo
- Control de fechas de vencimiento de licencias
- Total coherencia con la estructura de la tabla cliente_modulo_activo
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import json


class ModuloActivoBase(BaseModel):
    """
    Esquema base para la entidad ModuloActivo, alineado con la tabla cliente_modulo_activo.
    Define la relación entre clientes y módulos activados con sus configuraciones específicas.
    """
    # ========================================
    # IDENTIFICACIÓN Y CONTEXTO
    # ========================================
    cliente_id: int = Field(..., description="ID del cliente que activa el módulo.")
    modulo_id: int = Field(..., description="ID del módulo que se activa.")

    # ========================================
    # CONFIGURACIÓN Y LÍMITES
    # ========================================
    configuracion_json: Optional[Dict[str, Any]] = Field(
        None, 
        description="JSON con configuraciones custom del módulo para este cliente."
    )
    limite_usuarios: Optional[int] = Field(
        None, 
        description="Máximo de usuarios que pueden usar este módulo (NULL = ilimitado)."
    )
    limite_registros: Optional[int] = Field(
        None, 
        description="Límite de registros para este módulo (NULL = ilimitado)."
    )

    # === VALIDADORES ===
    @validator('limite_usuarios')
    def validar_limite_usuarios(cls, v):
        """
        Valida que el límite de usuarios sea positivo si se especifica.
        """
        if v is not None and v < 1:
            raise ValueError("El límite de usuarios debe ser al menos 1 o NULL para ilimitado.")
        return v

    @validator('limite_registros')
    def validar_limite_registros(cls, v):
        """
        Valida que el límite de registros sea positivo si se especifica.
        """
        if v is not None and v < 0:
            raise ValueError("El límite de registros debe ser al menos 0 o NULL para ilimitado.")
        return v

    @validator('configuracion_json')
    def validar_configuracion_json(cls, v):
        """
        Valida que la configuración JSON sea un objeto válido.
        """
        if v is not None:
            try:
                # Verificar que se puede serializar a JSON
                json.dumps(v)
            except (TypeError, ValueError) as e:
                raise ValueError(f"Configuración JSON inválida: {str(e)}")
        return v

    @field_validator('cliente_id', 'modulo_id')
    @classmethod
    def validar_ids_positivos(cls, v: int) -> int:
        """
        Valida que los IDs sean números positivos.
        """
        if v <= 0:
            raise ValueError("Los IDs deben ser números positivos.")
        return v

    class Config:
        from_attributes = True


class ModuloActivoCreate(ModuloActivoBase):
    """
    Esquema para la activación de un módulo para un cliente.
    Hereda todos los campos de ModuloActivoBase.
    """
    pass


class ModuloActivoUpdate(BaseModel):
    """
    Esquema para la actualización parcial de un módulo activo.
    Permite modificar configuraciones y límites sin cambiar el estado de activación.
    """
    configuracion_json: Optional[Dict[str, Any]] = None
    limite_usuarios: Optional[int] = None
    limite_registros: Optional[int] = None
    fecha_vencimiento: Optional[datetime] = Field(
        None, 
        description="Nueva fecha de vencimiento de la licencia."
    )
    esta_activo: Optional[bool] = Field(
        None, 
        description="Cambiar estado de activación del módulo."
    )

    class Config:
        from_attributes = True


class ModuloActivoRead(ModuloActivoBase):
    """
    Esquema de lectura completo de un módulo activo.
    Incluye campos de estado, fechas y relación con la información del módulo.
    """
    cliente_modulo_activo_id: int = Field(..., description="Identificador único del registro de activación.")
    esta_activo: bool = Field(..., description="Indica si el módulo está activo para el cliente.")
    fecha_activacion: datetime = Field(..., description="Fecha de activación del módulo.")
    fecha_vencimiento: Optional[datetime] = Field(
        None, 
        description="Fecha de vencimiento de la licencia (NULL = ilimitado)."
    )
    
    # Información del módulo (join desde cliente_modulo)
    modulo_nombre: Optional[str] = Field(None, description="Nombre del módulo.")
    codigo_modulo: Optional[str] = Field(None, description="Código único del módulo.")
    modulo_descripcion: Optional[str] = Field(None, description="Descripción del módulo.")

    class Config:
        from_attributes = True


class ModuloActivoConEstadisticas(ModuloActivoRead):
    """
    Esquema extendido que incluye estadísticas de uso del módulo activo.
    Útil para dashboards de administración y control de límites.
    """
    usuarios_activos: int = Field(0, description="Número de usuarios activos usando el módulo.")
    registros_totales: int = Field(0, description="Total de registros en el módulo.")
    porcentaje_uso_usuarios: Optional[float] = Field(
        None, 
        description="Porcentaje de uso del límite de usuarios (0-100)."
    )
    porcentaje_uso_registros: Optional[float] = Field(
        None, 
        description="Porcentaje de uso del límite de registros (0-100)."
    )
    dias_restantes_licencia: Optional[int] = Field(
        None, 
        description="Días restantes hasta el vencimiento (NULL = ilimitado)."
    )
    esta_proximo_vencimiento: bool = Field(
        False, 
        description="True si la licencia vence en menos de 30 días."
    )
    esta_sobre_limite: bool = Field(
        False, 
        description="True si se ha excedido algún límite configurado."
    )