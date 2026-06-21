"""
Rotación atómica de refresh tokens (IAM-BE-SESSIONS-P1-04).

Ejecuta lock + idle + activity + insert + revoke en una única UnitOfWork.
Patrón alineado con INV estorno (UPDLOCK, ROWLOCK + commit único).

⚠️ Dark code: no invocado por endpoints legacy hasta fase de conexión.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.application.unit_of_work import UnitOfWork
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.application.session.rotate_result import RotateOutcome

import logging

logger = logging.getLogger(__name__)

# --- SQL canónico (SQL Server) ---

SQL_LOCK_REFRESH_TOKEN_BY_HASH = """
SELECT
    token_id,
    usuario_id,
    token_hash,
    expires_at,
    is_revoked,
    revoked_reason,
    created_at,
    last_used_at,
    client_type,
    cliente_id,
    empresa_id,
    CASE
        WHEN :idle_timeout_minutes IS NULL OR :idle_timeout_minutes <= 0 THEN 0
        WHEN COALESCE(last_used_at, created_at) IS NULL THEN 0
        WHEN DATEDIFF(
            minute,
            COALESCE(last_used_at, created_at),
            GETDATE()
        ) > :idle_timeout_minutes THEN 1
        ELSE 0
    END AS idle_expired,
    CASE
        WHEN expires_at <= GETDATE() THEN 1
        ELSE 0
    END AS is_expired
FROM refresh_tokens WITH (UPDLOCK, ROWLOCK)
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id
"""

SQL_RECORD_ACTIVITY_IN_TX = """
UPDATE refresh_tokens
SET last_used_at = GETDATE(),
    uso_count = COALESCE(uso_count, 0) + 1
WHERE token_id = :token_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0
"""

SQL_INSERT_ROTATED_REFRESH_TOKEN = """
INSERT INTO refresh_tokens (
    usuario_id, token_hash, expires_at, client_type,
    ip_address, user_agent, cliente_id, empresa_id, device_name, device_id
)
OUTPUT
    INSERTED.token_id,
    INSERTED.usuario_id,
    INSERTED.cliente_id,
    INSERTED.empresa_id,
    INSERTED.expires_at,
    INSERTED.created_at
VALUES (
    :usuario_id, :new_token_hash, :expires_at, :client_type,
    :ip_address, :user_agent, :cliente_id, :empresa_id, :device_name, :device_id
)
"""

SQL_REVOKE_OLD_FOR_ROTATION = """
UPDATE refresh_tokens
SET is_revoked = 1,
    revoked_at = GETDATE(),
    revoked_reason = :revoked_reason
OUTPUT INSERTED.token_id, INSERTED.is_revoked
WHERE token_hash = :old_token_hash
  AND cliente_id = :cliente_id
  AND is_revoked = 0
"""

SQL_REVOKE_IDLE_IN_TX = """
UPDATE refresh_tokens
SET is_revoked = 1,
    revoked_at = GETDATE(),
    revoked_reason = :revoked_reason
OUTPUT INSERTED.token_id, INSERTED.is_revoked
WHERE token_id = :token_id
  AND cliente_id = :cliente_id
  AND is_revoked = 0
"""


def lock_refresh_token_params(
    *,
    token_hash: str,
    cliente_id: UUID,
    idle_timeout_minutes: Optional[int],
) -> Dict[str, Any]:
    return {
        "token_hash": token_hash,
        "cliente_id": cliente_id,
        "idle_timeout_minutes": idle_timeout_minutes if idle_timeout_minutes else 0,
    }


def _coerce_usuario_id_uuid(value: Any) -> Optional[UUID]:
    """Normaliza usuario_id a UUID para comparación (P1-04-HOTFIX-01)."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _refresh_token_user_mismatch(
    old_row: Dict[str, Any],
    usuario_id: Any,
) -> bool:
    """
    True si debe retornarse USER_MISMATCH.
    Compara únicamente uuid.UUID normalizados en ambos lados.
    """
    if not old_row.get("usuario_id"):
        return False
    row_uid = _coerce_usuario_id_uuid(old_row["usuario_id"])
    param_uid = _coerce_usuario_id_uuid(usuario_id)
    if row_uid is None or param_uid is None:
        return True
    return row_uid != param_uid


async def rotate_refresh_token_core(
    uow: UnitOfWork,
    *,
    old_token_hash: str,
    new_token_hash: str,
    cliente_id: UUID,
    usuario_id: UUID,
    expires_at: datetime,
    idle_timeout_minutes: Optional[int] = None,
    client_type: str = "web",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
    device_name: Optional[str] = None,
    device_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rotación atómica dentro de una UnitOfWork ya abierta.

    Secuencia:
    1. SELECT ... WITH (UPDLOCK, ROWLOCK)
    2. Validar estado / idle / expiración
    3. Activity tracking (last_used_at)
    4. INSERT nuevo token
    5. UPDATE old → SESSION_ROTATED

    Returns:
        Dict con ``outcome`` (RotateOutcome) y metadatos de filas.
    """
    lock_rows = await uow.execute(
        SQL_LOCK_REFRESH_TOKEN_BY_HASH,
        lock_refresh_token_params(
            token_hash=old_token_hash,
            cliente_id=cliente_id,
            idle_timeout_minutes=idle_timeout_minutes,
        ),
    )

    if not lock_rows:
        return {"outcome": RotateOutcome.NOT_FOUND}

    old_row = lock_rows[0]
    old_token_id = old_row.get("token_id")

    if _refresh_token_user_mismatch(old_row, usuario_id):
        return {
            "outcome": RotateOutcome.USER_MISMATCH,
            "old_token_id": old_token_id,
            "old_token_row": old_row,
        }

    if old_row.get("is_revoked"):
        reason = old_row.get("revoked_reason")
        if reason and str(reason) == RevokedReason.SESSION_ROTATED:
            outcome = RotateOutcome.ALREADY_ROTATED
        else:
            outcome = RotateOutcome.ALREADY_REVOKED
        return {
            "outcome": outcome,
            "old_token_id": old_token_id,
            "revoked_reason": str(reason) if reason else None,
            "old_token_row": old_row,
        }

    if bool(old_row.get("is_expired")):
        return {
            "outcome": RotateOutcome.EXPIRED,
            "old_token_id": old_token_id,
            "old_token_row": old_row,
        }

    if bool(old_row.get("idle_expired")):
        await uow.execute(
            SQL_REVOKE_IDLE_IN_TX,
            {
                "token_id": old_token_id,
                "cliente_id": cliente_id,
                "revoked_reason": str(RevokedReason.IDLE_TIMEOUT),
            },
        )
        logger.info(
            "[ROTATE-CORE] Idle timeout en txn token_id=%s cliente=%s",
            old_token_id,
            cliente_id,
        )
        return {
            "outcome": RotateOutcome.IDLE_TIMEOUT,
            "old_token_id": old_token_id,
            "revoked_reason": str(RevokedReason.IDLE_TIMEOUT),
            "old_token_row": old_row,
        }

    await uow.execute(
        SQL_RECORD_ACTIVITY_IN_TX,
        {"token_id": old_token_id, "cliente_id": cliente_id},
    )

    insert_rows = await uow.execute(
        SQL_INSERT_ROTATED_REFRESH_TOKEN,
        {
            "usuario_id": usuario_id,
            "new_token_hash": new_token_hash,
            "expires_at": expires_at,
            "client_type": client_type,
            "ip_address": ip_address,
            "user_agent": user_agent[:500] if user_agent else None,
            "cliente_id": cliente_id,
            "empresa_id": empresa_id,
            "device_name": device_name,
            "device_id": device_id,
        },
    )

    if not insert_rows:
        raise RuntimeError("INSERT rotation refresh token no retornó filas OUTPUT")

    new_row = insert_rows[0]
    new_token_id = new_row.get("token_id")

    revoke_rows = await uow.execute(
        SQL_REVOKE_OLD_FOR_ROTATION,
        {
            "old_token_hash": old_token_hash,
            "cliente_id": cliente_id,
            "revoked_reason": str(RevokedReason.SESSION_ROTATED),
        },
    )

    if not revoke_rows:
        raise RuntimeError(
            f"No se pudo revocar token antiguo en rotación token_id={old_token_id}"
        )

    logger.info(
        "[ROTATE-CORE] Rotación atómica OK old=%s new=%s cliente=%s",
        old_token_id,
        new_token_id,
        cliente_id,
    )

    return {
        "outcome": RotateOutcome.ROTATED,
        "old_token_id": old_token_id,
        "new_token_id": new_token_id,
        "revoked_reason": str(RevokedReason.SESSION_ROTATED),
        "old_token_row": old_row,
        "new_token_row": new_row,
    }


__all__ = [
    "SQL_LOCK_REFRESH_TOKEN_BY_HASH",
    "SQL_RECORD_ACTIVITY_IN_TX",
    "SQL_INSERT_ROTATED_REFRESH_TOKEN",
    "SQL_REVOKE_OLD_FOR_ROTATION",
    "SQL_REVOKE_IDLE_IN_TX",
    "lock_refresh_token_params",
    "_coerce_usuario_id_uuid",
    "_refresh_token_user_mismatch",
    "rotate_refresh_token_core",
]
