# BOOTSTRAP_MANIFEST — ERP multiempresa (v2)

| Campo | Valor |
|-------|--------|
| Versión | 2.0.0 |
| Ruta oficial | `app/bootstrap_v2/` |
| Legacy (inmutable) | `app/docs/database/` |
| Mapa máquina | `SOURCE_MAP.json` |
| Orden ejecución | `BOOTSTRAP_ORDER.md` |
| Gaps conocidos | `BOOTSTRAP_GAPS.md` |

---

## Estructura de carpetas

| Carpeta | Propósito | Prefijo |
|---------|-----------|---------|
| `00_manifest/` | Documentación y mapa fuentes | — |
| `01_schema/` | DDL tablas | `V###__` |
| `02_catalog/` | Catálogo global (módulos, menús, permisos) | `S###__` |
| `03_runtime/` | Seeds post-catalog necesarios en prod | `R###__` |
| `04_qa/` | Demo tenants y grants QA | `D###__` |
| `05_dedicated/` | DDL específico BD dedicada | `V###__` |

---

## Inventario completo

### 01_schema — PROD

| Archivo v2 | Legacy | Tablas principales |
|------------|--------|-------------------|
| `V010__tablas_bd_erp_completo.sql` | `3.- TABLAS_BD_ERP_COMPLETO.sql` | ~100 tablas `org_*`, `inv_*`, … `aud_*` |
| `V020__tablas_bd_central.sql` | `1.- TABLAS_BD_CENTRAL.sql` | `cliente`, `modulo*`, `usuario`, `rol`, `usuario_rol`, `rol_menu_permiso`, auth |
| `V030__rbac_tablas_central.sql` | `5.- SCRIPT_RBAC_TABLAS_CENTRAL.sql` | `permiso`, `rol_permiso` |

### 02_catalog — PROD

| Archivo v2 | Legacy | Modifica |
|------------|--------|----------|
| `S010__seed_modulo_menu_completo.sql` | `4.- SEED_MODULO_MENU_COMPLETO.sql` | `modulo`, `modulo_seccion`, `modulo_menu` (27 módulos) |
| `S020__seed_admin_menu.sql` | `6.- SEED_ADMIN_MENU.sql` | `SYS_ADMIN` + menús admin + `permiso` admin.* + `rol_permiso` parcial |
| `S030__seed_permisos_core.sql` | `7.- SEED_PERMISOS_CORE.sql` | `permiso` `core.app.acceder` |

#### 02_catalog/permisos_rbac — PROD (módulos contratados / dev full)

| v2 | Legacy |
|----|--------|
| `S040__permisos_rbac_org.sql` | `SEED_PERMISOS_RBAC_ORG.sql` |
| `S041__permisos_rbac_inv-fase4.sql` | `SEED_PERMISOS_RBAC_INV_FASE4.sql` |
| `S042__permisos_rbac_inv-lifecycle.sql` | `SEED_PERMISOS_RBAC_INV_LIFECYCLE.sql` |
| `S043__permisos_rbac_wms.sql` | `SEED_PERMISOS_RBAC_WMS.sql` |
| `S044__permisos_rbac_qms.sql` | `SEED_PERMISOS_RBAC_QMS.sql` |
| `S045__permisos_rbac_pur.sql` | `SEED_PERMISOS_RBAC_PUR.sql` |
| `S046__permisos_rbac_log.sql` | `SEED_PERMISOS_RBAC_LOG.sql` |
| `S047__permisos_rbac_mfg.sql` | `SEED_PERMISOS_RBAC_MFG.sql` |
| `S048__permisos_rbac_mrp.sql` | `SEED_PERMISOS_RBAC_MRP.sql` |
| `S049__permisos_rbac_mps.sql` | `SEED_PERMISOS_RBAC_MPS.sql` |
| `S050__permisos_rbac_mnt.sql` | `SEED_PERMISOS_RBAC_MNT.sql` |
| `S051__permisos_rbac_sls.sql` | `SEED_PERMISOS_RBAC_SLS.sql` |
| `S052__permisos_rbac_crm.sql` | `SEED_PERMISOS_RBAC_CRM.sql` |
| `S053__permisos_rbac_inv-bill.sql` | `SEED_PERMISOS_RBAC_INV_BILL.sql` |
| `S054__permisos_rbac_pos.sql` | `SEED_PERMISOS_RBAC_POS.sql` |
| `S055__permisos_rbac_hcm.sql` | `SEED_PERMISOS_RBAC_HCM.sql` |
| `S056__permisos_rbac_fin.sql` | `SEED_PERMISOS_RBAC_FIN.sql` |
| `S057__permisos_rbac_bdg.sql` | `SEED_PERMISOS_RBAC_BDG.sql` |
| `S058__permisos_rbac_cst.sql` | `SEED_PERMISOS_RBAC_CST.sql` |
| `S059__permisos_rbac_pm.sql` | `SEED_PERMISOS_RBAC_PM.sql` |
| `S060__permisos_rbac_svc.sql` | `SEED_PERMISOS_RBAC_SVC.sql` |
| `S061__permisos_rbac_tkt.sql` | `SEED_PERMISOS_RBAC_TKT.sql` |
| `S062__permisos_rbac_bi.sql` | `SEED_PERMISOS_RBAC_BI.sql` |
| `S063__permisos_rbac_dms.sql` | `SEED_PERMISOS_RBAC_DMS.sql` |
| `S064__permisos_rbac_wfl.sql` | `SEED_PERMISOS_RBAC_WFL.sql` |
| `S065__permisos_rbac_aud.sql` | `SEED_PERMISOS_RBAC_AUD.sql` |
| `S066__permisos_rbac_fase4-candidatos.sql` | `SEED_PERMISOS_RBAC_FASE4_CANDIDATOS.sql` |
| `S067__permisos_rbac__legacy_empty_stub.sql` | `SEED_PERMISOS_RBAC.sql` (**vacío**, legacy) |

### 03_runtime — PROD (transitorio)

| Archivo v2 | Legacy | Reemplazo futuro backend |
|------------|--------|--------------------------|
| `R010__asignar_core_app_a_roles.sql` | `8.- SEED_ASIGNAR_CORE_APP_A_ROLES.sql` | Onboarding: grant `core.app.acceder` |
| `R020__relacion_sys_admin_cliente_modulo.sql` | `10.- RELACION_SYS_ADMIN_CLIENTE_MODULO.sql` | Onboarding: activar `SYS_ADMIN` |

### 04_qa — QA / DEV only

| Archivo v2 | Legacy | Contenido activo |
|------------|--------|------------------|
| `D010__seed_bd_central.sql` | `2.- SEED_BD_CENTRAL.sql` | 5 clientes demo + usuarios/roles (bloques legacy comentados) |
| `D020__rol_permiso_administrador.sql` | `9.- SEED_ROL_PERMISO_ADMINISTRADOR.sql` | Grant masivo permisos → Administrador |
| `D030__cliente_modulo_activar_org.sql` | `SEED_CLIENTE_MODULO_ACTIVAR_ORG.sql` | `cliente_modulo` ORG para UUIDs demo |

### 05_dedicated — PROD (por BD dedicada)

| Archivo v2 | Legacy |
|------------|--------|
| `V010__rbac_tablas_dedicated.sql` | `SCRIPT_RBAC_TABLAS_DEDICADA.sql` |

---

## Clasificación por entorno

| Etiqueta | Archivos |
|----------|----------|
| **PROD** | `V010`, `V020`, `V030`, `S010`, `S020`, `S030`, `S040–S066`, app startup, `R010`, `R020`, dedicated `V010` |
| **QA** | `D010`, `D020`, `D030` |
| **LEGACY (no ejecutar)** | `S067`, bloques comentados dentro de `D010`, `SEED_BD_DEDICADA_*` (fuera de v2) |

---

## Idempotencia (estado actual, sin corrección)

| Idempotente | Archivos |
|-------------|----------|
| Sí | `V030`, `S030`, `S040–S066` (MERGE), `R010`, `R020` (NOT EXISTS), `D020` |
| No | `V010`, `V020`, `S010`, `S020`, `D010`, `D030` |

---

## Reemplazos planificados por runtime backend

| Concern | Servicio / módulo |
|---------|-------------------|
| Sync permisos API | `app/core/authorization/permission_sync_service.py` |
| Crear tenant | `ClienteOnboardingService` |
| Activar módulos | `ClienteModuloService` + `rol_plantilla_applier` |
| Menú ↔ permiso | `MenuPermissionBinder` (pendiente wiring startup) |
| Empresa + JWT | `AuthService`, `EmpresaService` |

---

## Política de cambios

1. **No editar** SQL en `bootstrap_v2/` para lógica de negocio (solo headers de trazabilidad).
2. Cambios de lógica → archivos legacy en `app/docs/database/`.
3. Tras cambiar legacy → refrescar copias v2 (script futuro `scripts/refresh_bootstrap_v2.ps1`).
4. Gaps → documentar en `BOOTSTRAP_GAPS.md`, no parchear silenciosamente en v2.
