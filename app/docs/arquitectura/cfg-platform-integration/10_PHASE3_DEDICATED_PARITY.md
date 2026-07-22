# Fase 3 — Paridad Dedicated para CFG

**Fecha:** 2026-07-18  
**Alcance:** Solo `catalog_profiles.py`. Sin refactor ni cambios de arquitectura.

---

## 1. Archivo modificado

| Archivo |
|---------|
| `app/infrastructure/provisioning/catalog_profiles.py` |

Ningún otro archivo de código tocado.

---

## 2. Cambios realizados

### 2.1 Checksum S010

Actualizado en `_CATALOG_CHECKSUMS` tras Fase 1 (módulo/menú CFG):

```text
02_catalog/S010__seed_modulo_menu_completo.sql
→ 6916565c051a0206a033ac258ec727a0324752e6d11629aa76eeacaeb9eb96de
```

**Justificación:** el profile Dedicated valida SHA256 antes de ejecutar; sin esto el seed falla.

### 2.2 Registro de S068

- Checksum añadido: `02_catalog/permisos_rbac/S068__permisos_rbac_cfg.sql`  
  → `ff6752f1eca3085debb90925db3cf2034f1501201825b7ae9872c97cdb93cd5e`
- Registry: `catalog_s068`, `execution_order=35`, `module_code=None` (script global, como S030)
- Base de `resolve_catalog_seed_profile`:

```python
script_codes = ["catalog_s010", "catalog_s020", "catalog_s030", "catalog_s068"]
```

**Justificación:** Dedicated debe sembrar `cfg.secuencias.*` en `permiso` para que el onboarding (global grants) tenga el mismo efecto que en Shared.

### 2.3 Expectativa de módulos

```python
("modulo", 27)  →  ("modulo", 28)
```

en `_row_expectations_for_plan`.

**Justificación:** S010 inserta 28 módulos (incluye CFG).

### 2.4 Orden de ejecución

Tras `scripts.sort(key=execution_order)`, el prefijo fijo queda:

```text
catalog_s010 (10)
catalog_s020 (20)
catalog_s030 (30)
catalog_s068 (35)
… S04x según plan …
```

Verificado con `resolve_catalog_seed_profile("trial")`.

---

## 3. Equivalencia funcional Shared ↔ Dedicated (CFG)

| Capacidad | Shared | Dedicated (post Fase 3) |
|-----------|--------|-------------------------|
| Catálogo `modulo`/`modulo_menu` CFG | S010 bootstrap | S010 vía catalog profile |
| Permisos `cfg.secuencias.*` | S068 bootstrap | S068 vía catalog profile |
| `cliente_modulo(CFG)` | `TRIAL_MODULES` + onboarding | Igual (mismo onboarding) |
| RMP menú CFG | OwnerSync | Igual |
| `/auth/menu` → `/app/cfg/secuencias` | Q1∩Q2 + normalizer | Igual |

**Confirmación:** Shared y Dedicated quedan funcionalmente equivalentes para CFG en el provisioning de un tenant nuevo.

---

## 4. Fuera de alcance (no tocado)

S010/S020/S021/S068 (contenido), onboarding, OwnerSync, TRIAL_MODULES, FE, OpenAPI, API CFG, Manager/User, repairs, tests.
