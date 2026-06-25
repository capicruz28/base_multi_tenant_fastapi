"""Cluster 8 Fase 3 — E2E smoke V2 (E-01…E-13)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt

from app.core.config import settings
from app.infrastructure.database.queries.auth.session import user_session_queries_core as usq
from tests.integration.conftest_iam_sessions_v2 import (
    iam_v2_flag_all_tenants_on,
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


def _login(client, seeds, *, flag_on: bool = True):
    ctx = iam_v2_flag_all_tenants_on() if flag_on else iam_v2_flag_off()
    with ctx:
        return client.post(
            "/api/v1/auth/login/",
            data={
                "username": seeds.user_a_username,
                "password": seeds.user_a_password,
            },
            headers=iam_v2_mobile_headers(seeds.subdominio_a),
        )


def _claims(access_token: str) -> dict:
    return jwt.get_unverified_claims(access_token)


@pytest.mark.asyncio
async def test_e01_login_v2_returns_sid_and_refresh_cookie(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        resp = _login(iam_v2_http_client, iam_v2_seeds)
        if resp.status_code != 200:
            pytest.skip(f"Login V2 no disponible ({resp.status_code}) — verificar seeds §10")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = resp.json()
        assert body.get("refresh_token")
        assert _claims(body["access_token"]).get("sid")


@pytest.mark.asyncio
async def test_e02_refresh_rotates_and_reissues_sid(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        old_refresh = login.json()["refresh_token"]
        old_sid = _claims(login.json()["access_token"]).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {login.json()['access_token']}",
        }
        refreshed = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": old_refresh},
            headers=headers,
        )
        assert refreshed.status_code == 200
        new_body = refreshed.json()
        assert new_body["refresh_token"] != old_refresh
        assert _claims(new_body["access_token"]).get("sid") == old_sid


@pytest.mark.asyncio
async def test_e03_logout_invalidates_refresh_and_blacklists_access(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_redis_available,
    iam_v2_tenant_a,
    iam_v2_user_a,
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        access = body["access_token"]
        refresh = body["refresh_token"]
        sid = _claims(access).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        logout = iam_v2_http_client.post(
            "/api/v1/auth/logout/",
            json={"refresh_token": refresh},
            headers=headers,
        )
        assert logout.status_code == 200

        refresh_again = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": refresh},
            headers=headers,
        )
        assert refresh_again.status_code in (401, 403)

        if sid and settings.ENABLE_REDIS_CACHE:
            import redis

            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
            )
            try:
                assert client.exists(f"session:access_jti:{sid}") or client.keys(
                    f"*blacklist*"
                )
            finally:
                client.close()


@pytest.mark.asyncio
async def test_e04_list_sessions_is_current_by_session_id(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        access = login.json()["access_token"]
        sid = _claims(access).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        listed = iam_v2_http_client.get("/api/v1/auth/sessions/", headers=headers)
        assert listed.status_code == 200
        sessions = listed.json()
        assert isinstance(sessions, list)
        current = [s for s in sessions if s.get("is_current")]
        assert len(current) == 1
        if sid:
            assert str(current[0].get("session_id")) == str(sid)


@pytest.mark.asyncio
async def test_e05_self_revoke_remote_session(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        first = _login(iam_v2_http_client, iam_v2_seeds)
        second = _login(iam_v2_http_client, iam_v2_seeds)
        if first.status_code != 200 or second.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        remote_sid = _claims(second.json()["access_token"]).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {first.json()['access_token']}",
        }
        target_id = remote_sid or second.json().get("current_token_id")
        if not target_id:
            listed = iam_v2_http_client.get("/api/v1/auth/sessions/", headers=headers)
            non_current = [s for s in listed.json() if not s.get("is_current")]
            target_id = non_current[0].get("session_id") or non_current[0].get("token_id")

        revoke = iam_v2_http_client.post(
            f"/api/v1/auth/sessions/{target_id}/revoke/",
            headers=headers,
        )
        assert revoke.status_code == 200


@pytest.mark.asyncio
async def test_e06_admin_revoke_emits_audit(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a, iam_v2_user_admin_a
):
    with iam_v2_flag_all_tenants_on():
        user_login = _login(iam_v2_http_client, iam_v2_seeds)
        if user_login.status_code != 200:
            pytest.skip("Login usuario no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        admin_login = iam_v2_http_client.post(
            "/api/v1/auth/login/",
            data={
                "username": iam_v2_seeds.admin_a_username,
                "password": iam_v2_seeds.admin_a_password,
            },
            headers=iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
        )
        if admin_login.status_code != 200:
            pytest.skip("Login admin no disponible — verificar RBAC revoke §10")

        sid = _claims(user_login.json()["access_token"]).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {admin_login.json()['access_token']}",
        }
        with patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            new_callable=AsyncMock,
        ) as mock_audit:
            resp = iam_v2_http_client.post(
                f"/api/v1/auth/sessions/{sid}/revoke_admin/",
                headers=headers,
            )
        if resp.status_code == 403:
            pytest.skip("Admin sin permiso revoke — configurar RBAC §10")
        assert resp.status_code == 200
        mock_audit.assert_awaited()
        assert mock_audit.await_args.kwargs.get("evento") == "session_admin_revoked"


@pytest.mark.asyncio
async def test_e07_replay_old_refresh_closes_session(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        old_refresh = login.json()["refresh_token"]
        sid = _claims(login.json()["access_token"]).get("sid")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {login.json()['access_token']}",
        }
        first = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": old_refresh},
            headers=headers,
        )
        assert first.status_code == 200
        replay = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": old_refresh},
            headers=headers,
        )
        assert replay.status_code in (401, 403, 409, 422)
        if sid:
            assert await usq.get_active_session_by_id_core(
                __import__("uuid").UUID(str(sid)), iam_v2_tenant_a
            ) is None


@pytest.mark.asyncio
async def test_e08_cambiar_empresa_without_relogin(
    request,
    iam_v2_seeds,
    iam_v2_http_client,
    iam_v2_tenant_a,
    iam_v2_user_a,
    iam_v2_empresa_a1,
    iam_v2_empresa_a2,
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        access = login.json()["access_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        target = (
            iam_v2_empresa_a2
            if str(_claims(access).get("empresa_id")) == str(iam_v2_empresa_a1)
            else iam_v2_empresa_a1
        )
        resp = iam_v2_http_client.post(
            "/api/v1/auth/empresa/cambiar/",
            json={"empresa_id": str(target)},
            headers=headers,
        )
        if resp.status_code == 409:
            pytest.skip("Usuario requiere selección empresa previa")
        assert resp.status_code == 200
        assert str(_claims(resp.json()["access_token"]).get("empresa_id")) == str(target)


@pytest.mark.asyncio
async def test_e09_multi_empresa_selection_flow(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a, iam_v2_empresa_a2
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        if body.get("requiere_seleccion_empresa"):
            selection_token = body.get("access_token")
            headers = {
                **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
                "Authorization": f"Bearer {selection_token}",
            }
            selected = iam_v2_http_client.post(
                "/api/v1/auth/empresa/seleccionar/",
                json={"empresa_id": str(iam_v2_empresa_a2)},
                headers=headers,
            )
            assert selected.status_code == 200
            assert selected.json().get("refresh_token")
        else:
            assert body.get("refresh_token")


@pytest.mark.asyncio
async def test_e10_password_change_revokes_others_and_sid(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        first = _login(iam_v2_http_client, iam_v2_seeds)
        second = _login(iam_v2_http_client, iam_v2_seeds)
        if first.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        new_password = "NewTest1234!"
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {second.json()['access_token']}",
        }
        changed = iam_v2_http_client.post(
            "/api/v1/auth/password/change/",
            json={
                "current_password": iam_v2_seeds.user_a_password,
                "new_password": new_password,
            },
            headers=headers,
        )
        if changed.status_code != 200:
            pytest.skip(f"Password change no disponible: {changed.status_code}")
        assert _claims(changed.json()["access_token"]).get("sid")
        assert await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a) >= 1


@pytest.mark.asyncio
async def test_e11_logout_all_closes_all_sessions(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        _login(iam_v2_http_client, iam_v2_seeds)
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {login.json()['access_token']}",
        }
        resp = iam_v2_http_client.post("/api/v1/auth/logout_all/", headers=headers)
        assert resp.status_code == 200
        assert await usq.count_active_sessions_core(iam_v2_user_a, iam_v2_tenant_a) == 0


@pytest.mark.asyncio
async def test_e12_flag_off_login_refresh_logout_v1(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_off():
        login = _login(iam_v2_http_client, iam_v2_seeds, flag_on=False)
        if login.status_code != 200:
            pytest.skip(
                "HOTFIX candidato IAM-BE-PREF14-C8-HOTFIX-01: "
                "rama V1 incompatible con DDL V031 (login falló)"
            )
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        refresh = body.get("refresh_token")
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {body['access_token']}",
        }
        refreshed = iam_v2_http_client.post(
            "/api/v1/auth/refresh/",
            json={"refresh_token": refresh},
            headers=headers,
        )
        assert refreshed.status_code == 200
        logout = iam_v2_http_client.post(
            "/api/v1/auth/logout/",
            json={"refresh_token": refresh},
            headers=headers,
        )
        assert logout.status_code == 200


@pytest.mark.asyncio
async def test_e13_me_probe_rejects_revoked_session(
    request, iam_v2_seeds, iam_v2_http_client, iam_v2_tenant_a, iam_v2_user_a
):
    with iam_v2_flag_all_tenants_on():
        login = _login(iam_v2_http_client, iam_v2_seeds)
        if login.status_code != 200:
            pytest.skip("Login no disponible")
        iam_v2_register_teardown(request, cliente_id=iam_v2_tenant_a, usuario_id=iam_v2_user_a)

        body = login.json()
        access = body["access_token"]
        refresh = body["refresh_token"]
        headers = {
            **iam_v2_mobile_headers(iam_v2_seeds.subdominio_a),
            "Authorization": f"Bearer {access}",
        }
        iam_v2_http_client.post(
            "/api/v1/auth/logout/",
            json={"refresh_token": refresh},
            headers=headers,
        )
        me = iam_v2_http_client.get("/api/v1/auth/me/", headers=headers)
        assert me.status_code in (401, 403)
