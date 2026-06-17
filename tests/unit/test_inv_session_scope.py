"""INV session scope — alineación con ORG (impersonación → JWT tenant)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.auth.impersonation import impersonation_effective_level_info
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.tenant.session_scope import resolve_session_cliente_id

SYSTEM_ID = uuid4()
ACME_ID = uuid4()


def _impersonation_payload(*, selection_pending: bool = False) -> dict:
    data = {
        "sub": "platform_admin",
        "cliente_id": str(ACME_ID),
        "is_impersonation": True,
        "effective_scope": "tenant",
        **impersonation_effective_level_info(),
    }
    if selection_pending:
        data["empresa_selection_pending"] = True
    return data


def test_resolve_session_cliente_id_inv_pattern_matches_org_impersonation():
    """Mismo resultado que ORG: JWT tenant, no fila SYSTEM del operador."""
    res = resolve_session_cliente_id(
        payload=_impersonation_payload(),
        user_cliente_id=SYSTEM_ID,
        request_cliente_id=SYSTEM_ID,
    )
    assert res.cliente_id == ACME_ID
    assert res.source == "jwt_impersonation"


def test_get_inv_session_client_id_exported():
    assert get_inv_session_client_id.__name__ == "get_inv_session_client_id"
