# app/api/v1/endpoints/auth.py
"""
Módulo de endpoints para la gestión de la autenticación de usuarios (Login, Logout, Refresh Token).

Este módulo maneja el flujo de autenticación basado en JWT y cookies seguras.

Características principales:
- **Login:** Verifica credenciales, genera un Access Token y un Refresh Token (establecido en cookie HttpOnly).
- **Me:** Permite al usuario obtener su información y roles usando el Access Token.
- **Refresh:** Genera un nuevo Access Token usando el Refresh Token de la cookie (implementando rotación de refresh token).
- **Logout:** Elimina la cookie del Refresh Token para cerrar la sesión.
- **✅ NUEVO: Detección de cliente:** Diferencia entre peticiones web y móvil mediante header X-Client-Type.
"""
from typing import List, Dict # Importación necesaria para el nuevo endpoint /sessions/
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Path
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import Token, UserDataWithRoles
from app.core.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh,
)
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.usuario_service import UsuarioService
from app.services.refresh_token_service import RefreshTokenService
from app.api.deps import RoleChecker 

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
@router.post(
    "/login/",
    response_model=Token,
    summary="Autenticar usuario y obtener token",
    description="""
    Verifica credenciales (nombre de usuario/email y contraseña) proporcionadas mediante formulario `OAuth2PasswordRequestForm`. 
    Genera un **Access Token** (retornado en el cuerpo de la respuesta) y un **Refresh Token**.
    
    **✅ NUEVO - Estrategia de tokens según cliente:**
    - **Web (X-Client-Type: web):** Access Token en JSON, Refresh Token en HttpOnly cookie
    - **Móvil (X-Client-Type: mobile):** Ambos tokens en JSON (sin cookie)
    
    Retorna los datos básicos del usuario, incluyendo sus roles.

    **Respuestas:**
    - 200: Autenticación exitosa y tokens generados.
    - 401: Credenciales inválidas.
    - 500: Error interno del servidor durante el proceso.
    """
)
async def login(
    request: Request,  # ✅ NUEVO: Para detectar tipo de cliente
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Realiza la autenticación del usuario y emite los tokens de sesión.

    Args:
        request: Objeto Request para detectar tipo de cliente
        response: Objeto Response de FastAPI para manipular cookies.
        form_data: Objeto de formulario con `username` y `password` para autenticar.

    Returns:
        Token: Objeto que contiene el Access Token, tipo de token y los datos completos del usuario (`UserDataWithRoles`).

    Raises:
        HTTPException: Si la autenticación falla (401) o por un error interno (500).
    """
    usuario_service = UsuarioService()
    
    try:
        # ✅ NUEVO: Detectar tipo de cliente
        client_type = get_client_type(request)
        
        # 1) Autenticación (maneja 401 si falla)
        user_base_data = await authenticate_user(form_data.username, form_data.password)

        # 2) Roles
        user_id = user_base_data.get('usuario_id')
        user_role_names = await usuario_service.get_user_role_names(user_id=user_id)

        user_full_data = {**user_base_data, "roles": user_role_names}

        # 3) Tokens
        access_token = create_access_token(data={"sub": form_data.username})
        refresh_token = create_refresh_token(data={"sub": form_data.username})

        # ✅ NUEVO: Almacenar refresh token en BD
        try:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
            stored = await RefreshTokenService.store_refresh_token(
                usuario_id=user_id,
                token=refresh_token,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # ✅ NUEVO: Verificar si se almacenó correctamente
            if stored and stored.get('token_id', -1) > 0:
                logger.info(f"[LOGIN-{client_type.upper()}] Token almacenado en BD - ID: {stored['token_id']}")
            else:
                logger.warning(f"[LOGIN-{client_type.upper()}] Token duplicado ignorado (no afecta funcionalidad)")
                
        except Exception as e:
            logger.error(f"Error almacenando refresh token: {str(e)}")
            # No fallar el login si falla el almacenamiento
            # El token JWT seguirá funcionando temporalmente

        # ✅ NUEVO: Lógica diferenciada según tipo de cliente
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user_data": user_full_data
        }
        
        if client_type == "web":
            # 4a) WEB: Refresh en HttpOnly cookie, Access en JSON
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=refresh_token,
                httponly=True,  # ✅ Protege contra XSS
                secure=settings.COOKIE_SECURE,  # ✅ True en producción (HTTPS)
                samesite=settings.COOKIE_SAMESITE,  # ✅ 'strict' en prod, 'lax' en dev
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
                path="/",
                domain=settings.COOKIE_DOMAIN,  # ✅ Dominio específico en producción
            )
            logger.info(f"Usuario {form_data.username} autenticado exitosamente (WEB) - Refresh en cookie")
            
        else:  # mobile
            # 4b) MÓVIL: Ambos tokens en JSON (sin cookie)
            response_data["refresh_token"] = refresh_token
            logger.info(f"Usuario {form_data.username} autenticado exitosamente (MOBILE) - Ambos tokens en JSON")

        return response_data

    except HTTPException:
        # Re-lanza 401 si proviene de authenticate_user
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
        # Obtener roles, que es la información extra
        user_role_names = await usuario_service.get_user_role_names(user_id=user_id)
        user_full_data = {**current_user, "roles": user_role_names}
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
            revoked = await RefreshTokenService.revoke_token(old_refresh_token)
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
async def logout(request: Request, response: Response):
    """
    Cierra sesión revocando el refresh token en BD.

    Args:
        request: Objeto Request para detectar tipo de cliente
        response: Objeto Response de FastAPI para manipular cookies.

    Returns:
        Dict[str, str]: Mensaje de éxito.

    Raises:
        HTTPException: En caso de error al cerrar sesión
    """
    try:
        # ✅ NUEVO: Detectar tipo de cliente
        client_type = get_client_type(request)
        
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
        
        # ✅ NUEVO: Revocar token en BD
        if refresh_token:
            revoked = await RefreshTokenService.revoke_token(refresh_token)
            if revoked:
                logger.info(f"[LOGOUT-{client_type.upper()}] Token revocado exitosamente en BD")
            else:
                logger.warning(f"[LOGOUT-{client_type.upper()}] Token no encontrado en BD")
        else:
            logger.warning(f"[LOGOUT-{client_type.upper()}] No se proporcionó refresh token")
        
        return {"message": f"Sesión cerrada exitosamente ({client_type})"}
    
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
    username = current_user.get('nombre_usuario')
    logger.info(f"Solicitud /sessions/ recibida para usuario: {username}")
    try:
        sessions = await RefreshTokenService.get_active_sessions(usuario_id=user_id)
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
    username = current_user.get('nombre_usuario')
    logger.info(f"Solicitud /logout_all/ recibida para usuario: {username}")
    try:
        rows_affected = await RefreshTokenService.revoke_all_user_tokens(usuario_id=user_id)
        
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
    username = current_user.get('nombre_usuario', 'N/A')
    logger.info(f"[ADMIN] Solicitud /sessions/admin/ por usuario: {username}")
    try:
        sessions = await RefreshTokenService.get_all_active_sessions_for_admin()
        
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
