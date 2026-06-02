from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user
from app.modules.catalogos.application.services.catalogos_service import CatalogosService
from app.modules.catalogos.presentation.schemas import (
    MonedaRead,
    PaisRead,
    DepartamentoRead,
    ProvinciaRead,
    DistritoRead,
)


router = APIRouter()


@router.get("/monedas", response_model=list[MonedaRead], summary="Listar monedas (cat_moneda)")
async def list_monedas(
    solo_activos: bool = Query(True),
    current_user=Depends(get_current_active_user),
):
    return await CatalogosService.list_monedas(client_id=current_user.cliente_id, solo_activos=solo_activos)


@router.get("/paises", response_model=list[PaisRead], summary="Listar países (cat_pais)")
async def list_paises(
    solo_activos: bool = Query(True),
    current_user=Depends(get_current_active_user),
):
    return await CatalogosService.list_paises(client_id=current_user.cliente_id, solo_activos=solo_activos)


@router.get("/departamentos", response_model=list[DepartamentoRead], summary="Listar departamentos (cat_departamento)")
async def list_departamentos(
    solo_activos: bool = Query(True),
    pais_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    return await CatalogosService.list_departamentos(
        client_id=current_user.cliente_id,
        pais_id=pais_id,
        solo_activos=solo_activos,
    )


@router.get("/provincias", response_model=list[ProvinciaRead], summary="Listar provincias (cat_provincia)")
async def list_provincias(
    solo_activos: bool = Query(True),
    departamento_id: Optional[UUID] = Query(None),
    current_user=Depends(get_current_active_user),
):
    return await CatalogosService.list_provincias(
        client_id=current_user.cliente_id,
        departamento_id=departamento_id,
        solo_activos=solo_activos,
    )


@router.get("/distritos", response_model=list[DistritoRead], summary="Listar distritos (cat_distrito)")
async def list_distritos(
    solo_activos: bool = Query(True),
    provincia_id: Optional[UUID] = Query(None),
    ubigeo: Optional[str] = Query(None, min_length=1, max_length=6),
    current_user=Depends(get_current_active_user),
):
    return await CatalogosService.list_distritos(
        client_id=current_user.cliente_id,
        provincia_id=provincia_id,
        ubigeo=ubigeo,
        solo_activos=solo_activos,
    )

