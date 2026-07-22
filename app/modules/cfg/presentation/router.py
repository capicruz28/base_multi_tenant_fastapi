"""Router padre del módulo CFG.

Spec: cfg-implementation-spec v1.0 — Etapa 7.
Runtime Snapshot: Etapa 2 (superficie /runtime separada de Admin /secuencias).
"""

from fastapi import APIRouter, Depends

from app.modules.cfg.presentation.cfg_deps import require_cfg_tenant_erp_session
from app.modules.cfg.presentation.endpoints_codigo_secuencia import (
    router as router_secuencias,
)
from app.modules.cfg.presentation.endpoints_runtime_snapshot import (
    router as router_runtime,
)

router = APIRouter()

router.include_router(
    router_secuencias,
    prefix="/secuencias",
    tags=["CFG - Secuencias de código"],
    dependencies=[Depends(require_cfg_tenant_erp_session)],
)

router.include_router(
    router_runtime,
    prefix="/runtime",
    tags=["CFG - Runtime Snapshot"],
    dependencies=[Depends(require_cfg_tenant_erp_session)],
)
