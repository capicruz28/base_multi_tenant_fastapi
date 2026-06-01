"""
I2.1 integración: propagación empresa_id en menú y coherencia con Permission Resolver.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.authorization.menu_resolver import get_menu_resolver
from app.core.authorization.rbac import has_permission
from app.core.tenant.company_scope import resolve_empresa_id_for_rbac
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse

CLIENT_ID = uuid4()
USER_ID = uuid4()
EMPRESA_A = uuid4()
EMPRESA_B = uuid4()


def _jwt_payload(empresa_id) -> Dict[str, Any]:
    p: Dict[str, Any] = {
        "sub": "menu_user",
        "cliente_id": str(CLIENT_ID),
        "access_level": 2,
        "type": "access",
    }
    if empresa_id is not None:
        p["empresa_id"] = str(empresa_id)
    return p


@pytest.mark.integration
@pytest.mark.asyncio
async def test_menu_resolver_passes_empresa_id_to_modulo_menu_service():
    captured: Dict[str, Any] = {}

    async def fake_obtener_menu_usuario(**kwargs):
        captured.update(kwargs)
        return MenuUsuarioResponse(modulos=[])

    class FakeEffective:
        codes = ["inv.producto.leer"]

    with patch(
        "app.core.authorization.menu_resolver.get_permission_resolver"
    ) as mock_get_resolver:
        resolver = MagicMock()
        resolver.get_effective_permissions = AsyncMock(return_value=FakeEffective())
        mock_get_resolver.return_value = resolver
        with patch.object(
            ModuloMenuService,
            "obtener_menu_usuario",
            new=AsyncMock(side_effect=fake_obtener_menu_usuario),
        ):
            menu_resolver = get_menu_resolver()
            await menu_resolver.get_menu_for_user(
                usuario_id=USER_ID,
                cliente_id=CLIENT_ID,
                empresa_id=EMPRESA_A,
            )

    assert captured.get("empresa_id") == EMPRESA_A
    resolver.get_effective_permissions.assert_awaited_once()
    assert resolver.get_effective_permissions.await_args.kwargs.get("empresa_id") == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_modulos_menus_me_resolves_empresa_from_context():
    captured: Dict[str, Any] = {}

    async def fake_obtener_menu_usuario(**kwargs):
        captured.update(kwargs)
        return MenuUsuarioResponse(modulos=[])

    mock_user = MagicMock()
    mock_user.usuario_id = USER_ID
    mock_user.cliente_id = CLIENT_ID
    mock_user.is_super_admin = False
    mock_user.access_level = 2
    mock_user.permisos = ["inv.producto.leer"]

    from app.modules.modulos.presentation.endpoints_menus import obtener_mi_menu

    with patch(
        "app.modules.modulos.presentation.endpoints_menus.ModuloMenuService.obtener_menu_usuario",
        new=AsyncMock(side_effect=fake_obtener_menu_usuario),
    ), patch(
        "app.core.tenant.company_scope.try_get_current_empresa_id",
        return_value=EMPRESA_A,
    ):
        await obtener_mi_menu(current_user=mock_user)

    assert captured.get("empresa_id") == EMPRESA_A


@pytest.mark.integration
@pytest.mark.asyncio
async def test_permissions_and_menu_use_same_empresa_resolution():
    """Misma empresa resuelta → resolver y menú reciben el mismo UUID."""
    from app.core.tenant import empresa_context

    token = empresa_context.set_current_empresa_id(EMPRESA_A)
    try:
        payload = _jwt_payload(EMPRESA_A)
        empresa_rbac = resolve_empresa_id_for_rbac(payload=payload)
        assert empresa_rbac == EMPRESA_A

        perm_captured: Dict[str, Any] = {}
        menu_captured: Dict[str, Any] = {}

        class FakeEffective:
            codes = ["inv.producto.leer", "inv.producto.crear"]

        async def fake_permissions(**kwargs):
            perm_captured.update(kwargs)
            return FakeEffective()

        async def fake_menu(**kwargs):
            menu_captured.update(kwargs)
            return MenuUsuarioResponse(modulos=[])

        with patch(
            "app.core.authorization.menu_resolver.get_permission_resolver"
        ) as mock_get_resolver:
            resolver = MagicMock()
            resolver.get_effective_permissions = AsyncMock(side_effect=fake_permissions)
            mock_get_resolver.return_value = resolver
            with patch.object(
                ModuloMenuService,
                "obtener_menu_usuario",
                new=AsyncMock(side_effect=fake_menu),
            ):
                await get_menu_resolver().get_menu_for_user(
                    usuario_id=USER_ID,
                    cliente_id=CLIENT_ID,
                    empresa_id=empresa_rbac,
                )

        assert perm_captured.get("empresa_id") == EMPRESA_A
        assert menu_captured.get("empresa_id") == EMPRESA_A
    finally:
        empresa_context.reset_current_empresa_id(token)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_require_permission_aligns_with_resolver_codes_for_session():
    """user.permisos (build) y resolver deben compartir códigos para la misma empresa."""
    mock_user = MagicMock()
    mock_user.nombre_usuario = "u1"
    mock_user.is_super_admin = False
    mock_user.permisos = ["inv.producto.leer"]

    assert has_permission(mock_user, "inv.producto.leer") is True
    assert has_permission(mock_user, "inv.producto.crear") is False

    class FakeEffective:
        codes = ["inv.producto.leer"]

    with patch(
        "app.core.authorization.permission_resolver.PermissionResolverService.get_effective_permissions",
        new=AsyncMock(return_value=FakeEffective()),
    ):
        from app.core.authorization.permission_resolver import get_permission_resolver

        effective = await get_permission_resolver().get_effective_permissions(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
            empresa_id=EMPRESA_A,
        )

    assert set(effective.codes) == set(mock_user.permisos)


@pytest.mark.integration
def test_resolve_empresa_for_rbac_context_over_jwt_when_both_set():
    from app.core.tenant import empresa_context

    token = empresa_context.set_current_empresa_id(EMPRESA_B)
    try:
        resolved = resolve_empresa_id_for_rbac(payload=_jwt_payload(EMPRESA_A))
        assert resolved == EMPRESA_B
    finally:
        empresa_context.reset_current_empresa_id(token)
