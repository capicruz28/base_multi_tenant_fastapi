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
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Path, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.core.auth import get_user_access_level_info

# Importar la función que lee el ContextVar del cliente (¡Asume que está definida!)
from app.core.tenant.context import get_current_client_id 

from app.modules.auth.presentation.schemas import Token, UserDataWithRoles, LoginData
from app.core.auth import (
    authenticate_user,
    get_current_user,
    get_current_user_from_refresh,
    authenticate_user_sso_azure_ad,
    authenticate_user_sso_google
)
from app.core.security.jwt import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.logging_config import get_logger
from app.modules.users.application.services.user_service import UsuarioService
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.tenant.application.services.cliente_service import ClienteService
from app.modules.superadmin.application.services.audit_service import AuditService
from app.api.deps import RoleChecker
from app.core.exceptions import AuthenticationError
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

# ----
# --- Endpoint para Login ---
# ----
# ✅ FASE 1: Rate limiting en login (aplicado correctamente para FastAPI)
# El decorador se aplica después del router.post para que funcione correctamente
@router.post(
    "/login/",
    response_model=Token,
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
        target_cliente_id = user_base_data.get('target_cliente_id', cliente_id)
        
        # Para superadmin, podría no tener roles en el cliente destino
        if es_superadmin:
            user_role_names = ["Super Administrador"]  # Rol implícito
            logger.info(f"[LOGIN] Superadmin accediendo a cliente_id={target_cliente_id}")
        else:
            user_role_names = await UsuarioService.get_user_role_names(cliente_id, user_id)
        
        user_full_data = {**user_base_data, "roles": user_role_names}

        # 6. ✅ Tokens con contexto correcto
        level_info = get_user_access_level_info(user_id, target_cliente_id)
        token_data = {
            "sub": form_data.username,
            "cliente_id": target_cliente_id,  # Cliente al que accede
            "level_info": level_info 
        }
        
        if es_superadmin:
            token_data["es_superadmin"] = True
        
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        # ✅ CORRECCIÓN: Almacenar en el cliente destino
        try:
            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=target_cliente_id,
                usuario_id=user_id,
                token=refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                is_rotation=False  # ✅ CRÍTICO: False porque es un login nuevo
            )
            
            if stored and stored.get('token_id', -1) > 0:
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
            "user_data": user_full_data
        }
        
        if client_type == "web":
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
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
    except Exception as e:
        logger.exception(f"Error inesperado en /login/ para usuario {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado durante el proceso de login."
        )


# ----
# --- Endpoint para Obtener Usuario Actual (Me) ---
# ----
# app/api/v1/endpoints/auth.py (línea ~200)

@router.get(
    "/me/",
    response_model=UserDataWithRoles,
    summary="Obtener usuario actual"
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Recupera los datos del usuario identificado por el Access Token.
    ✅ CORRECCIÓN CRÍTICA: Usar niveles del TOKEN, no recalcularlos
    """
    logger.info(f"Solicitud /me/ recibida para usuario: {current_user.get('nombre_usuario')}")
    try:
        usuario_service = UsuarioService()
        user_id = current_user.get('usuario_id')
        cliente_id = current_user.get('cliente_id')
        
        # ✅ CRÍTICO: Leer niveles DESDE EL TOKEN (ya vienen correctos)
        access_level_from_token = current_user.get('access_level', 1)
        is_super_admin_from_token = current_user.get('is_super_admin', False)
        user_type_from_token = current_user.get('user_type', 'user')
        
        logger.info(
            f"[ME] Niveles desde token - Level: {access_level_from_token}, "
            f"Super Admin: {is_super_admin_from_token}, Type: {user_type_from_token}"
        )
        
        usuario_completo = await usuario_service.obtener_usuario_completo_por_id(cliente_id, user_id)
        
        if not usuario_completo:
            logger.error(f"Usuario {user_id} no encontrado en cliente {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Extraer nombres de roles
        role_names = []
        for rol in usuario_completo.get("roles", []):
            if rol.get("nombre"):
                role_names.append(rol["nombre"])
        
        # ✅ CORRECCIÓN CRÍTICA: Usar valores del TOKEN, NO recalcular
        user_full_data = {
            **current_user,  # Incluye los datos básicos del token
            "roles": role_names,
            "tipo_usuario": user_type_from_token,  # ✅ DEL TOKEN
            "es_super_admin": is_super_admin_from_token,  # ✅ DEL TOKEN
            "es_tenant_admin": access_level_from_token >= 4 and not is_super_admin_from_token,
            "cliente": usuario_completo.get("cliente_info"),
            "modulos_activos": usuario_completo.get("modulos_activos", []),
            # ✅ CRÍTICO: Estos campos deben venir del TOKEN
            "access_level": access_level_from_token,  # ✅ DEL TOKEN
            "is_super_admin": is_super_admin_from_token,  # ✅ DEL TOKEN
            "user_type": user_type_from_token  # ✅ DEL TOKEN
        }
        
        logger.info(
            f"[ME] Datos completos enviados - Usuario: {current_user.get('nombre_usuario')}, "
            f"Type: {user_type_from_token}, Level: {access_level_from_token}, "
            f"Super Admin: {is_super_admin_from_token}, Roles: {len(role_names)}"
        )
        return user_full_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en /me/: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo datos del usuario"
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

        level_info = get_user_access_level_info(
            current_user.get("usuario_id"),
            current_user.get("cliente_id")
        )

        token_data = {
            "sub": username,
            "cliente_id": current_user.get("cliente_id"),
            "level_info": level_info  # ✅ AGREGAR ESTO
        }

        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)    

        # === PASO 2: GENERAR NUEVOS TOKENS ===
        #new_access_token = create_access_token(data={"sub": username})
        #new_refresh_token = create_refresh_token(data={"sub": username})

        # === PASO 3: ALMACENAR EL NUEVO TOKEN CON is_rotation=True ===
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=current_user.get("cliente_id"),
                usuario_id=current_user.get("usuario_id"),
                token=new_refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
                is_rotation=True  # ✅ CRÍTICO: True porque es una rotación
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
            if stored and stored.get('token_id', -1) > 0:
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
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
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
            await AuditService.registrar_auth_event(
                cliente_id=current_user.get("cliente_id"),
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
@router.post(
    "/logout/",
    summary="Cerrar sesión",
    description="""
    Cierra la sesión del usuario revocando el **Refresh Token** en BD.
    
    **✅ NUEVO - Estrategia según cliente:**
    - **Web (X-Client-Type: web):** Elimina cookie y revoca token en BD
    - **Móvil (X-Client-Type: mobile):** Revoca token en BD

    **Respuestas:**
    - 200: Sesión cerrada exitosamente.
    """
)
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    Cierra sesión revocando el refresh token en BD.

    Args:
        request: Objeto Request para detectar tipo de cliente
        response: Objeto Response de FastAPI para manipular cookies.
        current_user: Diccionario con datos del usuario autenticado (proporciona cliente_id y usuario_id)

    Returns:
        Dict[str, str]: Mensaje de éxito.

    Raises:
        HTTPException: En caso de error al cerrar sesión
    """
    try:
        # ✅ NUEVO: Detectar tipo de cliente
        client_type = get_client_type(request)
        
        # ✅ INYECCIÓN: Obtener cliente_id y usuario_id del contexto actual
        cliente_id = current_user.get("cliente_id")
        usuario_id = current_user.get("usuario_id")
        username = current_user.get("nombre_usuario")
        
        if not cliente_id or not usuario_id:
            logger.warning(f"[LOGOUT] Datos de cliente/usuario inválidos para {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contexto de usuario inválido"
            )
        
        # Obtener refresh token
        refresh_token = None
        if client_type == "web":
            refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
            # Eliminar cookie
            response.delete_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                path="/",
                samesite=settings.COOKIE_SAMESITE,
                domain=settings.COOKIE_DOMAIN,
            )
        else:  # mobile
            try:
                body = await request.json()
                refresh_token = body.get("refresh_token")
            except:
                pass
        
        # ✅ REFACTORIZADO: Revocar token en BD con cliente_id y usuario_id
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        if refresh_token:
            try:
                revoked = await RefreshTokenService.revoke_token(
                    cliente_id=cliente_id,
                    usuario_id=usuario_id,
                    token=refresh_token
                )
                if revoked:
                    logger.info(
                        f"[LOGOUT-{client_type.upper()}] Token revocado exitosamente - "
                        f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
                    )
                else:
                    # Token no encontrado (ya expirado/revocado) - NO es error, sesión ya cerrada
                    logger.info(
                        f"[LOGOUT-{client_type.upper()}] Token no encontrado en BD (ya expirado/revocado) - "
                        f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
                    )
                
                # Registrar logout como EXITO siempre (token encontrado o no, la sesión está cerrada)
                # Solo será error si hay una excepción real al revocar (capturada abajo)
                try:
                    await AuditService.registrar_auth_event(
                        cliente_id=cliente_id,
                        usuario_id=usuario_id,
                        evento="logout",
                        nombre_usuario_intento=username,
                        descripcion="Logout de sesión",
                        exito=True,  # ✅ SIEMPRE éxito: token revocado o ya no existe
                        codigo_error=None,  # ✅ NUNCA error para token no encontrado
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "client_type": client_type,
                            "token_revoked": revoked,  # Info adicional: si se revocó o ya no existía
                        },
                    )
                except Exception:
                    logger.exception(
                        "[AUDIT] Error registrando evento logout (no crítico)"
                    )
            except Exception as revoke_error:
                # ✅ SOLO AQUÍ es un error real: excepción al intentar revocar
                logger.error(
                    f"[LOGOUT-{client_type.upper()}] Error al revocar token - "
                    f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username}): {str(revoke_error)}"
                )
                # Registrar como error solo si hay excepción real
                try:
                    await AuditService.registrar_auth_event(
                        cliente_id=cliente_id,
                        usuario_id=usuario_id,
                        evento="logout",
                        nombre_usuario_intento=username,
                        descripcion="Error al revocar token durante logout",
                        exito=False,
                        codigo_error=f"REVOKE_ERROR: {str(revoke_error)[:100]}",  # Limitar longitud
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "client_type": client_type,
                            "error_type": type(revoke_error).__name__,
                        },
                    )
                except Exception:
                    logger.exception(
                        "[AUDIT] Error registrando evento logout con error (no crítico)"
                    )
                # No propagar el error, el logout sigue siendo exitoso desde el punto de vista del usuario
        else:
            # No se proporcionó refresh token (None) - NO es error, logout válido
            logger.info(
                f"[LOGOUT-{client_type.upper()}] Logout sin refresh token proporcionado - "
                f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
            )
            # Registrar logout exitoso sin token
            try:
                await AuditService.registrar_auth_event(
                    cliente_id=cliente_id,
                    usuario_id=usuario_id,
                    evento="logout",
                    nombre_usuario_intento=username,
                    descripcion="Logout de sesión (sin refresh token)",
                    exito=True,  # ✅ Éxito: logout válido sin token
                    codigo_error=None,  # ✅ NO es error
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "client_type": client_type,
                        "no_token_provided": True,
                    },
                )
            except Exception:
                logger.exception(
                    "[AUDIT] Error registrando evento logout sin token (no crítico)"
                )
        
        return {"message": f"Sesión cerrada exitosamente ({client_type})"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar sesión"
        )

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
    token_id: int = Path(..., description="ID del token de sesión a revocar (PK en refresh_tokens)"), 
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
    cliente_id: Optional[int] = Body(None),
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

        access_token = create_access_token(data={"sub": user_full_data['nombre_usuario']})
        refresh_token = create_refresh_token(data={"sub": user_full_data['nombre_usuario']})

        # Almacenar refresh token
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await RefreshTokenService.store_refresh_token(
            cliente_id=cliente_id,
            usuario_id=user_id,
            token=refresh_token,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent
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
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
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
    cliente_id: Optional[int] = Body(None),
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

        access_token = create_access_token(data={"sub": user_full_data['nombre_usuario']})
        refresh_token = create_refresh_token(data={"sub": user_full_data['nombre_usuario']})

        # Almacenar refresh token
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await RefreshTokenService.store_refresh_token(
            cliente_id=cliente_id,
            usuario_id=user_id,
            token=refresh_token,
            client_type=client_type,
            ip_address=ip_address,
            user_agent=user_agent
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
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
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