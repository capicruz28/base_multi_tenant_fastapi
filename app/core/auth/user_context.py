"""
Servicio ligero para obtener contexto de usuario autenticado.

Este módulo proporciona funciones optimizadas para obtener solo el contexto
mínimo necesario del usuario autenticado, sin construir objetos de dominio completos.

F8-A: lecturas vía Identity Gateway (sin UsuarioTable directo).
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass
import logging

from app.core.auth.platform_user_lookup import resolve_platform_superadmin_flag
from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway

logger = logging.getLogger(__name__)

_NULL_CLIENTE_ID = UUID("00000000-0000-0000-0000-000000000000")


@dataclass
class CurrentUserContext:
    """
    Contexto mínimo del usuario autenticado.

    Contiene solo la información esencial necesaria para autorización
    y validación de tenant, sin objetos de dominio completos.
    """
    usuario_id: UUID
    cliente_id: Optional[UUID]
    nombre_usuario: str
    es_activo: bool
    is_superadmin: bool
    nivel_acceso: int
    roles: List[str]


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


def _resolve_cliente_id_from_user_row(
    user_result: Dict[str, Any],
    request_cliente_id: Optional[UUID],
) -> Optional[UUID]:
    """Normaliza cliente_id; usa contexto de request si la fila no lo trae."""
    user_cliente_id = _normalize_cliente_id(user_result.get("cliente_id"))
    if user_cliente_id:
        return user_cliente_id

    if request_cliente_id:
        logger.debug(
            "[USER_CONTEXT] cliente_id ausente en fila, usando request_cliente_id=%s",
            request_cliente_id,
        )
        return request_cliente_id

    from app.core.tenant.context import try_get_current_client_id

    ctx_cliente_id = try_get_current_client_id()
    if ctx_cliente_id:
        logger.debug(
            "[USER_CONTEXT] cliente_id ausente en fila, usando contexto=%s",
            ctx_cliente_id,
        )
        return ctx_cliente_id

    logger.warning(
        "[USER_CONTEXT] No se pudo resolver cliente_id para usuario '%s'",
        user_result.get("nombre_usuario"),
    )
    return None


async def get_user_auth_context(
    username: str,
    request_cliente_id: Optional[UUID] = None,
) -> Optional[CurrentUserContext]:
    """
    Obtiene el contexto mínimo del usuario autenticado.

    Args:
        username: Nombre de usuario del token JWT
        request_cliente_id: ID del cliente del request (del contexto de tenant)

    Returns:
        CurrentUserContext si el usuario existe y está activo, None en caso contrario
    """
    try:
        user_result = await IdentityGateway.lookup_user_for_auth_context(
            username,
            request_cliente_id,
        )

        if not user_result:
            logger.warning("Usuario '%s' no encontrado en BD", username)
            return None

        usuario_id = user_result.get("usuario_id")
        es_activo = user_result.get("es_activo", False)
        cliente_id = _resolve_cliente_id_from_user_row(user_result, request_cliente_id)

        if not es_activo:
            logger.warning("Usuario '%s' inactivo", username)
            return None

        roles_cliente_id = cliente_id or request_cliente_id
        if not roles_cliente_id:
            logger.warning("Sin cliente_id para roles de usuario '%s'", username)
            return None

        roles_result = await IdentityGateway.get_user_roles_for_auth(
            IdentityContext(cliente_id=roles_cliente_id),
            usuario_id,
        )

        roles_list: List[str] = []
        nivel_acceso = 1
        is_superadmin = False

        if roles_result:
            niveles = []
            for role in roles_result:
                role_name = role.get("nombre")
                if role_name:
                    roles_list.append(role_name)

                nivel = role.get("nivel_acceso", 1)
                if nivel:
                    niveles.append(nivel)

                codigo_rol = role.get("codigo_rol")
                if codigo_rol == "SUPER_ADMIN" and nivel == 5:
                    is_superadmin = True

            if niveles:
                nivel_acceso = max(niveles)

        is_superadmin = resolve_platform_superadmin_flag(
            username=username,
            request_cliente_id=request_cliente_id,
            roles_result=roles_result,
            nivel_acceso=nivel_acceso,
            is_superadmin_from_roles=is_superadmin,
        )

        context = CurrentUserContext(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            nombre_usuario=username,
            es_activo=es_activo,
            is_superadmin=is_superadmin,
            nivel_acceso=nivel_acceso,
            roles=roles_list,
        )

        logger.debug(
            "Contexto de usuario obtenido: %s, cliente_id=%s, nivel=%s, superadmin=%s",
            username,
            cliente_id,
            nivel_acceso,
            is_superadmin,
        )

        return context

    except Exception as e:
        logger.error(
            "Error obteniendo contexto de usuario '%s': %s",
            username,
            e,
            exc_info=True,
        )
        return None


async def validate_tenant_access(
    context: CurrentUserContext,
    request_cliente_id: Optional[UUID],
) -> bool:
    """
    Valida que el usuario tenga acceso al tenant del request.

    Reglas:
    - SuperAdmin puede acceder a cualquier tenant
    - Usuarios regulares solo pueden acceder a su propio tenant
    """
    if context.is_superadmin:
        return True

    if context.cliente_id is None:
        logger.warning(
            "Usuario regular '%s' tiene cliente_id NULL",
            context.nombre_usuario,
        )
        return False

    if request_cliente_id is None:
        logger.warning(
            "Request no tiene cliente_id para validar acceso de '%s'",
            context.nombre_usuario,
        )
        return False

    return context.cliente_id == request_cliente_id


def determine_user_type(
    access_level: int,
    is_super_admin: bool,
    *,
    request_cliente_id: Optional[UUID] = None,
) -> str:
    """Determina el tipo de usuario basado en nivel de acceso."""
    from app.core.auth.platform_user_lookup import is_system_request_client

    if is_super_admin and is_system_request_client(request_cliente_id):
        return "platform_admin"
    if is_super_admin:
        return "super_admin"
    if access_level >= 4:
        return "tenant_admin"
    return "user"
