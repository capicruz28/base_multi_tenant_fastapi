"""
F13-1 — Tipos normativos para resolución de store por operación (F13-A1 §8).

Contrato de infraestructura sin wire-up productivo. Referencia: F13-A1, F13-B1, RI-39.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, FrozenSet, Optional
from uuid import UUID

from app.core.exceptions import DatabaseError
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.routing import (
    DEFAULT_DATABASE_TYPE,
    DEDICATED_ROUTE_FAIL_CLOSED,
    _validate_dedicated_route_metadata,
)
from app.infrastructure.database.connection_async import DatabaseConnection


class OperationPlane(str, Enum):
    CONTROL_PLANE = "control_plane"
    TENANT_DATA = "tenant_data"


class SessionKind(str, Enum):
    TENANT_SESSION = "tenant_session"
    PLATFORM_OPERATOR = "platform_operator"
    IMPERSONATION = "impersonation"


class EngineKind(str, Enum):
    SHARED_SINGLE = "shared_single"
    DEDICATED_MULTI = "dedicated_multi"


@dataclass(frozen=True, slots=True)
class OperationDescriptor:
    """Entrada al algoritmo de resolución — Host HTTP no participa."""

    target_cliente_id: UUID
    operation_plane: OperationPlane
    tables: Optional[FrozenSet[str]] = None
    session_kind: SessionKind = SessionKind.TENANT_SESSION
    session_target_cliente_id: Optional[UUID] = None


@dataclass(frozen=True, slots=True)
class InstallationProfile:
    """Installation Profile derivado de metadata CP del target (vía routing)."""

    cliente_id: UUID
    tipo_instalacion: str
    engine_kind: EngineKind
    database_type: str
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def from_metadata(cls, cliente_id: UUID, metadata: dict[str, Any]) -> InstallationProfile:
        """Delega validación RI-39 en routing — sin duplicar reglas."""
        _validate_dedicated_route_metadata(metadata, cliente_id)
        database_type = metadata.get("database_type", DEFAULT_DATABASE_TYPE)
        tipo_instalacion = metadata.get("tipo_instalacion") or "shared"

        if database_type == "multi":
            engine_kind = EngineKind.DEDICATED_MULTI
        elif database_type == "single":
            engine_kind = EngineKind.SHARED_SINGLE
        else:
            raise DatabaseError(
                detail=(
                    f"Tenant {cliente_id} con database_type={database_type!r} "
                    f"no soportado para tenant_data (RI-39)."
                ),
                internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
            )

        return cls(
            cliente_id=cliente_id,
            tipo_instalacion=tipo_instalacion,
            engine_kind=engine_kind,
            database_type=database_type,
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class ExecuteQueryIntent:
    """Salida unificada — kwargs compatibles con ``execute_query``."""

    connection_type: DatabaseConnection
    client_id: Optional[UUID]
    identity_scope: IdentityScope
    operation_class: str
    engine_kind: EngineKind
    database_type: str

    def to_execute_query_kwargs(self) -> dict[str, Any]:
        """Kwargs aceptados por ``execute_query`` (F12-E2B3N / RD-07)."""
        return {
            "connection_type": self.connection_type,
            "client_id": self.client_id,
            "identity_scope": self.identity_scope,
            "operation_class": self.operation_class,
        }


__all__ = [
    "EngineKind",
    "ExecuteQueryIntent",
    "InstallationProfile",
    "OperationDescriptor",
    "OperationPlane",
    "SessionKind",
]
