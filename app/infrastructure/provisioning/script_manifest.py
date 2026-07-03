"""Manifiesto bootstrap Dedicated — PR-F4-05 / PR-F4-05b (DTSP) / BL-F4 §11 S4–S5."""

from __future__ import annotations



import hashlib

from dataclasses import dataclass

from pathlib import Path

from typing import Sequence



from app.core.exceptions import ValidationError



BOOTSTRAP_V2_ROOT = Path(__file__).resolve().parents[2] / "bootstrap_v2"



# Checksums congelados — recalcular solo si cambia contenido bootstrap_v2 (prohibido F4-05b).

_V010_ERP_SHA256 = (

    "78733886529a88af139bde57af5e44a663d417cb5cab0835f7a45b87adda1237"

)

_V020_DTSP_SHA256 = (

    "adb0708438113220cfd587bf3624c760a9022bf64e4a7a87500553cde4c81583"

)

_V010_RBAC_DEDICATED_SHA256 = (

    "7b613facaf14ded29dd3792083bf50a065a51b207d36e5bd2a4b5ccf1a497c47"

)

_V030_AUTH_AUDIT_DEDICATED_SHA256 = (

    "ad1fb3c6c28e26c5766282c09bbd498ce9b774e20a26ab07d350a7a2f91612a8"

)



# Tablas mínimas DTSP — verificación post-bootstrap (PR-F4-05b).

DTSP_REQUIRED_TABLES: frozenset[str] = frozenset(

    {

        "modulo",

        "modulo_seccion",

        "modulo_menu",

        "permiso",

        "rol",

        "usuario",

        "usuario_rol",

        "cliente_modulo",

        "rol_menu_permiso",

    }

)



DEDICATED_RBAC_GRANTS_TABLE = "rol_permiso"



# Tablas runtime obligatorias en Data Plane — gate READY post-bootstrap (F12-G3).

DEDICATED_RUNTIME_EXTRA_TABLES: frozenset[str] = frozenset(

    {

        "auth_audit_log",

        "cfg_codigo_secuencia",

        "org_empresa",

    }

)



DEDICATED_RUNTIME_REQUIRED_TABLES: frozenset[str] = frozenset(

    DTSP_REQUIRED_TABLES

    | {DEDICATED_RBAC_GRANTS_TABLE}

    | DEDICATED_RUNTIME_EXTRA_TABLES

)





@dataclass(frozen=True, slots=True)

class BootstrapScriptManifestEntry:

    """Entrada ordenada del manifiesto dedicated schema."""



    script_code: str

    relative_path: str

    step_code: str

    execution_order: int

    expected_sha256: str





@dataclass(frozen=True, slots=True)

class BootstrapScriptManifest:

    """Perfil bootstrap schema dedicated Data Plane."""



    version: str

    profile: str

    entries: tuple[BootstrapScriptManifestEntry, ...]





DEDICATED_SCHEMA_MANIFEST_V1 = BootstrapScriptManifest(

    version="1.0.0",

    profile="dedicated_schema_v1",

    entries=(

        BootstrapScriptManifestEntry(

            script_code="apply_schema_erp_v010",

            relative_path="01_schema/V010__tablas_bd_erp_completo.sql",

            step_code="apply_schema_erp",

            execution_order=1,

            expected_sha256=_V010_ERP_SHA256,

        ),

        BootstrapScriptManifestEntry(

            script_code="apply_schema_rbac_v010",

            relative_path="05_dedicated/V010__rbac_tablas_dedicated.sql",

            step_code="apply_schema_rbac",

            execution_order=2,

            expected_sha256=_V010_RBAC_DEDICATED_SHA256,

        ),

    ),

)



DEDICATED_SCHEMA_MANIFEST_V2 = BootstrapScriptManifest(

    version="2.1.0",

    profile="dedicated_schema_v2",

    entries=(

        BootstrapScriptManifestEntry(

            script_code="apply_schema_erp_v010",

            relative_path="01_schema/V010__tablas_bd_erp_completo.sql",

            step_code="apply_schema_erp",

            execution_order=1,

            expected_sha256=_V010_ERP_SHA256,

        ),

        BootstrapScriptManifestEntry(

            script_code="apply_schema_tenant_store_v020",

            relative_path="05_dedicated/V020__tenant_identity_rbac_store.sql",

            step_code="apply_schema_rbac",

            execution_order=2,

            expected_sha256=_V020_DTSP_SHA256,

        ),

        BootstrapScriptManifestEntry(

            script_code="apply_schema_rbac_v010",

            relative_path="05_dedicated/V010__rbac_tablas_dedicated.sql",

            step_code="apply_schema_rbac",

            execution_order=3,

            expected_sha256=_V010_RBAC_DEDICATED_SHA256,

        ),

        BootstrapScriptManifestEntry(

            script_code="apply_schema_auth_audit_v030",

            relative_path="05_dedicated/V030__auth_audit_log_dedicated.sql",

            step_code="apply_schema_rbac",

            execution_order=4,

            expected_sha256=_V030_AUTH_AUDIT_DEDICATED_SHA256,

        ),

    ),

)



_MANIFEST_BY_PROFILE: dict[str, BootstrapScriptManifest] = {

    DEDICATED_SCHEMA_MANIFEST_V1.profile: DEDICATED_SCHEMA_MANIFEST_V1,

    DEDICATED_SCHEMA_MANIFEST_V2.profile: DEDICATED_SCHEMA_MANIFEST_V2,

}



DEFAULT_DEDICATED_SCHEMA_PROFILE = DEDICATED_SCHEMA_MANIFEST_V2.profile





def get_bootstrap_v2_root() -> Path:

    return BOOTSTRAP_V2_ROOT





def load_dedicated_schema_manifest(

    *,

    profile: str = DEFAULT_DEDICATED_SCHEMA_PROFILE,

) -> BootstrapScriptManifest:

    manifest = _MANIFEST_BY_PROFILE.get(profile)

    if manifest is None:

        raise ValidationError(

            detail=f"Perfil bootstrap dedicated no soportado: {profile}.",

            internal_code="BOOTSTRAP_PROFILE_UNSUPPORTED",

        )

    return manifest





def compute_file_sha256(path: Path) -> str:

    return hashlib.sha256(path.read_bytes()).hexdigest()





def discover_manifest_entries(

    manifest: BootstrapScriptManifest,

    *,

    bootstrap_root: Path | None = None,

) -> list[tuple[BootstrapScriptManifestEntry, Path, str]]:

    """

    Resuelve rutas en disco y calcula checksum por archivo.



    Returns:

        Lista (entry, absolute_path, sha256) en orden de ejecución.

    """

    root = bootstrap_root or get_bootstrap_v2_root()

    if not root.is_dir():

        raise ValidationError(

            detail=f"Directorio bootstrap_v2 no encontrado: {root}.",

            internal_code="BOOTSTRAP_ROOT_NOT_FOUND",

        )



    discovered: list[tuple[BootstrapScriptManifestEntry, Path, str]] = []

    for entry in sorted(manifest.entries, key=lambda item: item.execution_order):

        script_path = root / entry.relative_path

        if not script_path.is_file():

            raise ValidationError(

                detail=f"Script bootstrap no encontrado: {entry.relative_path}.",

                internal_code="BOOTSTRAP_SCRIPT_NOT_FOUND",

            )

        if script_path.stat().st_size == 0:

            raise ValidationError(

                detail=f"Script bootstrap vacío: {entry.relative_path}.",

                internal_code="BOOTSTRAP_SCRIPT_EMPTY",

            )

        checksum = compute_file_sha256(script_path)

        discovered.append((entry, script_path, checksum))

    return discovered





def validate_manifest_integrity(

    manifest: BootstrapScriptManifest,

    *,

    bootstrap_root: Path | None = None,

) -> None:

    """

    Valida existencia, orden y checksum congelado del manifiesto.



    Raises:

        ValidationError: drift, archivo faltante u orden inválido.

    """

    orders = [entry.execution_order for entry in manifest.entries]

    if orders != sorted(orders) or len(set(orders)) != len(orders):

        raise ValidationError(

            detail="Orden de ejecución bootstrap inválido en manifiesto.",

            internal_code="BOOTSTRAP_MANIFEST_ORDER_INVALID",

        )



    discovered = discover_manifest_entries(manifest, bootstrap_root=bootstrap_root)

    for entry, _path, checksum in discovered:

        if checksum != entry.expected_sha256:

            raise ValidationError(

                detail=(

                    f"Checksum bootstrap divergente para {entry.relative_path} "

                    f"(esperado manifiesto v{manifest.version})."

                ),

                internal_code="BOOTSTRAP_MANIFEST_INTEGRITY_FAILED",

            )





def split_sql_server_batches(sql: str) -> list[str]:

    """Divide script T-SQL en batches separados por líneas ``GO``."""

    batches: list[str] = []

    current: list[str] = []

    for line in sql.splitlines():

        if line.strip().upper() == "GO":

            batch = "\n".join(current).strip()

            if batch:

                batches.append(batch)

            current = []

            continue

        current.append(line)

    trailing = "\n".join(current).strip()

    if trailing:

        batches.append(trailing)

    return batches





def ordered_script_codes(manifest: BootstrapScriptManifest) -> Sequence[str]:

    return tuple(

        entry.script_code

        for entry in sorted(manifest.entries, key=lambda item: item.execution_order)

    )





__all__ = [

    "BOOTSTRAP_V2_ROOT",

    "DEFAULT_DEDICATED_SCHEMA_PROFILE",

    "DEDICATED_RBAC_GRANTS_TABLE",

    "BootstrapScriptManifest",

    "BootstrapScriptManifestEntry",

    "DEDICATED_SCHEMA_MANIFEST_V1",

    "DEDICATED_SCHEMA_MANIFEST_V2",

    "DEDICATED_RUNTIME_EXTRA_TABLES",

    "DEDICATED_RUNTIME_REQUIRED_TABLES",

    "DTSP_REQUIRED_TABLES",

    "compute_file_sha256",

    "discover_manifest_entries",

    "get_bootstrap_v2_root",

    "load_dedicated_schema_manifest",

    "ordered_script_codes",

    "split_sql_server_batches",

    "validate_manifest_integrity",

]


