"""Cliente DDL SQL Server — abstracción inyectable (PR-F4-04)."""
from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager
from typing import Optional, Protocol, runtime_checkable

from app.core.config import settings
from app.core.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


@runtime_checkable
class DedicatedDdlSession(Protocol):
    """Sesión DDL reutilizable sobre una conexión ODBC (unidad de trabajo S3)."""

    async def scalar_int(self, sql: str) -> Optional[int]:
        ...

    async def scalar_str(self, sql: str) -> Optional[str]:
        ...

    async def execute(self, sql: str) -> None:
        ...


@runtime_checkable
class DedicatedDdlSessionContext(AbstractAsyncContextManager[DedicatedDdlSession], Protocol):
    """Context manager async que entrega una ``DedicatedDdlSession``."""

    async def __aenter__(self) -> DedicatedDdlSession:
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...


@runtime_checkable
class DedicatedDdlClient(Protocol):
    """Puerto async para ejecutar DDL en SQL Server (master o tenant DB)."""

    def open_session(
        self,
        *,
        database: str = "master",
    ) -> DedicatedDdlSessionContext:
        ...

    async def scalar_int(self, sql: str, *, database: str = "master") -> Optional[int]:
        ...

    async def scalar_str(self, sql: str, *, database: str = "master") -> Optional[str]:
        ...

    async def execute(self, sql: str, *, database: str = "master") -> None:
        ...


def validate_provisioning_ddl_settings() -> None:
    missing = []
    if not settings.PROVISIONING_DDL_SERVER:
        missing.append("PROVISIONING_DDL_SERVER")
    if not settings.PROVISIONING_DDL_USER:
        missing.append("PROVISIONING_DDL_USER")
    if not settings.PROVISIONING_DDL_PASSWORD:
        missing.append("PROVISIONING_DDL_PASSWORD")
    if missing:
        raise ValidationError(
            detail=(
                "Credenciales DDL platform incompletas: "
                f"{', '.join(missing)}."
            ),
            internal_code="PROVISIONING_DDL_CONFIG_INCOMPLETE",
        )


def build_ddl_connection_string(*, database: str) -> str:
    validate_provisioning_ddl_settings()
    return (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={settings.PROVISIONING_DDL_SERVER},{settings.PROVISIONING_DDL_PORT};"
        f"DATABASE={database};"
        f"UID={settings.PROVISIONING_DDL_USER};"
        f"PWD={settings.PROVISIONING_DDL_PASSWORD};"
        "TrustServerCertificate=yes;"
    )


class AioOdbcDedicatedDdlSession:
    """Operaciones DDL sobre una conexión aioodbc ya abierta (autocommit=True)."""

    def __init__(self, conn) -> None:
        self._conn = conn

    async def scalar_int(self, sql: str) -> Optional[int]:
        async with self._conn.cursor() as cursor:
            await cursor.execute(sql)
            row = await cursor.fetchone()
            if not row:
                return None
            return int(row[0]) if row[0] is not None else None

    async def scalar_str(self, sql: str) -> Optional[str]:
        async with self._conn.cursor() as cursor:
            await cursor.execute(sql)
            row = await cursor.fetchone()
            if not row or row[0] is None:
                return None
            return str(row[0])

    async def execute(self, sql: str) -> None:
        async with self._conn.cursor() as cursor:
            await cursor.execute(sql)


class _AioOdbcDedicatedDdlSessionContext:
    """Abre una conexión DDL única con autocommit=True para toda la unidad de trabajo."""

    def __init__(self, *, database: str) -> None:
        self._database = database
        self._connect_ctx = None

    async def __aenter__(self) -> AioOdbcDedicatedDdlSession:
        try:
            import aioodbc
        except ImportError as exc:
            raise DatabaseError(
                detail="aioodbc no disponible para executor DDL dedicated.",
                internal_code="DDL_CLIENT_UNAVAILABLE",
            ) from exc

        conn_str = build_ddl_connection_string(database=self._database)
        self._connect_ctx = aioodbc.connect(dsn=conn_str, autocommit=True)
        conn = await self._connect_ctx.__aenter__()
        return AioOdbcDedicatedDdlSession(conn)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._connect_ctx is not None:
            await self._connect_ctx.__aexit__(exc_type, exc_val, exc_tb)
            self._connect_ctx = None


class AioOdbcDedicatedDdlClient:
    """Implementación real vía aioodbc — staging/integration only."""

    def open_session(
        self,
        *,
        database: str = "master",
    ) -> _AioOdbcDedicatedDdlSessionContext:
        return _AioOdbcDedicatedDdlSessionContext(database=database)

    async def scalar_int(self, sql: str, *, database: str = "master") -> Optional[int]:
        try:
            async with self.open_session(database=database) as session:
                return await session.scalar_int(sql)
        except DatabaseError:
            raise
        except Exception as exc:
            logger.exception("Error DDL scalar_int database=%s", database)
            raise DatabaseError(
                detail="Error ejecutando consulta DDL de plataforma.",
                internal_code="DDL_SCALAR_FAILED",
            ) from exc

    async def scalar_str(self, sql: str, *, database: str = "master") -> Optional[str]:
        try:
            async with self.open_session(database=database) as session:
                return await session.scalar_str(sql)
        except DatabaseError:
            raise
        except Exception as exc:
            logger.exception("Error DDL scalar_str database=%s", database)
            raise DatabaseError(
                detail="Error ejecutando consulta DDL de plataforma.",
                internal_code="DDL_SCALAR_FAILED",
            ) from exc

    async def execute(self, sql: str, *, database: str = "master") -> None:
        try:
            async with self.open_session(database=database) as session:
                await session.execute(sql)
        except DatabaseError:
            raise
        except Exception as exc:
            logger.exception("Error DDL execute database=%s", database)
            raise DatabaseError(
                detail="Error ejecutando sentencia DDL de plataforma.",
                internal_code="DDL_EXECUTE_FAILED",
            ) from exc


def create_default_ddl_client() -> DedicatedDdlClient:
    if not settings.PROVISIONING_DDL_EXECUTOR_ENABLED:
        raise ValidationError(
            detail=(
                "Executor DDL dedicated deshabilitado "
                "(PROVISIONING_DDL_EXECUTOR_ENABLED=false)."
            ),
            internal_code="PROVISIONING_DDL_EXECUTOR_DISABLED",
        )
    validate_provisioning_ddl_settings()
    return AioOdbcDedicatedDdlClient()


__all__ = [
    "AioOdbcDedicatedDdlClient",
    "AioOdbcDedicatedDdlSession",
    "DedicatedDdlClient",
    "DedicatedDdlSession",
    "DedicatedDdlSessionContext",
    "build_ddl_connection_string",
    "create_default_ddl_client",
    "validate_provisioning_ddl_settings",
]
