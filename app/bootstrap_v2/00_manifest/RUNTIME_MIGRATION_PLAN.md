# RUNTIME MIGRATION PLAN

**Objetivo:** eliminar dependencia operativa de `S030`, `R010`, `R020` y `S040–S066` sin romper onboarding, login admin sin empresa, menú SYS_ADMIN ni autorización API.

**Restricción de esta fase:** solo plan; **sin cambios de código/SQL** hasta aprobación explícita.

---

## Fase 0 — Baseline (hoy)

### Bootstrap mínimo obligatorio (sin cambios propuestos)

```
01_schema/  V010 → V020 → V030
02_catalog/ S010 → S020 (menús) → [omitir S030, S040–S066 en PROD con sync]
03_runtime/ [omitir R010, R020 si se implementa Fase 2–3]
startup/    FastAPI arranque (permission_sync obligatorio)
onboarding/ API crear cliente
```

### Comportamiento actual tras crear tenant (sin SQL runtime)

| Funcionalidad | Estado |
|---------------|--------|
| Login admin sin empresa | ✅ (auth + `usuario_rol.empresa_id NULL`) |
| JWT / refresh | ✅ |
| Llamar API `org.*`, `inv.*`, … | ❌ sin `rol_permiso` |
| Llamar API `admin.*`, `tenant.*` | ❌ sin `rol_permiso` |
| Ver menú SYS_ADMIN | ❌ sin `cliente_modulo` SYS_ADMIN |
| Ver menú ORG/INV | ❌ sin activar módulos |

---

## Fase 1 — Permisos: backend como única fuente (`permiso`)

### 1.1 Cambios backend (futuros)

| # | Tarea | Archivo(s) | Criterio de aceptación |
|---|-------|------------|------------------------|
| 1.1 | Registry estático `CORE_PERMISSIONS` | `permission_registry.py` o módulo `core_permissions.py` | Incluir al menos `core.app.acceder` |
| 1.2 | Excluir de desactivación permisos “grant-only” | `permission_sync_service.py` | Lista blanca: `core.app.acceder` (y otros sin endpoint si aplica) |
| 1.2b | Opcional: registrar `admin.*`, `tenant.*`, `modulos.*` vía metadata en routers | endpoints existentes | Evitar depender solo del escaneo `require_permission` |
| 1.3 | Documentar en manifest: PROD no ejecuta S040–S066 | `BOOTSTRAP_ORDER.md` | Cold-install: solo schema + S010 + S020 menús + startup |

### 1.2 SQL a deprecar (catálogo)

| Script | Acción |
|--------|--------|
| `S030__seed_permisos_core.sql` | Deprecar tras 1.1 |
| `permisos_rbac/S040–S066` | Mover a `02_catalog/_legacy/` o marcar `DEPRECATED` en manifest |
| `S067` | Mantener skip |

### 1.3 Validación ejecutable

```text
1. BD vacía → V010, V020, V030, S010, S020 (solo menús SYS_ADMIN)
2. NO ejecutar S030, S040–S066, R010, R020
3. Arrancar FastAPI → logs [RBAC] Permission synced (N ≈ 113)
4. SELECT COUNT(*) FROM permiso WHERE es_activo=1 → N
5. Crear tenant vía API onboarding
6. Verificar permiso activo admin.usuario.leer existe (sync), rol_permiso aún vacío (esperado hasta Fase 2)
```

---

## Fase 2 — Grants: `rol_permiso` en onboarding (reemplaza R010 + S020§6)

### 2.1 Servicio nuevo o extensión onboarding

**Responsabilidad:** tras crear `ADMIN_TENANT`, insertar `rol_permiso` mínimos.

| Permiso | Motivo |
|---------|--------|
| `core.app.acceder` | Contrato histórico R010 (opcional si no se usa en API) |
| `admin.usuario.leer`, `admin.usuario.crear`, `admin.usuario.actualizar` | Gestión usuarios |
| `admin.rol.leer`, `admin.rol.asignar`, `admin.rol.actualizar` | RBAC UI |
| `tenant.cliente.leer`, `tenant.cliente.actualizar` | Config tenant |
| `modulos.menu.leer`, `modulos.menu.administrar` | Menús/módulos |
| `org.empresa.*` (leer/crear/actualizar) | Primera empresa post-login |

**Implementación sugerida (cuando se codifique):**

- Función `OnboardingRbacGrantService.grant_admin_tenant_bootstrap(cliente_id, admin_rol_id, session)`.
- SQL: `INSERT rol_permiso` con `SELECT permiso_id FROM permiso WHERE codigo IN (...)` y `NOT EXISTS`.
- Ejecutar **después** de `_insertar_roles_base` y **antes** de commit.
- Requiere que **startup/sync** haya corrido al menos una vez en el entorno (tabla `permiso` poblada), **o** insertar permisos faltantes en la misma transacción vía sync inline (más complejo).

### 2.2 Orden operativo PROD recomendado

```text
1. Deploy app (sync puebla permiso)
2. Bootstrap SQL global (S010, S020 menús) una vez
3. Crear tenants vía API (onboarding con grants)
```

### 2.3 SQL a deprecar

| Script | Reemplazo |
|--------|-----------|
| `R010__asignar_core_app_a_roles.sql` | Grant en onboarding + job “reparación” opcional para roles legacy |
| S020 secciones 5–6 (`admin.tenant.access`, `rol_permiso`) | Grants con códigos reales de API |

### 2.4 Job de reparación (opcional, transitorio)

Para tenants creados antes de Fase 2:

- Endpoint interno o script Python que ejecute la misma lógica que R010 + grants admin para `codigo_rol = 'ADMIN_TENANT'`.
- Idempotente (`NOT EXISTS`).

---

## Fase 3 — Módulos: `cliente_modulo` en onboarding (reemplaza R020)

### 3.1 Cambios backend (futuros)

| # | Tarea | Detalle |
|---|-------|---------|
| 3.1 | Activar módulos por defecto al crear tenant | `ClienteOnboardingService` o llamada a `ClienteModuloService.activar_modulo_cliente` |
| 3.2 | Módulos mínimos | `SYS_ADMIN` (codigo), `ORG` (codigo) — resolver `modulo_id` por `SELECT codigo FROM modulo` |
| 3.3 | No depender de R020 batch sobre todos los clientes | R020 solo útil para migración masiva legacy |

### 3.2 SQL a deprecar

| Script | Reemplazo |
|--------|-----------|
| `R020__relacion_sys_admin_cliente_modulo.sql` | Onboarding activa SYS_ADMIN (+ ORG) |

### 3.3 Validación ejecutable

```text
1. POST crear cliente (onboarding)
2. SELECT * FROM cliente_modulo WHERE cliente_id = @id
   → filas SYS_ADMIN y ORG, esta_activo=1
3. Login admin → GET /auth/menu (o equivalente)
   → módulos SYS_ADMIN visibles (as_tenant_admin o rol_menu_permiso)
```

---

## Fase 4 — Alinear menú UI con API (`rol_menu_permiso` vs `rol_permiso`)

**Problema auditado:** `aplicar_plantillas_roles` solo escribe `rol_menu_permiso`; API usa `rol_permiso`.

### Opciones (elegir una en implementación)

| Opción | Descripción | Esfuerzo |
|--------|-------------|----------|
| A | Al activar módulo, además de plantillas menú, asignar `rol_permiso` leyendo mismos códigos que sync | Medio |
| B | Unificar menú: filtrar por `effective_permission_codes` (ya parcial en `MenuResolverService`) y reducir dependencia de `rol_menu_permiso` | Alto |
| C | Mantener dual; onboarding grant admin + plantillas solo para módulos activados manualmente | Bajo (status quo mejorado) |

**Recomendación plan:** **A + C** en corto plazo; **B** como refactor posterior.

---

## Fase 5 — Limpieza bootstrap manifest

### Estructura objetivo

```text
01_schema/          V010, V020, V030 (sin cambio)
02_catalog/
  S010__modulo_menu.sql     PERMANENTE
  S020__sys_admin_menu.sql  PERMANENTE (solo DDL menú; sin MERGE permiso/rol_permiso)
  _legacy/
    S030, S040–S066           DEPRECATED
03_runtime/
  _legacy/
    R010, R020                DEPRECATED
startup/              (documentación; código en app/core/authorization)
onboarding/           (documentación; código en ClienteOnboardingService)
```

### Actualizar documentos

- `BOOTSTRAP_ORDER.md`: Fase 2 catálogo = S010 + S020 menús; sync en startup.
- `BOOTSTRAP_GAPS.md`: cerrar G-032 cuando S040 deprecado.
- `SOURCE_MAP.json`: marcar `replaced_by` onboarding grants.

---

## Cronograma sugerido

| Sprint | Entregable | Elimina |
|--------|------------|---------|
| S1 | Registry + whitelist sync + manifest PROD sin S040 | Riesgo desactivación; reduce S040 |
| S2 | Onboarding `rol_permiso` grants | R010, S020§6 |
| S3 | Onboarding `cliente_modulo` SYS_ADMIN+ORG | R020 |
| S4 | Job reparación tenants legacy + tests integración | Deuda histórica |
| S5 | Alinear plantillas → `rol_permiso` (opción A) | Hueco menú/API |

---

## Criterios de “hecho” global

- [ ] Crear tenant solo vía API: admin puede `admin.usuario.leer` y `tenant.cliente.leer` sin ejecutar R010/R020.
- [ ] Menú SYS_ADMIN visible sin R020 manual.
- [ ] `SELECT COUNT(*) FROM permiso WHERE es_activo=1` ≈ códigos en registry (± whitelist).
- [ ] No ejecutar S030, S040–S066, R010, R020 en pipeline PROD nuevo.
- [ ] Tests: `tests/integration/test_erp_session_contract.py` o nuevo test onboarding RBAC.

---

## Riesgos de migración

| Riesgo | Mitigación |
|--------|------------|
| Onboarding antes del primer startup (permiso vacío) | Documentar orden: bootstrap schema+catálogo → deploy app → crear tenants |
| Tenants existentes sin grants | Job reparación Fase 2.4 |
| Sync desactiva permisos SQL legacy | No ejecutar S040–S066; whitelist core |
| Admin ve menú pero no API | Fase 4 alinear grants |
