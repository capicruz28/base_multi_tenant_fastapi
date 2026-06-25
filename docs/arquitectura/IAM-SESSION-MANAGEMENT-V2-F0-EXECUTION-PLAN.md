# IAM Session Management V2 — Plan de Ejecución Fase F0

**Ticket:** IAM-BE-F0-EXEC-01  
**Versión:** 1.0.0  
**Estado:** Plan de ejecución inmediata (pre-código F0)  
**Fecha:** 2026-06-22  
**Fase:** F0 — Gobernanza y preparación  

**Documento maestro:** `IAM-SESSION-MANAGEMENT-V2-IMPLEMENTATION-PLAN-01.md`  
**Restricción de este artefacto:** Planificación ejecutable de F0 únicamente. Sin implementación de código en la elaboración de este documento.

---

## Índice

1. [Propósito y alcance de F0](#1-propósito-y-alcance-de-f0)
2. [Estado previo satisfecho (adaptación al contexto actual)](#2-estado-previo-satisfecho-adaptación-al-contexto-actual)
3. [Plan maestro adaptado post-F0](#3-plan-maestro-adaptado-post-f0)
4. [Decisiones arquitectónicas — cierre obligatorio en F0](#4-decisiones-arquitectónicas--cierre-obligatorio-en-f0)
5. [Tareas F0 — orden de ejecución](#5-tareas-f0--orden-de-ejecución)
6. [Especificación del feature flag](#6-especificación-del-feature-flag)
7. [Especificación del contrato API V2 (contenido obligatorio)](#7-especificación-del-contrato-api-v2-contenido-obligatorio)
8. [Ticket de cutover F14 — plantilla](#8-ticket-de-cutover-f14--plantilla)
9. [Configuración de entornos y ramas](#9-configuración-de-entornos-y-ramas)
10. [Validaciones y gates de salida F0](#10-validaciones-y-gates-de-salida-f0)
11. [Riesgos, rollback y criterios de aceptación](#11-riesgos-rollback-y-criterios-de-aceptación)
12. [Checklist ejecutable](#12-checklist-ejecutable)
13. [Siguiente fase — F1 adaptada](#13-siguiente-fase--f1-adaptada)

---

## 1. Propósito y alcance de F0

### 1.1 Objetivo F0 (según plan maestro)

Alinear stakeholders, introducir el **feature flag** de conmutación V1/V2, publicar el **contrato API V2** aditivo y abrir el **ticket de cutover** (F14) con checklist operativo — **sin tocar lógica de sesión ni endpoints**.

### 1.2 Qué incluye F0

| Incluye ✅ | Excluye ❌ |
|-----------|-----------|
| Feature flag en `config.py` + helper de resolución | Queries, services, transacciones |
| Documento `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` | Modificación `auth_service`, `endpoints` |
| Cierre formal decisiones D-01 a D-10 (registro) | SQLAlchemy `tables.py` (F1) |
| Ticket F14 + comunicación template | Tests de dominio (F2+) |
| Rama `feature/iam-session-v2` | Activar flag en producción |
| `.env.example` / documentación dev flag | Cutover DDL producción |

### 1.3 Entregable único de la fase (commit F0)

```
chore(iam-session): F0 governance — feature flag and API V2 contract
```

**Archivos tocados en implementación F0 (máximo 4):**

| Acción | Archivo |
|--------|---------|
| Crear | `docs/arquitectura/ERP-IAM-SESSIONS-API-CONTRACT-V2.md` |
| Crear | `docs/arquitectura/IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md` |
| Modificar | `app/core/config.py` |
| Crear | `app/modules/auth/application/session/session_v2_feature.py` (helper flag — ver T4) |
| Opcional | `.env.example` — variables flag |

> **Nota:** El helper `session_v2_feature.py` es infraestructura mínima de gobernanza (10–20 LOC), no lógica de dominio. Se incluye en F0 para evitar duplicar parsing del flag en fases posteriores.

---

## 2. Estado previo satisfecho (adaptación al contexto actual)

El plan maestro original asume DDL en F1 y cutover DDL en F14. **El contexto del proyecto ha avanzado:**

| Ítem plan original | Estado actual | Impacto en ejecución |
|--------------------|---------------|----------------------|
| DDL V3 aprobado (`tables_session_management_new.sql`) | ✅ **SATISFECHO** | No rediseñar modelo |
| Tablas `user_session`, `token_family`, `refresh_tokens` v3 en BD dev | ✅ **SATISFECHO** | F1 no ejecuta DDL en dev |
| Script bootstrap `V031__iam_session_management_v3.sql` en repo | ⬜ Pendiente (opcional) | Ver §2.2 |
| ORM `UserSessionTable`, `TokenFamilyTable`, `RefreshTokensTable` v3 | ⬜ Pendiente | **F1** (sin migración) |
| Feature flag | ⬜ Pendiente | **F0** |
| Contrato API V2 | ⬜ Pendiente | **F0** |
| Código V2 | ⬜ Pendiente | F2–F15 |

### 2.1 Reglas adaptadas (obligatorias)

1. **No proponer ni ejecutar nuevas migraciones SQL** ni recreación de tablas en dev.
2. **No DROP/CREATE** en BD dev durante F0–F13.
3. F1 se redefine como **solo ORM + validación esquema contra BD existente** (ver §13).
4. F14 en staging/prod: ejecutar DDL solo donde **aún no exista** el esquema v3; dev queda excluido.
5. Referencia canónica DDL: `tables_session_management_new.sql` (v3). Si se versiona en bootstrap, debe ser **copia fiel** sin alterar semántica — tarea opcional F1, no bloqueante para dev.

### 2.2 V031 bootstrap — política adaptada

| Entorno | Acción DDL |
|---------|------------|
| **Dev (actual)** | Ninguna — tablas ya existen |
| **CI efímero** | Aplicar `tables_session_management_new.sql` o snapshot dev |
| **Staging / Prod (F14)** | Aplicar script aprobado en ventana; inventario multi-DB |

**F0 no crea V031.** Si el equipo decide versionar el script en F1, será documentación/bootstrap para otros entornos, no migración dev.

### 2.3 Validación esquema dev (tarea F0, solo lectura)

Antes de cerrar F0, confirmar manualmente en BD dev:

```sql
-- Verificación mínima (solo lectura)
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('user_session', 'token_family', 'refresh_tokens');

SELECT COUNT(*) AS col_count FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'user_session';  -- esperado: columnas según v3 (~22)

SELECT name FROM sys.indexes
WHERE object_id = OBJECT_ID('user_session') AND name LIKE 'IDX_session%';
```

Registrar resultado en `IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md` § «Validación esquema dev».

---

## 3. Plan maestro adaptado post-F0

```
F0  Gobernanza y feature flag                    ← ESTA FASE
F1  SQLAlchemy ORM v3 + test schema match        ← ADAPTADA (sin DDL dev)
F2  Domain types (C19)
F3  Queries user_session + token_family
F4  Queries refresh_token v3 + session_transaction
F5  Bridges audit + redis
F6  Query services
F7  Policy + creation
F8  Rotation + replay
F9  Revocation
F10 Orquestación auth core
F11 Orquestación empresa/password/impersonation
F12 Read path + DTOs aditivos
F13 Adyacentes
F14 Cutover (solo envs sin esquema v3 + flag prod)
F15 Legacy cleanup
```

**Cambio respecto al plan original:** F1 ya no incluye «ejecutar V031 en dev». F14 excluye dev si esquema v3 ya está presente.

---

## 4. Decisiones arquitectónicas — cierre obligatorio en F0

Registrar en `IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md` con estado **ACCEPTED**:

| ID | Decisión | Resolución F0 (DESIGN-01) |
|----|----------|---------------------------|
| D-01 | Identificador API sesión | **Opción C:** `session_id` canónico + `token_id` vigente en DTO |
| D-02 | Redis mapping key | **`session:access_jti:{session_id}`** (+ dual-write V1 en F10–F14) |
| D-03 | Compatibilidad FE | **Extensión aditiva** — mismos paths `/api/v1/auth/*` |
| D-04 | Retención forense | **90 días** tokens usados/revocados; familias comprometidas 1 año |
| D-05 | RevokedReason mapping | Funciones `to_session_reason()` / `to_token_reason()` / `to_family_reason()` en F2 |
| D-06 | Claim JWT `sid` | **Sí** en access token — implementación F13 |
| D-07 | Device session reuse | **Fase 1: siempre nueva sesión** en login |
| D-08 | Logout all tx | Bulk si &lt;20 sesiones; chunks si más |
| D-09 | TTL dual | Sesión `expires_at` absoluto; token `refresh_token_days` |
| D-10 | V1 Enterprise en rama | **No mergear** read service V1 sin adaptar a V2 |
| **D-11** (nueva) | DDL dev | **Pre-aplicado** — sin migración dev en F1–F13 |

**Gate F0:** Ningún desarrollador inicia F1 sin `DECISIONS-LOG` merged con D-01 a D-11 ACCEPTED.

---

## 5. Tareas F0 — orden de ejecución

### Resumen

| Orden | ID | Tarea | Tipo | Estimación |
|:-----:|----|-------|------|:----------:|
| 1 | T0 | Crear rama `feature/iam-session-v2` | Git | 15 min |
| 2 | T1 | Validación esquema BD dev (lectura) | Ops | 30 min |
| 3 | T2 | Crear `DECISIONS-LOG` con D-01–D-11 | Doc | 1 h |
| 4 | T3 | Crear `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` | Doc | 3–4 h |
| 5 | T4 | Implementar feature flag + helper | Código | 1–2 h |
| 6 | T5 | Actualizar `.env.example` | Doc | 15 min |
| 7 | T6 | Crear ticket F14 (cutover) | Gestión | 1 h |
| 8 | T7 | Review arquitectura + FE contrato V2 | Review | 2 h |
| 9 | T8 | Gate salida F0 + commit | Cierre | 30 min |

**Duración total estimada F0:** 1–1.5 días-persona.

---

### T0 — Rama de integración

**Acción:**
```text
git checkout -b feature/iam-session-v2
```

**Criterio:** Rama existe en remoto con protección PR opcional.

---

### T1 — Validación esquema BD dev (SATISFECHO parcial → verificar)

**Objetivo:** Confirmar que BD dev coincide con `tables_session_management_new.sql` v3.

**Checklist columnas críticas `user_session`:**

- `session_id`, `usuario_id`, `cliente_id`, `empresa_id`
- `login_method`, `selection_token_completed`, `platform`
- `device_name`, `device_id`, `device_fingerprint`, `user_agent`
- `login_ip`, `last_seen_ip`
- `is_active`, `revoked_at`, `revoked_reason`
- `last_refresh_at`, `last_business_activity_at`, `created_at`, `expires_at`

**Checklist `token_family`:** `family_id`, `session_id`, `usuario_id`, `cliente_id`, `current_token_id`, `is_compromised`, `compromised_at`, `invalidation_reason`

**Checklist `refresh_tokens` v3:** `family_id`, `session_id`, `parent_token_id`, `is_used`, `used_at` (+ columnas tenant/hash/estado)

**Si discrepancia:** Documentar en DECISIONS-LOG; **no** alterar BD en F0 — escalar a DBA fuera de alcance código.

---

### T2 — Decision Log

**Crear:** `docs/arquitectura/IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md`

**Estructura mínima:**
```markdown
# IAM Session V2 — Decision Log
| ID | Fecha | Decisión | Estado | Aprobado por |
| D-01 | YYYY-MM-DD | Opción C dual ID | ACCEPTED | ... |
...
## Validación esquema dev
- Fecha: ...
- Resultado: OK / GAP (detalle)
```

---

### T3 — Contrato API V2

**Crear:** `docs/arquitectura/ERP-IAM-SESSIONS-API-CONTRACT-V2.md`

Contenido obligatorio detallado en §7 de este documento.

**Review obligatorio:** 1 arquitecto backend + 1 representante Frontend.

---

### T4 — Feature flag

**Modificar:** `app/core/config.py`  
**Crear:** `app/modules/auth/application/session/session_v2_feature.py`

Ver especificación completa §6.

**Comportamiento requerido:**
- Default `False` en todos los entornos.
- Producción: flag solo activable explícitamente (F14).
- Dev local: `IAM_SESSION_MANAGEMENT_V2_ENABLED=true` en `.env` para F3+.

---

### T5 — `.env.example`

Añadir:
```env
# IAM Session Management V2 (default false — do not enable in production until F14)
IAM_SESSION_MANAGEMENT_V2_ENABLED=false
IAM_SESSION_V2_TENANT_ALLOWLIST=
```

---

### T6 — Ticket cutover F14

Crear ticket en sistema de gestión (plantilla §8).

---

### T7 — Review gate

| Revisor | Aprueba |
|---------|---------|
| Backend lead | DECISIONS-LOG + flag spec |
| Frontend | API CONTRACT V2 § breaking/aditivo |
| DevOps | Ticket F14 checklist |

---

### T8 — Cierre F0

- [ ] Todos los gates §10 verdes
- [ ] PR `phase/00-governance` → `feature/iam-session-v2`
- [ ] Commit mensaje estándar
- [ ] Anuncio equipo: «F1 puede iniciar — ORM only, dev DDL pre-aplicado»

---

## 6. Especificación del feature flag

### 6.1 Variables (`app/core/config.py`)

```text
IAM_SESSION_MANAGEMENT_V2_ENABLED: bool = False
IAM_SESSION_V2_TENANT_ALLOWLIST: str = ""   # CSV UUIDs; vacío = solo global flag
```

**Parsing:**
- Env `IAM_SESSION_MANAGEMENT_V2_ENABLED`: `true`/`false` (case insensitive).
- En `ENVIRONMENT=production`: log WARNING si se intenta `true` antes de F14 (no bloquear en F0 — solo advertencia).

### 6.2 Helper `session_v2_feature.py`

```text
def is_session_v2_enabled(cliente_id: UUID | None) -> bool:
    """
    True si V2 activo globalmente Y (allowlist vacía O cliente_id en allowlist).
    False si cliente_id es None y se requiere tenant (callers deben manejar).
    """
```

**Ubicación:** `app/modules/auth/application/session/` — junto a tipos dominio futuros.

**Uso previsto (F10+):**
```text
if is_session_v2_enabled(cliente_id):
    → SessionCreationService / SessionRotationService / ...
else:
    → RefreshTokenService (legado)
```

### 6.3 Matriz de activación por entorno (post-F0)

| Entorno | F0–F9 | F10–F13 | F14 |
|---------|-------|---------|-----|
| Local dev | `false` default; dev puede `true` | `true` recomendado | `true` |
| CI V2 tests | `true` en job dedicado | `true` | `true` |
| CI regresión V1 | `false` | `false` | — |
| Staging | `false` hasta F10 | `true` | `true` |
| Producción | `false` | `false` | `true` ventana |

---

## 7. Especificación del contrato API V2 (contenido obligatorio)

El archivo `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` debe incluir como mínimo:

### 7.1 Metadatos

- Versión `2.0.0`
- Estado: «En implementación — backend F10+»
- Supersedes parcialmente V1 (sin invalidar paths)
- Referencia: DESIGN-01 D-01, D-03

### 7.2 Principios de compatibilidad

1. **Mismos endpoints** que V1 bajo `/api/v1/auth/`.
2. **JSON superset** — todos los campos V1 permanecen.
3. **Campos nuevos** opcionales para FE legacy.
4. **Sin eliminación** de campos hasta F15+ acuerdo FE.

### 7.3 Cambios de semántica documentados

| Campo V1 | Semántica V1 | Semántica V2 |
|----------|--------------|--------------|
| `token_id` en listado | ID de sesión | ID del **refresh token vigente** |
| `session_id` | — | **ID canónico de sesión** (nuevo) |
| `issued_at` | Emisión refresh vigente | Inicio sesión lógica (`user_session.created_at`) |
| `last_refresh_at` | = `last_used_at` | Último `POST /refresh` (`user_session.last_refresh_at`) |
| `expires_at` | Expiración refresh | Expiración **sesión** (TTL absoluto) |
| `client_type` | Tipo cliente | Alias de `platform` — ambos presentes |
| `ip_address` (listado) | IP token | `last_seen_ip` de sesión |
| — | — | `login_ip` nuevo (auditoría, inmutable) |

### 7.4 Endpoints — delta V2

Documentar **todos** los de V1 más:

| Endpoint | Delta V2 |
|----------|----------|
| `GET /sessions/` | Response incluye `session_id`, `platform`, `login_ip` |
| `GET /sessions/admin/` | Idem + sort whitelist ampliada con `platform`, `login_ip`, `session_id` |
| `POST /sessions/{id}/revoke/` | Path param `{id}` = `session_id` **o** `token_id` vigente (alias) |
| `POST /sessions/{id}/revoke_admin/` | Idem |
| `GET /me/` | + `current_session_id`; `current_token_id` conservado |

### 7.5 JWT access — claim `sid`

| Claim | Tipo | Descripción |
|-------|------|-------------|
| `sid` | UUID string | `session_id` — disponible desde F13 |

### 7.6 Comportamiento post-cutover F14

- Re-login obligatorio tras deploy.
- Sesiones V1 invalidadas (tabla monolítica reemplazada en envs migrados).

### 7.7 Matriz FE — acciones recomendadas

Copiar §14.3 del plan maestro (P0–P3).

---

## 8. Ticket de cutover F14 — plantilla

**Título:** `IAM Session V2 — Production Cutover (F14)`

**Descripción:**

```markdown
## Objetivo
Activar IAM Session Management V2 en producción.

## Pre-requisitos
- [ ] F13 merged en feature/iam-session-v2
- [ ] Suite test_iam_sessions_v2_* verde
- [ ] Staging con esquema v3 + flag ON ≥ 48h sin P0
- [ ] FE desplegado tolerante a superset JSON
- [ ] Comunicación usuarios T-72h

## Alcance DDL
- [ ] Inventario tenants Multi-DB
- [ ] Aplicar tables_session_management_new.sql SOLO en envs sin v3
- [ ] Dev: OMITIR (ya aplicado)

## Pasos ventana
1. Backup BD central + tenants dedicados
2. DDL en envs pendientes
3. Deploy backend release X.Y.Z
4. IAM_SESSION_MANAGEMENT_V2_ENABLED=true
5. Smoke M1–M10
6. Monitor 24h

## Rollback
- Flag OFF no restaura datos post-DDL — ver IMPLEMENTATION-PLAN §9.1

## Comunicación
- Plantilla email: «Actualización de seguridad de sesiones — re-inicio de sesión requerido»
```

---

## 9. Configuración de entornos y ramas

### 9.1 Git

```text
main
 └── feature/iam-session-v2
      └── phase/00-governance    ← PR F0
```

Tras merge F0: crear `phase/01-orm` para F1.

### 9.2 Variables entorno dev (post-F0 implementación)

```env
IAM_SESSION_MANAGEMENT_V2_ENABLED=true
IAM_SESSION_V2_TENANT_ALLOWLIST=
```

Permite desarrollar F3+ contra tablas v3 existentes sin afectar código V1 (flag aún no wired hasta F10).

### 9.3 CI (registrar en ticket técnico F0)

| Job | Flag | BD |
|-----|------|-----|
| `test-iam-v1` | OFF | V020 o mock |
| `test-iam-v2` | ON | Schema v3 |

---

## 10. Validaciones y gates de salida F0

### 10.1 Automáticas (post-implementación F0)

| Validación | Comando / acción |
|------------|------------------|
| App arranca | `uvicorn` / import settings sin error |
| Flag default false | Assert en test unitario mínimo `test_session_v2_feature_default_false.py` |
| Helper allowlist | Test: global false → false; global true + allowlist → filtrado |

### 10.2 Manuales

| # | Validación | Responsable |
|---|------------|-------------|
| V1 | DECISIONS-LOG con 11 decisiones ACCEPTED | Arquitectura |
| V2 | API CONTRACT V2 revisado por FE | Frontend |
| V3 | Esquema dev verificado T1 | Backend |
| V4 | Ticket F14 creado | TL |
| V5 | `.env.example` actualizado | Backend |

### 10.3 Gate absoluto

**No iniciar F1** hasta que los 5 ítems manuales estén marcados.

---

## 11. Riesgos, rollback y criterios de aceptación

### 11.1 Riesgos F0

| Riesgo | Nivel | Mitigación |
|--------|:-----:|------------|
| FE no revisa contrato V2 | Medio | Gate V2 bloquea F12 |
| Esquema dev diverge de v3 | Alto | T1 antes de F1 ORM |
| Flag activado accidentalmente en prod | Medio | Default false + warning log |
| Trabajo V1 Enterprise mergeado sin adaptar | Medio | D-10 en DECISIONS-LOG |

### 11.2 Rollback F0

```text
git revert <commit-f0>
```

Impacto: nulo en runtime (flag default false, sin wiring).

### 11.3 Criterios de aceptación F0 (definitivos)

- [ ] `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` existe y aprobado por FE
- [ ] `IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md` con D-01–D-11 ACCEPTED
- [ ] `IAM_SESSION_MANAGEMENT_V2_ENABLED` default `False` en `config.py`
- [ ] `is_session_v2_enabled()` helper testeado
- [ ] Validación esquema dev documentada OK
- [ ] Ticket F14 creado con checklist
- [ ] PR F0 merged a `feature/iam-session-v2`
- [ ] **Cero** cambios en `auth_service`, `endpoints`, queries sesión

---

## 12. Checklist ejecutable

Copiar y marcar durante implementación F0:

```markdown
## F0 Execution Checklist

### Preparación
- [ ] T0 Rama feature/iam-session-v2 creada
- [ ] T1 Esquema dev verificado (SQL lectura)
- [ ] GAP esquema documentado o confirmado OK

### Documentación
- [ ] T2 IAM-SESSION-MANAGEMENT-V2-DECISIONS-LOG.md
- [ ] T3 ERP-IAM-SESSIONS-API-CONTRACT-V2.md
- [ ] T6 Ticket F14 creado

### Código (alcance mínimo F0)
- [ ] T4 config.py — IAM_SESSION_MANAGEMENT_V2_ENABLED
- [ ] T4 config.py — IAM_SESSION_V2_TENANT_ALLOWLIST
- [ ] T4 session_v2_feature.py
- [ ] T5 .env.example
- [ ] test_session_v2_feature_default_false.py

### Review
- [ ] T7 Backend lead aprueba
- [ ] T7 Frontend aprueba contrato V2
- [ ] T7 DevOps recibe ticket F14

### Cierre
- [ ] T8 PR merged
- [ ] T8 Commit: chore(iam-session): F0 governance — feature flag and API V2 contract
- [ ] Equipo notificado: F1 ORM-only puede iniciar
```

---

## 13. Siguiente fase — F1 adaptada

### 13.1 Objetivo F1 revisado

**«SQLAlchemy ORM v3 + validación contra BD dev existente»** — sin migración SQL.

### 13.2 Tareas F1 (preview — no ejecutar en F0)

| Tarea | Acción |
|-------|--------|
| F1-T1 | Añadir `UserSessionTable`, `TokenFamilyTable` en `tables.py` |
| F1-T2 | Actualizar `RefreshTokensTable` a columnas v3 |
| F1-T3 | Test `test_iam_sessions_v2_f1_tables.py` — introspección BD vs ORM |
| F1-T4 | *(Opcional)* Copiar `tables_session_management_new.sql` → `V031__...sql` para bootstrap staging/prod **sin ejecutar en dev** |

### 13.3 Dependencia F1

- **Bloqueada por:** F0 gate completo
- **No bloqueada por:** DDL dev (ya satisfecho)

### 13.4 Commit F1 previsto

```text
feat(iam-session): F1 SQLAlchemy tables v3 and schema validation (dev DDL pre-applied)
```

---

## Anexo — Trazabilidad plan maestro → F0 adaptado

| Sección IMPLEMENTATION-PLAN-01 | Estado en F0 |
|------------------------------|--------------|
| §16 Fase F0 | Ejecutada vía este documento |
| §16 Fase F1 DDL | **Adaptada** — ORM only (§13) |
| §7 Migración incremental | Dev DDL pre-aplicado registrado |
| §9 Rollback F14 | Ticket F14 referencia |
| §14 Integración FE | Contrato V2 en T3 |

---

**Fin del documento — IAM-BE-F0-EXEC-01**

**Acción inmediata tras aprobación de este plan:** Ejecutar checklist §12 (implementación F0 — siguiente sesión de desarrollo).
