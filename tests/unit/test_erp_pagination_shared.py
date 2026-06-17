"""Tests infraestructura compartida paginación ERP."""
import pytest

from app.shared.pagination.builder import build_paginated_response, calc_total_paginas
from app.shared.pagination.params import DEFAULT_LIMIT, MAX_LIMIT, ErpPaginationParams
from app.shared.pagination.response_mode import is_paginated_mode


def test_calc_total_paginas_zero():
    assert calc_total_paginas(0, 50) == 0


def test_calc_total_paginas_exact():
    assert calc_total_paginas(100, 50) == 2


def test_calc_total_paginas_partial():
    assert calc_total_paginas(101, 50) == 3


def test_is_paginated_mode():
    assert is_paginated_mode(None) is False
    assert is_paginated_mode(1) is True


def test_erp_pagination_params_legacy():
    p = ErpPaginationParams(page=None, limit=DEFAULT_LIMIT)
    assert p.is_paginated is False
    assert p.offset == 0


def test_erp_pagination_params_page2_limit10():
    p = ErpPaginationParams(page=2, limit=10)
    assert p.is_paginated is True
    assert p.offset == 10


def test_build_paginated_response():
    p = ErpPaginationParams(page=1, limit=50)
    resp = build_paginated_response(items=["a", "b"], total=120, pagination=p)
    assert resp.items == ["a", "b"]
    assert resp.total == 120
    assert resp.pagina_actual == 1
    assert resp.total_paginas == 3
    assert resp.limit == 50


def test_constants():
    assert DEFAULT_LIMIT == 50
    assert MAX_LIMIT == 100
