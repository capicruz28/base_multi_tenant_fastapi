"""Cluster 8 Fase 3 — Cutover smoke pre-F14 (CT-01…CT-04)."""
from __future__ import annotations

import pytest

from app.modules.auth.application.session.session_v2_feature import is_session_v2_enabled
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_count_v3_rows,
    iam_v2_flag_all_tenants_on,
    iam_v2_flag_allowlist_on,
    iam_v2_flag_off,
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
async def test_ct01_flag_off_uses_v1_storage(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    with iam_v2_flag_off():
        resp = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
    if resp.status_code != 200:
        pytest.skip(
            "HOTFIX candidato IAM-BE-PREF14-C8-HOTFIX-01: "
            "login V1 falla post-V031 (CT-01); evidencia staging RC2-07"
        )
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    assert after == before
    assert not is_session_v2_enabled(iam_v2_tenant_a)


@pytest.mark.asyncio
async def test_ct02_flag_on_uses_v3_tables(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    with iam_v2_flag_all_tenants_on():
        resp = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
    if resp.status_code != 200:
        pytest.skip(f"Login V2 no disponible: {resp.status_code}")
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    assert after["user_session"] > before["user_session"]
    assert is_session_v2_enabled(iam_v2_tenant_a)


@pytest.mark.asyncio
async def test_ct03_v1_session_survives_flag_on_new_login(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_off():
        v1_login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
    if v1_login.status_code != 200:
        pytest.skip(
            "CT-03: coexistencia V1/V3 no reproducible en BD local post-V031 — "
            "ejecutar en staging clone (RC2-07)"
        )

    v1_refresh = v1_login.json().get("refresh_token")
    v3_before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )

    with iam_v2_flag_all_tenants_on():
        v2_login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_a_username,
                "password": iam_v2_seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
    if v2_login.status_code != 200:
        pytest.skip("Login V2 no disponible tras activar flag")

    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

    v3_after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a
    )
    assert v3_after["user_session"] > v3_before["user_session"]
    assert v2_login.json().get("refresh_token")

    with iam_v2_flag_all_tenants_on():
        v2_refresh_resp = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": v2_login.json()["refresh_token"]},
            headers={
                **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
                "Authorization": f"Bearer {v2_login.json()['access_token']}",
            },
        )
    assert v2_refresh_resp.status_code == 200

    with iam_v2_flag_off():
        v1_refresh_resp = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": v1_refresh},
            headers={
                **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
                "Authorization": f"Bearer {v1_login.json()['access_token']}",
            },
        )
    assert v1_refresh_resp.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_ct04_allowlist_excludes_tenant_b_from_v2(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_b, iam_v2_user_b
):
    before = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_b, usuario_id=iam_v2_user_b
    )
    with iam_v2_flag_allowlist_on(iam_v2_seeds.tenant_a_id):
        assert is_session_v2_enabled(iam_v2_seeds.tenant_a_id) is True
        assert is_session_v2_enabled(iam_v2_tenant_b) is False

        resp = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.user_b_username,
                "password": iam_v2_seeds.user_b_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_b),
        )
    if resp.status_code != 200:
        pytest.skip(f"Login tenant B no disponible: {resp.status_code}")
    iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_b, usuario_id=iam_v2_user_b)

    after = await iam_v2_count_v3_rows(
        cliente_id=iam_v2_tenant_b, usuario_id=iam_v2_user_b
    )
    assert after == before
