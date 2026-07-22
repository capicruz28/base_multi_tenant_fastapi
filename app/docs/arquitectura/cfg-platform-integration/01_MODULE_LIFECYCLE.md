# Ciclo de vida de un módulo ERP (referencia ORG / INV)

---

## 1. Pipeline canónico (AS-IS)

```text
[1] Catálogo global
    S010 → modulo + modulo_seccion + modulo_menu
    S021 → alinea rutas legacy a /app/...
    S04x → permisos API ligados a modulo_id (ORG/INV)
         (CFG ya usa S068 con modulo_id NULL — distinto pero válido)

[2] Provisioning / install
    Shared: bootstrap_v2 catalog en BD central
    Dedicated: catalog_profiles ejecuta S010/S020/S030 + scripts por plan

[3] Onboarding tenant
    resolve_modulos_for_plan(plan) → TRIAL_MODULES
    OnboardingRbacService.activar_modulos_base_cliente
         → INSERT cliente_modulo (ORG, SYS_ADMIN, INV, …)
    bootstrap_global_grants_admin_tenant
         → rol_permiso globales (incl. cfg.% ya)
    OwnerSyncService.sync_modules_for_owner
         → rol_permiso por modulo_id + rol_menu_permiso por menús
    ManagerStandard / UserStandard
         → bundles operativos (ORG/INV subset; NO admin)

[4] Runtime menú
    GET /auth/menu
      Q1: modulo_menu ⋈ cliente_modulo (activo)
      Q2: rol_menu_permiso.puede_ver
      normalize_menu_ruta_for_fe → /app/...

[5] Runtime API
    require_permission(codigos)
    PermissionResolver ← rol_permiso
```

---

## 2. Capas y responsables

| Capa | ORG | INV | Quién crea |
|------|-----|-----|------------|
| `modulo` | `ORG` | `INV` | `S010` |
| `modulo_seccion` | `PRINCIPAL` | `PRINCIPAL` | `S010` |
| `modulo_menu` | 6 pantallas `/org/*` | 9 pantallas `/inv/*` | `S010` (+ `S021`) |
| Permisos API | `S040` (`modulo_id` ORG) | `S041/S042` | Catalog permisos_rbac |
| `cliente_modulo` | Onboarding trial | Onboarding trial | `OnboardingRbacService` |
| `rol_menu_permiso` owner | OwnerSync `ORG` | OwnerSync `INV` | `OwnerSyncService` |
| `rol_permiso` owner (módulo) | OwnerSync JOIN `permiso.modulo_id` | Igual | `OwnerSyncService` |
| Bundles Manager/User | Subset menús ORG/INV | Subset | Manager/User Standard |
| Visibilidad menú | Q1∩Q2 | Q1∩Q2 | `ModuloMenuService` |

---

## 3. Constantes de control

| Símbolo | Archivo | Valor actual |
|---------|---------|--------------|
| `TRIAL_MODULES` | `owner_sync_constants.py` | `("ORG", "SYS_ADMIN", "INV")` |
| `MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS` | mismo | `18` (= 6+3+9) |
| `MODULOS_BASE` | `onboarding_rbac_service.py` | alias trial |
| `MODULOS_MENU_BASE` | `onboarding_menu_bootstrap_service.py` | alias trial |
| `resolve_modulos_for_plan` | `plan_modulo_resolver.py` | todos los planes → trial |

---

## 4. Qué hace CFG distinto (ya aprobado / AS-IS)

| Aspecto | ORG/INV | CFG (aprobado / AS-IS) |
|---------|---------|-------------------------|
| Permisos API seed | Ligados a `modulo_id` | `S068` con `modulo_id IS NULL` |
| Grant API nuevos tenants | OwnerSync por módulo + globales | **`bootstrap_global_grants` (`cfg.%`)** + S068 backfill |
| Grant menú | OwnerSync | OwnerSync (igual, una vez exista menú) |
| Ruta FE | `/app/org`, `/app/inv` | `/app/cfg/secuencias` |
| Bundles Manager/User | Sí | **No** (solo ADMIN_TENANT) |

**No cambiar** el modelo de permisos API existentes. Solo completar el pipeline de **catálogo + suscripción + RMP**.

---

## 5. Mapa ORG/INV → puntos CFG

| Paso lifecycle | ¿CFG ya? | ¿Integrar? |
|----------------|----------|------------|
| Fila `modulo` | No | Sí → S010 |
| Sección + menú | No | Sí → S010 |
| Alineación `/app` | N/A | Sí → S021 + normalizer (runtime ya ok) |
| Permisos API | Sí S068 | Confirmar only |
| `cliente_modulo` trial | No | Sí → `TRIAL_MODULES` |
| OwnerSync menú | No (sin menús) | Automático tras trial |
| OwnerSync RP por modulo_id | No aplica a cfg.* NULL | No requerido |
| Global grants cfg.% | Sí | No tocar |
| Manager/User | — | **No añadir** |
| Dedicated catalog | S010 sin CFG; S068 ausente del registry | Sí |
| `/auth/menu` | No aparece | Tras F1–F5 |
