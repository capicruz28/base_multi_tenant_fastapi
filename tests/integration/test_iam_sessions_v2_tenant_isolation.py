"""Cluster 8 Fase 1 — P1-10 tenant isolation V3 (MT-01…MT-07)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from app.infrastructure.database.queries.auth.session import (
    refresh_token_queries_core as rtq,
    session_transaction_core as stx,
    token_family_queries_core as tfq,
    user_session_queries_core as usq,
)
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_create_session_via_c18,
    iam_v2_flag_all_tenants_on,
    iam_v2_mobile_headers,
    iam_v2_register_teardown,
)

pytestmark = [
    pytest.mark.iam_v2_integration,
    pytest.mark.requires_sqlserver,
]


@pytest.fixture(autouse=True)
async def _teardown(iam_v2_autouse_teardown):
    yield


@pytest.mark.asyncio
async def test_mt01_get_active_session_cross_tenant_returns_none(
    request,
    iam_v2_seeds,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    row_a = await usq.get_active_session_by_id_core(created["session_id"], iam_v2_tenant_a)
    row_b = await usq.get_active_session_by_id_core(created["session_id"], iam_v2_tenant_b)

    assert row_a is not None
    assert row_b is None


@pytest.mark.asyncio
async def test_mt02_get_token_by_hash_cross_tenant_returns_none(
    request,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    token_a = await rtq.get_refresh_token_by_hash_core(created["token_hash"], iam_v2_tenant_a)
    token_b = await rtq.get_refresh_token_by_hash_core(created["token_hash"], iam_v2_tenant_b)

    assert token_a is not None
    assert token_b is None


@pytest.mark.asyncio
async def test_mt03_get_family_by_session_cross_tenant_returns_none(
    request,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    fam_a = await tfq.get_family_by_session_id_core(created["session_id"], iam_v2_tenant_a)
    fam_b = await tfq.get_family_by_session_id_core(created["session_id"], iam_v2_tenant_b)

    assert fam_a is not None
    assert fam_b is None


@pytest.mark.asyncio
async def test_mt04_revoke_session_cross_tenant_affects_zero_rows(
    request,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
):
    from app.core.application.unit_of_work import UnitOfWork

    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    async with UnitOfWork(client_id=iam_v2_tenant_b) as uow:
        result = await stx.revoke_session_tx(
            uow,
            session_id=created["session_id"],
            family_id=created["family_id"],
            cliente_id=iam_v2_tenant_b,
            session_revoked_reason="logout",
            family_invalidation_reason="session_revoked",
            token_revoked_reason="logout",
        )

    assert result["session_rows"] == 0
    assert result["family_rows"] == 0
    assert result["token_rows"] == 0

    still_active = await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    )
    assert still_active is not None


@pytest.mark.asyncio
async def test_mt05_rotate_with_wrong_cliente_id_fails(
    request,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
):
    from app.core.application.unit_of_work import UnitOfWork
    from app.modules.auth.application.services.refresh_token_service import (
        RefreshTokenService,
    )

    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    new_hash = RefreshTokenService.hash_token("wrong-tenant-rotate-token")

    async with UnitOfWork(client_id=iam_v2_tenant_b) as uow:
        with pytest.raises(RuntimeError, match="Token no encontrado"):
            await stx.rotate_refresh_token_tx(
                uow,
                old_token_hash=created["token_hash"],
                new_token_hash=new_hash,
                cliente_id=iam_v2_tenant_b,
                token_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            )


@pytest.mark.asyncio
async def test_mt06_cleanup_tenant_a_does_not_delete_tenant_b(
    request,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
    iam_v2_user_b,
):
    from sqlalchemy import update

    from app.infrastructure.database.queries_async import execute_update
    from app.infrastructure.database.tables import RefreshTokensTable

    created_a = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    created_b = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_b,
        usuario_id=iam_v2_user_b,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_b, usuario_id=iam_v2_user_b)

    old_used_at = datetime.now(timezone.utc) - timedelta(days=120)
    for cliente_id, token_id in (
        (iam_v2_tenant_a, created_a["token_id"]),
        (iam_v2_tenant_b, created_b["token_id"]),
    ):
        stmt = (
            update(RefreshTokensTable)
            .where(
                RefreshTokensTable.c.token_id == token_id,
                RefreshTokensTable.c.cliente_id == cliente_id,
            )
            .values(is_used=True, used_at=old_used_at, is_revoked=True, revoked_at=old_used_at)
        )
        await execute_update(stmt, client_id=cliente_id)

    deleted_a = await rtq.purge_expired_tokens_core(iam_v2_tenant_a, retention_days=90)
    assert deleted_a >= 1

    token_b = await rtq.get_refresh_token_by_hash_core(
        created_b["token_hash"], iam_v2_tenant_b
    )
    assert token_b is not None


@pytest.mark.asyncio
async def test_mt07_endpoint_revoke_other_tenant_session_404(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_tenant_a,
    iam_v2_tenant_b,
    iam_v2_user_a,
    iam_v2_user_b,
):
    with iam_v2_flag_all_tenants_on():
        created_b = await iam_v2_create_session_via_c18(
            cliente_id=iam_v2_tenant_b,
            usuario_id=iam_v2_user_b,
        )
        iam_v2_register_teardown(
            request, cliente_id=iam_v2_tenant_b, usuario_id=iam_v2_user_b
        )

        login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
        if login.status_code != 200:
            pytest.skip(f"Login admin tenant A no disponible: {login.status_code}")

        access = login.json().get("access_token")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        resp = iam_v2_http_client.post(
            f"/api/v1/auth/sessions/{created_b['session_id']}/revoke_admin/",
            headers=headers,
        )
        assert resp.status_code == 404
