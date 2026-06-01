"""
I1: contrato de sesión ERP (require_erp_session).

Valida selection token bloqueado, empresa en permissions/menu y compatibilidad platform.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_active_user
from app.api.deps_auth import require_erp_session, require_full_session_payload
from app.core.auth.user_context import CurrentUserContext
from app.core.exceptions import AuthorizationError
from app.core.tenant.company_scope import (
    resolve_empresa_id_for_rbac,
    validate_erp_operational_session,
)

EMPRESA_A = uuid4()
EMPRESA_B = uuid4()
CLIENT_ID = uuid4()
USERNAME = "erp_user"


def _jwt_payload(
    *,
    empresa_id=None,
    selection_pending: bool = False,
    user_type: str = "user",
    is_super_admin: bool = False,
    es_superadmin: bool = False,
) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "sub": USERNAME,
        "cliente_id": str(CLIENT_ID),
        "access_level": 2,
        "is_super_admin": is_super_admin,
        "user_type": user_type,
        "type": "access",
    }
    if empresa_id is not None:
        p["empresa_id"] = str(empresa_id)
    if selection_pending:
        p["empresa_selection_pending"] = True
    if es_superadmin:
        p["es_superadmin"] = True
    return p


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


def _mock_user(user_type: str = "user", is_super_admin: bool = False) -> MagicMock:
    u = MagicMock()
    u.cliente_id = CLIENT_ID
    u.usuario_id = uuid4()
    u.nombre_usuario = USERNAME
    u.access_level = 2
    u.is_super_admin = is_super_admin
    u.user_type = user_type
    u.roles = []
    u.permisos = []
    return u


def _build_erp_probe_app() -> FastAPI:
    app = FastAPI()

    @app.get("/__test__/erp-probe")
    async def erp_probe(
        current_user=Depends(require_erp_session),
        payload: Dict = Depends(require_full_session_payload),
    ):
        empresa = resolve_empresa_id_for_rbac(payload=payload)
        return {
            "empresa_id": str(empresa) if empresa is not None else None,
            "user_type": current_user.user_type,
        }

    return app


@pytest.mark.integration
def test_validate_erp_session_requires_empresa_for_normal_user():
    with pytest.raises(AuthorizationError) as exc:
        validate_erp_operational_session(
            payload=_jwt_payload(empresa_id=None),
            user_type="user",
        )
    assert exc.value.internal_code == "MISSING_SESSION_EMPRESA"


@pytest.mark.integration
def test_validate_erp_session_allows_platform_admin_without_empresa():
    empresa = validate_erp_operational_session(
        payload=_jwt_payload(empresa_id=None, user_type="platform_admin", is_super_admin=True),
        user_type="platform_admin",
        is_super_admin=True,
    )
    assert empresa is None


def _override_jwt(app: FastAPI, payload: Dict[str, Any]) -> None:
    from app.api import deps

    async def _payload():
        return payload

    app.dependency_overrides[deps.get_current_user_data] = _payload


@pytest.mark.integration
@pytest.mark.asyncio
async def test_selection_token_blocked_on_erp_probe():
    app = _build_erp_probe_app()
    _override_jwt(app, _jwt_payload(selection_pending=True))
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/__test__/erp-probe")
        assert response.status_code == 409
        assert "selección" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_erp_session_without_empresa_returns_403():
    app = _build_erp_probe_app()
    _override_jwt(app, _jwt_payload(empresa_id=None))
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
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/__test__/erp-probe")
            assert response.status_code == 403
            body = response.json()
            assert "empresa" in body.get("detail", "").lower()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_erp_session_with_empresa_returns_empresa_in_handler():
    app = _build_erp_probe_app()
    _override_jwt(app, _jwt_payload(empresa_id=EMPRESA_A))
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
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/__test__/erp-probe")
            assert response.status_code == 200
            assert response.json()["empresa_id"] == str(EMPRESA_A)
        finally:
            app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_permissions_me_passes_empresa_id_to_resolver():
    from app.modules.auth.presentation.endpoints import get_permissions_me

    captured: Dict[str, Any] = {}

    class FakeEffective:
        codes = ["inv.producto.leer"]

    async def fake_get_effective_permissions(self, **kwargs):
        captured.update(kwargs)
        return FakeEffective()

    mock_user = _mock_user()
    payload = _jwt_payload(empresa_id=EMPRESA_A)

    with patch(
        "app.core.tenant.context.get_current_client_id",
        return_value=CLIENT_ID,
    ), patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=MagicMock(database_type="single"),
    ), patch(
        "app.core.authorization.permission_resolver.PermissionResolverService.get_effective_permissions",
        fake_get_effective_permissions,
    ), patch(
        "app.core.tenant.empresa_context.set_current_empresa_id",
        return_value=MagicMock(),
    ) as mock_set, patch(
        "app.core.tenant.empresa_context.reset_current_empresa_id",
    ):
        from app.core.tenant import empresa_context

        empresa_context.set_current_empresa_id(EMPRESA_A)
        try:
            result = await get_permissions_me(current_user=mock_user, payload=payload)
        finally:
            empresa_context.reset_current_empresa_id(mock_set.return_value)

    assert "inv.producto.leer" in result.permissions
    assert captured.get("empresa_id") == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_platform_admin_erp_session_without_empresa_ok():
    app = _build_erp_probe_app()
    _override_jwt(
        app,
        _jwt_payload(
            empresa_id=None,
            user_type="platform_admin",
            is_super_admin=True,
            es_superadmin=True,
        ),
    )
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
        new=AsyncMock(return_value=_mock_user("platform_admin", True)),
    ):
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/__test__/erp-probe")
            assert response.status_code == 200
            assert response.json()["empresa_id"] is None
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
def test_permission_cache_invalidate_for_user_all_empresa_keys():
    from app.core.authorization.permission_cache import PermissionCache

    cache = PermissionCache(ttl_seconds=60)
    uid, cid = uuid4(), uuid4()
    e1, e2 = uuid4(), uuid4()
    from app.core.authorization.effective_permissions import EffectivePermissions

    eff = EffectivePermissions(codes=["a"], is_super_admin=False, cliente_id=cid, usuario_id=uid)
    cache.set(cid, uid, eff, empresa_id=e1)
    cache.set(cid, uid, eff, empresa_id=e2)
    cache.set(cid, uid, eff, empresa_id=None)

    cache.invalidate_for_user(uid, cid)
    assert cache.get(cid, uid, e1) is None
    assert cache.get(cid, uid, e2) is None
    assert cache.get(cid, uid, None) is None
