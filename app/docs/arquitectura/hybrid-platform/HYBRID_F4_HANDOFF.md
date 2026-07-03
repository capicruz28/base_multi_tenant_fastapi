# Hybrid Platform — F4 Handoff Document

**Documento:** HYBRID_F4_HANDOFF  
**Versión:** 1.0  
**Fecha:** 2026-06-25  
**De:** Etapa 6 (F0–F3) — CERRADA  
**Para:** Etapa 7 (F4) — Dedicated Database Provisioning  
**Baseline origen:** BL-1.0  
**Baseline destino:** BL-F4-1.0 (APROBADO)  
**Plan ejecución:** IP-2.0.1 (READY FOR IMPLEMENTATION)

---

## 1. Propósito

Documento de **traspaso formal** entre el cierre de Etapa Hybrid F0–F3 y el inicio de F4. Define prerrequisitos, primer paso operativo, reutilización de componentes y criterios de éxito.

---

## 2. Trazabilidad documental

```
BL-1.0 (FROZEN)
    ├── IP-1.0 → F0–F3 IMPLEMENTADO
    │       └── HYBRID_STAGE_COMPLETION_REPORT.md (cierre)
    │       └── HYBRID_IMPLEMENTATION_SUMMARY.md (inventario)
    │       └── HYBRID_TECHNICAL_DEBT_REGISTER.md (deuda)
    │
    └── Gate Review GO F4
            └── BL-F4-1.0 (baseline provisioning)
                    └── IP-2.0.1 (12 PRs)
                            └── PRE-F4 Gate 0 → PR-F4-01
```

| Documento | Función en handoff |
|-----------|-------------------|
| **BL-1.0** | Guardrails transversales G-01–G-20; prohibiciones ERP |
| **IP-1.0** | Evidencia F0–F3 completado |
| **BL-F4-1.0** | Saga S1–S10, CP/DP, estados, compensación |
| **IP-2.0.1** | WPs, PRs, whitelists, DoD, gates G-F4-01…03 |

---

## 3. Estado al momento del handoff

| Dimensión | Estado |
|-----------|--------|
| Hybrid Gateway (Capa 1–2) | **Operativo** — tests + CI |
| Dedicated runtime routing | **Listo** — fail-closed RI-39 |
| Dedicated provisioning | **No existe** — inicia F4 |
| Shared tenants | **Sin regresión** |
| Dedicated producción | **DESHABILITADO** |
| IP-2.0.1 | **READY FOR IMPLEMENTATION** |
| Etapa F0–F3 | **OFICIALMENTE CERRADA** |

---

## 4. Componentes F0–F3 que F4 debe reutilizar (no reimplementar)

| Componente | Ruta | Uso F4 |
|------------|------|--------|
| Connection metadata resolver | `app/core/tenant/routing.py` | Smoke S9; post-activate |
| Cache invalidation | `invalidate_client_connection_cache()` | PR-F4-09 obligatorio |
| Async engines | `connection_async.py` | Runtime `tenant_{cliente_id}` |
| Query pipeline | `queries_async.py` | Seed S7 en DP |
| Defensive filter | `query_helpers.py` | Queries seed dedicated |
| Fail-closed policy | routing RI-39 | Pre-Ready blocking |
| Test harness | `tests/integration/test_hybrid_*` | Base E2E F4-12 |
| Mock metadata | `helpers/hybrid_mock_metadata.py` | Tests sin BD real |
| Whitelist gate | `check_database_type_whitelist.py` | Regresión F4 |
| Shared regression | `validate_shared_regression.py` | Todo PR F4 |
| ConexionService | `conexion_service.py` | S8 wrap — **extender**, no fork |
| Onboarding services | `cliente_onboarding_service.py`, etc. | Lógica S7 adaptada DP |

**Prohibido F4:** `DatabaseConnection.DEDICATED`, `execute_*_dedicated`, forks ERP.

---

## 5. Qué inicia formalmente en F4

| # | Capacidad | BL-F4 | IP-2.0.1 |
|---|-----------|-------|-----------|
| 1 | State machine CP `provisioning/ready/failed` | §4 | F4-01, F4-02 |
| 2 | Job dispatcher async in-process | §8 | F4-03 |
| 3 | CREATE DATABASE + login SQL | §11 S3 | F4-04 |
| 4 | bootstrap_v2 runner per-tenant | §11 | F4-05 |
| 5 | Catalog seed ADR-011 | §12 S6 | F4-06 |
| 6 | Tenant seed en Data Plane | §12 S7 | F4-07 |
| 7 | Saga orchestrator S1–S10 | §8 | F4-08 |
| 8 | Activación metadata + cache + Ready | §10, §13 | F4-09 |
| 9 | Compensation semi-auto | §9 | F4-10 |
| 10 | API status/retry/abort | §8 | F4-11 |
| 11 | E2E + observability + runbook | §16, §19 | F4-12 |
| 12 | `DEDICATED_ENABLED` flag | IP-2.0.1 | F4-08 |

**Primer entregable código:** PR-F4-01 (CP provisioning state tables) — **solo tras PRE-F4 Gate 0**.

---

## 6. Prerrequisitos Dedicated Database (PRE-F4 Gate 0)

Ejecutar checklist IP-2.0.1 §11 **antes** de PR-F4-01:

| ID | Item | Responsable |
|----|------|-------------|
| PF4-01 | G-F3 checklist 100% | Tech Lead |
| PF4-02 | Tag `hybrid-bl10-f0-f3-complete` | DevOps |
| PF4-03 | Gate Review Go F4 — minutes | Architect |
| PF4-04 | BL-F4-1.0 ack equipo | All |
| PF4-05 | ADR-F4-01…05 ratificados | Architect |
| PF4-06 | F3.5 catalog list ADR-011 firmada | Platform |
| PF4-07 | Q-030 cerrado (= BL-F4-1.0 / IP-2.0.1) | Architect |
| PF4-08 | Credenciales SQL DDL staging (Vault) | SRE |
| PF4-09 | `DEDICATED_ENABLED=false` verificado prod | SRE |
| PF4-10 | Branch `hybrid/f4-provisioning` creada | Tech Lead |
| PF4-11 | `SHARED_ONBOARDING_REQUIRED_CHECK` en CI/docs | DevOps |

### SHARED_ONBOARDING_REQUIRED_CHECK (IP-2.0.1 §10.1)

```text
pytest tests/unit/test_onboarding_rbac_bootstrap.py \
       tests/unit/test_onboarding_menu_bootstrap.py \
       tests/unit/test_minimal_erp_tenant_bootstrap.py \
       tests/unit/test_platform_identity_bootstrap.py \
       tests/unit/test_tenant_exception_propagation.py \
       tests/unit/test_base_operative_t1.py \
       -q --tb=line
```

Obligatorio en todo PR F4 desde F4-07; recomendado desde F4-01 si se toca `modules/tenant/`.

---

## 7. Orden de ejecución F4 (resumen IP-2.0.1 §13)

```
PRE-F4 Gate 0
  → PR-F4-01 → F4-02 → (F4-03 ∥ F4-04) → F4-05
  → G-F4-01
  → F4-06 → F4-07 (merge secuencial S6→S7)
  → F4-08 → F4-09
  → G-F4-02 (Tenant Ready staging)
  → F4-10 → F4-11 → F4-12
  → G-F4-03 / hybrid-gate-f4-complete
  → Gate Review F5b
```

---

## 8. Restricciones heredadas (BL-1.0 + BL-F4)

| ID | Restricción |
|----|-------------|
| G-01 | Zero diff ERP operativo |
| G-07 | OpenAPI existing stable; F4 solo aditivo |
| BLF4-R02 | `POST /clientes/` response invariant |
| BLF4-R03 | `POST /conexiones/` metadata-only (sin auto-merge MVP) |
| BLF4-R04 | Seed dedicated solo DP |
| BLF4-R05 | Metadata después DDL+seed |
| BLF4-R19 | Merge F4-06 antes F4-07 |

Lista completa: IP-2.0.1 §8.

---

## 9. Deuda técnica relevante para F4

Ver `HYBRID_TECHNICAL_DEBT_REGISTER.md` §5, §11.

**Crítico resolver en F4:** TD-PROV-01…08, TD-CAT-01, TD-CACHE-01.

**No resolver en F4:** TD-L5-01…16 (congelada); TD-ERP-01.

---

## 10. Contratos externos

| Contrato | Impacto F4 |
|----------|------------|
| `docs/contracts/CONNECTION_CREATION_API_CONTRACT.md` | Permanece metadata-only; S8 usa servicio interno |
| OpenAPI `POST /clientes/` | Invariant — optional `provisioning_status_url` aditivo |
| JWT / Session | Sin cambio F4 |
| Frontend | Transparente (G-03) |

---

## 11. Entornos

| Entorno | F4 expectation |
|---------|----------------|
| **Local / docker-compose** | Harness mock; no CREATE DATABASE |
| **Staging** | Primer tenant dedicated Ready manual |
| **Producción** | `DEDICATED_ENABLED=false` hasta G-F4-03 + F6 |

---

## 12. Criterios de éxito F4 (handoff target)

| Gate | Criterio |
|------|----------|
| G-F4-01 | DDL pipeline staging OK |
| G-F4-02 | 1 tenant dedicated **Ready** staging |
| G-F4-03 | DOD-F4 completo; tag `hybrid-gate-f4-complete` |

Post-F4 → criterios F5b: IP-2.0.1 §14.

---

## 13. Roles en Etapa 7

| Rol | F4 responsabilidad |
|-----|-------------------|
| Implementador | PR IP-2.0.1 §5; whitelist §7 |
| Architect | BL-F4 traceability; PRE-F4 sign-off |
| SRE | DDL creds; orphan DB cleanup; PF4-08/09 |
| QA | Staging E2E; G-F4-02 |
| Security | PR-F4-04, F4-07, F4-11 |
| Tech Lead | Merge order; gates |

---

## 14. Primer paso operativo recomendado

1. **Re-ejecutar PRE-F4 Gate 0** (PF4-01…11) con evidencia actualizada post-cierre Etapa 6.
2. Crear branch `hybrid/f4-provisioning` desde `main` @ `hybrid-bl10-f0-f3-complete`.
3. Registrar `SHARED_ONBOARDING_REQUIRED_CHECK` en CI (PF4-11).
4. Ratificar ADR-F4-01…05 y F3.5 catalog list si no formalizados.
5. **Solo entonces** abrir PR-F4-01.

---

## 15. Referencias

| Documento | Ruta |
|-----------|------|
| Stage Completion | `HYBRID_STAGE_COMPLETION_REPORT.md` |
| Implementation Summary | `HYBRID_IMPLEMENTATION_SUMMARY.md` |
| Technical Debt | `HYBRID_TECHNICAL_DEBT_REGISTER.md` |
| IP-2.0.1 | `implementation-planning/IP-2.0_F4_IMPLEMENTATION_PLAN.md` |
| BL-1.0 | `architecture-baseline/01_ARCHITECTURE_BASELINE.md` |
| Change Surface Capa 3 | `impact-analysis/03_CHANGE_SURFACE.md` |

---

## 16. Declaración de handoff

La Etapa Hybrid **F0–F3** entrega un **Persistence Gateway consolidado** listo para soportar tenants dedicated **una vez completado F4**. El runtime Hybrid **no requiere cambios arquitectónicos** para F4; F4 construye la **Capa 3 Provisioning** sobre infraestructura existente.

**Handoff status:** **COMPLETE** — awaiting PRE-F4 Gate 0 pass → PR-F4-01.
