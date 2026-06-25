# IAM Session Management V2 — Plan Oficial de Ejecución Cluster 8 (RC2)

**Ticket:** `IAM-BE-PREF14-C8-EXEC-01`  
**Versión:** 1.1.0  
**Estado:** Documento oficial de ejecución (post-auditoría independiente)  
**Fecha:** 2026-06-22  
**Cluster:** **C8 — Testing Gate + RC2**

**Documento maestro congelado:** Plan Maestro de Implementación por Componentes **V1.0**  
**Auditoría base:** `IAM-BE-PREF14-C8-AUDIT-01` (veredicto **GO WITH MINOR OBSERVATIONS**)  
**Enmiendas:** Incorporación auditoría arquitectónica independiente v1.0 → v1.1.0  
**Hallazgos:** P0-07, P1-09, P1-10  
**Restricción:** Plan operativo de ejecución únicamente. Sin implementación de runtime.

---

## Índice

1. [Objetivo](#1-objetivo)  
2. [Alcance](#2-alcance)  
3. [Exclusiones](#3-exclusiones)  
4. [Dependencias](#4-dependencias)  
5. [Orden exacto de implementación](#5-orden-exacto-de-implementación)  
6. [Archivos autorizados](#6-archivos-autorizados)  
7. [Archivos prohibidos](#7-archivos-prohibidos)  
8. [Harness de integración](#8-harness-de-integración)  
9. [Fixtures necesarios](#9-fixtures-necesarios)  
10. [Seeds necesarios](#10-seeds-necesarios)  
11. [Estrategia oficial de teardown](#11-estrategia-oficial-de-teardown)  
12. [Configuración SQL Server](#12-configuración-sql-server)  
13. [Configuración Redis](#13-configuración-redis)  
14. [Configuración Feature Flag](#14-configuración-feature-flag)  
15. [Configuración CI](#15-configuración-ci)  
16. [Alineación Implementation Plan §12.1](#16-alineación-implementation-plan-121)  
17. [Tests Integration obligatorios](#17-tests-integration-obligatorios)  
18. [Tests Concurrency obligatorios](#18-tests-concurrency-obligatorios)  
19. [Tests Multi-tenant obligatorios](#19-tests-multi-tenant-obligatorios)  
20. [Tests E2E obligatorios](#20-tests-e2e-obligatorios)  
21. [Tests Cutover obligatorios](#21-tests-cutover-obligatorios)  
22. [Escenarios negativos](#22-escenarios-negativos)  
23. [Escenarios rollback](#23-escenarios-rollback)  
24. [Criterios RC2](#24-criterios-rc2)  
25. [Gates de salida](#25-gates-de-salida)  
26. [Code Freeze](#26-code-freeze)  
27. [Preparación F14](#27-preparación-f14)  
28. [Riesgos](#28-riesgos)  
29. [Estrategia de rollback del cluster](#29-estrategia-de-rollback-del-cluster)

---

## 1. Objetivo

Construir la **evidencia objetiva pre-cutover** requerida por el Plan Maestro V1.0 para:

- Cerrar **P0-07** (suite Integration/E2E + cutover smoke pre-F14).  
- Cerrar **P1-09** (integration C18 con SQL Server real y UPDLOCK).  
- Cerrar **P1-10** (aislamiento multi-tenant tablas/queries V3).  
- Declarar oficialmente **RC2**.  
- Habilitar **Code Freeze** y preparación de **F14** (sin ejecutar F14 en este cluster).

**Naturaleza del cluster:** exclusivamente **tests + infraestructura de QA**. Cero cambios en runtime auth congelado post-C7.

---

## 2. Alcance

### Incluido

| Área | Detalle |
|------|---------|
| Harness | `conftest` IAM V2, markers pytest, helpers seed/cleanup/teardown |
| Integration C18 | `create` / `rotate` / `revoke` / `revoke_all` / `replay` en BD real |
| Integration cleanup V2 | Purge tokens/sesiones en BD real (evidencia C7; archivo dedicado) |
| Tenant isolation V3 | C15, C16, C17, C18 + endpoints revoke cross-tenant |
| E2E smoke | Login → refresh → logout flag ON; flujos críticos M1–M10 (subconjunto automatizado) |
| Cutover smoke pre-F14 | Flag OFF→ON, coexistencia V1/V3, regresión V1 |
| Regresión | Suite §12.2 Implementation Plan + unitarios V2 + legacy V1 |
| CI | Job o pipeline documentado para suite integration (mínimo local gate obligatorio) |

### Estado de entrada verificado

| Hito | Estado |
|------|--------|
| F0–F13 | ✅ Completos |
| C1–C5 + C4T + HA1 | ✅ |
| C7 (P1-04 cleanup) | ✅ |
| RC1 | ✅ Declarado |
| Tests unitarios V2 | ✅ 269/269 verdes |
| `tests/integration/test_iam_sessions_v2_*` | ❌ 0 archivos (gap a cerrar) |

---

## 3. Exclusiones

| Exclusión | Motivo |
|-----------|--------|
| **Implementación runtime** auth/sesiones | Congelado C1–C7 |
| **Cluster 9 / F15** | P1-01, P1-02, P1-08 (SSO V2, refactor C18 ownership) |
| **F14 cutover producción** | Posterior a RC2 + Code Freeze |
| **Fix manifest V031** | Deuda P0-01 operativa; prerrequisito entorno, no código C8 |
| **E2E SSO Azure/Google** | Rama V1; P1-08 → F15 |
| **Impersonation E2E HTTP obligatorio** | Cubierto por unitarios F11 (ver §16) |
| **Modificación OpenAPI / DTOs** | Fuera alcance |
| **Nuevos endpoints HTTP** | Fuera alcance |
| **Performance / load testing** | Fuera alcance RC2 |
| **Modificación `tests/test_tenant_isolation.py` legacy** | Reemplazado por archivo nuevo V3 (ver §6, §24) |

---

## 4. Dependencias

### Bloqueantes (cumplidas — ✅)

| Dependencia | Estado |
|-------------|--------|
| RC1 declarado (C1–C5 + C4T + HA1) | ✅ |
| C7 mergeado (P1-04) | ✅ |
| Suite unitaria V2 verde (269+) | ✅ |
| Auditoría C8 con veredicto GO WITH MINOR OBSERVATIONS | ✅ |
| Enmiendas v1.1.0 incorporadas | ✅ |

### Prerrequisitos de entorno (no código)

| Prerrequisito | Responsable | Verificación |
|---------------|-------------|--------------|
| DDL **V031** aplicado en BD de pruebas | DevOps / QA | `test_f1_orm_columns_match_database_schema` |
| SQL Server accesible desde runner tests | QA | `DB_*` en `.env` test |
| Redis accesible (E-03) o skip documentado | QA | `redis-cli ping` |
| Seeds §10 completos (2 tenants, 2 empresas, admin revoke) | QA harness | Fixtures pre-flight |

### Desbloquea

```
C8 merge → RC2 declarado → Code Freeze → F14 (ticket separado)
```

---

## 5. Orden exacto de implementación

### Fase 0 — Infraestructura QA (bloqueante)

| Paso | Entregable |
|------|------------|
| 0.1 | Markers pytest: `iam_v2_integration`, `requires_sqlserver`, `requires_redis`, `slow` |
| 0.2 | `tests/integration/conftest_iam_sessions_v2.py` |
| 0.3 | `tests/integration/helpers/iam_v2_teardown.py` (DELETE directo — §11) |
| 0.4 | Checklist pre-flight V031 + env vars |
| 0.5 | Helpers: `skip_if_no_db()`, `skip_if_no_redis()`, `iam_v2_flag_on()` |

### Fase 1 — P1-10 Tenant isolation V3

| Paso | Entregable |
|------|------------|
| 1.1 | `tests/integration/test_iam_sessions_v2_tenant_isolation.py` |
| 1.2 | Casos MT-01 … MT-07 (§19) |
| 1.3 | Gate G1 verde |

### Fase 2 — P1-09 Integration C18 + cleanup BD

| Paso | Entregable |
|------|------------|
| 2.1 | `tests/integration/test_iam_sessions_v2_f4_tx_integration.py` |
| 2.2 | Casos I-01 … I-07 + R-01 … R-04 (§17, §23) |
| 2.3 | `tests/integration/test_iam_sessions_v2_cleanup_integration.py` |
| 2.4 | Casos CL-01 … CL-03 (§17) |
| 2.5 | Casos CC-01, CC-03, CC-04, CC-05 (§18); CC-02 opcional |
| 2.6 | Gate G2 verde |

### Fase 3 — P0-07 E2E + Cutover pre-F14

| Paso | Entregable |
|------|------------|
| 3.1 | `tests/integration/test_iam_sessions_v2_e2e_smoke.py` |
| 3.2 | Casos E-01 … E-13 (§20) |
| 3.3 | `tests/integration/test_iam_sessions_v2_cutover_pre_f14.py` |
| 3.4 | Casos CT-01 … CT-04 (§21) |
| 3.5 | Evidencia M1–M10 manual staging (ticket RC2) |
| 3.6 | Gate G3, G4 verdes |

### Fase 4 — Regresión + CI + RC2

| Paso | Entregable |
|------|------------|
| 4.1 | Ampliar `scripts/run_rc_validation_pipeline.py` (recomendado) |
| 4.2 | Job CI integration (recomendado) |
| 4.3 | Suite §12.2 completa verde (§24) |
| 4.4 | **Declaración RC2** |

**Regla:** no avanzar de fase sin gate de fase verde.

---

## 6. Archivos autorizados

### Crear (obligatorio)

| Archivo | Fase |
|---------|------|
| `tests/integration/conftest_iam_sessions_v2.py` | 0 |
| `tests/integration/helpers/iam_v2_teardown.py` | 0 |
| `tests/integration/test_iam_sessions_v2_tenant_isolation.py` | 1 |
| `tests/integration/test_iam_sessions_v2_f4_tx_integration.py` | 2 |
| `tests/integration/test_iam_sessions_v2_cleanup_integration.py` | 2 |
| `tests/integration/test_iam_sessions_v2_e2e_smoke.py` | 3 |
| `tests/integration/test_iam_sessions_v2_cutover_pre_f14.py` | 3 |

> **Nota nomenclatura:** el módulo cutover se nombra `cutover_pre_f14` para distinguirlo del cutover productivo F14.

### Modificar (autorizado)

| Archivo | Fase | Naturaleza |
|---------|------|------------|
| `pytest.ini` | 0 | Markers |
| `tests/conftest.py` | 0 | Registro mínimo fixtures IAM |
| `scripts/run_rc_validation_pipeline.py` | 4 | Suite §12.2 |
| `.github/workflows/ci.yml` | 4 | Job integration (recomendado) |

### No modificar

| Archivo | Motivo |
|---------|--------|
| `tests/test_tenant_isolation.py` | Legacy V1; **reemplazo oficial** = `test_iam_sessions_v2_tenant_isolation.py` (§24 RC2-04b) |

---

## 7. Archivos prohibidos

| Archivo / área | Motivo |
|----------------|--------|
| `app/modules/auth/application/services/auth_service.py` | Congelado C5 |
| `app/modules/auth/presentation/endpoints.py` | Congelado C5 |
| `app/modules/auth/application/services/session_rotation_service.py` | Congelado C3 |
| `app/modules/auth/application/services/session_revocation_service.py` | Congelado C4 |
| `app/modules/auth/application/services/session_creation_service.py` | Fuera alcance |
| `app/infrastructure/database/queries/auth/session/session_transaction_core.py` | Congelado C2 |
| `app/infrastructure/database/queries/auth/session/user_session_queries_core.py` | Congelado C7 |
| `app/infrastructure/database/queries/auth/session/refresh_token_queries_core.py` | Congelado C7 |
| `app/modules/auth/application/services/refresh_token_cleanup_job.py` | Congelado C7 |
| `app/modules/auth/application/services/password_change_service.py` | Congelado HA1 |
| `app/core/security/jwt.py` | Prohibido |
| `app/core/config.py` | Prohibido |
| `app/bootstrap_v2/**` | Prohibido |
| DTOs / OpenAPI schemas auth | Prohibido |
| `session_v2_feature.py` | Prohibido |

**Excepción formal:** defecto P0 bloqueante en C18 descubierto en integration → ticket `IAM-BE-PREF14-C8-HOTFIX-XX` fuera de C8, con aprobación Release Manager.

---

## 8. Harness de integración

### Principios

1. **Opt-in:** `@pytest.mark.iam_v2_integration` + `@pytest.mark.requires_sqlserver`.  
2. **Skip seguro:** `SKIP_DB_INTEGRATION_TESTS=1` o credenciales ausentes → `pytest.skip`.  
3. **Teardown directo:** §11 — **nunca** depender del cleanup job entre tests.  
4. **BD dedicada:** clone staging / `*_test`; no producción.  
5. **Dual flag:** suites `flag_on` / `flag_off` separadas.

### Estructura

```
tests/integration/conftest_iam_sessions_v2.py
tests/integration/helpers/iam_v2_teardown.py
├── iam_v2_db_available
├── iam_v2_schema_ready
├── iam_v2_tenant_a / tenant_b
├── iam_v2_user_a / user_b / user_admin_a
├── iam_v2_credentials_a / credentials_admin_a
├── iam_v2_empresa_a1 / empresa_a2          # dos empresas tenant A
├── iam_v2_flag_all_tenants_on              # flag ON + allowlist vacía
├── iam_v2_flag_allowlist_on                # flag ON + allowlist explícita
├── iam_v2_flag_off
├── iam_v2_tenant_context_a
├── iam_v2_uow
├── iam_v2_http_client
├── iam_v2_redis_available
└── iam_v2_teardown_sessions                # §11 DELETE directo
```

### Comando local canónico (gate RC2)

```text
set SKIP_DB_INTEGRATION_TESTS=
set IAM_SESSION_MANAGEMENT_V2_ENABLED=true
set IAM_SESSION_V2_TENANT_ALLOWLIST=

pytest tests/unit/test_iam_sessions_v2_* tests/integration/test_iam_sessions_v2_* -v
pytest tests/unit/test_iam_sessions_* -v
```

---

## 9. Fixtures necesarios

| Fixture | Descripción |
|---------|-------------|
| `iam_v2_db_available` | Verifica `DB_*`, pyodbc/SQLAlchemy |
| `iam_v2_schema_ready` | Tablas V3 presentes (V031) |
| `iam_v2_tenant_a` / `tenant_b` | `cliente_id` distintos |
| `iam_v2_user_a` / `user_b` | Usuario local activo por tenant |
| `iam_v2_user_admin_a` | Usuario admin tenant A con permiso revoke |
| `iam_v2_credentials_a` | Login password usuario estándar |
| `iam_v2_credentials_admin_a` | Login password admin |
| `iam_v2_empresa_a1` / `empresa_a2` | Dos empresas activas tenant A |
| `iam_v2_flag_all_tenants_on` | `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` + allowlist **vacía** |
| `iam_v2_flag_allowlist_on` | Flag ON + allowlist con `tenant_a` únicamente |
| `iam_v2_flag_off` | Flag global `false` |
| `iam_v2_tenant_context_a` | `TenantContext` + set/reset |
| `iam_v2_uow` | `UnitOfWork(client_id=tenant_a)` |
| `iam_v2_http_client` | TestClient / AsyncClient |
| `iam_v2_redis_available` | Skip si Redis no responde |
| `iam_v2_teardown_sessions` | Teardown §11 por `usuario_id` / `session_id` |

---

## 10. Seeds necesarios

### Por entorno de pruebas (mínimo)

| Entidad | Tenant A | Tenant B | Notas |
|---------|----------|----------|-------|
| `cliente` | `TENANT_IAM_V2_A` | `TENANT_IAM_V2_B` | Activos, `shared` |
| `usuario` estándar | `iam_v2_user_a` | `iam_v2_user_b` | `proveedor_autenticacion=local`, password conocido |
| `usuario` admin | `iam_v2_admin_a` | — | Rol con permisos revoke admin |
| `org_empresa` | **2 empresas** (`empresa_a1`, `empresa_a2`) | ≥1 empresa | E-09 requiere 2 en tenant A |
| `usuario_empresa` | vínculos a ambas empresas | vínculo default | E-08/E-09 |
| RBAC | `auth.sessions.revoke_admin` (o permiso equivalente canónico) | — | E-06 admin revoke |
| RBAC estándar | login + list sessions self | idem | E-04, E-05 |

### Datos creados por tests (no seed manual)

- `user_session`, `token_family`, `refresh_tokens` V3 → vía login E2E o C18.  
- Sesión V1 legacy para CT-03 → procedimiento §21 (insert controlado en test).

### Script de referencia

Reutilizar onboarding/bootstrap existente. SQL idempotente documentado en ticket RC2 si no hay script.

---

## 11. Estrategia oficial de teardown

### Regla absoluta

**Los tests de C8 NO deben invocar `RefreshTokenCleanupJob` ni `purge_*_core` para limpiar datos entre casos.**

Motivo: retención forense C7 — tokens 90d, sesiones cerradas 90d, familias comprometidas hasta 365d. El job no eliminará filas de test recientes y contaminará la BD.

### Procedimiento oficial (`iam_v2_teardown.py`)

Orden DELETE respetando FK (`refresh_tokens` → `token_family` → `user_session`):

```text
1. DELETE refresh_tokens WHERE cliente_id = :tenant AND usuario_id IN (:test_users)
2. DELETE token_family   WHERE cliente_id = :tenant AND usuario_id IN (:test_users)
3. DELETE user_session   WHERE cliente_id = :tenant AND usuario_id IN (:test_users)
```

Para tests de purge (CL-01…CL-03): crear filas con `revoked_at` / `used_at` / `compromised_at` **artificialmente antiguos** (>90d / >365d) en el propio test, o usar transacción rollback cuando el caso lo permita.

### Fixture

- `iam_v2_teardown_sessions` — `autouse=True` en módulos integration IAM V2.  
- Parámetro: lista `usuario_id` registrados por el test en `request.node.iam_v2_users`.

### Prohibido en teardown

- `RefreshTokenCleanupJob.cleanup_single_tenant()`  
- Confiar en `purge_expired_tokens_core` / `purge_closed_sessions_core` para cleanup entre tests

---

## 12. Configuración SQL Server

```text
DB_SERVER=<host>
DB_PORT=1433
DB_USER=<user>
DB_PASSWORD=<secret>
DB_DATABASE=<bd_test_con_V031>
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_ADMIN_*=<bd_central>
SKIP_DB_INTEGRATION_TESTS=     # vacío o false para C8
ENABLE_CONNECTION_POOLING=false  # recomendado en tests
```

Verificación: `test_f1_orm_columns_match_database_schema`.

Multi-DB: mínimo 1 caso en shared-DB; multi-DB documentado como opcional RC2.

---

## 13. Configuración Redis

```text
ENABLE_REDIS_CACHE=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

| Test | Redis |
|------|-------|
| E-03 | **Requerido** o `@pytest.mark.skip(reason="Redis no disponible")` |
| Resto E2E | Opcional |
| Integration C18 / tenant / cleanup | No requerido |

E-03 debe verificar blacklist access (y preferiblemente clave `session:access_jti:{session_id}` cuando `sid` presente).

---

## 14. Configuración Feature Flag

### Semántica oficial (código `session_v2_feature.py`)

| Condición | V2 activo para tenant |
|-----------|----------------------|
| `IAM_SESSION_MANAGEMENT_V2_ENABLED=false` | **Nadie** |
| `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` + allowlist **vacía** | **Todos los tenants** |
| `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` + allowlist con UUIDs | **Solo tenants listados** |
| `cliente_id=None` | **Nadie** |

### Perfiles de test

| Perfil | Env | Uso |
|--------|-----|-----|
| **Todos V2** | `ENABLED=true`, `ALLOWLIST=` (vacío) | E-01…E-13, I-*, MT-*, CT-01/02 |
| **Allowlist parcial** | `ENABLED=true`, `ALLOWLIST=<tenant_a>` | CT-04 |
| **V1** | `ENABLED=false` | E-12, CT-01 |

### Fixtures

- `iam_v2_flag_all_tenants_on` → flag true + allowlist vacía (CT-01/02 **no** usan este perfil para validar V1).  
- `iam_v2_flag_allowlist_on` → flag true + solo `tenant_a` en allowlist.  
- `iam_v2_flag_off` → flag false.

**CT-04:** con allowlist explícita (`tenant_a` únicamente), login V2 en `tenant_b` debe seguir rama **V1** (`RefreshTokenService`), sin filas en `user_session` V3.

---

## 15. Configuración CI

### Estado actual

CI ejecuta solo `tests/unit/` — insuficiente para RC2 automatizado.

### Objetivo C8

Job `iam-v2-integration` con Redis service + runner con SQL Server y V031.

### Alternativa aceptable RC2

Runner self-hosted **o** gate manual documentado con salida §12.2 adjunta + RC2-07 + RC2-09 sign-off.

**Mínimo no negociable:** suite §12.2 verde en entorno acordado antes de declarar RC2.

---

## 16. Alineación Implementation Plan §12.1

### Leyenda

| Símbolo | Significado |
|---------|-------------|
| **C8** | Implementa este cluster (integration/E2E) |
| **UNIT** | Cubierto por unitarios F7–F13 existentes; no duplicar en C8 salvo evidencia BD |
| **MANUAL** | M1–M10 staging con evidencia ticket |
| **F15** | Fuera alcance |

### Tabla de trazabilidad §12.1

| §12.1 | Escenario | Cobertura RC2 | Evidencia |
|-------|-----------|---------------|-----------|
| F1 | ORM columns match DDL | **UNIT** + G0 schema check | `test_iam_sessions_v2_f1_tables` |
| F4 | create+rotate integration BD | **C8** | I-01…I-07, CC-* |
| F4 | create rollback on failure | **C8** + **UNIT** | R-01, `test_f4b_create_session_rollback_*` |
| F7 | Session limit evicts oldest | **UNIT** | `test_iam_sessions_v2_f7_services` |
| F7 | create TTL remember_me | **UNIT** | `test_iam_sessions_v2_f7_services` |
| F8 | Rotate success | **UNIT** + **C8** | F8 + I-03 |
| F8 | Replay `is_used=1` | **UNIT** + **C8** + **E2E** | F8 + I-07 + E-07 |
| F8 | Double concurrent refresh | **C8** | CC-01 |
| F8 | Idle timeout revokes before rotate | **UNIT** + negativo | F8 + N-02 |
| F9 | Logout idempotent | **UNIT** + **E2E** | F9 + E-03/N-07 |
| F9 | Self-revoke 404 cross-user | **UNIT** | F9, F12 |
| F9 | Logout all count | **UNIT** + **E2E** | F9 + E-11 |
| F9 | Admin revoke 404 closed | **UNIT** | F9, F12 |
| F10 | Login→refresh→logout E2E | **C8** | E-01, E-02, E-03 |
| F10 | Impersonation refresh blocked 403 | **UNIT** | `test_iam_sessions_v2_f11_secondary_flows` |
| F11 | Password change revokes all + new session | **UNIT** + **E2E** | F11 + E-10 |
| F11 | Empresa seleccionar updates session | **UNIT** + **E2E** | F11 + E-09 |
| F12 | `is_current` by session_id | **UNIT** + **E2E** | F12 + E-04 |
| F12 | Admin pagination | **UNIT** | `test_iam_sessions_v2_f12_read_path` |
| F13 | Tenant isolation all queries | **C8** (muestra V3) + **UNIT** parcial | MT-* ; inventario completo no requerido en C8 |
| F13 | Cleanup + users + superadmin | **UNIT** + **C8** cleanup BD | F13 + CL-* |
| F14 | Cutover smoke staging | **C8** pre-F14 + **MANUAL** | CT-* + ticket |

**Conclusión:** C8 cierra los gaps **integration/E2E/BD real** de P0-07, P1-09, P1-10. Los ítems §12.1 restantes quedan cubiertos por unitarios F7–F13 salvo M1–M10 manuales y cutover productivo F14.

---

## 17. Tests Integration obligatorios

### `test_iam_sessions_v2_f4_tx_integration.py` (C18)

| ID | Test |
|----|------|
| I-01 | `test_i01_create_session_four_writes_persisted` |
| I-02 | `test_i02_create_session_rollback_on_step_failure` |
| I-03 | `test_i03_rotate_chain_parent_token_id` |
| I-04 | `test_i04_rotate_rollback_when_mark_used_zero` |
| I-05 | `test_i05_revoke_session_closes_session_and_tokens` |
| I-06 | `test_i06_revoke_all_bulk_coherent` |
| I-07 | `test_i07_replay_attack_compromises_family_and_session` |

### `test_iam_sessions_v2_cleanup_integration.py` (C7 evidencia BD)

| ID | Test |
|----|------|
| CL-01 | `test_cl01_purge_expired_tokens_respects_90d_retention` |
| CL-02 | `test_cl02_purge_closed_sessions_respects_90d_and_si_365d` |
| CL-03 | `test_cl03_purge_closed_sessions_skips_with_remaining_tokens` |

> Usar fechas artificiales antiguas en filas de test; teardown §11.

---

## 18. Tests Concurrency obligatorios

| ID | Test | Obligatorio |
|----|------|-------------|
| CC-01 | `test_cc01_double_refresh_one_wins` | **Sí** |
| CC-02 | `test_cc02_double_rotate_via_service` | No (redundante con CC-01) |
| CC-03 | `test_cc03_refresh_vs_logout_all_race` | **Sí** |
| CC-04 | `test_cc04_double_replay_attack_idempotent` | **Sí** |
| CC-05 | `test_cc05_refresh_vs_revoke_session_race` | **Sí** |

Marcar `@pytest.mark.slow`.

---

## 19. Tests Multi-tenant obligatorios

**Archivo:** `test_iam_sessions_v2_tenant_isolation.py` (reemplazo oficial de legacy §24)

| ID | Test |
|----|------|
| MT-01 | `test_mt01_get_active_session_cross_tenant_returns_none` |
| MT-02 | `test_mt02_get_token_by_hash_cross_tenant_returns_none` |
| MT-03 | `test_mt03_get_family_by_session_cross_tenant_returns_none` |
| MT-04 | `test_mt04_revoke_session_cross_tenant_affects_zero_rows` |
| MT-05 | `test_mt05_rotate_with_wrong_cliente_id_fails` |
| MT-06 | `test_mt06_cleanup_tenant_a_does_not_delete_tenant_b` |
| MT-07 | `test_mt07_endpoint_revoke_other_tenant_session_404` |

---

## 20. Tests E2E obligatorios

**Archivo:** `test_iam_sessions_v2_e2e_smoke.py`  
**Perfil flag:** `iam_v2_flag_all_tenants_on` salvo E-12.

| ID | Test | Ref |
|----|------|-----|
| E-01 | `test_e01_login_v2_returns_sid_and_refresh_cookie` | M1 |
| E-02 | `test_e02_refresh_rotates_and_reissues_sid` | M2 |
| E-03 | `test_e03_logout_invalidates_refresh_and_blacklists_access` | M3 |
| E-04 | `test_e04_list_sessions_is_current_by_session_id` | M4 |
| E-05 | `test_e05_self_revoke_remote_session` | M5 |
| E-06 | `test_e06_admin_revoke_emits_audit` | M6 |
| E-07 | `test_e07_replay_old_refresh_closes_session` | M7 |
| E-08 | `test_e08_cambiar_empresa_without_relogin` | M8 |
| E-09 | `test_e09_multi_empresa_selection_flow` | M9 |
| E-10 | `test_e10_password_change_revokes_others_and_sid` | M10 |
| E-11 | `test_e11_logout_all_closes_all_sessions` | F9 |
| E-12 | `test_e12_flag_off_login_refresh_logout_v1` | Regresión |
| E-13 | `test_e13_me_probe_rejects_revoked_session` | P1-13 |

### E-14 — Clasificación única

**E-14 eliminado del alcance C8.** Business activity throttle ya cubierto por unitarios F13 (`test_f13_business_activity_*`). No es obligatorio en RC2.

---

## 21. Tests Cutover obligatorios

**Archivo:** `test_iam_sessions_v2_cutover_pre_f14.py`  
**Alcance:** smoke pre-F14 — **no** cutover productivo F14.

| ID | Test | Descripción |
|----|------|-------------|
| CT-01 | `test_ct01_flag_off_uses_v1_storage` | `ENABLED=false` → `RefreshTokenService`, sin filas V3 |
| CT-02 | `test_ct02_flag_on_uses_v3_tables` | `ENABLED=true` + allowlist vacía → login crea `user_session` |
| CT-03 | `test_ct03_v1_session_survives_flag_on_new_login` | Ver procedimiento abajo |
| CT-04 | `test_ct04_allowlist_excludes_tenant_b_from_v2` | Ver §14 |

### CT-03 — Procedimiento oficial (coexistencia V1 + V3)

**Objetivo:** Verificar que activar V2 no invalida ni migra automáticamente sesiones V1 preexistentes.

**Pasos en test (flag OFF inicialmente):**

1. **Setup:** `iam_v2_flag_off`; usuario `iam_v2_user_a` en tenant A.  
2. **Crear sesión V1:** `POST /auth/login/` → obtener `refresh_token` V1.  
3. **Verificar V1 en BD:** fila en `refresh_tokens` (modelo V1/V020) con `token_hash` correspondiente; **sin** fila en `user_session` para ese login.  
4. **Activar V2:** patch `IAM_SESSION_MANAGEMENT_V2_ENABLED=true`, allowlist vacía o con `tenant_a`.  
5. **Nuevo login V2:** segundo `POST /auth/login/` mismo usuario → crea filas V3 (`user_session`, `token_family`, `refresh_tokens` v3).  
6. **Assert coexistencia:**  
   - Token refresh V1 antiguo: sigue resoluble vía rama V1 **o** rechazado según política — documentar expectativa: **fila V1 permanece en BD** (no DELETE automático).  
   - Token refresh V2 nuevo: operativo.  
   - Contar filas: ≥1 fila V1 legacy + ≥1 sesión V3 activa.  
7. **Teardown §11:** DELETE directo filas V1 y V3 del `usuario_id` test.

**Nota:** Si esquema V031 reemplazó estructura `refresh_tokens` sin convivencia V1, CT-03 se ejecuta solo en BD con **ambos modelos coexistiendo** (staging clone real). Si no es posible en BD test local → `pytest.skip` con referencia a ejecución en staging clone (evidencia RC2-07).

---

## 22. Escenarios negativos

| ID | Escenario | Suite |
|----|-----------|-------|
| N-01 | Refresh token `is_used=1` → replay | E-07 / I-07 |
| N-02 | Idle timeout antes de rotate | UNIT F8 + integration opcional |
| N-03 | Sesión `expires_at` absoluto expirado | Integration |
| N-04 | Familia `is_compromised=1` | Integration |
| N-05 | Access sin `sid` → business activity noop | UNIT F13 |
| N-06 | Access `sid` revocado → probe falla | E-13 |
| N-07 | Doble logout idempotente | E-03 |
| N-08 | Self-revoke sesión cerrada → 404 | E-05 |
| N-09 | `sort_by` inválido → 422 | UNIT F12 |
| N-10 | Flag OFF no escribe V3 | CT-01 |

---

## 23. Escenarios rollback

| ID | Escenario | Verificación |
|----|-----------|--------------|
| R-01 | Create: fallo insert token | 0 filas session/family/token |
| R-02 | Create: fallo update `current_token_id` | 0 filas residuales |
| R-03 | Rotate: `mark_used` 0 filas | token nuevo no existe |
| R-04 | Revoke all: excepción mid-tx | estado pre-tx |
| R-05 | Deadlock (opcional) | error limpio, sin huérfanas |

---

## 24. Criterios RC2

| ID | Criterio |
|----|----------|
| RC2-01 | P0-07 cerrado — E-01…E-13 + CT-01…CT-04 verdes (o CT-03 skip documentado en staging) |
| RC2-02 | P1-09 cerrado — I-* + CC-01,03,04,05 + R-* verdes en SQL Server |
| RC2-03 | P1-10 cerrado — MT-01…MT-07 verdes |
| RC2-04 | Suite §12.2 Implementation Plan verde |
| RC2-04b | **`tests/integration/test_iam_sessions_v2_tenant_isolation.py` verde** como **reemplazo oficial** de `tests/test_tenant_isolation.py` para dominio IAM V3; legacy V1 no requiere modificación |
| RC2-05 | `tests/unit/test_iam_sessions_v2_*` verde sin regresión |
| RC2-06 | `tests/unit/test_iam_sessions_*` + `test_iam_sessions_v1_enterprise.py` verdes |
| RC2-07 | Evidencia M1–M10 manual staging adjunta al ticket |
| RC2-08 | Sin defecto P0 abierto detectado en integration |
| RC2-09 | Release Manager + QA Lead sign-off |
| RC2-10 | **No** autoriza F14 en el mismo merge — solo RC2 |

### Comando §12.2 (canónico)

```text
pytest tests/unit/test_iam_sessions_v2_* tests/integration/test_iam_sessions_v2_* -v
pytest tests/unit/test_iam_sessions_* -v
```

---

## 25. Gates de salida

| Gate | Fase | Condición |
|------|------|-----------|
| **G0** | 0 | Harness + schema V031 + teardown helper |
| **G1** | 1 | MT-01…MT-07 verdes |
| **G2** | 2 | I-01…I-07 + CL-01…CL-03 + CC obligatorios + R-01…R-04 verdes |
| **G3** | 3a | E-01…E-13 verdes |
| **G4** | 3b | CT-01…CT-04 verdes (CT-03 skip staging documentado si aplica) |
| **G5** | 4 | RC2-04 + RC2-04b + RC2-05 + RC2-06 verdes |
| **G6** | 4 | RC2-07 evidencia manual |
| **G7** | 4 | **RC2 declarado** (RC2-09) |

---

## 26. Code Freeze

Tras **G7 (RC2 declarado)**:

| Regla | Detalle |
|-------|---------|
| Alcance congelado | Runtime auth/sesión congelado C1–C7 + HA1 |
| Hotfix permitido | Solo P0 con ticket + aprobación Release Manager |
| Tests | Permiten nuevos tests hasta F14; no cambiar lógica runtime |
| Duración | Desde RC2 hasta cierre F14 o rollback F14 |

---

## 27. Preparación F14

C8 **no ejecuta F14**. Entrega preparatoria:

| Entregable C8 | Uso F14 |
|---------------|---------|
| Suite §12.2 verde | Gate pre-cutover |
| CT-* pre-F14 | Evidencia convivencia V1/V3 |
| RC2-07 M1–M10 | Checklist §13.2 |
| Documentación skip CT-03 | Plan staging clone §13.3 |

F14 requiere ticket separado: DDL prod, flag prod, comunicación 72h, rollback script probado.

---

## 28. Riesgos

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-C8-01 | Sin SQL Server en CI | Runner self-hosted o gate manual RC2-09 |
| R-C8-02 | V031 no aplicado | G0 schema check bloqueante |
| R-C8-03 | Contaminación BD por retención | Teardown §11 DELETE directo |
| R-C8-04 | CT-03 no reproducible en BD local | Skip + evidencia staging RC2-07 |
| R-C8-05 | Flaky concurrency | `@pytest.mark.slow`, reintentos ≤2 |
| R-C8-06 | Redis down | Skip E-03 + M3 manual obligatorio |

---

## 29. Estrategia de rollback del cluster

| Situación | Acción |
|-----------|--------|
| Merge C8 defectuoso | Revert PR — cero impacto runtime |
| RC2 revocado | Revert C8; RC1 permanece válido |
| P0 en C18 descubierto | Hotfix fuera C8; re-ejecutar suite |
| F14 pospuesto | Mantener tests; Code Freeze hasta F14 |

---

## Checklist ejecutable

```
[ ] G0  Harness + V031 + teardown §11
[ ] G1  P1-10 MT-01…MT-07
[ ] G2  P1-09 I-* + CL-* + CC-* + R-*
[ ] G3  P0-07 E-01…E-13
[ ] G4  P0-07 CT-01…CT-04
[ ] G5  §12.2 + RC2-04b + unitarios V2/V1
[ ] G6  M1–M10 evidencia staging
[ ] G7  Declaración RC2
```

---

## Commits sugeridos

| # | Mensaje |
|---|---------|
| 1 | `test(iam-session): pre-f14 C8 harness markers and teardown helper` |
| 2 | `test(iam-session): pre-f14 C8 tenant isolation V3 integration` |
| 3 | `test(iam-session): pre-f14 C8 C18 tx and cleanup integration` |
| 4 | `test(iam-session): pre-f14 C8 E2E smoke and cutover pre-F14 tests` |
| 5 | `ci(iam-session): pre-f14 C8 integration pipeline gate` (opcional) |

---

## Historial de versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2026-06-22 | Versión inicial |
| 1.1.0 | 2026-06-22 | Enmiendas auditoría: allowlist, §12.1, teardown §11, RC2-04b, CT-03, E-14, seeds, cleanup file split, cutover naming |

---

## Aprobación

### **DOCUMENTO APROBADO — LISTO PARA INICIAR LA IMPLEMENTACIÓN COMPLETA DEL CLUSTER 8**

Condiciones de arranque Fase 0:

1. V031 aplicado en BD de pruebas.  
2. Seeds §10 completos (2 empresas, admin revoke).  
3. Teardown §11 implementado antes de cualquier test que escriba BD.  
4. Compromiso: no modificar archivos §7.

**No autoriza F14 ni Code Freeze** hasta G7.
