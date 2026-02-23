# app/modules/rbac/presentation/endpoints_permisos_catalogo.py
"""
Endpoint para listar el catálogo de permisos de negocio (tabla permiso).
Usado por el frontend para mostrar la lista de permisos al asignar a un rol.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.rbac.presentation.schemas import PermisoCatalogoRead
from app.modules.rbac.application.services.permisos_negocio_service import listar_catalogo_permisos
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.logging_config import get_logger
from app.core.exceptions import CustomException

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[PermisoCatalogoRead],
    summary="Listar catálogo de permisos de negocio",
    description="""
    Devuelve todos los permisos activos del catálogo (tabla `permiso` en BD central).
    **URL:** GET /api/v1/permisos-catalogo o GET /api/v1/permisos-catalogo/
    **Autorización:** `admin.rol.leer`.
    """,
    dependencies=[Depends(require_permission("admin.rol.leer"))],
)
@router.get(
    "/",
    response_model=List[PermisoCatalogoRead],
    include_in_schema=False,
    dependencies=[Depends(require_permission("admin.rol.leer"))],
)
async def get_permisos_catalogo(
    current_user=Depends(get_current_active_user),
):
    try:
        # Filtrar por módulos habilitados del tenant (cliente_modulo)
        items = await listar_catalogo_permisos(cliente_id=current_user.cliente_id)
        return [PermisoCatalogoRead(**r) for r in items]
    except CustomException as ce:
        logger.error(f"Error listando catálogo de permisos: {ce.detail}")
        raise HTTPException(status_code=ce.status_code, detail=ce.detail)
    except Exception as e:
        logger.exception("Error inesperado listando catálogo de permisos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el catálogo de permisos.",
        )
