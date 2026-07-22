"""Seed de secuencias para onboarding tenant (INC-01 / INC-02).

F17C/F17D — `SequenceCatalog` es la única fuente de verdad. Aquí **no** se re-declara
ningún metadato (prefijo, padding, separador, scope) ni existe una lista manual de keys.

Criterio F17D (Opción A): el onboarding siembra automáticamente **todas** las secuencias
de store CFG cuyo `scope_fingerprint` queda completamente determinado en el onboarding
—es decir, scope TENANT o EMPRESA (existe cliente + empresa sede)—. Las secuencias de
scope ALMACEN y PUNTO_VENTA se crean lazy vía `AllocationCoordinator.ensure_row()` cuando
existe la entidad (almacén / punto de venta) que su fingerprint requiere. Las 2 fiscales
(store FISCAL) nunca van a `cfg_codigo_secuencia`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.codigo.enums import CodePolicy, ScopeType, StoreType
from app.core.codigo.platform_initial_policy import platform_initial_generation_policy
from app.core.codigo.sequence_catalog import CATALOG_VERSION, SequenceCatalog
from app.core.codigo.sequence_definition import SequenceDefinition

__all__ = [
    "CATALOG_VERSION",
    "ONBOARDING_RESOLVABLE_SCOPES",
    "OnboardingSequenceSeed",
    "ONBOARDING_SEQUENCE_SEEDS",
    "EAGER_SEQUENCE_KEYS",
    "SECUENCIAS_CODIGO",
]

# Scopes cuyo fingerprint se resuelve por completo durante el onboarding: existe el
# cliente (TENANT) y la empresa sede (EMPRESA). ALMACEN / PUNTO_VENTA requieren una
# entidad que aún no existe → quedan para lazy creation, no para el seed.
ONBOARDING_RESOLVABLE_SCOPES: frozenset[ScopeType] = frozenset(
    (ScopeType.TENANT, ScopeType.EMPRESA)
)


@dataclass(frozen=True, slots=True)
class OnboardingSequenceSeed:
    sequence_key: str
    scope_type: ScopeType
    prefijo: str
    longitud_numero: int
    separador: str
    generation_policy: CodePolicy
    ultimo_numero: int = 0
    numero_inicial: int = 1

    @classmethod
    def from_definition(cls, defn: SequenceDefinition) -> "OnboardingSequenceSeed":
        """Deriva el seed de onboarding desde el contrato del SequenceCatalog.

        Prefijo/padding/separador/scope vienen del catálogo.
        ``generation_policy`` inicial es decisión de provisioning Platform
        (ver ``platform_initial_generation_policy``), no ``defn.policy`` F15A.
        """
        # BR-BOOT-04: EMP001 bootstrap consume correlativo 1 antes del seed cfg TENANT.
        ultimo_numero = 1 if defn.sequence_key == "org_empresa" else 0
        return cls(
            sequence_key=defn.sequence_key,
            scope_type=defn.scope_type,
            prefijo=defn.default_prefix,
            longitud_numero=defn.default_padding,
            separador=defn.default_separator,
            generation_policy=platform_initial_generation_policy(),
            ultimo_numero=ultimo_numero,
            numero_inicial=defn.numero_inicial,
        )


def _onboarding_definitions() -> tuple[SequenceDefinition, ...]:
    """Todas las entradas CFG del catálogo con scope resoluble en onboarding.

    Sin lista manual: la selección se deriva del catálogo (store CFG + scope
    TENANT/EMPRESA). Excluye automáticamente FISCAL y ALMACEN/PUNTO_VENTA.
    """
    return tuple(
        defn
        for defn in SequenceCatalog.all_definitions()
        if defn.store_type == StoreType.CFG
        and defn.scope_type in ONBOARDING_RESOLVABLE_SCOPES
    )


ONBOARDING_SEQUENCE_SEEDS: tuple[OnboardingSequenceSeed, ...] = tuple(
    OnboardingSequenceSeed.from_definition(defn) for defn in _onboarding_definitions()
)

# Vista derivada (no es una lista mantenida a mano): keys sembradas en onboarding.
EAGER_SEQUENCE_KEYS: tuple[str, ...] = tuple(
    seed.sequence_key for seed in ONBOARDING_SEQUENCE_SEEDS
)

# Compatibilidad tests legacy: (sequence_key, prefijo, longitud, separador, ultimo)
SECUENCIAS_CODIGO: list[tuple[str, str, int, str, int]] = [
    (s.sequence_key, s.prefijo, s.longitud_numero, s.separador, s.ultimo_numero)
    for s in ONBOARDING_SEQUENCE_SEEDS
]
