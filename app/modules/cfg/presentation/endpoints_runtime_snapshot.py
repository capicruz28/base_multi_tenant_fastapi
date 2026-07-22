"""Endpoint HTTP Runtime Snapshot — proyección read-only.

Spec HTTP: GET /api/v1/cfg/runtime/snapshot
Sin ETag / filtros / permisos cfg.secuencias.*.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.exceptions import CustomException
from app.modules.cfg.application.services.codigo_runtime_snapshot_service import (
    CodigoRuntimeSnapshotService,
)
from app.modules.cfg.presentation.cfg_deps import get_cfg_session_client_id
from app.modules.cfg.presentation.schemas_runtime import CodigoRuntimeSnapshotResponse

router = APIRouter()


@router.get(
    "/snapshot",
    response_model=CodigoRuntimeSnapshotResponse,
    summary="Runtime Snapshot de secuencias de código",
    operation_id="get_cfg_codigo_runtime_snapshot",
)
async def get_runtime_snapshot(
    client_id: UUID = Depends(get_cfg_session_client_id),
) -> CodigoRuntimeSnapshotResponse:
    """Proyección puntual del tenant: cfg ∩ módulos activos ∩ SequenceCatalog."""
    try:
        snapshot = await CodigoRuntimeSnapshotService().build_snapshot(client_id)
        return CodigoRuntimeSnapshotResponse.model_validate(snapshot)
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
