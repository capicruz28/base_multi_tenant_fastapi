"""Ola 1 — org_departamento integración con motor de códigos."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.org.application.services import departamento_service
from app.modules.org.presentation.schemas import DepartamentoCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
DEPARTAMENTO_ID = uuid4()


def _departamento_create(*, codigo: str | None = "DEP001") -> DepartamentoCreate:
    return DepartamentoCreate(
        empresa_id=EMPRESA_ID,
        codigo=codigo,
        nombre="Ventas",
    )


def _departamento_row(codigo: str) -> dict:
    return {
        "departamento_id": DEPARTAMENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": codigo,
        "nombre": "Ventas",
        "es_activo": True,
    }


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_auto_generate_without_codigo():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo=None)

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ) as mock_get_conn:
                with patch(
                    "app.modules.org.application.services.departamento_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="DEP001",
                ) as mock_resolve:
                    with patch(
                        "app.modules.org.application.services.departamento_service.create_departamento",
                        new_callable=AsyncMock,
                        return_value=_departamento_row("DEP001"),
                    ) as mock_create:
                        result = await departamento_service.create_departamento_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    session.begin.assert_called_once()
    mock_resolve.assert_awaited_once_with(
        "org_departamento",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["codigo"] == "DEP001"
    assert result.codigo == "DEP001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_manual_codigo_accepted():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo="DEP999")

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.departamento_service.get_departamento_by_codigo",
                    new_callable=AsyncMock,
                    return_value=None,
                ) as mock_dup:
                    with patch(
                        "app.modules.org.application.services.departamento_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        return_value="DEP999",
                    ) as mock_resolve:
                        with patch(
                            "app.modules.org.application.services.departamento_service.create_departamento",
                            new_callable=AsyncMock,
                            return_value=_departamento_row("DEP999"),
                        ):
                            result = await departamento_service.create_departamento_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_dup.assert_awaited_once_with(
        CLIENT_ID, EMPRESA_ID, "DEP999", session=session
    )
    mock_resolve.assert_awaited_once_with(
        "org_departamento",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code="DEP999",
    )
    assert result.codigo == "DEP999"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_duplicate_manual_raises_conflict():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo="DEP001")

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.departamento_service.get_departamento_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_departamento_row("DEP001"),
                ):
                    with patch(
                        "app.modules.org.application.services.departamento_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                    ) as mock_resolve:
                        with pytest.raises(ConflictError):
                            await departamento_service.create_departamento_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_resolve.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_cfg_missing_propagates():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo=None)

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.departamento_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    side_effect=NotFoundError(
                        detail="Configuración de secuencia no encontrada.",
                        internal_code="CFG_SEQUENCE_NOT_FOUND",
                    ),
                ):
                    with patch(
                        "app.modules.org.application.services.departamento_service.create_departamento",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(NotFoundError):
                            await departamento_service.create_departamento_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_create.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_single_transaction_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo=None)

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.departamento_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="DEP002",
                ):
                    with patch(
                        "app.modules.org.application.services.departamento_service.create_departamento",
                        new_callable=AsyncMock,
                        return_value=_departamento_row("DEP002"),
                    ):
                        await departamento_service.create_departamento_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    session.begin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _departamento_create(codigo="DEP001")

    with patch(
        "app.modules.org.application.services.departamento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.departamento_service.get_departamento_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_departamento_row("DEP001"),
                ):
                    with patch(
                        "app.modules.org.application.services.departamento_service.create_departamento",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(ConflictError):
                            await departamento_service.create_departamento_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    session.begin.assert_called_once()
    mock_create.assert_not_called()


@pytest.mark.unit
def test_departamento_create_schema_accepts_missing_codigo():
    data = DepartamentoCreate(
        empresa_id=EMPRESA_ID,
        nombre="Ventas",
    )
    assert data.codigo is None
