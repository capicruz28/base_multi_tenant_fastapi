"""
Etapa C2 ORG: precedencia parámetros híbridos.
"""
from __future__ import annotations

from uuid import uuid4

from app.infrastructure.database.queries.org.parametro_queries import (
    apply_parametro_precedence,
)

EMPRESA_A = uuid4()
EMPRESA_B = uuid4()


def _row(modulo: str, codigo: str, empresa_id=None, nombre: str = "x"):
    return {
        "modulo_codigo": modulo,
        "codigo_parametro": codigo,
        "empresa_id": empresa_id,
        "nombre_parametro": nombre,
    }


def test_precedence_override_wins_over_global():
    rows = [
        _row("INV", "STOCK_MIN", None, "global"),
        _row("INV", "STOCK_MIN", EMPRESA_A, "override A"),
        _row("INV", "OTRO", None, "solo global"),
    ]
    merged, overrides, pure_global = apply_parametro_precedence(rows, EMPRESA_A)
    assert len(merged) == 2
    by_code = {r["codigo_parametro"]: r for r in merged}
    assert by_code["STOCK_MIN"]["nombre_parametro"] == "override A"
    assert by_code["OTRO"]["nombre_parametro"] == "solo global"
    assert overrides == 1
    assert pure_global == 1


def test_user_can_manage_global_tenant_admin():
    from unittest.mock import MagicMock

    from app.modules.org.presentation.org_deps import user_can_manage_global_parametros

    user = MagicMock(user_type="tenant_admin", access_level=2, is_super_admin=False)
    assert user_can_manage_global_parametros(user, {}) is True


def test_user_can_manage_global_erp_user_denied():
    from unittest.mock import MagicMock

    from app.modules.org.presentation.org_deps import user_can_manage_global_parametros

    user = MagicMock(user_type="user", access_level=2, is_super_admin=False)
    assert user_can_manage_global_parametros(user, {}) is False


def test_precedence_excludes_other_company_rows():
    """Filas de empresa B no entran si la query ya filtró; merge solo A + global."""
    rows = [
        _row("INV", "X", None),
        _row("INV", "Y", EMPRESA_A, "a"),
    ]
    merged, _, _ = apply_parametro_precedence(rows, EMPRESA_A)
    assert len(merged) == 2
    assert all(
        r.get("empresa_id") is None or r.get("empresa_id") == EMPRESA_A for r in merged
    )
