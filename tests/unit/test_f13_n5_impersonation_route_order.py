"""
F13-N5 — Colisión de rutas POST /auth/impersonate/end/ vs /impersonate/{cliente_id}/.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.routing import Match

from app.core.security.jwt import create_access_token
from app.main import app
from app.modules.auth.presentation import endpoints as auth_endpoints


def _impersonate_routes():
    return [
        route
        for route in auth_endpoints.router.routes
        if hasattr(route, "path") and "impersonate" in route.path
    ]


@pytest.mark.unit
def test_impersonate_end_route_registered_before_parametric():
    routes = _impersonate_routes()
    assert len(routes) >= 2
    assert routes[0].path == "/impersonate/end/"
    assert routes[0].endpoint.__name__ == "finalizar_impersonacion"
    assert routes[1].path == "/impersonate/{cliente_id}/"
    assert routes[1].endpoint.__name__ == "iniciar_impersonacion"


@pytest.mark.unit
def test_starlette_first_match_for_impersonate_end_is_finalizar():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/impersonate/end/",
        "headers": [],
        "query_string": b"",
    }
    matches = []
    for route in auth_endpoints.router.routes:
        if not hasattr(route, "matches"):
            continue
        match, _ = route.matches(scope)
        if match == Match.FULL:
            matches.append(route.endpoint.__name__)
    assert matches[0] == "finalizar_impersonacion"


@pytest.mark.unit
def test_starlette_parametric_route_still_matches_uuid_cliente_id():
    cliente_id = uuid4()
    scope = {
        "type": "http",
        "method": "POST",
        "path": f"/impersonate/{cliente_id}/",
        "headers": [],
        "query_string": b"",
    }
    matches = []
    for route in auth_endpoints.router.routes:
        if not hasattr(route, "matches"):
            continue
        match, _ = route.matches(scope)
        if match == Match.FULL:
            matches.append((route.path, route.endpoint.__name__))
    assert matches == [
        ("/impersonate/{cliente_id}/", "iniciar_impersonacion"),
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_post_impersonate_end_dispatches_to_finalizar_handler():
    token, _jti = create_access_token(
        data={
            "sub": "superadmin",
            "cliente_id": str(uuid4()),
            "is_impersonation": True,
            "user_type": "tenant_admin",
            "is_super_admin": False,
            "access_level": 4,
            "effective_scope": "tenant",
        }
    )
    restored = {"access_token": "parent-access-token", "token_type": "bearer"}

    with patch(
        "app.infrastructure.redis.client.RedisService.is_token_blacklisted",
        new=AsyncMock(return_value=False),
    ), patch.object(
        auth_endpoints.ImpersonationService,
        "finalizar_impersonacion",
        new=AsyncMock(return_value=restored.copy()),
    ) as mock_finalizar:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/impersonate/end/",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "parent-access-token"
    assert "Super Administrador" not in (response.text or "")
    mock_finalizar.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_post_impersonate_end_no_super_admin_403():
    """Regresión F13-N4: /end/ con JWT impersonación no debe devolver 403 Super Admin."""
    token, _jti = create_access_token(
        data={
            "sub": "superadmin",
            "cliente_id": str(uuid4()),
            "is_impersonation": True,
            "user_type": "tenant_admin",
            "is_super_admin": False,
            "access_level": 4,
        }
    )

    with patch(
        "app.infrastructure.redis.client.RedisService.is_token_blacklisted",
        new=AsyncMock(return_value=False),
    ), patch.object(
        auth_endpoints.ImpersonationService,
        "finalizar_impersonacion",
        new=AsyncMock(
            return_value={"access_token": "restored", "token_type": "bearer"}
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/impersonate/end/",
                headers={"Authorization": f"Bearer {token}"},
            )

    assert response.status_code == 200
    assert response.json()["access_token"] == "restored"
    assert "Super Administrador" not in response.text


def _run_route_order_regression():
    """Ejecutado también desde documentación F13-N5."""
    test_impersonate_end_route_registered_before_parametric()
    test_starlette_first_match_for_impersonate_end_is_finalizar()


if __name__ == "__main__":
    _run_route_order_regression()
    print("route order OK")
