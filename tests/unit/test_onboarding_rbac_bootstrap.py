"""

Fase 4 + OwnerSync: bootstrap RBAC en onboarding (cliente_modulo, rol_permiso, OwnerSync).

"""

from __future__ import annotations



from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4



import pytest



from app.core.authorization.core_permissions import CORE_APP_ACCEDER

from app.modules.tenant.application.services.onboarding_rbac_service import (

    EXCLUDED_PERMISO_CODIGOS,

    OnboardingRbacService,

)

from app.modules.tenant.application.services.owner_sync_result import (

    OwnerSyncBatchResult,

    OwnerSyncResult,

)





def _mock_result(rows=None, scalar=None):

    result = MagicMock()

    if scalar is not None:

        result.fetchone.return_value = (scalar,)

    else:

        result.fetchall.return_value = rows or []

    return result





@pytest.mark.asyncio

async def test_activar_modulos_base_cliente_idempotent():

    session = AsyncMock()

    cliente_id = uuid4()

    org_id = uuid4()

    sys_id = uuid4()

    inv_id = uuid4()



    session.execute = AsyncMock(

        side_effect=[

            _mock_result(rows=[(org_id, "ORG"), (sys_id, "SYS_ADMIN"), (inv_id, "INV")]),

            MagicMock(),

            MagicMock(),

            MagicMock(),

        ]

    )



    codes = await OnboardingRbacService.activar_modulos_base_cliente(

        session, cliente_id=cliente_id, activado_por_usuario_id=uuid4()

    )



    assert codes == ["ORG", "SYS_ADMIN", "INV"]

    assert session.execute.await_count == 4





@pytest.mark.asyncio

async def test_bootstrap_global_grants_excludes_org_prefix():

    session = AsyncMock()

    cliente_id = uuid4()

    admin_rol_id = uuid4()



    session.execute = AsyncMock(

        side_effect=[

            _mock_result(rows=[(admin_rol_id,)]),

            _mock_result(scalar=0),

            MagicMock(),

            _mock_result(scalar=3),

            _mock_result(rows=[(CORE_APP_ACCEDER,), ("modulos.menu.leer",)]),

        ]

    )



    grants = await OnboardingRbacService.bootstrap_global_grants_admin_tenant(

        session, cliente_id=cliente_id, admin_rol_id=admin_rol_id

    )



    assert grants["inserted"] == 3

    assert "tenant.cliente.crear" not in grants["codigos"]

    assert "tenant.cliente.crear" in EXCLUDED_PERMISO_CODIGOS



    grant_sql = str(session.execute.await_args_list[2][0][0])

    assert "INSERT INTO rol_permiso" in grant_sql

    assert "p.modulo_id IS NULL" in grant_sql

    assert "org." not in grant_sql





@pytest.mark.asyncio

async def test_bootstrap_fails_when_permiso_catalog_empty():

    session = AsyncMock()

    session.execute = AsyncMock(return_value=_mock_result(scalar=0))



    with pytest.raises(Exception) as exc:

        await OnboardingRbacService.bootstrap_cliente_rbac(

            session,

            cliente_id=uuid4(),

            admin_rol_id=uuid4(),

        )



    assert getattr(exc.value, "internal_code", None) == "ONBOARDING_PERMISSO_CATALOG_EMPTY"





@pytest.mark.asyncio

async def test_bootstrap_orchestrates_modulos_owner_sync():

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

    ) as mock_sync, patch(

        "app.modules.tenant.application.services.onboarding_rbac_service.BaseOperativeService.apply_to_operative_roles",

        new=AsyncMock(return_value={"total_inserted": 6, "roles": []}),

    ):

        result = await OnboardingRbacService.bootstrap_cliente_rbac(

            session,

            cliente_id=cliente_id,

            admin_rol_id=admin_rol_id,

            activado_por_usuario_id=uuid4(),

            plan_suscripcion="trial",

        )



    assert result["modulos"] == ["ORG", "SYS_ADMIN", "INV"]

    assert result["grants"]["has_modulos_menu_leer"] is True

    mock_sync.assert_awaited_once()


