"""Regression: superadmin auditoría endpoints must bind naive UTC datetimes to SQL Server."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.modules.superadmin.application.datetime_sql import (
    normalize_datetime_for_sql_server,
    sql_int_or_zero,
)
from app.modules.superadmin.application.services.superadmin_auditoria_service import (
    SuperadminAuditoriaService,
)


def test_normalize_datetime_for_sql_server_strips_utc_offset():
    aware = datetime(2026, 6, 2, 16, 59, 0, 233000, tzinfo=timezone.utc)
    naive = normalize_datetime_for_sql_server(aware)
    assert naive == datetime(2026, 6, 2, 16, 59, 0, 233000)
    assert naive.tzinfo is None


def test_normalize_datetime_for_sql_server_passthrough_naive():
    naive = datetime(2026, 6, 2, 0, 0, 0)
    assert normalize_datetime_for_sql_server(naive) is naive


def test_normalize_datetime_for_sql_server_none():
    assert normalize_datetime_for_sql_server(None) is None


def test_sql_int_or_zero_coerces_null():
    assert sql_int_or_zero(None) == 0
    assert sql_int_or_zero(5) == 5


@pytest.mark.asyncio
async def test_obtener_estadisticas_passes_naive_datetimes_to_execute_query():
    fecha_desde = datetime(2026, 6, 2, 0, 0, 0, tzinfo=timezone.utc)
    fecha_hasta = datetime(2026, 6, 3, 23, 59, 59, tzinfo=timezone.utc)
    captured_params: list[tuple] = []

    async def fake_execute_query(query, params, client_id=None):
        captured_params.append(params)
        if "GROUP BY evento" in query:
            return []
        if "GROUP BY tipo_sincronizacion" in query:
            return []
        if "GROUP BY ip_address" in query:
            return []
        if "GROUP BY u.usuario_id" in query:
            return []
        return []

    with patch(
        "app.modules.superadmin.application.services.superadmin_auditoria_service.execute_query",
        new=fake_execute_query,
    ):
        result = await SuperadminAuditoriaService.obtener_estadisticas(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    assert result["autenticacion"]["total_eventos"] == 0
    assert captured_params, "expected execute_query calls"
    for params in captured_params:
        for param in params:
            if isinstance(param, datetime):
                assert param.tzinfo is None, f"expected naive datetime, got {param!r}"


@pytest.mark.asyncio
async def test_obtener_estadisticas_null_aggregates_coerced_to_zero():
    auth_row = {
        "total_eventos": 0,
        "login_exitosos": None,
        "login_fallidos": None,
        "evento": None,
        "eventos_por_tipo": None,
    }

    async def fake_execute_query(query, params, client_id=None):
        if "GROUP BY evento" in query:
            return [auth_row]
        return []

    with patch(
        "app.modules.superadmin.application.services.superadmin_auditoria_service.execute_query",
        new=fake_execute_query,
    ):
        result = await SuperadminAuditoriaService.obtener_estadisticas()

    assert result["autenticacion"]["login_exitosos"] == 0
    assert result["autenticacion"]["login_fallidos"] == 0


@pytest.mark.asyncio
async def test_get_logs_autenticacion_passes_naive_datetimes():
    fecha_desde = datetime(2026, 6, 2, 0, 0, 0, tzinfo=timezone.utc)
    fecha_hasta = datetime(2026, 6, 3, 0, 0, 0, tzinfo=timezone.utc)
    captured: list[tuple] = []

    async def fake_execute_query(query, params, client_id=None):
        captured.append(params)
        if "COUNT(*)" in query:
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.superadmin.application.services.superadmin_auditoria_service.execute_query",
        new=fake_execute_query,
    ):
        await SuperadminAuditoriaService.get_logs_autenticacion(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=1,
            limit=10,
        )

    assert captured
    date_params = [p for params in captured for p in params if isinstance(p, datetime)]
    assert len(date_params) == 4  # count + data queries, each with 2 dates
    assert all(p.tzinfo is None for p in date_params)


@pytest.mark.asyncio
async def test_get_logs_sincronizacion_passes_naive_datetimes():
    fecha_desde = datetime(2026, 6, 2, 0, 0, 0, tzinfo=timezone.utc)
    fecha_hasta = datetime(2026, 6, 3, 0, 0, 0, tzinfo=timezone.utc)
    captured: list[tuple] = []

    async def fake_execute_query(query, params, client_id=None):
        captured.append(params)
        if "COUNT(*)" in query:
            return [{"total": 0}]
        return []

    with patch(
        "app.modules.superadmin.application.services.superadmin_auditoria_service.execute_query",
        new=fake_execute_query,
    ):
        await SuperadminAuditoriaService.get_logs_sincronizacion(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=1,
            limit=10,
        )

    assert captured
    date_params = [p for params in captured for p in params if isinstance(p, datetime)]
    assert len(date_params) == 4
    assert all(p.tzinfo is None for p in date_params)
