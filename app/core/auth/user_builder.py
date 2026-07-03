"""
Servicio para construir objetos Pydantic completos de usuario.

F8-A: lecturas vía Identity Gateway (sin ramas database_type ni UsuarioTable directo).
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.rbac.presentation.schemas import RolRead
from app.core.config import settings
from app.core.auth.auth_runtime_scope import resolve_rbac_database_type
from app.core.auth.platform_user_lookup import (
    is_system_request_client,
    resolve_platform_superadmin_flag,
)
from app.core.auth.user_context import determine_user_type
from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.shared.validators import sanitize_person_name

logger = logging.getLogger(__name__)

_NULL_CLIENTE_ID = UUID("00000000-0000-0000-0000-000000000000")
_ROLES_GLOBALES_SISTEMA = frozenset(
    {
        "SUPER_ADMIN",
        "SUPERADMIN",
        "SYSTEM_ADMIN",
        "ADMIN_PLATFORM",
        "SUPPORT_PLATFORM",
        "USER_PLATFORM",
    }
)


def _normalize_cliente_id(raw: Any) -> Optional[UUID]:
    if raw is None:
        return None
    if isinstance(raw, UUID):
        return None if raw == _NULL_CLIENTE_ID else raw
    if isinstance(raw, str):
        try:
            parsed = UUID(raw)
        except (ValueError, AttributeError):
            return None
        return None if parsed == _NULL_CLIENTE_ID else parsed
    return None


def _prepare_usuario_read_dict(
    user_result: Dict[str, Any],
    *,
    cliente_id: UUID,
    nivel_acceso: int,
    is_superadmin: bool,
    user_type: str,
) -> Dict[str, Any]:
    """Completa campos mínimos exigidos por UsuarioReadWithRoles."""
    prepared = dict(user_result)
    prepared["cliente_id"] = cliente_id
    prepared["nombre"] = sanitize_person_name(prepared.get("nombre"))
    prepared["apellido"] = sanitize_person_name(prepared.get("apellido"))
    prepared.setdefault("fecha_creacion", datetime.utcnow())
    prepared.setdefault("fecha_ultimo_acceso", None)
    prepared.setdefault("correo_confirmado", False)
    prepared.setdefault("proveedor_autenticacion", "local")
    prepared.setdefault("fecha_ultimo_cambio_contrasena", None)
    prepared.setdefault("requiere_cambio_contrasena", False)
    prepared.setdefault("intentos_fallidos", 0)
    prepared.setdefault("fecha_bloqueo", None)
    prepared.setdefault("es_eliminado", False)
    prepared.setdefault("correo", prepared.get("correo") or "")
    prepared["access_level"] = nivel_acceso
    prepared["is_super_admin"] = is_superadmin
    prepared["user_type"] = user_type
    return prepared


def _resolve_cliente_id(
    user_result: Dict[str, Any],
    request_cliente_id: Optional[UUID],
) -> Optional[UUID]:
    user_cliente_id = _normalize_cliente_id(user_result.get("cliente_id"))
    if user_cliente_id:
        return user_cliente_id
    if request_cliente_id:
        return request_cliente_id
    from app.core.tenant.context import try_get_current_client_id

    return try_get_current_client_id()


async def build_user_with_roles(
    username: str,
    request_cliente_id: Optional[UUID] = None,
) -> Optional[UsuarioReadWithRoles]:
    """
    Construye un objeto UsuarioReadWithRoles completo con todos los datos del usuario.
    """
    try:
        from app.core.tenant.empresa_context import try_get_current_empresa_id

        empresa_id_ctx = try_get_current_empresa_id()

        user_result = await IdentityGateway.lookup_user_for_auth_context(
            username,
            request_cliente_id,
        )
        if not user_result or not user_result.get("es_activo", False):
            return None

        usuario_id = user_result.get("usuario_id")
        cliente_id = _resolve_cliente_id(user_result, request_cliente_id)
        if not cliente_id:
            logger.warning(
                "[USER_BUILDER] No se pudo resolver cliente_id para usuario '%s'",
                username,
            )
            return None

        identity_ctx = IdentityContext(cliente_id=cliente_id)
        roles_result = await IdentityGateway.get_user_roles_for_auth(
            identity_ctx,
            usuario_id,
            empresa_id=empresa_id_ctx,
        )

        roles_list: List[RolRead] = []
        nivel_acceso = 1
        is_superadmin = False

        if roles_result:
            niveles = []
            for role_data in roles_result:
                try:
                    fecha_creacion = role_data.get("fecha_creacion")
                    if isinstance(fecha_creacion, str):
                        try:
                            fecha_creacion = datetime.fromisoformat(
                                fecha_creacion.replace("Z", "+00:00")
                            )
                        except Exception:
                            fecha_creacion = datetime.now()
                    elif not isinstance(fecha_creacion, datetime):
                        fecha_creacion = datetime.now()

                    rol_cliente_id = _normalize_cliente_id(role_data.get("cliente_id"))
                    codigo_rol = role_data.get("codigo_rol")
                    if codigo_rol and codigo_rol.upper() in _ROLES_GLOBALES_SISTEMA:
                        rol_cliente_id = None

                    rol_read = RolRead(
                        rol_id=role_data.get("rol_id"),
                        nombre=role_data.get("nombre"),
                        descripcion=role_data.get("descripcion"),
                        nivel_acceso=role_data.get("nivel_acceso", 1),
                        codigo_rol=codigo_rol,
                        es_activo=bool(role_data.get("es_activo", True)),
                        fecha_creacion=fecha_creacion,
                        cliente_id=rol_cliente_id,
                    )
                    roles_list.append(rol_read)

                    nivel = role_data.get("nivel_acceso", 1)
                    if nivel:
                        niveles.append(nivel)

                    codigo = (codigo_rol or "").upper()
                    if codigo in ("SUPER_ADMIN", "ADMIN_PLATFORM") and nivel >= 5:
                        is_superadmin = True

                except Exception as e:
                    logger.warning("Error construyendo RolRead: %s", e)
                    continue

            if niveles:
                nivel_acceso = max(niveles)

        is_superadmin = resolve_platform_superadmin_flag(
            username=username,
            request_cliente_id=request_cliente_id,
            roles_result=roles_result,
            nivel_acceso=nivel_acceso,
            is_superadmin_from_roles=is_superadmin,
        )

        if is_superadmin and is_system_request_client(request_cliente_id):
            user_type = "platform_admin"
        else:
            user_type = determine_user_type(nivel_acceso, is_superadmin)

        database_type = resolve_rbac_database_type()
        permisos_codigos: List[str] = []
        try:
            from app.core.config import settings as _settings

            use_resolver = getattr(_settings, "USE_PERMISSION_RESOLVER", False)
            if use_resolver:
                try:
                    from app.core.authorization.permission_resolver import (
                        get_permission_resolver,
                    )

                    resolver = get_permission_resolver()
                    effective = await resolver.get_effective_permissions(
                        usuario_id=usuario_id,
                        cliente_id=cliente_id,
                        database_type=database_type,
                        is_super_admin=is_superadmin,
                        filter_by_subscription=getattr(
                            _settings,
                            "PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION",
                            False,
                        ),
                        empresa_id=empresa_id_ctx,
                    )
                    permisos_codigos = list(effective.codes)
                except Exception as resolver_err:
                    logger.warning(
                        "[USER_BUILDER] Permission resolver falló, usando fallback: %s",
                        resolver_err,
                        exc_info=False,
                    )
                    from app.modules.rbac.application.services.permisos_usuario_service import (
                        obtener_codigos_permiso_usuario,
                    )

                    permisos_codigos = await obtener_codigos_permiso_usuario(
                        usuario_id=usuario_id,
                        cliente_id=cliente_id,
                        database_type=database_type,
                        empresa_id=empresa_id_ctx,
                    )
            else:
                from app.modules.rbac.application.services.permisos_usuario_service import (
                    obtener_codigos_permiso_usuario,
                )

                permisos_codigos = await obtener_codigos_permiso_usuario(
                    usuario_id=usuario_id,
                    cliente_id=cliente_id,
                    database_type=database_type,
                    empresa_id=empresa_id_ctx,
                )
        except Exception as perm_err:
            logger.debug(
                "[USER_BUILDER] Permisos RBAC no cargados para %s: %s",
                username,
                perm_err,
            )

        usuario_dict = _prepare_usuario_read_dict(
            user_result,
            cliente_id=cliente_id,
            nivel_acceso=nivel_acceso,
            is_superadmin=is_superadmin,
            user_type=user_type,
        )
        return UsuarioReadWithRoles(
            **usuario_dict,
            roles=roles_list,
            permisos=permisos_codigos,
        )

    except Exception as e:
        if settings.ENABLE_AUTH_VERBOSE:
            logger.error(
                "[ME-ENDPOINT] build_user_with_roles exception=%s:%s username=%s "
                "request_cliente_id=%s",
                type(e).__name__,
                e,
                username,
                request_cliente_id,
                exc_info=True,
            )
        return None
