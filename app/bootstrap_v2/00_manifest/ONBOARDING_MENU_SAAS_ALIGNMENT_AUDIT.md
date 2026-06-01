# Auditoría — Alineación menú/scopes SaaS (pre-implementación)

**Fecha:** 2026-05-22  
**Decisión arquitectura:** PLATFORM → `/super-admin/*`; TENANT_ADMIN → `/admin/*` + ORG + `SYS_ADMIN.TENANT.*`; ERP usuarios → `/app/*` por módulo contratado.

---

## 1. Hallazgos

### 1.1 `OnboardingMenuBootstrapService` (gap confirmado)

| Filtro actual | Efecto |
|---------------|--------|
| `m.codigo IN ('ORG','SYS_ADMIN')` | Activa **todo** menú SYS_ADMIN del módulo |
| Excluye solo `SYS_ADMIN.PLATFORM.%` | **Incluye `SYS_ADMIN.CATALOGOS.*`** (5 ítems) → incorrecto para tenant_admin |
| No filtra por prefijo menú ORG | OK (módulo ORG solo tiene `ORG_*`) |

**Conteo actual tenant nuevo:** 14 grants = 6 ORG + 3 TENANT + 5 CATALOGOS.  
**Objetivo:** **9** = 6 ORG + 3 `SYS_ADMIN.TENANT.*`.

### 1.2 Catálogo `S010__seed_modulo_menu_completo.sql`

| Área | Rutas en BD |
|------|-------------|
| ORG | `/org/empresa`, `/org/sucursales`, … |
| INV, CRM, … | `/inv/*`, etc. |
| S020 SYS_ADMIN.TENANT | `/admin/usuarios`, `/admin/roles`, `/admin/sesiones` ✅ |
| S020 PLATFORM / CATALOGOS | `/super-admin/*` ✅ |

FE espera ERP en **`/app/{modulo}/*`**.

### 1.3 Payload `/auth/menu`

- `ModuloMenuService.obtener_menu_usuario` lee `modulo_menu.ruta` tal cual.
- `menu_transformer` expone `ruta` sin normalizar → FE recibe `/org/...`.

### 1.4 Scopes (sin cambio en esta fase)

| Tabla | Rol |
|-------|-----|
| `cliente_modulo` | Módulos contratados (onboarding: ORG + SYS_ADMIN) ✅ |
| `rol_permiso` | API (`onboarding_rbac_service`) — no tocar |
| `rol_menu_permiso` | Visibilidad sidebar — corregir alcance |

`access_level` / elevación admin: **no tocar** (fuera de alcance).

---

## 2. Estrategia (mínima, enterprise)

| # | Acción | Archivo |
|---|--------|---------|
| 1 | Filtro menú tenant_admin: ORG + `SYS_ADMIN.TENANT.%` only | `onboarding_menu_bootstrap_service.py`, `repair_tenant_menu_grants.py` |
| 2 | Normalización runtime rutas legacy → `/app/*` en payload | `menu_route_normalizer.py` + `menu_transformer.py` |
| 3 | Migración SQL opcional catálogo (idempotente) | `S021__menu_routes_saas_alignment.sql` |
| 4 | Repair: **prune** grants inválidos + re-insert | `repair_tenant_menu_grants.py` |
| 5 | Tests unitarios filtros + rutas | `test_onboarding_menu_bootstrap.py`, `test_menu_route_normalizer.py` |

**No tocar:** auth, JWT, permission_sync, onboarding_rbac, resolver, FE, access_level.

**Compatibilidad legacy:** normalización en **runtime** (payload); SQL S021 alinea BD para nuevos deploys y reporting; APIs HTTP siguen en rutas reales del router (`/api/v1/org/...`).

---

## 3. Impacto esperado

| Actor | Antes | Después |
|-------|-------|---------|
| Tenant admin sidebar | ORG + SYS_ADMIN (incl. catálogos) | ORG + 3 ítems admin tenant |
| Rutas menú ORG en JSON | `/org/...` | `/app/org/...` |
| `rol_menu_permiso` nuevo tenant | 14 | **9** |
| Platform superadmin | Sin cambio | Menús platform solo con rol platform / elevación |

---

## 4. Riesgos

| Riesgo | Mitigación |
|--------|------------|
| FE bookmarks a `/org/*` | Rutas menú son navegación; FE usa payload nuevo |
| Tenants con 14 grants legacy | Repair prune + re-grant |
| Doble prefijo `/app/app/` | Normalizer idempotente si ya `/app/` |
| INV visible si se activa módulo después | Sin grant menú hasta rol/plantilla; `cliente_modulo` no incluye INV en onboarding |

---

## 5. Criterios aceptación RC

- [ ] Tenant nuevo: `rol_menu_permiso` = **9**, sin CATALOGOS/PLATFORM
- [ ] `/auth/menu`: módulos `ORG`, `SYS_ADMIN`; menús ORG con `ruta` `/app/org/...`
- [ ] Sin `SYS_ADMIN.CATALOGOS.*` ni `SYS_ADMIN.PLATFORM.*` en payload tenant admin
- [x] Smoke PASS (tenant `smokerc3aad0984`, 2026-05-22)

---

## 6. Implementación aplicada

| Componente | Cambio |
|----------|--------|
| `onboarding_menu_bootstrap_service` | Scope `ORG` + `SYS_ADMIN.TENANT.%`; prune CATALOGOS/PLATFORM; **9** grants |
| `modulo_menu_service` | Filtro payload elevado tenant_admin (sin tocar access_level) |
| `menu_route_normalizer` + `menu_transformer` | `/org/*` → `/app/org/*` en JSON |
| `S021__menu_routes_saas_alignment.sql` | UPDATE catálogo idempotente |
| `repair_tenant_menu_grants` | Mismo scope + prune legacy |
| `http_smoke_runner` | Valida ausencia CATALOGOS/PLATFORM y rutas `/app/org/*` |

Evidencia: `evidence/RC1_ONBOARDING_MENU_FINAL_VALIDATION.json`
