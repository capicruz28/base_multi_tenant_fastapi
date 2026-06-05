# app/api/v1/endpoints/auth.py
"""
Módulo de endpoints para la gestión de la autenticación de usuarios (Login, Logout, Refresh Token).

Este módulo maneja el flujo de autenticación basado en JWT y cookies seguras en una arquitectura multi-tenant.

Características principales:
- **Login:** Verifica credenciales dentro del contexto de un cliente, genera Access/Refresh Tokens.
- **Me:** Obtiene información del usuario autenticado.
- **Refresh:** Genera un nuevo Access Token usando el Refresh Token.
- **Logout:** Revoca el Refresh Token para cerrar la sesión.
- **✅ MULTI-TENANT:** Autenticación segmentada por cliente (subdominio o cliente_id).
- **✅ SSO:** Soporte para Azure AD y Google Workspace.
"""
from typing import List, Dict, Optional, Union, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Path, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.core.auth import get_user_access_level_info

# Importar la función que lee el ContextVar del cliente (¡Asume que está definida!)
from app.core.tenant.context import get_current_client_id 

from app.modules.auth.presentation.schemas import (
    Token,
    UserDataWithRoles,
    MeResponse,
    LoginData,
    PermissionsMeResponse,
    LoginEmpresaSelectionResponse,
    EmpresaDisponible,
    EmpresaIdRequest,
    build_user_data_with_roles_dict,
    ImpersonationEndResponse,
)
from app.core.authorization.rbac import require_super_admin
from app.core.auth.impersonation import is_impersonation_payload
from app.core.security.jwt import normalize_bearer_jwt_token
from app.modules.auth.application.services.impersonation_service import (
    ImpersonationService,
)
from app.api.deps_auth import (
    require_selection_token_payload,
    require_full_session_payload,
    require_erp_session,
    get_current_active_user_full_session,
    reject_selection_token_for_me,
)
from app.core.auth import (
    authenticate_user,
    get_current_user,
    get_current_user_from_refresh,
    authenticate_user_sso_azure_ad,
    authenticate_user_sso_google
)
from app.api.deps import get_current_active_user, get_current_user_data
from app.core.authorization.rbac import has_permission
from app.core.security.jwt import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.logging_config import get_logger
from app.modules.users.application.services.user_service import UsuarioService
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.tenant.application.services.cliente_service import ClienteService
from app.modules.superadmin.application.services.audit_service import AuditService
from app.api.deps import RoleChecker, get_current_active_user
from app.core.exceptions import AuthenticationError, CustomException
from app.infrastructure.database.connection import DatabaseConnection, get_db_connection

# ✅ FASE 1: Rate Limiting (condicional)
from app.core.security.rate_limiting import get_rate_limit_decorator

router = APIRouter()
logger = get_logger(__name__)

# Dependencia específica para requerir rol 'admin'
require_admin = RoleChecker(["Administrador"])

# ✅ NUEVO: Función para detectar tipo de cliente
def get_client_type(request: Request) -> str:
    """
    Detecta el tipo de cliente desde el header X-Client-Type.
    
    Args:
        request: Objeto Request de FastAPI
        
    Returns:
        str: 'web' o 'mobile'
    """
    client_type = request.headers.get("X-Client-Type", "web").lower()
    if client_type not in ["web", "mobile"]:
        logger.warning(f"Tipo de cliente desconocido: '{client_type}', usando 'web' por defecto")
        return "web"
    logger.debug(f"Cliente detectado: {client_type}")
    return client_type


def _extract_bearer_from_request(request: Request) -> str:
    """Obtiene el JWT del header Authorization."""
    authorization = request.headers.get("Authorization") or ""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return normalize_bearer_jwt_token(authorization[7:].strip())


def _access_only_token_response(session: Dict[str, Any]) -> Dict[str, Any]:
    """Respuesta Token sin refresh (impersonación)."""
    return {
        "access_token": session["access_token"],
        "token_type": "bearer",
        "user_data": session.get("user_data"),
    }


def _session_token_http_response(
    response: Response,
    request: Request,
    session: Dict,
) -> Dict:
    """
    Arma respuesta Token (JSON + cookie refresh en web) a partir de emitir_sesion_*.
    """
    client_type = get_client_type(request)
    refresh_expire_days = session["refresh_expire_days"]
    refresh_cookie_max_age = refresh_expire_days * 24 * 60 * 60
    response_data = {
        "access_token": session["access_token"],
        "token_type": "bearer",
        "user_data": session["user_data"],
    }
    refresh_token = session["refresh_token"]
    if client_type == "web":
        response.set_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            value=refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=refresh_cookie_max_age,
            path="/",
            domain=settings.COOKIE_DOMAIN,
        )
    else:
        response_data["refresh_token"] = refresh_token
    return response_data


# ----
# --- Endpoint para Login ---
# ----
# ✅ FASE 1: Rate limiting en login (aplicado correctamente para FastAPI)
# El decorador se aplica después del router.post para que funcione correctamente
@router.post(
    "/login/",
    response_model=Union[Token, LoginEmpresaSelectionResponse],
    summary="Autenticar usuario y obtener token",
    description="""
    Verifica credenciales (nombre de usuario/email y contraseña) **dentro del contexto de un cliente**.
    El cliente se identifica mediante `cliente_id` o `subdominio` en el cuerpo de la solicitud.
    
    Genera un **Access Token** y un **Refresh Token**.
    
    **✅ MULTI-TENANT: Estrategia de tokens según cliente:**
    - **Web (X-Client-Type: web):** Access Token en JSON, Refresh Token en HttpOnly cookie
    - **Móvil (X-Client-Type: mobile):** Ambos tokens en JSON (sin cookie)
    
    Retorna los datos básicos del usuario, incluyendo sus roles.

    **Respuestas:**
    - 200: Autenticación exitosa y tokens generados.
    - 400: No se proporcionó identificador de cliente (cliente_id o subdominio).
    - 401: Credenciales inválidas o cliente inactivo.
    - 404: Cliente no encontrado.
    - 429: Demasiadas solicitudes (rate limit excedido).
    - 500: Error interno del servidor.
    """
)
# ✅ FASE 1: Rate limiting aplicado después del decorador de router (orden correcto para FastAPI)
@get_rate_limit_decorator("login")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Realiza la autenticación del usuario **dentro del cliente especificado** y emite los tokens de sesión.

    Args:
        request: Objeto Request para detectar tipo de cliente.
        response: Objeto Response de FastAPI para manipular cookies.
        login_data: Datos de login que incluyen credenciales y contexto del cliente.

    Returns:
        Token: Objeto que contiene el Access Token, tipo de token y los datos del usuario.

    Raises:
        HTTPException: Si la autenticación falla o hay error interno.
    """
    try:
        # 1. 🔑 RESOLVER CLIENTE_ID DESDE EL CONTEXTO (MIDDLEWARE)
        try:
            # CORRECCIÓN CLAVE: Usamos la función de contexto (Opción 1)
            cliente_id = get_current_client_id()
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cliente ID no disponible. El subdominio no pudo ser resuelto por el middleware."
            )
        
        # 2. ✅ VALIDAR CLIENTE ACTIVO
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente or not cliente.es_activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El cliente asociado al subdominio no está activo."
            )
            
        logger.info(f"Cliente {cliente_id} resuelto y validado para login.")

        # 3. ✅ NUEVO: Detectar tipo de cliente
        client_type = get_client_type(request)

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 4. Autenticación (maneja 401 si falla)
        try:
            user_base_data = await authenticate_user(
                cliente_id, form_data.username, form_data.password
            )
        except HTTPException as auth_exc:
            # Registrar intento fallido de login en auditoría (no debe romper el flujo)
            try:
                await AuditService.registrar_auth_event(
                    cliente_id=cliente_id,
                    usuario_id=None,
                    evento="login_failed",
                    nombre_usuario_intento=form_data.username,
                    descripcion="Intento de login fallido",
                    exito=False,
                    codigo_error=str(auth_exc.detail),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "client_type": client_type,
                        "auth_method": "password",
                        "status_code": auth_exc.status_code,
                    },
                )
            except Exception:
                logger.exception(
                    "[AUDIT] Error registrando evento login_failed (no crítico)"
                )
            # Propagar el error original
            raise auth_exc

        # 5. ✅ CORRECCIÓN: Manejar contexto multi-tenant para superadmin
        user_id = user_base_data.get('usuario_id')
        es_superadmin = user_base_data.get('es_superadmin', False)
        # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, target_cliente_id debe ser el cliente_id del contexto
        # no el cliente_id del usuario (que puede ser nulo)
        target_cliente_id = user_base_data.get('target_cliente_id')
        if not target_cliente_id:
            # Si no hay target_cliente_id, usar cliente_id del contexto (siempre correcto)
            target_cliente_id = cliente_id
            logger.debug(f"[LOGIN] target_cliente_id no encontrado en user_base_data, usando cliente_id del contexto: {cliente_id}")

        # 5b. Resolución de empresa activa (multi-empresa); superadmin nunca selecciona empresa
        empresa_ctx = await AuthService.get_empresa_activa_para_login(
            user_id,
            target_cliente_id,
            es_superadmin=es_superadmin,
            user_type=user_base_data.get("user_type"),
        )
        empresa_activa = empresa_ctx.get("empresa_activa")
        requiere_seleccion = empresa_ctx.get("requiere_seleccion", False)
        es_admin_sin_empresa = empresa_ctx.get("es_admin_sin_empresa", False)
        empresas_disponibles = empresa_ctx.get("empresas_disponibles") or []

        AuthService.assert_operational_login_allowed(
            empresa_ctx,
            es_superadmin=es_superadmin,
            user_type=user_base_data.get("user_type"),
        )

        # Para superadmin, podría no tener roles en el cliente destino
        if es_superadmin:
            user_role_names = ["Super Administrador"]  # Rol implícito
            logger.info(f"[LOGIN] Superadmin accediendo a cliente_id={target_cliente_id}")
        else:
            user_role_names = await UsuarioService.get_user_role_names(
                cliente_id, user_id, empresa_id=empresa_activa
            )

        # 6. Tokens con contexto correcto
        level_info = await get_user_access_level_info(
            user_id,
            target_cliente_id,
            empresa_id=empresa_activa,
            username=form_data.username,
        )
        if es_superadmin or level_info.get("is_super_admin"):
            level_info = AuthService._platform_superadmin_level_info()
            es_superadmin = True

        es_admin_cliente = await AuthService.usuario_tiene_es_admin_cliente(
            user_id,
            target_cliente_id,
            empresa_activa,
            username=form_data.username,
        )
        user_type_login = level_info.get("user_type", "user")

        user_profile = build_user_data_with_roles_dict(
            usuario_id=user_id,
            nombre_usuario=form_data.username,
            correo=user_base_data.get("correo", ""),
            nombre=user_base_data.get("nombre"),
            apellido=user_base_data.get("apellido"),
            es_activo=user_base_data.get("es_activo", True),
            roles=user_role_names,
            access_level=level_info.get("access_level", 1),
            is_super_admin=level_info.get("is_super_admin", False),
            user_type=user_type_login,
            cliente_id=target_cliente_id,
            es_admin_cliente=es_admin_cliente,
            empresa_activa=(
                str(empresa_activa) if empresa_activa is not None else None
            ),
        )

        token_data = {
            "sub": form_data.username,
            "cliente_id": str(target_cliente_id),
            "level_info": level_info,
        }

        if es_superadmin:
            token_data["es_superadmin"] = True

        token_expiration = await AuthService.get_token_expiration_for_cliente(target_cliente_id)
        access_expire_minutes = token_expiration["access_token_minutes"]
        refresh_expire_days = token_expiration["refresh_token_days"]
        refresh_cookie_max_age = refresh_expire_days * 24 * 60 * 60

        # Selección de empresa obligatoria: token temporal sin refresh
        if requiere_seleccion:
            selection_payload = {**token_data, "empresa_selection_pending": True}
            selection_token, _selection_jti = create_access_token(
                data=selection_payload,
                empresa_id=None,
                es_admin_cliente=es_admin_cliente,
                access_token_expire_minutes=access_expire_minutes,
            )
            logger.info(
                "[LOGIN] Usuario %s requiere selección de empresa (%s opciones)",
                form_data.username,
                len(empresas_disponibles),
            )
            selection_profile = build_user_data_with_roles_dict(
                usuario_id=user_id,
                nombre_usuario=form_data.username,
                correo=user_base_data.get("correo", ""),
                nombre=user_base_data.get("nombre"),
                apellido=user_base_data.get("apellido"),
                es_activo=user_base_data.get("es_activo", True),
                roles=user_role_names,
                access_level=level_info.get("access_level", 1),
                is_super_admin=level_info.get("is_super_admin", False),
                user_type=user_type_login,
                cliente_id=target_cliente_id,
                es_admin_cliente=es_admin_cliente,
            )
            return LoginEmpresaSelectionResponse(
                requiere_seleccion_empresa=True,
                empresas_disponibles=[
                    EmpresaDisponible.model_validate(e) for e in empresas_disponibles
                ],
                selection_token=selection_token,
                token_type="bearer",
                user_data=UserDataWithRoles.model_validate(selection_profile),
            )

        if empresa_activa is None and es_admin_sin_empresa and not empresas_disponibles:
            logger.info(
                "[LOGIN] Usuario %s admin sin empresa (onboarding); continúa sin empresa_id",
                form_data.username,
            )

        access_token, access_jti = create_access_token(
            data=token_data,
            empresa_id=empresa_activa,
            es_admin_cliente=es_admin_cliente,
            access_token_expire_minutes=access_expire_minutes,
        )
        refresh_token, refresh_jti = create_refresh_token(
            data=token_data,
            empresa_id=empresa_activa,
            es_admin_cliente=es_admin_cliente,
            refresh_token_expire_days=refresh_expire_days,
        )

        try:
            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=target_cliente_id,
                usuario_id=user_id,
                token=refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                is_rotation=False,
                empresa_id=empresa_activa,
                refresh_token_expire_days=refresh_expire_days,
            )
            
            if stored and stored.get('token_id'):
                logger.info(f"[LOGIN-{client_type.upper()}] Token almacenado - ID: {stored['token_id']}")
            else:
                logger.warning(f"[LOGIN-{client_type.upper()}] Token duplicado en login (revisar)")
                
        except Exception as e:
            logger.error(f"[LOGIN] Error almacenando refresh token: {str(e)}")
            # No fallar el login

        # ✅ NUEVO: Lógica diferenciada según tipo de cliente
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": UserDataWithRoles.model_validate(user_profile),
        }
        
        if client_type == "web":
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=refresh_cookie_max_age,
                path="/",
                domain=settings.COOKIE_DOMAIN,
            )
            logger.info(f"Usuario {form_data.username} autenticado exitosamente (WEB) para cliente {cliente_id}")
            
        else:  # mobile
            response_data["refresh_token"] = refresh_token
            logger.info(f"Usuario {form_data.username} autenticado exitosamente (MOBILE) para cliente {cliente_id}")

        # Registrar login exitoso en auditoría (no bloquear login si falla)
        try:
            await AuditService.registrar_auth_event(
                cliente_id=target_cliente_id,
                usuario_id=user_id,
                evento="login_success",
                nombre_usuario_intento=form_data.username,
                descripcion="Login exitoso",
                exito=True,
                codigo_error=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "client_type": client_type,
                    "es_superadmin": es_superadmin,
                    "auth_method": "password",
                },
            )
        except Exception:
            logger.exception(
                "[AUDIT] Error registrando evento login_success (no crítico)"
            )

        return response_data

    except HTTPException:
        raise
    except CustomException:
        raise
    except Exception as e:
        logger.exception(f"Error inesperado en /login/ para usuario {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado durante el proceso de login."
        )


# ----
# --- Selección y cambio de empresa activa ---
# ----

@router.post(
    "/empresa/seleccionar/",
    response_model=Token,
    summary="Confirmar empresa tras login multi-empresa",
    description="""
    Cierra el flujo iniciado con `LoginEmpresaSelectionResponse`.

    **Autenticación:** Bearer con JWT que incluya `empresa_selection_pending: true`
    (selection_token del login). No acepta access token de sesión normal (409).

    **Body:** `{ "empresa_id": "<uuid>" }`

    **Respuesta 200:** Igual que login exitoso (`Token` con access, refresh según X-Client-Type,
    `user_data` con `empresa_activa`, `es_admin_cliente`, roles filtrados por empresa).
    """,
)
async def seleccionar_empresa(
    request: Request,
    response: Response,
    body: EmpresaIdRequest,
    payload: Dict = Depends(require_selection_token_payload),
):
    client_type = get_client_type(request)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    try:
        session = await AuthService.seleccionar_empresa_post_login(
            payload=payload,
            empresa_id=body.empresa_id,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if not session.get("refresh_token"):
            return _access_only_token_response(session)
        return _session_token_http_response(response, request, session)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en POST /empresa/seleccionar/: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al seleccionar empresa",
        )


@router.post(
    "/empresa/cambiar/",
    response_model=Token,
    summary="Cambiar empresa activa en sesión",
    description="""
    Cambia la empresa activa sin re-login (selector en header ERP).

    **Autenticación:** Bearer access token de sesión normal (no selection token; 409 si pending).

    **Body:** `{ "empresa_id": "<uuid>" }`

    **Respuesta 200:** Nuevo access (+ refresh rotado en web/mobile), `user_data` actualizado.
    """,
)
async def cambiar_empresa(
    request: Request,
    response: Response,
    body: EmpresaIdRequest,
    payload: Dict = Depends(get_current_user_data),
):
    if is_impersonation_payload(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "No se puede cambiar de empresa durante una sesión de "
                "impersonación de soporte."
            ),
        )

    if payload.get("empresa_selection_pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Debe completar la selección de empresa con "
                "POST /api/v1/auth/empresa/seleccionar/ antes de cambiar de empresa."
            ),
        )

    client_type = get_client_type(request)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    old_refresh_token = None
    if client_type == "web":
        old_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    else:
        old_refresh_token = body.refresh_token

    try:
        session = await AuthService.cambiar_empresa_sesion(
            payload=payload,
            empresa_id=body.empresa_id,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            old_refresh_token=old_refresh_token,
        )
        return _session_token_http_response(response, request, session)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en POST /empresa/cambiar/: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar empresa",
        )


# ----
# --- Impersonación (soporte plataforma) ---
# ----

@router.post(
    "/impersonate/{cliente_id}/",
    response_model=Union[Token, LoginEmpresaSelectionResponse],
    summary="Iniciar sesión de soporte en un tenant (impersonación)",
    description="""
    Emite una sesión temporal (**120 min**, solo access token, sin refresh)
    para operar en el tenant indicado como soporte de plataforma.

    **Requisitos:** operador autenticado con privilegios de Super Administrador.
    **Claims:** `is_impersonation`, `impersonated_by`, `impersonated_by_username`.

    Si el tenant tiene más de una empresa activa, devuelve `selection_token`
    (mismo contrato que login multi-empresa) para completar con
    `POST /auth/empresa/seleccionar/`.
    """,
)
async def iniciar_impersonacion(
    request: Request,
    cliente_id: UUID = Path(..., description="UUID del tenant destino"),
    current_user=Depends(require_super_admin()),
    parent_payload: Dict = Depends(get_current_user_data),
):
    from app.core.auth.impersonate_auth_diag import log_impersonate_request_headers

    log_impersonate_request_headers(request, phase="endpoint_handler_deps_ok")
    logger.info(
        "[IMPERSONATE-AUTH] endpoint_handler target_cliente_id=%s operator=%s",
        cliente_id,
        getattr(current_user, "nombre_usuario", None),
    )

    if is_impersonation_payload(parent_payload):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se permite impersonación anidada",
        )

    parent_access = _extract_bearer_from_request(request)
    client_type = get_client_type(request)
    parent_refresh = None
    if client_type == "web":
        parent_refresh = request.cookies.get(settings.REFRESH_COOKIE_NAME)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        result = await ImpersonationService.iniciar_impersonacion(
            target_cliente_id=cliente_id,
            operator_usuario_id=current_user.usuario_id,
            operator_username=current_user.nombre_usuario,
            parent_access_token=parent_access,
            parent_refresh_token=parent_refresh,
            parent_payload=parent_payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if result["kind"] == "selection":
            return result["response"]
        return _access_only_token_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en POST /impersonate/{cliente_id}/: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar impersonación",
        )


@router.post(
    "/impersonate/end/",
    response_model=ImpersonationEndResponse,
    summary="Finalizar impersonación y restaurar sesión del operador",
    description="""
    Cierra la sesión de soporte (impersonación) y devuelve el access token
  (y refresh en móvil / cookie en web) de la sesión original del operador.

    **Auth:** Bearer con token de impersonación activo (`is_impersonation=true`).
    """,
)
async def finalizar_impersonacion(
    request: Request,
    response: Response,
    payload: Dict = Depends(get_current_user_data),
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    client_type = get_client_type(request)

    try:
        restored = await ImpersonationService.finalizar_impersonacion(
            payload=payload,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        refresh_token = restored.pop("refresh_token", None)
        if client_type == "web" and refresh_token:
            refresh_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=refresh_expire_days * 24 * 60 * 60,
                path="/",
                domain=settings.COOKIE_DOMAIN,
            )
        elif client_type == "mobile" and refresh_token:
            restored["refresh_token"] = refresh_token
        return ImpersonationEndResponse.model_validate(restored)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en POST /impersonate/end/: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al finalizar impersonación",
        )


# ----
# --- Endpoint para Obtener Usuario Actual (Me) ---
# ----
# app/api/v1/endpoints/auth.py (línea ~200)

@router.get(
    "/me/",
    response_model=MeResponse,
    summary="Obtener usuario actual"
)
async def get_me(
    _payload_ok: Dict = Depends(reject_selection_token_for_me),
    current_user=Depends(get_current_active_user),
):
    """
    Recupera los datos del usuario identificado por el Access Token.
    ✅ CORRECCIÓN CRÍTICA: Usar niveles del TOKEN, no recalcularlos.
    """
    payload = _payload_ok
    from app.core.auth.platform_user_lookup import is_system_request_client

    lookup_db = "tenant_routing"
    try:
        from app.core.tenant.context import try_get_current_client_id

        req_cid = try_get_current_client_id()
        if is_system_request_client(req_cid):
            lookup_db = "system_admin_then_bd_sistema_fallback"
    except Exception:
        pass

    logger.info(
        "[ME-ENDPOINT] payload=%s user_type=%s is_super_admin=%s es_superadmin=%s "
        "cliente_id=%s lookup_db=%s roles=%s",
        {k: payload.get(k) for k in (
            "sub", "user_type", "access_level", "cliente_id", "empresa_id",
            "es_superadmin", "is_super_admin",
        )},
        payload.get("user_type"),
        payload.get("is_super_admin"),
        payload.get("es_superadmin"),
        payload.get("cliente_id"),
        lookup_db,
        [
            getattr(r, "nombre", None) or (r.get("nombre") if isinstance(r, dict) else None)
            for r in (getattr(current_user, "roles", None) or [])
        ],
    )
    logger.info(f"Solicitud /me/ recibida para usuario: {current_user.nombre_usuario}")
    try:
        from app.core.tenant.empresa_context import coerce_empresa_id

        usuario_service = UsuarioService()

        user_id = current_user.usuario_id
        cliente_id = current_user.cliente_id
        if cliente_id is None and payload.get("cliente_id"):
            try:
                cliente_id = UUID(str(payload["cliente_id"]))
            except (ValueError, TypeError):
                pass

        empresa_activa_uuid = coerce_empresa_id(payload.get("empresa_id"))
        es_admin_cliente_me = bool(payload.get("es_admin_cliente", False))
        if empresa_activa_uuid is None:
            es_admin_cliente_me = await AuthService.usuario_tiene_es_admin_cliente(
                user_id, cliente_id, None
            )
        else:
            es_admin_cliente_me = await AuthService.usuario_tiene_es_admin_cliente(
                user_id, cliente_id, empresa_activa_uuid
            )

        token_access_level = payload.get("access_level")
        if token_access_level is not None:
            access_level_me = int(token_access_level)
        else:
            access_level_me = int(getattr(current_user, "access_level", 1))

        token_is_super_admin = payload.get("is_super_admin")
        token_user_type = payload.get("user_type")

        # Normalizar platform tras refresh: no degradar por roles tenant en SYSTEM
        system_cid = AuthService._coerce_uuid(settings.SUPERADMIN_CLIENTE_ID)
        session_cid = AuthService._coerce_uuid(
            str(cliente_id) if cliente_id is not None else payload.get("cliente_id")
        )
        if payload.get("es_superadmin") or (
            system_cid
            and session_cid == system_cid
            and (
                token_user_type == "platform_admin"
                or payload.get("access_level") == 5
                or token_is_super_admin
            )
        ):
            user_type_me = "platform_admin"
            is_super_admin_me = True
            access_level_me = max(access_level_me, 5)
        elif token_user_type:
            user_type_me = str(token_user_type)
            is_super_admin_me = bool(
                token_is_super_admin
                if token_is_super_admin is not None
                else getattr(current_user, "is_super_admin", False)
            )
        else:
            codigos_rol = []
            if hasattr(current_user, "roles") and current_user.roles:
                for rol in current_user.roles:
                    cod = getattr(rol, "codigo_rol", None) or (
                        rol.get("codigo_rol") if isinstance(rol, dict) else None
                    )
                    if cod:
                        codigos_rol.append(str(cod).strip().upper())

            if "ADMIN_PLATFORM" in codigos_rol or "SUPER_ADMIN" in codigos_rol:
                user_type_me = "platform_admin"
                is_super_admin_me = True
            elif "ADMIN_TENANT" in codigos_rol:
                user_type_me = "tenant_admin"
                is_super_admin_me = False
            else:
                user_type_me = getattr(current_user, "user_type", "user")
                is_super_admin_me = (
                    bool(token_is_super_admin)
                    if token_is_super_admin is not None
                    else getattr(current_user, "is_super_admin", False)
                )

        logger.info(
            f"[ME] Niveles - access_level={access_level_me}, "
            f"user_type={user_type_me}, is_super_admin={is_super_admin_me}"
        )

        from app.core.tenant.company_scope import resolve_role_list_scope

        list_scope = await resolve_role_list_scope(
            payload=payload,
            user_type=user_type_me,
            is_super_admin=is_super_admin_me,
        )
        usuario_completo = await usuario_service.obtener_usuario_completo_por_id(
            cliente_id,
            user_id,
            list_scope=list_scope,
        )

        if not usuario_completo:
            logger.error(f"Usuario {user_id} no encontrado en cliente {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Extraer nombres de roles (desde modelo o desde usuario_completo)
        role_names = []
        if hasattr(current_user, "roles") and current_user.roles:
            for rol in current_user.roles:
                name = getattr(rol, "nombre", None) or (rol.get("nombre") if isinstance(rol, dict) else None)
                if name:
                    role_names.append(name)
        if not role_names:
            for rol in usuario_completo.get("roles", []):
                if rol.get("nombre"):
                    role_names.append(rol["nombre"])
        role_names = list(dict.fromkeys(role_names))

        requiere_seleccion_me = False
        empresas_disponibles_me: Optional[List[EmpresaDisponible]] = None
        if empresa_activa_uuid is None and es_admin_cliente_me:
            empresa_ctx = await AuthService.get_empresa_activa_para_login(
                user_id, cliente_id
            )
            requiere_seleccion_me = bool(empresa_ctx.get("requiere_seleccion", False))
            empresas_ctx = empresa_ctx.get("empresas_disponibles") or []
            if empresas_ctx:
                empresas_disponibles_me = [
                    EmpresaDisponible.model_validate(e) for e in empresas_ctx
                ]

        user_profile = build_user_data_with_roles_dict(
            usuario_id=user_id,
            nombre_usuario=current_user.nombre_usuario,
            correo=getattr(current_user, "correo", None) or "",
            nombre=getattr(current_user, "nombre", None),
            apellido=getattr(current_user, "apellido", None),
            es_activo=getattr(current_user, "es_activo", True),
            roles=role_names,
            access_level=access_level_me,
            is_super_admin=is_super_admin_me,
            user_type=user_type_me,
            cliente_id=cliente_id,
            es_admin_cliente=es_admin_cliente_me,
            empresa_activa=(
                str(empresa_activa_uuid) if empresa_activa_uuid is not None else None
            ),
        )
        user_profile["empresa_activa"] = (
            str(empresa_activa_uuid) if empresa_activa_uuid is not None else None
        )

        logger.info(
            f"[ME] Datos completos enviados - Usuario: {current_user.nombre_usuario}, "
            f"user_type: {user_type_me}, is_super_admin: {is_super_admin_me}, Roles: {len(role_names)}"
        )
        imp_by = payload.get("impersonated_by")
        return MeResponse(
            **user_profile,
            requiere_seleccion_empresa=requiere_seleccion_me,
            empresas_disponibles=empresas_disponibles_me,
            is_impersonation=bool(payload.get("is_impersonation")),
            impersonated_by=str(imp_by) if imp_by is not None else None,
            impersonated_by_username=payload.get("impersonated_by_username"),
        )

    except HTTPException:
        raise
    except Exception as e:
        from app.core.exceptions import CustomException

        logger.error(
            "[ME-ENDPOINT] exception=%s:%s payload=%s user_type=%s is_super_admin=%s "
            "es_superadmin=%s cliente_id=%s lookup_db=%s",
            type(e).__name__,
            e,
            {k: payload.get(k) for k in (
                "sub", "user_type", "access_level", "cliente_id", "es_superadmin",
            )},
            payload.get("user_type"),
            payload.get("is_super_admin"),
            payload.get("es_superadmin"),
            payload.get("cliente_id"),
            lookup_db,
            exc_info=True,
        )
        if isinstance(e, CustomException):
            raise HTTPException(status_code=e.status_code, detail=e.detail) from e
        logger.exception(f"Error en /me/: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo datos del usuario"
        )


# ----
# --- GET /auth/permissions/me - Permisos resueltos (Permission Resolver)
# ----
@router.get(
    "/permissions/me",
    response_model=PermissionsMeResponse,
    summary="Obtener permisos del usuario actual",
    description="""
    Devuelve la lista plana de códigos de permiso del usuario autenticado en el tenant actual.
    
    **Fuente de verdad:** Permission Resolver centralizado (con cache Redis/memoria según configuración).
    **Multi-tenant:** Usa el tenant del token/contexto; no se pasan parámetros de tenant en la URL.
    **Uso frontend:** Consumir este endpoint para ocultar/mostrar acciones según permisos.
    
    **Formato:** `{"permissions": ["billing.read", "crm.access", ...]}`
    """,
)
async def get_permissions_me(
    current_user=Depends(require_erp_session),
    payload: Dict = Depends(require_full_session_payload),
):
    """
    Lista de permisos efectivos del usuario actual desde el Permission Resolver.
    Incluye cache (cuando PERMISSION_RESOLVER_CACHE_ENABLED=true) y es tenant-aware.
    """
    try:
        from app.core.authorization.permission_resolver import get_permission_resolver
        from app.core.tenant.context import try_get_tenant_context
        from app.core.auth.impersonation_rbac import (
            is_impersonation_effective_tenant_session,
            resolve_impersonation_tenant_cliente_id,
        )

        request_cliente_id = None
        try:
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            pass

        cliente_id = getattr(current_user, "cliente_id", None)
        if is_impersonation_effective_tenant_session(payload):
            cliente_id = resolve_impersonation_tenant_cliente_id(
                payload,
                user_cliente_id=cliente_id,
                request_cliente_id=request_cliente_id,
            )
        elif not cliente_id:
            if not request_cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Contexto de tenant no disponible",
                )
            cliente_id = request_cliente_id

        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        from app.core.auth.impersonation import suppress_platform_privileges

        is_super_admin, _, _ = suppress_platform_privileges(
            payload=payload,
            is_super_admin=getattr(current_user, "is_super_admin", False),
            user_type=getattr(current_user, "user_type", None),
            access_level=getattr(current_user, "access_level", None),
        )

        if is_super_admin:
            from sqlalchemy import text
            from app.infrastructure.database.connection_async import DatabaseConnection
            from app.infrastructure.database.queries_async import execute_query

            rows = await execute_query(
                text("SELECT codigo FROM permiso WHERE es_activo = 1"),
                connection_type=DatabaseConnection.ADMIN,
            )
            return PermissionsMeResponse(permissions=[r["codigo"] for r in rows if r.get("codigo")])

        from app.core.tenant.company_scope import resolve_empresa_id_for_rbac

        empresa_id = resolve_empresa_id_for_rbac(payload=payload)

        resolver = get_permission_resolver()
        effective = await resolver.get_effective_permissions(
            usuario_id=current_user.usuario_id,
            cliente_id=cliente_id,
            database_type=database_type,
            is_super_admin=is_super_admin,
            empresa_id=empresa_id,
            payload=payload,
            filter_by_subscription=getattr(
                settings, "PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION", False
            ),
        )
        return PermissionsMeResponse(permissions=list(effective.codes))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en GET /auth/permissions/me: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener permisos del usuario",
        )


# ----
# --- GET /auth/menu - Menú resuelto (Menu Resolver)
# ----
@router.get(
    "/menu",
    response_model=None,
    summary="Obtener menú del usuario actual",
    description="""
    Devuelve el menú de navegación del usuario autenticado ya filtrado por:
    - **Tenant:** módulos contratados (cliente_modulo).
    - **Permissions:** permisos efectivos del Permission Resolver.
    - **Configuración:** modulo_menu + rol_menu_permiso.
    
    Flujo: Tenant → Modules → Permissions → Menu.
    Misma estructura que GET /modulos-menus/me/; no reemplaza ese endpoint.
    """,
)
async def get_menu(
    current_user=Depends(require_erp_session),
    payload: Dict = Depends(require_full_session_payload),
):
    """
    Menú centralizado vía Menu Resolver (Permission Resolver + ModuloMenuService).
    Reutiliza cache del Permission Resolver.
    """
    try:
        from app.core.authorization.menu_resolver import get_menu_resolver
        from app.core.tenant.context import try_get_tenant_context

        request_cliente_id = None
        try:
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            pass

        from app.core.auth.impersonation_rbac import resolve_menu_cliente_id_for_session

        cliente_id = resolve_menu_cliente_id_for_session(
            payload=payload,
            user_cliente_id=getattr(current_user, "cliente_id", None),
            request_cliente_id=request_cliente_id,
        )
        if not cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contexto de tenant no disponible",
            )

        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        from app.core.auth.impersonation import suppress_platform_privileges

        is_super_admin, _, _access_level = suppress_platform_privileges(
            payload=payload,
            is_super_admin=getattr(current_user, "is_super_admin", False),
            user_type=getattr(current_user, "user_type", None),
            access_level=getattr(current_user, "access_level", None),
        )

        from app.core.tenant.company_scope import resolve_empresa_id_for_rbac

        empresa_id = resolve_empresa_id_for_rbac(payload=payload)

        menu_resolver = get_menu_resolver()
        menu = await menu_resolver.get_menu_for_user(
            usuario_id=current_user.usuario_id,
            cliente_id=cliente_id,
            database_type=database_type,
            is_super_admin=is_super_admin,
            as_tenant_admin=False,
            empresa_id=empresa_id,
            payload=payload,
        )
        return menu
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en GET /auth/menu: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener menú del usuario",
        )


# ----
# --- Endpoint para Refrescar Access Token ---
# ----
@router.post("/refresh/", response_model=Token)
async def refresh_access_token(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user_from_refresh)
):
    try:
        client_type = get_client_type(request)
        username = current_user.get("nombre_usuario")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no válido en el refresh token"
            )

        # === PASO 1: OBTENER EL REFRESH TOKEN ANTIGUO ===
        old_refresh_token = None
        if client_type == "web":
            old_refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
        else:  # mobile
            try:
                body = await request.json()
                old_refresh_token = body.get("refresh_token")
            except:
                pass

        if not old_refresh_token:
            logger.warning(f"[REFRESH] No se proporcionó refresh token - Usuario: {username} ({client_type})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token no proporcionado"
            )

        from app.core.security.jwt import decode_refresh_token

        try:
            refresh_payload = decode_refresh_token(old_refresh_token)
            if refresh_payload.get("is_impersonation"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "La sesión de impersonación no admite refresh. "
                        "Finalice la impersonación o vuelva a iniciar soporte en el tenant."
                    ),
                )
        except HTTPException:
            raise

        from app.core.tenant.empresa_context import coerce_empresa_id

        # Fuente de verdad: refresh_tokens.empresa_id (cargado en get_current_user_from_refresh)
        refresh_empresa_id = coerce_empresa_id(current_user.get("empresa_id"))
        refresh_usuario_id = current_user.get("usuario_id")
        refresh_cliente_id = current_user.get("cliente_id")

        level_info = await AuthService.resolve_level_info_for_token_refresh(
            refresh_payload=refresh_payload,
            username=username,
            usuario_id=refresh_usuario_id,
            cliente_id=refresh_cliente_id,
            empresa_id=refresh_empresa_id,
        )
        es_admin_cliente = await AuthService.usuario_tiene_es_admin_cliente(
            refresh_usuario_id,
            refresh_cliente_id,
            refresh_empresa_id,
            username=username,
        )

        token_expiration = await AuthService.get_token_expiration_for_cliente(refresh_cliente_id)
        access_expire_minutes = token_expiration["access_token_minutes"]
        refresh_expire_days = token_expiration["refresh_token_days"]
        refresh_cookie_max_age = refresh_expire_days * 24 * 60 * 60

        token_data = AuthService.build_token_data_from_level_info(
            username=username,
            cliente_id=current_user.get("cliente_id"),
            level_info=level_info,
            refresh_payload=refresh_payload,
        )

        new_access_token, new_access_jti = create_access_token(
            data=token_data,
            empresa_id=refresh_empresa_id,
            es_admin_cliente=es_admin_cliente,
            access_token_expire_minutes=access_expire_minutes,
        )
        new_refresh_token, new_refresh_jti = create_refresh_token(
            data=token_data,
            empresa_id=refresh_empresa_id,
            es_admin_cliente=es_admin_cliente,
            refresh_token_expire_days=refresh_expire_days,
        )

        # === PASO 2: GENERAR NUEVOS TOKENS ===
        #new_access_token = create_access_token(data={"sub": username})
        #new_refresh_token = create_refresh_token(data={"sub": username})

        # === PASO 3: ALMACENAR EL NUEVO TOKEN CON is_rotation=True ===
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            # ✅ Obtener cliente_id del contexto si no está en current_user
            cliente_id_for_token = current_user.get("cliente_id")
            if not cliente_id_for_token:
                from app.core.tenant.context import try_get_current_client_id
                cliente_id_for_token = try_get_current_client_id()
            
            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=cliente_id_for_token,
                usuario_id=current_user.get("usuario_id"),
                token=new_refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                is_rotation=True,
                empresa_id=refresh_empresa_id,
                refresh_token_expire_days=refresh_expire_days,
            )
            
            # === PASO 4: REVOCAR TOKEN ANTIGUO SOLO SI EL NUEVO SE GUARDÓ ===
            if stored and not stored.get('duplicate_ignored'):
                # Nuevo token guardado exitosamente, revocar el antiguo
                try:
                    revoked = await RefreshTokenService.revoke_token(
                        cliente_id=current_user.get("cliente_id"),
                        usuario_id=current_user.get("usuario_id"),
                        token=old_refresh_token
                    )
                    if revoked:
                        logger.info(f"[REFRESH] Token antiguo revocado después de rotación exitosa")
                    else:
                        logger.warning(f"[REFRESH] Token antiguo no encontrado para revocar (no crítico)")
                except Exception as revoke_err:
                    logger.warning(f"[REFRESH] Error revocando token antiguo (no crítico): {str(revoke_err)}")
            
            # Logging según resultado
            if stored and stored.get('token_id'):
                logger.info(f"[REFRESH-{client_type.upper()}] Token rotado exitosamente - ID: {stored['token_id']}")
            elif stored and stored.get('duplicate_ignored'):
                logger.info(f"[REFRESH-{client_type.upper()}] Duplicado ignorado (doble refresh simultáneo)")
            else:
                logger.warning(f"[REFRESH-{client_type.upper()}] Almacenamiento devolvió resultado inesperado")
                
        except AuthenticationError:
            # Si hay error de seguridad (reuso real), propagar
            raise
        except Exception as e:
            logger.error(f"[REFRESH] Error en rotación de token: {str(e)}")
            # Si falla el almacenamiento, NO continuar con el refresh
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al rotar el refresh token"
            )

        # === PASO 5: PREPARAR RESPUESTA ===
        response_data = {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user_data": None
        }
        
        if client_type == "web":
            # WEB: Nuevo refresh en cookie
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=new_refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=refresh_cookie_max_age,
                path="/",
                domain=settings.COOKIE_DOMAIN,
            )
            logger.info(f"[REFRESH-WEB] Token refrescado exitosamente - Usuario: {username}")
        else:  # mobile
            # MÓVIL: Nuevo refresh en JSON
            response_data["refresh_token"] = new_refresh_token
            logger.info(f"[REFRESH-MOBILE] Token refrescado exitosamente - Usuario: {username}")
        
        # Registrar refresh exitoso en auditoría (no bloquear flujo si falla)
        try:
            # ✅ Obtener cliente_id del contexto si no está en current_user
            cliente_id_for_audit = current_user.get("cliente_id")
            if not cliente_id_for_audit:
                from app.core.tenant.context import try_get_current_client_id
                cliente_id_for_audit = try_get_current_client_id()
            
            await AuditService.registrar_auth_event(
                cliente_id=cliente_id_for_audit,
                usuario_id=current_user.get("usuario_id"),
                evento="token_refresh",
                nombre_usuario_intento=username,
                descripcion="Refresh de token exitoso",
                exito=True,
                codigo_error=None,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "client_type": client_type,
                },
            )
        except Exception:
            logger.exception(
                "[AUDIT] Error registrando evento token_refresh (no crítico)"
            )

        return response_data
        
    except HTTPException:
        raise
    except AuthenticationError:
        # Convertir AuthenticationError a HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación durante el refresh"
        )
    except Exception as e:
        logger.exception(f"[REFRESH] Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al refrescar el token"
        )

# ----
# --- Endpoint para Cerrar Sesión (Logout) ---
# ----
@router.post("/logout", include_in_schema=False)
@router.post(
    "/logout/",
    summary="Cerrar sesión",
    description="""
    Cierra sesión de forma **idempotente** (siempre 200).

    **Revocación en BD:**
    - Lee el refresh desde cookie HttpOnly (web) o body `refresh_token` (mobile).
    - Marca `refresh_tokens.is_revoked = 1` y `revoked_at` para ese hash.
    - Usa `cliente_id` del JWT refresh (válido para platform y tenant).

    **Cliente web:** limpia cookies de refresh (y access si aplica).

    **Opcional:** si envía `Authorization: Bearer <access>`, blacklistea el `jti` del access.

    No requiere access token para revocar el refresh en BD.
    """
)
async def logout(request: Request, response: Response):
    """
    Logout: revoca refresh en BD + limpia cookies. Idempotente (200 siempre).
    """
    client_type = get_client_type(request)

    try:
        await AuthService.perform_logout(request=request, client_type=client_type)
    except Exception as e:
        logger.warning("[LOGOUT] perform_logout falló (fail-soft): %s", e)

    try:
        response.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
        response.delete_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            path="/",
            samesite=settings.COOKIE_SAMESITE,
            domain=settings.COOKIE_DOMAIN,
        )
    except Exception:
        pass

    return {"message": "Logout successful"}

# ----
# --- NUEVOS Endpoints para Gestión de Sesiones ---
# ----

@router.get(
    "/sessions/",
    response_model=List[Dict], # Retorna una lista de diccionarios de la BD (asumiendo estructura: token_id, client_type, ip_address, created_at, etc.)
    summary="Listar sesiones activas",
    description="""
    Retorna una lista de todas las sesiones activas del usuario, usando el Access Token para identificar al usuario. 
    Ideal para mostrar al usuario dónde ha iniciado sesión (auditoría).

    **Permisos requeridos:**
    - Autenticación (Access Token válido).

    **Respuestas:**
    - 200: Lista de sesiones activas.
    - 401: Token inválido o expirado.
    """
)
async def get_active_sessions_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Obtiene la lista de sesiones activas para el usuario actual.

    Args:
        current_user: Diccionario con los datos del usuario.

    Returns:
        List[Dict]: Lista de diccionarios que representan las sesiones.
    """
    user_id = current_user.get('usuario_id')
    cliente_id = current_user.get('cliente_id')
    username = current_user.get('nombre_usuario')
    logger.info(f"Solicitud /sessions/ recibida para usuario: {username}")
    try:
        sessions = await RefreshTokenService.get_active_sessions(cliente_id=cliente_id, usuario_id=user_id)
        # Asegurarse de que el servicio no devuelva el hash del token por seguridad.
        return sessions
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en /sessions/ para {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo sesiones activas"
        )


@router.post(
    "/logout_all/",
    summary="Cerrar todas las sesiones (Logout global)",
    description="""
    Revoca **todos** los Refresh Tokens activos del usuario en la base de datos, 
    forzando el cierre de sesión en todos los dispositivos. 
    Requiere un Access Token válido.

    **Nota:** Después de esta llamada, el Access Token actual seguirá siendo válido hasta que expire, 
    pero no podrá ser renovado. Se recomienda redirigir al usuario al login inmediatamente.

    **Respuestas:**
    - 200: Todas las sesiones (tokens) han sido revocadas.
    - 401: Token inválido o expirado.
    """
)
async def logout_all_sessions(current_user: dict = Depends(get_current_user)):
    """
    Revoca todos los refresh tokens activos para el usuario actual.

    Args:
        current_user: Diccionario con los datos del usuario.

    Returns:
        Dict[str, str]: Mensaje de éxito con el número de sesiones cerradas.
    """
    user_id = current_user.get('usuario_id')
    cliente_id = current_user.get('cliente_id')
    username = current_user.get('nombre_usuario')
    logger.info(f"Solicitud /logout_all/ recibida para usuario: {username}")
    try:
        rows_affected = await RefreshTokenService.revoke_all_user_tokens(
            cliente_id=cliente_id, usuario_id=user_id
        )

        # Registrar logout global en auditoría
        try:
            await AuditService.registrar_auth_event(
                cliente_id=cliente_id,
                usuario_id=user_id,
                evento="logout_forced",
                nombre_usuario_intento=username,
                descripcion="Logout global de todas las sesiones del usuario",
                exito=True,
                codigo_error=None,
                ip_address=None,
                user_agent=None,
                metadata={"revoked_sessions": rows_affected},
            )
        except Exception:
            logger.exception(
                "[AUDIT] Error registrando evento logout_forced (no crítico)"
            )

        return {
            "message": f"Se han cerrado {rows_affected} sesiones activas para el usuario {username}."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en /logout_all/ para {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar todas las sesiones"
        )

# ----
# --- NUEVOS Endpoints para ADMINISTRACIÓN (Requiere Rol 'Administrador') ---
# ----

@router.get(
    "/sessions/admin/",
    response_model=List[Dict],
    summary="[ADMIN] Listar TODAS las sesiones activas del sistema",
    description="""
    Retorna una lista de todas las sesiones activas (refresh tokens) en el sistema.
    Incluye detalles como nombre de usuario, tipo de cliente, IP, y fechas de creación/expiración.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Lista de sesiones activas del sistema.
    - 403: Permiso denegado.
    - 500: Error interno del servidor.
    """,
    dependencies=[Depends(require_admin)]
)
async def admin_list_all_active_sessions(current_user: dict = Depends(get_current_user)):
    """
    Obtiene la lista global de todas las sesiones activas en el sistema para auditoría.
    
    Args:
        current_user: Usuario que realiza la petición (solo para logging, ya validado por RoleChecker).

    Returns:
        List[Dict]: Lista de diccionarios que representan todas las sesiones activas.
    """
    cliente_id = current_user.get("cliente_id")
    username = current_user.get('nombre_usuario', 'N/A')
    logger.info(f"[ADMIN] Solicitud /sessions/admin/ por usuario: {username}")
    try:
        sessions = await RefreshTokenService.get_all_active_sessions_for_admin(cliente_id=cliente_id)
        
        logger.info(f"[ADMIN] Recuperadas {len(sessions)} sesiones activas totales.")
        return sessions
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ADMIN] Error en /sessions/admin/ (usuario: {username}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la lista global de sesiones activas."
        )


@router.post(
    "/sessions/{token_id}/revoke_admin/",
    summary="[ADMIN] Revocar sesión activa por ID",
    description="""
    Permite a un administrador revocar (cerrar) una sesión activa específica
    utilizando su `token_id` (ID primario en la tabla `refresh_tokens`).

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Parámetros de ruta:**
    - token_id: ID numérico del refresh token a revocar.

    **Respuestas:**
    - 200: Sesión revocada exitosamente.
    - 404: Token ID no encontrado o ya revocado.
    - 403: Permiso denegado.
    - 500: Error interno del servidor.
    """,
    dependencies=[Depends(require_admin)]
)
async def admin_revoke_session_by_id(
    token_id: UUID = Path(..., description="ID del token de sesión a revocar (PK en refresh_tokens)"), 
    current_user: dict = Depends(get_current_user) # Para contexto/logging
):
    """
    Revoca un refresh token específico por su ID.

    Args:
        token_id: ID numérico del token a revocar.
        current_user: Usuario que realiza la petición (solo para logging).

    Returns:
        Dict[str, str]: Mensaje de éxito.

    Raises:
        HTTPException: En caso de errores de autorización, no encontrado o interno.
    """
    username = current_user.get('nombre_usuario', 'N/A')
    logger.info(f"[ADMIN] Solicitud de revocación de Token ID {token_id} por: {username}")
    
    try:
        revoked = await RefreshTokenService.revoke_refresh_token_by_id(token_id=token_id)
        
        if revoked:
            logger.info(f"[ADMIN-REVOKE] Token ID {token_id} revocado exitosamente por {username}.")
            return {"message": f"Sesión (Token ID: {token_id}) revocada exitosamente."}
        else:
            logger.warning(f"[ADMIN-REVOKE] Intento de revocación fallido: Token ID {token_id} no encontrado o ya inactivo.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El token ID {token_id} no se encontró activo o ya ha sido revocado."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ADMIN-REVOKE] Error inesperado revocando Token ID {token_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al revocar la sesión."
        )


@router.post(
    "/admin/cleanup-expired-tokens/",
    summary="[ADMIN] Limpiar tokens expirados en todos los tenants",
    description="""
    Ejecuta cleanup de tokens expirados y revocados en todos los tenants activos del sistema.
    
    **✅ FASE 4: Endpoint administrativo para cleanup global de tokens.**
    
    Este endpoint:
    - Itera todos los tenants activos
    - Ejecuta cleanup para cada tenant (Single-DB y Multi-DB)
    - Retorna estadísticas detalladas del proceso
    
    **Permisos requeridos:**
    - Rol 'Administrador'
    
    **Respuestas:**
    - 200: Cleanup completado con estadísticas.
    - 403: Permiso denegado.
    - 500: Error interno del servidor.
    """,
    dependencies=[Depends(require_admin)]
)
async def admin_cleanup_expired_tokens_all_tenants(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint administrativo para limpiar tokens expirados en todos los tenants.
    Solo accesible para administradores.
    
    ✅ FASE 4: Ejecuta RefreshTokenCleanupJob.cleanup_all_tenants()
    """
    username = current_user.get('nombre_usuario', 'N/A')
    logger.info(f"[ADMIN] Solicitud /admin/cleanup-expired-tokens/ por usuario: {username}")
    
    try:
        from app.modules.auth.application.services.refresh_token_cleanup_job import RefreshTokenCleanupJob
        
        stats = await RefreshTokenCleanupJob.cleanup_all_tenants()
        
        logger.info(
            f"[ADMIN-CLEANUP] Completado por {username}: "
            f"{stats['tenants_processed']} tenants, {stats['tokens_deleted']} tokens eliminados"
        )
        
        return {
            "status": "completed",
            "message": f"Cleanup completado: {stats['tenants_processed']} tenants procesados, "
                      f"{stats['tokens_deleted']} tokens eliminados",
            "stats": stats
        }
    
    except Exception as e:
        logger.exception(f"[ADMIN-CLEANUP] Error en cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ejecutar cleanup de tokens: {str(e)}"
        )


# === ENDPOINTS PARA SSO (NUEVOS) ===

@router.post(
    "/sso/azure/",
    response_model=Token,
    summary="Autenticar usuario mediante Azure AD",
    description="""
    Inicia el flujo de autenticación con Azure Active Directory.
    **En esta primera fase, el endpoint recibe el id_token de Azure y autentica al usuario.**
    
    **Flujo:**
    1. El frontend obtiene el id_token desde Azure AD.
    2. El frontend envía el id_token a este endpoint junto con el contexto del cliente.
    3. El backend valida el id_token y autentica al usuario.
    
    **Parámetros en el cuerpo:**
    - `id_token`: El JWT token de Azure AD.
    - `cliente_id` o `subdominio`: Para identificar el cliente.
    
    **Respuestas:**
    - 200: Autenticación SSO exitosa.
    - 400: Parámetros inválidos.
    - 401: Token de Azure inválido o cliente no autorizado.
    - 500: Error interno.
    """
)
async def sso_azure_login(
    request: Request,
    response: Response,
    id_token: str = Body(..., embed=True),
    cliente_id: Optional[UUID] = Body(None),
    subdominio: Optional[str] = Body(None)
):
    """
    Autentica a un usuario utilizando un token de Azure AD.
    """
    try:
        # Resolver cliente_id desde contexto o parámetros
        try:
            # Intentar obtener desde el contexto del middleware
            cliente_id = get_current_client_id()
        except RuntimeError:
            # Si no está en el contexto, resolver desde subdominio o usar el proporcionado
            if not cliente_id and subdominio:
                query = "SELECT cliente_id FROM cliente WHERE subdominio = ? AND es_activo = 1"
                with get_db_connection(DatabaseConnection.ADMIN) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (subdominio,))
                    row = cursor.fetchone()
                    if row:
                        cliente_id = row[0]
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Cliente con subdominio '{subdominio}' no encontrado."
                        )
            elif not cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Se requiere cliente_id o subdominio, o acceso desde subdominio válido."
                )
        
        client_type = get_client_type(request)
        
        # Autenticar con SSO
        user_base_data = await authenticate_user_sso_azure_ad(cliente_id, id_token)
        
        # Continuar con el flujo normal de generación de tokens
        user_id = user_base_data.get('usuario_id')
        user_role_names = await UsuarioService.get_user_role_names(cliente_id, user_id)
        user_full_data = {**user_base_data, "roles": user_role_names}

        # ✅ FASE 1: Construir payload completo con cliente_id y level_info (igual que login password)
        from app.core.security.jwt import build_token_payload_for_sso
        token_payload = await build_token_payload_for_sso(
            user_full_data=user_full_data,
            cliente_id=cliente_id,
            user_role_names=user_role_names
        )

        token_expiration = await AuthService.get_token_expiration_for_cliente(cliente_id)
        access_expire_minutes = token_expiration["access_token_minutes"]
        refresh_expire_days = token_expiration["refresh_token_days"]
        refresh_cookie_max_age = refresh_expire_days * 24 * 60 * 60
        
        access_token, access_jti = create_access_token(
            data=token_payload,
            access_token_expire_minutes=access_expire_minutes,
        )
        refresh_token, refresh_jti = create_refresh_token(
            data=token_payload,
            refresh_token_expire_days=refresh_expire_days,
        )

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await RefreshTokenService.store_refresh_token(
            cliente_id=cliente_id,
            usuario_id=user_id,
            token=refresh_token,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            refresh_token_expire_days=refresh_expire_days,
        )

        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": user_full_data
        }
        
        if client_type == "web":
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=refresh_cookie_max_age,
                path="/",
                domain=settings.COOKIE_DOMAIN,
            )
        else:
            response_data["refresh_token"] = refresh_token

        return response_data

    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Autenticación SSO con Azure AD no implementada aún."
        )
    except Exception as e:
        logger.exception(f"Error en /sso/azure/: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación SSO con Azure AD."
        )


@router.post(
    "/sso/google/",
    response_model=Token,
    summary="Autenticar usuario mediante Google Workspace",
    description="""
    Inicia el flujo de autenticación con Google Workspace.
    **En esta primera fase, el endpoint recibe el id_token de Google y autentica al usuario.**
    
    **Flujo:**
    1. El frontend obtiene el id_token desde Google.
    2. El frontend envía el id_token a este endpoint junto con el contexto del cliente.
    3. El backend valida el id_token y autentica al usuario.
    
    **Parámetros en el cuerpo:**
    - `id_token`: El JWT token de Google.
    - `cliente_id` o `subdominio`: Para identificar el cliente.
    
    **Respuestas:**
    - 200: Autenticación SSO exitosa.
    - 400: Parámetros inválidos.
    - 401: Token de Google inválido o cliente no autorizado.
    - 500: Error interno.
    """
)
async def sso_google_login(
    request: Request,
    response: Response,
    id_token: str = Body(..., embed=True),
    cliente_id: Optional[UUID] = Body(None),
    subdominio: Optional[str] = Body(None)
):
    """
    Autentica a un usuario utilizando un token de Google Workspace.
    """
    try:
        # Resolver cliente_id desde contexto o parámetros
        try:
            # Intentar obtener desde el contexto del middleware
            cliente_id = get_current_client_id()
        except RuntimeError:
            # Si no está en el contexto, resolver desde subdominio o usar el proporcionado
            if not cliente_id and subdominio:
                query = "SELECT cliente_id FROM cliente WHERE subdominio = ? AND es_activo = 1"
                with get_db_connection(DatabaseConnection.ADMIN) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (subdominio,))
                    row = cursor.fetchone()
                    if row:
                        cliente_id = row[0]
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Cliente con subdominio '{subdominio}' no encontrado."
                        )
            elif not cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Se requiere cliente_id o subdominio, o acceso desde subdominio válido."
                )
        
        client_type = get_client_type(request)
        
        # Autenticar con SSO
        user_base_data = await authenticate_user_sso_google(cliente_id, id_token)
        
        # Continuar con el flujo normal de generación de tokens
        user_id = user_base_data.get('usuario_id')
        user_role_names = await UsuarioService.get_user_role_names(cliente_id, user_id)
        user_full_data = {**user_base_data, "roles": user_role_names}

        # ✅ FASE 1: Construir payload completo con cliente_id y level_info (igual que login password)
        from app.core.security.jwt import build_token_payload_for_sso
        token_payload = await build_token_payload_for_sso(
            user_full_data=user_full_data,
            cliente_id=cliente_id,
            user_role_names=user_role_names
        )

        token_expiration = await AuthService.get_token_expiration_for_cliente(cliente_id)
        access_expire_minutes = token_expiration["access_token_minutes"]
        refresh_expire_days = token_expiration["refresh_token_days"]
        refresh_cookie_max_age = refresh_expire_days * 24 * 60 * 60
        
        access_token, access_jti = create_access_token(
            data=token_payload,
            access_token_expire_minutes=access_expire_minutes,
        )
        refresh_token, refresh_jti = create_refresh_token(
            data=token_payload,
            refresh_token_expire_days=refresh_expire_days,
        )

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await RefreshTokenService.store_refresh_token(
            cliente_id=cliente_id,
            usuario_id=user_id,
            token=refresh_token,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent,
            refresh_token_expire_days=refresh_expire_days,
        )

        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": user_full_data
        }
        
        if client_type == "web":
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=refresh_cookie_max_age,
                path="/",
                domain=settings.COOKIE_DOMAIN,
            )
        else:
            response_data["refresh_token"] = refresh_token

        return response_data

    except HTTPException:
        raise
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Autenticación SSO con Google no implementada aún."
        )
    except Exception as e:
        logger.exception(f"Error en /sso/google/: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación SSO con Google."
        )