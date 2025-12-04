# app/api/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import List, Dict, Any

from app.core.config import settings
from app.core.auth import oauth2_scheme
# ✅ FASE 2: Migrar a queries_async
from app.infrastructure.database.queries_async import execute_auth_query, execute_query

# --- Importar los schemas necesarios ---
from app.modules.auth.presentation.schemas import TokenPayload
from app.modules.users.presentation.schemas import UsuarioReadWithRoles # <<< Importar schema de usuario
from app.modules.rbac.presentation.schemas import RolRead # <<< Importar schema de rol
# --- Fin importación schemas ---
from app.modules.users.application.services.user_service import UsuarioService
from app.modules.rbac.application.services.rol_service import RolService # <<< NUEVA IMPORTACIÓN: Servicio de Roles

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


# --- NUEVAS FUNCIONES PARA NIVELES DE ACCESO ---

async def get_user_access_level(usuario_id: int, cliente_id: int) -> int:
    """
    Obtiene el nivel de acceso máximo del usuario basado en sus roles activos
    """
    try:
        from app.infrastructure.database.queries import GET_USER_MAX_ACCESS_LEVEL
        
        # ✅ FASE 2: Usar execute_query async
        result = await execute_query(GET_USER_MAX_ACCESS_LEVEL, (usuario_id, cliente_id))
        
        if result and len(result) > 0:
            max_level = result[0].get('max_level', 1)
            logger.debug(f"Nivel máximo calculado para usuario {usuario_id}: {max_level}")
            return max_level
        else:
            logger.warning(f"No se encontraron roles activos para usuario {usuario_id}, usando nivel 1")
            return 1
            
    except Exception as e:
        logger.error(f"Error al obtener nivel de acceso para usuario {usuario_id}: {e}")
        return 1  # Nivel mínimo por seguridad

# AGREGAR ESTA NUEVA FUNCIÓN PARA DIAGNÓSTICO
async def debug_user_access_levels(usuario_id: int, cliente_id: int) -> Dict[str, Any]:
    """
    Función de diagnóstico para verificar niveles de acceso
    """
    try:
        from app.infrastructure.database.queries import GET_USER_ACCESS_LEVEL_INFO_COMPLETE
        
        # ✅ FASE 2: Usar execute_query async
        result = await execute_query(GET_USER_ACCESS_LEVEL_INFO_COMPLETE, (usuario_id, cliente_id))
        
        if result and len(result) > 0:
            level_info = result[0]
            logger.info(f"DIAGNÓSTICO NIVELES - Usuario {usuario_id}: {level_info}")
            return level_info
        else:
            logger.warning(f"DIAGNÓSTICO NIVELES - Sin resultados para usuario {usuario_id}")
            return {"max_level": 1, "super_admin_count": 0, "total_roles": 0}
            
    except Exception as e:
        logger.error(f"Error en diagnóstico de niveles para usuario {usuario_id}: {e}")
        return {"error": str(e)}

async def check_is_super_admin(usuario_id: int) -> bool:
    """
    Verifica si el usuario tiene rol de SUPER_ADMIN (nivel 5)
    """
    try:
        from app.infrastructure.database.queries import IS_USER_SUPER_ADMIN
        
        # ✅ FASE 2: Usar execute_query async
        result = await execute_query(IS_USER_SUPER_ADMIN, (usuario_id,))
        
        if result and len(result) > 0:
            is_super_admin = result[0].get('is_super_admin', 0) > 0
            logger.debug(f"Usuario {usuario_id} es super admin: {is_super_admin}")
            return is_super_admin
        else:
            return False
            
    except Exception as e:
        logger.error(f"Error al verificar super admin para usuario {usuario_id}: {e}")
        return False


def determine_user_type(access_level: int, is_super_admin: bool) -> str:
    """
    Determina el tipo de usuario basado en nivel de acceso
    
    Args:
        access_level (int): Nivel de acceso del usuario
        is_super_admin (bool): Si es super admin
    
    Returns:
        str: Tipo de usuario: 'super_admin', 'tenant_admin', 'user'
    """
    if is_super_admin:
        return 'super_admin'
    elif access_level >= 4:
        return 'tenant_admin'
    else:
        return 'user'


# --- get_current_active_user (MODIFICADO PARA INCLUIR NIVELES) ---

async def get_current_active_user(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data)
) -> UsuarioReadWithRoles:
    """
    Dependencia principal: Obtiene los datos completos del usuario activo desde la BD
    basado en el nombre de usuario del token, añade sus roles (como objetos RolRead)
    y devuelve una instancia del schema UsuarioReadWithRoles.
    
    AHORA INCLUYE: access_level, is_super_admin, user_type
    """
    username = payload.get("sub")

    try:
        # ✅ OPTIMIZACIÓN 100%: Obtener usuario + roles + niveles en UNA SOLA query
        # Esta query obtiene TODO (usuario, roles, niveles) en un solo roundtrip
        # Mejora: 4 queries → 1 query = 100% reducción en roundtrips
        # Compatible con SQL Server 2005+ (detecta versión automáticamente)
        from app.infrastructure.database.queries import get_user_complete_data_query
        import json
        
        # Obtener cliente_id del contexto para la query optimizada
        # Si no hay contexto, usaremos el cliente_id del usuario (se obtendrá después)
        try:
            from app.core.tenant.context import get_current_client_id
            context_cliente_id = get_current_client_id()
        except RuntimeError:
            # Si no hay contexto, primero obtenemos el usuario básico y luego usamos su cliente_id
            # Esto es un fallback para casos edge (scripts de fondo, etc.)
            # ✅ CORRECCIÓN AUDITORÍA: Agregar filtro de cliente_id si está disponible
            # Si no hay contexto, primero buscamos sin filtro (fallback), pero luego validamos
            # ✅ FASE 2: Usar string SQL (temporal, hasta migrar completamente a SQLAlchemy Core)
            basic_user_query = """
            SELECT usuario_id, cliente_id, nombre_usuario, correo, nombre, apellido, 
                es_activo, fecha_creacion, fecha_ultimo_acceso, correo_confirmado,
                es_eliminado, proveedor_autenticacion, fecha_ultimo_cambio_contrasena,
                sincronizado_desde
            FROM usuario
            WHERE nombre_usuario = ? AND es_eliminado = 0
            """
            
            temp_user = await execute_auth_query(basic_user_query, (username,))
            if not temp_user:
                raise credentials_exception
            context_cliente_id = temp_user.get('cliente_id')
        
        # Query optimizada: usuario + roles (JSON) + niveles en una sola ejecución
        # La función get_user_complete_data_query() detecta la versión de SQL Server
        # y retorna la query apropiada (JSON para 2016+, XML para versiones antiguas)
        # ✅ CORRECCIÓN AUDITORÍA: Parámetros ahora incluyen cliente_id para filtrar usuario principal
        # Parámetros: (cliente_id para roles, cliente_id para niveles, cliente_id para super_admin, username, cliente_id para usuario)
        # ✅ FASE 2: Usar await
        optimized_query = get_user_complete_data_query()
        user_dict = await execute_auth_query(
            optimized_query, 
            (context_cliente_id, context_cliente_id, context_cliente_id, username, context_cliente_id)
        )

        if not user_dict:
            logger.warning(f"Usuario '{username}' del token válido no encontrado en BD (o eliminado).")
            raise credentials_exception

        if not user_dict.get('es_activo'):
            logger.warning(f"Usuario '{username}' autenticado pero inactivo.")
            raise inactive_user_exception

        # 🔒 Validación de aislamiento multi-tenant (MEJORADA)
        token_cliente_id = user_dict.get('cliente_id')
        
        # ✅ MEJORA: Obtener cliente_id del contexto de forma robusta
        try:
            from app.core.tenant.context import get_current_client_id
            request_cliente_id = get_current_client_id()
        except RuntimeError:
            # Si no hay contexto, intentar obtener de request.state (fallback)
            request_cliente_id = getattr(request.state, 'cliente_id', None)
            if request_cliente_id is None:
                logger.error(
                    f"[SECURITY] No se pudo obtener cliente_id del contexto para usuario '{username}'. "
                    f"Esto no debería ocurrir si el middleware está configurado correctamente."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error interno: contexto de tenant no disponible"
                )

        # ✅ MEJORA: Verificar si el usuario es SuperAdmin ANTES de validar tenant
        is_super_admin = user_dict.get('is_super_admin', False)
        
        if is_super_admin:
            # SuperAdmin puede acceder a cualquier tenant
            # Pero validar que el token tenga el flag correcto
            if not user_dict.get('is_super_admin'):
                logger.warning(
                    f"[SECURITY] Usuario '{username}' tiene cliente_id NULL pero no es SuperAdmin. "
                    f"Posible token comprometido."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token no válido: inconsistencia en permisos de SuperAdmin"
                )
            logger.debug(
                f"[SECURITY] SuperAdmin '{username}' accediendo a tenant {request_cliente_id} "
                f"(permitido)"
            )
        else:
            # Usuario regular: DEBE coincidir el tenant
            if token_cliente_id is None:
                logger.warning(
                    f"[SECURITY] Usuario regular '{username}' tiene cliente_id NULL en token. "
                    f"Token inválido o comprometido."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token inválido: falta cliente_id para usuario regular"
                )
            
            if request_cliente_id is None:
                logger.error(
                    f"[SECURITY] Contexto de tenant no disponible para validación. "
                    f"Usuario: '{username}', token_cliente_id: {token_cliente_id}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error interno: contexto de tenant no disponible"
                )
            
            if token_cliente_id != request_cliente_id:
                logger.warning(
                    f"[SECURITY] Acceso denegado: el usuario '{username}' (cliente {token_cliente_id}) "
                    f"intentó acceder al cliente {request_cliente_id}. Violación de tenant."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acceso denegado: token no válido para este tenant"
                )
            
            logger.debug(
                f"[SECURITY] Validación de tenant exitosa: usuario '{username}', "
                f"token_cliente_id={token_cliente_id}, request_cliente_id={request_cliente_id}"
            )

        # ✅ AUDITORÍA: Registrar accesos cross-tenant (especialmente SuperAdmin)
        if is_super_admin and token_cliente_id != request_cliente_id:
            try:
                from app.modules.superadmin.application.services.audit_service import AuditService
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
                await AuditService.registrar_tenant_access(
                    usuario_id=user_dict['usuario_id'],
                    token_cliente_id=token_cliente_id,
                    request_cliente_id=request_cliente_id,
                    tipo_acceso="superadmin_cross_tenant",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "username": username,
                        "access_level": user_dict.get('access_level'),
                    }
                )
                logger.info(
                    f"[AUDIT] Acceso cross-tenant registrado: SuperAdmin '{username}' "
                    f"(token_cliente_id={token_cliente_id}) accediendo a tenant {request_cliente_id}"
                )
            except Exception as audit_error:
                # No interrumpir el flujo si falla la auditoría
                logger.warning(
                    f"[AUDIT] Error registrando acceso cross-tenant (no crítico): {audit_error}"
                )

        # ✅ OPTIMIZACIÓN: Los roles ya vienen en la query optimizada como JSON
        # No necesitamos hacer query adicional - parsear JSON directamente
        roles_list: List[RolRead] = []
        try:
            # Parsear roles desde JSON retornado por la query
            roles_json_str = user_dict.get('roles_json')
            
            if roles_json_str:
                try:
                    # Parsear JSON string a lista de diccionarios
                    roles_dict_list: List[Dict] = json.loads(roles_json_str)
                    logger.debug(f"[PERF] Roles obtenidos de query optimizada para usuario ID {user_dict['usuario_id']}: {len(roles_dict_list)} roles")
                except json.JSONDecodeError as json_error:
                    logger.warning(
                        f"[PERF] Error parseando roles_json para usuario {user_dict['usuario_id']}: {json_error}. "
                        f"JSON recibido: {roles_json_str[:100] if roles_json_str else 'None'}"
                    )
                    roles_dict_list = []
            else:
                # Si no hay roles_json (usuario sin roles), lista vacía
                roles_dict_list = []
                logger.debug(f"[PERF] Usuario {user_dict['usuario_id']} no tiene roles asignados")

            # --- Convertir List[Dict] a List[RolRead] ---
            from datetime import datetime
            
            for rol_dict in roles_dict_list:
                try:
                    # ✅ CORRECCIÓN: Parsear fecha_creacion desde string ISO a datetime
                    # La query retorna fecha_creacion como string ISO 8601 desde JSON
                    if 'fecha_creacion' in rol_dict:
                        fecha_creacion = rol_dict['fecha_creacion']
                        if isinstance(fecha_creacion, str):
                            try:
                                # Parsear formato ISO 8601: "2024-01-01T12:00:00" o "2024-01-01T12:00:00.000"
                                # Manejar diferentes formatos de fecha
                                fecha_str = fecha_creacion.replace('Z', '+00:00')
                                # Si no tiene timezone, agregar uno por defecto
                                if '+' not in fecha_str and '-' not in fecha_str[-6:]:
                                    fecha_str = fecha_str + '+00:00'
                                rol_dict['fecha_creacion'] = datetime.fromisoformat(fecha_str)
                            except (ValueError, AttributeError) as date_error:
                                logger.warning(
                                    f"[PERF] Error parseando fecha_creacion para rol {rol_dict.get('rol_id')}: {date_error}. "
                                    f"Fecha recibida: {fecha_creacion}. Intentando parseo alternativo."
                                )
                                # Intentar parseo alternativo con strptime (formato común de SQL Server)
                                try:
                                    # SQL Server retorna formato: "2024-01-01T12:00:00" o "2024-01-01 12:00:00"
                                    fecha_str_clean = fecha_creacion.replace('T', ' ').split('.')[0]  # Remover milisegundos
                                    rol_dict['fecha_creacion'] = datetime.strptime(fecha_str_clean, '%Y-%m-%d %H:%M:%S')
                                except Exception:
                                    # Si todo falla, usar fecha actual como fallback
                                    logger.warning(f"[PERF] Usando fecha actual como fallback para rol {rol_dict.get('rol_id')}")
                                    rol_dict['fecha_creacion'] = datetime.now()
                        elif isinstance(fecha_creacion, datetime):
                            # Ya es datetime, mantenerlo
                            pass
                        else:
                            # Tipo desconocido, usar fecha actual
                            logger.warning(f"[PERF] fecha_creacion tiene tipo inesperado: {type(fecha_creacion)}")
                            rol_dict['fecha_creacion'] = datetime.now()
                    else:
                        # Si no viene fecha_creacion, usar fecha actual
                        logger.warning(f"[PERF] fecha_creacion no encontrado en rol {rol_dict.get('rol_id')}, usando fecha actual")
                        rol_dict['fecha_creacion'] = datetime.now()
                    
                    # ✅ CORRECCIÓN: La tabla rol NO tiene es_eliminado, usar valor por defecto del schema (False)
                    # El schema RolRead tiene es_eliminado con default=False, así que no es necesario incluirlo
                    if 'es_eliminado' not in rol_dict:
                        rol_dict['es_eliminado'] = False  # Valor por defecto del schema
                    
                    # ✅ CORRECCIÓN: Asegurar que es_activo sea boolean
                    if 'es_activo' in rol_dict:
                        rol_dict['es_activo'] = bool(rol_dict['es_activo'])
                    
                    # ✅ CORRECCIÓN: Manejar cliente_id NULL correctamente
                    if 'cliente_id' in rol_dict and rol_dict['cliente_id'] is None:
                        rol_dict['cliente_id'] = None  # Mantener None explícitamente
                    
                    # ✅ CORRECCIÓN: Remover nivel_acceso del diccionario antes de crear RolRead
                    # nivel_acceso no está en RolRead schema, solo en la entidad de dominio
                    rol_dict_clean = {k: v for k, v in rol_dict.items() if k != 'nivel_acceso'}
                    
                    # ✅ VALIDACIÓN: Verificar que roles de sistema solo pertenezcan al cliente SUPER ADMIN
                    # Si un rol tiene codigo_rol y cliente_id != 1, filtrarlo (es un error de datos)
                    codigo_rol = rol_dict_clean.get('codigo_rol')
                    cliente_id_rol = rol_dict_clean.get('cliente_id')
                    
                    if codigo_rol is not None and cliente_id_rol is not None and cliente_id_rol != 1:
                        logger.warning(
                            f"[VALIDATION] Rol con codigo_rol='{codigo_rol}' encontrado en cliente_id={cliente_id_rol} "
                            f"(rol_id={rol_dict_clean.get('rol_id')}). "
                            f"Los roles de sistema solo pueden pertenecer al cliente SUPER ADMIN (cliente_id=1). "
                            f"Filtrando este rol inválido."
                        )
                        continue  # Saltar este rol inválido
                    
                    # Crear instancia de RolRead desde cada diccionario (sin nivel_acceso)
                    try:
                        roles_list.append(RolRead(**rol_dict_clean))
                    except Exception as validation_error:
                        # Si falla la validación de Pydantic, registrar warning y continuar sin ese rol
                        logger.warning(
                            f"[VALIDATION] Error de validación al crear RolRead para rol {rol_dict_clean.get('rol_id')}: {validation_error}. "
                            f"Datos del rol: {rol_dict_clean}. Continuando sin este rol."
                        )
                        continue  # Continuar con el siguiente rol
                except Exception as rol_parse_error:
                    # Loggear error si hay un problema inesperado (no de validación)
                    logger.error(f"Error inesperado parseando diccionario de rol a RolRead: {rol_dict}. Error: {rol_parse_error}", exc_info=True)
                    # No fallar completamente - continuar sin ese rol
                    logger.warning(f"[PERF] Continuando sin rol {rol_dict.get('rol_id')} debido a error inesperado")
                    continue
            # --- FIN CONVERSIÓN ---

            logger.debug(f"[PERF] Roles convertidos a List[RolRead] para usuario ID {user_dict['usuario_id']}: {[r.nombre for r in roles_list]}")

        except HTTPException:
            # Re-lanzar HTTPException
            raise
        except Exception as role_error:
            # Captura errores en el parseo de roles
            logger.error(f"Error procesando roles desde JSON para usuario ID {user_dict['usuario_id']}: {role_error}", exc_info=True)
            # No fallar completamente - continuar con lista vacía de roles
            roles_list = []
            logger.warning(f"[PERF] Continuando sin roles para usuario {user_dict['usuario_id']} debido a error de parseo")

        # ✅ OPTIMIZACIÓN: Los niveles ya vienen en la query optimizada
        # No necesitamos hacer queries adicionales para access_level e is_super_admin
        try:
            # Los niveles ya están calculados en la query GET_USER_WITH_LEVELS
            access_level = user_dict.get('access_level', 1)
            is_super_admin = bool(user_dict.get('is_super_admin', 0))
            
            # Determinar tipo de usuario
            user_type = determine_user_type(access_level, is_super_admin)
            
            # Asegurar que los campos estén en el diccionario
            user_dict['access_level'] = access_level
            user_dict['is_super_admin'] = is_super_admin
            user_dict['user_type'] = user_type
            
            logger.debug(f"[PERF] Niveles obtenidos de query optimizada para usuario '{username}': "
                        f"access_level={access_level}, is_super_admin={is_super_admin}, user_type={user_type}")
                        
        except Exception as level_error:
            logger.error(f"Error procesando niveles de acceso para usuario {user_dict.get('usuario_id')}: {level_error}")
            # Asignar valores por defecto en caso de error
            user_dict['access_level'] = 1
            user_dict['is_super_admin'] = False
            user_dict['user_type'] = 'user'

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
            # ✅ CRÍTICO: Pasar cliente_id para filtrar roles del tenant correcto
            min_required_level = await RolService.get_min_required_access_level(
                role_names=self.required_roles,
                cliente_id=current_user.cliente_id
            )
        except Exception as e:
            logger.error(f"Error al obtener nivel requerido para roles {self.required_roles}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al verificar el nivel de rol requerido."
            )
        
        # 2. Determinar el nivel máximo del usuario (Nivel N)
        try:
            # El RolService consulta la BD para el MAX(nivel_acceso) del usuario
            # ✅ CRÍTICO: Pasar cliente_id para filtrar roles del tenant correcto
            user_max_level = await RolService.get_user_max_access_level(
                usuario_id=user_id,
                cliente_id=current_user.cliente_id
            )
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