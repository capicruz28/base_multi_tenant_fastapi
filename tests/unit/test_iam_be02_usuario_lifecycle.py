"""IAM-BE-02: invariantes y consolidación del ciclo de vida de Usuario."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.modules.users.application.services.user_service import UsuarioService
from app.shared.usuario_lifecycle import (
    assert_usuario_delete_state,
    assert_usuario_lifecycle_valid,
    assert_usuario_reactivate_state,
)

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()


def test_lifecycle_invalid_state_raises():
    with pytest.raises(ValidationError) as exc:
        assert_usuario_lifecycle_valid(es_activo=True, es_eliminado=True)
    assert exc.value.internal_code == "USER_LIFECYCLE_INVALID"


def test_lifecycle_valid_states_pass():
    assert_usuario_lifecycle_valid(es_activo=True, es_eliminado=False)
    assert_usuario_lifecycle_valid(es_activo=False, es_eliminado=False)
    assert_usuario_lifecycle_valid(es_activo=False, es_eliminado=True)


def test_delete_and_reactivate_state_helpers():
    assert_usuario_delete_state(es_activo=False, es_eliminado=True)
    assert_usuario_reactivate_state(es_activo=True, es_eliminado=False)


@pytest.mark.asyncio
async def test_actualizar_rejects_es_eliminado_in_payload():
    with patch.object(
        UsuarioService,
        "obtener_usuario_por_id",
        new_callable=AsyncMock,
        return_value={"usuario_id": USUARIO_ID, "es_activo": True},
    ):
        with pytest.raises(ValidationError) as exc:
            await UsuarioService.actualizar_usuario(
                CLIENTE_ID,
                USUARIO_ID,
                {"es_eliminado": True},
            )
    assert exc.value.internal_code == "USER_ELIMINADO_NOT_EDITABLE"


@pytest.mark.asyncio
async def test_actualizar_deactivate_only_es_activo():
    captured_sql = []

    async def fake_update(query, params):
        captured_sql.append(str(query))
        return {"usuario_id": USUARIO_ID, "es_activo": False}

    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={"usuario_id": USUARIO_ID, "es_activo": True},
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            side_effect=fake_update,
        ),
    ):
        result = await UsuarioService.actualizar_usuario(
            CLIENTE_ID,
            USUARIO_ID,
            {"es_activo": False},
        )

    assert result["es_activo"] is False
    sql = captured_sql[0]
    assert "es_activo = ?" in sql
    assert "es_eliminado = ?" not in sql


@pytest.mark.asyncio
async def test_reactivar_post_state_is_active_not_deleted():
    usuario_inactivo = {
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "es_eliminado": True,
        "es_activo": False,
    }
    usuario_reactivado = {
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "nombre_usuario": "u1",
        "correo": "a@b.com",
        "es_activo": True,
    }
    revisado = {**usuario_inactivo, "es_eliminado": False, "es_activo": True}

    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_incluyendo_eliminados",
            new_callable=AsyncMock,
            side_effect=[usuario_inactivo, revisado],
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            new_callable=AsyncMock,
            return_value={"usuario_id": USUARIO_ID},
        ),
        patch.object(
            UsuarioService,
            "obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value=usuario_reactivado,
        ),
    ):
        result = await UsuarioService.reactivar_usuario(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
        )

    assert result["es_activo"] is True


@pytest.mark.asyncio
async def test_reactivar_fixes_invalid_pre_state():
    usuario_invalido = {
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "es_eliminado": True,
        "es_activo": True,
    }
    revisado = {**usuario_invalido, "es_eliminado": False, "es_activo": True}

    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_incluyendo_eliminados",
            new_callable=AsyncMock,
            side_effect=[usuario_invalido, revisado],
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            new_callable=AsyncMock,
            return_value={"usuario_id": USUARIO_ID},
        ),
        patch.object(
            UsuarioService,
            "obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value={"usuario_id": USUARIO_ID, "es_activo": True},
        ),
    ):
        await UsuarioService.reactivar_usuario(
            cliente_id=CLIENTE_ID,
            usuario_id=USUARIO_ID,
        )
