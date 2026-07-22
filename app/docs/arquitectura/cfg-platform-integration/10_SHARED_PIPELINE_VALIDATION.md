# Micro-validación — Pipeline Shared completo para CFG

**Fecha:** 2026-07-18  
**Contexto:** Fase 1 (S010) + Fase 2 (`TRIAL_MODULES`) implementadas. Solo tenants nuevos. Sin Dedicated.

---

## 1. ¿Tenant nuevo obtiene `cliente_modulo(CFG)` automáticamente?

**Sí.**

Evidencia:

- `TRIAL_MODULES = ("ORG", "SYS_ADMIN", "INV", "CFG")` (`owner_sync_constants.py`)
- `resolve_modulos_for_plan()` → lista trial
- `activar_modulos_base_cliente()` inserta `cliente_modulo` por cada código hallado en `modulo`
- S010 define `modulo.codigo = 'CFG'` (`E100001C-…`)

Precondición operativa: S010 ejecutado en la BD Shared del entorno (bootstrap estándar).

---

## 2. ¿`bootstrap_global_grants_admin_tenant` otorga `cfg.secuencias.*` sin cambios?

**Sí.**

Evidencia: en `onboarding_rbac_service.py` el SQL de grants globales incluye `OR p.codigo LIKE 'cfg.%'` sobre permisos con `modulo_id IS NULL`.  
S068 ya define `cfg.secuencias.consultar` / `cfg.secuencias.actualizar`. No hace falta cambiar grants.

---

## 3. ¿OwnerSync genera `rol_menu_permiso` para CFG automáticamente?

**Sí.**

Evidencia:

- Onboarding llama `sync_modules_for_owner(..., modulos_codigo=modulos)` con la lista activada (incluye CFG)
- `_sync_rol_menu_permiso_module` inserta RMP de menús activos/visibles del módulo (sin filtro especial salvo `SYS_ADMIN`)
- S010 tiene `CFG_SECUENCIAS` (`E31C0001-…`, `es_activo=1`, `es_visible=1`)

Resultado esperado: 1 RMP Owner para `ADMIN_TENANT`.

---

## 4. ¿`GET /auth/menu` devuelve CFG con ruta `/app/cfg/secuencias` sin más cambios?

**Sí.**

Evidencia:

- Q1: `cliente_modulo(CFG)` + menú en catálogo
- Q2: `rol_menu_permiso.puede_ver` del Owner
- S010 guarda `ruta = '/cfg/secuencias'`
- `normalize_menu_ruta_for_fe` antepone `/app` a paths absolutos no reservados → **`/app/cfg/secuencias`**
- S021 no es requerido para el payload de menú (dictamen Fase 2 rutas)

---

## 5. ¿Bloqueo funcional restante (Shared, tenant nuevo)?

**Ninguno.**

No se listan mejoras futuras, Dedicated ni backfill.

---

## Veredicto final

```
El pipeline Shared quedó completamente integrado para CFG y está listo para pasar a la fase Dedicated.
```
