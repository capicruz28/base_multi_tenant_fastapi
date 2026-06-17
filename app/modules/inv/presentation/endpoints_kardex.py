"""Endpoints INV - Kardex (consulta)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import KardexLineaRead
from app.modules.inv.application.services import kardex_service
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "movimiento"


@router.get("", response_model=list[KardexLineaRead], summary="Kardex (líneas por producto/almacén)")
async def obtener_kardex(
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén (origen o destino)"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Kardex de la empresa activa en sesión (sin mezclar otras empresas del tenant)."""
    try:
        rows = await kardex_service.list_kardex_servicio(
            client_id=client_id,
            producto_id=producto_id,
            almacen_id=almacen_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        return rows
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
