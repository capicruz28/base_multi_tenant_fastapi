# Auditoría de registro de módulos en el menú — Resumen ejecutivo

**Rol:** Arquitecto Principal — Backend ERP  
**Fecha:** 2026-07-18  
**Alcance:** Solo lectura. Sin código, sin seeds, sin migraciones, sin registrar CFG.  
**Precondición:** `cfg-menu-audit/` (mecánica `/auth/menu`) conocida.  
**Módulos analizados:** ORG · INV · IAM (Tenant Admin)

---

## 1. Dictamen

| Pregunta | Respuesta factual |
|----------|-------------------|
| ¿ORG cómo se registra? | **Módulo propio** en catálogo (`modulo.codigo=ORG`) + sección + 6 menús + `cliente_modulo` + RMP |
| ¿INV cómo se registra? | **Módulo propio** (`INV`) + sección + 9 menús + `cliente_modulo` + RMP |
| ¿IAM cómo se registra? | **No es módulo propio.** Son 3 menús dentro de **`SYS_ADMIN`** / sección `TENANT_ADMIN` |
| ¿Qué patrón debe seguir CFG? | **Módulo propio `CFG`** (mismo patrón de registro que ORG/INV), **no** embebido en `SYS_ADMIN` como IAM |
| ¿CFG aparece hoy en `/auth/menu`? | **No** — faltan registros de catálogo + contrato + RMP |

---

## 2. Por qué CFG = patrón ORG/INV (no IAM)

Evidencia normativa ya aprobada (sin proponer cambios):

| Fuente | Afirmación |
|--------|------------|
| `cfg-platform-architecture/00` | Código de módulo **`cfg`**; módulo ERP operativo transversal; **no** Platform |
| `cfg-platform-architecture/04` | Estructura alineada a ORG/INV; menú en **tenant shell ERP**, no SuperAdmin |
| Backend AS-IS | `app/modules/cfg/` + mount `/api/v1/cfg` (paralelo a `/org`, `/inv`) |
| FE certificado | Contrato “módulo CFG”; permisos `cfg.secuencias.*`; checklist de menú/ruta CFG |

IAM existe como **capacidad UI de administración** bajo `SYS_ADMIN` porque no hay dominio ERP `IAM` ni API `/iam`. CFG **sí** tiene dominio ERP propio — por tanto su registro de menú coherente es el de **módulo comercial propio**, no el de menú embebido en `SYS_ADMIN`.

> Nota: la *persona* primaria (ADMIN_TENANT) se parece a IAM; el *patrón de registro en catálogo* se parece a ORG/INV. Esta auditoría separa ambos ejes.

---

## 3. Índice

| Doc | Contenido |
|-----|-----------|
| [`01_ORG_REGISTRATION.md`](01_ORG_REGISTRATION.md) | Inventario ORG + seeds |
| [`02_INV_REGISTRATION.md`](02_INV_REGISTRATION.md) | Inventario INV + seeds |
| [`03_IAM_SYS_ADMIN_REGISTRATION.md`](03_IAM_SYS_ADMIN_REGISTRATION.md) | Inventario IAM / SYS_ADMIN TENANT |
| [`04_PATTERN_COMPARISON_AND_CFG.md`](04_PATTERN_COMPARISON_AND_CFG.md) | Diferencias, patrón IAM, patrón CFG, matriz, faltantes |

---

## 4. Referencia rápida de seeds

| Artefacto | Archivo |
|-----------|---------|
| Catálogo ORG/INV | `app/bootstrap_v2/02_catalog/S010__seed_modulo_menu_completo.sql` |
| Rutas `/app` | `app/bootstrap_v2/02_catalog/S021__menu_routes_saas_alignment.sql` |
| Catálogo SYS_ADMIN + IAM menus | `app/bootstrap_v2/02_catalog/S020__seed_admin_menu.sql` |
| `cliente_modulo` SYS_ADMIN (todos clientes) | `app/bootstrap_v2/03_runtime/R020__relacion_sys_admin_cliente_modulo.sql` |
| `cliente_modulo` ORG/INV/SYS_ADMIN trial | Onboarding Python: `OnboardingRbacService` + `TRIAL_MODULES` |
| `rol_menu_permiso` owner | `OwnerSyncService` (`owner_sync_service.py`) |
