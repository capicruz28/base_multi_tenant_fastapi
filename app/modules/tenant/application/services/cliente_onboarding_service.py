"""
Onboarding transaccional al crear un cliente nuevo.

Inserta cliente + roles base + usuario admin + usuario_rol + cliente_auth_config
+ cfg_codigo_secuencia en una sola transacción (rollback completo si falla).
"""
from __future__ import annotations

import logging
import secrets
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.application.base_service import BaseService
from app.core.exceptions import DatabaseError, ServiceError
from app.core.security.password import get_password_hash
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    MinimalErpTenantBootstrapService,
)
from app.modules.tenant.application.services.onboarding_rbac_service import (
    OnboardingRbacService,
)
from app.modules.tenant.presentation.schemas import (
    ClienteCreate,
    ClienteRead,
    CredencialesInicialesRead,
)
from app.shared.validators import sanitize_person_name

logger = logging.getLogger(__name__)

ROLES_BASE: List[Dict[str, Any]] = [
    {
        "codigo_rol": "ADMIN_TENANT",
        "nombre": "Administrador",
        "descripcion": "Rol de administrador del tenant",
        "es_rol_sistema": True,
        "nivel_acceso": 5,
        "es_admin_cliente": True,
    },
    {
        "codigo_rol": "MANAGER_TENANT",
        "nombre": "Supervisor",
        "descripcion": "Rol de supervisor",
        "es_rol_sistema": True,
        "nivel_acceso": 3,
        "es_admin_cliente": False,
    },
    {
        "codigo_rol": "USER_TENANT",
        "nombre": "Usuario",
        "descripcion": "Rol de usuario estándar",
        "es_rol_sistema": True,
        "nivel_acceso": 1,
        "es_admin_cliente": False,
    },
]

SECUENCIAS_CODIGO: List[Tuple[str, str, int, str, int]] = [
    ("org_empresa", "EMP", 3, "", 0),
    ("org_sucursal", "SUC", 3, "", 0),
    ("org_departamento", "DEP", 3, "", 0),
    ("org_cargo", "CAR", 3, "", 0),
    ("org_centro_costo", "CC", 3, "", 0),
    ("inv_almacen", "ALM", 3, "", 0),
    ("inv_producto", "P", 5, "", 0),
    ("inv_categoria", "CAT", 3, "", 0),
    ("inv_movimiento", "MOV", 6, "", 0),
]

ADMIN_USERNAME = "admin"
MENSAJE_CREACION_EXITOSA = (
    "Cliente creado exitosamente. Guarde las credenciales, no se volverán a mostrar."
)


@dataclass
class ClienteOnboardingResult:
    cliente: ClienteRead
    credenciales: CredencialesInicialesRead


def _generar_contrasena_segura(length: int = 12) -> str:
    """12 caracteres: mayúsculas, minúsculas, números y al menos 1 especial."""
    if length < 4:
        raise ValueError("La longitud mínima de contraseña es 4")
    minus = string.ascii_lowercase
    mayus = string.ascii_uppercase
    digitos = string.digits
    especiales = "!@#$%&*"
    chars = [
        secrets.choice(mayus),
        secrets.choice(minus),
        secrets.choice(digitos),
        secrets.choice(especiales),
    ]
    pool = minus + mayus + digitos + especiales
    chars.extend(secrets.choice(pool) for _ in range(length - 4))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _row_to_dict(row, keys) -> Dict[str, Any]:
    if row is None:
        return {}
    return dict(zip(keys, row))


class ClienteOnboardingService:
    """Seed inicial de tenant en BD central (ADMIN)."""

    @staticmethod
    @BaseService.handle_service_errors
    async def crear_cliente_con_onboarding(cliente_data: ClienteCreate) -> ClienteOnboardingResult:
        contrasena_plana = _generar_contrasena_segura(12)
        contrasena_hash = get_password_hash(contrasena_plana)

        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            async with session.begin():
                cliente_row = await ClienteOnboardingService._insertar_cliente(
                    session, cliente_data
                )
                cliente_id = cliente_row["cliente_id"]

                roles_ids = await ClienteOnboardingService._insertar_roles_base(
                    session, cliente_id
                )
                admin_rol_id = roles_ids["ADMIN_TENANT"]

                erp_seed = await MinimalErpTenantBootstrapService.ensure_empresa_inicial(
                    session,
                    cliente_id=cliente_id,
                    cliente_data=cliente_data,
                )
                empresa_id = UUID(str(erp_seed["empresa_id"]))

                usuario_id = await ClienteOnboardingService._insertar_usuario_admin(
                    session,
                    cliente_id=cliente_id,
                    cliente_data=cliente_data,
                    contrasena_hash=contrasena_hash,
                    admin_rol_id=admin_rol_id,
                    empresa_id=empresa_id,
                )
                await MinimalErpTenantBootstrapService.vincular_admin_empresa(
                    session,
                    cliente_id=cliente_id,
                    usuario_id=usuario_id,
                    admin_rol_id=admin_rol_id,
                    empresa_id=empresa_id,
                )
                await OnboardingRbacService.bootstrap_cliente_rbac(
                    session,
                    cliente_id=cliente_id,
                    admin_rol_id=admin_rol_id,
                    activado_por_usuario_id=usuario_id,
                    plan_suscripcion=cliente_data.plan_suscripcion,
                )
                await ClienteOnboardingService._insertar_auth_config_si_no_existe(
                    session, cliente_id
                )
                await ClienteOnboardingService._insertar_secuencias_codigo(
                    session, cliente_id
                )

        cliente = ClienteRead(**cliente_row)
        credenciales = CredencialesInicialesRead(
            nombre_usuario=ADMIN_USERNAME,
            contrasena=contrasena_plana,
            requiere_cambio=True,
        )
        try:
            from app.core.authorization.permission_resolver import get_permission_resolver

            get_permission_resolver().invalidate_for_tenant(cliente_id)
        except Exception as inv:
            logger.debug("Permission cache invalidation post-onboarding (no bloqueante): %s", inv)

        logger.info(
            "Onboarding completado para cliente %s (%s)",
            cliente_id,
            cliente_data.subdominio,
        )
        return ClienteOnboardingResult(cliente=cliente, credenciales=credenciales)

    @staticmethod
    async def _insertar_cliente(
        session: AsyncSession, cliente_data: ClienteCreate
    ) -> Dict[str, Any]:
        fields = [
            "codigo_cliente",
            "subdominio",
            "razon_social",
            "nombre_comercial",
            "ruc",
            "tipo_instalacion",
            "servidor_api_local",
            "modo_autenticacion",
            "logo_url",
            "favicon_url",
            "color_primario",
            "color_secundario",
            "tema_personalizado",
            "plan_suscripcion",
            "estado_suscripcion",
            "fecha_inicio_suscripcion",
            "fecha_fin_trial",
            "contacto_nombre",
            "contacto_email",
            "contacto_telefono",
            "es_activo",
            "es_demo",
            "metadata_json",
            "api_key_sincronizacion",
            "sincronizacion_habilitada",
            "ultima_sincronizacion",
        ]
        placeholders = ", ".join(f":{f}" for f in fields)
        bind = {field: getattr(cliente_data, field) for field in fields}

        sql = text(f"""
            INSERT INTO cliente ({", ".join(fields)})
            OUTPUT
                INSERTED.cliente_id,
                INSERTED.codigo_cliente,
                INSERTED.subdominio,
                INSERTED.razon_social,
                INSERTED.nombre_comercial,
                INSERTED.ruc,
                INSERTED.tipo_instalacion,
                INSERTED.servidor_api_local,
                INSERTED.modo_autenticacion,
                INSERTED.logo_url,
                INSERTED.favicon_url,
                INSERTED.color_primario,
                INSERTED.color_secundario,
                INSERTED.tema_personalizado,
                INSERTED.plan_suscripcion,
                INSERTED.estado_suscripcion,
                INSERTED.fecha_inicio_suscripcion,
                INSERTED.fecha_fin_trial,
                INSERTED.contacto_nombre,
                INSERTED.contacto_email,
                INSERTED.contacto_telefono,
                INSERTED.es_activo,
                INSERTED.es_demo,
                INSERTED.metadata_json,
                INSERTED.api_key_sincronizacion,
                INSERTED.sincronizacion_habilitada,
                INSERTED.ultima_sincronizacion,
                INSERTED.fecha_creacion,
                INSERTED.fecha_actualizacion,
                INSERTED.fecha_ultimo_acceso
            VALUES ({placeholders})
        """).bindparams(**bind)

        result = await session.execute(sql)
        row = result.fetchone()
        if not row:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el cliente en la base de datos.",
                internal_code="CLIENT_CREATION_FAILED",
            )
        return _row_to_dict(row, result.keys())

    @staticmethod
    async def _insertar_roles_base(
        session: AsyncSession, cliente_id: UUID
    ) -> Dict[str, UUID]:
        roles_ids: Dict[str, UUID] = {}
        for rol in ROLES_BASE:
            rol_id = uuid4()
            sql = text("""
                INSERT INTO rol (
                    rol_id, cliente_id, empresa_id, codigo_rol, nombre, descripcion,
                    es_rol_sistema, nivel_acceso, es_admin_cliente, es_activo
                )
                OUTPUT INSERTED.rol_id
                VALUES (
                    :rol_id, :cliente_id, NULL, :codigo_rol, :nombre, :descripcion,
                    :es_rol_sistema, :nivel_acceso, :es_admin_cliente, 1
                )
            """).bindparams(
                rol_id=rol_id,
                cliente_id=cliente_id,
                codigo_rol=rol["codigo_rol"],
                nombre=rol["nombre"],
                descripcion=rol["descripcion"],
                es_rol_sistema=rol["es_rol_sistema"],
                nivel_acceso=rol["nivel_acceso"],
                es_admin_cliente=rol["es_admin_cliente"],
            )
            result = await session.execute(sql)
            row = result.fetchone()
            if not row:
                raise DatabaseError(
                    detail=f"No se pudo crear el rol {rol['codigo_rol']}",
                    internal_code="ROLE_CREATION_FAILED",
                )
            roles_ids[rol["codigo_rol"]] = row[0]
        return roles_ids

    @staticmethod
    async def _insertar_usuario_admin(
        session: AsyncSession,
        *,
        cliente_id: UUID,
        cliente_data: ClienteCreate,
        contrasena_hash: str,
        admin_rol_id: UUID,
        empresa_id: Optional[UUID] = None,
    ) -> UUID:
        usuario_id = uuid4()
        apellido_source = (cliente_data.contacto_nombre or "").strip() or (
            cliente_data.razon_social or ""
        )
        apellido_raw = sanitize_person_name(apellido_source[:100])
        apellido = apellido_raw

        sql_usuario = text("""
            INSERT INTO usuario (
                usuario_id, cliente_id, nombre_usuario, contrasena,
                nombre, apellido, correo,
                requiere_cambio_contrasena, correo_confirmado,
                empresa_default_id, es_activo, es_eliminado,
                proveedor_autenticacion
            )
            OUTPUT INSERTED.usuario_id
            VALUES (
                :usuario_id, :cliente_id, :nombre_usuario, :contrasena,
                :nombre, :apellido, :correo,
                1, 1,
                :empresa_default_id, 1, 0,
                'local'
            )
        """).bindparams(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            nombre_usuario=ADMIN_USERNAME,
            contrasena=contrasena_hash,
            nombre="Administrador",
            apellido=apellido,
            correo=cliente_data.contacto_email,
            empresa_default_id=empresa_id,
        )

        try:
            result = await session.execute(sql_usuario)
        except Exception as exc:
            if "empresa_default_id" in str(exc).lower():
                raise DatabaseError(
                    detail=(
                        "No se pudo crear el usuario admin: empresa_default_id debe "
                        "permitir NULL en la tabla usuario para el onboarding."
                    ),
                    internal_code="USER_ONBOARDING_EMPRESA_DEFAULT",
                ) from exc
            raise

        row = result.fetchone()
        if not row:
            raise ServiceError(
                status_code=500,
                detail="No se pudo crear el usuario administrador inicial.",
                internal_code="ADMIN_USER_CREATION_FAILED",
            )

        sql_ur = text("""
            INSERT INTO usuario_rol (
                usuario_rol_id, usuario_id, rol_id, cliente_id,
                empresa_id, es_empresa_default, es_activo
            )
            VALUES (
                :usuario_rol_id, :usuario_id, :rol_id, :cliente_id,
                NULL, 0, 1
            )
        """).bindparams(
            usuario_rol_id=uuid4(),
            usuario_id=usuario_id,
            rol_id=admin_rol_id,
            cliente_id=cliente_id,
        )

        try:
            await session.execute(sql_ur)
        except Exception as exc:
            if "es_empresa_default" in str(exc).lower():
                sql_ur_fallback = text("""
                    INSERT INTO usuario_rol (
                        usuario_rol_id, usuario_id, rol_id, cliente_id,
                        empresa_id, es_activo
                    )
                    VALUES (
                        :usuario_rol_id, :usuario_id, :rol_id, :cliente_id,
                        NULL, 1
                    )
                """).bindparams(
                    usuario_rol_id=uuid4(),
                    usuario_id=usuario_id,
                    rol_id=admin_rol_id,
                    cliente_id=cliente_id,
                )
                await session.execute(sql_ur_fallback)
            else:
                raise

        return usuario_id

    @staticmethod
    async def _insertar_auth_config_si_no_existe(
        session: AsyncSession, cliente_id: UUID
    ) -> None:
        sql = text("""
            IF NOT EXISTS (
                SELECT 1 FROM cliente_auth_config WHERE cliente_id = :cliente_id
            )
            INSERT INTO cliente_auth_config (cliente_id)
            VALUES (:cliente_id)
        """).bindparams(cliente_id=cliente_id)
        await session.execute(sql)

    @staticmethod
    async def _insertar_secuencias_codigo(
        session: AsyncSession, cliente_id: UUID
    ) -> None:
        repo = CfgCodigoSecuenciaRepository()
        for entidad, prefijo, longitud_numero, separador, ultimo_numero in SECUENCIAS_CODIGO:
            await repo.insert_secuencia(
                cliente_id=cliente_id,
                empresa_id=None,
                entidad=entidad,
                prefijo=prefijo,
                longitud_numero=longitud_numero,
                separador=separador,
                session=session,
                ultimo_numero=ultimo_numero,
            )
