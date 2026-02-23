# app/modules/modulos/presentation/endpoints_secciones.py
"""
Endpoints para la gestión de secciones de módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from typing import List, Dict
from uuid import UUID
import logging

from app.modules.modulos.presentation.schemas import ModuloSeccionRead, ModuloSeccionCreate, ModuloSeccionUpdate
from app.modules.modulos.application.services.modulo_seccion_service import ModuloSeccionService
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
    summary="Listar secciones de un módulo",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def listar_secciones_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    solo_activas: bool = Query(False, description="Filtrar solo activas (False = devuelve todas)"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Lista todas las secciones de un módulo."""
    try:
        secciones = await ModuloSeccionService.obtener_secciones_modulo(modulo_id, solo_activas)
        return {
            "success": True,
            "message": f"Secciones del módulo {modulo_id} obtenidas exitosamente.",
            "data": secciones
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/{seccion_id}/",
    response_model=dict,
    summary="Obtener detalle de sección",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_seccion(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene una sección específica por su ID."""
    try:
        seccion = await ModuloSeccionService.obtener_seccion_por_id(seccion_id)
        if not seccion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada.")
        return {
            "success": True,
            "message": "Sección recuperada exitosamente.",
            "data": seccion
        }
    except HTTPException:
        raise
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva sección",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def crear_seccion(
    seccion_data: ModuloSeccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Crea una nueva sección en un módulo."""
    try:
        seccion = await ModuloSeccionService.crear_seccion(seccion_data)
        return {
            "success": True,
            "message": f"Sección '{seccion.nombre}' creada exitosamente.",
            "data": seccion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/{seccion_id}/",
    response_model=dict,
    summary="Actualizar sección",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def actualizar_seccion(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    seccion_data: ModuloSeccionUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza una sección existente."""
    try:
        seccion = await ModuloSeccionService.actualizar_seccion(seccion_id, seccion_data)
        return {
            "success": True,
            "message": f"Sección '{seccion.nombre}' actualizada exitosamente.",
            "data": seccion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/{seccion_id}/",
    status_code=status.HTTP_200_OK,
    summary="Eliminar sección",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def eliminar_seccion(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Elimina una sección."""
    try:
        await ModuloSeccionService.eliminar_seccion(seccion_id)
        return {
            "success": True,
            "message": f"Sección con ID {seccion_id} eliminada exitosamente."
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{seccion_id}/activar/",
    response_model=dict,
    summary="Activar sección",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def activar_seccion(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Activa una sección."""
    try:
        seccion = await ModuloSeccionService.activar_seccion(seccion_id)
        return {
            "success": True,
            "message": f"Sección '{seccion.nombre}' activada exitosamente.",
            "data": seccion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{seccion_id}/desactivar/",
    response_model=dict,
    summary="Desactivar sección",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def desactivar_seccion(
    seccion_id: UUID = Path(..., description="ID de la sección"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Desactiva una sección."""
    try:
        seccion = await ModuloSeccionService.desactivar_seccion(seccion_id)
        return {
            "success": True,
            "message": f"Sección '{seccion.nombre}' desactivada exitosamente.",
            "data": seccion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/modulo/{modulo_id}/reordenar/",
    response_model=dict,
    summary="Reordenar secciones",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def reordenar_secciones(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    ordenes: Dict[UUID, int] = Body(..., description="Diccionario {seccion_id: nuevo_orden}"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Reordena las secciones de un módulo."""
    try:
        secciones = await ModuloSeccionService.reordenar_secciones(modulo_id, ordenes)
        return {
            "success": True,
            "message": "Secciones reordenadas exitosamente.",
            "data": secciones
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

