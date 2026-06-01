"""

Bootstrap de rol_menu_permiso — delegado a OwnerSyncService v1.0.



Mantiene API legacy para repair_tenant_menu_grants.py (deprecated, M3).

"""

from __future__ import annotations



import logging

from typing import Any, Dict, List, Optional, Sequence

from uuid import UUID



from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession



from app.core.exceptions import DatabaseError

from app.modules.tenant.application.services.owner_sync_constants import (

    ADMIN_ROL_CODIGO,

    MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS,

    TRIAL_MODULES,

)

from app.modules.tenant.application.services.owner_sync_service import OwnerSyncService

from app.modules.tenant.application.services.plan_modulo_resolver import (

    resolve_modulos_for_plan,

)



logger = logging.getLogger(__name__)



MODULOS_MENU_BASE: tuple[str, ...] = TRIAL_MODULES

MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS = MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS



# Legacy repair scope SQL (deprecated — no usar prune comercial post-Owner)

TENANT_ADMIN_MENU_SCOPE_SQL = """

  AND (

        m.codigo = 'ORG'

        OR (m.codigo = 'SYS_ADMIN' AND mm.codigo LIKE 'SYS_ADMIN.TENANT.%')

  )

  AND (mm.codigo IS NULL OR (

        mm.codigo NOT LIKE 'SYS_ADMIN.PLATFORM.%'

    AND mm.codigo NOT LIKE 'SYS_ADMIN.CATALOGOS.%'

  ))

"""





class OnboardingMenuBootstrapService:

    """Delega grants UI a OwnerSyncService (sin prune destructivo)."""



    @staticmethod

    async def bootstrap_admin_menu_grants(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

        modulos_codigo: Sequence[str] = MODULOS_MENU_BASE,

    ) -> Dict[str, Any]:

        """

        Sincroniza rol_menu_permiso vía OwnerSync (idempotente, sin prune comercial).

        """

        await OnboardingMenuBootstrapService._validar_rol_admin(

            session, cliente_id=cliente_id, admin_rol_id=admin_rol_id

        )



        codigos = [c.strip().upper() for c in modulos_codigo if c and c.strip()]

        if not codigos:

            codigos = resolve_modulos_for_plan("trial")



        batch = await OwnerSyncService.sync_modules_for_owner(

            session,

            cliente_id=cliente_id,

            modulos_codigo=codigos,

            admin_rol_id=admin_rol_id,

        )



        sql_count = text("""

            SELECT COUNT(*) AS total

            FROM rol_menu_permiso

            WHERE cliente_id = :cliente_id AND rol_id = :admin_rol_id

        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)

        count_after = int((await session.execute(sql_count)).fetchone()[0])



        expected = await OwnerSyncService.count_expected_owner_menu_grants(

            session, cliente_id=cliente_id

        )

        menu_codes = await OnboardingMenuBootstrapService._list_granted_menu_codes(

            session,

            cliente_id=cliente_id,

            admin_rol_id=admin_rol_id,

        )



        inserted = batch.total_rol_menu_permiso_inserted

        logger.info(

            "Onboarding menu (OwnerSync) cliente=%s inserted=%s total=%s expected=%s",

            cliente_id,

            inserted,

            count_after,

            expected,

        )



        return {

            "inserted": inserted,

            "pruned": 0,

            "skipped_existing": max(0, count_after - inserted),

            "total_rol_menu_permiso": count_after,

            "expected_menu_grants": expected,

            "modulos": list(codigos),

            "menu_codigos_sample": menu_codes[:20],

            "menu_codigos_count": len(menu_codes),

        }



    @staticmethod

    async def prune_invalid_admin_menu_grants(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

    ) -> int:

        """

        Deprecated: solo elimina grants PLATFORM/CATALOGOS erróneos, nunca módulos comerciales.

        """

        sql = text("""

            DELETE rmp

            FROM rol_menu_permiso rmp

            INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id

            WHERE rmp.cliente_id = :cliente_id

              AND rmp.rol_id = :admin_rol_id

              AND rmp.empresa_id IS NULL

              AND (

                    mm.codigo LIKE 'SYS_ADMIN.PLATFORM.%'

                 OR mm.codigo LIKE 'SYS_ADMIN.CATALOGOS.%'

              )

        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)

        result = await session.execute(sql)

        return int(getattr(result, "rowcount", 0) or 0)



    @staticmethod

    async def count_expected_tenant_admin_menus(

        session: AsyncSession,

        *,

        cliente_id: UUID,

    ) -> int:

        return await OwnerSyncService.count_expected_owner_menu_grants(

            session, cliente_id=cliente_id

        )



    @staticmethod

    async def _validar_rol_admin(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

    ) -> None:

        sql = text("""

            SELECT rol_id FROM rol

            WHERE rol_id = :admin_rol_id

              AND cliente_id = :cliente_id

              AND codigo_rol = :codigo_rol

              AND es_activo = 1

        """).bindparams(

            admin_rol_id=admin_rol_id,

            cliente_id=cliente_id,

            codigo_rol=ADMIN_ROL_CODIGO,

        )

        row = (await session.execute(sql)).fetchone()

        if not row:

            raise DatabaseError(

                detail="Rol ADMIN_TENANT no encontrado para bootstrap de menú.",

                internal_code="ONBOARDING_MENU_ADMIN_ROLE_NOT_FOUND",

            )



    @staticmethod

    async def _list_granted_menu_codes(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

    ) -> List[str]:

        sql = text("""

            SELECT DISTINCT mm.codigo

            FROM rol_menu_permiso rmp

            INNER JOIN modulo_menu mm ON mm.menu_id = rmp.menu_id

            INNER JOIN modulo m ON m.modulo_id = mm.modulo_id

            INNER JOIN cliente_modulo cm ON cm.modulo_id = m.modulo_id

                AND cm.cliente_id = :cliente_id AND cm.esta_activo = 1

            WHERE rmp.cliente_id = :cliente_id

              AND rmp.rol_id = :admin_rol_id

              AND rmp.puede_ver = 1

              AND (

                    m.codigo <> 'SYS_ADMIN'

                    OR (

                        mm.codigo LIKE 'SYS_ADMIN.TENANT.%'

                        AND mm.codigo NOT LIKE 'SYS_ADMIN.PLATFORM.%'

                        AND mm.codigo NOT LIKE 'SYS_ADMIN.CATALOGOS.%'

                    )

              )

            ORDER BY mm.codigo

        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)

        rows = (await session.execute(sql)).fetchall()

        return [str(r[0]) for r in rows if r and r[0]]


