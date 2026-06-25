# 05 — Risk Register

**Etapa:** 6.0 — Repository Readiness  
**Fecha:** 2026-06-25  
**Baseline:** BL-1.0 | **Plan:** IP-1.0

---

## 1. Leyenda severidad

| Nivel | Definición | Bloquea F0 |
|-------|------------|------------|
| **CRITICAL** | Impide F0 o viola BL de forma irrecuperable | Sí |
| **HIGH** | Impide F1/F3 o requiere replan significativo | No |
| **MEDIUM** | Mitigable en fase correspondiente | No |
| **LOW** | Deuda conocida / doc-only | No |

---

## 2. Registro de riesgos

### RR-CRIT — (ninguno)

No se identificaron riesgos CRITICAL. El repositorio permite crear el harness F0 sin modificar producción.

---

### RR-H01 — SLS queries bypass gateway

| Campo | Valor |
|-------|-------|
| **ID** | RR-H01 |
| **Severidad** | **HIGH** |
| **Fase afectada** | F1 |
| **Descripción** | `pedido_detalle_queries.py` y `cotizacion_detalle_queries.py` invocan `get_connection_for_tenant` directamente, evitando `execute_*`. |
| **Evidencia** | `app/infrastructure/database/queries/sls/` — 2 archivos |
| **Guardrail** | G-09 (all SQL via gateway) |
| **Impacto** | Dedicated routing puede no aplicarse en esos paths; tenant filter inconsistente |
| **Mitigación IP** | F1-WP09 Repository/query delegation audit |
| **Bloquea F0** | No |
| **Owner** | Implementador F1 |
| **Estado** | Open |

---

### RR-H02 — F3 scope database_type incompleto

| Campo | Valor |
|-------|-------|
| **ID** | RR-H02 |
| **Severidad** | **HIGH** |
| **Fase afectada** | F3 |
| **Descripción** | IP F3 planifica cleanup en 3 archivos L5; repo tiene ~15 archivos producción con `database_type`. |
| **Evidencia** | `03_WHITELIST_VALIDATION.md` §3.2 |
| **Guardrail** | G-10 |
| **Impacto** | F3-WP04 grep gate fallará post-cleanup parcial; deuda L5 persistente |
| **Mitigación** | Ampliar F3 con WPs adicionales o fase F3.1; no requiere ADR nuevo (mismo RD-03) |
| **Bloquea F0** | No |
| **Owner** | Arquitecto + Tech Lead pre-F3 |
| **Estado** | Open |

---

### RR-M01 — Async engines no cerrados en shutdown

| Campo | Valor |
|-------|-------|
| **ID** | RR-M01 |
| **Severidad** | **MEDIUM** |
| **Fase afectada** | F1 |
| **Descripción** | `close_all_async_engines()` existe pero `main.py` solo invoca `close_all_pools()` en lifespan shutdown. |
| **Evidencia** | `connection_async.py`, `main.py` |
| **Impacto** | Resource leak en deploy/restart; dedicated engines acumulados |
| **Mitigación** | F1-WP01 (planificado) |
| **Bloquea F0** | No |
| **Estado** | Open — tracked IP |

---

### RR-M02 — Repositories legacy fuera gateway

| Campo | Valor |
|-------|-------|
| **ID** | RR-M02 |
| **Severidad** | **MEDIUM** |
| **Fase afectada** | F1 |
| **Descripción** | 3 repository files usan conexión directa pattern legacy |
| **Evidencia** | `app/infrastructure/database/repositories/` |
| **Impacto** | Dedicated path no unificado |
| **Mitigación** | F1-WP09 |
| **Bloquea F0** | No |
| **Estado** | Open |

---

### RR-M03 — rol_service conexión directa

| Campo | Valor |
|-------|-------|
| **ID** | RR-M03 |
| **Severidad** | **MEDIUM** |
| **Fase afectada** | F3 |
| **Descripción** | `rol_service.py` ~L1244 usa `get_db_connection()` además de database_type L5 |
| **Impacto** | Cleanup F3-WP03 más amplio de lo estimado (~100 LOC) |
| **Mitigación** | Incluir en F3-WP03 scope real |
| **Bloquea F0** | No |
| **Estado** | Open |

---

### RR-M04 — CI gates no implementados

| Campo | Valor |
|-------|-------|
| **ID** | RR-M04 |
| **Severidad** | **MEDIUM** |
| **Fase afectada** | F0–F3 |
| **Descripción** | hybrid job, erp-guard, openapi-diff, database_type grep ausentes en CI |
| **Impacto** | Regresiones no detectadas hasta gates activos |
| **Mitigación** | F0-WP05, F2-WP02, F3-WP04 per IP |
| **Bloquea F0** | No — F0 los crea |
| **Estado** | Expected pre-F0 |

---

### RR-L01 — Inconsistencias conteo IP

| Campo | Valor |
|-------|-------|
| **ID** | RR-L01 |
| **Severidad** | **LOW** |
| **Descripción** | IP docs divergen 18/20/22 WPs/PRs |
| **Impacto** | Confusión operativa menor |
| **Mitigación** | Usar `03`/`10` como fuente (20/20); IP-1.1 opcional |
| **Bloquea F0** | No |

---

### RR-L02 — DEDICATED_ENABLED flag ausente

| Campo | Valor |
|-------|-------|
| **ID** | RR-L02 |
| **Severidad** | **LOW** |
| **Descripción** | Config flag mencionado IP no presente en `config.py` |
| **Impacto** | Ninguno F0–F3 (opcional F1+) |
| **Mitigación** | Crear si equipo decide feature toggle |
| **Bloquea F0** | No |

---

### RR-L03 — IAM sessions v2 cambios paralelos

| Campo | Valor |
|-------|-------|
| **ID** | RR-L03 |
| **Severidad** | **LOW** |
| **Descripción** | Branch tiene trabajo IAM sessions v2 no en BL hybrid scope |
| **Impacto** | Posible conflicto merge en auth/deps si no coordinado |
| **Mitigación** | Branch isolation; G-F0 review cross-team |
| **Bloquea F0** | No |

---

## 3. Resumen por severidad

| Severidad | Count | Bloquean F0 |
|-----------|-------|-------------|
| CRITICAL | 0 | — |
| HIGH | 2 | 0 |
| MEDIUM | 4 | 0 |
| LOW | 3 | 0 |
| **Total** | **9** | **0** |

---

## 4. Riesgos por fase

| Fase | Riesgos aplicables |
|------|-------------------|
| F0 | RR-M04 (expected), RR-L01, RR-L03 |
| F1 | RR-H01, RR-M01, RR-M02 |
| F2 | RR-M04 |
| F3 | RR-H02, RR-M03 |

---

## 5. Escalación

| Condición | Acción |
|-----------|--------|
| Nuevo CRITICAL detectado en F0 | Stop merge; re-audit Etapa 6 |
| RR-H02 sin plan pre-F3 | No iniciar F3 hasta scope ampliado |
| RR-H01 sin resolución post-F1 | Escalar a Gate Review |

---

## 6. Conclusión

**Ningún riesgo bloquea autorización F0.** Riesgos HIGH documentados para F1/F3 con mitigación en IP-1.0 o nota de ejecución.
