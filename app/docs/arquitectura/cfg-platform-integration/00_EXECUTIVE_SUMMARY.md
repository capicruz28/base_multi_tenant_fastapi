# CFG Platform Integration — Resumen ejecutivo

**Fecha:** 2026-07-18  
**Tipo:** Plan de implementación (inventario + orden de ejecución)  
**Estado:** Listo para implementar — **sin código en este paquete**

---

## Decisiones aprobadas (no negociables)

| Decisión | Valor |
|----------|--------|
| Dominio | Módulo ERP independiente `CFG` |
| API | `/api/v1/cfg/*` (sin cambio) |
| FE | `/app/cfg/secuencias` (sin rediseño) |
| Catálogo | `modulo.codigo = CFG` propio |
| Contrato | `cliente_modulo` propio |
| Menú | `modulo_menu` propio |
| Pipeline | Idéntico a ORG / INV |
| Visibilidad inicial | Solo `ADMIN_TENANT` (RMP + RP) |
| Fuera de alcance | `/admin`, OpenAPI, contratos, permisos nuevos |

---

## Gap actual (una frase)

API + permisos `cfg.secuencias.*` ya existen; **falta el cableado de plataforma** (catálogo menú + suscripción + OwnerSync menú + trial/Dedicated) para que `GET /auth/menu` devuelva CFG.

---

## Superficies a tocar (mapa)

| # | Superficie | ¿Modificar? | Notas |
|---|------------|-------------|--------|
| 1 | `S010` | **Sí** | Insertar `modulo` + sección + menú CFG |
| 2 | `S021` | **Sí** | Whitelist `/cfg/%` → `/app/cfg/%` |
| 3 | `S020` | **No** | No es patrón IAM |
| 4 | `S068` | **No** (permisos) | Ya suficiente; Dedicated debe **ejecutarlo** |
| 5 | `R020` | **No** | Solo SYS_ADMIN |
| 6 | `TRIAL_MODULES` | **Sí** | Añadir `CFG` |
| 7 | Health grants `18` | **Sí** | +N menús CFG (p.ej. 19 si 1 pantalla) |
| 8 | OwnerSync | **Automático** | Tras trial + catálogo |
| 9 | Manager/User Standard | **No** | Excluir CFG (solo ADMIN_TENANT) |
| 10 | `catalog_profiles.py` | **Sí** | S068 + checksum S010 + count `modulo` |
| 11 | API `/cfg` / OpenAPI | **No** | Ya certificado |
| 12 | FE | **No** | Ruta ya decidida |

---

## Índice

| Doc | Contenido |
|-----|-----------|
| [`01_MODULE_LIFECYCLE.md`](01_MODULE_LIFECYCLE.md) | Ciclo ORG/INV completo |
| [`02_CATALOG_INTEGRATION.md`](02_CATALOG_INTEGRATION.md) | Catálogo menú |
| [`03_BOOTSTRAP_INTEGRATION.md`](03_BOOTSTRAP_INTEGRATION.md) | S010/S020/S021/R0xx |
| [`04_ONBOARDING_INTEGRATION.md`](04_ONBOARDING_INTEGRATION.md) | Trial, OwnerSync, bundles |
| [`05_MENU_INTEGRATION.md`](05_MENU_INTEGRATION.md) | `/auth/menu` + registros mínimos |
| [`06_SHARED_DEDICATED_IMPACT.md`](06_SHARED_DEDICATED_IMPACT.md) | Shared / Dedicated / provisioning |
| [`07_IMPLEMENTATION_ORDER.md`](07_IMPLEMENTATION_ORDER.md) | Orden exacto de ejecución |
| [`08_REGRESSION_CHECKLIST.md`](08_REGRESSION_CHECKLIST.md) | Riesgos y checklist |

---

## Criterio de done (plataforma)

1. Tenant trial nuevo Shared: `cliente_modulo(CFG)` activo.  
2. `ADMIN_TENANT`: RMP del menú CFG + RP `cfg.secuencias.*`.  
3. `GET /auth/menu` incluye módulo `CFG` con ruta `/app/cfg/secuencias`.  
4. MANAGER / USER: **sin** menú CFG.  
5. Dedicated: mismo resultado vía catalog seed + onboarding RBAC.  
6. Sin cambios OpenAPI / contratos / permisos nuevos.
