"""F10 — tests wiring auth_service V1/V2 detrás del feature flag."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
REFRESH_OLD = "old-refresh-plain"
REFRESH_NEW = "new-refresh-plain"
ACCESS_JTI = "access-jti-f10"

_AUTH = "app.modules.auth.application.services.auth_service"
_FEATURE = f"{_AUTH}.is_session_v2_enabled"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_persist_login_v1_when_flag_off():
    with (
        patch(_FEATURE, return_value=False),
        patch(f"{_AUTH}.RefreshTokenService.store_refresh_token", new_callable=AsyncMock) as mock_store,
        patch(f"{_AUTH}.RefreshTokenService.link_session_access_jti", new_callable=AsyncMock) as mock_link,
        patch(
            "app.modules.auth.application.services.session_creation_service.SessionCreationService.create",
            new_callable=AsyncMock,
        ),
    ):
        mock_store.return_value = {"token_id": uuid4()}
        used_v2 = await AuthService.persist_login_session(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            refresh_token=REFRESH_OLD,
            access_jti=ACCESS_JTI,
            access_expire_minutes=15,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            empresa_id=None,
            refresh_expire_days=7,
        )
    assert used_v2 is False
    mock_store.assert_awaited_once()
    mock_link.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_persist_login_v2_when_flag_on():
    with (
        patch(_FEATURE, return_value=True),
        patch(
            "app.modules.auth.application.services.session_creation_service.SessionCreationService.create",
            new_callable=AsyncMock,
        ) as mock_create,
        patch(f"{_AUTH}.RefreshTokenService.store_refresh_token", new_callable=AsyncMock) as mock_store,
    ):
        used_v2 = await AuthService.persist_login_session(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            refresh_token=REFRESH_OLD,
            access_jti=ACCESS_JTI,
            access_expire_minutes=15,
            client_type="mobile",
            ip_address="127.0.0.1",
            user_agent="pytest",
            empresa_id=uuid4(),
            refresh_expire_days=7,
        )
    assert used_v2 is True
    mock_create.assert_awaited_once()
    mock_store.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_rotate_refresh_v1_when_flag_off():
    v1_result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        new_token_id=uuid4(),
    )
    with (
        patch(_FEATURE, return_value=False),
        patch(f"{_AUTH}.rotate_refresh_token_service", new_callable=AsyncMock, return_value=v1_result),
        patch(f"{_AUTH}.RefreshTokenService.link_session_access_jti", new_callable=AsyncMock) as mock_link,
        patch(
            "app.modules.auth.application.services.session_rotation_service.SessionRotationService.rotate",
            new_callable=AsyncMock,
        ) as mock_v2,
    ):
        result = await AuthService.rotate_refresh_session(
            old_refresh_token=REFRESH_OLD,
            new_refresh_token=REFRESH_NEW,
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            client_type="web",
            ip_address="10.0.0.1",
            user_agent="agent",
            empresa_id=None,
            refresh_expire_days=7,
            new_access_jti=ACCESS_JTI,
            access_expire_minutes=15,
        )
    assert result.success is True
    mock_v2.assert_not_awaited()
    mock_link.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_rotate_refresh_v2_when_flag_on():
    empresa_id = uuid4()
    v2_result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        new_token_id=uuid4(),
    )
    with (
        patch(_FEATURE, return_value=True),
        patch(
            "app.modules.auth.application.services.session_rotation_service.SessionRotationService.rotate",
            new_callable=AsyncMock,
            return_value=v2_result,
        ) as mock_v2,
        patch(f"{_AUTH}.rotate_refresh_token_service", new_callable=AsyncMock) as mock_v1,
        patch(f"{_AUTH}.RefreshTokenService.link_session_access_jti", new_callable=AsyncMock) as mock_link,
    ):
        result = await AuthService.rotate_refresh_session(
            old_refresh_token=REFRESH_OLD,
            new_refresh_token=REFRESH_NEW,
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
            client_type="web",
            ip_address="10.0.0.1",
            user_agent="agent",
            empresa_id=empresa_id,
            refresh_expire_days=7,
            new_access_jti=ACCESS_JTI,
            access_expire_minutes=15,
        )
    assert result.outcome == RotateOutcome.ROTATED
    mock_v2.assert_awaited_once()
    assert mock_v2.await_args.kwargs["empresa_id"] == empresa_id
    mock_v1.assert_not_awaited()
    mock_link.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_logout_v2_uses_revocation_service():
    request = MagicMock()
    request.client = MagicMock(host="127.0.0.1")
    request.headers = {"user-agent": "pytest"}
    request.cookies = {"refresh_token": REFRESH_OLD}

    with (
        patch(f"{_AUTH}.decode_refresh_token", return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)}),
        patch(_FEATURE, return_value=True),
        patch.object(
            AuthService,
            "_fetch_user_row_for_refresh",
            new_callable=AsyncMock,
            return_value={"usuario_id": USUARIO_ID},
        ),
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_current_session",
            new_callable=AsyncMock,
        ) as mock_revoke,
        patch(f"{_AUTH}.RefreshTokenService.revoke_token", new_callable=AsyncMock) as mock_v1_revoke,
    ):
        from app.modules.auth.application.session.revoke_result import RevokeResult

        mock_revoke.return_value = RevokeResult(
            session_id=uuid4(),
            was_active=True,
        )
        outcome = await AuthService.perform_logout(request=request, client_type="web")

    assert outcome["refresh_revoked"] is True
    mock_revoke.assert_awaited_once()
    mock_v1_revoke.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_logout_v1_when_flag_off():
    request = MagicMock()
    request.client = MagicMock(host="127.0.0.1")
    request.headers = {"user-agent": "pytest"}
    request.cookies = {"refresh_token": REFRESH_OLD}

    with (
        patch(f"{_AUTH}.decode_refresh_token", return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)}),
        patch(_FEATURE, return_value=False),
        patch(f"{_AUTH}.RefreshTokenService.validate_refresh_token", new_callable=AsyncMock, return_value={"usuario_id": USUARIO_ID}),
        patch(f"{_AUTH}.RefreshTokenService.revoke_token", new_callable=AsyncMock, return_value=True) as mock_v1,
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_current_session",
            new_callable=AsyncMock,
        ) as mock_v2,
        patch(f"{_AUTH}.AuditService.registrar_auth_event", new_callable=AsyncMock),
    ):
        outcome = await AuthService.perform_logout(request=request, client_type="web")

    assert outcome["refresh_revoked"] is True
    mock_v1.assert_awaited_once()
    mock_v2.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_get_current_user_from_refresh_v2_path():
    request = MagicMock()
    request.headers = {"X-Client-Type": "web"}
    request.client = MagicMock(host="127.0.0.1")

    token_row = {
        "empresa_id": None,
        "usuario_id": USUARIO_ID,
    }
    context = MagicMock()
    context.token_row = token_row

    with (
        patch(_FEATURE, return_value=True),
        patch(f"{_AUTH}.decode_refresh_token", return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)}),
        patch.object(
            AuthService,
            "_get_current_user_from_refresh_v2",
            new_callable=AsyncMock,
        ) as mock_v2,
        patch(f"{_AUTH}.RefreshTokenService.validate_refresh_token", new_callable=AsyncMock) as mock_v1,
    ):
        mock_v2.return_value = {"nombre_usuario": "user", "es_activo": True}
        user = await AuthService.get_current_user_from_refresh(
            request,
            refresh_token_cookie=REFRESH_OLD,
        )

    assert user["nombre_usuario"] == "user"
    mock_v2.assert_awaited_once()
    mock_v1.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_get_current_user_from_refresh_v1_when_flag_off():
    request = MagicMock()
    request.headers = {"X-Client-Type": "web"}
    request.client = MagicMock(host="127.0.0.1")

    with (
        patch(_FEATURE, return_value=False),
        patch(f"{_AUTH}.decode_refresh_token", return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)}),
        patch(f"{_AUTH}.RefreshTokenService.validate_refresh_token", new_callable=AsyncMock, return_value={"usuario_id": USUARIO_ID, "empresa_id": None}),
        patch.object(
            AuthService,
            "_fetch_user_row_for_refresh",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": USUARIO_ID,
                "es_activo": True,
                "cliente_id": CLIENTE_ID,
            },
        ),
        patch.object(
            AuthService,
            "_get_current_user_from_refresh_v2",
            new_callable=AsyncMock,
        ) as mock_v2,
    ):
        user = await AuthService.get_current_user_from_refresh(
            request,
            refresh_token_cookie=REFRESH_OLD,
        )

    assert user["es_activo"] is True
    mock_v2.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_refresh_v2_validation_rejects_missing_user():
    request = MagicMock()
    request.headers = {"X-Client-Type": "web"}

    with (
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.hash_token",
            return_value="a" * 64,
        ),
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch.object(
            AuthService,
            "_fetch_user_row_for_refresh",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await AuthService._get_current_user_from_refresh_v2(
                request=request,
                refresh_token=REFRESH_OLD,
                payload={"sub": "user"},
                token_cliente_id=CLIENTE_ID,
                client_type="web",
            )
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_f10_auth_service_orchestrator_has_no_direct_session_sql():
    import inspect

    source = inspect.getsource(AuthService.persist_login_session)
    assert "execute_query" not in source
    assert "INSERT" not in source

    rotate_src = inspect.getsource(AuthService.rotate_refresh_session)
    assert "revoke_session_tx" not in rotate_src


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_probe_session_id_inactive_when_token_revoked():
    from app.modules.auth.application.services.session_probe_service import (
        SessionProbeService,
    )

    session_id = uuid4()
    token_id = uuid4()
    with (
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionQueryService.get_session",
            new_callable=AsyncMock,
            return_value={"session_id": session_id, "is_active": True},
        ),
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionQueryService.get_family_for_session",
            new_callable=AsyncMock,
            return_value={"family_id": uuid4(), "current_token_id": token_id},
        ),
        patch(
            "app.modules.auth.application.services.session_probe_service._get_token_by_id_core",
            new_callable=AsyncMock,
            return_value={"token_id": token_id, "is_revoked": True, "is_used": False},
        ),
    ):
        result = await SessionProbeService.resolve_context(
            CLIENTE_ID,
            access_session_id=session_id,
        )

    assert result.current_session_id == session_id
    assert result.is_active is False


@pytest.mark.unit
def test_f10_materialize_auth_user_row_coerces_sql_strings_to_uuid():
    usuario_id = uuid4()
    cliente_id = uuid4()
    row = {
        "usuario_id": str(usuario_id),
        "cliente_id": str(cliente_id),
        "nombre_usuario": "admin",
    }
    materialized = AuthService._materialize_auth_user_row(row)
    assert materialized is row
    assert materialized["usuario_id"] == usuario_id
    assert isinstance(materialized["usuario_id"], UUID)
    assert materialized["cliente_id"] == cliente_id
    assert isinstance(materialized["cliente_id"], UUID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f10_rotate_refresh_session_coerces_str_usuario_id_for_v2_motor():
    """Regresión F5: row SQL str → motor V2 recibe UUID (no USER_MISMATCH falso)."""
    usuario_id = uuid4()
    v2_result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        new_token_id=uuid4(),
    )
    with (
        patch(_FEATURE, return_value=True),
        patch(
            "app.modules.auth.application.services.session_rotation_service.SessionRotationService.rotate",
            new_callable=AsyncMock,
            return_value=v2_result,
        ) as mock_v2,
    ):
        await AuthService.rotate_refresh_session(
            old_refresh_token=REFRESH_OLD,
            new_refresh_token=REFRESH_NEW,
            cliente_id=CLIENTE_ID,
            usuario_id=str(usuario_id),
            client_type="web",
            ip_address="10.0.0.1",
            user_agent="agent",
            empresa_id=None,
            refresh_expire_days=7,
            new_access_jti=ACCESS_JTI,
            access_expire_minutes=15,
        )
    assert mock_v2.await_args.kwargs["usuario_id"] == usuario_id
    assert isinstance(mock_v2.await_args.kwargs["usuario_id"], UUID)
