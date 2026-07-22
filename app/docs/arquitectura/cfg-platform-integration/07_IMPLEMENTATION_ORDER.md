# Orden de implementación recomendado

> Ejecutar en este orden para evitar `ONBOARDING_MODULOS_BASE_NOT_FOUND`, RMP=0 y desalineación Dedicated.

---

## Fase 0 — Precondiciones (ya cumplidas)

| # | Ítem | Estado |
|---|------|--------|
| 0.1 | API `/api/v1/cfg` certificada | OK |
| 0.2 | S068 permisos + grants ADMIN_TENANT | OK |
| 0.3 | `bootstrap_global_grants` incluye `cfg.%` | OK |
| 0.4 | FE ruta `/app/cfg/secuencias` decidida | OK |
| 0.5 | OpenAPI / contratos sin cambio | OK |

---

## Fase 1 — Catálogo menú (Shared bootstrap)

| Orden | Trabajo | Archivo(s) | Dependencia |
|-------|---------|------------|-------------|
| 1.1 | Insertar `modulo` CFG + sección + `modulo_menu` (ruta `/cfg/secuencias` o `/app/cfg/secuencias`) | `S010` | — |
| 1.2 | Whitelist `/cfg/%` | `S021` | 1.1 si se usa ruta corta |
| 1.3 | Aplicar seeds en entorno Shared / central | pipeline bootstrap | 1.1–1.2 |
| 1.4 | Verificar filas en BD | SQL check | 1.3 |

**Gate:** `SELECT codigo FROM modulo WHERE codigo='CFG'` → 1 fila; menú con ruta alineada a `/app/cfg/secuencias`.

---

## Fase 2 — Dedicated catalog parity

| Orden | Trabajo | Archivo(s) |
|-------|---------|------------|
| 2.1 | Registrar `catalog_s068` + checksum | `catalog_profiles.py` |
| 2.2 | Actualizar checksum S010 + `row_expectations` modulo 27→28 | `catalog_profiles.py` |
| 2.3 | (Opcional) Registrar S021 si se mantiene ruta corta en S010 | `catalog_profiles.py` |
| 2.4 | Validar provision Dedicated de prueba | pipeline DTSP |

**Gate:** Dedicated nueva recibe `permiso` cfg.* y `modulo` CFG.

---

## Fase 3 — Onboarding / trial

| Orden | Trabajo | Archivo(s) |
|-------|---------|------------|
| 3.1 | `TRIAL_MODULES` += `"CFG"` | `owner_sync_constants.py` |
| 3.2 | `MIN_HEALTHY_TRIAL_OWNER_MENU_GRANTS` += N menús | mismo |
| 3.3 | Ajustar tests/scripts que hardcodean 18 o lista de 3 módulos | tests + scripts |
| 3.4 | **No** tocar Manager/User constants | — |
| 3.5 | Revisar SQL legacy repair scope si aplica CFG | `onboarding_menu_bootstrap_service` / repair scripts |

**Gate:** Onboarding trial inserta `cliente_modulo(CFG)` + OwnerSync RMP > 0 para CFG.

---

## Fase 4 — Tenants existentes (operación)

| Orden | Trabajo | Notas |
|-------|---------|-------|
| 4.1 | Backfill `cliente_modulo` CFG para tenants activos deseados | Script/repair idempotente (fuera de S068) |
| 4.2 | OwnerSync / repair menu grants por tenant | `repair_tenant_menu_grants` o sync batch |
| 4.3 | Confirmar RP `cfg.*` (S068 ya backfillea ADMIN_TENANT) | Smoke `permissions/me` |

---

## Fase 5 — Validación runtime

| Orden | Prueba |
|-------|--------|
| 5.1 | Login ADMIN_TENANT → `GET /auth/menu` contiene `CFG` + ruta `/app/cfg/secuencias` |
| 5.2 | `GET /auth/permissions/me` contiene `cfg.secuencias.consultar` |
| 5.3 | Login MANAGER → menú **sin** CFG |
| 5.4 | API `GET /api/v1/cfg/secuencias` 200 con permiso |
| 5.5 | Dedicated: repetir 5.1–5.4 |
| 5.6 | Impersonación: menú incluye CFG (RMP admin) |

---

## Fase 6 — Cierre

| Orden | Trabajo |
|-------|---------|
| 6.1 | Actualizar evidence JSON / staging validation |
| 6.2 | Checklist regresión (`08`) PASS |
| 6.3 | No mergear cambios OpenAPI/contratos/FE |

---

## Qué no hacer en ninguna fase

- Mover rutas a `/admin`
- Meter CFG en `S020` / `SYS_ADMIN.TENANT.*` como único contenedor
- Añadir CFG a Manager/User Standard
- Crear permisos nuevos (`cfg.ver`, etc.)
- Modificar handlers `/cfg` o OpenAPI
- Confiar solo en R020 para `cliente_modulo` CFG
