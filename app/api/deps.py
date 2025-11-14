# app/api/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import List, Dict, Any

from app.core.config import settings
from app.core.auth import oauth2_scheme
from app.db.queries import execute_auth_query, execute_query

# --- Importar los schemas necesarios ---
from app.schemas.auth import TokenPayload
from app.schemas.usuario import UsuarioReadWithRoles # <<< Importar schema de usuario
from app.schemas.rol import RolRead # <<< Importar schema de rol
# --- Fin importación schemas ---
from app.services.usuario_service import UsuarioService
from app.services.rol_service import RolService # <<< NUEVA IMPORTACIÓN: Servicio de Roles

import logging
logger = logging.getLogger(__name__)

# Excepciones (sin cambios)
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales",
    headers={"WWW-Authenticate": "Bearer"},
)
inactive_user_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Usuario inactivo",
)
# Modificamos la excepción base para que la RoleChecker pueda rellenar los niveles
forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permisos insuficientes",
)

# get_current_user_data (sin cambios)
async def get_current_user_data(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Decodifica el token, obtiene el nombre de usuario y lo devuelve.
    No accede a la base de datos aquí para optimizar.
    Lanza excepción si el token es inválido o ha expirado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token JWT inválido: falta 'sub'.")
            raise credentials_exception
        return payload
    except JWTError as e:
        logger.warning(f"Error de validación JWT: {e}")
        raise credentials_exception

# --- get_current_active_user (SIN CAMBIOS FUNCIONALES) ---
async def get_current_active_user(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data)
) -> UsuarioReadWithRoles:
    # ... (Contenido de get_current_active_user se mantiene exactamente igual) ...
    """
    Dependencia principal: Obtiene los datos completos del usuario activo desde la BD
    basado en el nombre de usuario del token, añade sus roles (como objetos RolRead)
    y devuelve una instancia del schema UsuarioReadWithRoles.
    """
    username = payload.get("sub")

    try:
        # Obtener datos básicos del usuario como diccionario **incluyendo cliente_id**
        user_query = """
        SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, 
            es_activo, fecha_creacion, fecha_ultimo_acceso, correo_confirmado,
            es_eliminado, proveedor_autenticacion, fecha_ultimo_cambio_contrasena,
            sincronizado_desde
        FROM usuario
        WHERE nombre_usuario = ? AND es_eliminado = 0
        """
        user_dict = execute_auth_query(user_query, (username,)) # Asume que devuelve dict o None

        if not user_dict:
            logger.warning(f"Usuario '{username}' del token válido no encontrado en BD (o eliminado).")
            raise credentials_exception

        if not user_dict.get('es_activo'):
            logger.warning(f"Usuario '{username}' autenticado pero inactivo.")
            raise inactive_user_exception

        # 🔒 Validación de aislamiento multi-tenant
        token_cliente_id = user_dict.get('cliente_id')
        request_cliente_id = getattr(request.state, 'cliente_id', None)

        # Si el usuario NO es un Super Administrador (cliente_id no es NULL) Y 
        # el ID del token no coincide con el ID del contexto del request, denegar.
        # NOTE: El Super Administrador (rol_id=NULL) debe poder acceder a cualquier cliente,
        # pero esta validación de seguridad SÓLO permite que los usuarios de un TENANT
        # accedan a su propio TENANT. El SUPER ADMIN debe tener cliente_id=NULL en la tabla usuario
        # O la lógica de tenant_middleware debe manejar una excepción para el cliente 'admin'.
        # Por ahora, mantenemos la lógica de que un usuario con cliente_id debe coincidir.
        if token_cliente_id is not None and request_cliente_id is not None and token_cliente_id != request_cliente_id:
            logger.warning(f"Acceso denegado: el usuario '{username}' (cliente {token_cliente_id}) "
                           f"intentó acceder al cliente {request_cliente_id}. Violación de tenant.")
            raise credentials_exception


        # Obtener roles del usuario usando el servicio (devuelve List[Dict])
        roles_list: List[RolRead] = [] # Inicializar lista para objetos RolRead
        try:
            # roles_dict_list será del tipo List[Dict]
            roles_dict_list: List[Dict] = await UsuarioService.obtener_roles_de_usuario(token_cliente_id, user_dict['usuario_id'])
            logger.debug(f"Roles (dicts) obtenidos para usuario ID {user_dict['usuario_id']}: {roles_dict_list}")

            # --- Convertir List[Dict] a List[RolRead] ---
            for rol_dict in roles_dict_list:
                try:
                    # Crear instancia de RolRead desde cada diccionario
                    roles_list.append(RolRead(**rol_dict))
                except Exception as rol_parse_error:
                    # Loggear error si un diccionario de rol no es válido
                    logger.error(f"Error parseando diccionario de rol a RolRead: {rol_dict}. Error: {rol_parse_error}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error interno al procesar datos de roles del usuario."
                    )
            # --- FIN CONVERSIÓN ---

            logger.debug(f"Roles convertidos a List[RolRead] para usuario ID {user_dict['usuario_id']}: {[r.nombre for r in roles_list]}")


        except Exception as role_error:
            # Captura errores de UsuarioService.obtener_roles_de_usuario o de la conversión
            logger.error(f"Error obteniendo/procesando roles para usuario ID {user_dict['usuario_id']}: {role_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al obtener o procesar roles del usuario."
            )

        # --- Construir y devolver la instancia Pydantic ---
        try:
            # Crear la instancia usando el diccionario de datos y la LISTA DE OBJETOS RolRead
            usuario_pydantic = UsuarioReadWithRoles(**user_dict, roles=roles_list)
            logger.debug(f"Usuario activo '{username}' (ID: {usuario_pydantic.usuario_id}) construido como objeto Pydantic.")
            return usuario_pydantic # <<< Devolver el objeto Pydantic

        except Exception as pydantic_error:
            # Error si los datos del diccionario no coinciden con el schema
            logger.error(f"Error creando instancia Pydantic UsuarioReadWithRoles para '{username}': {pydantic_error}", exc_info=True)
            logger.error(f"Datos del usuario (dict): {user_dict}")
            logger.error(f"Roles obtenidos y convertidos (list[RolRead]): {roles_list}") # Loggear la lista convertida
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al procesar datos del usuario."
            )

    except HTTPException as e:
        # Re-lanzar excepciones HTTP ya manejadas (credentials, inactive, etc.)
        raise e
    except Exception as e:
        # Capturar cualquier otro error inesperado
        logger.error(f"Error inesperado obteniendo usuario activo '{username}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el usuario."
        )


# --- RoleChecker (MODIFICADO PARA LBAC) ---

class RoleChecker:
    """
    Clase para crear dependencias que verifican roles específicos.
    
    AHORA BASADO EN NIVEL DE ACCESO (LBAC): Un usuario con nivel N puede acceder
    a cualquier recurso que requiera un nivel M, si N >= M.
    """
    def __init__(self, required_roles: List[str]):
        """
        Inicializa con los nombres de rol requeridos.
        """
        self.required_roles = required_roles
        self.min_required_level: int = 0
        
        # NOTE: El cálculo del nivel mínimo debe hacerse DENTRO de __call__ de forma asíncrona
        # ya que la dependencia se resuelve de forma asíncrona y necesita acceso a la DB.

    async def __call__(self,
        current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
    ):
        """
        Verifica si el nivel de acceso máximo del usuario es suficiente para cubrir
        el nivel de acceso mínimo requerido por los roles permitidos.
        """
        user_id = current_user.usuario_id
        
        # 1. Determinar el nivel mínimo requerido (Nivel M)
        try:
            # El RolService consulta la BD para el MIN(nivel_acceso) de los roles requeridos
            min_required_level = await RolService.get_min_required_access_level(self.required_roles)
        except Exception as e:
            logger.error(f"Error al obtener nivel requerido para roles {self.required_roles}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al verificar el nivel de rol requerido."
            )
        
        # 2. Determinar el nivel máximo del usuario (Nivel N)
        try:
            # El RolService consulta la BD para el MAX(nivel_acceso) del usuario
            user_max_level = await RolService.get_user_max_access_level(user_id)
        except Exception as e:
            logger.error(f"Error al obtener nivel máximo para usuario {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al verificar el nivel de rol del usuario."
            )

        # 3. Comparación Jerárquica: N >= M
        # Esto soluciona el problema: SUPER_ADMIN (99) vs. Administrador (50). 99 >= 50. ACCESO.
        if user_max_level < min_required_level:
            
            # --- LOGS Y MENSAJE DE ERROR MEJORADOS ---
            user_role_names = [role.nombre for role in current_user.roles]
            logger.warning(
                f"Acceso denegado para usuario '{current_user.nombre_usuario}'. "
                f"Roles del usuario: {user_role_names}. Nivel Máximo: {user_max_level}. "
                f"Roles requeridos: {self.required_roles}. Nivel Mínimo Requerido: {min_required_level}"
            )
            
            # Lanzamos la excepción con un detalle más informativo.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Nivel de acceso del usuario ({user_max_level}) es menor al requerido ({min_required_level})."
            )

        logger.debug(f"Acceso permitido para usuario '{current_user.nombre_usuario}' por LBAC (Nivel {user_max_level} >= {min_required_level}).")
        
        # Retornamos el current_user para que esté disponible en la ruta si es necesario
        return current_user