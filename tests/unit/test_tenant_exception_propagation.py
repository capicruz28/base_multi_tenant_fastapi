"""Tenant presentation must propagate CustomException to the global handler (not mask as 500)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.tenant.presentation import endpoints_clientes as clientes_ep
from app.modules.tenant.presentation import endpoints_conexiones as conexiones_ep


def _unwrap(fn):
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _fake_user():
    user = MagicMock()
    user.nombre_usuario = "pytest-superadmin"
    user.usuario_id = uuid4()
    return user


@pytest.mark.asyncio
async def test_crear_cliente_propagates_conflict_error():
    crear = _unwrap(clientes_ep.crear_cliente)
    cliente_data = MagicMock(razon_social="QA Tenant")
    conflict = ConflictError(
        detail="El código de cliente 'CLI003' ya está en uso.",
        internal_code="CLIENT_CODE_CONFLICT",
    )
    with patch.object(
        clientes_ep.ClienteService,
        "crear_cliente",
        new_callable=AsyncMock,
        side_effect=conflict,
    ):
        with pytest.raises(ConflictError) as exc:
            await crear(cliente_data=cliente_data, current_user=_fake_user())

    assert exc.value.status_code == 409
    assert exc.value.internal_code == "CLIENT_CODE_CONFLICT"


@pytest.mark.asyncio
async def test_actualizar_cliente_propagates_subdomain_conflict():
    actualizar = _unwrap(clientes_ep.actualizar_cliente)
    cliente_id = uuid4()
    cliente_data = MagicMock()
    conflict = ConflictError(
        detail="El subdominio 'dup' ya está en uso por otro cliente activo.",
        internal_code="SUBDOMAIN_CONFLICT",
    )
    with patch.object(
        clientes_ep.ClienteService,
        "actualizar_cliente",
        new_callable=AsyncMock,
        side_effect=conflict,
    ):
        with pytest.raises(ConflictError) as exc:
            await actualizar(
                cliente_id=cliente_id,
                cliente_data=cliente_data,
                current_user=_fake_user(),
            )

    assert exc.value.status_code == 409
    assert exc.value.internal_code == "SUBDOMAIN_CONFLICT"


@pytest.mark.asyncio
async def test_obtener_estadisticas_propagates_not_found():
    stats = _unwrap(clientes_ep.obtener_estadisticas_cliente)
    cliente_id = uuid4()
    not_found = NotFoundError(
        detail=f"Cliente con ID {cliente_id} no encontrado.",
        internal_code="CLIENT_NOT_FOUND",
    )
    with patch.object(
        clientes_ep.ClienteService,
        "obtener_estadisticas",
        new_callable=AsyncMock,
        side_effect=not_found,
    ):
        with pytest.raises(NotFoundError) as exc:
            await stats(cliente_id=cliente_id, current_user=_fake_user())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_branding_subdominio_propagates_validation_and_not_found():
    branding = clientes_ep.obtener_branding_por_subdominio
    validation = ValidationError(
        detail="El subdominio no es válido.",
        internal_code="SUBDOMAIN_INVALID",
    )
    not_found = NotFoundError(
        detail="Subdominio no encontrado.",
        internal_code="CLIENT_NOT_FOUND",
    )

    with patch.object(
        clientes_ep.ClienteService,
        "get_branding_by_subdomain",
        new_callable=AsyncMock,
        side_effect=validation,
    ):
        with pytest.raises(ValidationError) as exc:
            await branding(subdominio="bad!")
        assert exc.value.status_code == 400

    with patch.object(
        clientes_ep.ClienteService,
        "get_branding_by_subdomain",
        new_callable=AsyncMock,
        side_effect=not_found,
    ):
        with pytest.raises(NotFoundError) as exc:
            await branding(subdominio="missing")
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_crear_conexion_propagates_conflict_error():
    crear = _unwrap(conexiones_ep.crear_conexion)
    cliente_id = uuid4()
    conexion_data = MagicMock()
    conflict = ConflictError(
        detail="Ya existe una conexión principal para este cliente.",
        internal_code="PRIMARY_CONNECTION_EXISTS",
    )
    with patch.object(
        conexiones_ep.ConexionService,
        "crear_conexion",
        new_callable=AsyncMock,
        side_effect=conflict,
    ):
        with pytest.raises(ConflictError) as exc:
            await crear(
                cliente_id=cliente_id,
                conexion_data=conexion_data,
                current_user=_fake_user(),
            )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_eliminar_cliente_propagates_not_found():
    eliminar = _unwrap(clientes_ep.eliminar_cliente)
    cliente_id = uuid4()
    not_found = NotFoundError(
        detail=f"Cliente con ID {cliente_id} no encontrado.",
        internal_code="CLIENT_NOT_FOUND",
    )
    with patch.object(
        clientes_ep.ClienteService,
        "eliminar_cliente",
        new_callable=AsyncMock,
        side_effect=not_found,
    ):
        with pytest.raises(NotFoundError) as exc:
            await eliminar(cliente_id=cliente_id, current_user=_fake_user())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_global_handler_maps_conflict_to_409_with_error_code():
    from fastapi import FastAPI
    from starlette.requests import Request

    from app.core.exceptions import configure_exception_handlers

    app = FastAPI()
    configure_exception_handlers(app)
    from app.core.exceptions import CustomException

    handler = app.exception_handlers[CustomException]

    exc = ConflictError(
        detail="El código de cliente 'CLI003' ya está en uso.",
        internal_code="CLIENT_CODE_CONFLICT",
    )
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/api/v1/clientes/",
        "headers": [],
    }
    response = await handler(Request(scope), exc)
    assert response.status_code == 409
    import json

    body = json.loads(response.body)
    assert body["detail"] == "El código de cliente 'CLI003' ya está en uso."
    assert body["error_code"] == "CLIENT_CODE_CONFLICT"
