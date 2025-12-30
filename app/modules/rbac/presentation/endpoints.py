# app/api/v1/endpoints/roles.py
"""
Módulo de endpoints para la gestión de roles y permisos de acceso.

Este módulo proporciona una API REST completa para operaciones CRUD sobre roles,
incluyendo la creación, lectura, actualización y desactivación de roles.
Además, gestiona las operaciones de asignación y revocación de permisos a cada rol.

Características principales:
- Autenticación JWT con requerimiento de rol 'Administrador' para todas las operaciones de gestión.
- Validación robusta de datos de entrada (Pydantic).
- Manejo consistente de errores de negocio con CustomException y mensajes descriptivos.
- Implementación de paginación y búsqueda para el listado de roles.
- Borrado lógico (`es_activo = False`) como mecanismo de desactivación, con opción de reactivación.
- Endpoints específicos para la gestión integral de permisos asociados a cada rol.
- **✅ MULTI-TENANT: Aislamiento de roles por cliente_id y gestión de roles del sistema.**
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from typing import List, Optional, Dict, Any
from uuid import UUID

# Importar Schemas
from app.modules.rbac.presentation.schemas import RolCreate, RolUpdate, RolRead, PaginatedRolResponse, PermisoRead, PermisoUpdatePayload

# Importar Servicio
from app.modules.rbac.application.services.rol_service import RolService

# Importar Excepciones personalizadas
from app.core.exceptions import CustomException

# Importar Dependencias de Autorización
from app.api.deps import get_current_active_user, RoleChecker

# Logging
from app.core.logging_config import get_logger
logger = get_logger(__name__)

router = APIRouter()

# --- CONFIGURACIÓN DE DEPENDENCIAS ---
# Requiere rol de administrador para todas las operaciones de gestión
require_admin = RoleChecker(["Administrador"])


# --- FUNCIÓN DE AYUDA PARA ROLES DEL SISTEMA ---
def _is_system_role(role_data: Dict) -> bool:
    """Determina si un rol es un rol del sistema."""
    return role_data.get('cliente_id') is None


def _can_manage_system_role(current_user: Any) -> bool:
    """Verifica si el usuario actual puede gestionar roles del sistema."""
    user_role_names = [role.nombre for role in current_user.roles]
    return "SUPER_ADMIN" in user_role_names


# ----------------------------------------------------------------------
# --- Endpoint para Crear Roles ---
# ----------------------------------------------------------------------
@router.post(
    "/",
    response_model=RolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
    description="""
    Crea un nuevo rol en el sistema **dentro del cliente del administrador**.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Validaciones:**
    - Nombre único **dentro del cliente**.
    - Campos obligatorios: nombre.

    **Respuestas:**
    - 201: Rol creado exitosamente
    - 403: Intento de crear un rol del sistema sin ser SUPER_ADMIN
    - 409: Conflicto - El nombre del rol ya existe **en el cliente**
    - 422: Error de validación en los datos de entrada
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def create_rol(
    rol_in: RolCreate = Body(...),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para crear un nuevo rol **asociado al cliente del administrador**.

    Args:
        rol_in: Datos validados del rol a crear (RolCreate).
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        RolRead: Rol creado con todos sus datos, incluyendo el ID generado.

    Raises:
        HTTPException: En caso de conflicto, error de validación o error interno.
    """
    logger.info(f"Solicitud POST /roles/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} para crear rol: '{rol_in.nombre}'")
    
    rol_dict = rol_in.model_dump()
    
    # ✅ MULTI-TENANT: Asignar cliente_id si no se especificó (para roles de cliente)
    if rol_dict.get('cliente_id') is None:
        rol_dict['cliente_id'] = current_user.cliente_id
    
    # ✅ CORRECCIÓN: Si se está creando un rol de cliente (con cliente_id), eliminar codigo_rol si existe
    # Los roles de cliente NO deben tener codigo_rol (solo los roles del sistema lo tienen)
    if rol_dict.get('cliente_id') is not None and rol_dict.get('codigo_rol') is not None:
        logger.debug(f"Eliminando codigo_rol '{rol_dict.get('codigo_rol')}' de rol de cliente. Los roles de cliente no deben tener codigo_rol.")
        rol_dict['codigo_rol'] = None
    
    # ✅ VALIDAR: Solo SUPER_ADMIN puede crear roles del sistema
    if _is_system_role(rol_dict) and not _can_manage_system_role(current_user):
        logger.warning(f"Usuario {current_user.usuario_id} intentó crear un rol del sistema sin permisos.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los SUPER_ADMIN pueden crear roles del sistema."
        )

    try:
        # ✅ Obtener cliente_id del rol_dict (ya asignado arriba)
        cliente_id_rol = rol_dict.get('cliente_id')
        if not cliente_id_rol:
            logger.error(f"No se pudo obtener cliente_id para crear rol. rol_dict: {rol_dict}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo determinar el cliente_id para crear el rol."
            )
        created_rol = await RolService.crear_rol(cliente_id=cliente_id_rol, rol_data=rol_dict)
        logger.info(f"Rol '{created_rol['nombre']}' creado exitosamente en cliente {current_user.cliente_id}.")
        return created_rol
    except CustomException as ce:
        logger.warning(f"Error de negocio al crear rol '{rol_in.nombre}' en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception("Error inesperado en endpoint POST /roles/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al crear el rol.")


# ----------------------------------------------------------------------
# --- Endpoint para Listar Roles (PAGINADO) ---
# ----------------------------------------------------------------------
@router.get(
    "/",
    response_model=dict,  # Cambiado a dict para evitar validación estricta que impide cliente_id en roles del sistema
    summary="Obtener lista paginada de roles",
    description="""
    Recupera una lista paginada de roles **del cliente actual y roles del sistema**.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Parámetros de consulta:**
    - page: Número de página a mostrar (comienza en 1)
    - limit: Número máximo de roles por página (1-100)
    - search: Término opcional para buscar en nombre o descripción

    **Respuestas:**
    - 200: Lista paginada recuperada exitosamente
    - 422: Parámetros de consulta inválidos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def read_roles_paginated(
    current_user: Any = Depends(get_current_active_user),
    page: int = Query(1, ge=1, description="Número de página a recuperar"),
    limit: int = Query(10, ge=1, le=100, description="Número de roles por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda para filtrar por nombre o descripción")
):
    """
    Endpoint para obtener una lista paginada y filtrada de roles **del cliente del usuario y roles del sistema**.

    Args:
        current_user: Usuario autenticado y activo (inyectado por dependencia).
        page: Número de página solicitada.
        limit: Límite de resultados por página.
        search: Término opcional para búsqueda textual.

    Returns:
        PaginatedRolResponse: Respuesta paginada con roles y metadatos.

    Raises:
        HTTPException: En caso de error en los parámetros o error interno.
    """
    logger.info(f"Solicitud GET /roles/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} - Paginación: page={page}, limit={limit}, Búsqueda: '{search}'")
    
    # ✅ VALIDACIÓN: Verificar que cliente_id es válido (UUID)
    from uuid import UUID
    cliente_id_valido = current_user.cliente_id
    if not cliente_id_valido:
        logger.error(f"Cliente ID inválido en endpoint /roles/: {current_user.cliente_id} para usuario {current_user.usuario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente ID no disponible en el contexto del usuario. No se puede obtener la lista de roles."
        )
    
    # Verificar que no sea UUID nulo
    if isinstance(cliente_id_valido, UUID) and cliente_id_valido == UUID('00000000-0000-0000-0000-000000000000'):
        logger.error(f"Cliente ID es UUID nulo en endpoint /roles/ para usuario {current_user.usuario_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente ID no disponible en el contexto del usuario. No se puede obtener la lista de roles."
        )
    
    try:
        paginated_response = await RolService.obtener_roles_paginados(
            cliente_id=current_user.cliente_id,
            page=page,
            limit=limit,
            search=search
        )
        logger.info(f"Respuesta exitosa para GET /roles/ - Cliente: {current_user.cliente_id}, Total roles: {paginated_response.get('total_roles', 0)}")
        return paginated_response
    except CustomException as ce:
        logger.warning(f"Error de negocio al listar roles para cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception("Error inesperado en endpoint GET /roles/ (paginado)")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener roles paginados.")


# ----------------------------------------------------------------------
# --- Endpoint para Obtener todos los roles activos ---
# ----------------------------------------------------------------------
@router.get(
    "/all-active/",
    response_model=List[RolRead],
    summary="Obtener todos los roles activos",
    description="""
    Devuelve una lista de todos los roles activos **del cliente actual y roles del sistema**.
    Ideal para selectores y listas desplegables en interfaces de usuario.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Lista simple recuperada exitosamente
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def read_all_active_roles(
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para obtener una lista simplificada de roles activos **del cliente y del sistema**.

    Args:
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        List[RolRead]: Lista de todos los roles activos.

    Raises:
        HTTPException: En caso de error interno del servidor.
    """
    logger.info(f"Solicitud GET /roles/all-active/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} para lista simple")
    try:
        active_roles_dicts = await RolService.get_all_active_roles(cliente_id=current_user.cliente_id)
        
        # ✅ Convertir dicts a RolRead para cumplir con el schema de respuesta
        from app.modules.rbac.presentation.schemas import RolRead
        active_roles = [RolRead(**rol_dict) for rol_dict in active_roles_dicts]
        
        logger.info(f"Lista simple de roles activos recuperada para cliente {current_user.cliente_id} - Total: {len(active_roles)}")
        return active_roles
    except CustomException as ce:
        logger.error(f"Error de servicio en endpoint /roles/all-active/ para cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception("Error inesperado en endpoint GET /roles/all-active/")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al intentar obtener los roles activos."
        )


# ----------------------------------------------------------------------
# --- Endpoint para Obtener un Rol por ID ---
# ----------------------------------------------------------------------
@router.get(
    "/{rol_id}/",
    response_model=RolRead,
    summary="Obtener un rol por ID",
    description="""
    Recupera los detalles completos de un rol específico por su ID.
    Permite obtener roles del cliente, roles del sistema y roles inactivos.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Rol encontrado y devuelto
    - 403: Acceso denegado (rol del sistema sin ser SUPER_ADMIN)
    - 404: Rol no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def read_rol(
    rol_id: UUID = Path(..., description="ID del rol"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para obtener los detalles completos de un rol específico.

    Args:
        rol_id: Identificador único del rol a consultar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        RolRead: Detalles completos del rol solicitado.

    Raises:
        HTTPException: Si el rol no existe, es de otro cliente, o hay error interno.
    """
    logger.debug(f"Solicitud GET /roles/{rol_id}/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id}")
    try:
        rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol is None:
            logger.warning(f"Rol con ID {rol_id} no encontrado")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        # ✅ VALIDAR: El rol debe pertenecer al cliente o ser del sistema (y tener permiso)
        rol_cliente_id = rol.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            logger.warning(f"Acceso denegado: El rol {rol_id} no pertenece al cliente {current_user.cliente_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None and not _can_manage_system_role(current_user):
            logger.warning(f"Acceso denegado: El rol {rol_id} es del sistema y el usuario no es SUPER_ADMIN")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para acceder a roles del sistema.")
        
        logger.debug(f"Rol ID {rol_id} encontrado: '{rol['nombre']}'")
        return rol
    except CustomException as ce:
        logger.error(f"Error de servicio obteniendo rol ID {rol_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint GET /roles/{rol_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener el rol.")


# ----------------------------------------------------------------------
# --- Endpoint para Actualizar un Rol ---
# ----------------------------------------------------------------------
@router.put(
    "/{rol_id}/",
    response_model=RolRead,
    summary="Actualizar un rol existente",
    description="""
    Actualiza la información de un rol existente mediante operación parcial.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Validaciones:**
    - Si se actualiza el nombre, debe mantenerse único **dentro del cliente**.
    - Al menos un campo debe ser proporcionado.

    **Respuestas:**
    - 200: Rol actualizado exitosamente
    - 400: Cuerpo de solicitud vacío
    - 403: Acceso denegado (rol del sistema sin ser SUPER_ADMIN)
    - 404: Rol no encontrado
    - 409: Conflicto - Nuevo nombre ya existe **en el cliente**
    - 422: Error de validación en los datos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def update_rol(
    rol_id: UUID = Path(..., description="ID del rol"),
    rol_in: RolUpdate = Body(...),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para actualizar parcialmente un rol existente **del cliente del usuario**.

    Args:
        rol_id: Identificador único del rol a actualizar.
        rol_in: Campos a actualizar (actualización parcial).
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        RolRead: Rol actualizado con los nuevos datos.

    Raises:
        HTTPException: En caso de cuerpo vacío, rol no encontrado, conflicto o error interno.
    """
    logger.info(f"Solicitud PUT /roles/{rol_id}/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} para actualizar")
    
    update_data = rol_in.model_dump(exclude_unset=True)
    if not update_data:
         logger.warning(f"Intento de actualizar rol {rol_id} sin datos")
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Se debe proporcionar al menos un campo para actualizar el rol."
         )

    try:
        # ✅ VALIDAR: El rol debe pertenecer al cliente o ser del sistema (y tener permiso)
        rol_existente = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol_existente is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        rol_cliente_id = rol_existente.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None and not _can_manage_system_role(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para editar roles del sistema.")

        updated_rol = await RolService.actualizar_rol(rol_id=rol_id, rol_data=update_data)
        logger.info(f"Rol ID {rol_id} actualizado exitosamente: '{updated_rol['nombre']}'")
        return updated_rol
    except CustomException as ce:
        logger.warning(f"Error de negocio al actualizar rol {rol_id} en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint PUT /roles/{rol_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al actualizar el rol.")


# ----------------------------------------------------------------------
# --- Endpoint para Desactivar un Rol (Borrado Lógico) ---
# ----------------------------------------------------------------------
@router.delete(
    "/{rol_id}/",
    response_model=RolRead,
    summary="Desactivar un rol (Borrado Lógico)",
    description="""
    Desactiva un rol estableciendo su estado 'es_activo' a False (borrado lógico).

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Notas:**
    - Operación reversible mediante el endpoint de reactivación.
    - No elimina físicamente el registro.
    - **No se puede desactivar un rol del sistema.**

    **Respuestas:**
    - 200: Rol desactivado exitosamente
    - 403: Acceso denegado (rol del sistema o fuera de cliente)
    - 404: Rol no encontrado
    - 400: Rol ya está desactivado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def deactivate_rol(
    rol_id: UUID = Path(..., description="ID del rol"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para desactivar un rol (borrado lógico) **del cliente del usuario**.

    Args:
        rol_id: Identificador único del rol a desactivar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        RolRead: El rol con el estado `es_activo=False`.

    Raises:
        HTTPException: Si el rol no existe, es de otro cliente o es del sistema.
    """
    logger.info(f"Solicitud DELETE /roles/{rol_id}/ recibida (desactivar) por usuario {current_user.usuario_id} del cliente {current_user.cliente_id}")
    try:
        # ✅ VALIDAR antes de desactivar
        rol_existente = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol_existente is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        rol_cliente_id = rol_existente.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pueden desactivar los roles del sistema.")

        deactivated_rol = await RolService.desactivar_rol(rol_id=rol_id)
        logger.info(f"Rol ID {rol_id} desactivado exitosamente en cliente {current_user.cliente_id}")
        return deactivated_rol
    except CustomException as ce:
        logger.warning(f"No se pudo desactivar rol {rol_id} en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint DELETE /roles/{rol_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al desactivar el rol.")


# ----------------------------------------------------------------------
# --- Endpoint para Reactivar un Rol ---
# ----------------------------------------------------------------------
@router.post(
    "/{rol_id}/reactivate/",
    response_model=RolRead,
    status_code=status.HTTP_200_OK,
    summary="Reactivar un rol desactivado",
    description="""
    Reactiva un rol previamente desactivado estableciendo 'es_activo' a True.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Rol reactivado exitosamente
    - 403: Acceso denegado (rol del sistema o fuera de cliente)
    - 404: Rol no encontrado
    - 400: Rol ya está activo
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def reactivate_rol(
    rol_id: UUID = Path(..., description="ID del rol"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para reactivar un rol inactivo **del cliente del usuario**.

    Args:
        rol_id: Identificador único del rol a reactivar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        RolRead: El rol con el estado `es_activo=True`.

    Raises:
        HTTPException: Si el rol no existe o es de otro cliente.
    """
    logger.info(f"Solicitud POST /roles/{rol_id}/reactivate/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id}")
    try:
        # ✅ VALIDAR antes de reactivar
        rol_existente = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol_existente is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        rol_cliente_id = rol_existente.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pueden reactivar los roles del sistema.")

        reactivated_rol = await RolService.reactivar_rol(rol_id=rol_id)
        logger.info(f"Rol ID {rol_id} reactivado exitosamente en cliente {current_user.cliente_id}")
        return reactivated_rol
    except CustomException as ce:
        logger.warning(f"No se pudo reactivar rol {rol_id} en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint POST /roles/{rol_id}/reactivate/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al reactivar el rol.")


# ----------------------------------------------------------------------
# --- Endpoint para Obtener Permisos de un Rol ---
# ----------------------------------------------------------------------
@router.get(
    "/{rol_id}/permisos/",
    response_model=List[PermisoRead],
    summary="Obtener Permisos de un Rol",
    description="""
    Obtiene la lista de permisos de menú activos asignados a un rol específico.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Lista de permisos recuperada
    - 403: Acceso denegado (rol del sistema sin ser SUPER_ADMIN)
    - 404: Rol no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def get_permisos_por_rol(
    rol_id: UUID = Path(..., title="ID del Rol", description="El ID del rol para consultar sus permisos"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para obtener los permisos activos asignados a un rol.

    Args:
        rol_id: Identificador único del rol a consultar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        List[PermisoRead]: Lista de roles activos asignados al usuario.

    Raises:
        HTTPException: Si el rol no existe o hay error interno.
    """
    logger.info(f"Solicitud recibida en GET /roles/{rol_id}/permisos/ por usuario {current_user.usuario_id}")
    try:
        # ✅ VALIDAR acceso al rol antes de obtener permisos
        rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        rol_cliente_id = rol.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None and not _can_manage_system_role(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para acceder a roles del sistema.")

        permisos = await RolService.obtener_permisos_por_rol(rol_id=rol_id)
        logger.debug(f"Permisos para rol {rol_id} recuperados - Total: {len(permisos)}")
        return permisos
    except CustomException as ce:
        logger.error(f"Error de servicio obteniendo permisos para rol {rol_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al obtener permisos para rol {rol_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los permisos del rol."
        )


# ----------------------------------------------------------------------
# --- Endpoint para Actualizar Permisos de un Rol ---
# ----------------------------------------------------------------------
@router.put(
    "/{rol_id}/permisos/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Actualizar Permisos de un Rol",
    description="""
    Sobrescribe **TODOS** los permisos de menú para un rol específico.
    La lista enviada reemplazará completamente la lista actual de permisos.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 204: Permisos actualizados exitosamente (No Content)
    - 403: Acceso denegado (rol del sistema sin ser SUPER_ADMIN)
    - 404: Rol no encontrado
    - 422: Error de validación en la lista de permisos
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def update_permisos_rol(
    rol_id: UUID = Path(..., title="ID del Rol", description="El ID del rol cuyos permisos se actualizarán"),
    payload: PermisoUpdatePayload = Body(..., description="Objeto que contiene la lista completa de los nuevos permisos para el rol"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Endpoint para sobrescribir la lista de permisos de un rol.

    Args:
        rol_id: Identificador único del rol a actualizar.
        payload: Objeto que contiene la lista completa de IDs de permisos a asignar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        None: Respuesta sin contenido (204).

    Raises:
        HTTPException: Si el rol no existe, hay error de validación o error interno.
    """
    logger.info(f"Solicitud recibida en PUT /roles/{rol_id}/permisos/ por usuario {current_user.usuario_id}")
    try:
        # ✅ VALIDAR acceso al rol
        rol = await RolService.obtener_rol_por_id(rol_id=rol_id, incluir_inactivos=True)
        if rol is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol con ID {rol_id} no encontrado.")
        
        rol_cliente_id = rol.get('cliente_id')
        if rol_cliente_id is not None and rol_cliente_id != current_user.cliente_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El rol no pertenece a su cliente.")
        
        if rol_cliente_id is None and not _can_manage_system_role(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para editar roles del sistema.")

        await RolService.actualizar_permisos_rol(rol_id=rol_id, permisos_payload=payload)
        logger.info(f"Permisos para rol {rol_id} actualizados exitosamente")
        return None
    except CustomException as ce:
        logger.error(f"Error de servicio al actualizar permisos para rol {rol_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al actualizar permisos para rol {rol_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar los permisos del rol."
        )