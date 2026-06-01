"""Reglas puras de detección para reparación legacy RBAC (sin imports de app modules)."""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple
from uuid import UUID

REQUIRED_MODULOS: frozenset[str] = frozenset({"ORG", "SYS_ADMIN"})
MIN_ADMIN_ROL_PERMISO_HEALTHY = 5
# Tenants con bundle legacy completo (S040/R010); no reparar aunque falte core en EXISTS.
LEGACY_COMPLETE_ROL_PERMISO_THRESHOLD = 40
ADMIN_ROL_CODIGO = "ADMIN_TENANT"


def evaluate_repair_need(
    *,
    cliente_modulo_count: int,
    modulos_codigos: Sequence[str],
    admin_rol_id: Optional[UUID],
    rol_permiso_admin_count: int,
    has_core_app_acceder: bool,
) -> Tuple[bool, List[str], bool, Optional[str]]:
    mod_set = {c.strip().upper() for c in modulos_codigos if c}
    reasons: List[str] = []

    if admin_rol_id is None:
        return False, [], True, "ADMIN_TENANT_MISSING"

    if (
        REQUIRED_MODULOS <= mod_set
        and rol_permiso_admin_count >= LEGACY_COMPLETE_ROL_PERMISO_THRESHOLD
    ):
        return False, [], False, None

    if cliente_modulo_count == 0:
        reasons.append("NO_CLIENTE_MODULO")
    else:
        missing_mod = REQUIRED_MODULOS - mod_set
        if missing_mod:
            reasons.append(f"MISSING_MODULOS:{','.join(sorted(missing_mod))}")

    if rol_permiso_admin_count == 0:
        reasons.append("NO_ROL_PERMISO_ADMIN")
    elif not has_core_app_acceder:
        reasons.append("MISSING_CORE_APP_ACCEDER")
    elif rol_permiso_admin_count < MIN_ADMIN_ROL_PERMISO_HEALTHY:
        reasons.append("LOW_ROL_PERMISO_ADMIN_COUNT")

    return len(reasons) > 0, reasons, False, None
