"""F13-K2-P0 — TD-08 remediación CRITICAL (queries con :cliente_id nombrado)."""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import SecurityError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.query_helpers import (
    _has_tenant_filter,
    apply_tenant_filter_to_text_clause,
)
from app.infrastructure.database.queries.auth.auth_queries import IS_USER_SUPER_ADMIN
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    build_dedicated_metadata,
    build_tenant_context,
)

DEDICATED_ID = HYBRID_FIXTURE_TENANT_DEDICATED


@pytest.fixture
def dedicated_tenant_context():
    ctx = build_tenant_context(
        DEDICATED_ID,
        build_dedicated_metadata(DEDICATED_ID),
        subdominio="dedicated-mock",
        codigo_cliente="DEDICATED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


def _bind_p0_query(sql: str):
    base = {
        "usuario_id": uuid4(),
        "cliente_id": DEDICATED_ID,
        "usuario_rol_id": uuid4(),
        "permiso_id": uuid4(),
    }
    return text(sql).bindparams(
        **{k: v for k, v in base.items() if f":{k}" in sql}
    )


P0_CASES = [
    (
        "usuario dedicated",
        """
        SELECT u.usuario_id FROM dbo.usuario u
        WHERE u.usuario_id = :usuario_id
          AND (u.cliente_id = :cliente_id OR u.cliente_id IS NULL)
          AND u.es_eliminado = 0
        """,
        "usuario",
    ),
    (
        "usuario_rol by pk",
        """
        SELECT usuario_rol_id FROM dbo.usuario_rol
        WHERE usuario_rol_id = :usuario_rol_id AND cliente_id = :cliente_id
        """,
        "usuario_rol",
    ),
    (
        "rol_menu_permiso by id",
        """
        SELECT permiso_id FROM rol_menu_permiso
        WHERE permiso_id = :permiso_id AND cliente_id = :cliente_id
        """,
        "rol_menu_permiso",
    ),
    (
        "auth_audit_log actividad",
        """
        SELECT log_id FROM dbo.auth_audit_log a
        WHERE a.usuario_id = :usuario_id AND a.cliente_id = :cliente_id
        """,
        "auth_audit_log",
    ),
    (
        "is_super_admin",
        IS_USER_SUPER_ADMIN,
        "usuario_rol",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize("label,sql,table", P0_CASES)
def test_p0_sql_has_tenant_filter_detected(label, sql, table):
    assert _has_tenant_filter(sql, "cliente_id", DEDICATED_ID) is True


@pytest.mark.unit
@pytest.mark.parametrize("label,sql,table", P0_CASES)
def test_p0_dedicated_apply_filter_no_security_error(dedicated_tenant_context, label, sql, table):
    clause = _bind_p0_query(sql)
    try:
        result = apply_tenant_filter_to_text_clause(clause, table_name=table)
    except SecurityError as exc:
        pytest.fail(f"P0 query '{label}' raised SecurityError on Dedicated: {exc.detail}")
    assert result is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_usuario_rol_by_id_uses_named_cliente_id():
    from unittest.mock import AsyncMock, patch

    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    ur_id = uuid4()
    captured: dict = {}

    async def _capture(query, **kwargs):
        captured["sql"] = query.text if hasattr(query, "text") else str(query)
        captured["client_id"] = kwargs.get("client_id")
        return [{"usuario_rol_id": ur_id}]

    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=_capture),
    ):
        row = await UsuarioService._fetch_usuario_rol_by_id(cliente_id, ur_id)

    assert row is not None
    assert "cliente_id = :cliente_id" in captured["sql"]
    assert captured["client_id"] == cliente_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_super_admin_passes_cliente_id_to_execute_query():
    from unittest.mock import AsyncMock, patch

    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()
    captured: dict = {}

    async def _capture(query, **kwargs):
        captured["sql"] = query.text if hasattr(query, "text") else str(query)
        captured["client_id"] = kwargs.get("client_id")
        return [{"is_super_admin": 0}]

    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(side_effect=_capture),
    ):
        result = await UsuarioService.is_super_admin(usuario_id, cliente_id)

    assert result is False
    assert "ur.cliente_id = :cliente_id" in captured["sql"]
    assert captured["client_id"] == cliente_id
