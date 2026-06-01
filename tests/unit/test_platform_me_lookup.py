"""Tests: lookup platform /me — fila usuario completa (no columnas parciales)."""
from datetime import datetime
from uuid import UUID
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.core.auth.platform_user_lookup import fetch_usuario_auth_row, is_system_request_client
from app.modules.users.presentation.schemas import UsuarioReadWithRoles


SYSTEM_ID = UUID(str(settings.SUPERADMIN_CLIENTE_ID))


@pytest.mark.unit
def test_is_system_request_client_matches_superadmin_uuid():
    assert is_system_request_client(SYSTEM_ID) is True
    assert is_system_request_client(UUID("11111111-1111-1111-1111-111111111111")) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_usuario_auth_row_system_prefers_full_admin_row():
    """No debe devolver fila parcial si execute_auth_query ya encontró usuario."""
    from sqlalchemy import select
    from app.infrastructure.database.tables import UsuarioTable

    full_row = {
        "usuario_id": UUID("00000000-0000-0000-0000-000000000100"),
        "cliente_id": SYSTEM_ID,
        "nombre_usuario": "superadmin",
        "correo": "admin@plataforma.com",
        "nombre": "Administrador",
        "apellido": "Sistema",
        "es_activo": True,
        "fecha_creacion": datetime(2025, 1, 1),
        "proveedor_autenticacion": "local",
        "es_eliminado": False,
    }
    partial_row = {
        "usuario_id": full_row["usuario_id"],
        "cliente_id": SYSTEM_ID,
        "nombre_usuario": "superadmin",
        "correo": "admin@plataforma.com",
        "nombre": "Administrador",
        "apellido": "Sistema",
        "es_activo": True,
    }

    user_query = select(UsuarioTable)

    with patch(
        "app.core.auth.platform_user_lookup.execute_auth_query",
        new=AsyncMock(return_value=full_row),
    ) as mock_auth, patch(
        "app.core.auth.platform_user_lookup.fetch_platform_usuario_row",
        new=AsyncMock(return_value=partial_row),
    ) as mock_platform:
        row = await fetch_usuario_auth_row(
            user_query,
            username="superadmin",
            request_cliente_id=SYSTEM_ID,
        )

    assert row == full_row
    mock_auth.assert_awaited_once()
    mock_platform.assert_not_awaited()


@pytest.mark.unit
def test_usuario_read_with_roles_requires_fecha_creacion():
    """Fila parcial (sin fecha_creacion) falla validación — causa del 500 en /me."""
    partial = {
        "usuario_id": UUID("00000000-0000-0000-0000-000000000100"),
        "cliente_id": SYSTEM_ID,
        "nombre_usuario": "superadmin",
        "correo": "admin@plataforma.com",
        "es_activo": True,
        "access_level": 5,
        "is_super_admin": True,
        "user_type": "platform_admin",
    }
    with pytest.raises(Exception):
        UsuarioReadWithRoles(**partial, roles=[], permisos=[])
