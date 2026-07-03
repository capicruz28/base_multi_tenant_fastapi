# app/core/tenant/context.py
"""
Contexto de cliente (tenant) para arquitectura multi-tenant híbrida.

RD-03 / ADR-005: Installation Mode es metadata de infraestructura (L6).
La capa de aplicación (L5) consume identidad de tenant (client_id, subdominio,
codigo_cliente). El modo de instalación y routing de persistencia vive en
``connection_metadata`` resuelto por middleware + routing — no es API pública L5.

USO L5:
    from app.core.tenant.context import get_current_client_id, get_tenant_context

    client_id = get_current_client_id()
    context = get_tenant_context()
    print(f"Cliente: {context.client_id}")
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

current_client_id: ContextVar[Optional[UUID]] = ContextVar(
    'current_client_id',
    default=None
)

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
    Contexto de tenant para la capa de aplicación.

    Campos públicos L5:
        client_id, subdominio, codigo_cliente

    Metadata de routing (RD-03): almacenada en ``connection_metadata`` y
    campos legacy de init usados solo por infra/middleware durante transición F3.
    No serializar ni exponer vía helpers de módulo — ver F3-WP02/03.
    """

    client_id: UUID
    subdominio: Optional[str] = None
    codigo_cliente: Optional[str] = None

    connection_metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Init-only routing (infra transition — acceso directo deprecado post F3-01)
    database_type: str = field(default="single", repr=False)
    nombre_bd: Optional[str] = field(default=None, repr=False)
    servidor: Optional[str] = field(default=None, repr=False)
    puerto: Optional[int] = field(default=None, repr=False)
    tipo_instalacion: Optional[str] = field(default="cloud", repr=False)

    def __post_init__(self):
        if self.client_id is None:
            raise ValueError("client_id es obligatorio en TenantContext")

        md = dict(self.connection_metadata or {})
        md.setdefault("database_type", self.database_type)
        md.setdefault("tipo_instalacion", self.tipo_instalacion or "cloud")
        if self.nombre_bd:
            md.setdefault("nombre_bd", self.nombre_bd)
        if self.servidor is not None:
            md.setdefault("servidor", self.servidor)
        if self.puerto is not None:
            md.setdefault("puerto", self.puerto)
        self.connection_metadata = md

        if not self.nombre_bd and md.get("nombre_bd"):
            object.__setattr__(self, "nombre_bd", md.get("nombre_bd"))

        logger.debug(
            "[TENANT_CTX] Contexto creado: cliente_id=%s subdominio=%s",
            self.client_id,
            self.subdominio,
        )

    @classmethod
    def from_middleware_resolution(
        cls,
        *,
        client_id: UUID,
        subdominio: Optional[str],
        codigo_cliente: Optional[str],
        connection_metadata: Dict[str, Any],
    ) -> "TenantContext":
        """
        Factory interna — solo TenantMiddleware (RD-03).

        Enriquece connection_metadata sin exponer resolución de modo a L5.
        """
        md = dict(connection_metadata or {})
        return cls(
            client_id=client_id,
            subdominio=subdominio,
            codigo_cliente=codigo_cliente,
            connection_metadata=md,
            database_type=md.get("database_type", "single"),
            nombre_bd=md.get("nombre_bd"),
            servidor=md.get("servidor"),
            puerto=md.get("puerto"),
            tipo_instalacion=md.get("tipo_instalacion", "cloud"),
        )

    def is_single_db(self) -> bool:
        """Deprecated infra transition — no usar en L5 (F3-WP03)."""
        return self.database_type == "single"

    def is_multi_db(self) -> bool:
        """Deprecated infra transition — no usar en L5 (F3-WP03)."""
        return self.database_type == "multi"

    def get_database_name(self) -> str:
        """Deprecated infra transition — routing vía L6, no L5."""
        return self.nombre_bd or "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialización L5 — sin Installation Mode ni metadata de routing (RD-03).
        """
        return {
            "client_id": self.client_id,
            "subdominio": self.subdominio,
            "codigo_cliente": self.codigo_cliente,
        }

    def __repr__(self) -> str:
        return (
            f"TenantContext("
            f"client_id={self.client_id}, "
            f"subdominio={self.subdominio!r}, "
            f"codigo={self.codigo_cliente!r}"
            f")"
        )


# ============================================
# FUNCIONES HELPER
# ============================================

def get_current_client_id() -> UUID:
    """Obtiene el cliente_id del contexto actual."""
    client_id = current_client_id.get()

    if client_id is None:
        raise RuntimeError(
            "Cliente ID no encontrado en el contexto. "
            "El TenantMiddleware no se ejecutó o falló."
        )

    return client_id


def get_tenant_context() -> TenantContext:
    """Obtiene el contexto de tenant (identidad L5; sin Installation Mode público)."""
    context = current_tenant_context.get()

    if context is None:
        raise RuntimeError(
            "Contexto de Tenant no disponible. "
            "El request debe pasar por el TenantMiddleware."
        )

    return context


def try_get_current_client_id() -> Optional[UUID]:
    """Intenta obtener el cliente_id sin lanzar excepción."""
    return current_client_id.get()


def try_get_tenant_context() -> Optional[TenantContext]:
    """Intenta obtener el contexto completo sin lanzar excepción."""
    return current_tenant_context.get()


def get_database_type() -> str:
    """
    Deprecated (RD-03 / PR-F3-01).

    Retained only for ``app.core.tenant`` package re-export compat.
    L5 must not call — use routing layer (F3-WP02+).
    """
    return get_tenant_context().database_type


def get_database_name() -> str:
    """
    Deprecated (RD-03 / PR-F3-01).

    Retained only for ``app.core.tenant`` package re-export compat.
    """
    return get_tenant_context().get_database_name()


# ============================================
# FUNCIONES DE CONTEXTO (para middleware)
# ============================================

def set_tenant_context(context: TenantContext) -> Any:
    """Establece el contexto del tenant. USO INTERNO: TenantMiddleware."""
    ctx_token = current_tenant_context.set(context)
    id_token = current_client_id.set(context.client_id)

    logger.debug("[TENANT_CTX] Contexto establecido: %s", context)

    return (ctx_token, id_token)


def reset_tenant_context(tokens: tuple) -> None:
    """Resetea el contexto del tenant. USO INTERNO: TenantMiddleware."""
    ctx_token, id_token = tokens

    current_tenant_context.reset(ctx_token)
    current_client_id.reset(id_token)

    logger.debug("[TENANT_CTX] Contexto limpiado")


logger.info("Módulo tenant context cargado (RD-03 L5 identity)")
