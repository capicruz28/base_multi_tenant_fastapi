# app/core/tenant_context.py
"""
Define el contexto de cliente (tenant) para arquitectura multi-tenant HÍBRIDA.

MEJORAS EN ESTA VERSIÓN:
- Incluye metadata de conexión (database_type, nombre_bd, etc.)
- Soporta arquitectura Single-DB y Multi-DB
- Mantiene compatibilidad con código existente
- Thread-safe mediante ContextVar

CONTEXTO HÍBRIDO:
- Single-DB: Todos los clientes en bd_sistema (aislamiento por cliente_id)
- Multi-DB: Cada cliente en su propia BD (bd_cliente_acme, etc.)

USO:
    from app.core.tenant_context import get_current_client_id, get_tenant_context
    
    # Obtener solo el ID (como antes)
    client_id = get_current_client_id()
    
    # Obtener contexto completo (nuevo)
    context = get_tenant_context()
    print(f"Cliente: {context.client_id}")
    print(f"DB Type: {context.database_type}")
    print(f"BD: {context.nombre_bd}")
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# ============================================
# CONTEXTVARS (Thread-safe para async)
# ============================================

# ContextVar para el ID del cliente (UUID)
current_client_id: ContextVar[Optional[UUID]] = ContextVar(
    'current_client_id', 
    default=None
)

# ContextVar para el contexto completo del tenant (extendido)
current_tenant_context: ContextVar[Optional['TenantContext']] = ContextVar(
    'current_tenant_context', 
    default=None
)


# ============================================
# DATACLASS: TENANT CONTEXT
# ============================================

@dataclass
class TenantContext:
    """
    Clase de datos para el contexto completo del tenant.
    
    CAMPOS BÁSICOS (compatibilidad con versión anterior):
        client_id: ID del cliente
        subdominio: Subdominio usado para acceder (ej: 'acme')
        codigo_cliente: Código único del cliente (ej: 'ACME001')
    
    NUEVOS CAMPOS (arquitectura híbrida):
        database_type: "single" o "multi"
        nombre_bd: Nombre de la BD (ej: 'bd_sistema' o 'bd_cliente_acme')
        connection_metadata: Dict con metadata completa de conexión
    
    CAMPOS OPCIONALES:
        servidor: Servidor de BD (para Multi-DB)
        puerto: Puerto de BD (para Multi-DB)
        tipo_instalacion: "cloud", "onpremise", "hybrid"
    """
    
    # CAMPOS BÁSICOS (OBLIGATORIOS)
    client_id: UUID
    subdominio: Optional[str] = None
    codigo_cliente: Optional[str] = None
    
    # CAMPOS HÍBRIDOS (NUEVOS)
    database_type: str = "single"  # "single" o "multi"
    nombre_bd: Optional[str] = None  # Nombre de la BD
    connection_metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    # CAMPOS ADICIONALES (OPCIONALES)
    servidor: Optional[str] = None  # Para Multi-DB
    puerto: Optional[int] = None  # Para Multi-DB
    tipo_instalacion: Optional[str] = "cloud"  # "cloud", "onpremise", "hybrid"
    
    def __post_init__(self):
        """
        Validaciones y ajustes post-inicialización.
        """
        # Validar que client_id existe
        if self.client_id is None:
            raise ValueError("client_id es obligatorio en TenantContext")
        
        # Si no se especificó nombre_bd, intentar inferirlo
        if not self.nombre_bd and self.connection_metadata:
            self.nombre_bd = self.connection_metadata.get('nombre_bd')
        
        # Logging para debugging
        logger.debug(
            f"[TENANT_CTX] Contexto creado: "
            f"cliente_id={self.client_id}, "
            f"db_type={self.database_type}, "
            f"bd={self.nombre_bd}"
        )
    
    def is_single_db(self) -> bool:
        """
        Verifica si el cliente usa Single-DB.
        
        Returns:
            True si es Single-DB, False si es Multi-DB
        
        Ejemplo:
            >>> context = get_tenant_context()
            >>> if context.is_single_db():
            ...     print("Cliente en bd_sistema")
        """
        return self.database_type == "single"
    
    def is_multi_db(self) -> bool:
        """
        Verifica si el cliente usa Multi-DB.
        
        Returns:
            True si es Multi-DB, False si es Single-DB
        
        Ejemplo:
            >>> context = get_tenant_context()
            >>> if context.is_multi_db():
            ...     print(f"Cliente en {context.nombre_bd}")
        """
        return self.database_type == "multi"
    
    def get_database_name(self) -> str:
        """
        Obtiene el nombre de la BD del cliente.
        
        Returns:
            Nombre de la BD (ej: 'bd_sistema' o 'bd_cliente_acme')
        
        Ejemplo:
            >>> context = get_tenant_context()
            >>> db_name = context.get_database_name()
            >>> print(f"BD actual: {db_name}")
        """
        return self.nombre_bd or "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el contexto a diccionario.
        
        Útil para logging, serialización, o pasar a funciones.
        
        Returns:
            Dict con todos los campos del contexto
        
        Ejemplo:
            >>> context = get_tenant_context()
            >>> logger.info(f"Contexto: {context.to_dict()}")
        """
        return {
            "client_id": self.client_id,
            "subdominio": self.subdominio,
            "codigo_cliente": self.codigo_cliente,
            "database_type": self.database_type,
            "nombre_bd": self.nombre_bd,
            "servidor": self.servidor,
            "puerto": self.puerto,
            "tipo_instalacion": self.tipo_instalacion,
            "connection_metadata": self.connection_metadata
        }
    
    def __repr__(self) -> str:
        """Representación string del contexto."""
        return (
            f"TenantContext("
            f"client_id={self.client_id}, "
            f"codigo={self.codigo_cliente}, "
            f"db_type={self.database_type}, "
            f"bd={self.nombre_bd}"
            f")"
        )


# ============================================
# FUNCIONES HELPER
# ============================================

def get_current_client_id() -> UUID:
    """
    Obtiene el cliente_id del contexto actual.
    
    IMPORTANTE: Mantiene compatibilidad con código existente que solo
    necesita el ID y no la metadata completa.
    
    Returns:
        ID del cliente actual
    
    Raises:
        RuntimeError: Si se llama fuera de un contexto de request válido
    
    Ejemplo:
        >>> client_id = get_current_client_id()
        >>> print(f"Cliente actual: {client_id}")
    """
    client_id = current_client_id.get()
    
    if client_id is None:
        raise RuntimeError(
            "Cliente ID no encontrado en el contexto. "
            "El TenantMiddleware no se ejecutó o falló."
        )
    
    return client_id


def get_tenant_context() -> TenantContext:
    """
    Obtiene el contexto completo del tenant (incluyendo metadata de conexión).
    
    NUEVO: Ahora incluye información sobre database_type, nombre_bd, etc.
    
    Returns:
        TenantContext con toda la información del cliente actual
    
    Raises:
        RuntimeError: Si se llama fuera de un contexto de request válido
    
    Ejemplo:
        >>> context = get_tenant_context()
        >>> print(f"Cliente: {context.client_id}")
        >>> print(f"DB Type: {context.database_type}")
        >>> if context.is_multi_db():
        ...     print(f"BD dedicada: {context.nombre_bd}")
    """
    context = current_tenant_context.get()
    
    if context is None:
        raise RuntimeError(
            "Contexto de Tenant no disponible. "
            "El request debe pasar por el TenantMiddleware."
        )
    
    return context


def try_get_current_client_id() -> Optional[UUID]:
    """
    Intenta obtener el cliente_id sin lanzar excepción si no existe.
    
    Útil para casos donde el contexto puede no estar disponible
    (scripts de fondo, inicialización, etc.)
    
    Returns:
        ID del cliente o None si no hay contexto
    
    Ejemplo:
        >>> client_id = try_get_current_client_id()
        >>> if client_id:
        ...     print(f"Cliente: {client_id}")
        ... else:
        ...     print("Sin contexto de cliente")
    """
    return current_client_id.get()


def try_get_tenant_context() -> Optional[TenantContext]:
    """
    Intenta obtener el contexto completo sin lanzar excepción.
    
    Útil para casos donde el contexto puede no estar disponible.
    
    Returns:
        TenantContext o None si no hay contexto
    
    Ejemplo:
        >>> context = try_get_tenant_context()
        >>> if context and context.is_multi_db():
        ...     print(f"Multi-DB: {context.nombre_bd}")
    """
    return current_tenant_context.get()


def get_database_type() -> str:
    """
    Obtiene el tipo de BD del cliente actual.
    
    Shortcut conveniente para obtener solo el database_type.
    
    Returns:
        "single" o "multi"
    
    Raises:
        RuntimeError: Si no hay contexto disponible
    
    Ejemplo:
        >>> db_type = get_database_type()
        >>> print(f"Tipo de BD: {db_type}")
    """
    context = get_tenant_context()
    return context.database_type


def get_database_name() -> str:
    """
    Obtiene el nombre de la BD del cliente actual.
    
    Shortcut conveniente para obtener solo el nombre de la BD.
    
    Returns:
        Nombre de la BD (ej: 'bd_sistema' o 'bd_cliente_acme')
    
    Raises:
        RuntimeError: Si no hay contexto disponible
    
    Ejemplo:
        >>> db_name = get_database_name()
        >>> print(f"BD actual: {db_name}")
    """
    context = get_tenant_context()
    return context.get_database_name()


# ============================================
# FUNCIONES DE CONTEXTO (para middleware)
# ============================================

def set_tenant_context(context: TenantContext) -> Any:
    """
    Establece el contexto del tenant.
    
    USO INTERNO: Solo debe ser llamada por TenantMiddleware.
    
    Args:
        context: TenantContext a establecer
    
    Returns:
        Token para resetear el contexto después
    
    Ejemplo (en middleware):
        >>> context = TenantContext(client_id=2, database_type="multi")
        >>> token = set_tenant_context(context)
        >>> try:
        ...     # ... procesar request ...
        ... finally:
        ...     reset_tenant_context(token)
    """
    # Establecer el contexto completo
    ctx_token = current_tenant_context.set(context)
    
    # También establecer el ID solo (para compatibilidad)
    id_token = current_client_id.set(context.client_id)
    
    logger.debug(f"[TENANT_CTX] Contexto establecido: {context}")
    
    # Retornar ambos tokens (encapsulados en tuple)
    return (ctx_token, id_token)


def reset_tenant_context(tokens: tuple) -> None:
    """
    Resetea el contexto del tenant.
    
    USO INTERNO: Solo debe ser llamada por TenantMiddleware en finally.
    
    Args:
        tokens: Tuple con (ctx_token, id_token) retornado por set_tenant_context
    
    Ejemplo (en middleware):
        >>> tokens = set_tenant_context(context)
        >>> try:
        ...     # ... procesar request ...
        ... finally:
        ...     reset_tenant_context(tokens)
    """
    ctx_token, id_token = tokens
    
    current_tenant_context.reset(ctx_token)
    current_client_id.reset(id_token)
    
    logger.debug("[TENANT_CTX] Contexto limpiado")


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

logger.info("Módulo tenant_context cargado (versión híbrida)")