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

# Importar la función que lee el ContextVar del cliente (¡Asume que está definida!)
from app.core.tenant_context import get_current_client_id 

from app.schemas.auth import Token, UserDataWithRoles, LoginData
from app.core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh,
    authenticate_user_sso_azure_ad,
    authenticate_user_sso_google
)
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.usuario_service import UsuarioService
from app.services.refresh_token_service import RefreshTokenService
from app.services.cliente_service import ClienteService
from app.api.deps import RoleChecker

router = APIRouter()
logger = get_logger(__name__)

# Dependencia específica para requerir rol 'admin'
require_admin = RoleChecker(["Super Administrador"])

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
    - 500: Error interno del servidor.
    """
)
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
        
        # 4. Autenticación (maneja 401 si falla)
        user_base_data = await authenticate_user(cliente_id, form_data.username, form_data.password)

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
        token_data = {
            "sub": form_data.username,
            "cliente_id": target_cliente_id  # Cliente al que accede
        }
        
        if es_superadmin:
            token_data["es_superadmin"] = True
        
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        # ✅ CORRECCIÓN: Almacenar en el cliente destino
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=target_cliente_id,  # ✅ Cliente al que accede
                usuario_id=user_id,
                token=refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if stored and stored.get('token_id', -1) > 0:
                logger.info(f"[LOGIN-{client_type.upper()}] Token almacenado en BD - ID: {stored['token_id']}")
            else:
                logger.warning(f"[LOGIN-{client_type.upper()}] Token duplicado ignorado (no afecta funcionalidad)")
                
        except Exception as e:
            logger.error(f"Error almacenando refresh token: {str(e)}")
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
@router.get(
    "/me/",
    response_model=UserDataWithRoles,
    summary="Obtener usuario actual",
    description="""
    Retorna los datos completos del usuario autenticado, incluyendo roles y metadatos. 
    Requiere un **Access Token válido** en el header `Authorization: Bearer <token>`.

    **Permisos requeridos:**
    - Autenticación (Access Token válido).

    **Respuestas:**
    - 200: Datos del usuario actual recuperados.
    - 401: Token inválido o expirado.
    - 500: Error interno del servidor.
    """
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Recupera los datos del usuario identificado por el Access Token.

    Args:
        current_user: Diccionario con los datos del usuario extraídos del Access Token (proporcionado por `get_current_user`).

    Returns:
        UserDataWithRoles: Objeto con todos los datos del usuario, incluyendo roles.

    Raises:
        HTTPException: Si el token es inválido o expirado (401), o error interno (500).
    """
    logger.info(f"Solicitud /me/ recibida para usuario: {current_user.get('nombre_usuario')}")
    try:
        usuario_service = UsuarioService()
        user_id = current_user.get('usuario_id')
        cliente_id = current_user.get('cliente_id')
        
        # ✅ NUEVO: Obtener información extendida del usuario para diferenciación Super Admin vs Tenant Admin
        usuario_completo = await usuario_service.obtener_usuario_completo_por_id(user_id, cliente_id)
        
        if not usuario_completo:
            logger.error(f"Usuario {user_id} no encontrado en cliente {cliente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # ✅ NUEVO: Determinar tipo de usuario (Super Admin vs Tenant Admin vs Usuario normal)
        tipo_usuario = "user"
        es_super_admin = False
        es_tenant_admin = False
        
        # Verificar si es Super Admin (rol SUPER_ADMIN global o del cliente SYSTEM)
        for rol in usuario_completo.get("roles", []):
            if rol.get("codigo_rol") == "SUPER_ADMIN" and rol.get("cliente_id") is None:
                es_super_admin = True
                tipo_usuario = "super_admin"
                break
            elif rol.get("codigo_rol") == "ADMIN" and rol.get("cliente_id") == cliente_id and cliente_id != 1:
                es_tenant_admin = True
                tipo_usuario = "tenant_admin"
        
        # Caso especial: Super Admin del cliente SYSTEM (cliente_id = 1)
        if cliente_id == 1 and any(rol.get("codigo_rol") == "SUPER_ADMIN" for rol in usuario_completo.get("roles", [])):
            es_super_admin = True
            tipo_usuario = "super_admin"
        
        # ✅ NUEVO: Construir respuesta extendida
        user_full_data = {
            **current_user,
            "roles": usuario_completo.get("roles", []),
            "tipo_usuario": tipo_usuario,
            "es_super_admin": es_super_admin,
            "es_tenant_admin": es_tenant_admin,
            "cliente_info": usuario_completo.get("cliente_info"),
            "modulos_activos": usuario_completo.get("modulos_activos", [])
        }
        
        logger.info(f"Datos completos del usuario {current_user.get('nombre_usuario')} recuperados (tipo: {tipo_usuario})")
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
@router.post(
    "/refresh/",
    response_model=Token,
    summary="Refrescar Access Token",
    description="""
    Genera un nuevo Access Token usando el **Refresh Token**.
    
    **✅ NUEVO - Estrategia según cliente:**
    - **Web (X-Client-Type: web):** Lee Refresh Token de cookie HttpOnly, devuelve nuevo Access en JSON y rota Refresh en cookie
    - **Móvil (X-Client-Type: mobile):** Lee Refresh Token del body, devuelve ambos tokens en JSON
    
    Además, **rota el Refresh Token** (emite uno nuevo y lo reemplaza) para mayor seguridad.

    **✅ CORREGIDO: Rotación segura**
    - El refresh token ANTIGUO se revoca **ANTES** de emitir el nuevo
    - Garantiza que solo un refresh token esté activo por sesión

    **Respuestas:**
    - 200: Tokens refrescados exitosamente.
    - 401: Refresh Token ausente, inválido o expirado.
    - 500: Error interno del servidor.
    """
)
async def refresh_access_token(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user_from_refresh)
):
    """
    Genera un nuevo Access Token y rota el Refresh Token de forma segura.

    Args:
        request: Objeto Request para inspeccionar cookies y headers
        response: Objeto Response para establecer la nueva cookie HttpOnly.
        current_user: Payload del Refresh Token validado (proporcionado por `get_current_user_from_refresh`).

    Returns:
        Token: Objeto que contiene el nuevo Access Token y tipo de token.

    Raises:
        HTTPException: Si el token es inválido (401) o error interno (500).
    """
    try:
        # ✅ NUEVO: Detectar tipo de cliente
        client_type = get_client_type(request)
        
        username = current_user.get("nombre_usuario")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido en el refresh token")

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
            logger.warning(f"[REFRESH] No se pudo obtener el refresh token antiguo para {username} ({client_type})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token no proporcionado"
            )

        # === PASO 2: REVOCAR INMEDIATAMENTE EL TOKEN ANTIGUO ===
        # ✅ CORRECCIÓN CRÍTICA: Revocamos ANTES de generar el nuevo
        try:
            revoked = await RefreshTokenService.revoke_token(
                cliente_id=current_user.get("cliente_id"),
                usuario_id=current_user.get("usuario_id"),
                token=old_refresh_token
            )
            if not revoked:
                logger.warning(f"[REFRESH] Token antiguo ya estaba revocado o no existía para {username}")
                # Aún así continuamos, porque podría ser un intento legítimo tras limpieza
        except Exception as e:
            logger.error(f"[REFRESH] Error al revocar token antiguo: {str(e)}")
            # No fallamos el refresh por error de revocación, pero registramos

        # === PASO 3: GENERAR NUEVOS TOKENS ===
        new_access_token = create_access_token(data={"sub": username})
        new_refresh_token = create_refresh_token(data={"sub": username})

        # === PASO 4: ALMACENAR EL NUEVO REFRESH TOKEN ===
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            stored = await RefreshTokenService.store_refresh_token(
                cliente_id=current_user.get("cliente_id"),
                usuario_id=current_user.get("usuario_id"),
                token=new_refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # ✅ NUEVO: Verificar almacenamiento
            if stored and stored.get('token_id', -1) > 0:
                logger.info(f"[REFRESH] Nuevo token almacenado - ID: {stored['token_id']}")
            else:
                logger.warning(f"[REFRESH] Token duplicado ignorado (doble llamada detectada)")
                
        except Exception as e:
            logger.error(f"[REFRESH] Error almacenando nuevo refresh token: {str(e)}")
            # No fallamos el refresh, pero registramos el error

        # === PASO 5: PREPARAR RESPUESTA ===
        response_data = {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user_data": None
        }
        
        # ✅ NUEVO: Lógica diferenciada según tipo de cliente
        if client_type == "web":
            # WEB: Nuevo refresh en cookie
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=new_refresh_token,
                httponly=True,  # ✅ Protege contra XSS
                secure=settings.COOKIE_SECURE,  # ✅ True en producción
                samesite=settings.COOKIE_SAMESITE,  # ✅ 'strict' en prod, 'lax' en dev
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
                path="/",
                domain=settings.COOKIE_DOMAIN,  # ✅ Dominio específico
            )
            logger.info(f"[REFRESH-WEB] Token refrescado exitosamente para usuario: {username}")
        else:  # mobile
            # MÓVIL: Nuevo refresh en JSON
            response_data["refresh_token"] = new_refresh_token
            logger.info(f"[REFRESH-MOBILE] Token refrescado exitosamente para usuario: {username}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error en /refresh/: {str(e)}")
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
        if refresh_token:
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
                logger.warning(
                    f"[LOGOUT-{client_type.upper()}] Token no encontrado en BD - "
                    f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
                )
        else:
            logger.warning(
                f"[LOGOUT-{client_type.upper()}] No se proporcionó refresh token - "
                f"Cliente: {cliente_id}, Usuario: {usuario_id} ({username})"
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
        rows_affected = await RefreshTokenService.revoke_all_user_tokens(cliente_id=cliente_id, usuario_id=user_id)
        
        return {"message": f"Se han cerrado {rows_affected} sesiones activas para el usuario {username}."}
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
        cliente_id = await resolve_cliente_id(cliente_id, subdominio)
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
        cliente_id = await resolve_cliente_id(cliente_id, subdominio)
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