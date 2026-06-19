"""PA-003: búsqueda server-side en GET /api/v1/modulos-v2/."""
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.infrastructure.database.tables_modulos import ModuloTable
from app.modules.modulos.application.services.modulo_service import ModuloService
from app.modules.modulos.presentation import endpoints_modulos


def _modulo_row(**overrides):
    base = {
        "modulo_id": uuid4(),
        "codigo": "LOGISTICA",
        "nombre": "Logística",
        "descripcion": "Módulo logístico",
        "icono": None,
        "color": "#1976D2",
        "categoria": "operaciones",
        "es_core": False,
        "requiere_licencia": True,
        "precio_mensual": None,
        "modulos_requeridos": None,
        "orden": 1,
        "es_activo": True,
        "configuracion_defecto": None,
        "fecha_creacion": datetime(2026, 1, 1),
        "fecha_actualizacion": None,
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_t_u1_buscar_absent_no_kwarg_propagation():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list,
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_count,
    ):
        await endpoints_modulos.listar_modulos(
            skip=0,
            limit=10,
            solo_activos=False,
            categoria=None,
            buscar=None,
            current_user=object(),
        )

    mock_list.assert_awaited_once_with(
        skip=0, limit=10, solo_activos=False, categoria=None
    )
    mock_count.assert_awaited_once_with(solo_activos=False, categoria=None)


@pytest.mark.asyncio
async def test_t_u2_buscar_propagated_to_list_and_count():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list,
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_count,
    ):
        await endpoints_modulos.listar_modulos(
            skip=0,
            limit=10,
            solo_activos=True,
            categoria="core",
            buscar="log",
            current_user=object(),
        )

    mock_list.assert_awaited_once_with(
        skip=0, limit=10, solo_activos=True, categoria="core", buscar="log"
    )
    mock_count.assert_awaited_once_with(
        solo_activos=True, categoria="core", buscar="log"
    )


@pytest.mark.asyncio
async def test_t_u3_pagination_total_matches_filtered_count():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[_modulo_row(), _modulo_row()],
        ),
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=3,
        ),
    ):
        result = await endpoints_modulos.listar_modulos(
            skip=0,
            limit=10,
            solo_activos=False,
            categoria=None,
            buscar="log",
            current_user=object(),
        )

    assert result["pagination"]["total"] == 3
    assert len(result["data"]) == 2


@pytest.mark.asyncio
async def test_t_u4_buscar_with_solo_activos():
    with patch.object(
        ModuloService,
        "obtener_modulos",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_list:
        await endpoints_modulos.listar_modulos(
            skip=0,
            limit=5,
            solo_activos=True,
            categoria=None,
            buscar="inv",
            current_user=object(),
        )

    mock_list.assert_awaited_once_with(
        skip=0, limit=5, solo_activos=True, categoria=None, buscar="inv"
    )


@pytest.mark.asyncio
async def test_t_u5_buscar_with_categoria():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list,
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_count,
    ):
        await endpoints_modulos.listar_modulos(
            skip=0,
            limit=5,
            solo_activos=False,
            categoria="finanzas",
            buscar="erp",
            current_user=object(),
        )

    mock_list.assert_awaited_once_with(
        skip=0,
        limit=5,
        solo_activos=False,
        categoria="finanzas",
        buscar="erp",
    )
    mock_count.assert_awaited_once_with(
        solo_activos=False, categoria="finanzas", buscar="erp"
    )


def test_t_u6_whitespace_buscar_treated_as_no_filter():
    conditions = ModuloService._condiciones_listado_modulos(
        solo_activos=False, categoria=None, buscar="   "
    )
    assert conditions == []


@pytest.mark.asyncio
async def test_t_u7_pagination_metadata_with_buscar():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[_modulo_row()],
        ),
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=15,
        ),
    ):
        result = await endpoints_modulos.listar_modulos(
            skip=10,
            limit=5,
            solo_activos=False,
            categoria=None,
            buscar="mod",
            current_user=object(),
        )

    assert result["pagination"]["total"] == 15
    assert result["pagination"]["current_page"] == 3
    assert result["pagination"]["has_next"] is False
    assert result["pagination"]["has_prev"] is True


@pytest.mark.asyncio
async def test_t_u8_regression_f004_uses_contar_modulos():
    with (
        patch.object(
            ModuloService,
            "obtener_modulos",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch.object(
            ModuloService,
            "contar_modulos",
            new_callable=AsyncMock,
            return_value=100,
        ) as mock_count,
    ):
        result = await endpoints_modulos.listar_modulos(
            skip=10,
            limit=25,
            solo_activos=False,
            categoria=None,
            current_user=object(),
        )

    mock_count.assert_awaited_once_with(solo_activos=False, categoria=None)
    assert result["pagination"]["total"] == 100


def test_t_u9_search_condition_includes_codigo():
    conditions = ModuloService._condiciones_listado_modulos(
        solo_activos=False, categoria=None, buscar="LOG"
    )
    assert len(conditions) == 1
    query = select(ModuloTable).where(*conditions)
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "codigo" in compiled
    assert "lower" in compiled


def test_t_u10_search_condition_includes_descripcion():
    conditions = ModuloService._condiciones_listado_modulos(
        solo_activos=False, categoria=None, buscar="desc"
    )
    query = select(ModuloTable).where(*conditions)
    compiled = str(query.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "descripcion" in compiled


def test_t_u11_like_metacharacters_not_escaped():
    conditions = ModuloService._condiciones_listado_modulos(
        solo_activos=False, categoria=None, buscar="a_b%"
    )
    query = select(ModuloTable).where(*conditions)
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "%a_b%%" in compiled.replace(" ", "")
