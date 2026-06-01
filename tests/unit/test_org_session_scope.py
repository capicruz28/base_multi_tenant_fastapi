"""
Etapa A ORG: resolve_session_cliente_id y políticas de scope.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.auth.impersonation import impersonation_effective_level_info
from app.core.exceptions import AuthorizationError
from app.core.tenant.session_scope import (
    OrgScopePolicy,
    require_company_scope_if_needed,
    resolve_org_scope_policy,
    resolve_session_cliente_id,
)

SYSTEM_ID = uuid4()
ACME_ID = uuid4()
USER_ROW_ID = uuid4()


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


def test_resolve_session_cliente_id_impersonation_uses_jwt():
    res = resolve_session_cliente_id(
        payload=_impersonation_payload(),
        user_cliente_id=SYSTEM_ID,
        request_cliente_id=SYSTEM_ID,
    )
    assert res.cliente_id == ACME_ID
    assert res.source == "jwt_impersonation"
    assert res.is_impersonation is True


def test_resolve_session_cliente_id_legacy_uses_request_before_user():
    res = resolve_session_cliente_id(
        payload={"sub": "admin", "cliente_id": str(ACME_ID)},
        user_cliente_id=USER_ROW_ID,
        request_cliente_id=ACME_ID,
    )
    assert res.cliente_id == ACME_ID
    assert res.source == "request_tenant"
    assert res.is_impersonation is False


def test_resolve_org_scope_policy_empresa_is_tenant():
    assert resolve_org_scope_policy(resource="empresa") == OrgScopePolicy.TENANT
    assert resolve_org_scope_policy(resource="sucursales") == OrgScopePolicy.COMPANY
    assert resolve_org_scope_policy(resource="parametros") == OrgScopePolicy.HYBRID


def test_company_scope_blocks_impersonation_selection_pending():
    with pytest.raises(AuthorizationError) as exc:
        require_company_scope_if_needed(
            policy=OrgScopePolicy.COMPANY,
            payload=_impersonation_payload(selection_pending=True),
            user_type="tenant_admin",
            is_super_admin=False,
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


def test_tenant_scope_allows_impersonation_selection_pending():
    require_company_scope_if_needed(
        policy=OrgScopePolicy.TENANT,
        payload=_impersonation_payload(selection_pending=True),
        user_type="tenant_admin",
        is_super_admin=False,
    )
