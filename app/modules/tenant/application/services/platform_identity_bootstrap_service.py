"""
Bootstrap identidad plataforma — equivalente D010 bloques A–E.

Idempotente: no recrea entidades existentes ni modifica contraseñas.
"""
from __future__ import annotations

import logging
import secrets
import string
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import get_password_hash
from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.platform_bootstrap_constants import (
    ADMIN_PLATFORM_CODIGO_ROL,
    ADMIN_PLATFORM_DESCRIPCION,
    ADMIN_PLATFORM_NIVEL_ACCESO,
    ADMIN_PLATFORM_NOMBRE,
    COLOR_PRIMARIO,
    COLOR_SECUNDARIO,
    DEFAULT_CONTACT_EMAIL_FALLBACK,
    DEFAULT_CONTACTO_NOMBRE,
    DEFAULT_NOMBRE_COMERCIAL,
    DEFAULT_RAZON_SOCIAL,
    ESTADO_SUSCRIPCION_ACTIVO,
    MODO_AUTENTICACION_LOCAL,
    PLAN_SUSCRIPCION_ENTERPRISE,
    PROVEEDOR_AUTENTICACION_LOCAL,
    SUPERADMIN_APELLIDO,
    SUPERADMIN_NOMBRE,
    TIPO_INSTALACION_SHARED,
)
from app.modules.tenant.application.services.platform_rbac_bootstrap_service import (
    PLATFORM_ADMIN_ROL_CODIGO,
    PlatformRbacBootstrapService,
)

logger = logging.getLogger(__name__)


@dataclass
class PlatformIdentityBootstrapResult:
    """Resultado de bootstrap identidad."""

    cliente_created: bool = False
    rol_created: bool = False
    usuario_created: bool = False
    usuario_rol_created: bool = False
    auth_config_created: bool = False
    password_set: bool = False
    password_generated: bool = False
    cliente_id: Optional[str] = None
    rol_id: Optional[str] = None
    usuario_id: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cliente_created": self.cliente_created,
            "rol_created": self.rol_created,
            "usuario_created": self.usuario_created,
            "usuario_rol_created": self.usuario_rol_created,
            "auth_config_created": self.auth_config_created,
            "password_set": self.password_set,
            "password_generated": self.password_generated,
            "cliente_id": self.cliente_id,
            "rol_id": self.rol_id,
            "usuario_id": self.usuario_id,
            "actions": self.actions,
            "warnings": self.warnings,
        }


class PlatformIdentityBootstrapService:
    """Crea/reutiliza cliente plataforma, rol ADMIN_PLATFORM y usuario superadmin."""

    @staticmethod
    def _generar_contrasena_segura(longitud: int = 16) -> str:
        alfabeto = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alfabeto) for _ in range(longitud))

    @staticmethod
    def _resolve_initial_password(
        *,
        usuario_will_be_created: bool,
        expose_generated: bool = False,
    ) -> tuple[Optional[str], bool, List[str]]:
        """Retorna (password_plain, was_generated, warnings)."""
        warnings: List[str] = []
        if not usuario_will_be_created:
            return None, False, warnings

        explicit = (settings.PLATFORM_BOOTSTRAP_INITIAL_PASSWORD or "").strip()
        if explicit:
            return explicit, False, warnings

        if settings.ENVIRONMENT == "production":
            raise ValueError(
                "PLATFORM_BOOTSTRAP_INITIAL_PASSWORD es obligatoria en producción "
                "cuando se crea el usuario superadmin."
            )

        generated = PlatformIdentityBootstrapService._generar_contrasena_segura()
        msg = (
            "Contraseña generada automáticamente (dev). "
            "Defina PLATFORM_BOOTSTRAP_INITIAL_PASSWORD o use --expose-generated-password."
        )
        warnings.append(msg)
        if expose_generated:
            logger.warning("%s Valor: %s", msg, generated)
        else:
            logger.warning("%s (valor no expuesto en logs)", msg)
        return generated, True, warnings

    @staticmethod
    async def _ensure_cliente(session: AsyncSession, result: PlatformIdentityBootstrapResult) -> None:
        cid = PlatformRbacBootstrapService.resolve_platform_cliente_id()
        cid_str = str(cid)
        result.cliente_id = cid_str

        conflict = (
            await session.execute(
                text("""
                    SELECT TOP 1 cliente_id FROM cliente
                    WHERE cliente_id <> :cid
                      AND (subdominio = :subdominio OR codigo_cliente = :codigo)
                """).bindparams(
                    cid=cid_str,
                    subdominio=settings.SUPERADMIN_SUBDOMINIO,
                    codigo=settings.SUPERADMIN_CLIENTE_CODIGO,
                )
            )
        ).first()
        if conflict:
            raise DatabaseError(
                detail=(
                    "Conflicto cliente plataforma: subdominio o codigo_cliente ya asignado "
                    f"a otro cliente ({conflict[0]})."
                ),
                internal_code="PLATFORM_CLIENTE_CONFLICT",
            )

        row = (
            await session.execute(
                text("SELECT cliente_id, es_activo FROM cliente WHERE cliente_id = :cid").bindparams(
                    cid=cid_str
                )
            )
        ).first()

        if row:
            if not row[1]:
                await session.execute(
                    text(
                        "UPDATE cliente SET es_activo = 1, fecha_actualizacion = GETDATE() "
                        "WHERE cliente_id = :cid"
                    ).bindparams(cid=cid_str)
                )
                result.actions.append("cliente_reactivated")
            else:
                result.actions.append("cliente_reused")
            return

        razon = (settings.PLATFORM_BOOTSTRAP_RAZON_SOCIAL or "").strip() or DEFAULT_RAZON_SOCIAL
        contact_email = (
            (settings.PLATFORM_BOOTSTRAP_CONTACT_EMAIL or "").strip()
            or DEFAULT_CONTACT_EMAIL_FALLBACK
        )

        await session.execute(
            text("""
                INSERT INTO cliente (
                    cliente_id, codigo_cliente, razon_social, nombre_comercial,
                    subdominio, tipo_instalacion, modo_autenticacion, es_activo,
                    contacto_nombre, contacto_email,
                    color_primario, color_secundario,
                    plan_suscripcion, estado_suscripcion
                ) VALUES (
                    :cliente_id, :codigo_cliente, :razon_social, :nombre_comercial,
                    :subdominio, :tipo_instalacion, :modo_autenticacion, 1,
                    :contacto_nombre, :contacto_email,
                    :color_primario, :color_secundario,
                    :plan_suscripcion, :estado_suscripcion
                )
            """).bindparams(
                cliente_id=cid_str,
                codigo_cliente=settings.SUPERADMIN_CLIENTE_CODIGO,
                razon_social=razon,
                nombre_comercial=DEFAULT_NOMBRE_COMERCIAL,
                subdominio=settings.SUPERADMIN_SUBDOMINIO,
                tipo_instalacion=TIPO_INSTALACION_SHARED,
                modo_autenticacion=MODO_AUTENTICACION_LOCAL,
                contacto_nombre=DEFAULT_CONTACTO_NOMBRE,
                contacto_email=contact_email,
                color_primario=COLOR_PRIMARIO,
                color_secundario=COLOR_SECUNDARIO,
                plan_suscripcion=PLAN_SUSCRIPCION_ENTERPRISE,
                estado_suscripcion=ESTADO_SUSCRIPCION_ACTIVO,
            )
        )
        result.cliente_created = True
        result.actions.append("cliente_created")

    @staticmethod
    async def _ensure_rol(session: AsyncSession, result: PlatformIdentityBootstrapResult) -> str:
        cid_str = result.cliente_id or str(PlatformRbacBootstrapService.resolve_platform_cliente_id())

        row = (
            await session.execute(
                text("""
                    SELECT rol_id FROM rol
                    WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
                """).bindparams(cid=cid_str, codigo=PLATFORM_ADMIN_ROL_CODIGO)
            )
        ).first()

        if row:
            result.rol_id = str(row[0])
            result.actions.append("rol_reused")
            return result.rol_id

        rol_id = str(uuid4())
        await session.execute(
            text("""
                INSERT INTO rol (
                    rol_id, cliente_id, codigo_rol, nombre, descripcion,
                    es_rol_sistema, nivel_acceso, es_admin_cliente, es_activo
                ) VALUES (
                    :rol_id, :cliente_id, :codigo_rol, :nombre, :descripcion,
                    1, :nivel_acceso, 1, 1
                )
            """).bindparams(
                rol_id=rol_id,
                cliente_id=cid_str,
                codigo_rol=ADMIN_PLATFORM_CODIGO_ROL,
                nombre=ADMIN_PLATFORM_NOMBRE,
                descripcion=ADMIN_PLATFORM_DESCRIPCION,
                nivel_acceso=ADMIN_PLATFORM_NIVEL_ACCESO,
            )
        )
        result.rol_created = True
        result.rol_id = rol_id
        result.actions.append("rol_created")
        return rol_id

    @staticmethod
    async def _ensure_usuario(
        session: AsyncSession,
        result: PlatformIdentityBootstrapResult,
        *,
        password_plain: Optional[str],
    ) -> str:
        cid_str = result.cliente_id or str(PlatformRbacBootstrapService.resolve_platform_cliente_id())

        row = (
            await session.execute(
                text("""
                    SELECT usuario_id, es_activo FROM usuario
                    WHERE cliente_id = :cid AND nombre_usuario = :username AND es_eliminado = 0
                """).bindparams(cid=cid_str, username=settings.SUPERADMIN_USERNAME)
            )
        ).first()

        if row:
            result.usuario_id = str(row[0])
            result.actions.append("usuario_reused")
            if not row[1]:
                await session.execute(
                    text(
                        "UPDATE usuario SET es_activo = 1, fecha_actualizacion = GETDATE() "
                        "WHERE usuario_id = :uid"
                    ).bindparams(uid=result.usuario_id)
                )
                result.actions.append("usuario_reactivated")
            return result.usuario_id

        if not password_plain:
            raise ValueError(
                "Se requiere contraseña para crear usuario superadmin "
                "(PLATFORM_BOOTSTRAP_INITIAL_PASSWORD)."
            )

        usuario_id = str(uuid4())
        contrasena_hash = get_password_hash(password_plain)
        contact_email = (
            (settings.PLATFORM_BOOTSTRAP_CONTACT_EMAIL or "").strip()
            or DEFAULT_CONTACT_EMAIL_FALLBACK
        )
        await session.execute(
            text("""
                INSERT INTO usuario (
                    usuario_id, cliente_id, nombre_usuario, contrasena,
                    nombre, apellido, correo,
                    es_activo, correo_confirmado, es_eliminado,
                    proveedor_autenticacion
                ) VALUES (
                    :usuario_id, :cliente_id, :nombre_usuario, :contrasena,
                    :nombre, :apellido, :correo,
                    1, 1, 0,
                    :proveedor
                )
            """).bindparams(
                usuario_id=usuario_id,
                cliente_id=cid_str,
                nombre_usuario=settings.SUPERADMIN_USERNAME,
                contrasena=contrasena_hash,
                nombre=SUPERADMIN_NOMBRE,
                apellido=SUPERADMIN_APELLIDO,
                correo=contact_email,
                proveedor=PROVEEDOR_AUTENTICACION_LOCAL,
            )
        )
        result.usuario_created = True
        result.password_set = True
        result.usuario_id = usuario_id
        result.actions.append("usuario_created")
        return usuario_id

    @staticmethod
    async def _ensure_usuario_rol(
        session: AsyncSession,
        result: PlatformIdentityBootstrapResult,
        *,
        rol_id: str,
        usuario_id: str,
    ) -> None:
        cid_str = result.cliente_id or str(PlatformRbacBootstrapService.resolve_platform_cliente_id())

        row = (
            await session.execute(
                text("""
                    SELECT 1 FROM usuario_rol
                    WHERE usuario_id = :uid AND rol_id = :rid AND cliente_id = :cid
                      AND empresa_id IS NULL AND es_activo = 1
                """).bindparams(uid=usuario_id, rid=rol_id, cid=cid_str)
            )
        ).first()

        if row:
            result.actions.append("usuario_rol_reused")
            return

        await session.execute(
            text("""
                INSERT INTO usuario_rol (
                    usuario_rol_id, usuario_id, rol_id, cliente_id,
                    empresa_id, es_empresa_default, es_activo
                ) VALUES (
                    :ur_id, :uid, :rid, :cid,
                    NULL, 0, 1
                )
            """).bindparams(
                ur_id=str(uuid4()),
                uid=usuario_id,
                rid=rol_id,
                cid=cid_str,
            )
        )
        result.usuario_rol_created = True
        result.actions.append("usuario_rol_created")

    @staticmethod
    async def _ensure_auth_config(
        session: AsyncSession, result: PlatformIdentityBootstrapResult
    ) -> None:
        cid_str = result.cliente_id or str(PlatformRbacBootstrapService.resolve_platform_cliente_id())

        row = (
            await session.execute(
                text("SELECT 1 FROM cliente_auth_config WHERE cliente_id = :cid").bindparams(
                    cid=cid_str
                )
            )
        ).first()

        if row:
            result.actions.append("auth_config_reused")
            return

        await session.execute(
            text("""
                IF NOT EXISTS (
                    SELECT 1 FROM cliente_auth_config WHERE cliente_id = :cid
                )
                INSERT INTO cliente_auth_config (cliente_id)
                VALUES (:cid)
            """).bindparams(cid=cid_str)
        )
        result.auth_config_created = True
        result.actions.append("auth_config_created")

    @classmethod
    async def bootstrap_platform_identity(
        cls,
        session: AsyncSession,
        *,
        dry_run: bool = False,
        expose_generated_password: bool = False,
    ) -> PlatformIdentityBootstrapResult:
        """
        Bootstrap identidad plataforma (bloques A–E).

        Si dry_run=True, no persiste cambios (solo simula acciones vía audit previo).
        """
        result = PlatformIdentityBootstrapResult()

        cid_str = str(PlatformRbacBootstrapService.resolve_platform_cliente_id())
        result.cliente_id = cid_str

        cliente_exists = (
            await session.execute(
                text("SELECT 1 FROM cliente WHERE cliente_id = :cid").bindparams(cid=cid_str)
            )
        ).first() is not None

        rol_exists = (
            await session.execute(
                text("""
                    SELECT 1 FROM rol
                    WHERE cliente_id = :cid AND codigo_rol = :codigo AND es_activo = 1
                """).bindparams(cid=cid_str, codigo=PLATFORM_ADMIN_ROL_CODIGO)
            )
        ).first() is not None

        usuario_exists = (
            await session.execute(
                text("""
                    SELECT 1 FROM usuario
                    WHERE cliente_id = :cid AND nombre_usuario = :username AND es_eliminado = 0
                """).bindparams(cid=cid_str, username=settings.SUPERADMIN_USERNAME)
            )
        ).first() is not None

        usuario_will_create = not usuario_exists
        password_plain, was_generated, pwd_warnings = cls._resolve_initial_password(
            usuario_will_be_created=usuario_will_create,
            expose_generated=expose_generated_password,
        )
        result.password_generated = was_generated
        result.warnings.extend(pwd_warnings)

        if dry_run:
            if not cliente_exists:
                result.actions.append("would_create_cliente")
            else:
                result.actions.append("would_reuse_cliente")
            if not rol_exists:
                result.actions.append("would_create_rol")
            else:
                result.actions.append("would_reuse_rol")
            if usuario_will_create:
                result.actions.append("would_create_usuario")
            else:
                result.actions.append("would_reuse_usuario")
            if not usuario_exists or not rol_exists:
                result.actions.append("would_ensure_usuario_rol")
            auth_exists = (
                await session.execute(
                    text("SELECT 1 FROM cliente_auth_config WHERE cliente_id = :cid").bindparams(
                        cid=cid_str
                    )
                )
            ).first() is not None
            if not auth_exists:
                result.actions.append("would_create_auth_config")
            return result

        await cls._ensure_cliente(session, result)
        rol_id = await cls._ensure_rol(session, result)
        usuario_id = await cls._ensure_usuario(
            session, result, password_plain=password_plain if usuario_will_create else None
        )
        await cls._ensure_usuario_rol(session, result, rol_id=rol_id, usuario_id=usuario_id)
        await cls._ensure_auth_config(session, result)

        return result
