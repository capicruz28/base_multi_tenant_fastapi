from math import ceil
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
    PaginatedCatMonedaResponse,
    PaginatedCatPaisResponse,
    PaginatedCatDepartamentoResponse,
    PaginatedCatProvinciaResponse,
    PaginatedCatDistritoResponse,
)


router = APIRouter()


def _resolve_target_client_id(current_user, cliente_id: Optional[UUID]) -> UUID:
    target = cliente_id or getattr(current_user, "cliente_id", None)
    if not target:
        raise HTTPException(status_code=400, detail="cliente_id es requerido en este contexto")
    return target


def _paginated_metadata(total: int, skip: int, limit: int) -> tuple[int, int]:
    total_paginas = ceil(total / limit) if limit > 0 else 0
    pagina_actual = (skip // limit) + 1 if limit > 0 else 1
    return pagina_actual, total_paginas


# ----------------------------------------------------------------------
# Monedas (cat_moneda)
# ----------------------------------------------------------------------
@router.get(
    "/monedas",
    response_model=PaginatedCatMonedaResponse,
    summary="Listar monedas (cat_moneda) (Superadmin)",
)
@require_super_admin()
async def list_monedas(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None, max_length=100, description="Texto para buscar en código, nombre o símbolo"),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        filtros = {"client_id": target, "solo_activos": solo_activos, "buscar": buscar}
        rows = await CatalogosGlobalesService.list_monedas(skip=skip, limit=limit, **filtros)
        total = await CatalogosGlobalesService.contar_monedas(**filtros)
        pagina_actual, total_paginas = _paginated_metadata(total, skip, limit)
        return PaginatedCatMonedaResponse(
            monedas=[CatMonedaRead(**row) for row in rows],
            total_monedas=total,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            items_por_pagina=limit,
        )
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
    response_model=PaginatedCatPaisResponse,
    summary="Listar países (cat_pais) (Superadmin)",
)
@require_super_admin()
async def list_paises(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None, max_length=100, description="Texto para buscar en códigos ISO o nombre"),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        filtros = {"client_id": target, "solo_activos": solo_activos, "buscar": buscar}
        rows = await CatalogosGlobalesService.list_paises(skip=skip, limit=limit, **filtros)
        total = await CatalogosGlobalesService.contar_paises(**filtros)
        pagina_actual, total_paginas = _paginated_metadata(total, skip, limit)
        return PaginatedCatPaisResponse(
            paises=[CatPaisRead(**row) for row in rows],
            total_paises=total,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            items_por_pagina=limit,
        )
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
    response_model=PaginatedCatDepartamentoResponse,
    summary="Listar departamentos (cat_departamento) (Superadmin)",
)
@require_super_admin()
async def list_departamentos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True),
    pais_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None, max_length=100, description="Texto para buscar en código o nombre"),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        filtros = {
            "client_id": target,
            "solo_activos": solo_activos,
            "buscar": buscar,
            "pais_id": pais_id,
        }
        rows = await CatalogosGlobalesService.list_departamentos(skip=skip, limit=limit, **filtros)
        total = await CatalogosGlobalesService.contar_departamentos(**filtros)
        pagina_actual, total_paginas = _paginated_metadata(total, skip, limit)
        return PaginatedCatDepartamentoResponse(
            departamentos=[CatDepartamentoRead(**row) for row in rows],
            total_departamentos=total,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            items_por_pagina=limit,
        )
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
    response_model=PaginatedCatProvinciaResponse,
    summary="Listar provincias (cat_provincia) (Superadmin)",
)
@require_super_admin()
async def list_provincias(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True),
    departamento_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None, max_length=100, description="Texto para buscar en código o nombre"),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        filtros = {
            "client_id": target,
            "solo_activos": solo_activos,
            "buscar": buscar,
            "departamento_id": departamento_id,
        }
        rows = await CatalogosGlobalesService.list_provincias(skip=skip, limit=limit, **filtros)
        total = await CatalogosGlobalesService.contar_provincias(**filtros)
        pagina_actual, total_paginas = _paginated_metadata(total, skip, limit)
        return PaginatedCatProvinciaResponse(
            provincias=[CatProvinciaRead(**row) for row in rows],
            total_provincias=total,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            items_por_pagina=limit,
        )
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
    response_model=PaginatedCatDistritoResponse,
    summary="Listar distritos (cat_distrito) (Superadmin)",
)
@require_super_admin()
async def list_distritos(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros a retornar"),
    solo_activos: bool = Query(True),
    pais_id: Optional[UUID] = Query(None, description="Filtrar por país (cascada geográfica)"),
    departamento_id: Optional[UUID] = Query(None, description="Filtrar por departamento (cascada geográfica)"),
    provincia_id: Optional[UUID] = Query(None),
    ubigeo: Optional[str] = Query(None, min_length=1, max_length=6),
    buscar: Optional[str] = Query(None, max_length=100, description="Texto para buscar en código, nombre o ubigeo"),
    cliente_id: Optional[UUID] = Query(None, description="Opcional: ejecutar contra otro tenant"),
    current_user=Depends(get_current_active_user),
):
    try:
        target = _resolve_target_client_id(current_user, cliente_id)
        filtros = {
            "client_id": target,
            "solo_activos": solo_activos,
            "buscar": buscar,
            "pais_id": pais_id,
            "departamento_id": departamento_id,
            "provincia_id": provincia_id,
            "ubigeo": ubigeo,
        }
        rows = await CatalogosGlobalesService.list_distritos(skip=skip, limit=limit, **filtros)
        total = await CatalogosGlobalesService.contar_distritos(**filtros)
        pagina_actual, total_paginas = _paginated_metadata(total, skip, limit)
        return PaginatedCatDistritoResponse(
            distritos=[CatDistritoRead(**row) for row in rows],
            total_distritos=total,
            pagina_actual=pagina_actual,
            total_paginas=total_paginas,
            items_por_pagina=limit,
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

