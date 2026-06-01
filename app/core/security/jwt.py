# app/core/security/jwt.py
"""
Utilidades para creación y decodificación de tokens JWT.

✅ ARQUITECTURA: Contiene utilidades de seguridad relacionadas con JWT.
✅ REVOCACIÓN: Incluye jti (JWT ID) para revocación de tokens con Redis.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
import logging
from uuid import uuid4, UUID
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

logger = logging.getLogger(__name__)

# Swagger/OpenAPI: flujo password con tokenUrl en /api/v1
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/")


def normalize_bearer_jwt_token(raw: str) -> str:
    """
    Normaliza el valor extraído del header Authorization antes de jwt.decode.

    Rechaza tokens vacíos, placeholders del frontend (undefined/null) y
    valores que no tienen forma JWT (header.payload.signature).
    """
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token. Envíe Authorization: Bearer <JWT>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = raw.strip()
    if (token.startswith('"') and token.endswith('"')) or (
        token.startswith("'") and token.endswith("'")
    ):
        token = token[1:-1].strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token. Envíe Authorization: Bearer <JWT>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if token.lower() in ("undefined", "null", "none"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Token inválido. Tras login multi-empresa use selection_token "
                "del response en Bearer. No llame GET /auth/me/ con selection_token; "
                "use POST /api/v1/auth/empresa/seleccionar/."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if token.count(".") != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Token JWT inválido o incompleto. Debe tener tres segmentos "
                "(header.payload.signature). Verifique que copió el JWT completo "
                "desde access_token (sesión) o selection_token (selección de empresa)."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def _serialize_empresa_id_claim(value: Any) -> Optional[str]:
    """Serializa empresa_id para el payload JWT (string UUID o None)."""
    if value is None:
        return None
    if isinstance(value, UUID):
        null_uuid = UUID("00000000-0000-0000-0000-000000000000")
        if value == null_uuid:
            return None
        return str(value)
    text = str(value).strip()
    return text or None


def _apply_empresa_claims(
    to_encode: dict,
    *,
    empresa_id: Optional[UUID] = None,
    es_admin_cliente: Optional[bool] = None,
) -> None:
    """
    Añade empresa_id (opcional) y es_admin_cliente al payload del token.
    Los valores explícitos tienen prioridad sobre los presentes en ``data``.
    """
    data_empresa = to_encode.pop("empresa_id", None)
    data_admin = to_encode.pop("es_admin_cliente", None)

    resolved_empresa = empresa_id if empresa_id is not None else data_empresa
    serialized_empresa = _serialize_empresa_id_claim(resolved_empresa)
    if serialized_empresa is not None:
        to_encode["empresa_id"] = serialized_empresa

    if es_admin_cliente is not None:
        to_encode["es_admin_cliente"] = bool(es_admin_cliente)
    elif data_admin is not None:
        to_encode["es_admin_cliente"] = bool(data_admin)
    else:
        to_encode["es_admin_cliente"] = False


def create_access_token(
    data: dict,
    *,
    empresa_id: Optional[UUID] = None,
    es_admin_cliente: Optional[bool] = None,
    access_token_expire_minutes: Optional[int] = None,
) -> Tuple[str, str]:
    """
    Crea un token JWT de acceso con iat, exp, type='access' y jti (JWT ID).
    - Usa SECRET_KEY específica
    - Tiempo de expiración reducido (15 min por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type, empresa_id, es_admin_cliente
    - ✅ REVOCACIÓN: Incluye jti (UUID único) para blacklist
    
    Args:
        data: Claims base (sub, cliente_id, level_info, etc.)
        empresa_id: Empresa activa de la sesión (opcional)
        es_admin_cliente: True si algún rol activo tiene rol.es_admin_cliente = 1
        access_token_expire_minutes: Minutos de vida del access token (tenant o settings)
    
    Returns:
        Tuple[str, str]: (token, jti) - Token JWT y su identificador único
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire_minutes = (
        access_token_expire_minutes
        if access_token_expire_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = now + timedelta(minutes=expire_minutes)
    
    # ✅ REVOCACIÓN: Generar jti (JWT ID) único para cada token
    jti = str(uuid4())
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    is_super_admin = level_info.get("is_super_admin", False)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
        "jti": jti,  # ✅ REVOCACIÓN: JWT ID para blacklist
        "access_level": level_info.get("access_level", 1),
        "is_super_admin": is_super_admin,
        "user_type": level_info.get("user_type", "user"),
    })
    if is_super_admin or to_encode.get("es_superadmin"):
        to_encode["es_superadmin"] = True

    # Remover level_info temporal del payload
    to_encode.pop("level_info", None)

    _apply_empresa_claims(
        to_encode,
        empresa_id=empresa_id,
        es_admin_cliente=es_admin_cliente,
    )
    
    # Usa SECRET_KEY para access tokens
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return (token, jti)


def create_refresh_token(
    data: dict,
    *,
    empresa_id: Optional[UUID] = None,
    es_admin_cliente: Optional[bool] = None,
    refresh_token_expire_days: Optional[int] = None,
) -> Tuple[str, str]:
    """
    Crea un token JWT de refresh con iat, exp, type='refresh' y jti (JWT ID).
    - Usa REFRESH_SECRET_KEY separada (mayor seguridad)
    - Tiempo de expiración largo (7 días por defecto)
    - AHORA INCLUYE: access_level, is_super_admin, user_type, empresa_id, es_admin_cliente
    - ✅ REVOCACIÓN: Incluye jti (UUID único) para blacklist
    
    Args:
        data: Claims base (sub, cliente_id, level_info, etc.)
        empresa_id: Empresa activa de la sesión (opcional)
        es_admin_cliente: True si algún rol activo tiene rol.es_admin_cliente = 1
        refresh_token_expire_days: Días de vida del refresh token (tenant o settings)
    
    Returns:
        Tuple[str, str]: (token, jti) - Token JWT y su identificador único
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire_days = (
        refresh_token_expire_days
        if refresh_token_expire_days is not None
        else settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    expire = now + timedelta(days=expire_days)
    
    # ✅ REVOCACIÓN: Generar jti (JWT ID) único para cada token
    jti = str(uuid4())
    
    # ✅ AGREGAR CAMPOS DE NIVEL AL PAYLOAD
    level_info = to_encode.get('level_info', {})
    
    is_super_admin = level_info.get("is_super_admin", False)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": jti,  # ✅ REVOCACIÓN: JWT ID para blacklist
        "access_level": level_info.get("access_level", 1),
        "is_super_admin": is_super_admin,
        "user_type": level_info.get("user_type", "user"),
    })
    if is_super_admin or to_encode.get("es_superadmin"):
        to_encode["es_superadmin"] = True

    # Remover level_info temporal del payload
    to_encode.pop("level_info", None)

    _apply_empresa_claims(
        to_encode,
        empresa_id=empresa_id,
        es_admin_cliente=es_admin_cliente,
    )
    
    # Usa REFRESH_SECRET_KEY separada
    token = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return (token, jti)


async def build_token_payload_for_sso(
    user_full_data: Dict[str, Any],
    cliente_id: UUID,
    user_role_names: List[str]
) -> Dict[str, Any]:
    """
    Construye el payload del token JWT para flujos SSO.
    
    ✅ FASE 1: Incluye cliente_id y level_info igual que login password.
    Esto asegura que la validación de tenant funcione correctamente para SSO.
    
    Args:
        user_full_data: Datos completos del usuario (debe incluir 'usuario_id' y 'nombre_usuario')
        cliente_id: ID del cliente/tenant (UUID)
        user_role_names: Lista de nombres de roles del usuario
    
    Returns:
        Dict con payload completo para JWT, incluyendo:
        - sub: nombre de usuario
        - cliente_id: ID del cliente (string)
        - level_info: Dict con access_level, is_super_admin, user_type
        - es_superadmin: bool (si aplica)
    
    Example:
        ```python
        payload = await build_token_payload_for_sso(
            user_full_data={"usuario_id": uuid, "nombre_usuario": "user"},
            cliente_id=cliente_uuid,
            user_role_names=["Administrador"]
        )
        access_token, jti = create_access_token(data=payload)
        ```
    """
    from app.modules.auth.application.services.auth_service import AuthService
    
    user_id = user_full_data.get('usuario_id')
    if not user_id:
        raise ValueError("user_full_data debe incluir 'usuario_id'")
    
    nombre_usuario = user_full_data.get('nombre_usuario')
    if not nombre_usuario:
        raise ValueError("user_full_data debe incluir 'nombre_usuario'")
    
    # Obtener access_level (igual que en login password)
    level_info = await AuthService.get_user_access_level_info(user_id, cliente_id)
    
    # Determinar si es super admin
    is_super_admin = level_info.get('is_super_admin', False)
    user_type = level_info.get('user_type', 'user')
    
    # Construir payload igual que en login password
    payload = {
        "sub": nombre_usuario,
        "cliente_id": str(cliente_id),  # Convertir UUID a string para JSON serialization
        "level_info": level_info
    }
    
    # Añadir flag de superadmin si aplica (platform_admin)
    if is_super_admin or user_type == "platform_admin":
        payload["es_superadmin"] = True

    return payload


def decode_refresh_token(token: str) -> dict:
    """
    Decodifica y valida un refresh token (type='refresh')
    - Usa REFRESH_SECRET_KEY para validación
    - Verifica que el tipo sea 'refresh'
    - AHORA VALIDA: access_level, is_super_admin, user_type
    """
    try:
        # Usa REFRESH_SECRET_KEY para decodificar
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Token type is not refresh")
        
        # ✅ VALIDAR QUE TENGA CAMPOS DE NIVEL
        if 'access_level' not in payload or 'user_type' not in payload:
            logger.warning("Refresh token no contiene campos de nivel de acceso")
            raise JWTError("Token missing access level fields")
            
        return payload
    except JWTError as e:
        logger.error(f"Error decodificando refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )



