"""Unit tests — platform RBAC bootstrap (sin BD)."""
from uuid import uuid4

import pytest

from app.modules.tenant.application.services.platform_rbac_bootstrap_service import (
    ADMIN_PLATFORM_ACCESS,
    CORE_APP_ACCEDER,
    PLATFORM_ADMIN_ROL_CODIGO,
    PLATFORM_MODULOS,
)


def test_platform_constants():
    assert PLATFORM_ADMIN_ROL_CODIGO == "ADMIN_PLATFORM"
    assert "SYS_ADMIN" in PLATFORM_MODULOS
    assert ADMIN_PLATFORM_ACCESS == "admin.platform.access"
    assert CORE_APP_ACCEDER == "core.app.acceder"
