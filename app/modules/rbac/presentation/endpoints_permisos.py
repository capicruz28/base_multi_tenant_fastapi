# app/api/v1/endpoints/permisos.py
"""
Módulo de endpoints para la gestión granular de permisos de roles sobre elementos de menú.

Este módulo proporciona una API REST dedicada a las operaciones CRUD (Creación, Lectura, Actualización, Eliminación)
de la relación Rol-Menú-Permiso. Permite establecer qué acciones (ver, editar, eliminar)
puede realizar un rol específico sobre un determinado menú o característica.

Características principales:
- Gestión completa de la matriz de permisos (Rol x Menú x Acción).
- Autenticación JWT con requerimiento estricto del rol 'Administrador'.
- Manejo consistente de errores utilizando CustomException.
- Operación de asignación/actualización unificada (PUT).
- Eliminación (Revocación) del registro de permiso.
- **✅ MULTI-TENANT: Aislamiento de permisos por cliente_id.**
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from typing import List, Dict, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

# ✅ Importar Schemas actualizados desde schemas.py
from app.modules.rbac.presentation.schemas import PermisoRead, PermisoBase, RolMenuPermisoRead, RolMenuPermisoUpdate

# ✅ Schema para crear/actualizar permisos sin menu_id (viene de la URL)
class PermisoCreateUpdate(BaseModel):
    """
    Schema para crear/actualizar permisos en endpoint PUT.
    No incluye menu_id porque viene de la URL.
    """
    puede_ver: Optional[bool] = Field(None, description="Permiso para ver el menú")
    puede_crear: Optional[bool] = Field(None, description="Permiso para crear nuevos registros")
    puede_editar: Optional[bool] = Field(None, description="Permiso para editar contenido")
    puede_eliminar: Optional[bool] = Field(None, description="Permiso para eliminar contenido")
    puede_exportar: Optional[bool] = Field(None, description="Permiso para exportar datos")
    puede_imprimir: Optional[bool] = Field(None, description="Permiso para imprimir datos")
    puede_aprobar: Optional[bool] = Field(None, description="Permiso para aprobar acciones")
    permisos_extra: Optional[str] = Field(None, description="JSON con permisos específicos del módulo")
    
    class Config:
        from_attributes = True

class PermisoReadWithMenu(PermisoRead):
    menu_nombre: Optional[str] = None
    menu_url: Optional[str] = None
    menu_icono: Optional[str] = None

    class Config:
        from_attributes = True


# Importar Servicio
from app.modules.rbac.application.services.permiso_service import PermisoService

# Importar Excepciones personalizadas (Estandarizado a CustomException)
from app.core.exceptions import CustomException 
# from app.core.exceptions import ServiceError, ValidationError # ELIMINADAS/IGNORADAS

# Importar Dependencias de Autorización
from app.api.deps import get_current_active_user, RoleChecker

# Logging
from app.core.logging_config import get_logger
logger = get_logger(__name__)

router = APIRouter()

# Dependencia específica para requerir rol 'admin'
require_admin = RoleChecker(["Administrador"])

# ----------------------------------------------------------------------
# --- Endpoint para Asignar/Actualizar Permisos (PUT) ---
# ----------------------------------------------------------------------
@router.put(
    "/roles/{rol_id}/menus/{menu_id}/",
    response_model=PermisoRead,
    summary="Asignar o actualizar permisos de un rol sobre un menú",
    description="""
    Establece los permisos (ver, editar, eliminar) para un rol específico sobre un menú específico. 
    Si la asignación de permisos no existe, se crea. Si existe, se actualiza con los valores proporcionados.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Permiso creado/actualizado exitosamente
    - 403: Acceso denegado (rol o menú de otro cliente)
    - 404: Rol o Menú no encontrado
    - 422: Error de validación en los datos de entrada
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def set_permission(
    rol_id: UUID = Path(..., description="ID del rol"),
    menu_id: UUID = Path(..., description="ID del menú"),
    permisos_in: PermisoCreateUpdate = Body(...),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Asigna o actualiza los permisos `puede_ver`, `puede_editar`, `puede_eliminar`
    para el `rol_id` sobre el `menu_id`.

    Args:
        rol_id: ID del rol al que se le asigna el permiso.
        menu_id: ID del menú sobre el que se asigna el permiso.
        permisos_in: Objeto con los flags booleanos (puede_ver, puede_editar, puede_eliminar) a establecer.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        PermisoRead: La asignación de permiso resultante, con sus IDs de relación.

    Raises:
        HTTPException: En caso de rol/menú no encontrado (404), error de validación (422) o error interno (500).
    """
    logger.info(f"Solicitud PUT /permisos/roles/{rol_id}/menus/{menu_id}/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} para crear/actualizar")
    
    # ✅ CORRECCIÓN CRÍTICA: Usar cliente_id del contexto del tenant, no del usuario autenticado
    # Esto permite que superadmin opere en el contexto del tenant al que accede
    from app.core.tenant.context import get_current_client_id
    try:
        tenant_cliente_id = get_current_client_id()
    except RuntimeError:
        # Fallback: usar cliente_id del usuario si no hay contexto de tenant
        tenant_cliente_id = current_user.cliente_id
        logger.warning(f"No se pudo obtener cliente_id del contexto de tenant, usando cliente_id del usuario: {tenant_cliente_id}")
    
    logger.debug(f"[PERMISOS] Usando cliente_id del tenant: {tenant_cliente_id} (usuario autenticado: {current_user.cliente_id})")
    
    try:
        # ✅ Actualizado: Incluir todos los permisos extendidos
        updated_perm = await PermisoService.asignar_o_actualizar_permiso(
            cliente_id=tenant_cliente_id,
            rol_id=rol_id,
            menu_id=menu_id,
            puede_ver=permisos_in.puede_ver,
            puede_crear=permisos_in.puede_crear,
            puede_editar=permisos_in.puede_editar,
            puede_eliminar=permisos_in.puede_eliminar,
            puede_exportar=permisos_in.puede_exportar,
            puede_imprimir=permisos_in.puede_imprimir,
            puede_aprobar=permisos_in.puede_aprobar,
            permisos_extra=permisos_in.permisos_extra
        )
        logger.info(f"Permiso para Rol {rol_id} y Menú {menu_id} gestionado exitosamente en cliente {tenant_cliente_id}.")
        return updated_perm
    # MODIFICACIÓN: Capturar CustomException en lugar de ServiceError/ValidationError
    except CustomException as ce:
        logger.warning(f"Error de negocio al gestionar permiso (Rol: {rol_id}, Menú: {menu_id}) en cliente {tenant_cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint PUT /permisos/roles/{rol_id}/menus/{menu_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al gestionar el permiso.")

# ----------------------------------------------------------------------
# --- Endpoint para Obtener Permisos de un Rol (LISTA) ---
# ----------------------------------------------------------------------
@router.get(
    "/roles/{rol_id}/permisos/",
    response_model=List[PermisoReadWithMenu],
    summary="Obtener todos los permisos de un rol",
    description="""
    Devuelve una lista de todos los permisos asignados a un rol específico, incluyendo detalles del menú asociado (nombre, URL, ícono).

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Lista de permisos recuperada exitosamente
    - 403: Acceso denegado (rol de otro cliente)
    - 404: Rol no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def get_permissions_for_role(
    rol_id: UUID = Path(..., description="ID del rol"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Obtiene la lista de permisos para el rol con el ID especificado, con detalles de menú.

    Args:
        rol_id: ID del rol cuyos permisos se desean consultar.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        List[PermisoReadWithMenu]: Lista de permisos del rol, con información del menú.

    Raises:
        HTTPException: En caso de rol no encontrado (404) o error interno (500).
    """
    logger.debug(f"Solicitud GET /permisos/roles/{rol_id}/permisos/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id}")
    try:
        permisos = await PermisoService.obtener_permisos_por_rol(
            cliente_id=current_user.cliente_id,
            rol_id=rol_id
        )
        logger.debug(f"Permisos para Rol {rol_id} recuperados - Total: {len(permisos)}")
        return permisos
    # MODIFICACIÓN: Capturar CustomException
    except CustomException as ce:
        logger.error(f"Error de negocio al obtener permisos para Rol {rol_id} en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint GET /permisos/roles/{rol_id}/permisos/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener los permisos.")

# ----------------------------------------------------------------------
# --- Endpoint para Obtener Permiso Específico (GET) ---
# ----------------------------------------------------------------------
@router.get(
    "/roles/{rol_id}/menus/{menu_id}/",
    response_model=PermisoRead,
    summary="Obtener el permiso específico de un rol sobre un menú",
    description="""
    Devuelve los detalles de la asignación de permisos de un rol sobre un menú específico.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Permiso encontrado y devuelto
    - 403: Acceso denegado (permiso de otro cliente)
    - 404: Permiso (asignación Rol-Menú) no encontrado
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def get_specific_permission(
    rol_id: UUID = Path(..., description="ID del rol"),
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Obtiene el permiso específico para el `rol_id` y `menu_id`.

    Args:
        rol_id: ID del rol asociado al permiso.
        menu_id: ID del menú asociado al permiso.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        PermisoRead: La asignación de permiso encontrada.

    Raises:
        HTTPException: Si la asignación de permiso no existe (404) o hay error interno (500).
    """
    logger.debug(f"Solicitud GET /permisos/roles/{rol_id}/menus/{menu_id}/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id}")
    try:
        permiso_dict = await PermisoService.obtener_permiso_especifico(
            cliente_id=current_user.cliente_id,
            rol_id=rol_id,
            menu_id=menu_id
        )
        if permiso_dict is None:
            logger.warning(f"Permiso no encontrado para Rol {rol_id} y Menú {menu_id} en cliente {current_user.cliente_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Permiso no encontrado para Rol {rol_id} y Menú {menu_id}.")
        
        # ✅ Convertir diccionario a PermisoRead para validación correcta
        # Asegurar que todos los campos requeridos estén presentes con valores por defecto
        permiso_dict.setdefault('puede_ver', True)
        permiso_dict.setdefault('puede_crear', False)
        permiso_dict.setdefault('puede_editar', False)
        permiso_dict.setdefault('puede_eliminar', False)
        permiso_dict.setdefault('puede_exportar', False)
        permiso_dict.setdefault('puede_imprimir', False)
        permiso_dict.setdefault('puede_aprobar', False)
        permiso_dict.setdefault('permisos_extra', None)
        permiso_dict.setdefault('fecha_creacion', None)
        permiso_dict.setdefault('fecha_actualizacion', None)
        
        # ✅ Convertir a PermisoRead (el schema ya maneja permiso_id y tiene alias rol_menu_id)
        permiso = PermisoRead(**permiso_dict)
        return permiso
    # ✅ HTTPException debe propagarse sin ser capturado
    except HTTPException:
        raise
    # MODIFICACIÓN: Capturar CustomException
    except CustomException as ce:
        logger.error(f"Error de negocio al obtener permiso específico (Rol: {rol_id}, Menú: {menu_id}) en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint GET /permisos/roles/{rol_id}/menus/{menu_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al obtener el permiso.")


# ----------------------------------------------------------------------
# --- Endpoint para Revocar Permiso (DELETE) ---
# ----------------------------------------------------------------------
@router.delete(
    "/roles/{rol_id}/menus/{menu_id}/",
    response_model=Dict[str, str],
    summary="Revocar el permiso de un rol sobre un menú",
    description="""
    Elimina (revoca) la asignación de permisos entre un rol y un menú.

    **Permisos requeridos:**
    - Rol 'Administrador'

    **Respuestas:**
    - 200: Permiso revocado exitosamente
    - 403: Acceso denegado (permiso de otro cliente)
    - 404: Permiso no encontrado (no se puede eliminar lo que no existe)
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_admin)]
)
async def revoke_permission(
    rol_id: UUID = Path(..., description="ID del rol"),
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Elimina el permiso asociado al `rol_id` y `menu_id`.

    Args:
        rol_id: ID del rol al que se le revoca el permiso.
        menu_id: ID del menú del que se revoca el permiso.
        current_user: Usuario autenticado y activo (inyectado por dependencia).

    Returns:
        Dict[str, str]: Mensaje de éxito de la operación.

    Raises:
        HTTPException: Si el permiso no existe (404) o hay error interno (500).
    """
    logger.info(f"Solicitud DELETE /permisos/roles/{rol_id}/menus/{menu_id}/ recibida por usuario {current_user.usuario_id} del cliente {current_user.cliente_id} para revocar")
    try:
        result = await PermisoService.revocar_permiso(
            cliente_id=current_user.cliente_id,
            rol_id=rol_id,
            menu_id=menu_id
        )
        logger.info(f"Permiso para Rol {rol_id} y Menú {menu_id} revocado exitosamente en cliente {current_user.cliente_id}.")
        return result
    # MODIFICACIÓN: Capturar CustomException
    except CustomException as ce:
        logger.warning(f"Error de negocio al revocar permiso (Rol: {rol_id}, Menú: {menu_id}) en cliente {current_user.cliente_id}: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado en endpoint DELETE /permisos/roles/{rol_id}/menus/{menu_id}/")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor al revocar el permiso.")