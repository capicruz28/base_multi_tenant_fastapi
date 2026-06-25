"""Cluster 8 Fase 2 — C7 cleanup integration (CL-01…CL-03)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import and_, update

from app.infrastructure.database.queries.auth.session import (
    refresh_token_queries_core as rtq,
    user_session_queries_core as usq,
)
from app.infrastructure.database.queries_async import execute_update
from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_create_session_via_c18,
    iam_v2_register_teardown,
)

pytestmark = [
    pytest.mark.iam_v2_integration,
    pytest.mark.requires_sqlserver,
]

_OLD = datetime.now(timezone.utc) - timedelta(days=120)


@pytest.fixture(autouse=True)
async def _teardown(iam_v2_autouse_teardown):
    yield


async def _close_session_old(
    *,
    session_id,
    cliente_id,
    usuario_id,
    family_id,
    token_id,
) -> None:
    await execute_update(
        update(UserSessionTable)
        .where(
            UserSessionTable.c.session_id == session_id,
            UserSessionTable.c.cliente_id == cliente_id,
        )
        .values(
            is_active=False,
            revoked_at=_OLD,
            revoked_reason="logout",
        ),
        client_id=cliente_id,
    )
    await execute_update(
        update(TokenFamilyTable)
        .where(
            TokenFamilyTable.c.family_id == family_id,
            TokenFamilyTable.c.cliente_id == cliente_id,
        )
        .values(is_compromised=True, compromised_at=_OLD, invalidation_reason="replay_detected"),
        client_id=cliente_id,
    )
    await execute_update(
        update(RefreshTokensTable)
        .where(
            RefreshTokensTable.c.token_id == token_id,
            RefreshTokensTable.c.cliente_id == cliente_id,
        )
        .values(is_revoked=True, revoked_at=_OLD, revoked_reason="logout"),
        client_id=cliente_id,
    )


@pytest.mark.asyncio
async def test_cl01_purge_expired_tokens_respects_90d_retention(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    await execute_update(
        update(RefreshTokensTable)
        .where(RefreshTokensTable.c.token_id == created["token_id"])
        .values(is_used=True, used_at=_OLD, is_revoked=True, revoked_at=_OLD),
        client_id=iam_v2_tenant_a,
    )

    deleted = await rtq.purge_expired_tokens_core(iam_v2_tenant_a, retention_days=90)
    assert deleted >= 1
    assert (
        await rtq.get_refresh_token_by_hash_core(
            created["token_hash"], iam_v2_tenant_a
        )
        is None
    )


@pytest.mark.asyncio
async def test_cl02_purge_closed_sessions_respects_90d_and_si_365d(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    await _close_session_old(
        session_id=created["session_id"],
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
        family_id=created["family_id"],
        token_id=created["token_id"],
    )
    await rtq.purge_expired_tokens_core(iam_v2_tenant_a, retention_days=90)

    deleted = await usq.purge_closed_sessions_core(
        iam_v2_tenant_a,
        retention_days=90,
        compromised_retention_days=365,
    )
    assert deleted >= 1


@pytest.mark.asyncio
async def test_cl03_purge_closed_sessions_skips_with_remaining_tokens(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    await execute_update(
        update(UserSessionTable)
        .where(UserSessionTable.c.session_id == created["session_id"])
        .values(is_active=False, revoked_at=_OLD, revoked_reason="logout"),
        client_id=iam_v2_tenant_a,
    )

    deleted = await usq.purge_closed_sessions_core(iam_v2_tenant_a, retention_days=90)
    assert deleted == 0

    row = await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    )
    assert row is None

    from app.infrastructure.database.queries_async import execute_query
    from sqlalchemy import select

    rows = await execute_query(
        select(UserSessionTable).where(
            and_(
                UserSessionTable.c.session_id == created["session_id"],
                UserSessionTable.c.cliente_id == iam_v2_tenant_a,
            )
        ),
        client_id=iam_v2_tenant_a,
    )
    assert len(rows) == 1
