# IAM Session Management V2 — Decision Log

**Ticket:** IAM-BE-F0-DECISIONS-01  
**Versión:** 1.0.0  
**Fecha:** 2026-06-22  
**Estado:** ACCEPTED (Fase F0)

Referencias: `IAM-SESSION-MANAGEMENT-V2-DESIGN-01.md` §17, `IAM-SESSION-MANAGEMENT-V2-F0-EXECUTION-PLAN.md` §4.

---

## Decisiones arquitectónicas

| ID | Fecha | Decisión | Estado | Aprobado por |
|----|-------|----------|--------|--------------|
| D-01 | 2026-06-22 | Identificador API sesión: **Opción C** — `session_id` canónico + `token_id` vigente en DTO | ACCEPTED | Arquitectura Backend |
| D-02 | 2026-06-22 | Redis mapping key: **`session:access_jti:{session_id}`** (+ dual-write V1 en F10–F14) | ACCEPTED | Arquitectura Backend |
| D-03 | 2026-06-22 | Compatibilidad FE: **extensión aditiva** — mismos paths `/api/v1/auth/*` | ACCEPTED | Arquitectura Backend + Frontend (pendiente review formal) |
| D-04 | 2026-06-22 | Retención forense: **90 días** tokens usados/revocados; familias comprometidas **1 año** | ACCEPTED | Arquitectura Backend |
| D-05 | 2026-06-22 | `RevokedReason` mapping vía `to_session_reason()` / `to_token_reason()` / `to_family_reason()` en **F2** | ACCEPTED | Arquitectura Backend |
| D-06 | 2026-06-22 | Claim JWT access **`sid`** = `session_id` — implementación **F13** | ACCEPTED | Arquitectura Backend |
| D-07 | 2026-06-22 | Device session reuse: **Fase 1 siempre nueva sesión** en login | ACCEPTED | Arquitectura Backend |
| D-08 | 2026-06-22 | Logout all transaccional: bulk si &lt;20 sesiones; chunks si más | ACCEPTED | Arquitectura Backend |
| D-09 | 2026-06-22 | TTL dual: `user_session.expires_at` absoluto + `refresh_tokens.expires_at` por emisión | ACCEPTED | Arquitectura Backend |
| D-10 | 2026-06-22 | No mergear read service V1 Enterprise sin adaptar a modelo V2 | ACCEPTED | Arquitectura Backend |
| D-11 | 2026-06-22 | DDL dev **pre-aplicado** — sin migración dev en F1–F13 | ACCEPTED | Arquitectura Backend + DevOps |

---

## Validación esquema BD dev

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-06-22 |
| **Entorno** | BD desarrollo local (`bd_caxis_saas` vía `.env`) |
| **Referencia DDL** | `tables_session_management_new.sql` (v3) |
| **Resultado** | **PARCIAL — GAP en `refresh_tokens`** |
| **Método** | Consultas SQL de solo lectura (`INFORMATION_SCHEMA.COLUMNS`, `sys.indexes`) |
| **Responsable verificación** | Auditoría F0 Backend |

### Resultado por tabla (auditoría 2026-06-22)

| Tabla | Estado | Columnas v3 | Observación |
|-------|--------|-------------|-------------|
| `user_session` | ✅ OK | 20/20 críticas presentes | Índices `IDX_session_*` presentes (8) |
| `token_family` | ✅ OK | 9/9 críticas presentes | — |
| `refresh_tokens` | ❌ GAP | Esquema **V020 monolítico** | Faltan `family_id`, `session_id`, `parent_token_id`, `is_used`, `used_at`. Presentes columnas legacy: `client_type`, `device_name`, `device_id`, `ip_address`, `user_agent`, `uso_count` |

### Acción requerida pre-F1

Migrar `refresh_tokens` a esquema v3 según `tables_session_management_new.sql` (ventana que invalida sesiones activas). **No ejecutar en F0** — bloquea gate F1 ORM hasta resolución.

D-11 queda **ACCEPTED** con nota: `user_session` + `token_family` pre-aplicados; `refresh_tokens` v3 **pendiente** en dev.

### Checklist columnas críticas (referencia v3)

**`user_session`:** `session_id`, `usuario_id`, `cliente_id`, `empresa_id`, `login_method`, `selection_token_completed`, `platform`, `device_name`, `device_id`, `device_fingerprint`, `user_agent`, `login_ip`, `last_seen_ip`, `is_active`, `revoked_at`, `revoked_reason`, `last_refresh_at`, `last_business_activity_at`, `created_at`, `expires_at`

**`token_family`:** `family_id`, `session_id`, `usuario_id`, `cliente_id`, `current_token_id`, `is_compromised`, `compromised_at`, `invalidation_reason`

**`refresh_tokens` v3:** `family_id`, `session_id`, `parent_token_id`, `is_used`, `used_at`, `token_hash`, `cliente_id`, `usuario_id`, `empresa_id`, `expires_at`, `is_revoked`, `revoked_at`, `revoked_reason`

---

## Feature flag F0

| Variable | Default | Notas |
|----------|---------|-------|
| `IAM_SESSION_MANAGEMENT_V2_ENABLED` | `false` | Activación wiring en F10+; prod solo F14 |
| `IAM_SESSION_V2_TENANT_ALLOWLIST` | vacío | CSV UUIDs; vacío = todos los tenants si flag global true |

Helper: `app/modules/auth/application/session/session_v2_feature.py` → `is_session_v2_enabled(cliente_id)`.

---

## Gate F1

F1 (ORM v3 + validación esquema) puede iniciar cuando:

- [x] Este decision log merged con D-01–D-11 ACCEPTED
- [x] `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` publicado
- [x] Feature flag implementado y testeado
- [ ] **`refresh_tokens` migrado a esquema v3 en BD dev** (GAP detectado auditoría F0)
- [ ] Review formal Frontend del contrato V2 (pendiente sign-off)
- [ ] Ticket cutover F14 registrado en sistema de gestión externo (plantilla en repo: `IAM-SESSION-MANAGEMENT-V2-F14-CUTOVER-TICKET.md`)

---

**Fin del documento — IAM-BE-F0-DECISIONS-01**
