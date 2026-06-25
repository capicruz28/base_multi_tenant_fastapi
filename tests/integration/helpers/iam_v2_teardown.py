"""
Teardown IAM V2 — Cluster 8 §11.

DELETE directo en orden FK. Prohibido usar RefreshTokenCleanupJob o purge_*_core.
"""
from __future__ import annotations

from typing import Dict, List, Sequence
from uuid import UUID

from sqlalchemy import and_, delete

from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)


def _rows_affected(result) -> int:
    if result and len(result) > 0:
        return int(result[0].get("rows_affected", 0))
    return 0


async def teardown_iam_v2_sessions(
    *,
    cliente_id: UUID,
    usuario_ids: Sequence[UUID],
) -> Dict[str, int]:
    """
    Elimina filas IAM V3 de prueba para los usuarios indicados en el tenant.

    Orden: refresh_tokens → token_family → user_session (respeta FK NO ACTION).
    """
    from app.infrastructure.database.queries_async import execute_query

    if not usuario_ids:
        return {"refresh_tokens": 0, "token_family": 0, "user_session": 0}

    usuario_ids_list = list(usuario_ids)
    tenant_users = and_(
        RefreshTokensTable.c.cliente_id == cliente_id,
        RefreshTokensTable.c.usuario_id.in_(usuario_ids_list),
    )

    tokens_stmt = delete(RefreshTokensTable).where(tenant_users)
    tokens_result = await execute_query(tokens_stmt, client_id=cliente_id)

    family_stmt = delete(TokenFamilyTable).where(
        and_(
            TokenFamilyTable.c.cliente_id == cliente_id,
            TokenFamilyTable.c.usuario_id.in_(usuario_ids_list),
        )
    )
    family_result = await execute_query(family_stmt, client_id=cliente_id)

    session_stmt = delete(UserSessionTable).where(
        and_(
            UserSessionTable.c.cliente_id == cliente_id,
            UserSessionTable.c.usuario_id.in_(usuario_ids_list),
        )
    )
    session_result = await execute_query(session_stmt, client_id=cliente_id)

    return {
        "refresh_tokens": _rows_affected(tokens_result),
        "token_family": _rows_affected(family_result),
        "user_session": _rows_affected(session_result),
    }


def register_iam_v2_test_user(request, usuario_id: UUID) -> None:
    """Registra usuario_id para teardown autouse en módulos IAM V2."""
    registry: List[UUID] = getattr(request.node, "iam_v2_test_users", [])
    if usuario_id not in registry:
        registry.append(usuario_id)
    request.node.iam_v2_test_users = registry


__all__ = ["register_iam_v2_test_user", "teardown_iam_v2_sessions"]
