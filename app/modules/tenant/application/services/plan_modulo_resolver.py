"""
Resuelve módulos comerciales activables según plan_suscripcion del tenant.

Trial congelado: ORG + SYS_ADMIN + INV (D1).
"""
from __future__ import annotations

import logging
from typing import List, Optional

from app.modules.tenant.application.services.owner_sync_constants import TRIAL_MODULES

logger = logging.getLogger(__name__)

_KNOWN_PLANS = frozenset({"trial", "basico", "profesional", "enterprise"})


def resolve_modulos_for_plan(plan_suscripcion: Optional[str] = None) -> List[str]:
    """
    Devuelve códigos de módulo a activar en onboarding según plan.

    v1.0: todos los planes conocidos usan TRIAL_MODULES hasta definir matrices comerciales.
    """
    plan = (plan_suscripcion or "trial").strip().lower()
    if plan not in _KNOWN_PLANS:
        logger.warning(
            "Plan desconocido '%s'; usando módulos trial %s",
            plan_suscripcion,
            list(TRIAL_MODULES),
        )
        return list(TRIAL_MODULES)
    return list(TRIAL_MODULES)
