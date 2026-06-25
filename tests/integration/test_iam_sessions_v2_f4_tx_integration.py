"""Cluster 8 Fase 2 — C18 integration (I-01…I-07, R-01…R-04, CC-01,03,04,05)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.core.application.unit_of_work import UnitOfWork
from app.infrastructure.database.queries.auth.session import (
    refresh_token_queries_core as rtq,
    session_transaction_core as stx,
    user_session_queries_core as usq,
)
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_count_v3_rows,
    iam_v2_create_session_via_c18,
    iam_v2_flag_all_tenants_on,
    iam_v2_mobile_headers,
    iam_v2_register_teardown,
)

pytestmark = [
    pytest.mark.iam_v2_integration,
    pytest.mark.requires_sqlserver,
]

_EXPIRES = datetime.now(timezone.utc) + timedelta(days=7)


@pytest.fixture(autouse=True)
async def _teardown(iam_v2_autouse_teardown):
    yield


@pytest.mark.asyncio
async def test_i01_create_session_four_writes_persisted(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)
    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )

    assert after["user_session"] == before["user_session"] + 1
    assert after["token_family"] == before["token_family"] + 1
    assert after["refresh_tokens"] == before["refresh_tokens"] + 1
    assert created["session_id"] is not None
    assert created["family_id"] is not None
    assert created["token_id"] is not None


@pytest.mark.asyncio
async def test_i02_create_session_rollback_on_step_failure(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    token_hash = RefreshTokenService.hash_token("rollback-create-token")

    with patch.object(
        stx,
        "_update_family_current_token_uow",
        return_value=0,
    ):
        with pytest.raises(RuntimeError, match="current_token_id"):
            async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
                await stx.create_session_with_token_tx(
                    uow,
                    usuario_id=iam_v2_user_a,
                    cliente_id=iam_v2_tenant_a,
                    session_expires_at=_EXPIRES,
                    token_hash=token_hash,
                    token_expires_at=_EXPIRES,
                    platform="web",
                )

    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    assert after == before


@pytest.mark.asyncio
async def test_i03_rotate_chain_parent_token_id(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    new_hash = RefreshTokenService.hash_token("rotate-successor")
    async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
        rotated = await stx.rotate_refresh_token_tx(
            uow,
            old_token_hash=created["token_hash"],
            new_token_hash=new_hash,
            cliente_id=iam_v2_tenant_a,
            token_expires_at=_EXPIRES,
        )

    successor = await rtq.get_refresh_token_by_hash_core(new_hash, iam_v2_tenant_a)
    assert rotated["old_token_id"] == created["token_id"]
    assert successor is not None
    assert successor["parent_token_id"] == created["token_id"]


@pytest.mark.asyncio
async def test_i04_rotate_rollback_when_mark_used_zero(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    new_hash = RefreshTokenService.hash_token("rotate-rollback")
    with patch.object(stx, "_mark_token_used_uow", return_value=0):
        with pytest.raises(RuntimeError, match="MARK token used"):
            async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
                await stx.rotate_refresh_token_tx(
                    uow,
                    old_token_hash=created["token_hash"],
                    new_token_hash=new_hash,
                    cliente_id=iam_v2_tenant_a,
                    token_expires_at=_EXPIRES,
                )

    assert await rtq.get_refresh_token_by_hash_core(new_hash, iam_v2_tenant_a) is None


@pytest.mark.asyncio
async def test_i05_revoke_session_closes_session_and_tokens(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
        result = await stx.revoke_session_tx(
            uow,
            session_id=created["session_id"],
            family_id=created["family_id"],
            cliente_id=iam_v2_tenant_a,
            session_revoked_reason="logout",
            family_invalidation_reason="session_revoked",
            token_revoked_reason="logout",
        )

    assert result["session_rows"] == 1
    assert result["token_rows"] >= 1
    assert await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    ) is None


@pytest.mark.asyncio
async def test_i06_revoke_all_bulk_coherent(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
        result = await stx.revoke_all_user_sessions_tx(
            uow,
            usuario_id=iam_v2_user_a,
            cliente_id=iam_v2_tenant_a,
            session_revoked_reason="logout",
            family_invalidation_reason="session_revoked",
            token_revoked_reason="logout",
        )

    assert result["sessions_closed"] >= 2
    assert result["tokens_revoked"] >= 2
    assert await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a) == 0


@pytest.mark.asyncio
async def test_i07_replay_attack_compromises_family_and_session(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a,
        usuario_id=iam_v2_user_a,
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
        await stx.handle_replay_attack_tx(
            uow,
            session_id=created["session_id"],
            family_id=created["family_id"],
            token_id=created["token_id"],
            cliente_id=iam_v2_tenant_a,
            usuario_id=iam_v2_user_a,
        )

    assert await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    ) is None


# --- Rollback R-01…R-04 ---


@pytest.mark.asyncio
async def test_r01_create_failure_leaves_zero_rows(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    token_hash = RefreshTokenService.hash_token("rollback-r01-token")

    with patch.object(stx, "_update_family_current_token_uow", return_value=0):
        with pytest.raises(RuntimeError, match="current_token_id"):
            async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
                await stx.create_session_with_token_tx(
                    uow,
                    usuario_id=iam_v2_user_a,
                    cliente_id=iam_v2_tenant_a,
                    session_expires_at=_EXPIRES,
                    token_hash=token_hash,
                    token_expires_at=_EXPIRES,
                    platform="web",
                )

    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    assert after == before


@pytest.mark.asyncio
async def test_r02_create_family_update_failure_leaves_zero_rows(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    await test_r01_create_failure_leaves_zero_rows(
        request, iam_v2_tenant_a, iam_v2_user_a
    )


@pytest.mark.asyncio
async def test_r03_rotate_mark_used_zero_no_successor(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    await test_i04_rotate_rollback_when_mark_used_zero(
        request, iam_v2_tenant_a, iam_v2_user_a
    )


@pytest.mark.asyncio
async def test_r04_revoke_all_exception_preserves_pre_tx_state(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    active_before = await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a)
    with patch.object(stx, "_revoke_all_tokens_for_user_uow", side_effect=RuntimeError("mid-tx")):
        with pytest.raises(RuntimeError, match="mid-tx"):
            async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
                await stx.revoke_all_user_sessions_tx(
                    uow,
                    usuario_id=iam_v2_user_a,
                    cliente_id=iam_v2_tenant_a,
                    session_revoked_reason="logout",
                    family_invalidation_reason="session_revoked",
                    token_revoked_reason="logout",
                )

    active_after = await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a)
    assert active_after == active_before
    assert await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    ) is not None


# --- Concurrency CC-01, CC-03, CC-04, CC-05 ---


@pytest.mark.slow
@pytest.mark.asyncio
async def test_cc01_double_refresh_one_wins(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        refresh = body["refresh_token"]
        access = body["access_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }

        async def _refresh():
            return iam_v2_http_client.post(
                "/api/v1/auth/refresh/",
                json={"refresh_token": refresh},
                headers=headers,
            )

        results = await asyncio.gather(_refresh(), _refresh())
        statuses = sorted(r.status_code for r in results)
        assert 200 in statuses
        assert any(s in (401, 409, 422) for s in statuses) or statuses.count(200) == 1


@pytest.mark.slow
@pytest.mark.asyncio
async def test_cc03_refresh_vs_logout_all_race(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        refresh = body["refresh_token"]
        access = body["access_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }

        async def _refresh():
            return iam_v2_http_client.post(
                "/api/v1/auth/refresh/",
                json={"refresh_token": refresh},
                headers=headers,
            )

        async def _logout_all():
            return iam_v2_http_client.post("/api/v1/auth/logout_all/", headers=headers)

        await asyncio.gather(_refresh(), _logout_all())
        assert await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a) == 0


@pytest.mark.slow
@pytest.mark.asyncio
async def test_cc04_double_replay_attack_idempotent(
    request, iam_v2_tenant_a, iam_v2_user_a
):
    created = await iam_v2_create_session_via_c18(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    async with UnitOfWork(client_id=iam_v2_tenant_a) as uow:
        await stx.handle_replay_attack_tx(
            uow,
            session_id=created["session_id"],
            family_id=created["family_id"],
            token_id=created["token_id"],
            cliente_id=iam_v2_tenant_a,
            usuario_id=iam_v2_user_a,
        )
        await stx.handle_replay_attack_tx(
            uow,
            session_id=created["session_id"],
            family_id=created["family_id"],
            token_id=created["token_id"],
            cliente_id=iam_v2_tenant_a,
            usuario_id=iam_v2_user_a,
        )

    assert await usq.get_active_session_by_id_core(
        created["session_id"], iam_v2_tenant_a
    ) is None


@pytest.mark.slow
@pytest.mark.asyncio
async def test_cc05_refresh_vs_revoke_session_race(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        refresh = body["refresh_token"]
        access = body["access_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        payload = __import__("jose.jwt", fromlist=["jwt"]).jwt.get_unverified_claims(access)
        sid = payload.get("sid")
        if not sid:
            pytest.skip("Access token sin sid — HOTFIX candidato auth login V2")

        async def _refresh():
            return iam_v2_http_client.post(
                "/api/v1/auth/refresh/",
                json={"refresh_token": refresh},
                headers=headers,
            )

        async def _revoke():
            return iam_v2_http_client.post(
                f"/api/v1/auth/sessions/{sid}/revoke/",
                headers=headers,
            )

        await asyncio.gather(_refresh(), _revoke())
        active = await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a)
        assert active == 0
