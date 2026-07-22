"""F2A — estorno y aprobación: sin generadores timestamp; allocate inv_movimiento."""
from __future__ import annotations

import pytest

from app.modules.inv.application.services import inventario_fisico_aprobacion_service
import app.modules.inv.application.services.inv_estorno_proceso as estorno_mod
import app.modules.inv.application.services.movimiento_proceso_service as proceso_mod


@pytest.mark.unit
def test_gen_numero_movimiento_estorno_removed():
    assert not hasattr(estorno_mod, "gen_numero_movimiento_estorno")


@pytest.mark.unit
def test_gen_numero_movimiento_aprobacion_removed():
    assert not hasattr(inventario_fisico_aprobacion_service, "_gen_numero_movimiento")


@pytest.mark.unit
def test_estorno_service_uses_inv_codigo_generation_service():
    assert hasattr(proceso_mod, "InvCodigoGenerationService")


@pytest.mark.unit
def test_aprobacion_service_uses_inv_codigo_generation_service():
    assert hasattr(inventario_fisico_aprobacion_service, "InvCodigoGenerationService")
    assert inventario_fisico_aprobacion_service._SEQUENCE_KEY_MOVIMIENTO == "inv_movimiento"
