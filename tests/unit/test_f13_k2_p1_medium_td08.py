"""F13-K2-P1 — TD-08 remediación MEDIUM (queries con :cliente_id nombrado)."""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import SecurityError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.query_helpers import (
    _has_tenant_filter,
    apply_tenant_filter_to_text_clause,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

DEDICATED_ID = HYBRID_FIXTURE_TENANT_DEDICATED
SHARED_ID = HYBRID_FIXTURE_TENANT_SHARED


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


@pytest.fixture
def shared_tenant_context():
    ctx = build_tenant_context(
        SHARED_ID,
        build_shared_metadata(SHARED_ID),
        subdominio="shared-mock",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


def _bind_query(sql: str, *, cliente_id=DEDICATED_ID):
    base = {
        "usuario_id": uuid4(),
        "cliente_id": cliente_id,
        "rol_id": uuid4(),
        "menu_id": uuid4(),
        "nombre_usuario": "user@test.com",
        "correo": "user@test.com",
    }
    return text(sql).bindparams(
        **{k: v for k, v in base.items() if f":{k}" in sql}
    )


MEDIUM_CASES = [
    (
        "usuario shared lookup",
        """
        SELECT usuario_id FROM dbo.usuario
        WHERE usuario_id = :usuario_id AND cliente_id = :cliente_id AND es_eliminado = 0
        """,
        "usuario",
    ),
    (
        "usuario_rol assignment check",
        """
        SELECT usuario_rol_id FROM dbo.usuario_rol
        WHERE usuario_id = :usuario_id AND rol_id = :rol_id AND cliente_id = :cliente_id
        """,
        "usuario_rol",
    ),
    (
        "rol_menu_permiso check",
        """
        SELECT permiso_id FROM rol_menu_permiso
        WHERE cliente_id = :cliente_id AND rol_id = :rol_id AND menu_id = :menu_id
        """,
        "rol_menu_permiso",
    ),
    (
        "superadmin roles enrichment",
        """
        SELECT r.rol_id FROM dbo.rol r
        INNER JOIN dbo.usuario_rol ur ON r.rol_id = ur.rol_id
        WHERE ur.usuario_id = :usuario_id AND ur.cliente_id = :cliente_id
        """,
        "usuario_rol",
    ),
    (
        "tenant federacion_identidad",
        """
        SELECT federacion_id FROM federacion_identidad
        WHERE cliente_id = :cliente_id AND es_activo = 1
        """,
        "federacion_identidad",
    ),
    (
        "tenant cliente_modulo activo",
        """
        SELECT cma.modulo_id FROM cliente_modulo_activo cma
        WHERE cma.cliente_id = :cliente_id AND cma.esta_activo = 1
        """,
        "cliente_modulo_activo",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize("label,sql,table", MEDIUM_CASES)
def test_p1_medium_has_tenant_filter(label, sql, table):
    assert _has_tenant_filter(sql, "cliente_id", DEDICATED_ID) is True


@pytest.mark.unit
@pytest.mark.parametrize("label,sql,table", MEDIUM_CASES)
def test_p1_medium_dedicated_no_security_error(dedicated_tenant_context, label, sql, table):
    clause = _bind_query(sql)
    try:
        result = apply_tenant_filter_to_text_clause(clause, table_name=table)
    except SecurityError as exc:
        pytest.fail(f"P1 query '{label}' raised SecurityError on Dedicated: {exc.detail}")
    assert result is not None


@pytest.mark.unit
@pytest.mark.parametrize("label,sql,table", MEDIUM_CASES)
def test_p1_medium_shared_no_security_error(shared_tenant_context, label, sql, table):
    clause = _bind_query(sql, cliente_id=SHARED_ID)
    try:
        result = apply_tenant_filter_to_text_clause(clause, table_name=table)
    except SecurityError as exc:
        pytest.fail(f"P1 query '{label}' raised SecurityError on Shared: {exc.detail}")
    assert result is not None
