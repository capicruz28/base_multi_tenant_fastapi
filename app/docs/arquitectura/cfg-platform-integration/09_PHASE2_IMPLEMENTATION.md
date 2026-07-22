# Fase 2 — Integración CFG al pipeline de onboarding

**Fecha:** 2026-07-18  
**Alcance:** Solo constantes de onboarding para **nuevos tenants**. Sin cambios arquitectónicos.

---

## 1. Archivos modificados

| Archivo | Acción |
|---------|--------|
| `app/modules/tenant/application/services/owner_sync_constants.py` | Único archivo de código tocado |
| `app/docs/arquitectura/cfg-platform-integration/09_PHASE2_IMPLEMENTATION.md` | Este informe |

**No modificados (confirmado):** OwnerSync, `activar_modulos_base_cliente`, `resolve_modulos_for_plan` (lógica), grants globales, Manager/User Standard, catalog_profiles, Dedicated, S068/S020/S021, FE, OpenAPI, `/cfg`, repairs, tests.

---

## 2. Cambios realizados

### 2.1 `TRIAL_MODULES`

```python
# Antes
TRIAL_MODULES: tuple[str, ...] = ("ORG", "SYS_ADMIN", "INV")

# Después
TRIAL_MODULES: tuple[str, ...] = ("ORG", "SYS_ADMIN", "INV", "CFG")
```

**Justificación:** Punto de entrada del pipeline validado en `cfg-onboarding-validation.md`. Al incluir `CFG`, `resolve_modulos_for_plan` → `activar_modulos_base_cliente` → `cliente_modulo(CFG)` → `OwnerSync("CFG")` → RMP del menú `CFG_SECUENCIAS` para `ADMIN_TENANT`.

### 2.2 Constantes derivadas

| Alias | Archivo | ¿Editado? | Motivo |
|-------|---------|-----------|--------|
| `MODULOS_BASE` | `onboarding_rbac_service.py` | **No** | `= TRIAL_MODULES` — se actualiza por referencia |
| `MODULOS_MENU_BASE` | `onboarding_menu_bootstrap_service.py` | **No** | `= TRIAL_MODULES` — se actualiza por referencia |
| `MIN_HEALTHY_TENANT_ADMIN_MENU_GRANTS` | `onboarding_menu_bootstrap_service.py` | **No** | `= MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS` |

No se crearon constantes nuevas.

### 2.3 Health Owner

```python
# Antes
# Trial owner menu grants esperados (S010): 6 ORG + 3 SYS_ADMIN.TENANT + 9 INV
MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS = 18

# Después
# Trial owner menu grants esperados (S010): 6 ORG + 3 SYS_ADMIN.TENANT + 9 INV + 1 CFG
MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS = 19
```

**Justificación:** S010 Fase 1 añadió 1 pantalla CFG (`CFG_SECUENCIAS`). El floor de salud del Owner debe incluir ese grant.

### 2.4 `resolve_modulos_for_plan()`

Sin cambio de algoritmo. Sigue devolviendo `list(TRIAL_MODULES)`. Verificado por import/assert: `trial` y `enterprise` incluyen `CFG`.

---

## 3. Verificación de compilación / import

Ejecutado:

```text
python -c "… import TRIAL_MODULES, resolve_modulos_for_plan, MODULOS_BASE, MODULOS_MENU_BASE …"
→ OK ('ORG', 'SYS_ADMIN', 'INV', 'CFG') 19
```

---

## 4. Confirmación arquitectónica

| Afirmación | Estado |
|------------|--------|
| Pipeline dinámico sin whitelist ORG/INV | Intacta |
| OwnerSync sin modificar | Sí |
| Manager/User sin CFG | Sí (fuera de alcance; sin tocar) |
| Solo onboarding de **nuevos** tenants vía trial | Sí |
| Sin cambios de dominio/API/FE/OpenAPI | Sí |

---

## 5. Precondiciones / fuera de esta fase

- Catálogo S010 con módulo/menú CFG debe estar aplicado en la BD del entorno antes del primer onboarding con CFG.
- Tenants **existentes** no reciben CFG automáticamente (requiere backfill/repair — fuera de alcance).
- Tests unitarios que hardcodean `18` o la tupla antigua de 3 módulos pueden fallar hasta una fase de tests (explícitamente prohibida aquí).
