"""BF-01 — regresión bloqueadores G3 (auth-config + usuarios globales)."""
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.modules.auth.presentation.schemas import AuthConfigRead
from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)
from app.modules.superadmin.presentation.schemas import ClienteInfo

_NULLABLE_AUTH_CONFIG_FIELDS = frozenset({
    "fecha_actualizacion",
    "ip_whitelist",
    "ip_blacklist",
    "horario_acceso_config",
})


def _build_auth_config_read(row: dict) -> AuthConfigRead:
    """Espejo de AuthConfigService._build_auth_config_read (evita import circular)."""
    payload = dict(row)
    for key in list(payload.keys()):
        if payload[key] is None and key not in _NULLABLE_AUTH_CONFIG_FIELDS:
            payload.pop(key)
    if not payload.get("fecha_creacion"):
        payload["fecha_creacion"] = datetime.utcnow()
    return AuthConfigRead(**payload)


def test_build_auth_config_read_strips_null_booleans():
    row = {
        "config_id": uuid4(),
        "cliente_id": uuid4(),
        "password_min_length": None,
        "password_require_uppercase": None,
        "fecha_creacion": datetime.utcnow(),
    }
    read = _build_auth_config_read(row)
    assert isinstance(read, AuthConfigRead)
    assert read.password_min_length == 8
    assert read.password_require_uppercase is True


@pytest.mark.asyncio
async def test_resolve_cliente_info_uses_filter_when_present():
    filtered_id = uuid4()
    filtered_info = ClienteInfo(
        cliente_id=filtered_id,
        razon_social="Filtered SA",
        subdominio="filtered",
        codigo_cliente="FIL",
        nombre_comercial=None,
        tipo_instalacion="shared",
        estado_suscripcion="activo",
    )
    resolved = await SuperadminUsuarioService._resolve_cliente_info_for_usuario(
        uuid4(),
        filtered_cliente_id=filtered_id,
        filtered_cliente_info=filtered_info,
    )
    assert resolved.subdominio == "filtered"


@pytest.mark.asyncio
async def test_resolve_cliente_info_fetches_per_user_without_filter(monkeypatch):
    user_cliente_id = uuid4()
    expected = ClienteInfo(
        cliente_id=user_cliente_id,
        razon_social="Tenant SA",
        subdominio="tenant-a",
        codigo_cliente="TA",
        nombre_comercial=None,
        tipo_instalacion="shared",
        estado_suscripcion="activo",
    )

    async def _mock_fetch(cliente_id: UUID):
        assert cliente_id == user_cliente_id
        return expected

    monkeypatch.setattr(
        SuperadminUsuarioService,
        "_fetch_cliente_info_from_admin",
        _mock_fetch,
    )
    resolved = await SuperadminUsuarioService._resolve_cliente_info_for_usuario(
        user_cliente_id,
        filtered_cliente_id=None,
        filtered_cliente_info=None,
    )
    assert resolved.subdominio == "tenant-a"
