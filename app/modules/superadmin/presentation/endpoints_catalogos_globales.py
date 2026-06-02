from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.api.deps import get_current_active_user
from app.core.authorization.lbac import require_super_admin
from app.core.exceptions import CustomException
from app.modules.superadmin.application.services.catalogos_globales_service import (
    CatalogosGlobalesService,
)
from app.modules.superadmin.presentation.schemas_catalogos_globales import (
    CatMonedaCreate,
    CatMonedaUpdate,
    CatMonedaRead,
    CatPaisCreate,
    CatPaisUpdate,
    CatPaisRead,
    CatDepartamentoCreate,
    CatDepartamentoUpdate,
    CatDepartamentoRead,
    CatProvinciaCreate,
    CatProvinciaUpdate,
    CatProvinciaRead,
    CatDistritoCreate,
    CatDistritoUpdate,
    CatDistritoRead,
)


router = APIRouter()


def _resolve_target_client_id(current_user, cliente_id: Optional[UUID]) -> UUID:
    target = cliente_id or getattr(current_user, "cliente_id", None)
    if not target:
        raise HTTPException(status_code=400, detail="cliente_id es requerido en este contexto")
    return target


# ----------------------------------------------------------------------
# Monedas (cat_moneda)
# ----------------------------------------------------------------------
@router.get(
    "/monedas",
    response_model=list[CatMonedaRead],
    summary="Listar monedas (cat_moneda) (Superadmin)",
)
@require_super_admin()
async def list_monedas(
    solo_activos: bool = Query(True),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.list_monedas(client_id=target, solo_activos=solo_activos)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/monedas",
    response_model=CatMonedaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear moneda (cat_moneda) (Superadmin)",
)
@require_super_admin()
async def create_moneda(
    data: CatMonedaCreate,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.create_moneda(client_id=target, data=data.model_dump())
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/monedas/{moneda_id}",
    response_model=CatMonedaRead,
    summary="Actualizar moneda (cat_moneda) (Superadmin)",
)
@require_super_admin()
async def update_moneda(
    moneda_id: UUID = Path(...),
    data: CatMonedaUpdate = ...,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.update_moneda(
            client_id=target,
            moneda_id=moneda_id,
            data=data.model_dump(exclude_unset=True),
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/monedas/{moneda_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar moneda (cat_moneda) (Superadmin)",
)
@require_super_admin()
async def deactivate_moneda(
    moneda_id: UUID = Path(...),
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        await CatalogosGlobalesService.deactivate_moneda(client_id=target, moneda_id=moneda_id)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


# ----------------------------------------------------------------------
# Países (cat_pais)
# ----------------------------------------------------------------------
@router.get(
    "/paises",
    response_model=list[CatPaisRead],
    summary="Listar países (cat_pais) (Superadmin)",
)
@require_super_admin()
async def list_paises(
    solo_activos: bool = Query(True),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.list_paises(client_id=target, solo_activos=solo_activos)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/paises",
    response_model=CatPaisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear país (cat_pais) (Superadmin)",
)
@require_super_admin()
async def create_pais(
    data: CatPaisCreate,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.create_pais(client_id=target, data=data.model_dump())
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/paises/{pais_id}",
    response_model=CatPaisRead,
    summary="Actualizar país (cat_pais) (Superadmin)",
)
@require_super_admin()
async def update_pais(
    pais_id: UUID = Path(...),
    data: CatPaisUpdate = ...,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.update_pais(
            client_id=target,
            pais_id=pais_id,
            data=data.model_dump(exclude_unset=True),
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/paises/{pais_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar país (cat_pais) (Superadmin)",
)
@require_super_admin()
async def deactivate_pais(
    pais_id: UUID = Path(...),
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        await CatalogosGlobalesService.deactivate_pais(client_id=target, pais_id=pais_id)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


# ----------------------------------------------------------------------
# Departamentos (cat_departamento)
# ----------------------------------------------------------------------
@router.get(
    "/departamentos",
    response_model=list[CatDepartamentoRead],
    summary="Listar departamentos (cat_departamento) (Superadmin)",
)
@require_super_admin()
async def list_departamentos(
    solo_activos: bool = Query(True),
    pais_id: Optional[UUID] = Query(None),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.list_departamentos(client_id=target, pais_id=pais_id, solo_activos=solo_activos)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/departamentos",
    response_model=CatDepartamentoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear departamento (cat_departamento) (Superadmin)",
)
@require_super_admin()
async def create_departamento(
    data: CatDepartamentoCreate,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.create_departamento(client_id=target, data=data.model_dump())
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/departamentos/{departamento_id}",
    response_model=CatDepartamentoRead,
    summary="Actualizar departamento (cat_departamento) (Superadmin)",
)
@require_super_admin()
async def update_departamento(
    departamento_id: UUID = Path(...),
    data: CatDepartamentoUpdate = ...,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.update_departamento(
            client_id=target,
            departamento_id=departamento_id,
            data=data.model_dump(exclude_unset=True),
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/departamentos/{departamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar departamento (cat_departamento) (Superadmin)",
)
@require_super_admin()
async def delete_departamento(
    departamento_id: UUID = Path(...),
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        await CatalogosGlobalesService.delete_departamento(client_id=target, departamento_id=departamento_id)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


# ----------------------------------------------------------------------
# Provincias (cat_provincia)
# ----------------------------------------------------------------------
@router.get(
    "/provincias",
    response_model=list[CatProvinciaRead],
    summary="Listar provincias (cat_provincia) (Superadmin)",
)
@require_super_admin()
async def list_provincias(
    solo_activos: bool = Query(True),
    departamento_id: Optional[UUID] = Query(None),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.list_provincias(client_id=target, departamento_id=departamento_id, solo_activos=solo_activos)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/provincias",
    response_model=CatProvinciaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear provincia (cat_provincia) (Superadmin)",
)
@require_super_admin()
async def create_provincia(
    data: CatProvinciaCreate,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.create_provincia(client_id=target, data=data.model_dump())
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/provincias/{provincia_id}",
    response_model=CatProvinciaRead,
    summary="Actualizar provincia (cat_provincia) (Superadmin)",
)
@require_super_admin()
async def update_provincia(
    provincia_id: UUID = Path(...),
    data: CatProvinciaUpdate = ...,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.update_provincia(
            client_id=target,
            provincia_id=provincia_id,
            data=data.model_dump(exclude_unset=True),
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/provincias/{provincia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar provincia (cat_provincia) (Superadmin)",
)
@require_super_admin()
async def delete_provincia(
    provincia_id: UUID = Path(...),
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        await CatalogosGlobalesService.delete_provincia(client_id=target, provincia_id=provincia_id)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


# ----------------------------------------------------------------------
# Distritos (cat_distrito)
# ----------------------------------------------------------------------
@router.get(
    "/distritos",
    response_model=list[CatDistritoRead],
    summary="Listar distritos (cat_distrito) (Superadmin)",
)
@require_super_admin()
async def list_distritos(
    solo_activos: bool = Query(True),
    provincia_id: Optional[UUID] = Query(None),
    ubigeo: Optional[str] = Query(None, min_length=1, max_length=6),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.list_distritos(
            client_id=target,
            provincia_id=provincia_id,
            ubigeo=ubigeo,
            solo_activos=solo_activos,
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.post(
    "/distritos",
    response_model=CatDistritoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear distrito (cat_distrito) (Superadmin)",
)
@require_super_admin()
async def create_distrito(
    data: CatDistritoCreate,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.create_distrito(client_id=target, data=data.model_dump())
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.put(
    "/distritos/{distrito_id}",
    response_model=CatDistritoRead,
    summary="Actualizar distrito (cat_distrito) (Superadmin)",
)
@require_super_admin()
async def update_distrito(
    distrito_id: UUID = Path(...),
    data: CatDistritoUpdate = ...,
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        return await CatalogosGlobalesService.update_distrito(
            client_id=target,
            distrito_id=distrito_id,
            data=data.model_dump(exclude_unset=True),
        )
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)


@router.delete(
    "/distritos/{distrito_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar distrito (cat_distrito) (Superadmin)",
)
@require_super_admin()
async def delete_distrito(
    distrito_id: UUID = Path(...),
    cliente_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        await CatalogosGlobalesService.delete_distrito(client_id=target, distrito_id=distrito_id)
    except CustomException as ce:
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)

