"""Perfiles seed catálogos Dedicated — PR-F4-06 / ADR-011 / BL-F4 §12 S6."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from app.core.exceptions import ValidationError
from app.infrastructure.provisioning.script_manifest import (
    compute_file_sha256,
    get_bootstrap_v2_root,
)
from app.modules.tenant.application.services.plan_modulo_resolver import (
    resolve_modulos_for_plan,
)

KNOWN_PLANS = frozenset({"trial", "basico", "profesional", "enterprise"})

# Módulos con scripts S040–S066 (excl. S067 legacy vacío).
ALL_CATALOG_MODULE_CODES: tuple[str, ...] = (
    "ORG",
    "INV",
    "WMS",
    "QMS",
    "PUR",
    "LOG",
    "MFG",
    "MRP",
    "MPS",
    "MNT",
    "SLS",
    "CRM",
    "INV_BILL",
    "POS",
    "HCM",
    "FIN",
    "BDG",
    "CST",
    "PM",
    "SVC",
    "TKT",
    "BI",
    "DMS",
    "WFL",
    "AUD",
)

_MODULE_TO_SCRIPT_CODES: dict[str, tuple[str, ...]] = {
    "ORG": ("catalog_s040",),
    "INV": ("catalog_s041", "catalog_s042"),
    "WMS": ("catalog_s043",),
    "QMS": ("catalog_s044",),
    "PUR": ("catalog_s045",),
    "LOG": ("catalog_s046", "catalog_s066"),
    "MFG": ("catalog_s047",),
    "MRP": ("catalog_s048",),
    "MPS": ("catalog_s049",),
    "MNT": ("catalog_s050",),
    "SLS": ("catalog_s051",),
    "CRM": ("catalog_s052",),
    "INV_BILL": ("catalog_s053",),
    "POS": ("catalog_s054",),
    "HCM": ("catalog_s055",),
    "FIN": ("catalog_s056", "catalog_s066"),
    "BDG": ("catalog_s057",),
    "CST": ("catalog_s058",),
    "PM": ("catalog_s059",),
    "SVC": ("catalog_s060",),
    "TKT": ("catalog_s061",),
    "BI": ("catalog_s062",),
    "DMS": ("catalog_s063",),
    "WFL": ("catalog_s064",),
    "AUD": ("catalog_s065",),
}

_CATALOG_CHECKSUMS: dict[str, str] = {
    "02_catalog/S010__seed_modulo_menu_completo.sql": (
        "a60ab6d4b5726a39c3c9197a637256e28d2afae00218aba0cfc5c12d45e96aba"
    ),
    "02_catalog/S020__seed_admin_menu.sql": (
        "99e9eaf9cea80d03acb098f291aa781aed9a747183335acbaf93d7482f1dbe7d"
    ),
    "02_catalog/S030__seed_permisos_core.sql": (
        "08c37b733373c74e1ad78397ad25e591dfc535ec9476fbf8d3ed9491fcf09ef3"
    ),
    "02_catalog/permisos_rbac/S040__permisos_rbac_org.sql": (
        "39476c80e783efb7c4d5d3dd7a2645e1c59add4516559690226b9968befb0d44"
    ),
    "02_catalog/permisos_rbac/S041__permisos_rbac_inv-fase4.sql": (
        "de97d838d83a1d8dccb886dec71668d80c0d277b92846745d369dd379f463b39"
    ),
    "02_catalog/permisos_rbac/S042__permisos_rbac_inv-lifecycle.sql": (
        "8e9893f178986a752f748325a0271ff096219a492a7349b37c971efa2b06470f"
    ),
    "02_catalog/permisos_rbac/S043__permisos_rbac_wms.sql": (
        "735cf8f357dd45ecc32ebe4980bb3461715fb73e51720a0ae1f43022dee1f23a"
    ),
    "02_catalog/permisos_rbac/S044__permisos_rbac_qms.sql": (
        "3bb883f4e70870f243dbda8728b543a668e2384b2857c41e3e1665823e7bf0ec"
    ),
    "02_catalog/permisos_rbac/S045__permisos_rbac_pur.sql": (
        "53d817db6c37510441baf437cb30311a1f5bf5a7c2ed461c482bc025a2e62872"
    ),
    "02_catalog/permisos_rbac/S046__permisos_rbac_log.sql": (
        "fb1a003297ddcee5f27221905f532c67bd00029ebe1e8b4dd1b53a046fa4cbf3"
    ),
    "02_catalog/permisos_rbac/S047__permisos_rbac_mfg.sql": (
        "61a2c122caddc155b18f1f810b295df33925d9230d88587bad91d938e36852ce"
    ),
    "02_catalog/permisos_rbac/S048__permisos_rbac_mrp.sql": (
        "02ffd92f3ea4bfc17dcbaa1e2d6f11eea588b360e62ea2d107bfac2b112a51ba"
    ),
    "02_catalog/permisos_rbac/S049__permisos_rbac_mps.sql": (
        "b6eab19b2c75f54b823bf05ab4ab66cac858090c86f83002c3e710226b2cbae6"
    ),
    "02_catalog/permisos_rbac/S050__permisos_rbac_mnt.sql": (
        "182e90a5d17435878b2028db834083317fc04779f1ab5a4395d7c8a566a62d44"
    ),
    "02_catalog/permisos_rbac/S051__permisos_rbac_sls.sql": (
        "2ef23b87f0d58ddc0df5e67b90b22b8fe712981e8ce43ec3a67b52f5a3b3f7d9"
    ),
    "02_catalog/permisos_rbac/S052__permisos_rbac_crm.sql": (
        "73ad008650d05c0078da79a1b748382e593343868b7c8e26dcb0c31a531aa143"
    ),
    "02_catalog/permisos_rbac/S053__permisos_rbac_inv-bill.sql": (
        "73e2f051d8f79cfb164b2fa58e7337d229fe5eb44f3ede67ea3bc959ee704bb7"
    ),
    "02_catalog/permisos_rbac/S054__permisos_rbac_pos.sql": (
        "b36d35b662ee087ea26a4a92013e839a42de4f075f88c4f40f4c0e20fe604e67"
    ),
    "02_catalog/permisos_rbac/S055__permisos_rbac_hcm.sql": (
        "b8e784e262d00bc3b23d986bfd003215cbdb3c2d1b528fc43fb39e5bf75ea7b4"
    ),
    "02_catalog/permisos_rbac/S056__permisos_rbac_fin.sql": (
        "8fb3585768087c962265339238de779ca7b8a5dc22573126cf7fd455d542ad9e"
    ),
    "02_catalog/permisos_rbac/S057__permisos_rbac_bdg.sql": (
        "d86a3aeea6cfb78d4094902c002588bdb95495f8d7c07b0cd878783dd6d26358"
    ),
    "02_catalog/permisos_rbac/S058__permisos_rbac_cst.sql": (
        "b803326f8b730eab8bd4316ca01490da40daa63741d1c97deac9f8daa4a068ef"
    ),
    "02_catalog/permisos_rbac/S059__permisos_rbac_pm.sql": (
        "e2af23d0190602a484ef08eb409b17de72f054f4868ba6253c20922bacdc17c7"
    ),
    "02_catalog/permisos_rbac/S060__permisos_rbac_svc.sql": (
        "abbe3ec923ab3329515b1af98ef301cf8fd4e54248ad44d8e4e3ffe27d1034c1"
    ),
    "02_catalog/permisos_rbac/S061__permisos_rbac_tkt.sql": (
        "b2e8a117c5e77e6bd1720b954fbd0318aa09b95de47faaf3f496e02ce8e2df4e"
    ),
    "02_catalog/permisos_rbac/S062__permisos_rbac_bi.sql": (
        "93777357992c8da2778a701afbc8f8d3465e6ec63e62fd92ec698cd6e3f8aa03"
    ),
    "02_catalog/permisos_rbac/S063__permisos_rbac_dms.sql": (
        "62db27c9f4252ee2046f6abc272b1a7d9ac2b71e74e6e923cc084203da4ed8f2"
    ),
    "02_catalog/permisos_rbac/S064__permisos_rbac_wfl.sql": (
        "37ab8603a31176e9d96d9c776eea6dbf75cf19fbef20d2b4bbe1c18e79af6f78"
    ),
    "02_catalog/permisos_rbac/S065__permisos_rbac_aud.sql": (
        "23a3538f6dae80185ea9f3602a4eae61b2a25d1b69b0b38390f96aaedc2d7ac8"
    ),
    "02_catalog/permisos_rbac/S066__permisos_rbac_fase4-candidatos.sql": (
        "6fc863d553a2873bfce283def456b3c6b3bd87b1e8256047963d61f4ac54eeac"
    ),
}


@dataclass(frozen=True, slots=True)
class CatalogSeedScriptEntry:
    """Script bootstrap_v2 02_catalog para perfil Dedicated S6."""

    script_code: str
    relative_path: str
    execution_order: int
    expected_sha256: str
    module_code: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogSeedProfile:
    """Perfil resuelto de scripts + verificaciones mínimas."""

    profile_code: str
    plan_suscripcion: str
    module_codes: tuple[str, ...]
    scripts: tuple[CatalogSeedScriptEntry, ...]
    row_expectations: tuple[tuple[str, int], ...]


def _build_catalog_registry() -> dict[str, CatalogSeedScriptEntry]:
    raw_defs: tuple[tuple[str, str, int, str | None], ...] = (
        ("catalog_s010", "02_catalog/S010__seed_modulo_menu_completo.sql", 10, None),
        ("catalog_s020", "02_catalog/S020__seed_admin_menu.sql", 20, None),
        ("catalog_s030", "02_catalog/S030__seed_permisos_core.sql", 30, None),
        ("catalog_s040", "02_catalog/permisos_rbac/S040__permisos_rbac_org.sql", 40, "ORG"),
        ("catalog_s041", "02_catalog/permisos_rbac/S041__permisos_rbac_inv-fase4.sql", 41, "INV"),
        ("catalog_s042", "02_catalog/permisos_rbac/S042__permisos_rbac_inv-lifecycle.sql", 42, "INV"),
        ("catalog_s043", "02_catalog/permisos_rbac/S043__permisos_rbac_wms.sql", 43, "WMS"),
        ("catalog_s044", "02_catalog/permisos_rbac/S044__permisos_rbac_qms.sql", 44, "QMS"),
        ("catalog_s045", "02_catalog/permisos_rbac/S045__permisos_rbac_pur.sql", 45, "PUR"),
        ("catalog_s046", "02_catalog/permisos_rbac/S046__permisos_rbac_log.sql", 46, "LOG"),
        ("catalog_s047", "02_catalog/permisos_rbac/S047__permisos_rbac_mfg.sql", 47, "MFG"),
        ("catalog_s048", "02_catalog/permisos_rbac/S048__permisos_rbac_mrp.sql", 48, "MRP"),
        ("catalog_s049", "02_catalog/permisos_rbac/S049__permisos_rbac_mps.sql", 49, "MPS"),
        ("catalog_s050", "02_catalog/permisos_rbac/S050__permisos_rbac_mnt.sql", 50, "MNT"),
        ("catalog_s051", "02_catalog/permisos_rbac/S051__permisos_rbac_sls.sql", 51, "SLS"),
        ("catalog_s052", "02_catalog/permisos_rbac/S052__permisos_rbac_crm.sql", 52, "CRM"),
        ("catalog_s053", "02_catalog/permisos_rbac/S053__permisos_rbac_inv-bill.sql", 53, "INV_BILL"),
        ("catalog_s054", "02_catalog/permisos_rbac/S054__permisos_rbac_pos.sql", 54, "POS"),
        ("catalog_s055", "02_catalog/permisos_rbac/S055__permisos_rbac_hcm.sql", 55, "HCM"),
        ("catalog_s056", "02_catalog/permisos_rbac/S056__permisos_rbac_fin.sql", 56, "FIN"),
        ("catalog_s057", "02_catalog/permisos_rbac/S057__permisos_rbac_bdg.sql", 57, "BDG"),
        ("catalog_s058", "02_catalog/permisos_rbac/S058__permisos_rbac_cst.sql", 58, "CST"),
        ("catalog_s059", "02_catalog/permisos_rbac/S059__permisos_rbac_pm.sql", 59, "PM"),
        ("catalog_s060", "02_catalog/permisos_rbac/S060__permisos_rbac_svc.sql", 60, "SVC"),
        ("catalog_s061", "02_catalog/permisos_rbac/S061__permisos_rbac_tkt.sql", 61, "TKT"),
        ("catalog_s062", "02_catalog/permisos_rbac/S062__permisos_rbac_bi.sql", 62, "BI"),
        ("catalog_s063", "02_catalog/permisos_rbac/S063__permisos_rbac_dms.sql", 63, "DMS"),
        ("catalog_s064", "02_catalog/permisos_rbac/S064__permisos_rbac_wfl.sql", 64, "WFL"),
        ("catalog_s065", "02_catalog/permisos_rbac/S065__permisos_rbac_aud.sql", 65, "AUD"),
        (
            "catalog_s066",
            "02_catalog/permisos_rbac/S066__permisos_rbac_fase4-candidatos.sql",
            66,
            None,
        ),
    )
    registry: dict[str, CatalogSeedScriptEntry] = {}
    for script_code, relative_path, order, module_code in raw_defs:
        expected = _CATALOG_CHECKSUMS.get(relative_path)
        if not expected:
            raise ValidationError(
                detail=f"Checksum catálogo no registrado: {relative_path}.",
                internal_code="CATALOG_PROFILE_REGISTRY_INCOMPLETE",
            )
        registry[script_code] = CatalogSeedScriptEntry(
            script_code=script_code,
            relative_path=relative_path,
            execution_order=order,
            expected_sha256=expected,
            module_code=module_code,
        )
    return registry


CATALOG_SCRIPT_REGISTRY: dict[str, CatalogSeedScriptEntry] = _build_catalog_registry()

# ADR-011 — tablas Product Reference en V010 (verificación post-seed).
CAT_REFERENCE_TABLES: tuple[str, ...] = (
    "cat_moneda",
    "cat_pais",
    "cat_departamento",
    "cat_provincia",
    "cat_distrito",
)


def normalize_plan_suscripcion(plan_suscripcion: str | None) -> str:
    plan = (plan_suscripcion or "trial").strip().lower()
    if plan not in KNOWN_PLANS:
        return "trial"
    return plan


def resolve_module_codes_for_plan(plan_suscripcion: str | None) -> tuple[str, ...]:
    plan = normalize_plan_suscripcion(plan_suscripcion)
    if plan == "enterprise":
        return ALL_CATALOG_MODULE_CODES
    modules = resolve_modulos_for_plan(plan)
    return tuple(dict.fromkeys(modules))


def _script_codes_for_modules(module_codes: Iterable[str]) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for module_code in module_codes:
        for script_code in _MODULE_TO_SCRIPT_CODES.get(module_code, ()):
            if script_code not in seen:
                selected.append(script_code)
                seen.add(script_code)
    return selected


def resolve_catalog_seed_profile(
    plan_suscripcion: str | None,
) -> CatalogSeedProfile:
    plan = normalize_plan_suscripcion(plan_suscripcion)
    module_codes = resolve_module_codes_for_plan(plan)
    script_codes = ["catalog_s010", "catalog_s020", "catalog_s030"]
    script_codes.extend(_script_codes_for_modules(module_codes))
    if "LOG" in module_codes or "FIN" in module_codes:
        if "catalog_s066" not in script_codes:
            script_codes.append("catalog_s066")

    scripts: list[CatalogSeedScriptEntry] = []
    for code in script_codes:
        entry = CATALOG_SCRIPT_REGISTRY.get(code)
        if entry is None:
            raise ValidationError(
                detail=f"Script catálogo no registrado: {code}.",
                internal_code="CATALOG_SCRIPT_NOT_REGISTERED",
            )
        scripts.append(entry)

    scripts.sort(key=lambda item: item.execution_order)
    profile_code = f"dedicated_catalog_{plan}_v1"
    row_expectations = _row_expectations_for_plan(plan, module_codes)

    return CatalogSeedProfile(
        profile_code=profile_code,
        plan_suscripcion=plan,
        module_codes=module_codes,
        scripts=tuple(scripts),
        row_expectations=row_expectations,
    )


def _row_expectations_for_plan(
    plan: str,
    module_codes: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    expectations: list[tuple[str, int]] = [
        ("modulo", 27),
        ("permiso", 1),
    ]
    if "ORG" in module_codes:
        expectations.append(("permiso", 5))
    for cat_table in CAT_REFERENCE_TABLES:
        expectations.append((cat_table, 0))
    if plan == "enterprise":
        expectations.append(("permiso", 50))
    return tuple(expectations)


def discover_catalog_scripts(
    profile: CatalogSeedProfile,
    *,
    bootstrap_root: Path | None = None,
) -> list[tuple[CatalogSeedScriptEntry, Path, str]]:
    root = bootstrap_root or get_bootstrap_v2_root()
    if not root.is_dir():
        raise ValidationError(
            detail=f"Directorio bootstrap_v2 no encontrado: {root}.",
            internal_code="BOOTSTRAP_ROOT_NOT_FOUND",
        )

    discovered: list[tuple[CatalogSeedScriptEntry, Path, str]] = []
    for entry in profile.scripts:
        script_path = root / entry.relative_path
        if not script_path.is_file():
            raise ValidationError(
                detail=f"Script catálogo no encontrado: {entry.relative_path}.",
                internal_code="CATALOG_SCRIPT_NOT_FOUND",
            )
        if script_path.stat().st_size == 0:
            raise ValidationError(
                detail=f"Script catálogo vacío: {entry.relative_path}.",
                internal_code="CATALOG_SCRIPT_EMPTY",
            )
        checksum = compute_file_sha256(script_path)
        discovered.append((entry, script_path, checksum))
    return discovered


def validate_catalog_profile_integrity(
    profile: CatalogSeedProfile,
    *,
    bootstrap_root: Path | None = None,
) -> None:
    orders = [entry.execution_order for entry in profile.scripts]
    if orders != sorted(orders):
        raise ValidationError(
            detail="Orden de ejecución catálogo inválido en perfil.",
            internal_code="CATALOG_PROFILE_ORDER_INVALID",
        )

    discovered = discover_catalog_scripts(profile, bootstrap_root=bootstrap_root)
    for entry, _path, checksum in discovered:
        if checksum != entry.expected_sha256:
            raise ValidationError(
                detail=(
                    f"Checksum catálogo divergente para {entry.relative_path} "
                    f"(perfil {profile.profile_code})."
                ),
                internal_code="CATALOG_PROFILE_INTEGRITY_FAILED",
            )


def dedupe_row_expectations(
    expectations: Sequence[tuple[str, int]],
) -> tuple[tuple[str, int], ...]:
    merged: dict[str, int] = {}
    for table_name, min_rows in expectations:
        merged[table_name] = max(merged.get(table_name, 0), min_rows)
    return tuple((table, merged[table]) for table in sorted(merged))


__all__ = [
    "ALL_CATALOG_MODULE_CODES",
    "CAT_REFERENCE_TABLES",
    "CATALOG_SCRIPT_REGISTRY",
    "CatalogSeedProfile",
    "CatalogSeedScriptEntry",
    "dedupe_row_expectations",
    "discover_catalog_scripts",
    "normalize_plan_suscripcion",
    "resolve_catalog_seed_profile",
    "resolve_module_codes_for_plan",
    "validate_catalog_profile_integrity",
]
