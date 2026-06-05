"""
Tests unitarios: impersonación de soporte plataforma.
"""
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps_auth import (
    reject_selection_token_for_me,
    require_full_session_payload,
)
from app.core.auth.impersonation import (
    extract_impersonation_claims,
    impersonation_effective_level_info,
    is_impersonation_payload,
    suppress_platform_privileges,
    IMPERSONATION_ACCESS_TTL_MINUTES,
)
from app.core.tenant.company_scope import is_platform_operator
from app.core.auth.impersonation_rbac import (
    is_impersonation_effective_tenant_session,
    impersonation_passes_tenant_admin_gate,
    resolve_menu_cliente_id_for_session,
)
from app.core.authorization.menu_resolver import get_menu_resolver
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse, ModuloMenuResponse
from app.modules.auth.application.services.auth_service import AuthService


@pytest.mark.unit
def test_is_impersonation_payload():
    assert not is_impersonation_payload(None)
    assert not is_impersonation_payload({})
    assert is_impersonation_payload({"is_impersonation": True})


@pytest.mark.unit
def test_extract_impersonation_claims():
    uid = uuid4()
    claims = extract_impersonation_claims(
        {
            "is_impersonation": True,
            "impersonated_by": str(uid),
            "impersonated_by_username": "operator",
        }
    )
    assert claims["is_impersonation"] is True
    assert claims["impersonated_by"] == str(uid)
    assert claims["impersonated_by_username"] == "operator"


@pytest.mark.unit
def test_impersonation_ttl_is_120_minutes():
    assert IMPERSONATION_ACCESS_TTL_MINUTES == 120


@pytest.mark.unit
@pytest.mark.asyncio
async def test_me_allows_selection_token_during_impersonation():
    payload = {
        "sub": "superadmin",
        "empresa_selection_pending": True,
        "is_impersonation": True,
        "type": "access",
    }
    result = await reject_selection_token_for_me(payload)
    assert result["is_impersonation"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_session_allows_impersonation_selection_for_menu():
    payload = {
        "sub": "superadmin",
        "empresa_selection_pending": True,
        "is_impersonation": True,
    }
    result = await require_full_session_payload(payload)
    assert result["is_impersonation"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cambiar_empresa_blocked_during_impersonation():
    payload = {
        "sub": "superadmin",
        "cliente_id": str(uuid4()),
        "is_impersonation": True,
        "impersonated_by": str(uuid4()),
        "impersonated_by_username": "op",
    }
    with pytest.raises(HTTPException) as exc:
        await AuthService.cambiar_empresa_sesion(
            payload=payload,
            empresa_id=uuid4(),
            client_type="web",
            ip_address=None,
            user_agent=None,
            old_refresh_token=None,
        )
    assert exc.value.status_code == 403


@pytest.mark.unit
def test_impersonation_effective_level_info_is_tenant_scoped():
    info = impersonation_effective_level_info()
    assert info["user_type"] == "tenant_admin"
    assert info["access_level"] == 4
    assert info["is_super_admin"] is False
    assert info["effective_scope"] == "tenant"


@pytest.mark.unit
def test_suppress_platform_privileges_during_impersonation():
    payload = {
        "is_impersonation": True,
        "impersonated_by": "x",
        "user_type": "platform_admin",
        "es_superadmin": True,
        "access_level": 5,
        "is_super_admin": True,
    }
    is_super, ut, level = suppress_platform_privileges(
        payload=payload,
        is_super_admin=True,
        user_type="platform_admin",
        access_level=5,
    )
    assert is_super is False
    assert ut == "tenant_admin"
    assert level == 4


@pytest.mark.unit
def test_is_impersonation_effective_tenant_session_requires_scope():
    assert is_impersonation_effective_tenant_session(
        {"is_impersonation": True, "effective_scope": "tenant"}
    )
    assert not is_impersonation_effective_tenant_session(
        {"is_impersonation": True, "effective_scope": "platform"}
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_effective_impersonation_permissions_from_admin_tenant_role():
    from unittest.mock import AsyncMock, patch
    from uuid import uuid4

    from app.core.auth.impersonation_rbac import get_effective_impersonation_permissions

    cid = uuid4()
    with patch(
        "app.core.auth.impersonation_rbac.execute_query",
        new=AsyncMock(
            return_value=[
                {"codigo": "admin.usuario.leer"},
                {"codigo": "tenant.branding.leer"},
                {"codigo": "org.empresa.leer"},
            ]
        ),
    ):
        codes = await get_effective_impersonation_permissions(cid, database_type="single")

    assert "admin.usuario.leer" in codes
    assert "tenant.branding.leer" in codes
    assert len(codes) == 3


@pytest.mark.unit
def test_impersonation_passes_tenant_admin_gate_with_context():
    from unittest.mock import MagicMock

    from app.core.auth.impersonation_rbac import (
        clear_impersonation_rbac_context,
        get_impersonation_effective_permissions_cached,
    )

    import app.core.auth.impersonation_rbac as mod

    mod._impersonation_permissions_ctx.set(frozenset(["admin.usuario.leer"]))
    try:
        user = MagicMock(access_level=4)
        assert impersonation_passes_tenant_admin_gate(user) is True
        user.access_level = 2
        assert impersonation_passes_tenant_admin_gate(user) is False
    finally:
        clear_impersonation_rbac_context()


@pytest.mark.unit
def test_resolve_menu_cliente_id_uses_jwt_not_system_user():
    acme = UUID("11111111-1111-1111-1111-111111111111")
    system = UUID("00000000-0000-0000-0000-000000000001")
    resolved = resolve_menu_cliente_id_for_session(
        payload={
            "is_impersonation": True,
            "effective_scope": "tenant",
            "cliente_id": str(acme),
        },
        user_cliente_id=system,
        request_cliente_id=system,
    )
    assert resolved == acme


@pytest.mark.unit
def test_resolve_impersonation_tenant_cliente_id_prefers_jwt_over_system():
    from app.core.auth.impersonation_rbac import resolve_impersonation_tenant_cliente_id

    acme = UUID("11111111-1111-1111-1111-111111111111")
    system = UUID("00000000-0000-0000-0000-000000000001")
    resolved = resolve_impersonation_tenant_cliente_id(
        {
            "is_impersonation": True,
            "effective_scope": "tenant",
            "cliente_id": str(acme),
        },
        user_cliente_id=system,
        request_cliente_id=system,
    )
    assert resolved == acme


@pytest.mark.unit
@pytest.mark.asyncio
async def test_permission_resolver_impersonation_uses_jwt_cliente_id_not_system():
    from unittest.mock import AsyncMock, patch
    from uuid import uuid4

    from app.core.authorization.permission_resolver import PermissionResolverService

    tenant_cid = uuid4()
    system_cid = UUID("00000000-0000-0000-0000-000000000001")
    payload = {
        "is_impersonation": True,
        "effective_scope": "tenant",
        "cliente_id": str(tenant_cid),
    }
    org_codes = ["org.empresa.leer", "org.sucursal.leer", "inv.producto.leer"]

    with patch(
        "app.core.auth.impersonation_rbac.get_effective_impersonation_permissions",
        new=AsyncMock(return_value=org_codes),
    ) as mock_imp:
        resolver = PermissionResolverService()
        effective = await resolver.get_effective_permissions(
            usuario_id=uuid4(),
            cliente_id=system_cid,
            payload=payload,
        )

    mock_imp.assert_awaited_once()
    assert mock_imp.await_args.args[0] == tenant_cid
    assert effective.cliente_id == tenant_cid
    assert "org.sucursal.leer" in effective.codes
    assert effective.source == "impersonation_effective_admin"


def _trial_admin_menu_response() -> MenuUsuarioResponse:
    return MenuUsuarioResponse(
        modulos=[
            ModuloMenuResponse(
                modulo_id=UUID("E1000001-0000-4000-8000-000000000001"),
                codigo="ORG",
                nombre="Organización",
                color="#1976D2",
                categoria="operaciones",
                orden=1,
            ),
            ModuloMenuResponse(
                modulo_id=UUID("E1000002-0000-4000-8000-000000000002"),
                codigo="INV",
                nombre="Inventarios",
                color="#4CAF50",
                categoria="operaciones",
                orden=2,
            ),
            ModuloMenuResponse(
                modulo_id=UUID("E1000003-0000-4000-8000-000000000003"),
                codigo="SYS_ADMIN",
                nombre="Administración",
                color="#9C27B0",
                categoria="administracion",
                orden=3,
            ),
        ]
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_menu_resolver_impersonation_preserves_modules_including_sys_admin():
    """Modelo A: menú impersonado = salida RMP sin filtro por prefijo de permiso."""
    tenant_cid = uuid4()
    service_menu = _trial_admin_menu_response()
    impersonation_payload = {
        "is_impersonation": True,
        "effective_scope": "tenant",
        "cliente_id": str(tenant_cid),
    }

    class FakeEffective:
        codes = ["org.empresa.leer", "inv.producto.leer", "admin.usuario.leer"]
        source = "impersonation_effective_admin"

    with patch(
        "app.core.authorization.menu_resolver.get_permission_resolver"
    ) as mock_get_resolver, patch.object(
        ModuloMenuService,
        "obtener_menu_impersonacion_tenant",
        new=AsyncMock(return_value=service_menu),
    ) as mock_imp_menu, patch(
        "app.core.authorization.menu_resolver.resolve_required_permissions_for_menu_tree",
        new=AsyncMock(return_value=None),
    ):
        resolver = mock_get_resolver.return_value
        resolver.get_effective_permissions = AsyncMock(return_value=FakeEffective())

        result = await get_menu_resolver().get_menu_for_user(
            usuario_id=uuid4(),
            cliente_id=tenant_cid,
            payload=impersonation_payload,
        )

    mock_imp_menu.assert_awaited_once()
    assert {m.codigo for m in result.modulos} == {"ORG", "INV", "SYS_ADMIN"}
    assert len(result.modulos) == 3


@pytest.mark.unit
def test_is_platform_operator_false_when_impersonating():
    assert is_platform_operator(
        payload={"is_impersonation": True, "user_type": "platform_admin"},
        user_type="platform_admin",
        is_super_admin=True,
    ) is False


@pytest.mark.unit
def test_require_super_admin_accepts_platform_admin_claim():
    """platform_admin + nivel 5 no debe caer en 403 por expectativa legacy super_admin."""
    from unittest.mock import MagicMock

    from app.core.authorization.rbac import require_super_admin

    user = MagicMock()
    user.nombre_usuario = "admin"
    user.is_super_admin = False
    user.user_type = "platform_admin"
    user.access_level = 5
    user.roles = []

    dep = require_super_admin()
    assert dep(current_user=user) is user


@pytest.mark.unit
def test_resolve_platform_superadmin_for_admin_platform_role():
    from uuid import UUID

    from app.core.auth.platform_user_lookup import resolve_platform_superadmin_flag
    from app.core.config import settings

    system_id = UUID(str(settings.SUPERADMIN_CLIENTE_ID))
    assert resolve_platform_superadmin_flag(
        username="admin",
        request_cliente_id=system_id,
        roles_result=[{"codigo_rol": "ADMIN_PLATFORM", "nivel_acceso": 5}],
        nivel_acceso=5,
        is_superadmin_from_roles=False,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_iniciar_impersonacion_rejects_nested():
    from app.modules.auth.application.services.impersonation_service import (
        ImpersonationService,
    )

    with pytest.raises(HTTPException) as exc:
        await ImpersonationService.iniciar_impersonacion(
            target_cliente_id=uuid4(),
            operator_usuario_id=uuid4(),
            operator_username="op",
            parent_access_token="parent",
            parent_refresh_token=None,
            parent_payload={"is_impersonation": True},
            ip_address=None,
            user_agent=None,
        )
    assert exc.value.status_code == 409
