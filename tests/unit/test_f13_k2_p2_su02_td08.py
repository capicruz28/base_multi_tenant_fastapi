"""F13-K2-P2 — TD-08 S-U-02 count/list superadmin usuarios (named bindparams)."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import SecurityError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.query_helpers import (
    _has_tenant_filter,
    apply_tenant_filter_to_text_clause,
)
from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

SERVICE = "app.modules.superadmin.application.services.superadmin_usuario_service"
EXECUTE_QUERY = f"{SERVICE}.execute_query"
RESOLVE_KWARGS = f"{SERVICE}.resolve_platform_tenant_data_execute_kwargs"
RESOLVE_DB_TYPE = f"{SERVICE}.resolve_platform_tenant_data_database_type"
SYSTEM_CLIENT_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def dedicated_tenant_context():
    ctx = build_tenant_context(
        HYBRID_FIXTURE_TENANT_DEDICATED,
        build_dedicated_metadata(HYBRID_FIXTURE_TENANT_DEDICATED),
        subdominio="dedicated-mock",
        codigo_cliente="DEDICATED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def shared_tenant_context():
    ctx = build_tenant_context(
        HYBRID_FIXTURE_TENANT_SHARED,
        build_shared_metadata(HYBRID_FIXTURE_TENANT_SHARED),
        subdominio="shared-mock",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


def _build_count_clause(cliente_id: UUID) -> text:
    where_clause, params, _, _ = SuperadminUsuarioService._build_usuarios_globales_where(
        cliente_id=cliente_id,
        database_type="single",
    )
    named_where, bind_params = SuperadminUsuarioService._usuarios_globales_where_to_named(
        where_clause,
        params,
    )
    sql = f"""
    SELECT COUNT(*) as total
    FROM dbo.usuario u
    WHERE {named_where}
    """
    return text(sql).bindparams(**bind_params)


def _build_select_clause(cliente_id: UUID, *, offset: int = 0, limit: int = 50) -> text:
    where_clause, params, order_field, order_dir = (
        SuperadminUsuarioService._build_usuarios_globales_where(
            cliente_id=cliente_id,
            database_type="single",
        )
    )
    named_where, bind_params = SuperadminUsuarioService._usuarios_globales_where_to_named(
        where_clause,
        params,
    )
    bind_params["offset"] = offset
    bind_params["limit"] = limit
    sql = f"""
    SELECT u.usuario_id
    FROM dbo.usuario u
    WHERE {named_where}
    ORDER BY {order_field} {order_dir}
    OFFSET :offset ROWS
    FETCH NEXT :limit ROWS ONLY
    """
    return text(sql).bindparams(**bind_params)


@pytest.mark.unit
def test_su02_count_has_tenant_filter_named_cliente_id():
    clause = _build_count_clause(SYSTEM_CLIENT_ID)
    assert _has_tenant_filter(clause.text, "cliente_id", SYSTEM_CLIENT_ID)


@pytest.mark.unit
def test_su02_select_has_tenant_filter_named_cliente_id():
    clause = _build_select_clause(SYSTEM_CLIENT_ID)
    assert _has_tenant_filter(clause.text, "cliente_id", SYSTEM_CLIENT_ID)


@pytest.mark.unit
def test_su02_count_apply_tenant_filter_shared_no_warning(shared_tenant_context, caplog):
    import logging

    clause = _build_count_clause(HYBRID_FIXTURE_TENANT_SHARED)
    with caplog.at_level(logging.WARNING):
        result = apply_tenant_filter_to_text_clause(
            clause,
            client_id=HYBRID_FIXTURE_TENANT_SHARED,
            table_name="usuario",
        )
    assert result is clause
    assert not any("[TENANT_FILTER]" in r.message for r in caplog.records)


@pytest.mark.unit
def test_su02_count_apply_tenant_filter_dedicated_no_security_error(dedicated_tenant_context):
    clause = _build_count_clause(HYBRID_FIXTURE_TENANT_DEDICATED)
    result = apply_tenant_filter_to_text_clause(
        clause,
        client_id=HYBRID_FIXTURE_TENANT_DEDICATED,
        table_name="usuario",
    )
    assert result is clause


@pytest.mark.unit
def test_su02_select_apply_tenant_filter_dedicated_no_security_error(dedicated_tenant_context):
    clause = _build_select_clause(HYBRID_FIXTURE_TENANT_DEDICATED)
    result = apply_tenant_filter_to_text_clause(
        clause,
        client_id=HYBRID_FIXTURE_TENANT_DEDICATED,
        table_name="usuario",
    )
    assert result is clause


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_uses_named_bindparams_not_qmark():
    captured: list = []

    async def _execute_query(query, **kwargs):
        captured.append(query)
        return [{"total": 3}]

    mock_cliente = type(
        "C",
        (),
        {
            "cliente_id": SYSTEM_CLIENT_ID,
            "razon_social": "System",
            "subdominio": "platform",
            "codigo_cliente": "SYSTEM",
            "nombre_comercial": None,
        },
    )()

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=mock_cliente),
    ), patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="single")), patch(
        RESOLVE_KWARGS,
        new=AsyncMock(return_value={"connection_type": "default", "client_id": SYSTEM_CLIENT_ID}),
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        total = await SuperadminUsuarioService.count_usuarios_globales(cliente_id=SYSTEM_CLIENT_ID)

    assert total == 3
    assert len(captured) == 1
    sql = captured[0].text
    assert ":cliente_id" in sql
    assert ":p0" not in sql
    assert "?" not in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_list_uses_named_offset_limit():
    captured: list = []

    async def _execute_query(query, **kwargs):
        captured.append(str(query.text if hasattr(query, "text") else query))
        if "COUNT(*)" in captured[-1]:
            return [{"total": 1}]
        return [
            {
                "usuario_id": uuid4(),
                "cliente_id": SYSTEM_CLIENT_ID,
                "nombre_usuario": "superadmin",
                "correo": "a@b.com",
                "nombre": "A",
                "apellido": "B",
                "dni": None,
                "telefono": None,
                "es_activo": 1,
                "es_eliminado": 0,
                "proveedor_autenticacion": "local",
                "referencia_externa_id": None,
                "referencia_externa_email": None,
                "correo_confirmado": 1,
                "intentos_fallidos": 0,
                "fecha_bloqueo": None,
                "ultimo_ip": None,
                "fecha_creacion": datetime(2026, 1, 1),
                "fecha_ultimo_acceso": None,
                "fecha_actualizacion": None,
                "sincronizado_desde": None,
                "fecha_ultima_sincronizacion": None,
            }
        ]

    mock_cliente = type(
        "C",
        (),
        {
            "cliente_id": SYSTEM_CLIENT_ID,
            "razon_social": "System",
            "subdominio": "platform",
            "codigo_cliente": "SYSTEM",
            "nombre_comercial": None,
        },
    )()

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=mock_cliente),
    ), patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="single")), patch(
        RESOLVE_KWARGS,
        new=AsyncMock(return_value={"connection_type": "default", "client_id": SYSTEM_CLIENT_ID}),
    ), patch(
        f"{SERVICE}.SuperadminUsuarioService._obtener_roles_usuario",
        new=AsyncMock(return_value=[]),
    ), patch(
        f"{SERVICE}.UsuarioService.get_user_level_info",
        new=AsyncMock(
            return_value={"access_level": 5, "is_super_admin": True, "user_type": "super_admin"}
        ),
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        await SuperadminUsuarioService.get_usuarios_globales(
            cliente_id=SYSTEM_CLIENT_ID,
            page=1,
            limit=50,
        )

    select_sql = next(sql for sql in captured if "OFFSET" in sql)
    assert ":offset" in select_sql
    assert ":limit" in select_sql
    assert ":cliente_id" in select_sql
    assert ":p0" not in select_sql
