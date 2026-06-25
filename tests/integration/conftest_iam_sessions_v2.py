"""
Harness IAM Session Management V2 — Cluster 8 Fase 0.

conftest_iam_sessions_v2.py — fixtures y pre-flight para integration/E2E V2.
Cargado vía pytest_plugins en tests/conftest.py.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Iterator, List, Optional
from uuid import UUID

import pytest

from tests.integration.helpers.iam_v2_teardown import (
    register_iam_v2_test_user,
    teardown_iam_v2_sessions,
)

# UUID de referencia para allowlist parcial (CT-04 / fixtures Fase 1+)
IAM_V2_FIXTURE_TENANT_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
IAM_V2_FIXTURE_TENANT_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

V031_TABLES = ("user_session", "token_family", "refresh_tokens")

_SKIP_DB_ENV = "SKIP_DB_INTEGRATION_TESTS"


def skip_if_no_db() -> None:
    """Skip si integration BD está deshabilitada o sin credenciales."""
    if os.getenv(_SKIP_DB_ENV, "").lower() in {"1", "true", "yes"}:
        pytest.skip(f"{_SKIP_DB_ENV} activo")

    try:
        import pyodbc  # noqa: F401
    except ImportError:
        pytest.skip("pyodbc no disponible")

    from app.core.config import settings

    if not settings.DB_SERVER or not settings.DB_DATABASE:
        pytest.skip("Credenciales BD no configuradas (DB_SERVER / DB_DATABASE)")


def skip_if_no_redis() -> None:
    """Skip si Redis no está habilitado o no responde."""
    from app.core.config import settings

    if not settings.ENABLE_REDIS_CACHE:
        pytest.skip("ENABLE_REDIS_CACHE=false")

    try:
        import redis
    except ImportError:
        pytest.skip("paquete redis no disponible")

    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    )
    try:
        if not client.ping():
            pytest.skip("Redis no responde a PING")
    except Exception as exc:
        pytest.skip(f"Redis no accesible: {exc}")
    finally:
        client.close()


def verify_sqlserver_env() -> List[str]:
    """Pre-flight: variables SQL Server. Retorna lista de errores (vacía = OK)."""
    errors: List[str] = []
    if os.getenv(_SKIP_DB_ENV, "").lower() in {"1", "true", "yes"}:
        errors.append(f"{_SKIP_DB_ENV} está activo")
    try:
        import pyodbc  # noqa: F401
    except ImportError:
        errors.append("pyodbc no instalado")

    from app.core.config import settings

    for name, value in (
        ("DB_SERVER", settings.DB_SERVER),
        ("DB_DATABASE", settings.DB_DATABASE),
        ("DB_USER", settings.DB_USER),
        ("DB_PASSWORD", settings.DB_PASSWORD),
    ):
        if not value:
            errors.append(f"variable {name} no configurada")
    return errors


def verify_v031_schema() -> List[str]:
    """Pre-flight: tablas V031 presentes en INFORMATION_SCHEMA."""
    errors: List[str] = []
    skip_if_no_db()
    try:
        import pyodbc
        from app.core.config import settings
    except Exception as exc:
        return [str(exc)]

    conn = pyodbc.connect(settings.get_database_url(is_admin=False))
    try:
        cur = conn.cursor()
        for table_name in V031_TABLES:
            cur.execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?",
                table_name,
            )
            if cur.fetchone() is None:
                errors.append(f"tabla V031 ausente: {table_name}")
    finally:
        conn.close()
    return errors


def verify_feature_flag_env() -> List[str]:
    """Pre-flight: variables feature flag parseables (no exige V2 activo)."""
    errors: List[str] = []
    raw = os.getenv("IAM_SESSION_MANAGEMENT_V2_ENABLED", "false").strip().lower()
    if raw not in {"true", "false", "1", "0", "yes", "no"}:
        errors.append(
            f"IAM_SESSION_MANAGEMENT_V2_ENABLED valor no reconocido: {raw!r}"
        )

    allowlist = os.getenv("IAM_SESSION_V2_TENANT_ALLOWLIST", "")
    for part in allowlist.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            UUID(token)
        except ValueError:
            errors.append(f"UUID inválido en IAM_SESSION_V2_TENANT_ALLOWLIST: {token!r}")
    return errors


def run_iam_v2_preflight(*, require_schema: bool = True) -> None:
    """Ejecuta checklist pre-flight; pytest.skip si falla."""
    env_errors = verify_sqlserver_env()
    if env_errors:
        pytest.skip(f"Pre-flight SQL Server: {'; '.join(env_errors)}")

    flag_errors = verify_feature_flag_env()
    if flag_errors:
        pytest.skip(f"Pre-flight Feature Flag: {'; '.join(flag_errors)}")

    if require_schema:
        schema_errors = verify_v031_schema()
        if schema_errors:
            pytest.skip(f"Pre-flight V031: {'; '.join(schema_errors)}")


@contextmanager
def iam_v2_flag_all_tenants_on() -> Iterator[None]:
    """Flag ON + allowlist vacía → V2 para todos los tenants (§14)."""
    from app.core.config import settings

    previous_enabled = settings._iam_session_management_v2_enabled_raw
    previous_allowlist = settings.IAM_SESSION_V2_TENANT_ALLOWLIST
    settings._iam_session_management_v2_enabled_raw = "true"
    settings.IAM_SESSION_V2_TENANT_ALLOWLIST = ""
    try:
        yield
    finally:
        settings._iam_session_management_v2_enabled_raw = previous_enabled
        settings.IAM_SESSION_V2_TENANT_ALLOWLIST = previous_allowlist


@contextmanager
def iam_v2_flag_allowlist_on(
    tenant_id: UUID = IAM_V2_FIXTURE_TENANT_A,
) -> Iterator[None]:
    """Flag ON + allowlist explícita con un solo tenant."""
    from app.core.config import settings

    previous_enabled = settings._iam_session_management_v2_enabled_raw
    previous_allowlist = settings.IAM_SESSION_V2_TENANT_ALLOWLIST
    settings._iam_session_management_v2_enabled_raw = "true"
    settings.IAM_SESSION_V2_TENANT_ALLOWLIST = str(tenant_id)
    try:
        yield
    finally:
        settings._iam_session_management_v2_enabled_raw = previous_enabled
        settings.IAM_SESSION_V2_TENANT_ALLOWLIST = previous_allowlist


@contextmanager
def iam_v2_flag_off() -> Iterator[None]:
    """Flag global OFF."""
    from app.core.config import settings

    previous_enabled = settings._iam_session_management_v2_enabled_raw
    previous_allowlist = settings.IAM_SESSION_V2_TENANT_ALLOWLIST
    settings._iam_session_management_v2_enabled_raw = "false"
    settings.IAM_SESSION_V2_TENANT_ALLOWLIST = ""
    try:
        yield
    finally:
        settings._iam_session_management_v2_enabled_raw = previous_enabled
        settings.IAM_SESSION_V2_TENANT_ALLOWLIST = previous_allowlist


# ---------------------------------------------------------------------------
# Fixtures (Fase 0 — pre-flight y flags; seeds en Fase 1+)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def iam_v2_db_available() -> None:
    """Gate sesión: SQL Server accesible."""
    skip_if_no_db()


@pytest.fixture(scope="session")
def iam_v2_schema_ready(iam_v2_db_available) -> None:
    """Gate sesión: schema V031 presente."""
    schema_errors = verify_v031_schema()
    if schema_errors:
        pytest.skip(f"Pre-flight V031: {'; '.join(schema_errors)}")


@pytest.fixture
def iam_v2_preflight(iam_v2_schema_ready) -> None:
    """Checklist pre-flight completo por test integration IAM V2."""
    run_iam_v2_preflight(require_schema=True)


@pytest.fixture
def iam_v2_redis_available() -> None:
    """Gate: Redis accesible."""
    skip_if_no_redis()


@pytest.fixture
def iam_v2_flag_all_tenants_on_fixture() -> Generator[None, None, None]:
    with iam_v2_flag_all_tenants_on():
        yield


@pytest.fixture
def iam_v2_flag_allowlist_on_fixture() -> Generator[None, None, None]:
    with iam_v2_flag_allowlist_on(IAM_V2_FIXTURE_TENANT_A):
        yield


@pytest.fixture
def iam_v2_flag_off_fixture() -> Generator[None, None, None]:
    with iam_v2_flag_off():
        yield


@pytest.fixture
async def iam_v2_teardown_sessions(request) -> Generator[None, None, None]:
    """
    Teardown autouse-ready: registra usuarios vía register_iam_v2_test_user.
    Requiere atributos en request.node: iam_v2_cliente_id, iam_v2_test_users.
    """
    yield
    cliente_id: Optional[UUID] = getattr(request.node, "iam_v2_cliente_id", None)
    usuario_ids: List[UUID] = getattr(request.node, "iam_v2_test_users", [])
    if cliente_id and usuario_ids:
        await teardown_iam_v2_sessions(
            cliente_id=cliente_id,
            usuario_ids=usuario_ids,
        )


# ---------------------------------------------------------------------------
# Seeds §10 + helpers Fases 1–4 (requeridos por MT/I/E/CT)
# ---------------------------------------------------------------------------

from dataclasses import dataclass
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select


@dataclass(frozen=True)
class IamV2Seeds:
    """Datos mínimos de entorno IAM V2 (§10)."""

    tenant_a_id: UUID
    tenant_b_id: UUID
    subdominio_a: str
    subdominio_b: str
    user_a_id: UUID
    user_b_id: UUID
    admin_a_id: UUID
    user_a_username: str
    user_a_password: str
    user_b_username: str
    user_b_password: str
    admin_a_username: str
    admin_a_password: str
    empresa_a1_id: Optional[UUID]
    empresa_a2_id: Optional[UUID]


def _env_uuid(name: str, default: Optional[UUID] = None) -> Optional[UUID]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return UUID(raw)


def _sync_fetch_one(query: str, params: tuple) -> Optional[tuple]:
    import pyodbc
    from app.core.config import settings

    conn = pyodbc.connect(settings.get_database_url(is_admin=False))
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        conn.close()


def load_iam_v2_seeds_sync() -> Optional[IamV2Seeds]:
    """Resuelve seeds §10 desde env + BD (sync para fixture session)."""
    skip_if_no_db()

    sub_a = os.getenv("IAM_V2_TEST_SUBDOMINIO_A", "TENANT_IAM_V2_A").strip()
    sub_b = os.getenv("IAM_V2_TEST_SUBDOMINIO_B", "TENANT_IAM_V2_B").strip()
    user_a_name = os.getenv("IAM_V2_TEST_USER_A_USERNAME", "iam_v2_user_a").strip()
    user_b_name = os.getenv("IAM_V2_TEST_USER_B_USERNAME", "iam_v2_user_b").strip()
    admin_a_name = os.getenv("IAM_V2_TEST_ADMIN_A_USERNAME", "iam_v2_admin_a").strip()
    user_a_pass = os.getenv("IAM_V2_TEST_USER_A_PASSWORD", "Test1234!")
    user_b_pass = os.getenv("IAM_V2_TEST_USER_B_PASSWORD", "Test1234!")
    admin_a_pass = os.getenv("IAM_V2_TEST_ADMIN_A_PASSWORD", "Admin1234!")

    tenant_a = _env_uuid("IAM_V2_TEST_TENANT_A_CLIENTE_ID", IAM_V2_FIXTURE_TENANT_A)
    tenant_b = _env_uuid("IAM_V2_TEST_TENANT_B_CLIENTE_ID", IAM_V2_FIXTURE_TENANT_B)

    row_a = _sync_fetch_one(
        "SELECT cliente_id FROM cliente WHERE subdominio = ? AND es_activo = 1",
        (sub_a,),
    )
    if row_a:
        tenant_a = UUID(str(row_a[0]))

    row_b = _sync_fetch_one(
        "SELECT cliente_id FROM cliente WHERE subdominio = ? AND es_activo = 1",
        (sub_b,),
    )
    if row_b:
        tenant_b = UUID(str(row_b[0]))

    if not tenant_a or not tenant_b:
        return None

    user_a_row = _sync_fetch_one(
        "SELECT usuario_id FROM usuario WHERE cliente_id = ? AND nombre_usuario = ? AND es_activo = 1",
        (str(tenant_a), user_a_name),
    )
    user_b_row = _sync_fetch_one(
        "SELECT usuario_id FROM usuario WHERE cliente_id = ? AND nombre_usuario = ? AND es_activo = 1",
        (str(tenant_b), user_b_name),
    )
    admin_a_row = _sync_fetch_one(
        "SELECT usuario_id FROM usuario WHERE cliente_id = ? AND nombre_usuario = ? AND es_activo = 1",
        (str(tenant_a), admin_a_name),
    )
    if not user_a_row or not user_b_row or not admin_a_row:
        return None

    empresa_a1 = _env_uuid("IAM_V2_TEST_EMPRESA_A1_ID")
    empresa_a2 = _env_uuid("IAM_V2_TEST_EMPRESA_A2_ID")
    if empresa_a1 is None or empresa_a2 is None:
        import pyodbc
        from app.core.config import settings

        conn = pyodbc.connect(settings.get_database_url(is_admin=False))
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TOP 2 empresa_id FROM org_empresa
                WHERE cliente_id = ? AND es_activo = 1
                ORDER BY fecha_creacion ASC
                """,
                (str(tenant_a),),
            )
            cur_rows = cur.fetchall()
        finally:
            conn.close()
        if len(cur_rows) >= 2:
            empresa_a1 = empresa_a1 or UUID(str(cur_rows[0][0]))
            empresa_a2 = empresa_a2 or UUID(str(cur_rows[1][0]))
        elif len(cur_rows) == 1:
            empresa_a1 = empresa_a1 or UUID(str(cur_rows[0][0]))

    return IamV2Seeds(
        tenant_a_id=tenant_a,
        tenant_b_id=tenant_b,
        subdominio_a=sub_a,
        subdominio_b=sub_b,
        user_a_id=UUID(str(user_a_row[0])),
        user_b_id=UUID(str(user_b_row[0])),
        admin_a_id=UUID(str(admin_a_row[0])),
        user_a_username=user_a_name,
        user_a_password=user_a_pass,
        user_b_username=user_b_name,
        user_b_password=user_b_pass,
        admin_a_username=admin_a_name,
        admin_a_password=admin_a_pass,
        empresa_a1_id=empresa_a1,
        empresa_a2_id=empresa_a2,
    )


def iam_v2_tenant_origin(subdominio: str, fe_port: str = "5173") -> str:
    from app.core.config import settings

    base = settings.BASE_DOMAIN or "app.local"
    return f"http://{subdominio}.{base}:{fe_port}"


def iam_v2_mobile_headers(subdominio: str) -> dict:
    return {
        "Origin": iam_v2_tenant_origin(subdominio),
        "X-Client-Type": "mobile",
    }


async def iam_v2_count_v3_rows(
    *,
    cliente_id: UUID,
    usuario_id: UUID,
) -> dict:
    from app.infrastructure.database.queries_async import execute_query

    async def _count(table, extra=None):
        stmt = select(func.count().label("total")).select_from(table).where(
            and_(
                table.c.cliente_id == cliente_id,
                table.c.usuario_id == usuario_id,
            )
        )
        if extra is not None:
            stmt = stmt.where(extra)
        rows = await execute_query(stmt, client_id=cliente_id)
        return int(rows[0].get("total", 0) if rows else 0)

    from app.infrastructure.database.tables import (
        RefreshTokensTable,
        TokenFamilyTable,
        UserSessionTable,
    )

    return {
        "user_session": await _count(UserSessionTable),
        "token_family": await _count(TokenFamilyTable),
        "refresh_tokens": await _count(RefreshTokensTable),
    }


async def iam_v2_create_session_via_c18(
    *,
    cliente_id: UUID,
    usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
    platform: str = "web",
) -> dict:
    """Crea sesión V3 vía C18 (integration helper)."""
    from app.core.application.unit_of_work import UnitOfWork
    from app.infrastructure.database.queries.auth.session import (
        session_transaction_core as stx,
    )
    from app.modules.auth.application.services.refresh_token_service import (
        RefreshTokenService,
    )

    token_plain = secrets.token_urlsafe(32)
    token_hash = RefreshTokenService.hash_token(token_plain)
    expires = datetime.now(timezone.utc) + timedelta(days=7)

    async with UnitOfWork(client_id=cliente_id) as uow:
        result = await stx.create_session_with_token_tx(
            uow,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            session_expires_at=expires,
            token_hash=token_hash,
            token_expires_at=expires,
            platform=platform,
            empresa_id=empresa_id,
        )
    return {**result, "token_hash": token_hash, "token_plain": token_plain}


@pytest.fixture(scope="session")
def iam_v2_seeds(iam_v2_schema_ready) -> IamV2Seeds:
    seeds = load_iam_v2_seeds_sync()
    if seeds is None:
        pytest.skip(
            "Seeds §10 incompletos: configure tenants TENANT_IAM_V2_A/B, "
            "usuarios iam_v2_user_a/b, iam_v2_admin_a y ≥2 empresas en tenant A"
        )
    return seeds


@pytest.fixture
def iam_v2_tenant_a(iam_v2_seeds: IamV2Seeds) -> UUID:
    return iam_v2_seeds.tenant_a_id


@pytest.fixture
def iam_v2_tenant_b(iam_v2_seeds: IamV2Seeds) -> UUID:
    return iam_v2_seeds.tenant_b_id


@pytest.fixture
def iam_v2_user_a(iam_v2_seeds: IamV2Seeds) -> UUID:
    return iam_v2_seeds.user_a_id


@pytest.fixture
def iam_v2_user_b(iam_v2_seeds: IamV2Seeds) -> UUID:
    return iam_v2_seeds.user_b_id


@pytest.fixture
def iam_v2_user_admin_a(iam_v2_seeds: IamV2Seeds) -> UUID:
    return iam_v2_seeds.admin_a_id


@pytest.fixture
def iam_v2_credentials_a(iam_v2_seeds: IamV2Seeds) -> dict:
    return {
        "username": iam_v2_seeds.user_a_username,
        "password": iam_v2_seeds.user_a_password,
        "subdominio": iam_v2_seeds.subdominio_a,
        "cliente_id": iam_v2_seeds.tenant_a_id,
    }


@pytest.fixture
def iam_v2_credentials_admin_a(iam_v2_seeds: IamV2Seeds) -> dict:
    return {
        "username": iam_v2_seeds.admin_a_username,
        "password": iam_v2_seeds.admin_a_password,
        "subdominio": iam_v2_seeds.subdominio_a,
        "cliente_id": iam_v2_seeds.tenant_a_id,
    }


@pytest.fixture
def iam_v2_empresa_a1(iam_v2_seeds: IamV2Seeds) -> UUID:
    if iam_v2_seeds.empresa_a1_id is None:
        pytest.skip("empresa_a1 no configurada (§10 E-09)")
    return iam_v2_seeds.empresa_a1_id


@pytest.fixture
def iam_v2_empresa_a2(iam_v2_seeds: IamV2Seeds) -> UUID:
    if iam_v2_seeds.empresa_a2_id is None:
        pytest.skip("empresa_a2 no configurada (§10 E-09)")
    return iam_v2_seeds.empresa_a2_id


@pytest.fixture
def iam_v2_tenant_context_a(iam_v2_seeds: IamV2Seeds):
    from app.core.tenant.context import TenantContext, reset_tenant_context, set_tenant_context

    ctx = TenantContext(
        client_id=iam_v2_seeds.tenant_a_id,
        subdominio=iam_v2_seeds.subdominio_a,
        codigo_cliente=iam_v2_seeds.subdominio_a,
        database_type="shared",
        nombre_bd="",
        servidor="localhost",
        puerto=1433,
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def iam_v2_uow(iam_v2_tenant_a):
    from app.core.application.unit_of_work import UnitOfWork

    return UnitOfWork(client_id=iam_v2_tenant_a)


@pytest.fixture
def iam_v2_http_client():
    from app.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
async def iam_v2_autouse_teardown(request, iam_v2_seeds: IamV2Seeds):
    """Teardown §11 autouse para módulos IAM V2 integration."""
    request.node.iam_v2_teardown_registry = {}
    yield
    registry: dict = getattr(request.node, "iam_v2_teardown_registry", {})
    for cliente_id, usuario_ids in registry.items():
        if usuario_ids:
            await teardown_iam_v2_sessions(
                cliente_id=cliente_id,
                usuario_ids=list(usuario_ids),
            )


def iam_v2_register_teardown(
    request,
    *,
    cliente_id: UUID,
    usuario_id: UUID,
) -> None:
    registry: dict = getattr(request.node, "iam_v2_teardown_registry", {})
    users: set = registry.setdefault(cliente_id, set())
    users.add(usuario_id)
    request.node.iam_v2_teardown_registry = registry


__all__ = [
    "IAM_V2_FIXTURE_TENANT_A",
    "IAM_V2_FIXTURE_TENANT_B",
    "IamV2Seeds",
    "iam_v2_count_v3_rows",
    "iam_v2_create_session_via_c18",
    "iam_v2_flag_all_tenants_on",
    "iam_v2_flag_allowlist_on",
    "iam_v2_flag_off",
    "iam_v2_mobile_headers",
    "iam_v2_register_teardown",
    "iam_v2_tenant_origin",
    "load_iam_v2_seeds_sync",
    "register_iam_v2_test_user",
    "run_iam_v2_preflight",
    "skip_if_no_db",
    "skip_if_no_redis",
    "teardown_iam_v2_sessions",
    "verify_feature_flag_env",
    "verify_sqlserver_env",
    "verify_v031_schema",
]
