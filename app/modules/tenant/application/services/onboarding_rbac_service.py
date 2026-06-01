"""

Bootstrap RBAC y módulos base al crear un tenant (reemplaza R010/R020 en runtime).



Usa únicamente la AsyncSession del onboarding (sin execute_query externo).

Fuente de permisos: tabla permiso poblada por permission_sync_service.

OwnerSyncService v1.0 sincroniza grants de módulo para ADMIN_TENANT.

"""

from __future__ import annotations



import logging

from typing import Any, Dict, List, Optional, Sequence

from uuid import UUID, uuid4



from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession



# Literal para evitar import circular (core_permissions → rbac → auth → tenant).
CORE_APP_ACCEDER = "core.app.acceder"

from app.core.exceptions import DatabaseError

from app.modules.tenant.application.services.owner_sync_constants import (

    ADMIN_ROL_CODIGO,

    EXCLUDED_GLOBAL_PERMISO_CODIGOS,

    TRIAL_MODULES,

)

from app.modules.tenant.application.services.base_operative_service import BaseOperativeService
from app.modules.tenant.application.services.manager_standard_service import (
    ManagerStandardService,
)
from app.modules.tenant.application.services.user_standard_service import (
    UserStandardService,
)
from app.modules.tenant.application.services.owner_sync_service import OwnerSyncService

from app.modules.tenant.application.services.plan_modulo_resolver import (

    resolve_modulos_for_plan,

)



logger = logging.getLogger(__name__)



# Compatibilidad tests / imports legacy

MODULOS_BASE: tuple[str, ...] = TRIAL_MODULES

EXCLUDED_PERMISO_CODIGOS = EXCLUDED_GLOBAL_PERMISO_CODIGOS





class OnboardingRbacService:

    """Activa módulos del plan y sincroniza RBAC owner (ADMIN_TENANT)."""



    @staticmethod

    async def bootstrap_cliente_rbac(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

        activado_por_usuario_id: Optional[UUID] = None,

        plan_suscripcion: Optional[str] = None,

    ) -> Dict[str, Any]:

        """

        Orquesta activación de módulos del plan, grants globales y OwnerSync por módulo.

        """

        await OnboardingRbacService._validar_catalogo_permiso(session)



        modulos_plan = resolve_modulos_for_plan(plan_suscripcion)

        modulos = await OnboardingRbacService.activar_modulos_base_cliente(

            session,

            cliente_id=cliente_id,

            activado_por_usuario_id=activado_por_usuario_id,

            modulos_codigo=modulos_plan,

        )

        global_grants = await OnboardingRbacService.bootstrap_global_grants_admin_tenant(

            session,

            cliente_id=cliente_id,

            admin_rol_id=admin_rol_id,

        )

        owner_sync = await OwnerSyncService.sync_modules_for_owner(

            session,

            cliente_id=cliente_id,

            modulos_codigo=modulos,

            admin_rol_id=admin_rol_id,

        )

        logger.info(

            "Onboarding RBAC cliente=%s modulos=%s global_rp_inserted=%s owner_rmp_inserted=%s",

            cliente_id,

            modulos,

            global_grants.get("inserted", 0),

            owner_sync.total_rol_menu_permiso_inserted,

        )

        base_operative = await BaseOperativeService.apply_to_operative_roles(

            session,

            cliente_id=cliente_id,

        )

        logger.info(

            "Onboarding BASE_OPERATIVE cliente=%s inserted=%s",

            cliente_id,

            base_operative.get("total_inserted", 0),

        )

        manager_standard = None
        try:
            manager_rol_id = await ManagerStandardService.resolve_manager_rol_id(
                session, cliente_id=cliente_id
            )
            if manager_rol_id:
                manager_standard = await ManagerStandardService.apply_to_manager_role(
                    session, cliente_id=cliente_id, manager_rol_id=manager_rol_id
                )
                logger.info(
                    "Onboarding MANAGER_STANDARD cliente=%s rp_inserted=%s rmp_inserted=%s",
                    cliente_id,
                    (manager_standard.get("rol_permiso") or {}).get("inserted", 0),
                    (manager_standard.get("rol_menu_permiso") or {}).get("inserted", 0),
                )
            else:
                logger.warning(
                    "Onboarding MANAGER_STANDARD: MANAGER_TENANT rol no encontrado cliente=%s",
                    cliente_id,
                )
        except Exception as e:
            logger.exception("Onboarding MANAGER_STANDARD error cliente=%s: %s", cliente_id, e)

        user_standard = None
        try:
            user_rol_id = await UserStandardService.resolve_user_rol_id(
                session, cliente_id=cliente_id
            )
            if user_rol_id:
                user_standard = await UserStandardService.apply_to_user_role(
                    session, cliente_id=cliente_id, user_rol_id=user_rol_id
                )
                logger.info(
                    "Onboarding USER_STANDARD cliente=%s rp_inserted=%s rmp_inserted=%s",
                    cliente_id,
                    (user_standard.get("rol_permiso") or {}).get("inserted", 0),
                    (user_standard.get("rol_menu_permiso") or {}).get("inserted", 0),
                )
            else:
                logger.warning(
                    "Onboarding USER_STANDARD: USER_TENANT rol no encontrado cliente=%s",
                    cliente_id,
                )
        except Exception as e:
            logger.exception("Onboarding USER_STANDARD error cliente=%s: %s", cliente_id, e)

        return {

            "modulos": modulos,

            "grants": global_grants,

            "owner_sync": owner_sync,

            "base_operative": base_operative,
            "manager_standard": manager_standard,
            "user_standard": user_standard,

        }



    @staticmethod

    async def _validar_catalogo_permiso(session: AsyncSession) -> None:

        """Requiere catálogo permiso (startup sync) antes de asignar rol_permiso."""

        sql = text("""

            SELECT COUNT(*) AS total

            FROM permiso

            WHERE es_activo = 1

        """)

        result = await session.execute(sql)

        row = result.fetchone()

        total = int(row[0] if row else 0)

        if total == 0:

            raise DatabaseError(

                detail=(

                    "Catálogo de permisos vacío. Arranque la aplicación al menos una vez "

                    "(permission_sync) antes de crear tenants."

                ),

                internal_code="ONBOARDING_PERMISSO_CATALOG_EMPTY",

            )



    @staticmethod

    async def activar_modulos_base_cliente(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        activado_por_usuario_id: Optional[UUID] = None,

        modulos_codigo: Sequence[str] = TRIAL_MODULES,

    ) -> List[str]:

        """Activa módulos en cliente_modulo (lookup por modulo.codigo, idempotente)."""

        codigos = [c.strip().upper() for c in modulos_codigo if c and c.strip()]

        if not codigos:

            return []



        placeholders = ", ".join(f":mc{i}" for i in range(len(codigos)))

        bind_modulos: Dict[str, Any] = {f"mc{i}": codigos[i] for i in range(len(codigos))}



        sql_modulos = text(f"""

            SELECT modulo_id, codigo

            FROM modulo

            WHERE codigo IN ({placeholders})

              AND es_activo = 1

        """).bindparams(**bind_modulos)

        result = await session.execute(sql_modulos)

        rows = result.fetchall()

        if not rows:

            raise DatabaseError(

                detail=(

                    f"No se encontraron módulos base ({', '.join(codigos)}). "

                    "Ejecute el seed de catálogo S010/S020 antes del onboarding."

                ),

                internal_code="ONBOARDING_MODULOS_BASE_NOT_FOUND",

            )



        found_codes: List[str] = []

        missing = set(codigos) - {str(r[1]).upper() for r in rows}

        if missing:

            raise DatabaseError(

                detail=f"Módulos no encontrados en catálogo: {', '.join(sorted(missing))}",

                internal_code="ONBOARDING_MODULO_MISSING",

            )



        for modulo_id, codigo in rows:

            mid = modulo_id if isinstance(modulo_id, UUID) else UUID(str(modulo_id))

            sql_insert = text("""

                IF NOT EXISTS (

                    SELECT 1 FROM cliente_modulo

                    WHERE cliente_id = :cliente_id AND modulo_id = :modulo_id

                )

                INSERT INTO cliente_modulo (

                    cliente_modulo_id, cliente_id, modulo_id,

                    esta_activo, fecha_activacion, activado_por_usuario_id

                )

                VALUES (

                    :cliente_modulo_id, :cliente_id, :modulo_id,

                    1, GETDATE(), :activado_por_usuario_id

                )

            """).bindparams(

                cliente_modulo_id=uuid4(),

                cliente_id=cliente_id,

                modulo_id=mid,

                activado_por_usuario_id=activado_por_usuario_id,

            )

            await session.execute(sql_insert)

            found_codes.append(str(codigo).upper())



        return found_codes



    @staticmethod

    async def bootstrap_global_grants_admin_tenant(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

    ) -> Dict[str, Any]:

        """

        Grants API globales (permiso.modulo_id IS NULL) para ADMIN_TENANT.

        Permisos de módulo (org.*, inv.*, …) los sincroniza OwnerSyncService.

        """

        sql_rol = text("""

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

        rol_row = (await session.execute(sql_rol)).fetchone()

        if not rol_row:

            raise DatabaseError(

                detail="Rol ADMIN_TENANT no encontrado para el cliente en onboarding.",

                internal_code="ONBOARDING_ADMIN_ROLE_NOT_FOUND",

            )



        sql_grant = text("""

            INSERT INTO rol_permiso (rol_permiso_id, cliente_id, rol_id, permiso_id, fecha_creacion)

            SELECT NEWID(), :cliente_id, :admin_rol_id, p.permiso_id, GETDATE()

            FROM permiso p

            WHERE p.es_activo = 1

              AND p.modulo_id IS NULL

              AND (

                    p.codigo = :core_app_acceder

                 OR p.codigo LIKE 'admin.%'

                 OR p.codigo LIKE 'modulos.%'

                 OR (

                        p.codigo LIKE 'tenant.%'

                    AND p.codigo <> :excluded_tenant_cliente_crear

                 )

              )

              AND NOT EXISTS (

                    SELECT 1 FROM rol_permiso rp

                    WHERE rp.cliente_id = :cliente_id

                      AND rp.rol_id = :admin_rol_id

                      AND rp.permiso_id = p.permiso_id

              )

        """).bindparams(

            cliente_id=cliente_id,

            admin_rol_id=admin_rol_id,

            core_app_acceder=CORE_APP_ACCEDER,

            excluded_tenant_cliente_crear="tenant.cliente.crear",

        )



        sql_count = text("""

            SELECT COUNT(*) FROM rol_permiso

            WHERE cliente_id = :cliente_id AND rol_id = :admin_rol_id

        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)



        before_row = (await session.execute(sql_count)).fetchone()

        count_before = int(before_row[0] if before_row else 0)



        await session.execute(sql_grant)



        after_row = (await session.execute(sql_count)).fetchone()

        count_after = int(after_row[0] if after_row else 0)

        inserted = max(0, count_after - count_before)



        sql_codes = text("""

            SELECT p.codigo

            FROM rol_permiso rp

            INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1

            WHERE rp.cliente_id = :cliente_id AND rp.rol_id = :admin_rol_id

            ORDER BY p.codigo

        """).bindparams(cliente_id=cliente_id, admin_rol_id=admin_rol_id)

        codes_rows = (await session.execute(sql_codes)).fetchall()

        codigos = [str(r[0]) for r in codes_rows]



        return {

            "inserted": inserted,

            "codigos": codigos,

            "has_modulos_menu_leer": "modulos.menu.leer" in codigos,

            "has_tenant_cliente_crear": "tenant.cliente.crear" in codigos,

        }



    @staticmethod

    async def asignar_permisos_admin_tenant(

        session: AsyncSession,

        *,

        cliente_id: UUID,

        admin_rol_id: UUID,

    ) -> Dict[str, Any]:

        """Alias legacy → bootstrap_global_grants_admin_tenant."""

        return await OnboardingRbacService.bootstrap_global_grants_admin_tenant(

            session,

            cliente_id=cliente_id,

            admin_rol_id=admin_rol_id,

        )


