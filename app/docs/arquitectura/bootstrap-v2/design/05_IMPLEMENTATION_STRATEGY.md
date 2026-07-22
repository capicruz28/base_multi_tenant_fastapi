# 05 — Bootstrap V2: Estrategia de implementación incremental

**Etapa:** Diseño TO-BE  
**Restricción:** compatibilidad total AS-IS en cada fase intermedia.

---

## 1. Enfoque general

La implementación Bootstrap V2 seguirá el patrón **Strangler Fig**:

1. Introducir facades V2 **detrás** de orquestadores existentes.
2. Delegar en código AS-IS sin cambiar comportamiento.
3. Mover invocaciones gradualmente a facades.
4. Deprecar (no eliminar) rutas mixtas cuando facades sean equivalentes.

**Prohibido:** big-bang rewrite, cambio de endpoints, split visible onboarding.

---

## 2. Fases incrementales propuestas

### Fase 0 — Baseline (completada)

- Auditoría AS-IS (`bootstrap-v2/01`–`06`)
- Diseño TO-BE (este directorio)
- Estabilización Ola 0 motor + fix auth config session (F19)

**Gate:** tests onboarding/provisioning verdes.

---

### Fase 1 — Empresa Bootstrap facade (sin mover archivos)

**Objetivo:** crear `EmpresaBootstrapService` conceptual que **delegue** a:
- `MinimalErpTenantBootstrapService.ensure_empresa_inicial`
- `MinimalErpTenantBootstrapService.vincular_admin_empresa`
- subset EMPRESA de `_insertar_secuencias_codigo` (56 filas cfg EMPRESA **sin extraer** aún la fila TENANT)

**Alcance Fase 1 vs Fase 4 (cfg split):**

| Aspecto | Fase 1 | Fase 4 |
|---------|--------|--------|
| Facade `EmpresaBootstrapService` | ✓ Creada | Reutilizada |
| Delegación E-ORG, E-LNK | ✓ | Sin cambio |
| cfg EMPRESA (56 filas) | ✓ vía subset de `_insertar_secuencias_codigo` | ✓ vía `seed_cfg_empresa` extraído |
| cfg TENANT (1 fila) | Permanece en caller AS-IS (`_insertar_secuencias_codigo` completo o paso T7) | Extraído a `seed_cfg_tenant` |
| Refactor de `_insertar_secuencias_codigo` | **No** — solo delegación interna | **Sí** — split formal TENANT/EMPRESA |
| Riesgo doble refactor | Evitado: Fase 1 no toca estructura del método seed | Fase 4 completa el split pendiente |

**Regla anti-doble-refactor:** Fase 1 introduce facade y reemplaza **call sites** (orquestador → facade). Fase 4 refactoriza **implementación interna** del seed sin cambiar call sites ya migrados. No repetir extracción de cfg en ambas fases.

**Cambio observable:** ninguno.

**Orquestador:** `ClienteOnboardingService` reemplaza llamadas directas por facade (mismos métodos underneath).

**Gate obligatorio (ver §8):** Fase 1.

---

### Fase 2 — Tenant Bootstrap orchestrator explícito (Shared)

**Objetivo:** extraer secuencia T1–T7 + invocaciones E a método/clase orchestrator; `crear_cliente_con_onboarding` delega.

**Cambio observable:** ninguno.

**Gate obligatorio (ver §8):** Fase 2.

---

### Fase 3 — Tenant Bootstrap orchestrator (Dedicated S7)

**Objetivo:** `execute_tenant_seed_step` enruta E-pasos a `EmpresaBootstrapService`; T-pasos a tenant facade.

**Cambio observable:** ninguno.

**Preservar:** markers `seed_org_empresa`, `seed_codigo_secuencias` (nombres AS-IS en `tenant_seed_profiles`).

**ADJ-07 (deuda AS-IS — opcional):** cerrar gap `cliente_auth_config` Dedicated es **fix de paridad CP**, no requisito Bootstrap V2 Fases 1–4. Si se implementa en Fase 3, requiere gate ADJ-07 propio (ver §8). No altera UX Dedicated.

**Gate obligatorio (ver §8):** Fase 3.

---

### Fase 4 — Split cfg seed (interno)

**Objetivo:** `_insertar_secuencias_codigo` divide en:
- `seed_cfg_tenant(session, cliente_id)` → Tenant facade
- `seed_cfg_empresa(session, cliente_id, empresa_id)` → Empresa facade

**Relación con Fase 1:** Fase 1 ya enruta cfg EMPRESA vía facade; Fase 4 **solo** extrae implementación interna del método monolítico. Call sites migrados en Fase 1 **no se re-tocan**.

**Cambio observable:** ninguno (57 filas totales, mismos valores).

**Gate obligatorio (ver §8):** Fase 4.

---

### Fase 5 — Multi-empresa ORG hook (futuro)

**Objetivo:** módulo ORG invoca `EmpresaBootstrapService` modo `ADDITIONAL` al crear empresa N>1.

**Prerequisito:** ORG módulo operativo.

**Cambio observable onboarding inicial:** ninguno.

**Nuevo observable:** empresa adicional tiene cfg EMPRESA automáticamente.

---

### Fase 6 — BootstrapExtensionRegistry (futuro)

**Objetivo:** registrar Warehouse/PV bootstraps como plug-ins.

**Sin modificar** Tenant/Empresa core.

---

## 3. Qué NO se hace en ninguna fase intermedia

| Prohibido | Razón |
|-----------|-------|
| Cambiar `POST /clientes/` request/response | DA-03 |
| Eliminar creación automática EMP001 | Principio fundamental |
| Separar onboarding en 2 API calls | UX |
| Renombrar step codes Dedicated públicos | Contratos saga |
| Modificar DDL / migraciones para V2 | Fuera alcance |
| Eliminar código AS-IS | Marcar deprecated si aplica |

---

## 4. Estrategia de compatibilidad

### 4.1 Shared

| Aspecto | Preservación |
|---------|--------------|
| TX única ADMIN | Facades reciben `session` existente |
| Rollback atómico | Sin commit intermedio en onboarding |
| Orden pasos | Ver `02` secuencia normativa |
| Auth config | Misma session propagation (F19) |

### 4.2 Dedicated

| Aspecto | Preservación |
|---------|--------------|
| S1–S10 orden | Sin cambio |
| Markers S7 | Nombres step_code AS-IS |
| Row expectations | Recalcular solo si split verificación (fase 4+) |
| Sesión DP | Empresa facade usa `provisioning_dedicated_session` |
| Seed ERP S7 | Paridad semántica con Shared (roles, EMP001, admin, RBAC, cfg×57) |
| `cliente_auth_config` CP | **Deuda AS-IS ADJ-07** — no bloquea compatibilidad V2; cierre opcional Fase 3 |

### 4.3 Platform

| Aspecto | Preservación |
|---------|--------------|
| CLI bootstrap_platform | Sin cambio en fases 1–4 |
| SUPERADMIN_CLIENTE_ID | Aislado de tenant bootstraps |

---

## 5. Criterios de aceptación por fase

| Fase | Criterio |
|------|----------|
| 1 | Facade delega 100% AS-IS; 0 diff comportamental tests |
| 2 | Orchestrator Shared; API contract unchanged |
| 3 | Dedicated S7 parity; saga e2e green |
| 4 | cfg split; 57 rows count unchanged |
| 5 | ORG empresa N tiene cfg; onboarding unchanged |
| 6 | Extension registered; core bootstraps untouched |

---

## 6. Rollback

Cada fase es **reversible** mientras facades deleguen en métodos originales:
- Fase 1–4: revertir a llamadas directas AS-IS
- Sin migraciones de datos requeridas

---

## 7. Riesgos mitigados por estrategia incremental

| Riesgo AS-IS (audit) | Mitigación V2 |
|----------------------|---------------|
| R-T1 FK cfg↔empresa | Empresa facade garantiza E-ORG antes E-CFG |
| R-T2 TX Shared | Orchestrator no añade commits |
| R-T3 Dedicated markers | Fase 3 preserva nombres |
| R-T5 admin sin default | Orden normativo `02` inmutable |
| G2 multi-empresa | Fase 5 ORG hook |
| G1 auth Dedicated | Fase 3 opcional ADJ-07 (deuda AS-IS, no blocker V2) |

---

## 8. Gates obligatorios de pruebas por fase

Cada fase **no avanza** hasta cumplir su gate. Tests mínimos obligatorios:

| Fase | Gate ID | Tests / verificaciones obligatorias | Bloqueante |
|------|---------|-------------------------------------|------------|
| 0 | G0 | Suite onboarding/provisioning verde (baseline post F19) | Sí |
| 1 | G1 | `test_f4_07_dedicated_tenant_seed_service`; `test_codigo_engine_f17d_full_cfg_seed`; Shared onboarding e2e (57 cfg, EMP001, admin); INV-01 verificado (E1 antes T3) | Sí |
| 2 | G2 | `test_f4_*` onboarding Shared; diff TX equivalente; `ClienteOnboardingResult` idéntico | Sí |
| 3 | G3 | `test_f4_08_dedicated_orchestrator`; `test_f4_09_dedicated_activation`; provisioning e2e harness Dedicated; markers S7 preservados | Sí |
| 3 | G3-ADJ07 | Auth config CP Dedicated presente post-saga | **No** — solo si ADJ-07 implementado |
| 4 | G4 | Conteo cfg: 1 TENANT + 56 EMPRESA = 57; valores idénticos pre/post split; F17D + F4-07 verdes | Sí |
| 5 | G5 | ORG empresa N>1 con cfg EMPRESA; onboarding inicial sin regresión | Sí |
| 6 | G6 | Extension registry smoke; core bootstraps sin modificación | Sí |

**Reglas gates:**

| Regla | Descripción |
|-------|-------------|
| GT-01 | Gate de fase N debe estar verde antes de iniciar fase N+1 |
| GT-02 | Regresión en gate → rollback fase y fix antes de continuar |
| GT-03 | Gates G3-ADJ07 y superiores a Fase 4 son independientes del criterio "cero cambio UX" |

---

*Resumen ejecutivo: `06`.*
