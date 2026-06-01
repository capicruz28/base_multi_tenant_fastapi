"""
Regresión: login no falla si apellido en BD tiene caracteres de razón social (p. ej. 'S.A.').
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.auth.presentation.schemas import (
    UserDataWithRoles,
    build_user_data_with_roles_dict,
)
from app.shared.validators import sanitize_person_name


def test_sanitize_person_name_strips_legal_suffix_dots():
    assert sanitize_person_name("ACME Corporation S.A.") == "ACME Corporation S A"


def test_sanitize_person_name_strips_digits_to_match_auth_validator():
    """Dígitos no son válidos en UserDataBase; se eliminan (E2E → E E)."""
    assert sanitize_person_name("E2E Validation Tenant S.A.") == "E E Validation Tenant S A"


def test_sanitize_person_name_none_for_empty_after_clean():
    assert sanitize_person_name("...123...") is None


def test_user_data_with_roles_accepts_onboarding_style_apellido_from_db():
    """Simula fila usuario con apellido = razon_social legacy (repro E2E)."""
    profile = build_user_data_with_roles_dict(
        usuario_id=uuid4(),
        nombre_usuario="admin",
        correo="admin@e2evalid01.test",
        nombre="Administrador",
        apellido="E2E Validation Tenant S.A.",
        es_activo=True,
        roles=["Administrador"],
        access_level=5,
        is_super_admin=False,
        user_type="tenant_admin",
        cliente_id=uuid4(),
        es_admin_cliente=True,
        empresa_activa=None,
    )
    user_data = UserDataWithRoles.model_validate(profile)
    assert user_data.apellido == "E E Validation Tenant S A"
    assert user_data.nombre_usuario == "admin"


def test_build_user_data_sanitizes_before_pydantic_validator():
    profile = build_user_data_with_roles_dict(
        usuario_id=uuid4(),
        nombre_usuario="admin",
        correo="x@y.com",
        nombre="Ok",
        apellido="ACME Corp. #1",
        es_activo=True,
        roles=[],
        access_level=5,
        is_super_admin=False,
        user_type="tenant_admin",
        cliente_id=uuid4(),
        es_admin_cliente=True,
    )
    assert profile["apellido"] == "ACME Corp"
    UserDataWithRoles.model_validate(profile)
