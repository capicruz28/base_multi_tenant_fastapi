# app/modules/modulos/presentation/endpoints_menus.py
"""
Endpoints para la gestión de menús de módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from typing import List, Optional, Dict
from uuid import UUID
import logging

from app.modules.modulos.presentation.schemas import (
    ModuloMenuRead, ModuloMenuCreate, ModuloMenuUpdate, MenuUsuarioResponse
)
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.core.exceptions import CustomException
from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/modulo/{modulo_id}/",
    response_model=dict,
    summary="Listar menús de un módulo",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def listar_menus_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    seccion_id: Optional[UUID] = Query(None, description="Filtrar por sección"),
    solo_activos: bool = Query(False, description="Filtrar solo activos (False = devuelve todos)"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Lista todos los menús de un módulo."""
    try:
        menus = await ModuloMenuService.obtener_menus_modulo(modulo_id, seccion_id, solo_activos)
        return {
            "success": True,
            "message": f"Menús del módulo {modulo_id} obtenidos exitosamente.",
            "data": menus
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/me/",
    response_model=MenuUsuarioResponse,
    summary="Obtener mi menú de navegación (usuario actual)",
    description="""
    Obtiene el menú completo del **usuario autenticado** para el **tenant actual** (sin pasar IDs en la URL).
    
    - Usa el `usuario_id` y `cliente_id` del token.
    - **Usuario normal:** solo ve módulos contratados y menús según sus permisos por rol.
    - **Admin tenant:** mismo criterio (módulos contratados + permisos de sus roles).
    - **SuperAdmin:** ve todos los menús de los módulos contratados del tenant con permisos completos.
    
    **Uso recomendado:** Llamar a este endpoint para construir el sidebar (una sola petición).
    
    **Respuestas:**
    - 200: Menú del usuario obtenido exitosamente
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_mi_menu(
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene el menú del usuario actual (tenant del token). Diferenciación automática por rol."""
    logger.info(f"Solicitud GET /modulos-menus/me/ recibida para usuario {current_user.usuario_id}")
    try:
        is_super_admin = getattr(current_user, "is_super_admin", False)
        access_level = getattr(current_user, "access_level", 1)
        as_tenant_admin = (access_level >= 4 and not is_super_admin)
        menu = await ModuloMenuService.obtener_menu_usuario(
            usuario_id=current_user.usuario_id,
            cliente_id=current_user.cliente_id,
            is_super_admin=is_super_admin,
            as_tenant_admin=as_tenant_admin,
        )
        logger.info(f"Menú /me/ obtenido exitosamente para usuario {current_user.usuario_id}")
        return menu
    except CustomException as ce:
        logger.error(f"Error al obtener menú /me/: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al obtener menú /me/: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener menú del usuario.",
        )


@router.get(
    "/{menu_id}/",
    response_model=dict,
    summary="Obtener detalle de menú",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_menu(
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene un menú específico por su ID."""
    try:
        menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
        if not menu:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menú no encontrado.")
        return {
            "success": True,
            "message": "Menú recuperado exitosamente.",
            "data": menu
        }
    except HTTPException:
        raise
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/usuario/{usuario_id}/",
    response_model=MenuUsuarioResponse,
    summary="Obtener menú completo de un usuario (por ID)",
    description="""
    Obtiene el menú completo de un usuario dado su ID (mismo tenant que el token).
    
    - Si el solicitante es **SuperAdmin** y pide su propio menú (`usuario_id` = usuario actual), recibe todos los menús con permisos completos.
    - En el resto de casos se aplica el filtro por permisos por rol.
    
    **Respuestas:**
    - 200: Menú del usuario obtenido exitosamente
    - 500: Error interno del servidor
    """,
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_menu_usuario(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene el menú de un usuario por ID. SuperAdmin recibe menú completo solo cuando pide el suyo."""
    logger.info(f"Solicitud GET /modulos-menus/usuario/{usuario_id}/ recibida")
    try:
        cliente_id = current_user.cliente_id
        is_own_user = str(current_user.usuario_id) == str(usuario_id)
        is_super_admin = getattr(current_user, "is_super_admin", False) and is_own_user
        access_level = getattr(current_user, "access_level", 1)
        as_tenant_admin = (access_level >= 4 and not getattr(current_user, "is_super_admin", False) and is_own_user)
        menu = await ModuloMenuService.obtener_menu_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            is_super_admin=is_super_admin,
            as_tenant_admin=as_tenant_admin,
        )
        logger.info(f"Menú del usuario {usuario_id} obtenido exitosamente")
        return menu
    except CustomException as ce:
        logger.error(f"Error al obtener menú del usuario: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception(f"Error inesperado al obtener menú del usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener menú del usuario."
        )


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo menú",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def crear_menu(
    menu_data: ModuloMenuCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Crea un nuevo menú en un módulo."""
    try:
        menu = await ModuloMenuService.crear_menu(menu_data)
        return {
            "success": True,
            "message": f"Menú '{menu.nombre}' creado exitosamente.",
            "data": menu
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/{menu_id}/",
    response_model=dict,
    summary="Actualizar menú",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def actualizar_menu(
    menu_id: UUID = Path(..., description="ID del menú"),
    menu_data: ModuloMenuUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza un menú existente."""
    try:
        menu = await ModuloMenuService.actualizar_menu(menu_id, menu_data)
        return {
            "success": True,
            "message": f"Menú '{menu.nombre}' actualizado exitosamente.",
            "data": menu
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/{menu_id}/",
    status_code=status.HTTP_200_OK,
    summary="Eliminar menú",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def eliminar_menu(
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Elimina un menú."""
    try:
        await ModuloMenuService.eliminar_menu(menu_id)
        return {
            "success": True,
            "message": f"Menú con ID {menu_id} eliminado exitosamente."
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{menu_id}/activar/",
    response_model=dict,
    summary="Activar menú",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def activar_menu(
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Activa un menú."""
    try:
        menu = await ModuloMenuService.activar_menu(menu_id)
        return {
            "success": True,
            "message": f"Menú '{menu.nombre}' activado exitosamente.",
            "data": menu
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{menu_id}/desactivar/",
    response_model=dict,
    summary="Desactivar menú",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def desactivar_menu(
    menu_id: UUID = Path(..., description="ID del menú"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Desactiva un menú."""
    try:
        menu = await ModuloMenuService.desactivar_menu(menu_id)
        return {
            "success": True,
            "message": f"Menú '{menu.nombre}' desactivado exitosamente.",
            "data": menu
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/seccion/{seccion_id}/reordenar/",
    response_model=dict,
    summary="Reordenar menús",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def reordenar_menus(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    ordenes: Dict[UUID, int] = Body(..., description="Diccionario {menu_id: nuevo_orden}"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Reordena los menús dentro de una sección."""
    try:
        menus = await ModuloMenuService.reordenar_menus(seccion_id, ordenes)
        return {
            "success": True,
            "message": "Menús reordenados exitosamente.",
            "data": menus
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/{menu_id}/duplicar/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicar menú para personalización",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def duplicar_menu(
    menu_id: UUID = Path(..., description="ID del menú a duplicar"),
    cliente_id: UUID = Body(..., description="ID del cliente"),
    nuevo_nombre: Optional[str] = Body(None, description="Nuevo nombre para el menú duplicado"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Duplica un menú para crear una versión personalizada para un cliente."""
    try:
        menu = await ModuloMenuService.duplicar_menu(menu_id, cliente_id, nuevo_nombre)
        return {
            "success": True,
            "message": f"Menú duplicado exitosamente.",
            "data": menu
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

