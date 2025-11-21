# app/schemas/conexion.py
"""
Esquemas Pydantic para la entidad Conexion en arquitectura multi-tenant.
Estos esquemas definen la estructura de datos para la gestión de conexiones de base de datos
por cliente y módulo, incluyendo validación de configuraciones, encriptación de credenciales
y soporte para múltiples motores de base de datos.

Características clave:
- Validación de configuraciones de conexión a BD
- Soporte para múltiples motores (SQL Server, PostgreSQL, MySQL, Oracle)
- Manejo seguro de credenciales con encriptación
- Configuración de connection pooling y timeouts
- Total coherencia con la estructura de la tabla cliente_modulo_conexion
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
import re


class ConexionBase(BaseModel):
    """
    Esquema base para la entidad Conexion, alineado con la tabla cliente_modulo_conexion.
    Define la configuración de conexiones de base de datos específicas por cliente y módulo.
    """
    # ========================================
    # IDENTIFICACIÓN Y CONTEXTO
    # ========================================
    cliente_id: int = Field(..., description="ID del cliente al que pertenece la conexión.")
    modulo_id: int = Field(..., description="ID del módulo para el que se configura la conexión.")

    # ========================================
    # CONFIGURACIÓN DE CONEXIÓN
    # ========================================
    servidor: str = Field(
        ..., 
        max_length=255, 
        description="Nombre o IP del servidor de BD (ej: 'localhost', 'sql.azure.com')."
    )
    puerto: int = Field(
        1433, 
        description="Puerto de conexión (1433 para SQL Server, 5432 para PostgreSQL, etc.)."
    )
    nombre_bd: str = Field(
        ..., 
        max_length=100, 
        description="Nombre de la base de datos (ej: 'bdpla_psf_web', 'produccion_2024')."
    )
    tipo_bd: str = Field(
        "sqlserver", 
        description="Tipo de base de datos: 'sqlserver', 'postgresql', 'mysql', 'oracle'."
    )

    # ========================================
    # CONFIGURACIÓN AVANZADA
    # ========================================
    usa_ssl: bool = Field(
        False, 
        description="Indica si la conexión usa SSL/TLS."
    )
    timeout_segundos: int = Field(
        30, 
        description="Timeout de conexión en segundos."
    )
    max_pool_size: int = Field(
        100, 
        description="Tamaño máximo del connection pool."
    )
    es_solo_lectura: bool = Field(
        False, 
        description="True = Conexión read-only (útil para réplicas)."
    )
    es_conexion_principal: bool = Field(
        False, 
        description="True = Es la conexión principal del módulo (solo una por cliente-módulo)."
    )

    # === VALIDADORES ===
    @validator('servidor')
    def validar_servidor(cls, v):
        """
        Valida el formato del servidor (hostname o IP válida).
        """
        if not v or not v.strip():
            raise ValueError("El servidor no puede estar vacío.")
        
        # Validar como hostname
        if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$", v):
            return v
            
        # Validar como IPv4
        if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", v):
            octetos = v.split('.')
            if all(0 <= int(octeto) <= 255 for octeto in octetos):
                return v
                
        # Validar como IPv6 (simplificado)
        if ':' in v and re.match(r"^[0-9a-fA-F:]+$", v):
            return v
            
        raise ValueError("Formato de servidor inválido. Use hostname, IPv4 o IPv6 válido.")

    @validator('puerto')
    def validar_puerto(cls, v):
        """
        Valida que el puerto esté en el rango válido.
        """
        if v < 1 or v > 65535:
            raise ValueError("El puerto debe estar entre 1 y 65535.")
        return v

    @validator('tipo_bd')
    def validar_tipo_bd(cls, v):
        """
        Valida que el tipo de base de datos sea soportado.
        """
        tipos_validos = ['sqlserver', 'postgresql', 'mysql', 'oracle']
        if v not in tipos_validos:
            raise ValueError(f"Tipo de BD no soportado. Use: {', '.join(tipos_validos)}")
        return v

    @validator('timeout_segundos')
    def validar_timeout(cls, v):
        """
        Valida que el timeout sea razonable.
        """
        if v < 5 or v > 300:
            raise ValueError("El timeout debe estar entre 5 y 300 segundos.")
        return v

    @validator('max_pool_size')
    def validar_pool_size(cls, v):
        """
        Valida que el tamaño del pool sea razonable.
        """
        if v < 1 or v > 1000:
            raise ValueError("El tamaño máximo del pool debe estar entre 1 y 1000.")
        return v

    @field_validator('nombre_bd')
    @classmethod
    def validar_nombre_bd(cls, v: str) -> str:
        """
        Valida que el nombre de BD no esté vacío y tenga formato válido.
        """
        if not v or not v.strip():
            raise ValueError("El nombre de la base de datos no puede estar vacío.")
        
        # Validar caracteres básicos para nombres de BD
        if not re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_\-\.]*$", v):
            raise ValueError(
                "El nombre de la base de datos solo puede contener letras, números, "
                "guiones bajos, guiones y puntos, y debe comenzar con letra o número."
            )
        return v.strip()

    class Config:
        from_attributes = True


class ConexionCreate(ConexionBase):
    """
    Esquema para la creación de una nueva conexión de base de datos.
    Incluye campos para credenciales en texto plano que serán encriptadas.
    """
    usuario: str = Field(..., description="Usuario de BD para encriptar.")
    password: str = Field(..., description="Password de BD para encriptar.")


class ConexionUpdate(BaseModel):
    """
    Esquema para la actualización parcial de una conexión.
    Todos los campos son opcionales, incluyendo credenciales.
    """
    servidor: Optional[str] = Field(None, max_length=255)
    puerto: Optional[int] = None
    nombre_bd: Optional[str] = Field(None, max_length=100)
    usuario: Optional[str] = Field(None, description="Nuevo usuario de BD (se encriptará).")
    password: Optional[str] = Field(None, description="Nuevo password de BD (se encriptará).")
    tipo_bd: Optional[str] = None
    usa_ssl: Optional[bool] = None
    timeout_segundos: Optional[int] = None
    max_pool_size: Optional[int] = None
    es_solo_lectura: Optional[bool] = None
    es_conexion_principal: Optional[bool] = None
    es_activo: Optional[bool] = None

    class Config:
        from_attributes = True


class ConexionRead(ConexionBase):
    """
    Esquema de lectura completo de una conexión.
    Incluye campos de identificación, auditoría y estado de la conexión.
    Los campos de credenciales muestran versiones encriptadas.
    """
    conexion_id: int = Field(..., description="Identificador único de la conexión.")
    usuario_encriptado: str = Field(..., description="Usuario de BD encriptado.")
    password_encriptado: str = Field(..., description="Password de BD encriptado.")
    connection_string_encriptado: Optional[str] = Field(
        None, 
        description="Connection string completo encriptado."
    )
    es_activo: bool = Field(..., description="Indica si la conexión está activa.")
    ultima_conexion_exitosa: Optional[datetime] = Field(
        None, 
        description="Última vez que se conectó exitosamente."
    )
    ultimo_error: Optional[str] = Field(None, description="Último mensaje de error de conexión.")
    fecha_ultimo_error: Optional[datetime] = Field(None, description="Fecha del último error.")
    fecha_creacion: datetime = Field(..., description="Fecha de creación del registro.")
    fecha_actualizacion: Optional[datetime] = Field(None, description="Fecha de última actualización.")
    creado_por_usuario_id: Optional[int] = Field(None, description="ID del usuario que creó la conexión.")

    class Config:
        from_attributes = True


class ConexionTest(BaseModel):
    """
    Esquema para testing de conectividad de una configuración de conexión.
    Permite probar conexiones sin guardarlas en la base de datos.
    """
    servidor: str = Field(..., max_length=255)
    puerto: int = Field(1433)
    nombre_bd: str = Field(..., max_length=100)
    usuario: str = Field(..., description="Usuario de BD para testing.")
    password: str = Field(..., description="Password de BD para testing.")
    tipo_bd: str = Field("sqlserver")
    usa_ssl: bool = Field(False)
    timeout_segundos: int = Field(30)

    class Config:
        from_attributes = True


class ConexionConEstadisticas(ConexionRead):
    """
    Esquema extendido que incluye estadísticas de uso de la conexión.
    Útil para monitoreo y troubleshooting.
    """
    total_conexiones: int = Field(0, description="Total de conexiones establecidas.")
    conexiones_activas: int = Field(0, description="Conexiones activas actualmente.")
    tiempo_promedio_respuesta: Optional[float] = Field(
        None, 
        description="Tiempo promedio de respuesta en milisegundos."
    )
    tasa_errores: Optional[float] = Field(
        None, 
        description="Porcentaje de errores en las últimas conexiones."
    )