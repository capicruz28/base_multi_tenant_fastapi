# app/modules/modulos/presentation/endpoints_plantillas.py
"""
Endpoints para la gestión de plantillas de roles de módulos.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from typing import List, Dict
from uuid import UUID
import logging

from app.modules.modulos.presentation.schemas import (
    ModuloRolPlantillaRead, ModuloRolPlantillaCreate, ModuloRolPlantillaUpdate
)
from app.modules.modulos.application.services.modulo_rol_plantilla_service import ModuloRolPlantillaService
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
    summary="Listar plantillas de un módulo",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def listar_plantillas_modulo(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    solo_activas: bool = Query(False, description="Filtrar solo activas (False = devuelve todas)"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Lista todas las plantillas de roles de un módulo."""
    try:
        plantillas = await ModuloRolPlantillaService.obtener_plantillas_modulo(modulo_id, solo_activas)
        return {
            "success": True,
            "message": f"Plantillas del módulo {modulo_id} obtenidas exitosamente.",
            "data": plantillas
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/{plantilla_id}/",
    response_model=dict,
    summary="Obtener detalle de plantilla",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
async def obtener_plantilla(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Obtiene una plantilla específica por su ID."""
    try:
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada.")
        return {
            "success": True,
            "message": "Plantilla recuperada exitosamente.",
            "data": plantilla
        }
    except HTTPException:
        raise
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva plantilla",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def crear_plantilla(
    plantilla_data: ModuloRolPlantillaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Crea una nueva plantilla de rol para un módulo."""
    try:
        plantilla = await ModuloRolPlantillaService.crear_plantilla(plantilla_data)
        return {
            "success": True,
            "message": f"Plantilla '{plantilla.nombre_rol}' creada exitosamente.",
            "data": plantilla
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/{plantilla_id}/",
    response_model=dict,
    summary="Actualizar plantilla",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def actualizar_plantilla(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    plantilla_data: ModuloRolPlantillaUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Actualiza una plantilla existente."""
    try:
        plantilla = await ModuloRolPlantillaService.actualizar_plantilla(plantilla_id, plantilla_data)
        return {
            "success": True,
            "message": f"Plantilla '{plantilla.nombre_rol}' actualizada exitosamente.",
            "data": plantilla
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/{plantilla_id}/",
    status_code=status.HTTP_200_OK,
    summary="Eliminar plantilla",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def eliminar_plantilla(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Elimina una plantilla."""
    try:
        await ModuloRolPlantillaService.eliminar_plantilla(plantilla_id)
        return {
            "success": True,
            "message": f"Plantilla con ID {plantilla_id} eliminada exitosamente."
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{plantilla_id}/activar/",
    response_model=dict,
    summary="Activar plantilla",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def activar_plantilla(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Activa una plantilla."""
    try:
        plantilla = await ModuloRolPlantillaService.activar_plantilla(plantilla_id)
        return {
            "success": True,
            "message": f"Plantilla '{plantilla.nombre_rol}' activada exitosamente.",
            "data": plantilla
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.patch(
    "/{plantilla_id}/desactivar/",
    response_model=dict,
    summary="Desactivar plantilla",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def desactivar_plantilla(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Desactiva una plantilla."""
    try:
        plantilla = await ModuloRolPlantillaService.desactivar_plantilla(plantilla_id)
        return {
            "success": True,
            "message": f"Plantilla '{plantilla.nombre_rol}' desactivada exitosamente.",
            "data": plantilla
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/modulo/{modulo_id}/reordenar/",
    response_model=dict,
    summary="Reordenar plantillas",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def reordenar_plantillas(
    modulo_id: UUID = Path(..., description="ID del módulo"),
    ordenes: Dict[UUID, int] = Body(..., description="Diccionario {plantilla_id: nuevo_orden}"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Reordena las plantillas de un módulo."""
    try:
        plantillas = await ModuloRolPlantillaService.reordenar_plantillas(modulo_id, ordenes)
        return {
            "success": True,
            "message": "Plantillas reordenadas exitosamente.",
            "data": plantillas
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/{plantilla_id}/validar-json/",
    response_model=dict,
    summary="Validar JSON de permisos",
    dependencies=[Depends(require_permission("modulos.menu.administrar"))],
)
@require_super_admin()
async def validar_json_permisos(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    permisos_json: str = Body(..., description="JSON de permisos a validar"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Valida la estructura del JSON de permisos de una plantilla."""
    try:
        plantilla = await ModuloRolPlantillaService.obtener_plantilla_por_id(plantilla_id)
        if not plantilla:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla no encontrada.")
        
        validacion = await ModuloRolPlantillaService.validar_json_permisos(permisos_json, plantilla.modulo_id)
        return {
            "success": True,
            "message": "JSON de permisos válido.",
            "data": validacion
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.get(
    "/{plantilla_id}/preview-aplicacion/{cliente_id}/",
    response_model=dict,
    summary="Preview de aplicación de plantilla",
    dependencies=[Depends(require_permission("modulos.menu.leer"))],
)
@require_super_admin()
async def preview_aplicacion(
    plantilla_id: UUID = Path(..., description="ID de la plantilla"),
    cliente_id: UUID = Path(..., description="ID del cliente"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    """Muestra un preview de qué se creará al aplicar la plantilla (sin ejecutar)."""
    try:
        preview = await ModuloRolPlantillaService.preview_aplicacion(plantilla_id, cliente_id)
        return {
            "success": True,
            "message": "Preview de aplicación generado exitosamente.",
            "data": preview
        }
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

