"""T1 — BASE_OPERATIVE bundle for MANAGER_TENANT / USER_TENANT."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.authorization.core_permissions import CORE_APP_ACCEDER
from app.modules.tenant.application.services.base_operative_constants import (
    BASE_OPERATIVE_PERMISSION_CODIGOS,
    MANAGER_ROL_CODIGO,
    OPERATIVE_ROLE_CODIGOS,
    USER_ROL_CODIGO,
)
from app.modules.tenant.application.services.base_operative_service import BaseOperativeService


def _mock_result(rows=None, scalar=None):
    result = MagicMock()
    if scalar is not None:
        result.fetchone.return_value = (scalar,)
    else:
        result.fetchall.return_value = rows or []
    return result


@pytest.mark.asyncio
async def test_constants_bundle_three_permissions():
    assert len(BASE_OPERATIVE_PERMISSION_CODIGOS) == 3
    assert CORE_APP_ACCEDER in BASE_OPERATIVE_PERMISSION_CODIGOS
    assert "tenant.branding.leer" in BASE_OPERATIVE_PERMISSION_CODIGOS
    assert "org.empresa.leer" in BASE_OPERATIVE_PERMISSION_CODIGOS
    assert OPERATIVE_ROLE_CODIGOS == (MANAGER_ROL_CODIGO, USER_ROL_CODIGO)


@pytest.mark.asyncio
async def test_apply_to_role_idempotent_when_complete():
    session = AsyncMock()
    cliente_id = uuid4()
    rol_id = uuid4()

    session.execute = AsyncMock(
        side_effect=[
            _mock_result(scalar=3),
            _mock_result(
                rows=[
                    (CORE_APP_ACCEDER,),
                    ("tenant.branding.leer",),
                    ("org.empresa.leer",),
                ]
            ),
            _mock_result(scalar=3),
            _mock_result(
                rows=[
                    (CORE_APP_ACCEDER,),
                    ("tenant.branding.leer",),
                    ("org.empresa.leer",),
                ]
            ),
        ]
    )

    result = await BaseOperativeService.apply_to_role(
        session,
        cliente_id=cliente_id,
        rol_id=rol_id,
        codigo_rol=MANAGER_ROL_CODIGO,
    )

    assert result["inserted"] == 0
    assert result["complete"] is True
    assert result["codigos_missing"] == []
    assert session.execute.await_count == 4


@pytest.mark.asyncio
async def test_apply_to_role_inserts_missing_grants():
    session = AsyncMock()
    cliente_id = uuid4()
    rol_id = uuid4()

    session.execute = AsyncMock(
        side_effect=[
            _mock_result(scalar=0),
            _mock_result(rows=[]),
            _mock_result(rows=[(CORE_APP_ACCEDER,), ("tenant.branding.leer",), ("org.empresa.leer",)]),
            MagicMock(),
            _mock_result(scalar=3),
            _mock_result(
                rows=[
                    (CORE_APP_ACCEDER,),
                    ("tenant.branding.leer",),
                    ("org.empresa.leer",),
                ]
            ),
        ]
    )

    result = await BaseOperativeService.apply_to_role(
        session,
        cliente_id=cliente_id,
        rol_id=rol_id,
        codigo_rol=USER_ROL_CODIGO,
    )

    assert result["inserted"] == 3
    assert result["complete"] is True
    insert_sql = str(session.execute.await_args_list[3][0][0])
    assert "INSERT INTO rol_permiso" in insert_sql


@pytest.mark.asyncio
async def test_apply_to_operative_roles_both_system_roles():
    session = AsyncMock()
    cliente_id = uuid4()
    manager_id = uuid4()
    user_id = uuid4()

    async def _apply_side_effect(session, *, cliente_id, rol_id, codigo_rol=None):
        return {
            "codigo_rol": codigo_rol,
            "rol_id": str(rol_id),
            "inserted": 3,
            "complete": True,
            "codigos_present": list(BASE_OPERATIVE_PERMISSION_CODIGOS),
            "codigos_missing": [],
            "total_base_grants": 3,
        }

    with patch.object(
        BaseOperativeService,
        "_resolve_rol_id",
        new=AsyncMock(side_effect=[manager_id, user_id]),
    ), patch.object(
        BaseOperativeService,
        "apply_to_role",
        new=AsyncMock(side_effect=_apply_side_effect),
    ):
        out = await BaseOperativeService.apply_to_operative_roles(
            session, cliente_id=cliente_id
        )

    assert out["total_inserted"] == 6
    assert len(out["roles"]) == 2
    assert out["roles"][0]["codigo_rol"] == MANAGER_ROL_CODIGO
    assert out["roles"][1]["codigo_rol"] == USER_ROL_CODIGO


@pytest.mark.asyncio
async def test_ensure_for_operative_role_skips_admin():
    result = await BaseOperativeService.ensure_for_operative_role(
        uuid4(), uuid4(), "ADMIN_TENANT"
    )
    assert result is None


@pytest.mark.asyncio
async def test_ensure_for_operative_role_applies_manager():
    cliente_id = uuid4()
    rol_id = uuid4()
    expected = {"inserted": 3, "complete": True}

    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        return_value=mock_cm,
    ), patch.object(
        BaseOperativeService,
        "apply_to_role",
        new=AsyncMock(return_value=expected),
    ), patch.object(
        BaseOperativeService,
        "_invalidate_tenant_cache",
    ) as mock_inv:
        out = await BaseOperativeService.ensure_for_operative_role(
            cliente_id, rol_id, MANAGER_ROL_CODIGO
        )

    assert out == expected
    mock_session.commit.assert_awaited_once()
    mock_inv.assert_called_once_with(cliente_id)


@pytest.mark.asyncio
async def test_bootstrap_cliente_rbac_includes_base_operative():
    from app.modules.tenant.application.services.onboarding_rbac_service import (
        OnboardingRbacService,
    )
    from app.modules.tenant.application.services.owner_sync_result import (
        OwnerSyncBatchResult,
        OwnerSyncResult,
    )

    session = AsyncMock()
    cliente_id = uuid4()
    admin_rol_id = uuid4()
    org_id = uuid4()
    sys_id = uuid4()
    inv_id = uuid4()

    owner_batch = OwnerSyncBatchResult(
        cliente_id=cliente_id,
        results=[
            OwnerSyncResult(
                cliente_id=cliente_id,
                modulo_codigo="ORG",
                admin_rol_id=admin_rol_id,
                rol_permiso_inserted=1,
                rol_permiso_total_module=1,
                rol_menu_permiso_inserted=6,
                rol_menu_permiso_total_module=6,
            ),
        ],
    )

    base_payload = {
        "cliente_id": str(cliente_id),
        "total_inserted": 6,
        "roles": [],
        "expected_codigos": list(BASE_OPERATIVE_PERMISSION_CODIGOS),
    }

    session.execute = AsyncMock(
        side_effect=[
            _mock_result(scalar=50),
            _mock_result(rows=[(org_id, "ORG"), (sys_id, "SYS_ADMIN"), (inv_id, "INV")]),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            _mock_result(rows=[(admin_rol_id,)]),
            _mock_result(scalar=0),
            MagicMock(),
            _mock_result(scalar=2),
            _mock_result(rows=[(CORE_APP_ACCEDER,), ("modulos.menu.leer",)]),
        ]
    )

    with patch(
        "app.modules.tenant.application.services.onboarding_rbac_service.OwnerSyncService.sync_modules_for_owner",
        new=AsyncMock(return_value=owner_batch),
    ), patch(
        "app.modules.tenant.application.services.onboarding_rbac_service.BaseOperativeService.apply_to_operative_roles",
        new=AsyncMock(return_value=base_payload),
    ) as mock_base:
        result = await OnboardingRbacService.bootstrap_cliente_rbac(
            session,
            cliente_id=cliente_id,
            admin_rol_id=admin_rol_id,
            activado_por_usuario_id=uuid4(),
            plan_suscripcion="trial",
        )

    mock_base.assert_awaited_once_with(session, cliente_id=cliente_id)
    assert result["base_operative"] == base_payload


@pytest.mark.asyncio
async def test_asignar_rol_triggers_base_operative_for_manager():
    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()
    rol_id = uuid4()

    usuario = {"usuario_id": usuario_id, "nombre_usuario": "mgr1"}
    rol = {"rol_id": rol_id, "es_activo": True, "codigo_rol": MANAGER_ROL_CODIGO}
    assignment_row = {
        "usuario_rol_id": uuid4(),
        "es_activo": True,
        "empresa_id": uuid4(),
    }

    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new=AsyncMock(return_value=usuario),
    ), patch(
        "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
        new=AsyncMock(return_value=rol),
    ), patch(
        "app.modules.users.application.services.user_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [assignment_row],
                [{"usuario_rol_id": assignment_row["usuario_rol_id"]}],
            ]
        ),
    ), patch.object(
        UsuarioService,
        "_validate_assign_scope_conflict",
    ), patch.object(
        UsuarioService,
        "_ensure_base_operative_for_operative_role",
        new=AsyncMock(),
    ) as mock_base, patch.object(
        UsuarioService,
        "_maybe_set_empresa_default_after_role_assign",
        new=AsyncMock(),
    ):
        await UsuarioService.asignar_rol_a_usuario(
            cliente_id,
            usuario_id,
            rol_id,
            target_empresa_id=assignment_row["empresa_id"],
        )

    mock_base.assert_awaited_once_with(cliente_id, rol_id, MANAGER_ROL_CODIGO)
