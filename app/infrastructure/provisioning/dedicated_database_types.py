"""Contratos internos — DedicatedDatabaseExecutor (PR-F4-04)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedDatabaseProvisionRequest:
    """Entrada S3 saga — sin side effects HTTP."""

    cliente_id: UUID
    codigo_cliente: str
    servidor: Optional[str] = None
    database_name: Optional[str] = None
    app_login_name: Optional[str] = None
    app_login_password: Optional[str] = None


@dataclass(frozen=True, slots=True)
class DedicatedDatabaseProvisionResult:
    """Resultado provision física S3 — consumo interno saga F4-08."""

    cliente_id: UUID
    servidor: str
    database_name: str
    app_login_name: str
    app_login_password: str
    database_created: bool
    login_created: bool
    database_already_existed: bool
    login_already_existed: bool


@dataclass(frozen=True, slots=True)
class DedicatedDatabaseDropRequest:
    """Entrada compensación S3 — DROP DATABASE/login (PR-F4-10)."""

    cliente_id: UUID
    database_name: str
    app_login_name: str
    drop_login: bool = True


@dataclass(frozen=True, slots=True)
class DedicatedDatabaseDropResult:
    """Resultado DROP físico — idempotente si recursos ausentes."""

    cliente_id: UUID
    database_name: str
    app_login_name: str
    database_existed: bool
    database_dropped: bool
    login_existed: bool
    login_dropped: bool


__all__ = [
    "DedicatedDatabaseDropRequest",
    "DedicatedDatabaseDropResult",
    "DedicatedDatabaseProvisionRequest",
    "DedicatedDatabaseProvisionResult",
]
