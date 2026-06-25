"""Unit tests — Reset administrativo de contraseña (PR1)."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ServiceError, ValidationError
from app.core.security.password_generator import generar_contrasena_segura
from app.modules.users.application.services.admin_password_reset_service import (
    AdminPasswordResetService,
)
from app.modules.users.presentation.endpoints import reset_usuario_password_admin
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

_CLIENTE_ID = uuid4()
_ADMIN_ID = uuid4()
_TARGET_ID = uuid4()

_SVC = "app.modules.users.application.services.admin_password_reset_service"
_AUDIT = f"{_SVC}.AuditService.registrar_auth_event"


def _admin_user(*, usuario_id=None, permisos=None) -> UsuarioReadWithRoles:
    return UsuarioReadWithRoles(
        usuario_id=usuario_id or _ADMIN_ID,
        cliente_id=_CLIENTE_ID,
        nombre_usuario="admin",
        correo="admin@test.com",
        es_activo=True,
        correo_confirmado=True,
        fecha_creacion="2026-01-01T00:00:00",
        roles=[],
        access_level=4,
        is_super_admin=False,
        user_type="tenant_admin",
        permisos=permisos or ["admin.usuario.reset_password"],
    )


def test_generar_contrasena_segura_meets_policy():
    pwd = generar_contrasena_segura(12)
    assert len(pwd) == 12
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)
    assert any(c.isdigit() for c in pwd)
    assert any(c in "!@#$%&*" for c in pwd)


@pytest.mark.asyncio
async def test_reset_rejects_self_reset():
    with patch(_AUDIT, new_callable=AsyncMock):
        with pytest.raises(ValidationError) as exc:
            await AdminPasswordResetService.reset_password_admin(
                cliente_id=_CLIENTE_ID,
                admin_usuario_id=_ADMIN_ID,
                target_usuario_id=_ADMIN_ID,
            )
    assert exc.value.internal_code == "SELF_PASSWORD_RESET_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_reset_user_not_found():
    with (
        patch(_AUDIT, new_callable=AsyncMock),
        patch(
            f"{_SVC}.UsuarioService.obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with pytest.raises(NotFoundError) as exc:
            await AdminPasswordResetService.reset_password_admin(
                cliente_id=_CLIENTE_ID,
                admin_usuario_id=_ADMIN_ID,
                target_usuario_id=_TARGET_ID,
            )
    assert exc.value.internal_code == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_reset_rejects_sso_user():
    with (
        patch(_AUDIT, new_callable=AsyncMock),
        patch(
            f"{_SVC}.UsuarioService.obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": _TARGET_ID,
                "nombre_usuario": "sso_user",
                "proveedor_autenticacion": "azure",
            },
        ),
    ):
        with pytest.raises(ValidationError) as exc:
            await AdminPasswordResetService.reset_password_admin(
                cliente_id=_CLIENTE_ID,
                admin_usuario_id=_ADMIN_ID,
                target_usuario_id=_TARGET_ID,
            )
    assert exc.value.internal_code == "USER_SSO_PASSWORD_NOT_MANAGED"


@pytest.mark.asyncio
async def test_reset_success_local_user():
    with (
        patch(_AUDIT, new_callable=AsyncMock),
        patch(
            f"{_SVC}.UsuarioService.obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": _TARGET_ID,
                "nombre_usuario": "jperez",
                "proveedor_autenticacion": "local",
            },
        ),
        patch(f"{_SVC}.get_password_hash", return_value="hashed"),
        patch(f"{_SVC}.generar_contrasena_segura", return_value="TempPass123!"),
        patch(
            f"{_SVC}.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 1},
        ),
        patch(
            f"{_SVC}.AdminPasswordResetService._revoke_sessions_after_reset",
            new_callable=AsyncMock,
            return_value=2,
        ),
    ):
        result = await AdminPasswordResetService.reset_password_admin(
            cliente_id=_CLIENTE_ID,
            admin_usuario_id=_ADMIN_ID,
            target_usuario_id=_TARGET_ID,
        )

    assert result["success"] is True
    assert result["usuario_id"] == _TARGET_ID
    assert result["sesiones_revocadas"] == 2
    assert result["credenciales_temporales"]["nombre_usuario"] == "jperez"
    assert result["credenciales_temporales"]["contrasena"] == "TempPass123!"
    assert result["credenciales_temporales"]["requiere_cambio"] is True


@pytest.mark.asyncio
async def test_reset_fails_when_update_affects_zero_rows():
    with (
        patch(_AUDIT, new_callable=AsyncMock),
        patch(
            f"{_SVC}.UsuarioService.obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": _TARGET_ID,
                "nombre_usuario": "jperez",
                "proveedor_autenticacion": "local",
            },
        ),
        patch(f"{_SVC}.get_password_hash", return_value="hashed"),
        patch(f"{_SVC}.generar_contrasena_segura", return_value="TempPass123!"),
        patch(
            f"{_SVC}.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 0},
        ),
    ):
        with pytest.raises(ServiceError) as exc:
            await AdminPasswordResetService.reset_password_admin(
                cliente_id=_CLIENTE_ID,
                admin_usuario_id=_ADMIN_ID,
                target_usuario_id=_TARGET_ID,
            )
    assert exc.value.internal_code == "PASSWORD_RESET_FAILED"


@pytest.mark.asyncio
async def test_reset_session_revoke_failure_raises():
    with (
        patch(_AUDIT, new_callable=AsyncMock),
        patch(
            f"{_SVC}.UsuarioService.obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": _TARGET_ID,
                "nombre_usuario": "jperez",
                "proveedor_autenticacion": "local",
            },
        ),
        patch(f"{_SVC}.get_password_hash", return_value="hashed"),
        patch(f"{_SVC}.generar_contrasena_segura", return_value="TempPass123!"),
        patch(
            f"{_SVC}.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 1},
        ),
        patch(
            f"{_SVC}.AdminPasswordResetService._revoke_sessions_after_reset",
            new_callable=AsyncMock,
            side_effect=RuntimeError("revoke failed"),
        ),
    ):
        with pytest.raises(ServiceError) as exc:
            await AdminPasswordResetService.reset_password_admin(
                cliente_id=_CLIENTE_ID,
                admin_usuario_id=_ADMIN_ID,
                target_usuario_id=_TARGET_ID,
            )
    assert exc.value.internal_code == "PASSWORD_RESET_SESSION_REVOKE_FAILED"


@pytest.mark.asyncio
async def test_endpoint_delegates_to_service():
    mock_request = type(
        "Req",
        (),
        {
            "client": type("C", (), {"host": "127.0.0.1"})(),
            "headers": {"user-agent": "pytest"},
        },
    )()
    expected = {
        "success": True,
        "message": "ok",
        "usuario_id": _TARGET_ID,
        "credenciales_temporales": {
            "nombre_usuario": "u",
            "contrasena": "x",
            "requiere_cambio": True,
        },
        "sesiones_revocadas": 0,
    }
    with patch.object(
        AdminPasswordResetService,
        "reset_password_admin",
        new_callable=AsyncMock,
        return_value=expected,
    ) as mock_svc:
        result = await reset_usuario_password_admin(
            request=mock_request,
            usuario_id=_TARGET_ID,
            current_user=_admin_user(),
        )
    assert result == expected
    mock_svc.assert_awaited_once()
