"""Certificación MVP Backend cfg — unit tests (05_TESTING_GUIDE)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.codigo.generation_result import PreviewResult
from app.core.exceptions import CustomException, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.cfg.application.services import codigo_secuencia_admin_servicio as svc
from app.modules.cfg.presentation.schemas import (
    CodigoSecuenciaUpdate,
    PaginatedCodigoSecuenciaResponse,
)
from app.shared.pagination import ErpPaginationParams, ErpSortParams

CLIENT_ID = uuid4()
OTHER_CLIENT = uuid4()
SEQ_ID = uuid4()
EMPRESA_ID = uuid4()
USER_ID = uuid4()


def _session_cm(session):
    @asynccontextmanager
    async def _cm(*_a, **_k):
        yield session

    return _cm()


def _patch_codigos_activos(*codigos: str):
    return patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio"
        ".ClienteModuloService.obtener_codigos_modulos_activos_cliente",
        new_callable=AsyncMock,
        return_value={c.upper() for c in codigos},
    )


def _base_row(**overrides) -> dict:
    row = {
        "secuencia_id": SEQ_ID,
        "cliente_id": CLIENT_ID,
        "sequence_key": "org_sucursal",
        "scope_type": "EMPRESA",
        "scope_fingerprint": "fp",
        "empresa_id": EMPRESA_ID,
        "almacen_id": None,
        "punto_venta_id": None,
        "prefijo": "SUC",
        "separador": "",
        "longitud_numero": 3,
        "numero_inicial": 1,
        "ultimo_numero": 5,
        "es_activo": True,
        "generation_policy": "AUTO_DEFAULT",
        "fecha_creacion": datetime(2026, 1, 1),
        "fecha_actualizacion": None,
        "usuario_actualizacion_id": None,
    }
    row.update(overrides)
    return row


# ----- Validator / reglas (T-V*) -----


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tv01_patch_org_empresa_locked():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row(sequence_key="org_empresa", prefijo="EMP")

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with pytest.raises(CustomException) as exc:
                await svc.update_codigo_secuencia_servicio(
                    CLIENT_ID,
                    SEQ_ID,
                    CodigoSecuenciaUpdate(prefijo="XXX"),
                    usuario_id=USER_ID,
                )
    assert exc.value.internal_code == "ORG_EMPRESA_CFG_LOCKED"
    assert exc.value.status_code == 422


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tv02_desactivar_org_empresa_locked():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row(sequence_key="org_empresa")

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with pytest.raises(CustomException) as exc:
                await svc.desactivar_codigo_secuencia_servicio(
                    CLIENT_ID, SEQ_ID, usuario_id=USER_ID
                )
    assert exc.value.internal_code == "ORG_EMPRESA_CFG_LOCKED"


@pytest.mark.unit
def test_tv03_prefijo_invalido():
    row = _base_row()
    with pytest.raises(CustomException) as exc:
        svc._validate_patch_payload(row, CodigoSecuenciaUpdate(prefijo="BAD-PREF"))
    assert exc.value.internal_code == "CFG_PREFIX_INVALID"


@pytest.mark.unit
def test_tv04_separador_invalido():
    with pytest.raises(PydanticValidationError):
        CodigoSecuenciaUpdate(separador="*")


@pytest.mark.unit
def test_tv05_padding_lt_1():
    with pytest.raises(PydanticValidationError):
        CodigoSecuenciaUpdate(longitud_numero=0)


@pytest.mark.unit
def test_tv06_numero_inicial_lt_1():
    with pytest.raises(PydanticValidationError):
        CodigoSecuenciaUpdate(numero_inicial=0)


@pytest.mark.unit
def test_tv07_numero_inicial_le_ultimo_aceptado():
    row = _base_row(ultimo_numero=10)
    payload = svc._validate_patch_payload(
        row, CodigoSecuenciaUpdate(numero_inicial=3)
    )
    assert payload["numero_inicial"] == 3


@pytest.mark.unit
def test_tv08_generation_policy_ok():
    row = _base_row()
    payload = svc._validate_patch_payload(
        row, CodigoSecuenciaUpdate(generation_policy="auto_default")
    )
    assert payload["generation_policy"] == "AUTO_DEFAULT"


@pytest.mark.unit
def test_tv09_generation_policy_invalida():
    with pytest.raises(PydanticValidationError):
        CodigoSecuenciaUpdate(generation_policy="EXTERNAL")


@pytest.mark.unit
def test_tv10_generation_policy_org_empresa_locked():
    row = _base_row(sequence_key="org_empresa")
    with pytest.raises(CustomException) as exc:
        svc._validate_patch_payload(
            row, CodigoSecuenciaUpdate(generation_policy="MANUAL_ONLY")
        )
    assert exc.value.internal_code == "ORG_EMPRESA_CFG_LOCKED"


# ----- Enrich (T-E*) -----


@pytest.mark.unit
def test_te01_enrich_catalog_key():
    enriched = svc._enrich_row(_base_row(sequence_key="org_sucursal"))
    assert enriched["modulo_codigo"]
    assert enriched["entity_table"]
    assert enriched["catalog_policy"]


@pytest.mark.unit
def test_te02_policy_drift():
    enriched = svc._enrich_row(
        _base_row(sequence_key="org_sucursal", generation_policy="MANUAL_ONLY")
    )
    assert enriched["policy_drift"] is True


@pytest.mark.unit
def test_te03_org_empresa_config_locked():
    enriched = svc._enrich_row(_base_row(sequence_key="org_empresa"))
    assert enriched["config_locked"] is True


# ----- Lectura (T-L*) -----


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl01_list_pasa_cliente_id():
    session = AsyncMock()
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.list_codigo_secuencias",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_list:
            with _patch_codigos_activos("ORG"):
                await svc.list_codigo_secuencias_servicio(CLIENT_ID)
    assert mock_list.await_args.args[0] == CLIENT_ID
    assert mock_list.await_args.kwargs["session"] is session


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl02_get_otro_tenant_not_found():
    session = AsyncMock()
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(NotFoundError):
                await svc.get_codigo_secuencia_servicio(OTHER_CLIENT, SEQ_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl03_list_con_page_envelope():
    session = AsyncMock()
    rows = [_base_row(secuencia_id=uuid4(), sequence_key="org_sucursal") for _ in range(3)]
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.list_codigo_secuencias",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            with _patch_codigos_activos("ORG"):
                result = await svc.list_codigo_secuencias_servicio(
                    CLIENT_ID,
                    pagination=ErpPaginationParams(page=1, limit=2),
                )
    assert isinstance(result, PaginatedCodigoSecuenciaResponse)
    assert result.total == 3
    assert len(result.items) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl04_modulo_codigo_page_totales():
    session = AsyncMock()
    rows = [
        _base_row(secuencia_id=uuid4(), sequence_key="org_sucursal"),
        _base_row(secuencia_id=uuid4(), sequence_key="inv_categoria_producto"),
    ]
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.list_codigo_secuencias",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            with _patch_codigos_activos("ORG", "INV"):
                result = await svc.list_codigo_secuencias_servicio(
                    CLIENT_ID,
                    modulo_codigo="ORG",
                    pagination=ErpPaginationParams(page=1, limit=50),
                )
    assert isinstance(result, PaginatedCodigoSecuenciaResponse)
    assert result.total == 1
    assert result.items[0].modulo_codigo == "ORG"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl04b_saas_oculta_modulos_no_contratados():
    session = AsyncMock()
    rows = [
        _base_row(secuencia_id=uuid4(), sequence_key="org_sucursal"),
        _base_row(secuencia_id=uuid4(), sequence_key="inv_categoria_producto"),
    ]
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.list_codigo_secuencias",
            new_callable=AsyncMock,
            return_value=rows,
        ):
            with _patch_codigos_activos("ORG"):
                result = await svc.list_codigo_secuencias_servicio(CLIENT_ID)
    assert len(result) == 1
    assert result[0].modulo_codigo == "ORG"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tl05_sort_by_invalido():
    session = AsyncMock()
    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.list_codigo_secuencias",
            new_callable=AsyncMock,
            return_value=[_base_row()],
        ):
            with _patch_codigos_activos("ORG"):
                with pytest.raises(CustomException) as exc:
                    await svc.list_codigo_secuencias_servicio(
                        CLIENT_ID,
                        sort=ErpSortParams(sort_by="no_existe", sort_dir="asc"),
                    )
    assert exc.value.internal_code == "INVALID_SORT_COLUMN"


# ----- Mutación (T-M*) -----


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tm01_patch_ok_audit():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row()
    updated = _base_row(prefijo="ABC", usuario_actualizacion_id=USER_ID)

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.update_codigo_secuencia_config",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                result = await svc.update_codigo_secuencia_servicio(
                    CLIENT_ID,
                    SEQ_ID,
                    CodigoSecuenciaUpdate(prefijo="abc"),
                    usuario_id=USER_ID,
                )
    mock_upd.assert_awaited_once()
    assert mock_upd.await_args.kwargs["usuario_actualizacion_id"] == USER_ID
    assert mock_upd.await_args.args[2]["prefijo"] == "ABC"
    assert result.prefijo == "ABC"
    session.begin.assert_called_once()


@pytest.mark.unit
def test_tm02_body_ultimo_numero_forbid():
    with pytest.raises(PydanticValidationError):
        CodigoSecuenciaUpdate.model_validate({"ultimo_numero": 9})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tm03_desactivar():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row(es_activo=True)
    updated = _base_row(es_activo=False)

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.set_codigo_secuencia_activo",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_set:
                result = await svc.desactivar_codigo_secuencia_servicio(
                    CLIENT_ID, SEQ_ID, usuario_id=USER_ID
                )
    mock_set.assert_awaited_once()
    assert mock_set.await_args.args[2] is False
    assert result.es_activo is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tm04_reactivar():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row(es_activo=False)
    updated = _base_row(es_activo=True)

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.set_codigo_secuencia_activo",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_set:
                result = await svc.reactivar_codigo_secuencia_servicio(
                    CLIENT_ID, SEQ_ID, usuario_id=USER_ID
                )
    assert mock_set.await_args.args[2] is True
    assert result.es_activo is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tm05_idempotencia_desactivar():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    row = _base_row(es_activo=False)

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.set_codigo_secuencia_activo",
                new_callable=AsyncMock,
            ) as mock_set:
                result = await svc.desactivar_codigo_secuencia_servicio(
                    CLIENT_ID, SEQ_ID, usuario_id=USER_ID
                )
    mock_set.assert_not_awaited()
    assert result.es_activo is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tm06_uow_get_connection_for_tenant():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ) as mock_conn:
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=_base_row(),
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.update_codigo_secuencia_config",
                new_callable=AsyncMock,
                return_value=_base_row(prefijo="ZZZ"),
            ):
                await svc.update_codigo_secuencia_servicio(
                    CLIENT_ID,
                    SEQ_ID,
                    CodigoSecuenciaUpdate(prefijo="zzz"),
                    usuario_id=USER_ID,
                )
    mock_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)


@pytest.mark.unit
def test_tm07_no_format_collision_and_queries_whitelist():
    from app.infrastructure.database.queries.cfg import codigo_secuencia_queries as q

    assert "CFG_FORMAT_COLLISION" not in open(
        "app/modules/cfg/application/services/codigo_secuencia_admin_servicio.py",
        encoding="utf-8",
    ).read()
    assert "ultimo_numero" not in q._CONFIG_UPDATE_FIELDS
    assert "generation_policy" in q._CONFIG_UPDATE_FIELDS
    assert "update_ultimo_numero" not in open(
        "app/infrastructure/database/queries/cfg/codigo_secuencia_queries.py",
        encoding="utf-8",
    ).read()


# ----- Preview (T-P*) -----


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tp01_to_tp06_preview():
    session = AsyncMock()
    row = _base_row(es_activo=False, ultimo_numero=41)
    preview = PreviewResult(code="SUC042", sequence_key="org_sucursal")

    with patch(
        "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_connection_for_tenant",
        return_value=_session_cm(session),
    ):
        with patch(
            "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.get_codigo_secuencia_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.CodigoGeneracionGateway.preview",
                new_callable=AsyncMock,
                return_value=preview,
            ) as mock_preview:
                with patch(
                    "app.modules.cfg.application.services.codigo_secuencia_admin_servicio.CodigoGeneracionGateway.allocate",
                    new_callable=AsyncMock,
                ) as mock_allocate:
                    result = await svc.preview_codigo_secuencia_servicio(
                        CLIENT_ID, SEQ_ID
                    )

    mock_preview.assert_awaited_once()
    mock_allocate.assert_not_awaited()
    ctx = mock_preview.await_args.args[1]
    assert ctx.empresa_id == EMPRESA_ID
    assert result.codigo_estimado == "SUC042"
    assert result.consume_contador is False
    assert result.ultimo_numero_actual == 41
    assert result.es_activo is False
    assert result.disclaimer
