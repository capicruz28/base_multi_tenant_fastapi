# Onboarding — integración CFG

---

## 1. Flujo actual (`OnboardingRbacService.bootstrap_cliente_rbac`)

```text
resolve_modulos_for_plan(plan)
  → TRIAL_MODULES  ["ORG","SYS_ADMIN","INV"]   ← añadir CFG
activar_modulos_base_cliente
  → cliente_modulo por cada código
bootstrap_global_grants_admin_tenant
  → rol_permiso globales (ya incluye cfg.%)
OwnerSyncService.sync_modules_for_owner(modulos)
  → RP por modulo_id + RMP menús
BaseOperative / ManagerStandard / UserStandard
  → NO incluir CFG
```

**Archivo:** `app/modules/tenant/application/services/onboarding_rbac_service.py`

---

## 2. Puntos exactos a integrar

### 2.1 `TRIAL_MODULES` (obligatorio)

| Archivo | Cambio futuro |
|---------|---------------|
| `owner_sync_constants.py` | `TRIAL_MODULES = ("ORG", "SYS_ADMIN", "INV", "CFG")` |

Propaga automáticamente a:

- `MODULOS_BASE` (`onboarding_rbac_service.py`)
- `MODULOS_MENU_BASE` (`onboarding_menu_bootstrap_service.py`)
- `resolve_modulos_for_plan` (`plan_modulo_resolver.py`) — todos los planes conocidos

### 2.2 Health / conteo RMP (obligatorio)

| Constante | Actual | Futuro |
|-----------|--------|--------|
| `MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS` | `18` | `18 + N` (N = nº menús CFG visibles; MVP típico **N=1 → 19**) |
| `MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS` | alias | Sigue al anterior |

Comentario actual: `6 ORG + 3 SYS_ADMIN.TENANT + 9 INV` → actualizar fórmula.

### 2.3 `activar_modulos_base_cliente` → `cliente_modulo`

| Comportamiento | Sin cambio de código de método |
|----------------|--------------------------------|
| Lookup `modulo` por `codigo` | Requiere fila CFG en S010 primero |
| INSERT idempotente `cliente_modulo` | Incluirá CFG al estar en trial list |

**Cómo ORG/INV llegan hoy:** exclusivamente este método en onboarding (no R020).  
**Cómo CFG llegará:** igual.

### 2.4 `bootstrap_global_grants_admin_tenant` → `rol_permiso`

| Estado | Acción |
|--------|--------|
| Ya filtra `p.codigo LIKE 'cfg.%'` + `modulo_id IS NULL` | **No modificar** |
| S068 backfill tenants existentes | Ya presente |

Confirmación: permisos API CFG **suficientes**; no crear nuevos.

### 2.5 `OwnerSyncService` → menú + RP módulo

| Método | Comportamiento con CFG |
|--------|------------------------|
| `sync_module_for_owner(..., "CFG")` | Tras trial, se invocará automáticamente |
| `_sync_rol_menu_permiso_module` | Inserta RMP de todos los menús CFG activos/visibles (sin filtro SYS_ADMIN) |
| `_sync_rol_permiso_module` | JOIN `permiso.modulo_id` — **no** recoge S068 (`NULL`); OK — API ya vía globales |
| Filtro `_SYS_ADMIN_MENU_FILTER` | Solo si código `SYS_ADMIN`; **no aplica a CFG** |

**Visibilidad solo ADMIN_TENANT:** OwnerSync escribe sobre rol `ADMIN_TENANT`.  
Manager/User **no** reciben RMP CFG si no se añaden a sus constants.

### 2.6 Manager / User Standard (explícito: no integrar CFG)

| Archivo | Acción |
|---------|--------|
| `manager_standard_constants.py` | **No** añadir menu UUIDs CFG ni `cfg.*` |
| `user_standard_constants.py` | **No** añadir |
| Services correspondientes | Sin cambio |

Cumple decisión: seed inicial solo ADMIN_TENANT.

### 2.7 `OnboardingMenuBootstrapService`

| Aspecto | Acción futura |
|---------|---------------|
| Delega a OwnerSync con lista trial | Cubierto al añadir CFG a `TRIAL_MODULES` |
| `TENANT_ADMIN_MENU_SCOPE_SQL` (legacy repair) | Si aún se usa en repair: incluir módulo `CFG` o menús CFG |
| Scripts `repair_tenant_menu_grants.py` | Siguen `MIN_HEALTHY_*` — actualizar expectativa |

### 2.8 Orchestrator

| Archivo | Acción |
|---------|--------|
| `tenant_bootstrap_orchestrator.py` | **Sin cambio estructural** — ya llama `seed_tenant_rbac` + `seed_codigo_secuencias` |
| Seed datos `cfg_codigo_secuencia` | Ya existe; ortogonal al menú |

---

## 3. Trial — tenant nuevo recibe CFG

Secuencia esperada post-implementación:

1. Catalog S010 tiene `CFG` + menú.  
2. Onboarding resuelve trial = `…, CFG`.  
3. `cliente_modulo(CFG)` insertado.  
4. Globales otorgan `cfg.secuencias.*` a ADMIN_TENANT (si no estaban).  
5. OwnerSync crea RMP del menú CFG para ADMIN_TENANT.  
6. Login admin → `/auth/menu` muestra CFG → `/app/cfg/secuencias`.  
7. Manager/User → sin ítem CFG.

---

## 4. Activación comercial post-onboarding (nota)

`ClienteModuloService.activar_modulo_cliente` hoy **no** llama `OwnerSync.sync_module_for_owner` (solo deactivate hook).  

Para activaciones **manuales** de CFG en tenants existentes, la implementación deberá o bien:

- invocar OwnerSync al activar, **o**
- documentar repair/sync explícito,

para no dejar `cliente_modulo` sin RMP.  
(Trial onboarding ya sincroniza en el mismo bootstrap.)

---

## 5. Tests / scripts a actualizar (inventario)

| Ubicación | Qué ajustar |
|-----------|-------------|
| `tests/unit/test_onboarding_menu_bootstrap.py` | floor 18 → N |
| `tests/unit/test_onboarding_rbac_bootstrap.py` | lista módulos + conservar assert `cfg.%` |
| `tests/unit/test_plan_modulo_resolver.py` | sigue `TRIAL_MODULES` |
| `tests/unit/test_impersonation_auth.py` / legacy repair / base_operative | sets de módulos |
| `scripts/run_m1_m2_staging_integration.py` | expected modules + health |
| Evidence JSON bootstrap | refrescar post-staging |
