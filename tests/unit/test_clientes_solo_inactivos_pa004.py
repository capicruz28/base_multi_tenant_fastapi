"""PA-004: filtro solo_inactivos en GET /api/v1/clientes/."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.tenant.application.services.cliente_service import ClienteService
from app.modules.tenant.presentation import endpoints_clientes


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _cliente_row(**overrides):
    base = {
        "cliente_id": uuid4(),
        "codigo_cliente": "CLI001",
        "subdominio": "cli001",
        "razon_social": "Cliente QA",
        "nombre_comercial": "QA",
        "ruc": None,
        "tipo_instalacion": "shared",
        "servidor_api_local": None,
        "modo_autenticacion": "local",
        "logo_url": None,
        "favicon_url": None,
        "color_primario": "#1976D2",
        "color_secundario": "#424242",
        "tema_personalizado": None,
        "plan_suscripcion": "trial",
        "estado_suscripcion": "cancelado",
        "fecha_inicio_suscripcion": None,
        "fecha_fin_trial": None,
        "contacto_nombre": None,
        "contacto_email": None,
        "contacto_telefono": None,
        "es_activo": False,
        "es_demo": False,
        "metadata_json": None,
        "api_key_sincronizacion": None,
        "sincronizacion_habilitada": False,
        "ultima_sincronizacion": None,
        "fecha_creacion": datetime(2026, 1, 1),
        "fecha_actualizacion": None,
        "fecha_ultimo_acceso": None,
    }
    base.update(overrides)
    return base


listar_clientes_handler = _unwrap(endpoints_clientes.listar_clientes)


def _fake_user():
    user = MagicMock()
    user.nombre_usuario = "pytest-superadmin"
    return user


def _vigencia_where_fragment(sql: str) -> str:
    lowered = sql.lower()
    if " where " not in lowered:
        return ""
    fragment = lowered.split(" where ", 1)[1]
    for separator in (" order by ", " offset "):
        if separator in fragment:
            fragment = fragment.split(separator, 1)[0]
    return fragment.strip()


@pytest.mark.asyncio
async def test_t_u1_solo_inactivos_default_pre_pa004_equivalence():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_list:
        await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            solo_inactivos=False,
            buscar=None,
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=10,
        solo_activos=True,
        solo_inactivos=False,
        buscar=None,
    )


@pytest.mark.asyncio
async def test_t_u2_solo_inactivos_propagated_to_service():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_list:
        await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            solo_inactivos=True,
            buscar=None,
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=10,
        solo_activos=True,
        solo_inactivos=True,
        buscar=None,
    )


@pytest.mark.asyncio
async def test_t_u3_total_matches_filtered_count():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 5),
    ):
        result = await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            solo_inactivos=True,
            buscar=None,
            current_user=_fake_user(),
        )

    assert result.total_clientes == 5
    assert len(result.clientes) == 0


@pytest.mark.asyncio
async def test_t_u4_precedence_solo_inactivos_with_default_solo_activos():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_list:
        await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            solo_inactivos=True,
            buscar=None,
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=10,
        solo_activos=True,
        solo_inactivos=True,
        buscar=None,
    )


@pytest.mark.asyncio
async def test_t_u5_solo_activos_false_without_solo_inactivos_all_clients():
    captured_queries = []

    async def fake_execute(query, *args, **kwargs):
        sql = str(query)
        captured_queries.append(sql)
        if "COUNT" in sql.upper():
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.tenant.application.services.cliente_service.execute_query",
        new=fake_execute,
    ):
        await ClienteService.listar_clientes(
            solo_activos=False,
            solo_inactivos=False,
        )

    count_sql = captured_queries[0].lower()
    assert "es_activo" not in count_sql


@pytest.mark.asyncio
async def test_t_u6_solo_activos_false_solo_inactivos_true():
    captured_queries = []

    async def fake_execute(query, *args, **kwargs):
        sql = str(query)
        captured_queries.append(sql)
        if "COUNT" in sql.upper():
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.tenant.application.services.cliente_service.execute_query",
        new=fake_execute,
    ):
        await ClienteService.listar_clientes(
            solo_activos=False,
            solo_inactivos=True,
        )

    count_sql = captured_queries[0]
    assert "es_activo = 0" in count_sql
    assert "es_activo = 1" not in count_sql


@pytest.mark.asyncio
async def test_t_u7_solo_inactivos_with_buscar():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_list:
        await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=False,
            solo_inactivos=True,
            buscar="acme",
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=10,
        solo_activos=False,
        solo_inactivos=True,
        buscar="acme",
    )


@pytest.mark.asyncio
async def test_t_u8_pagination_metadata_with_solo_inactivos():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 12),
    ):
        result = await listar_clientes_handler(
            skip=5,
            limit=5,
            solo_activos=True,
            solo_inactivos=True,
            buscar=None,
            current_user=_fake_user(),
        )

    assert result.total_clientes == 12
    assert result.pagina_actual == 2
    assert result.total_paginas == 3
    assert result.items_por_pagina == 5


@pytest.mark.asyncio
async def test_t_u9_buscar_regression_without_solo_inactivos():
    with patch.object(
        ClienteService,
        "listar_clientes",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_list:
        await listar_clientes_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            solo_inactivos=False,
            buscar="tenant",
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=10,
        solo_activos=True,
        solo_inactivos=False,
        buscar="tenant",
    )


@pytest.mark.asyncio
async def test_t_u10_vigencia_conditions_in_shared_where():
    async def run_case(solo_activos, solo_inactivos):
        captured = []

        async def fake_execute(query, *args, **kwargs):
            captured.append(str(query))
            if "COUNT" in str(query).upper():
                return [{"total": 0}]
            return []

        with patch(
            "app.modules.tenant.application.services.cliente_service.execute_query",
            new=fake_execute,
        ):
            await ClienteService.listar_clientes(
                solo_activos=solo_activos,
                solo_inactivos=solo_inactivos,
            )
        return captured[0].lower(), captured[1].lower()

    c1_count, c1_select = await run_case(True, False)
    assert "es_activo = 1" in c1_count
    assert _vigencia_where_fragment(c1_count) == _vigencia_where_fragment(c1_select)

    c2_count, _ = await run_case(False, False)
    assert "es_activo" not in c2_count

    c3_count, _ = await run_case(True, True)
    assert "es_activo = 0" in c3_count
    assert "es_activo = 1" not in c3_count
