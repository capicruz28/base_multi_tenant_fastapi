# app/core/tenant_context.py
"""
Define el contexto de cliente (tenant) para el manejo de arquitectura multi-tenant.
Utiliza ContextVar para almacenar el ID del cliente actual de forma asíncrona
y segura por cada solicitud (request).
"""

from contextvars import ContextVar
from typing import Optional
from dataclasses import dataclass

# El ID del cliente actual se almacenará aquí. None por defecto hasta que el middleware lo establezca.
# El ContextVar es esencial para mantener el aislamiento de datos en entornos asíncronos (como FastAPI).
current_client_id: ContextVar[Optional[int]] = ContextVar('current_client_id', default=None)

# Definición de la estructura de datos que encapsula el contexto del tenant
@dataclass
class TenantContext:
    """Clase de datos para el contexto del cliente actual."""
    client_id: Optional[int]
    subdominio: Optional[str]
    codigo_cliente: Optional[str]

# Almacena el contexto completo del tenant (incluyendo subdominio y código)
current_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar('current_tenant_context', default=None)


def get_current_client_id() -> int:
    """
    Obtiene el cliente_id del contexto actual de la solicitud.
    Lanza un error si se llama fuera de un contexto de tenant válido.
    """
    client_id = current_client_id.get()
    if client_id is None:
        # Esto debería ser capturado por el middleware, pero es una protección.
        raise RuntimeError("Cliente ID no encontrado en el contexto de la solicitud. El TenantMiddleware no se ejecutó o falló.")
    return client_id

def get_tenant_context() -> TenantContext:
    """
    Obtiene el contexto completo del tenant.
    """
    context = current_tenant_context.get()
    if context is None:
        # Usamos el contexto del cliente raíz (SYSTEM) si el middleware no lo estableció (ej. tareas de fondo, scripts)
        # Esto es un placeholder. En un entorno real se debe asegurar que estos scripts sean 'tenant-aware'.
        # Por ahora, levantamos un error o devolvemos un contexto nulo/default.
        # Si se requiere un contexto para operar (ej: servicios), se debe llamar a get_current_client_id()
        raise RuntimeError("Contexto de Tenant no disponible. El request debe pasar por el TenantMiddleware.")
    return context