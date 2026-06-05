"""Regression: login must propagate CustomException (403) instead of masking as 500."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.core.exceptions import AuthorizationError
from app.core.tenant.empresa_preference import USER_WITHOUT_COMPANY
from app.modules.auth.presentation import endpoints as auth_endpoints


def _unwrap_login():
    func = auth_endpoints.login
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


def _starlette_request() -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/api/v1/auth/login/",
        "headers": [(b"user-agent", b"pytest")],
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_login_reraises_custom_exception_for_user_without_company():
    login_fn = _unwrap_login()
    request = _starlette_request()
    response = Response()
    form_data = MagicMock(username="qa_norole", password="secret")

    cliente_id = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
    user_id = UUID("b3b06780-d718-47d8-86f1-49dc014cf372")

    fake_cliente = MagicMock(es_activo=True)

    with (
        patch(
            "app.modules.auth.presentation.endpoints.get_current_client_id",
            return_value=cliente_id,
        ),
        patch(
            "app.modules.auth.presentation.endpoints.ClienteService.obtener_cliente_por_id",
            new_callable=AsyncMock,
            return_value=fake_cliente,
        ),
        patch(
            "app.modules.auth.presentation.endpoints.get_client_type",
            return_value="mobile",
        ),
        patch(
            "app.modules.auth.presentation.endpoints.authenticate_user",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": user_id,
                "cliente_id": cliente_id,
                "target_cliente_id": cliente_id,
                "correo": "qa@t3.local",
                "nombre": None,
                "apellido": None,
                "es_activo": True,
                "es_superadmin": False,
            },
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.get_empresa_activa_para_login",
            new_callable=AsyncMock,
            return_value={
                "empresas_disponibles": [],
                "empresa_activa": None,
                "es_admin_sin_empresa": False,
                "requiere_seleccion": False,
            },
        ),
    ):
        with pytest.raises(AuthorizationError) as exc:
            await login_fn(request=request, response=response, form_data=form_data)

    assert exc.value.status_code == 403
    assert exc.value.internal_code == USER_WITHOUT_COMPANY


@pytest.mark.asyncio
async def test_login_still_maps_unexpected_errors_to_500():
    login_fn = _unwrap_login()
    request = _starlette_request()
    response = Response()
    form_data = MagicMock(username="broken", password="x")

    with (
        patch(
            "app.modules.auth.presentation.endpoints.get_current_client_id",
            return_value=UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.ClienteService.obtener_cliente_por_id",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db down"),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await login_fn(request=request, response=response, form_data=form_data)

    assert exc.value.status_code == 500
