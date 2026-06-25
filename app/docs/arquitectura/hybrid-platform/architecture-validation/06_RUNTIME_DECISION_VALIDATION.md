# 06 — Runtime Decision Validation

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Alcance:** Validación adversarial RD-01 a RD-15 (foco en solicitados)

---

## 1. Metodología

Por cada RD: Correcta / Debe modificarse / Debe ampliarse / Riesgos / Dependencias ocultas.

---

## 2. RD-01 — Resolución per operación de datos

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ✅ **Correcta** |
| **Justificación** | Alineada AS-IS; evita request-scoped session (G-17); L-A cache mitiga costo |
| **Debe modificarse** | No |
| **Debe ampliarse** | Documentar explícitamente interacción con UoW (una resolución al abrir scope) — parcialmente en E5 06 |
| **Riesgos** | N connections/request performance (AR-M01) |
| **Dependencias ocultas** | Performance testing Fase 2; no funcional |

---

## 3. RD-06 — Persistence Gateway único

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ✅ **Correcta** con ⚠️ |
| **Justificación** | Único punto Shared/Dedicated; G-05 compliant en target |
| **Debe modificarse** | No el principio; sí la **materialización** — hoy disperso |
| **Debe ampliarse** | Policy enforcement repositories (H-06); grep CI |
| **Riesgos** | Bypass vía repositories, get_db_connection directo platform |
| **Dependencias ocultas** | Fase 1 no crea módulo único — riesgo drift si no hay checklist |

---

## 4. RD-07 — Operation class control_plane \| tenant_data

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ⚠️ **Correcta pero incompleta** |
| **Justificación** | Clara semántica ADMIN/DEFAULT; alinea E3 |
| **Debe modificarse** | No |
| **Debe ampliarse** | **Sí — obligatorio:** tabla decisión por entidad/transversal (sesiones, auth_audit_log, auth_config) |
| **Riesgos** | Misclassification → RI-32 cross-plane write |
| **Dependencias ocultas** | RD-11 bloquea clasificación sesiones IAM |

**Acción requerida:** Ampliar con matriz entidad→operation_class antes F4.

---

## 5. RD-08 — Fallback Shared si metadata ausente

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ✅ **Correcta** para backward compat |
| **Justificación** | G-13; protege tenants legacy |
| **Debe modificarse** | No |
| **Debe ampliarse** | Logging/alert cuando fallback ocurre — detectar misconfigurations |
| **Riesgos** | Tenant mal migrado a dedicated sin metadata → silently shared (**mitigado RI-39** para explicit dedicated) |
| **Dependencias ocultas** | Requiere flag/mode explicit en registry, no solo ausencia metadata |

**Escenario adversarial:** Si Installation Mode=dedicated pero metadata row deleted → RI-39 debe fail. **Verificar** que mode explicit no depende solo de cliente_conexion row.

---

## 6. RD-11 — Session store location deferred

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ❌ **Debe cerrarse — no puede permanecer deferida para Etapa 6 dedicated** |
| **Justificación diferimiento** | L5 behavior identical either way — **verdadero para contrato HTTP**, **falso para L6 routing** |
| **Debe modificarse** | **Sí** — convertir en decisión con recomendación ADR-002 Alt A para MVP |
| **Debe ampliarse** | Impacto Redis bridge, probe, cleanup job, impersonation |
| **Riesgos** | AR-C01 Critical; R-C05 E0 |
| **Dependencias ocultas** | Q-011 Redis SoT; Q-012 impersonation dedicated; refresh_token_cleanup_job route |

**Recomendación validación:** Cerrar RD-11 adoptando **ADR-002 Alternativa A (central)** para MVP con acta formal — permite F1–F4 paralelo; desbloquea F5.

---

## 7. RD-12 — Onboarding saga multi-fase

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ✅ **Correcta** dirección; ⚠️ **insuficiente detalle** |
| **Justificación** | Única forma cross-plane sin 2PC; RD-12 alinea ADR-004 |
| **Debe modificarse** | No el modelo saga |
| **Debe ampliarse** | **Sí:** pasos, idempotency keys, estados Provisioning, compensación por step (Q-030) |
| **Riesgos** | AR-H04; tenants stuck Provisioning |
| **Dependencias ocultas** | Q-031 metadata timing; catálogos AR-H01; DDL pipeline Q-061 |

---

## 8. RD-13 — Migration blocks ERP traffic

| Aspecto | Evaluación |
|---------|------------|
| **Veredicto** | ✅ **Correcta** para MVP |
| **Justificación** | Elimina RR-40; pragmático |
| **Debe modificarse** | No para MVP |
| **Debe ampliarse** | UX tenant Migrando; superadmin read-only?; rollback procedure |
| **Riesgos** | Downtime comercial Q-050; SLA enterprise Q-071 |
| **Dependencias ocultas** | Cache invalidation all workers TD-09; RI-14 enforcement middleware |

---

## 9. Otras RD (resumen validación)

| RD | Veredicto | Nota |
|----|-----------|------|
| RD-02 Tenant before auth | ✅ | AS-IS aligned |
| RD-03 Mode invisible L5 | ⚠️ | Correcta; AS-IS viola — F3 |
| RD-04 Refresh tenant from token | ✅ | Critical correct |
| RD-05 Impersonation JWT tenant | ✅ | deps gap AR-C05 separado |
| RD-09 Request-scoped context | ✅ | |
| RD-10 ERP session gate | ✅ | |
| RD-14 Health minimal | ✅ | |
| RD-15 Permission resolution service | ⚠️ | Ampliar diseño técnico |

---

## 10. Matriz consolidada

| RD | Correcta | Modificar | Ampliar | Bloqueante E6 |
|----|----------|-----------|---------|----------------|
| RD-01 | ✅ | | ⚠️ | No |
| RD-06 | ✅ | | ⚠️ | No |
| RD-07 | ⚠️ | | ✅ | F4 |
| RD-08 | ✅ | | ⚠️ | No |
| RD-11 | | ✅ | ✅ | **Sí dedicated** |
| RD-12 | ✅ | | ✅ | F4 |
| RD-13 | ✅ | | ⚠️ | F7 only |

---

## 11. Conclusión

**11 de 15 RD validadas como correctas** en dirección. **RD-11 requiere cierre inmediato** antes dedicated. **RD-07 y RD-12 requieren ampliación** con matrices concretas. Ninguna RD debe **modificarse** en principio fundamental — solo RD-11 pasa de "deferida" a "decidida".
