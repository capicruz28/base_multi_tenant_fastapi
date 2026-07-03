# DTSP — Dedicated Tenant Store Profile

**PR:** PR-F4-05b  
**Versión:** 1.1.0  
**Estado:** Implementado (F12-G3 runtime alignment)  
**Perfil manifiesto:** `dedicated_schema_v2` (v2.1.0)

---

## 1. Objetivo

Provisionar en **Data Plane** (BD dedicada por tenant) las tablas de identidad, menús, permisos y relaciones tenant necesarias para ejecutar:

- S6 — `DedicatedCatalogSeedService`
- S7 — `DedicatedTenantSeedService`

Sin introducir tablas de **Control Plane** (`cliente`, `cliente_conexion`, `cliente_auth_config`, etc.).

---

## 2. Script oficial

| Campo | Valor |
|-------|--------|
| Ruta | `app/bootstrap_v2/05_dedicated/V020__tenant_identity_rbac_store.sql` |
| Script code | `apply_schema_tenant_store_v020` |
| Step saga | S5 — `apply_schema_rbac` |
| Orden | 2 (tras `apply_schema_erp_v010`, antes de `apply_schema_rbac_v010`) |
| Prerequisito | `01_schema/V010__tablas_bd_erp_completo.sql` (`org_empresa`) |

---

## 3. Tablas incluidas (9)

| Dominio | Tabla |
|---------|--------|
| Menús / catálogo módulo | `modulo`, `modulo_seccion`, `modulo_menu` |
| RBAC | `permiso`, `rol`, `rol_menu_permiso` |
| Identity | `usuario`, `usuario_rol` |
| Licenciamiento tenant | `cliente_modulo` |

**Fuera de DTSP (mismo pipeline S5):** `rol_permiso` vía `05_dedicated/V010__rbac_tablas_dedicated.sql`.

**Runtime audit (F12-G3, mismo pipeline S5):** `auth_audit_log` vía `05_dedicated/V030__auth_audit_log_dedicated.sql` — paridad columnas V020 central, sin FK → `cliente`.

**Fuera de Data Plane (Control Plane):** `log_sincronizacion_usuario`, IAM session store (`user_session`, `token_family`, `refresh_tokens`) — ADR-002-A MVP.

---

## 3b. Tablas runtime obligatorias (gate READY)

Conjunto `DEDICATED_RUNTIME_REQUIRED_TABLES` (`script_manifest.py`):

| Grupo | Tablas |
|-------|--------|
| DTSP | 9 tablas §3 |
| RBAC grants | `rol_permiso` |
| ERP mínimo auth | `org_empresa`, `cfg_codigo_secuencia` |
| Audit tenant | `auth_audit_log` |

Verificación: `BootstrapScriptRunner._verify_runtime_schema` tras perfil v2.

## 4. Reglas estructurales

| Regla | Especificación |
|-------|----------------|
| Paridad columnas | 100% idénticas a `V020__tablas_bd_central.sql` (subset) + `V030` (`permiso`) |
| `cliente_id` | Permanece como referencia lógica UUID — **sin FK → `cliente`** |
| FK eliminadas | Solo FK que referencian `cliente(cliente_id)` (6 tablas) |
| FK mantenidas | `modulo*`, `org_empresa`, relaciones intra-DTSP |
| Idempotencia | `IF NOT EXISTS` por tabla e índice |
| CP / DP | Tabla `cliente` solo en BD central |

---

## 5. Perfil manifiesto `dedicated_schema_v2`

| Orden | Script code | Archivo | Step |
|------:|-------------|---------|------|
| 1 | `apply_schema_erp_v010` | `01_schema/V010__tablas_bd_erp_completo.sql` | S4 |
| 2 | `apply_schema_tenant_store_v020` | `05_dedicated/V020__tenant_identity_rbac_store.sql` | S5 |
| 3 | `apply_schema_rbac_v010` | `05_dedicated/V010__rbac_tablas_dedicated.sql` | S5 |
| 4 | `apply_schema_auth_audit_v030` | `05_dedicated/V030__auth_audit_log_dedicated.sql` | S5 |

Implementación: `app/infrastructure/provisioning/script_manifest.py` (`DEDICATED_SCHEMA_MANIFEST_V2`, versión manifiesto **2.1.0**).

Perfil legacy `dedicated_schema_v1` (2 scripts, sin DTSP) permanece cargable explícitamente para compatibilidad de tests.

---

## 6. Verificación post-bootstrap

`BootstrapScriptRunner` valida presencia de **`DEDICATED_RUNTIME_REQUIRED_TABLES`** tras ejecutar perfil v2 (DTSP + `rol_permiso` + `auth_audit_log` + `org_empresa` + `cfg_codigo_secuencia`).

Markers idempotentes en tabla `bootstrap_applied` (sin cambio respecto PR-F4-05).

---

## 7. Trazabilidad

| Artefacto | Referencia |
|-----------|------------|
| ADR C-01 | Architecture Decision Review Bootstrap Dedicated |
| Diseño | PR-F4-05b Architecture & Implementation Design |
| Paridad schema | Pre-Implementation Review Schema Parity (cerrado) |
| Orden bootstrap | `BOOTSTRAP_ORDER.md` Fase 6 |
| Mapa fuentes | `SOURCE_MAP.json` |

**Siguiente PR:** PR-F4-08 (saga provisioning S1–S10).
