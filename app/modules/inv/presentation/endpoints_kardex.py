"""Endpoints INV - Kardex (consulta)."""
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import KardexLineaRead
from app.infrastructure.database.queries.inv import list_kardex

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "movimiento"


@router.get("", response_model=list[KardexLineaRead], summary="Kardex (líneas por producto/almacén)")
async def obtener_kardex(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén (origen o destino)"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    client_id = current_user.cliente_id
    rows = await list_kardex(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [KardexLineaRead(**r) for r in rows]

