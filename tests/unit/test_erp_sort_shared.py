"""Tests infraestructura compartida ordenamiento ERP (P2-001)."""
from __future__ import annotations

import pytest
from sqlalchemy import column, select

from app.core.exceptions import CustomException
from app.shared.pagination.query_helpers import apply_erp_sort, apply_memory_sort
from app.shared.pagination.sort import ErpSortParams, erp_sort_params

_COL_A = column("nombre")
_COL_B = column("codigo")
_COL_ID = column("entity_id")
_ALLOWED = frozenset({"nombre", "codigo"})
_COLUMN_MAP = {"nombre": _COL_A, "codigo": _COL_B}
_DEFAULT_ORDER = [(_COL_A, "asc")]


def test_erp_sort_params_ignores_sort_dir_without_sort_by():
    params = erp_sort_params(sort_by=None, sort_dir="desc")
    assert params.sort_by is None
    assert params.sort_dir is None
    assert params.is_active is False


def test_erp_sort_params_active_with_sort_by():
    params = erp_sort_params(sort_by="nombre", sort_dir="desc")
    assert params.sort_by == "nombre"
    assert params.sort_dir == "desc"
    assert params.is_active is True


def test_apply_erp_sort_default_without_sort_by():
    query = select(_COL_A, _COL_B)
    result = apply_erp_sort(
        query,
        allowed_columns=_ALLOWED,
        column_map=_COLUMN_MAP,
        sort_by=None,
        sort_dir=None,
        default_order=_DEFAULT_ORDER,
        tie_breaker=("entity_id", _COL_ID),
    )
    assert str(result).lower().count("order by") == 1


def test_apply_erp_sort_invalid_sort_by_raises():
    query = select(_COL_A)
    with pytest.raises(CustomException) as exc:
        apply_erp_sort(
            query,
            allowed_columns=_ALLOWED,
            column_map=_COLUMN_MAP,
            sort_by="invalid_col",
            sort_dir="asc",
            default_order=_DEFAULT_ORDER,
        )
    assert exc.value.status_code == 422
    assert "sort_by" in exc.value.detail


def test_apply_erp_sort_valid_sort_by_asc_default():
    query = select(_COL_A)
    result = apply_erp_sort(
        query,
        allowed_columns=_ALLOWED,
        column_map=_COLUMN_MAP,
        sort_by="codigo",
        sort_dir=None,
        default_order=_DEFAULT_ORDER,
        tie_breaker=("entity_id", _COL_ID),
    )
    sql = str(result).lower()
    assert "order by" in sql


def test_apply_memory_sort_default():
    rows = [
        {"modulo_codigo": "INV", "codigo_parametro": "B", "parametro_id": "2"},
        {"modulo_codigo": "INV", "codigo_parametro": "A", "parametro_id": "1"},
    ]
    sorted_rows = apply_memory_sort(
        rows,
        allowed_columns=frozenset({"modulo_codigo", "codigo_parametro"}),
        sort_by=None,
        sort_dir=None,
        default_key=lambda r: (r.get("modulo_codigo"), r.get("codigo_parametro")),
        tie_breaker_key=lambda r: r.get("parametro_id"),
    )
    assert sorted_rows[0]["codigo_parametro"] == "A"


def test_apply_memory_sort_invalid_raises():
    rows = [{"nombre": "x", "parametro_id": "1"}]
    with pytest.raises(CustomException) as exc:
        apply_memory_sort(
            rows,
            allowed_columns=frozenset({"nombre"}),
            sort_by="bad",
            sort_dir="asc",
            default_key=lambda r: r.get("nombre"),
            tie_breaker_key=lambda r: r.get("parametro_id"),
        )
    assert exc.value.status_code == 422


def test_apply_memory_sort_desc():
    rows = [
        {"nombre": "Alpha", "parametro_id": "1"},
        {"nombre": "Beta", "parametro_id": "2"},
    ]
    sorted_rows = apply_memory_sort(
        rows,
        allowed_columns=frozenset({"nombre"}),
        sort_by="nombre",
        sort_dir="desc",
        default_key=lambda r: r.get("nombre"),
        tie_breaker_key=lambda r: r.get("parametro_id"),
    )
    assert sorted_rows[0]["nombre"] == "Beta"
