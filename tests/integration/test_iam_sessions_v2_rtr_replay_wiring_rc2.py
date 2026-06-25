"""IAM-BE-RTR-REPLAY-WIRING-RC2 — replay secuencial vía HTTP + concurrencia."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.database.queries.auth.session import (
    refresh_token_queries_core as rtq,
    token_family_queries_core as tfq,
    user_session_queries_core as usq,
)
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_flag_all_tenants_on,
    iam_v2_mobile_headers,
    iam_v2_register_teardown,
    skip_if_no_db,
)


def _claims(access_token: str) -> dict:
    from app.core.security.jwt import decode_access_token

    return decode_access_token(access_token)


def _login(client, seeds):
    return client.post(
        "/api/v1/auth/login/",
        data={
            "username": seeds.user_a_username,
            "password": seeds.user_a_password,
        },
        headers=iam_v2_mobile_headers(seeds.subdominio_a),
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rc2_http_sequential_replay_compromises_session(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_tenant_a,
    iam_v2_user_a,
):
    skip_if_no_db()

    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(
            request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
        )

        body = login.json()
        old_refresh = body["refresh_token"]
        sid = _claims(body["access_token"]).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {body['access_token']}",
        }

        with patch(
            "app.modules.auth.application.services.session_rotation_service.SessionAuditEmitter.emit_replay_detected",
            new_callable=AsyncMock,
        ) as mock_audit, patch(
            "app.modules.auth.application.services.session_rotation_service.SessionRedisBridge.blacklist_session",
            new_callable=AsyncMock,
        ) as mock_redis:
            first = iam_v2_http_client.post(
                "/api/v1/auth/refresh/",
                json={"refresh_token": old_refresh},
                headers=headers,
            )
            assert first.status_code == 200
            new_refresh = first.json().get("refresh_token")
            assert new_refresh

            replay = iam_v2_http_client.post(
                "/api/v1/auth/refresh/",
                json={"refresh_token": old_refresh},
                headers=headers,
            )
            assert replay.status_code == 401

        assert sid is not None
        session_uuid = __import__("uuid").UUID(str(sid))
        assert await usq.get_active_session_by_id_core(session_uuid, iam_v2_tenant_a) is None

        old_hash = RefreshTokenService.hash_token(old_refresh)
        old_row = await rtq.get_refresh_token_by_hash_any_state_core(
            old_hash, iam_v2_tenant_a
        )
        assert old_row is not None
        assert old_row.get("is_used") is True
        assert old_row.get("is_revoked") is True

        new_hash = RefreshTokenService.hash_token(new_refresh)
        new_row = await rtq.get_refresh_token_by_hash_any_state_core(
            new_hash, iam_v2_tenant_a
        )
        assert new_row is not None
        assert new_row.get("is_revoked") is True

        family = await tfq.get_family_by_id_core(
            __import__("uuid").UUID(str(old_row["family_id"])),
            iam_v2_tenant_a,
        )
        assert family is not None
        assert family.get("is_compromised") is True

        mock_redis.assert_awaited()
        mock_audit.assert_awaited_once()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rc2_concurrent_refresh_still_one_winner(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_tenant_a,
    iam_v2_user_a,
):
    skip_if_no_db()

    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(
            request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
        )

        body = login.json()
        refresh = body["refresh_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {body['access_token']}",
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rc2_http_valid_refresh_unchanged(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_tenant_a,
    iam_v2_user_a,
):
    skip_if_no_db()

    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip(f"Login no disponible: {login.status_code}")
        iam_v2_register_teardown(
            request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
        )

        body = login.json()
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {body['access_token']}",
        }
        resp = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": body["refresh_token"]},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json().get("access_token")
        assert resp.json().get("refresh_token")
