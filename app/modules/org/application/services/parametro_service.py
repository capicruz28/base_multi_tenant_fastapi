# app/modules/org/application/services/parametro_service.py
"""Servicio de Parámetro Sistema (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.infrastructure.database.queries.org import (
    list_parametros,
    get_parametro_by_id,
    get_parametro_by_clave_natural,
    create_parametro,
    update_parametro,
)
from app.modules.org.presentation.schemas import (
    ParametroCreate,
    ParametroUpdate,
    ParametroRead,
)


def _row_to_read(row: dict) -> ParametroRead:
    return ParametroRead(**row)

def _require_empresa_id(empresa_id: Optional[UUID]) -> UUID:
    if empresa_id is None:
        raise ValidationError(
            detail="empresa_id es obligatorio para operar parámetros por ID.",
            internal_code="MISSING_REQUIRED_FIELDS",
        )
    return empresa_id


async def list_parametros_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    modulo_codigo: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[ParametroRead]:
    rows = await list_parametros(
        client_id=client_id,
        empresa_id=empresa_id,
        modulo_codigo=modulo_codigo,
        solo_activos=solo_activos,
    )
    parametros = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        parametros = [
            p
            for p in parametros
            if term in (p.modulo_codigo or "").lower()
            or term in (p.codigo_parametro or "").lower()
            or term in (p.nombre_parametro or "").lower()
        ]
    return parametros


async def get_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> ParametroRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    return _row_to_read(row)


async def create_parametro_servicio(
    client_id: UUID,
    data: ParametroCreate,
) -> ParametroRead:
    if await get_parametro_by_clave_natural(
        client_id,
        modulo_codigo=data.modulo_codigo,
        codigo_parametro=data.codigo_parametro,
        empresa_id=data.empresa_id,
    ):
        if data.empresa_id is not None:
            detail = (
                f"Ya existe un parámetro con el código '{data.codigo_parametro}' "
                f"en el módulo '{data.modulo_codigo}' para esta empresa."
            )
        else:
            detail = (
                f"Ya existe un parámetro con el código '{data.codigo_parametro}' "
                f"en el módulo '{data.modulo_codigo}' a nivel de todo el cliente."
            )
        raise ConflictError(detail=detail)
    payload = data.model_dump()
    row = await create_parametro(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    data: ParametroUpdate,
    empresa_id: Optional[UUID] = None,
) -> ParametroRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def delete_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> None:
    """
    Baja lógica de un parámetro (es_activo = False).
    """
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> ParametroRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    updated = await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
