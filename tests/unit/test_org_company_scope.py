"""
Etapa B ORG: aislamiento company-scoped (empresa desde sesión).
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import AuthorizationError
from app.core.tenant.company_scope import (
    assert_row_empresa,
    enforce_body_empresa_matches_session,
    reject_client_empresa_scope_override,
)
from app.core.tenant.empresa_context import set_current_empresa_id, reset_current_empresa_id

EMPRESA_A = uuid4()
EMPRESA_B = uuid4()


def test_reject_client_empresa_scope_override_mismatch():
    token = set_current_empresa_id(EMPRESA_A)
    try:
        with pytest.raises(AuthorizationError) as exc:
            reject_client_empresa_scope_override(EMPRESA_B, source="query")
        assert exc.value.internal_code == "EMPRESA_SCOPE_MISMATCH"
    finally:
        reset_current_empresa_id(token)


def test_reject_client_empresa_scope_override_none_ok():
    token = set_current_empresa_id(EMPRESA_A)
    try:
        reject_client_empresa_scope_override(None, source="query")
    finally:
        reset_current_empresa_id(token)


def test_enforce_body_empresa_matches_session():
    token = set_current_empresa_id(EMPRESA_A)
    try:
        assert enforce_body_empresa_matches_session(EMPRESA_A) == EMPRESA_A
        with pytest.raises(AuthorizationError) as exc:
            enforce_body_empresa_matches_session(EMPRESA_B)
        assert exc.value.internal_code == "EMPRESA_MISMATCH"
    finally:
        reset_current_empresa_id(token)


def test_assert_row_empresa_cross_company_404():
    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        assert_row_empresa(
            {"empresa_id": EMPRESA_B},
            EMPRESA_A,
            not_found_detail="Recurso no encontrado",
        )
