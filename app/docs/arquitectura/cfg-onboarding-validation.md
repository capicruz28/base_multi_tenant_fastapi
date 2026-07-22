# Micro-validación — CFG en pipeline de onboarding

**Fecha:** 2026-07-18  
**Alcance:** Solo `TRIAL_MODULES`, `resolve_modulos_for_plan()`, `activar_modulos_base_cliente()`, `OwnerSyncService.sync_modules_for_owner()`  
**Acción:** Auditoría — sin implementación

---

## 1. ¿`activar_modulos_base_cliente()` recorre dinámicamente los módulos de `TRIAL_MODULES`?

**Sí.**

Evidencia (`onboarding_rbac_service.py`):

- Parámetro `modulos_codigo: Sequence[str] = TRIAL_MODULES`
- Normaliza: `codigos = [c.strip().upper() for c in modulos_codigo …]`
- Lookup: `WHERE codigo IN ({placeholders})`
- Loop: `for modulo_id, codigo in rows:` → `IF NOT EXISTS … INSERT INTO cliente_modulo`
- Retorna `found_codes` (lista dinámica)

No hay rama fija por nombre de módulo.

---

## 2. ¿Tratamiento especial ORG / INV / SYS_ADMIN en estos cuatro puntos?

**Sí — solo SYS_ADMIN, y solo en el sync de menú de OwnerSync.**  
**No** hay `if` / switch / whitelist / diccionario hardcodeado para **ORG** ni **INV** en estos componentes.

| Componente | Tratamiento especial |
|------------|----------------------|
| `TRIAL_MODULES` | Tupla de códigos; sin lógica por módulo |
| `resolve_modulos_for_plan()` | Devuelve `list(TRIAL_MODULES)` para todos los planes; sin ramas por módulo |
| `activar_modulos_base_cliente()` | Genérico por lista recibida |
| `sync_modules_for_owner()` | `for codigo in modulos_codigo:` → `sync_module_for_owner` |
| Dentro de `sync_module_for_owner` → RMP | `sys_admin_extra = _SYS_ADMIN_MENU_FILTER if modulo_codigo == "SYS_ADMIN" else ""` |

`_SYS_ADMIN_MENU_FILTER` limita menús a `SYS_ADMIN.TENANT.%`.  
**CFG no entra en ese `if`** → se tratan todos sus menús visibles (como ORG/INV).

---

## 3. Si `TRIAL_MODULES` incluye `"CFG"`, ¿se crea `cliente_modulo` para CFG?

**Sí.**

Flujo real:

1. `resolve_modulos_for_plan()` → incluye `"CFG"`
2. `bootstrap_cliente_rbac` pasa esa lista a `activar_modulos_base_cliente`
3. Lookup `modulo` donde `codigo='CFG'` (requiere fila en catálogo — ya en S010)
4. `INSERT` idempotente en `cliente_modulo` si no existe

Sin fila `modulo` CFG → error `ONBOARDING_MODULO_MISSING` (no inserción silenciosa).

---

## 4. ¿OwnerSync recibirá CFG y sincronizará `rol_menu_permiso` sin cambios?

**Sí.**

Evidencia:

1. Tras activar, `bootstrap_cliente_rbac` llama:
   `OwnerSyncService.sync_modules_for_owner(..., modulos_codigo=modulos)`  
   donde `modulos` es la lista retornada por la activación (incluirá `CFG`).
2. `sync_modules_for_owner` itera **todos** los códigos recibidos.
3. `_sync_rol_menu_permiso_module` inserta RMP desde `modulo_menu` del `modulo_codigo` dado + `cliente_modulo` activo; sin whitelist ORG/INV.

Con menú `CFG_SECUENCIAS` en catálogo → se crea RMP para `ADMIN_TENANT`.

---

## 5. ¿Otro punto obligatorio a modificar (dentro de este pipeline)?

**Ninguno** en los cuatro componentes auditados.

Precondición de datos (fuera de estos símbolos, ya cumplida en Fase 1): existencia de `modulo`/`modulo_menu` CFG en catálogo.

Ajustes colaterales (`MIN_HEALTHY_*`, tests, repair legacy) **no** son bloqueos del pipeline de onboarding para crear `cliente_modulo` + RMP.

---

## Veredicto final

```
Puede agregarse CFG a TRIAL_MODULES sin modificar la arquitectura del onboarding.
```
