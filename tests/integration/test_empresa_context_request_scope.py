"""
I0: empresa_context debe permanecer activo durante todo el request HTTP.

Valida el patrón yield en get_current_active_user y aislamiento entre requests.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_active_user
from app.core.auth.user_context import CurrentUserContext
from app.core.exceptions import AuthorizationError
from app.core.tenant.company_scope import require_session_empresa_id
from app.core.tenant.empresa_context import (
    coerce_empresa_id,
    reset_current_empresa_id,
    set_current_empresa_id,
    try_get_current_empresa_id,
)

EMPRESA_A = uuid4()
EMPRESA_B = uuid4()
CLIENT_ID = uuid4()
USERNAME = "probe_user"


def _auth_context() -> CurrentUserContext:
    return CurrentUserContext(
        usuario_id=uuid4(),
        cliente_id=CLIENT_ID,
        nombre_usuario=USERNAME,
        es_activo=True,
        is_superadmin=False,
        nivel_acceso=2,
        roles=["Usuario"],
    )


def _jwt_payload(empresa_id: UUID | None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "sub": USERNAME,
        "cliente_id": str(CLIENT_ID),
        "access_level": 2,
        "is_super_admin": False,
        "user_type": "user",
        "type": "access",
    }
    if empresa_id is not None:
        payload["empresa_id"] = str(empresa_id)
    return payload


def _mock_user() -> MagicMock:
    user = MagicMock()
    user.cliente_id = CLIENT_ID
    user.nombre_usuario = USERNAME
    user.access_level = 2
    user.is_super_admin = False
    user.user_type = "user"
    user.roles = []
    user.permisos = []
    return user


async def _consume_active_user_dependency(
    *,
    empresa_id: UUID | None,
) -> tuple[MagicMock, UUID | None, UUID | None]:
    """
    Simula FastAPI: setup dependencia → fase handler → teardown.
    """
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    request.client = None
    request.headers = {}

    handler_empresa: UUID | None = None
    gen = get_current_active_user(request, _jwt_payload(empresa_id))

    with patch(
        "app.core.tenant.context.get_current_client_id",
        return_value=CLIENT_ID,
    ), patch(
        "app.api.deps.get_user_auth_context",
        new=AsyncMock(return_value=_auth_context()),
    ), patch(
        "app.api.deps.validate_tenant_access",
        new=AsyncMock(return_value=True),
    ), patch(
        "app.api.deps.build_user_with_roles",
        new=AsyncMock(return_value=_mock_user()),
    ):
        user = await gen.__anext__()
        handler_empresa = try_get_current_empresa_id()
        assert handler_empresa == coerce_empresa_id(empresa_id)
        if empresa_id is None:
            with pytest.raises(AuthorizationError):
                require_session_empresa_id()
        else:
            assert require_session_empresa_id() == empresa_id
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    after_teardown = try_get_current_empresa_id()
    return user, handler_empresa, after_teardown


def _simulate_pre_i0_dependency_finally_before_handler(empresa_id: UUID) -> None:
    """Réplica del bug: finally de la dependencia corre antes del handler."""
    token = set_current_empresa_id(empresa_id)
    try:
        pass  # cuerpo de get_current_active_user (return usuario)
    finally:
        reset_current_empresa_id(token)
    # Aquí ejecutaría el route handler en FastAPI (sin yield)


@pytest.mark.integration
def test_pre_i0_finally_clears_context_before_handler_phase():
    _simulate_pre_i0_dependency_finally_before_handler(EMPRESA_A)
    assert try_get_current_empresa_id() is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_active_user_dependency_preserves_empresa_for_handler_phase():
    user, handler_empresa, after = await _consume_active_user_dependency(
        empresa_id=EMPRESA_A,
    )
    assert user is not None
    assert handler_empresa == EMPRESA_A
    assert after is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_active_user_dependency_cleans_empresa_after_teardown():
    _, handler_empresa, after = await _consume_active_user_dependency(
        empresa_id=EMPRESA_A,
    )
    assert handler_empresa == EMPRESA_A
    assert after is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_active_user_without_empresa_jwt_keeps_none_until_inv_guard():
    user, handler_empresa, after = await _consume_active_user_dependency(
        empresa_id=None,
    )
    assert user is not None
    assert handler_empresa is None
    assert after is None


def _build_probe_app() -> FastAPI:
    app = FastAPI()

    @app.get("/__test__/empresa-probe")
    async def empresa_probe(
        _user=Depends(get_current_active_user),
    ):
        return {"empresa_id": str(require_session_empresa_id())}

    return app


@pytest.fixture
def probe_app():
    return _build_probe_app()


@pytest.fixture
def auth_patches():
    with patch(
        "app.core.tenant.context.get_current_client_id",
        return_value=CLIENT_ID,
    ), patch(
        "app.api.deps.get_user_auth_context",
        new=AsyncMock(return_value=_auth_context()),
    ), patch(
        "app.api.deps.validate_tenant_access",
        new=AsyncMock(return_value=True),
    ), patch(
        "app.api.deps.build_user_with_roles",
        new=AsyncMock(return_value=_mock_user()),
    ):
        yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_handler_sees_empresa_from_jwt(probe_app, auth_patches):
    from app.api import deps

    async def override_payload():
        return _jwt_payload(EMPRESA_A)

    probe_app.dependency_overrides[deps.get_current_user_data] = override_payload
    try:
        async with AsyncClient(
            transport=ASGITransport(app=probe_app),
            base_url="http://test",
        ) as client:
            response = await client.get("/__test__/empresa-probe")
        assert response.status_code == 200
        assert response.json()["empresa_id"] == str(EMPRESA_A)
    finally:
        probe_app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_requests_do_not_leak_empresa_between_calls(probe_app, auth_patches):
    from app.api import deps

    async def override_a():
        return _jwt_payload(EMPRESA_A)

    async def override_b():
        return _jwt_payload(EMPRESA_B)

    transport = ASGITransport(app=probe_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        probe_app.dependency_overrides[deps.get_current_user_data] = override_a
        r1 = await client.get("/__test__/empresa-probe")
        probe_app.dependency_overrides[deps.get_current_user_data] = override_b
        r2 = await client.get("/__test__/empresa-probe")
        probe_app.dependency_overrides.clear()

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["empresa_id"] == str(EMPRESA_A)
    assert r2.json()["empresa_id"] == str(EMPRESA_B)


def _build_concurrent_probe_app() -> FastAPI:
    """App mínima con el mismo patrón yield que I0 (sin carreras en overrides)."""

    app = FastAPI()

    async def empresa_from_header(
        request: Request,
    ) -> AsyncGenerator[UUID, None]:
        raw = request.headers.get("X-Empresa-Id")
        empresa_id = coerce_empresa_id(raw)
        token = set_current_empresa_id(empresa_id)
        try:
            yield empresa_id
        finally:
            reset_current_empresa_id(token)

    @app.get("/__test__/empresa-probe-concurrent")
    async def probe(_: UUID = Depends(empresa_from_header)):
        await asyncio.sleep(0.03)
        return {"empresa_id": str(require_session_empresa_id())}

    return app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_async_requests_isolate_empresa_context():
    app = _build_concurrent_probe_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:

        async def call(empresa_id: UUID, delay: float) -> str:
            await asyncio.sleep(delay)
            response = await client.get(
                "/__test__/empresa-probe-concurrent",
                headers={"X-Empresa-Id": str(empresa_id)},
            )
            assert response.status_code == 200
            return response.json()["empresa_id"]

        results = await asyncio.gather(
            call(EMPRESA_A, 0.0),
            call(EMPRESA_B, 0.01),
        )

    assert set(results) == {str(EMPRESA_A), str(EMPRESA_B)}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_inv_company_scope_compatible_after_i0():
    _, handler_empresa, after = await _consume_active_user_dependency(
        empresa_id=EMPRESA_A,
    )
    assert handler_empresa == EMPRESA_A
    assert coerce_empresa_id(str(EMPRESA_A)) == EMPRESA_A
    assert after is None
