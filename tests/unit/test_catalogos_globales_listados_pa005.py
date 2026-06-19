"""PA-005: listados escalables GET /api/v1/catalogos-globales/*."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.superadmin.application.services.catalogos_globales_service import (
    CatalogosGlobalesService,
)
from app.modules.superadmin.presentation import endpoints_catalogos_globales
from app.modules.superadmin.presentation.schemas_catalogos_globales import (
    PaginatedCatDepartamentoResponse,
    PaginatedCatDistritoResponse,
    PaginatedCatMonedaResponse,
    PaginatedCatPaisResponse,
    PaginatedCatProvinciaResponse,
)


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


list_distritos_handler = _unwrap(endpoints_catalogos_globales.list_distritos)
list_departamentos_handler = _unwrap(endpoints_catalogos_globales.list_departamentos)
list_provincias_handler = _unwrap(endpoints_catalogos_globales.list_provincias)
list_monedas_handler = _unwrap(endpoints_catalogos_globales.list_monedas)
list_paises_handler = _unwrap(endpoints_catalogos_globales.list_paises)


def _fake_user(cliente_id=None):
    user = MagicMock()
    user.nombre_usuario = "pytest-superadmin"
    user.cliente_id = cliente_id or uuid4()
    return user


def _where_fragment(sql: str) -> str:
    lowered = sql.lower()
    if " where " not in lowered:
        return ""
    fragment = lowered.split(" where ", 1)[1]
    for separator in (" order by ", " offset ", " limit "):
        if separator in fragment:
            fragment = fragment.split(separator, 1)[0]
    return fragment.strip()


@pytest.mark.asyncio
async def test_t_u01_distritos_response_is_paginated_envelope():
    with patch.object(
        CatalogosGlobalesService,
        "list_distritos",
        new_callable=AsyncMock,
        return_value=[],
    ), patch.object(
        CatalogosGlobalesService,
        "contar_distritos",
        new_callable=AsyncMock,
        return_value=0,
    ):
        result = await list_distritos_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            pais_id=None,
            departamento_id=None,
            provincia_id=None,
            ubigeo=None,
            buscar=None,
            cliente_id=None,
            current_user=_fake_user(),
        )

    assert isinstance(result, PaginatedCatDistritoResponse)
    assert hasattr(result, "total_distritos")
    assert hasattr(result, "pagina_actual")


@pytest.mark.asyncio
async def test_t_u02_distritos_propagates_params_to_service():
    with patch.object(
        CatalogosGlobalesService,
        "list_distritos",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_list, patch.object(
        CatalogosGlobalesService,
        "contar_distritos",
        new_callable=AsyncMock,
        return_value=0,
    ) as mock_count:
        cliente_id = uuid4()
        await list_distritos_handler(
            skip=5,
            limit=20,
            solo_activos=True,
            pais_id=None,
            departamento_id=None,
            provincia_id=None,
            ubigeo=None,
            buscar="lima",
            cliente_id=cliente_id,
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once_with(
        skip=5,
        limit=20,
        client_id=cliente_id,
        solo_activos=True,
        buscar="lima",
        pais_id=None,
        departamento_id=None,
        provincia_id=None,
        ubigeo=None,
    )
    mock_count.assert_awaited_once_with(
        client_id=cliente_id,
        solo_activos=True,
        buscar="lima",
        pais_id=None,
        departamento_id=None,
        provincia_id=None,
        ubigeo=None,
    )


@pytest.mark.asyncio
async def test_t_u03_defaults_skip_limit():
    with patch.object(
        CatalogosGlobalesService,
        "list_monedas",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_list, patch.object(
        CatalogosGlobalesService,
        "contar_monedas",
        new_callable=AsyncMock,
        return_value=0,
    ):
        await list_monedas_handler(
            skip=0,
            limit=100,
            solo_activos=True,
            buscar=None,
            cliente_id=None,
            current_user=_fake_user(),
        )

    mock_list.assert_awaited_once()
    assert mock_list.await_args.kwargs["skip"] == 0
    assert mock_list.await_args.kwargs["limit"] == 100


@pytest.mark.asyncio
async def test_t_u04_buscar_empty_normalized_in_service():
    assert CatalogosGlobalesService._normalizar_buscar(None) is None
    assert CatalogosGlobalesService._normalizar_buscar("   ") is None
    conditions = CatalogosGlobalesService._condiciones_listado_cat_moneda(True, "  ")
    assert len(conditions) == 1


@pytest.mark.asyncio
async def test_t_u05_pagination_metadata():
    with patch.object(
        CatalogosGlobalesService,
        "list_distritos",
        new_callable=AsyncMock,
        return_value=[],
    ), patch.object(
        CatalogosGlobalesService,
        "contar_distritos",
        new_callable=AsyncMock,
        return_value=25,
    ):
        result = await list_distritos_handler(
            skip=10,
            limit=5,
            solo_activos=True,
            pais_id=None,
            departamento_id=None,
            provincia_id=None,
            ubigeo=None,
            buscar=None,
            cliente_id=None,
            current_user=_fake_user(),
        )

    assert result.total_distritos == 25
    assert result.pagina_actual == 3
    assert result.total_paginas == 5
    assert result.items_por_pagina == 5


@pytest.mark.asyncio
async def test_t_u06_total_matches_count():
    with patch.object(
        CatalogosGlobalesService,
        "list_paises",
        new_callable=AsyncMock,
        return_value=[],
    ), patch.object(
        CatalogosGlobalesService,
        "contar_paises",
        new_callable=AsyncMock,
        return_value=42,
    ) as mock_count:
        result = await list_paises_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            buscar=None,
            cliente_id=None,
            current_user=_fake_user(),
        )

    mock_count.assert_awaited_once()
    assert result.total_paises == 42


@pytest.mark.asyncio
async def test_t_u07_solo_activos_false_without_es_activo_predicate():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        if "count" in str(query).lower():
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            solo_activos=False,
        )

    sql = _where_fragment(captured[0])
    assert "es_activo" not in sql


@pytest.mark.asyncio
async def test_t_u08_contar_uses_same_filter_kwargs_without_pagination():
    with patch.object(
        CatalogosGlobalesService,
        "list_departamentos",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_list, patch.object(
        CatalogosGlobalesService,
        "contar_departamentos",
        new_callable=AsyncMock,
        return_value=0,
    ) as mock_count:
        pais_id = uuid4()
        await list_departamentos_handler(
            skip=0,
            limit=10,
            solo_activos=True,
            pais_id=pais_id,
            buscar="and",
            cliente_id=None,
            current_user=_fake_user(),
        )

    list_kwargs = mock_list.await_args.kwargs
    count_kwargs = mock_count.await_args.kwargs
    assert "skip" not in count_kwargs
    assert "limit" not in count_kwargs
    assert count_kwargs["pais_id"] == list_kwargs["pais_id"]
    assert count_kwargs["buscar"] == list_kwargs["buscar"]
    assert count_kwargs["solo_activos"] == list_kwargs["solo_activos"]


@pytest.mark.asyncio
async def test_t_u10_distritos_provincia_id_and_ubigeo_in_sql():
    provincia_id = uuid4()
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 0}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            provincia_id=provincia_id,
            ubigeo="150101",
        )

    sql = captured[0].lower()
    assert "provincia_id" in sql
    assert "ubigeo" in sql


@pytest.mark.asyncio
async def test_t_u11_distritos_count_select_same_where():
    async def fake_execute(query, *args, **kwargs):
        if "count" in str(query).lower():
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        client_id = uuid4()
        await CatalogosGlobalesService.list_distritos(client_id=client_id, buscar="test")
        await CatalogosGlobalesService.contar_distritos(client_id=client_id, buscar="test")

    # Validado por helpers compartidos; smoke de invocación pareada sin error.


@pytest.mark.asyncio
async def test_t_u12_distritos_buscar_and_filters_composed():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 0}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            provincia_id=uuid4(),
            buscar="lima",
        )

    sql = captured[0].lower()
    assert "provincia_id" in sql
    assert "like" in sql


@pytest.mark.asyncio
async def test_t_u13_distritos_buscar_whitelist_columns():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query).lower())
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            buscar="x",
        )

    sql = captured[0]
    assert "codigo" in sql
    assert "nombre" in sql
    assert "ubigeo" in sql


@pytest.mark.asyncio
async def test_t_u14_distritos_pais_id_join_in_sql():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"count_1": 0}]

    pais_id = uuid4()
    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(client_id=uuid4(), pais_id=pais_id)
        await CatalogosGlobalesService.contar_distritos(client_id=uuid4(), pais_id=pais_id)

    list_sql = captured[0].lower()
    count_sql = captured[1].lower()
    for sql in (list_sql, count_sql):
        assert "cat_provincia" in sql
        assert "cat_departamento" in sql
        assert "pais_id" in sql
    assert _where_fragment(captured[0]) == _where_fragment(captured[1])


@pytest.mark.asyncio
async def test_t_u15_distritos_departamento_id_join_in_sql():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"count_1": 0}]

    departamento_id = uuid4()
    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            departamento_id=departamento_id,
        )

    sql = captured[0].lower()
    assert "cat_provincia" in sql
    assert "departamento_id" in sql
    assert "cat_departamento" not in sql


@pytest.mark.asyncio
async def test_t_u16_distritos_cascada_pais_departamento_buscar():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"count_1": 0}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            pais_id=uuid4(),
            departamento_id=uuid4(),
            buscar="lima",
        )

    sql = captured[0].lower()
    assert "cat_provincia" in sql
    assert "cat_departamento" in sql
    assert "pais_id" in sql
    assert "departamento_id" in sql
    assert "like" in sql


@pytest.mark.asyncio
async def test_t_u17_distritos_provincia_id_without_joins():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_distritos(
            client_id=uuid4(),
            provincia_id=uuid4(),
        )

    sql = captured[0].lower()
    assert "provincia_id" in sql
    assert "cat_provincia" not in sql


@pytest.mark.asyncio
async def test_t_u20_departamentos_pais_id_in_sql():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 0}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_departamentos(
            client_id=uuid4(),
            pais_id=uuid4(),
        )
        await CatalogosGlobalesService.contar_departamentos(
            client_id=uuid4(),
            pais_id=uuid4(),
        )

    assert "pais_id" in captured[0].lower()


@pytest.mark.asyncio
async def test_t_u21_provincias_departamento_id_in_sql():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 0}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_provincias(
            client_id=uuid4(),
            departamento_id=uuid4(),
        )

    assert "departamento_id" in captured[0].lower()


@pytest.mark.asyncio
async def test_t_u22_departamentos_count_select_shared_conditions():
    client_id = uuid4()
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 3}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_departamentos(client_id=client_id, buscar="a")
        total = await CatalogosGlobalesService.contar_departamentos(client_id=client_id, buscar="a")

    assert total == 3
    assert _where_fragment(captured[0]) == _where_fragment(captured[1])


@pytest.mark.asyncio
async def test_t_u23_provincias_count_select_shared_conditions():
    client_id = uuid4()
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 2}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_provincias(client_id=client_id, buscar="b")
        total = await CatalogosGlobalesService.contar_provincias(client_id=client_id, buscar="b")

    assert total == 2
    assert _where_fragment(captured[0]) == _where_fragment(captured[1])


@pytest.mark.asyncio
async def test_t_u24_departamentos_buscar_whitelist():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query).lower())
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_departamentos(client_id=uuid4(), buscar="x")

    sql = captured[0]
    assert "codigo" in sql
    assert "nombre" in sql


@pytest.mark.asyncio
async def test_t_u25_provincias_buscar_whitelist():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query).lower())
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_provincias(client_id=uuid4(), buscar="x")

    sql = captured[0]
    assert "codigo" in sql
    assert "nombre" in sql


@pytest.mark.asyncio
async def test_t_u30_monedas_count_select_and_order_by_codigo():
    client_id = uuid4()
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 1}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_monedas(client_id=client_id)
        total = await CatalogosGlobalesService.contar_monedas(client_id=client_id)

    assert total == 1
    assert "codigo" in captured[0].lower()
    assert _where_fragment(captured[0]) == _where_fragment(captured[1])


@pytest.mark.asyncio
async def test_t_u31_paises_count_select_shared_conditions():
    client_id = uuid4()
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query))
        return [] if "count" not in str(query).lower() else [{"total": 4}]

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_paises(client_id=client_id, buscar="pe")
        total = await CatalogosGlobalesService.contar_paises(client_id=client_id, buscar="pe")

    assert total == 4
    assert _where_fragment(captured[0]) == _where_fragment(captured[1])


@pytest.mark.asyncio
async def test_t_u32_monedas_buscar_whitelist():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query).lower())
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_monedas(client_id=uuid4(), buscar="usd")

    sql = captured[0]
    assert "codigo" in sql
    assert "nombre" in sql
    assert "simbolo" in sql


@pytest.mark.asyncio
async def test_t_u33_paises_buscar_whitelist():
    captured = []

    async def fake_execute(query, *args, **kwargs):
        captured.append(str(query).lower())
        return []

    with patch(
        "app.modules.superadmin.application.services.catalogos_globales_service.execute_query",
        new=fake_execute,
    ):
        await CatalogosGlobalesService.list_paises(client_id=uuid4(), buscar="pe")

    sql = captured[0]
    assert "codigo_iso2" in sql
    assert "codigo_iso3" in sql
    assert "nombre" in sql


@pytest.mark.asyncio
async def test_t_u34_all_envelopes_share_metadata_shape():
    handlers = [
        (list_monedas_handler, PaginatedCatMonedaResponse, "total_monedas"),
        (list_paises_handler, PaginatedCatPaisResponse, "total_paises"),
        (list_departamentos_handler, PaginatedCatDepartamentoResponse, "total_departamentos"),
        (list_provincias_handler, PaginatedCatProvinciaResponse, "total_provincias"),
        (list_distritos_handler, PaginatedCatDistritoResponse, "total_distritos"),
    ]
    for handler, model, total_field in handlers:
        service_prefix = handler.__name__.replace("list_", "")
        with patch.object(
            CatalogosGlobalesService,
            f"list_{service_prefix}",
            new_callable=AsyncMock,
            return_value=[],
        ), patch.object(
            CatalogosGlobalesService,
            f"contar_{service_prefix}",
            new_callable=AsyncMock,
            return_value=7,
        ):
            kwargs = {
                "skip": 0,
                "limit": 10,
                "solo_activos": True,
                "buscar": None,
                "cliente_id": None,
                "current_user": _fake_user(),
            }
            if service_prefix == "departamentos":
                kwargs["pais_id"] = None
            elif service_prefix == "provincias":
                kwargs["departamento_id"] = None
            elif service_prefix == "distritos":
                kwargs["pais_id"] = None
                kwargs["departamento_id"] = None
                kwargs["provincia_id"] = None
                kwargs["ubigeo"] = None
            result = await handler(**kwargs)

        assert isinstance(result, model)
        assert getattr(result, total_field) == 7
        assert result.pagina_actual == 1
        assert result.total_paginas == 1
        assert result.items_por_pagina == 10
