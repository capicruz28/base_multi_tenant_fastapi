"""

Bootstrap rol_menu_permiso — delegado a OwnerSyncService v1.0.

"""

from __future__ import annotations



from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4



import pytest



from app.core.exceptions import DatabaseError

from app.modules.tenant.application.services.onboarding_menu_bootstrap_service import (

    MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS,

    OnboardingMenuBootstrapService,

)

from app.modules.tenant.application.services.owner_sync_constants import (

    MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS,

)

from app.modules.tenant.application.services.owner_sync_result import (

    OwnerSyncBatchResult,

    OwnerSyncResult,

)





def _mock_scalar(value):

    result = MagicMock()

    result.fetchone.return_value = (value,)

    return result





def _mock_rows(rows):

    result = MagicMock()

    result.fetchall.return_value = rows

    return result





@pytest.mark.asyncio

async def test_bootstrap_admin_menu_grants_delegates_owner_sync():

    session = AsyncMock()

    cliente_id = uuid4()

    admin_rol_id = uuid4()



    batch = OwnerSyncBatchResult(

        cliente_id=cliente_id,

        results=[

            OwnerSyncResult(

                cliente_id=cliente_id,

                modulo_codigo="INV",

                admin_rol_id=admin_rol_id,

                rol_permiso_inserted=1,

                rol_permiso_total_module=1,

                rol_menu_permiso_inserted=9,

                rol_menu_permiso_total_module=9,

            ),

        ],

    )



    session.execute = AsyncMock(

        side_effect=[

            _mock_scalar(admin_rol_id),

            _mock_scalar(18),

            _mock_rows([("INV_PRODUCTOS",)]),

        ]

    )



    with patch(

        "app.modules.tenant.application.services.onboarding_menu_bootstrap_service.OwnerSyncService.sync_modules_for_owner",

        new=AsyncMock(return_value=batch),

    ) as mock_sync, patch(

        "app.modules.tenant.application.services.onboarding_menu_bootstrap_service.OwnerSyncService.count_expected_owner_menu_grants",

        new=AsyncMock(return_value=18),

    ):

        out = await OnboardingMenuBootstrapService.bootstrap_admin_menu_grants(

            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id

        )



    mock_sync.assert_awaited_once()

    assert out["inserted"] == 9

    assert out["pruned"] == 0

    assert out["total_rol_menu_permiso"] == 18

    assert out["expected_menu_grants"] == 18

    assert MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS == MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS == 18





@pytest.mark.asyncio

async def test_bootstrap_admin_menu_grants_missing_role():

    session = AsyncMock()

    missing = MagicMock()

    missing.fetchone.return_value = None

    session.execute = AsyncMock(return_value=missing)



    with pytest.raises(DatabaseError) as exc:

        await OnboardingMenuBootstrapService.bootstrap_admin_menu_grants(

            session, cliente_id=uuid4(), admin_rol_id=uuid4()

        )



    assert exc.value.internal_code == "ONBOARDING_MENU_ADMIN_ROLE_NOT_FOUND"


