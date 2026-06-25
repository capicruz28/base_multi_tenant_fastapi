"""F11 — empresa, password change e impersonation V1/V2 detrás del feature flag."""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.impersonation_service import ImpersonationService
from app.modules.auth.application.services.password_change_service import PasswordChangeService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
EMPRESA_ID = uuid4()
SESSION_ID = uuid4()
REFRESH_OLD = "old-refresh-plain"
REFRESH_NEW = "new-refresh-plain"

_AUTH = "app.modules.auth.application.services.auth_service"
_PWD = "app.modules.auth.application.services.password_change_service"
_IMP = "app.modules.auth.application.services.impersonation_service"
_FEATURE_AUTH = f"{_AUTH}.is_session_v2_enabled"
_FEATURE_PWD = f"{_PWD}.is_session_v2_enabled"
_FEATURE_IMP = f"{_IMP}.is_session_v2_enabled"


def _selection_payload():
    return {
        "sub": "testuser",
        "cliente_id": str(CLIENTE_ID),
        "empresa_selection_pending": True,
        "jti": "selection-jti",
        "exp": 9999999999,
        "type": "access",
    }


def _session_out():
    return {
        "access_token": "access",
        "refresh_token": REFRESH_NEW,
        "access_jti": "access-jti",
        "access_expire_minutes": 15,
        "access_exp": 9999999999,
        "user_data": {"nombre_usuario": "testuser"},
        "refresh_expire_days": 7,
    }


def _auth_context():
    return type(
        "Ctx",
        (),
        {"usuario_id": USUARIO_ID, "cliente_id": CLIENTE_ID, "es_activo": True},
    )()


def _seleccionar_patches(*, flag_off: bool = True):
    return [
        patch(_FEATURE_AUTH, return_value=not flag_off),
        patch(f"{_AUTH}.get_current_client_id", return_value=CLIENTE_ID),
        patch(
            "app.core.auth.user_context.get_user_auth_context",
            AsyncMock(return_value=_auth_context()),
        ),
        patch(
            "app.core.auth.user_context.validate_tenant_access",
            new=AsyncMock(return_value=True),
        ),
        patch.object(AuthService, "validar_empresa_para_sesion", new=AsyncMock()),
        patch(
            "app.core.tenant.empresa_preference.persist_usuario_empresa_default_id",
            new=AsyncMock(),
        ),
        patch.object(
            AuthService,
            "emitir_sesion_completa_con_empresa",
            new=AsyncMock(return_value=_session_out()),
        ),
        patch.object(AuthService, "blacklist_access_token_jti", new=AsyncMock()),
    ]


def _cambiar_payload(empresa_anterior=None):
    return {
        "sub": "testuser",
        "cliente_id": str(CLIENTE_ID),
        "empresa_id": str(empresa_anterior or uuid4()),
        "empresa_selection_pending": False,
        "type": "access",
    }


def _cambiar_patches(*, flag_off: bool = True):
    rotate_result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        new_token_id=uuid4(),
    )
    return [
        patch(_FEATURE_AUTH, return_value=not flag_off),
        patch(f"{_AUTH}.get_current_client_id", return_value=CLIENTE_ID),
        patch(
            "app.core.auth.user_context.get_user_auth_context",
            AsyncMock(return_value=_auth_context()),
        ),
        patch(
            "app.core.auth.user_context.validate_tenant_access",
            new=AsyncMock(return_value=True),
        ),
        patch.object(AuthService, "validar_empresa_para_sesion", new=AsyncMock()),
        patch(
            "app.core.tenant.empresa_preference.persist_usuario_empresa_default_id",
            new=AsyncMock(),
        ),
        patch.object(
            AuthService,
            "emitir_sesion_completa_con_empresa",
            new=AsyncMock(return_value=_session_out()),
        ),
        patch(
            f"{_AUTH}.rotate_refresh_token_service",
            new=AsyncMock(return_value=rotate_result),
        ),
        patch.object(
            AuthService,
            "rotate_refresh_session",
            new=AsyncMock(return_value=rotate_result),
        ),
        patch(f"{_AUTH}.RefreshTokenService.store_refresh_token", new=AsyncMock()),
        patch(f"{_AUTH}.RefreshTokenService.link_session_access_jti", new=AsyncMock()),
        patch(f"{_AUTH}.AuditService.registrar_auth_event", new=AsyncMock()),
    ]


def _mock_user():
    user = MagicMock()
    user.usuario_id = USUARIO_ID
    user.cliente_id = CLIENTE_ID
    user.nombre_usuario = "testuser"
    user.proveedor_autenticacion = "local"
    user.correo = "u@test.com"
    user.nombre = "Test"
    user.apellido = "User"
    user.es_activo = True
    return user


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_seleccionar_empresa_v1_uses_store_and_audit_service():
    with ExitStack() as stack:
        for p in _seleccionar_patches(flag_off=True):
            stack.enter_context(p)
        mock_store = stack.enter_context(
            patch(f"{_AUTH}.RefreshTokenService.store_refresh_token", new=AsyncMock(return_value={"token_id": uuid4()}))
        )
        mock_link = stack.enter_context(
            patch(f"{_AUTH}.RefreshTokenService.link_session_access_jti", new=AsyncMock())
        )
        mock_persist = stack.enter_context(
            patch.object(AuthService, "persist_login_session", new=AsyncMock(return_value=False))
        )
        stack.enter_context(patch(f"{_AUTH}.is_session_v2_enabled", return_value=False))
        mock_audit = stack.enter_context(
            patch(f"{_AUTH}.AuditService.registrar_auth_event", new=AsyncMock())
        )
        mock_emit = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_audit_emitter.SessionAuditEmitter.emit_empresa_selected",
                new=AsyncMock(),
            )
        )
        await AuthService.seleccionar_empresa_post_login(
            payload=_selection_payload(),
            empresa_id=EMPRESA_ID,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    mock_persist.assert_not_awaited()
    mock_store.assert_awaited_once()
    mock_link.assert_awaited_once()
    mock_audit.assert_awaited_once()
    mock_emit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_seleccionar_empresa_v2_uses_persist_and_session_audit():
    ctx = MagicMock(session_id=SESSION_ID)
    with ExitStack() as stack:
        for p in _seleccionar_patches(flag_off=False):
            stack.enter_context(p)
        mock_store = stack.enter_context(
            patch(f"{_AUTH}.RefreshTokenService.store_refresh_token", new=AsyncMock())
        )
        mock_persist = stack.enter_context(
            patch.object(AuthService, "persist_login_session", new=AsyncMock(return_value=True))
        )
        stack.enter_context(patch(f"{_AUTH}.is_session_v2_enabled", return_value=True))
        mock_resolve = stack.enter_context(
            patch.object(
                AuthService,
                "_resolve_v2_session_id_from_refresh",
                new=AsyncMock(return_value=SESSION_ID),
            )
        )
        mock_audit = stack.enter_context(
            patch(f"{_AUTH}.AuditService.registrar_auth_event", new=AsyncMock())
        )
        mock_emit = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_audit_emitter.SessionAuditEmitter.emit_empresa_selected",
                new=AsyncMock(),
            )
        )
        await AuthService.seleccionar_empresa_post_login(
            payload=_selection_payload(),
            empresa_id=EMPRESA_ID,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    mock_persist.assert_awaited_once()
    mock_store.assert_not_awaited()
    mock_resolve.assert_awaited_once()
    mock_emit.assert_awaited_once()
    mock_audit.assert_not_awaited()
    _ = ctx


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_cambiar_empresa_v1_uses_rotate_refresh_token_service():
    with ExitStack() as stack:
        for p in _cambiar_patches(flag_off=True):
            stack.enter_context(p)
        mock_v1_rotate = stack.enter_context(
            patch(
                f"{_AUTH}.rotate_refresh_token_service",
                new=AsyncMock(
                    return_value=RotateResult(
                        outcome=RotateOutcome.ROTATED,
                        cliente_id=CLIENTE_ID,
                        new_token_id=uuid4(),
                    )
                ),
            )
        )
        mock_v2_rotate = stack.enter_context(
            patch.object(AuthService, "rotate_refresh_session", new=AsyncMock())
        )
        mock_update = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_creation_service.SessionCreationService.update_empresa",
                new=AsyncMock(),
            )
        )
        mock_emit = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_audit_emitter.SessionAuditEmitter.emit_empresa_changed",
                new=AsyncMock(),
            )
        )
        mock_audit = stack.enter_context(
            patch(f"{_AUTH}.AuditService.registrar_auth_event", new=AsyncMock())
        )
        await AuthService.cambiar_empresa_sesion(
            payload=_cambiar_payload(),
            empresa_id=EMPRESA_ID,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=REFRESH_OLD,
        )

    mock_v1_rotate.assert_awaited_once()
    mock_v2_rotate.assert_not_awaited()
    mock_update.assert_not_awaited()
    mock_emit.assert_not_awaited()
    mock_audit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_cambiar_empresa_v2_updates_session_and_rotates():
    ctx = MagicMock(session_id=SESSION_ID)
    rotate_result = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        new_token_id=uuid4(),
    )
    with ExitStack() as stack:
        for p in _cambiar_patches(flag_off=False):
            stack.enter_context(p)
        mock_v1_rotate = stack.enter_context(
            patch(f"{_AUTH}.rotate_refresh_token_service", new=AsyncMock())
        )
        mock_v2_rotate = stack.enter_context(
            patch.object(
                AuthService,
                "rotate_refresh_session",
                new=AsyncMock(return_value=rotate_result),
            )
        )
        mock_update = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_creation_service.SessionCreationService.update_empresa",
                new=AsyncMock(),
            )
        )
        mock_get_ctx = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_query_service.SessionQueryService.get_by_hash_any_state",
                new=AsyncMock(return_value=ctx),
            )
        )
        mock_emit = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_audit_emitter.SessionAuditEmitter.emit_empresa_changed",
                new=AsyncMock(),
            )
        )
        mock_audit = stack.enter_context(
            patch(f"{_AUTH}.AuditService.registrar_auth_event", new=AsyncMock())
        )
        await AuthService.cambiar_empresa_sesion(
            payload=_cambiar_payload(),
            empresa_id=EMPRESA_ID,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=REFRESH_OLD,
        )

    mock_get_ctx.assert_awaited_once()
    mock_update.assert_awaited_once()
    mock_v2_rotate.assert_awaited_once()
    mock_v1_rotate.assert_not_awaited()
    mock_emit.assert_awaited_once()
    mock_audit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_cambiar_empresa_v2_without_refresh_updates_existing_session():
    payload = _cambiar_payload()
    payload["sid"] = str(SESSION_ID)
    with ExitStack() as stack:
        for p in _cambiar_patches(flag_off=False):
            stack.enter_context(p)
        mock_persist = stack.enter_context(
            patch.object(AuthService, "persist_login_session", new=AsyncMock())
        )
        mock_update = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_creation_service.SessionCreationService.update_empresa",
                new=AsyncMock(),
            )
        )
        mock_reissue = stack.enter_context(
            patch.object(
                AuthService,
                "_reissue_access_token_with_sid",
                new=AsyncMock(),
            )
        )
        mock_emit = stack.enter_context(
            patch(
                "app.modules.auth.application.services.session_audit_emitter.SessionAuditEmitter.emit_empresa_changed",
                new=AsyncMock(),
            )
        )
        await AuthService.cambiar_empresa_sesion(
            payload=payload,
            empresa_id=EMPRESA_ID,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=None,
        )

    mock_persist.assert_not_awaited()
    mock_update.assert_awaited_once()
    mock_reissue.assert_awaited_once()
    mock_emit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_password_change_v1_revokes_v1_tokens():
    with (
        patch(_FEATURE_PWD, return_value=False),
        patch.object(
            AuthService,
            "fetch_user_password_policy_fields",
            new=AsyncMock(return_value={"contrasena": "hashed"}),
        ),
        patch(
            f"{_PWD}.verify_password",
            return_value=True,
        ),
        patch(f"{_PWD}.get_password_hash", return_value="new-hash"),
        patch(f"{_PWD}.execute_update", new=AsyncMock()),
        patch(
            f"{_PWD}.RefreshTokenService.blacklist_access_for_user_active_sessions",
            new=AsyncMock(),
        ) as mock_bl_user,
        patch(
            f"{_PWD}.RefreshTokenService.revoke_all_user_tokens",
            new=AsyncMock(return_value=2),
        ) as mock_revoke_all,
        patch.object(AuthService, "blacklist_access_token_jti", new=AsyncMock()),
        patch.object(
            AuthService,
            "emitir_sesion_completa_con_empresa",
            new=AsyncMock(return_value=_session_out()),
        ),
        patch(f"{_PWD}.RefreshTokenService.store_refresh_token", new=AsyncMock(return_value={"token_id": uuid4()})),
        patch(f"{_PWD}.RefreshTokenService.link_session_access_jti", new=AsyncMock()),
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_due_to_password_change",
            new=AsyncMock(),
        ) as mock_v2_revoke,
        patch.object(AuthService, "persist_login_session", new=AsyncMock(return_value=False)),
    ):
        await PasswordChangeService.change_password(
            current_user=_mock_user(),
            current_password="old",
            new_password="NewPass1!",
            payload={"empresa_id": str(EMPRESA_ID)},
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=REFRESH_OLD,
            access_jti="jti",
            access_exp=999,
        )

    mock_revoke_all.assert_awaited_once()
    mock_bl_user.assert_awaited_once()
    mock_v2_revoke.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_password_change_v2_uses_revocation_and_persist():
    with (
        patch(_FEATURE_PWD, return_value=True),
        patch.object(
            AuthService,
            "fetch_user_password_policy_fields",
            new=AsyncMock(return_value={"contrasena": "hashed"}),
        ),
        patch(f"{_PWD}.verify_password", return_value=True),
        patch(f"{_PWD}.get_password_hash", return_value="new-hash"),
        patch(f"{_PWD}.execute_update", new=AsyncMock()),
        patch(
            f"{_PWD}.RefreshTokenService.blacklist_access_for_user_active_sessions",
            new=AsyncMock(),
        ) as mock_bl_user,
        patch(
            f"{_PWD}.RefreshTokenService.revoke_all_user_tokens",
            new=AsyncMock(),
        ) as mock_revoke_all,
        patch.object(AuthService, "blacklist_access_token_jti", new=AsyncMock()) as mock_bl_jti,
        patch.object(
            AuthService,
            "emitir_sesion_completa_con_empresa",
            new=AsyncMock(return_value=_session_out()),
        ),
        patch.object(AuthService, "persist_login_session", new=AsyncMock(return_value=True)) as mock_persist,
        patch.object(
            AuthService,
            "_attach_v2_sid_after_persist",
            new=AsyncMock(return_value=SESSION_ID),
        ) as mock_attach_sid,
        patch(
            "app.modules.auth.application.services.session_revocation_service.SessionRevocationService.revoke_due_to_password_change",
            new=AsyncMock(return_value=3),
        ) as mock_v2_revoke,
        patch(f"{_PWD}.RefreshTokenService.store_refresh_token", new=AsyncMock()),
    ):
        await PasswordChangeService.change_password(
            current_user=_mock_user(),
            current_password="old",
            new_password="NewPass1!",
            payload={"empresa_id": str(EMPRESA_ID)},
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=REFRESH_OLD,
            access_jti="jti",
            access_exp=999,
        )

    mock_v2_revoke.assert_awaited_once()
    mock_persist.assert_awaited_once()
    mock_attach_sid.assert_awaited_once()
    mock_bl_jti.assert_awaited_once()
    mock_revoke_all.assert_not_awaited()
    mock_bl_user.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_impersonation_start_v1_skips_v2_probe():
    target = uuid4()
    with (
        patch(_FEATURE_IMP, return_value=False),
        patch.object(
            ImpersonationService,
            "_assert_parent_refresh_active_v2",
            new=AsyncMock(),
        ) as mock_assert,
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
            new=AsyncMock(),
        ) as mock_probe,
        patch(
            "app.modules.tenant.application.services.cliente_service.ClienteService.obtener_cliente_por_id",
            new=AsyncMock(return_value=MagicMock(es_activo=True)),
        ),
        patch.object(
            ImpersonationService,
            "_resolver_operador_superadmin",
            new=AsyncMock(return_value={"nombre_usuario": "sa", "usuario_id": uuid4()}),
        ),
        patch.object(
            AuthService,
            "_listar_empresas_activas_org",
            new=AsyncMock(return_value=[{"empresa_id": EMPRESA_ID}]),
        ),
        patch.object(
            ImpersonationService,
            "_emitir_access_impersonacion",
            new=AsyncMock(
                return_value={
                    "access_token": "imp",
                    "access_jti": "imp-jti",
                    "user_data": {},
                }
            ),
        ),
        patch(
            "app.core.auth.impersonation.store_parent_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.modules.superadmin.application.services.audit_service.AuditService.registrar_auth_event",
            new=AsyncMock(),
        ),
    ):
        await ImpersonationService.iniciar_impersonacion(
            target_cliente_id=target,
            operator_usuario_id=USUARIO_ID,
            operator_username="operator",
            parent_access_token="parent-access",
            parent_refresh_token=REFRESH_OLD,
            parent_payload={"cliente_id": str(CLIENTE_ID)},
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    mock_assert.assert_awaited_once()
    mock_probe.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_impersonation_start_v2_rejects_inactive_parent():
    target = uuid4()
    with (
        patch(_FEATURE_IMP, return_value=True),
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
            new=AsyncMock(return_value=MagicMock(is_active=False)),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await ImpersonationService.iniciar_impersonacion(
                target_cliente_id=target,
                operator_usuario_id=USUARIO_ID,
                operator_username="operator",
                parent_access_token="parent-access",
                parent_refresh_token=REFRESH_OLD,
                parent_payload={"cliente_id": str(CLIENTE_ID)},
                ip_address="127.0.0.1",
                user_agent="pytest",
            )
    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_impersonation_end_v2_rejects_closed_parent_session():
    payload = {
        "jti": "imp-jti",
        "exp": 999,
        "is_impersonation": True,
        "impersonated_by": str(USUARIO_ID),
        "cliente_id": str(uuid4()),
        "impersonated_by_username": "operator",
    }
    with (
        patch(
            f"{_IMP}.pop_parent_session",
            new=AsyncMock(
                return_value={
                    "parent_access_token": "restored-access",
                    "parent_refresh_token": REFRESH_OLD,
                }
            ),
        ),
        patch.object(AuthService, "blacklist_access_token_jti", new=AsyncMock()),
        patch(f"{_IMP}.decode_refresh_token", return_value={"cliente_id": str(CLIENTE_ID)}),
        patch(_FEATURE_IMP, return_value=True),
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
            new=AsyncMock(return_value=MagicMock(is_active=False)),
        ),
        patch(
            "app.modules.superadmin.application.services.audit_service.AuditService.registrar_auth_event",
            new=AsyncMock(),
        ),
    ):
        with pytest.raises(HTTPException) as exc:
            await ImpersonationService.finalizar_impersonacion(
                payload=payload,
                ip_address="127.0.0.1",
                user_agent="pytest",
            )
    assert exc.value.status_code == 410


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f11_impersonation_end_v1_restores_without_probe():
    payload = {
        "jti": "imp-jti",
        "exp": 999,
        "is_impersonation": True,
        "impersonated_by": str(USUARIO_ID),
        "cliente_id": str(uuid4()),
        "impersonated_by_username": "operator",
    }
    with (
        patch(
            f"{_IMP}.pop_parent_session",
            new=AsyncMock(
                return_value={
                    "parent_access_token": "restored-access",
                    "parent_refresh_token": REFRESH_OLD,
                }
            ),
        ),
        patch.object(AuthService, "blacklist_access_token_jti", new=AsyncMock()),
        patch(f"{_IMP}.decode_refresh_token", return_value={"cliente_id": str(CLIENTE_ID)}),
        patch(_FEATURE_IMP, return_value=False),
        patch(
            "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
            new=AsyncMock(),
        ) as mock_probe,
        patch(
            "app.modules.superadmin.application.services.audit_service.AuditService.registrar_auth_event",
            new=AsyncMock(),
        ),
    ):
        result = await ImpersonationService.finalizar_impersonacion(
            payload=payload,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

    assert result["access_token"] == "restored-access"
    mock_probe.assert_not_awaited()
