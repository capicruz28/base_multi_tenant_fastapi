"""IAM-BE-SESSIONS-P0-01: integridad del dominio Session Management."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AuthenticationError
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.revoked_reason import RevokedReason

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()


@pytest.mark.asyncio
async def test_handle_revoked_refresh_reuse_revokes_all_and_raises():
    mock_revoke = AsyncMock(return_value=2)
    mock_blacklist = AsyncMock(return_value=1)
    mock_audit = AsyncMock()

    with patch(
        "app.modules.auth.application.services.refresh_token_service.AuditService.registrar_auth_event",
        mock_audit,
    ), patch.object(
        RefreshTokenService,
        "revoke_all_user_tokens",
        mock_revoke,
    ), patch.object(
        RefreshTokenService,
        "blacklist_access_for_user_active_sessions",
        mock_blacklist,
    ):
        with pytest.raises(AuthenticationError) as exc:
            await RefreshTokenService.handle_revoked_refresh_reuse(
                cliente_id=CLIENTE_ID,
                usuario_id=USUARIO_ID,
                username="admin",
                context="refresh",
            )

    assert exc.value.internal_code == "REFRESH_TOKEN_REUSE_DETECTED"
    mock_blacklist.assert_awaited_once_with(CLIENTE_ID, USUARIO_ID)
    mock_revoke.assert_awaited_once_with(
        CLIENTE_ID, USUARIO_ID, revoked_reason=RevokedReason.TOKEN_REUSE
    )
    mock_audit.assert_awaited_once()


@pytest.mark.asyncio
async def test_blacklist_access_for_token_id_uses_redis_mapping():
    mock_get = AsyncMock(return_value={"jti": "jti-abc", "exp": 9999999999})
    mock_delete = AsyncMock(return_value=True)
    mock_blacklist = AsyncMock()

    with patch(
        "app.infrastructure.redis.client.RedisService.get_json",
        mock_get,
    ), patch(
        "app.infrastructure.redis.client.RedisService.delete_key",
        mock_delete,
    ), patch(
        "app.modules.auth.application.services.auth_service.AuthService.blacklist_access_token_jti",
        mock_blacklist,
    ):
        ok = await RefreshTokenService.blacklist_access_for_token_id(TOKEN_ID)

    assert ok is True
    mock_blacklist.assert_awaited_once_with("jti-abc", 9999999999)
    mock_delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_deactivate_revokes_refresh_tokens():
    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()
    update_result = {
        "usuario_id": usuario_id,
        "es_activo": False,
        "nombre_usuario": "u1",
    }

    mock_update = AsyncMock(return_value=update_result)
    mock_blacklist = AsyncMock(return_value=0)
    mock_revoke = AsyncMock(return_value=3)
    mock_obtener = AsyncMock(return_value={"usuario_id": usuario_id, "es_activo": True})

    with patch(
        "app.modules.users.application.services.user_service.UsuarioService.obtener_usuario_por_id",
        mock_obtener,
    ), patch(
        "app.modules.users.application.services.user_service.execute_update",
        mock_update,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.RefreshTokenService.blacklist_access_for_user_active_sessions",
        mock_blacklist,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.RefreshTokenService.revoke_all_user_tokens",
        mock_revoke,
    ):
        result = await UsuarioService.actualizar_usuario(
            cliente_id,
            usuario_id,
            {"es_activo": False},
        )

    assert result["es_activo"] is False
    mock_blacklist.assert_awaited_once_with(cliente_id, usuario_id)
    mock_revoke.assert_awaited_once_with(
        cliente_id, usuario_id, revoked_reason=RevokedReason.USER_DEACTIVATED
    )


@pytest.mark.asyncio
async def test_user_delete_revokes_refresh_tokens():
    from app.modules.users.application.services.user_service import UsuarioService

    cliente_id = uuid4()
    usuario_id = uuid4()

    mock_status = AsyncMock(return_value=[{"es_eliminado": False}])
    mock_update = AsyncMock(
        return_value={
            "usuario_id": usuario_id,
            "nombre_usuario": "u1",
            "es_eliminado": True,
        }
    )
    mock_roles = AsyncMock()
    mock_blacklist = AsyncMock(return_value=0)
    mock_revoke = AsyncMock(return_value=2)

    with patch(
        "app.modules.users.application.services.user_service.execute_query",
        mock_status,
    ), patch(
        "app.modules.users.application.services.user_service.execute_update",
        side_effect=[mock_update.return_value, mock_roles.return_value],
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.RefreshTokenService.blacklist_access_for_user_active_sessions",
        mock_blacklist,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.RefreshTokenService.revoke_all_user_tokens",
        mock_revoke,
    ), patch(
        "app.core.authorization.permission_resolver.get_permission_resolver",
        return_value=MagicMock(invalidate_for_user=MagicMock()),
    ):
        result = await UsuarioService.eliminar_usuario(cliente_id, usuario_id)

    assert result["es_eliminado"] is True
    mock_blacklist.assert_awaited_once_with(cliente_id, usuario_id)
    mock_revoke.assert_awaited_once_with(
        cliente_id, usuario_id, revoked_reason=RevokedReason.USER_DELETED
    )


@pytest.mark.asyncio
async def test_get_refresh_token_by_hash_any_state_includes_revoked():
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        get_refresh_token_by_hash_any_state_core,
    )

    mock_query = AsyncMock(
        return_value=[
            {
                "token_id": TOKEN_ID,
                "usuario_id": USUARIO_ID,
                "is_revoked": True,
                "cliente_id": CLIENTE_ID,
            }
        ]
    )
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        mock_query,
    ):
        row = await get_refresh_token_by_hash_any_state_core("hash", CLIENTE_ID)

    assert row is not None
    assert row["is_revoked"] is True
