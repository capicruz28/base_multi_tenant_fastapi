"""
Etapa C1 ORG: org_empresa tenant-scoped (assert_row_tenant, session client_id).
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import assert_row_tenant
from app.core.tenant.session_scope import resolve_session_cliente_id

TENANT_A = uuid4()
TENANT_B = uuid4()
EMPRESA_ID = uuid4()


def test_assert_row_tenant_cross_tenant_404():
    with pytest.raises(NotFoundError):
        assert_row_tenant(
            {"cliente_id": TENANT_B, "empresa_id": EMPRESA_ID},
            TENANT_A,
            not_found_detail="Empresa no encontrada",
        )


def test_assert_row_tenant_ok():
    assert_row_tenant(
        {"cliente_id": TENANT_A, "empresa_id": EMPRESA_ID},
        TENANT_A,
    )


def test_resolve_session_cliente_id_impersonation_not_user_row():
    """Impersonación: JWT tenant gana sobre user_row SYSTEM."""
    res = resolve_session_cliente_id(
        payload={
            "cliente_id": str(TENANT_A),
            "is_impersonation": True,
            "effective_scope": "tenant",
        },
        user_cliente_id=TENANT_B,
        request_cliente_id=TENANT_B,
    )
    assert res.cliente_id == TENANT_A
    assert res.source == "jwt_impersonation"
