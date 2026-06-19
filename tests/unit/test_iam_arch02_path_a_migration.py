"""IAM-ARCH-02: PATH A migration — build_user_with_roles multi + session endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.auth.user_builder import build_user_with_roles
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

CLIENTE_ID = UUID("c405c76f-0cf8-44c5-a281-e95b0ac26f8b")
USUARIO_ID = uuid4()


def _usuario_row() -> dict:
    return {
        "usuario_id": USUARIO_ID,
        "cliente_id": None,
        "nombre_usuario": "admin",
        "correo": "admin@test.com",
        "nombre": "Admin",
        "apellido": "User",
        "es_activo": True,
        "fecha_creacion": "2026-01-01T00:00:00",
        "es_eliminado": False,
        "proveedor_autenticacion": "local",
    }


@pytest.mark.asyncio
async def test_build_user_with_roles_multi_fetches_user_row():
    """AUTH-CTX-01: rama multi debe invocar fetch_usuario_auth_row."""
    mock_fetch = AsyncMock(return_value=_usuario_row())
    tenant_ctx = MagicMock(database_type="multi")

    with patch(
        "app.core.tenant.context.try_get_tenant_context",
        return_value=tenant_ctx,
    ), patch(
        "app.core.tenant.empresa_context.try_get_current_empresa_id",
        return_value=None,
    ), patch(
        "app.core.auth.user_builder.fetch_usuario_auth_row",
        mock_fetch,
    ), patch(
        "app.infrastructure.database.queries_async.execute_query",
        AsyncMock(return_value=[]),
    ), patch(
        "app.core.auth.user_builder.resolve_platform_superadmin_flag",
        return_value=False,
    ):
        result = await build_user_with_roles("admin", request_cliente_id=CLIENTE_ID)

    mock_fetch.assert_awaited_once()
    assert result is not None
    assert result.cliente_id == CLIENTE_ID
    assert result.nombre_usuario == "admin"


def test_session_endpoints_use_path_a_dependencies():
    """Los 5 endpoints migrados no deben importar Depends(get_current_user)."""
    import inspect

    from app.modules.auth.presentation import endpoints as auth_ep

    targets = [
        auth_ep.get_active_sessions_endpoint,
        auth_ep.logout_all_sessions,
        auth_ep.admin_list_all_active_sessions,
        auth_ep.admin_revoke_session_by_id,
        auth_ep.admin_cleanup_expired_tokens_all_tenants,
    ]
    for fn in targets:
        sig = inspect.signature(fn)
        for name, param in sig.parameters.items():
            if name != "current_user":
                continue
            default = param.default
            dep = getattr(default, "dependency", None)
            assert dep is not None, f"{fn.__name__}: current_user sin Depends"
            dep_name = getattr(dep, "__name__", str(dep))
            assert "get_current_user" not in dep_name, (
                f"{fn.__name__} aún usa PATH B: {dep_name}"
            )


def test_session_endpoints_no_router_level_require_admin_duplicate():
    """Admin endpoints: un solo require_admin vía parámetro (no dependencies= duplicado)."""
    from app.modules.auth.presentation.endpoints import router

    path_handlers = {
        (getattr(r, "path", None), tuple(getattr(r, "methods", ()) or ())): r
        for r in router.routes
    }
    admin_paths = [
        ("/sessions/admin/", ("GET",)),
        ("/sessions/{token_id}/revoke_admin/", ("POST",)),
        ("/admin/cleanup-expired-tokens/", ("POST",)),
    ]
    for key in admin_paths:
        route = path_handlers.get(key)
        assert route is not None, f"Ruta no encontrada: {key}"
        dep_names = [
            getattr(d.dependency, "__name__", str(d.dependency))
            for d in (route.dependencies or [])
        ]
        assert "RoleChecker.__call__" not in str(dep_names) and not any(
            "require_admin" in n for n in dep_names
        ), f"Ruta {key} tiene dependencies= redundante: {dep_names}"
