# 01 — Repository Readiness Report

**Etapa:** 6.0 — Repository Readiness (Pre-Implementation Audit)  
**Fecha auditoría:** 2026-06-25  
**Baseline:** BL-1.0 (FROZEN)  
**Plan:** IP-1.0  
**Tipo:** Inspección read-only — **sin modificación de código ni arquitectura**

---

## 1. Resumen ejecutivo

Se auditó el repositorio `base_multi_tenant_fastapi` contra BL-1.0 e IP-1.0 para autorizar el inicio de **F0 (Test Harness)**.

| Veredicto | Resultado |
|-----------|-----------|
| **Repositorio alineado con supuestos AS-IS** | **Sí** — infra core intacta |
| **IP-1.0 ejecutable sin modificar plan** | **Sí para F0–F1**; **ajustes menores recomendados F3** |
| **Desviaciones críticas que bloquean F0** | **Ninguna** |
| **Decisión F0** | **GO — REPOSITORY READY FOR F0** |
| **Autorización PR-F0-01** | **Sí** |

**Readiness Score global F0–F3:** **72/100** (ver `06_IMPLEMENTATION_READINESS_SCORE.md`)  
**Readiness Score F0 only:** **88/100**

---

## 2. Estado del repositorio

| Dimensión | Estado | Notas |
|-----------|--------|-------|
| Whitelist BL archivos infra | ✅ Existen | 9/9 paths verificados |
| `execute_*` API | ✅ Estable | Firmas sin cambio vs E5 |
| UnitOfWork | ✅ Estable | Patrón AS-IS preservado |
| SessionLocal / Depends(get_db) | ✅ Ausente | 0 coincidencias |
| `create_async_engine` | ✅ Centralizado | Solo `connection_async.py` |
| `close_all_async_engines` | ⚠️ Gap AS-IS | Existe; **no** invocado en `main.py` (F1-WP01) |
| Tests hybrid IP-1.0 | ⏳ Por crear | Esperado — objetivo F0 |
| CI gates IP (openapi, erp-guard) | ⏳ Por crear | F0–F2 |
| `database_type` L5 | ⚠️ Deuda ampliada | Más archivos que F3 planifica |
| ERP query bypass gateway | ⚠️ 2 archivos SLS | Pre-existente |

---

## 3. Validaciones ejecutadas

| # | Validación | Resultado |
|---|------------|-----------|
| V-01 | Whitelist BL archivos existen | ✅ PASS |
| V-02 | Archivos WP IP existen | ✅ PASS (targets F1–F3) |
| V-03 | Rutas IP correctas | ✅ PASS (rol_service path confirmado) |
| V-04 | `database_type` fuera whitelist | ⚠️ FAIL parcial — 15+ archivos L5 (ver `03`) |
| V-05 | `create_async_engine` | ✅ PASS — único en connection_async |
| V-06 | Conexiones SQL fuera gateway | ⚠️ 2 query files SLS + repos/scripts conocidos |
| V-07 | SessionLocal | ✅ PASS — 0 |
| V-08 | Depends(get_db) | ✅ PASS — 0 |
| V-09 | Firmas execute_* | ✅ PASS |
| V-10 | UnitOfWork | ✅ PASS |
| V-11 | OpenAPI snapshot presente | ✅ PASS — `app/docs/openapi_snapshot.json` |
| V-12 | Módulos ERP | ✅ 32 routers presentation (consistente E0) |
| V-13 | Tests IP referenciados | ⏳ Ninguno existe — **crear en F0** (esperado) |
| V-14 | BL / IP / repo conflictos | ⚠️ Ver `04_CONSISTENCY_REPORT` |

---

## 4. Desviaciones encontradas

### 4.1 Esperadas (documentadas AS-IS / BL)

| Desviación | Impacto F0 | Acción |
|------------|------------|--------|
| `close_all_async_engines` no en shutdown | Ninguno | F1-WP01 |
| `database_type` en user_context, rol_service, middleware | Ninguno | F3 |
| Tests hybrid inexistentes | Ninguno | F0 crea |

### 4.2 No documentadas en IP F3 scope (HIGH — no bloquea F0)

| Desviación | Archivos adicionales con `database_type` L5 |
|------------|---------------------------------------------|
| F3 scope IP incompleto vs repo | `auth_service.py`, `user_service.py`, `user_builder.py`, `permisos_negocio_service.py`, `permisos_usuario_service.py`, `auth/endpoints.py`, `empresa_preference.py`, `permission_resolver.py`, `menu_resolver.py`, `deps.py`, `impersonation_rbac.py`, superadmin services |

**Nota:** No modifica BL-1.0. Registrar en `05_RISK_REGISTER`; ampliar F3 durante ejecución (sin nueva ADR si mismo objetivo RD-03).

### 4.3 Query layer bypass (MEDIUM)

| Archivo | Patrón |
|---------|--------|
| `queries/sls/pedido_detalle_queries.py` | `get_connection_for_tenant` directo |
| `queries/sls/cotizacion_detalle_queries.py` | Idem |

Contradice G-09 parcialmente en capa queries ERP. **No bloquea F0.** Evaluar en F1-WP09 o ADR si refactor requerido (tocaría ERP queries — fuera whitelist BL).

---

## 5. Riesgos (resumen)

| Severidad | Count | Bloquea F0 |
|-----------|-------|------------|
| CRITICAL | 0 | — |
| HIGH | 2 | No |
| MEDIUM | 4 | No |
| LOW | 3 | No |

Detalle: `05_RISK_REGISTER.md`

---

## 6. Inconsistencias documentales IP-1.0

| ID | Issue | Bloquea F0 |
|----|-------|------------|
| IP-INC-01 | WP count: 01 dice 22, 02/10 dicen 20 | No |
| IP-INC-02 | PR count: 01 dice 18, 03/10 dicen 20 | No |
| IP-INC-03 | 02 conclusión dice "22 WPs" vs tabla 20 | No |

**No se corrige en Etapa 6.0** — reportar solo.

---

## 7. Readiness Score

| Scope | Score |
|-------|-------|
| F0 | **88/100** |
| F1 | **82/100** |
| F2 | **75/100** |
| F3 | **58/100** (scope L5 gap) |
| **Global F0–F3** | **72/100** |

---

## 8. Go / No-Go F0

# GO — REPOSITORY READY FOR IMPLEMENTATION (F0)

**Autorización formal:** Iniciar **PR-F0-01** conforme IP-1.0.

**Condiciones (no bloqueantes):**
1. Reconocer F3 scope ampliado vs IP (riesgo RR-H02)
2. No merge F1 hasta G-F0
3. CI gates documentados se implementan en F0–F2 según plan

**No autorizado aún:** F4+, dedicated production, modificación ERP queries SLS sin gate.

---

## 9. Recomendaciones

| # | Recomendación | Cuándo |
|---|---------------|--------|
| R-01 | Ejecutar Pre-flight checklist IP `08` §1 | Antes PR-F0-01 |
| R-02 | Crear `tests/integration/conftest_hybrid.py` per PR-F0-01 | F0 |
| R-03 | Ampliar F3 WP list con archivos L5 adicionales identificados | Pre-F3 (not IP change — execution note) |
| R-04 | Evaluar SLS bypass en F1 architecture review | F1-WP09 |
| R-05 | Resolver IP-INC-01/02 en IP-1.1 doc-only (opcional) | Post-F0 |

---

## 10. Confirmaciones Etapa 6.0

| Confirmación | Estado |
|--------------|--------|
| NO se modificó código fuente | ✅ |
| NO se modificó arquitectura / BL / IP / ADR / RD | ✅ |
| Solo documentación `repository-readiness/` creada | ✅ |

---

## 11. Documentos de esta etapa

Ver `02`–`07` en `repository-readiness/`.

**Decisión final:** **REPOSITORY READY FOR IMPLEMENTATION (F0)** — **PR-F0-01 autorizado.**
