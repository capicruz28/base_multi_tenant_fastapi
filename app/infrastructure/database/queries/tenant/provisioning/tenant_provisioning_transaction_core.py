"""
Transacciones atómicas provisioning CP con row lock (PR-F4-02).

UPDLOCK en run activo — mitiga race conditions documentadas IP-2.0.1 F4-WP02.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import text

from app.core.application.unit_of_work import UnitOfWork

SQL_LOCK_PROVISIONING_RUN = """
SELECT
    provisioning_run_id,
    cliente_id,
    provisioning_state,
    is_current,
    attempt_number,
    idempotency_key,
    current_step_code,
    started_at,
    updated_at,
    ready_at,
    failed_at,
    last_error_code,
    last_error_message,
    created_by_usuario_id
FROM tenant_provisioning_run WITH (UPDLOCK, ROWLOCK)
WHERE provisioning_run_id = :provisioning_run_id
  AND cliente_id = :cliente_id
"""


async def lock_provisioning_run_tx(
    uow: UnitOfWork,
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
) -> Optional[Dict[str, Any]]:
    rows = await uow.execute(
        text(SQL_LOCK_PROVISIONING_RUN),
        {
            "provisioning_run_id": str(provisioning_run_id),
            "cliente_id": str(cliente_id),
        },
    )
    if not rows:
        return None
    return rows[0]


__all__ = ["SQL_LOCK_PROVISIONING_RUN", "lock_provisioning_run_tx"]
