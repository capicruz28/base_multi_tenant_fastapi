# Hybrid F4 — Dedicated Provisioning Runbook (Staging)

**Documento:** `HYBRID_F4_PROVISIONING_RUNBOOK.md`  
**Versión:** 1.0  
**Fecha:** 2026-06-25  
**PR:** PR-F4-12 (F4-WP12)  
**Referencias:** IP-2.0.1, BL-F4-1.0, `DEDICATED_PROVISIONING_API_CONTRACT.md`

---

## 1. Propósito

Procedimiento operativo para provisioning dedicated en **staging**: happy path S1→S10, retry, abort, compensación, smoke Ready y sign-off **G-F4-02** / **G-F4-03**.

**Producción:** `DEDICATED_ENABLED=false` hasta cierre formal G-F4-03 + Gate Review F5b.

---

## 2. Flags de entorno

| Variable | Staging | Producción (pre-F5b) |
|----------|---------|----------------------|
| `DEDICATED_ENABLED` | `true` | `false` |
| `PROVISIONING_DISPATCHER_ENABLED` | `true` | `true` |
| `PROVISIONING_DISPATCHER_SYNC` | `false` (async) | `false` |
| `PROVISIONING_DDL_EXECUTOR_ENABLED` | `true` | `false` |
| `PROVISIONING_DDL_*` | Vault SRE (PF4-08) | No configurar |

---

## 3. Happy path S1→S10 (staging manual)

### 3.1 Crear tenant dedicated

```http
POST /api/v1/clientes/
Authorization: Bearer <superadmin_jwt>
Content-Type: application/json

{
  "codigo_cliente": "STG001",
  "subdominio": "stg001",
  "razon_social": "Staging Dedicated",
  "contacto_email": "admin@staging.test",
  "tipo_instalacion": "dedicated",
  "plan_suscripcion": "trial"
}
```

**Esperado:** HTTP 201 en &lt;500 ms; `provisioning_state=provisioning`; saga async S1→S10.

### 3.2 Polling status

```http
GET /api/v1/clientes/{cliente_id}/provisioning-status/
```

Poll cada 5–15 s hasta `ready` o `failed` (timeout UI sugerido 30 min).

### 3.3 Verificación Tenant Ready (G-F4-02)

| # | Check | Comando / evidencia |
|---|-------|---------------------|
| 1 | `provisioning_state=ready` | GET provisioning-status |
| 2 | `cliente_conexion` CP | Query CP — `es_conexion_principal=1`, `database_type=multi` |
| 3 | Smoke routing S9 | Login ERP tenant; query simple vía gateway |
| 4 | Cache invalidada | Sin metadata stale &lt;5 s post-S8 |
| 5 | Admin seed DP | Login admin con credenciales 201 |

Registrar sign-off en `docs/implementation/HYBRID_F4_GATE_EVIDENCE_GF402.json`.

---

## 4. Retry (failed → reprovisioning)

**Precondición:** `provisioning_state=failed`, `retry_allowed=true`.

```http
POST /api/v1/clientes/{cliente_id}/provisioning/retry
Authorization: Bearer <superadmin_jwt>
```

**Validar:** máximo 2 reintentos operativos sin duplicar BD (`nombre_bd` idempotente). E2E mock: `test_retry_twice_dispatches_without_duplicate_active_runs`.

---

## 5. Abort + compensación

**Precondición:** `provisioning_state=provisioning`, `abort_allowed=true`.

```http
POST /api/v1/clientes/{cliente_id}/provisioning/abort
Authorization: Bearer <superadmin_jwt>
Content-Type: application/json

{ "reason": "ops cancel staging test" }
```

**Efectos esperados (F4-10):**

1. Transición `provisioning` → `failed`
2. Invalidación cache (S9)
3. Soft-delete / cleanup `cliente_conexion` (S8)
4. `DROP DATABASE` físico (S3) — solo si `provisioning_state=failed`
5. Reset steps desde orden saga 3

**Guard:** compensación **prohibida** en `ready`.

---

## 6. Tenants failed — limpieza manual (pre-F4-10 interim / residual)

Si compensación automática no completó:

1. Verificar `provisioning_state=failed` en CP
2. Confirmar ausencia de tráfico ERP (fail-closed RI-39)
3. DROP DATABASE huérfano vía runbook SRE (credenciales DDL)
4. Eliminar / desactivar `cliente_conexion` residual
5. Invalidar cache: reinicio worker o invalidación explícita

---

## 7. Observabilidad — 5 señales mínimas (contrato §16)

| Señal | Uso ops |
|-------|---------|
| `dedicated.provisioning.started` | Conteo altas dedicated |
| `dedicated.provisioning.step.completed` | Latencia por step |
| `dedicated.provisioning.ready` | SLA time-to-ready (`duration_seconds`) |
| `dedicated.provisioning.failed` | Alertas + runbook abort |
| `dedicated.provisioning.retry` | Reintentos ops |

Manifest: `docs/implementation/HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json`

Dashboard staging: configurar en F5b; E2E mock valida contrato de eventos.

---

## 8. CI gates (automático)

| Gate | Script | Obligatorio |
|------|--------|-------------|
| `SHARED_ONBOARDING_REQUIRED_CHECK` | `scripts/validate_shared_onboarding_required_check.py` | Todo PR F4 |
| `shared-regression` | `scripts/validate_shared_regression.py` | Todo PR F4 |
| F4 E2E mock | `scripts/validate_f4_provisioning_e2e.py` | PR-F4-12+ |

---

## 9. Sign-off G-F4-02 (Tenant Ready staging)

| ID | Item | Estado |
|----|------|--------|
| GF4-02-01 | PR-F4-06…09 merged | ☐ |
| GF4-02-02 | Dedicated seed DP verificado | ☐ |
| GF4-02-03 | Metadata + cache + smoke OK | ☐ |
| GF4-02-04 | Tenant staging `ready` E2E manual | ☐ |
| GF4-02-05 | SHARED_ONBOARDING + shared-regression green | ☐ |
| GF4-02-06 | Runbook failed tenants ack SRE | ☐ |
| GF4-02-07 | Tag `hybrid-gate-f4-02` | ☐ |

Evidencia: `docs/implementation/HYBRID_F4_GATE_EVIDENCE_GF402.json`

---

## 10. Sign-off G-F4-03 (cierre F4)

| ID | Item | Estado |
|----|------|--------|
| GF4-03-01 | PR-F4-10…12 merged | ☐ |
| GF4-03-02 | DOD-F4 completo | ☐ |
| GF4-03-03 | E2E mock + staging sign-off | ☐ |
| GF4-03-04 | Métricas provisioning staging | ☐ |
| GF4-03-05 | Security review F4 | ☐ |
| GF4-03-06 | OpenAPI cumulative F0–F4 clean | ☐ |
| GF4-03-07 | Zero ERP diffs | ☐ |
| GF4-03-08 | Este runbook | ☐ |
| GF4-03-09 | Tag `hybrid-gate-f4-complete` | ☐ |

Evidencia: `docs/implementation/HYBRID_F4_GATE_EVIDENCE_GF403.json`

### Tag final

Tras merge PR-F4-12 y checklist G-F4-03 100%:

```bash
git tag -a hybrid-gate-f4-complete -m "F4 Dedicated Provisioning complete — DOD-F4"
git push origin hybrid-gate-f4-complete
```

---

## 11. Rollback

| Escenario | Acción |
|-----------|--------|
| Dedicated defectuoso en staging | `DEDICATED_ENABLED=false`; shared sin impacto |
| Tenant stuck `provisioning` | POST abort; verificar compensación |
| BD huérfana post-failed | SRE DROP manual + cleanup CP |

---

## 12. Contactos

| Rol | Responsabilidad |
|-----|-----------------|
| Platform / Implementador | Saga, API status |
| SRE | DDL creds, orphan DB |
| QA | E2E staging G-F4-02 |
| Architect | Gate Review F5b |
