# Shared / Dedicated / Provisioning — impacto CFG

---

## 1. Shared Database

| Componente | Impacto |
|------------|---------|
| Catálogo menú (S010/S021) | Se aplica en BD central / shared catalog |
| S068 | Ya en línea bootstrap Shared (manifest) |
| Onboarding RBAC | Misma sesión tenant; `TRIAL_MODULES` + OwnerSync |
| Q1 menú | `menu_catalog_store` → store TENANT_DATA / shared |
| Q2 RMP | DEFAULT + `client_id` |

**Acción:** integrar S010/S021 + trial; Shared queda cubierto por bootstrap + onboarding.

---

## 2. Dedicated Database

| Componente | Impacto / gap AS-IS |
|------------|---------------------|
| `catalog_profiles.py` registry | Ejecuta S010, S020, S030 + S04x por plan |
| **S068** | **No está** en `CATALOG_SCRIPT_REGISTRY` hoy → Dedicated puede **no** sembrar `cfg.secuencias.*` en `permiso` al provisionar |
| **S021** | No está en registry; rutas pueden depender solo del normalizer runtime o de S010 ya con `/app/...` |
| `row_expectations` | `("modulo", 27)` → subir a **28** tras S010 |
| Checksum S010 | Recalcular tras editar S010 |
| `ALL_CATALOG_MODULE_CODES` | Lista comercial enterprise; **añadir `CFG`** si enterprise debe sembrar/activar CFG como módulo de plan (trial ya vía `resolve_modulos_for_plan`) |
| `_MODULE_TO_SCRIPT_CODES` | CFG no tiene S04x propio; permisos siguen S068 global — **no** mapear a script de módulo ligado salvo decisión futura |
| RBAC seed Dedicated | `dedicated_tenant_seed_adapters` → mismo `OnboardingRbacService` |
| `DedicatedPermissionCatalogSyncService` | Debe poder copiar permisos `modulo_id NULL` (`cfg.*`) |

### Acciones futuras Dedicated (obligatorias para paridad)

1. Registrar **`catalog_s068`** en `catalog_profiles` (path `permisos_rbac/S068__…`, checksum, order ~68, always-run como S030).  
2. Tras editar S010: actualizar checksum + `modulo` count 27→28.  
3. Incluir `CFG` en resolución de módulos trial (vía `TRIAL_MODULES`) — ya cubre Dedicated onboarding.  
4. Validar sync de permisos NULL-`modulo_id` hacia DP.

---

## 3. Provisioning

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dedicated provisioning debe incorporar CFG? | **Sí** — en catálogo (S010+S068) y en trial modules (cliente_modulo + OwnerSync) |
| ¿Nuevo job provisioning? | **No** — extender perfiles/constantes existentes |
| ¿DTSP schema? | Tablas `modulo*`, `cliente_modulo`, `permiso`, `rol_*` ya contempladas |
| Seed datos secuencias | Ya `seed_codigo_secuencias` / onboarding CFG data — ortogonal al menú |

---

## 4. Owner Sync en ambos modos

| Modo | Dónde corre OwnerSync |
|------|------------------------|
| Shared | Onboarding sobre store shared del tenant |
| Dedicated | Misma API de servicio sobre BD dedicada post-catalog-seed |

Contrato: módulo `CFG` contratado + menús en catálogo del mismo store → RMP insertados para `ADMIN_TENANT`.

---

## 5. Matriz Shared vs Dedicated

| Entregable | Shared | Dedicated |
|------------|--------|-----------|
| S010 + menú CFG | Bootstrap catalog | Catalog profile seed |
| S021 | Bootstrap (si se usa) | Opcional si S010 ya `/app/...`; o registrar S021 |
| S068 permisos | Ya | **Registrar en profile** |
| `cliente_modulo` CFG | Onboarding trial | Onboarding trial |
| RMP CFG | OwnerSync | OwnerSync |
| RP `cfg.*` | S068 + global grants | S068 en DP + global grants |
