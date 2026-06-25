# 01 — Architecture Consistency Review

**Etapa:** 5.5 — Architecture Validation & Implementation Readiness Review  
**Fecha:** 2026-06-25  
**Rol:** Arquitecto Principal (revisión adversarial)  
**Alcance:** Etapas 0–5  
**Restricción:** Solo revisión documental. Sin modificación de código.

---

## 1. Propósito

Verificar coherencia interna del corpus arquitectónico aprobado en borrador. **No se asume corrección.** Se buscan contradicciones, ambigüedades y deuda documental.

---

## 2. Metodología

| Paso | Acción |
|------|--------|
| 1 | Lectura cruzada E0→E5 por dominio |
| 2 | Confrontación decisiones vs invariantes |
| 3 | Confrontación ownership E3 vs routing E5 |
| 4 | Confrontación AS-IS E0 vs diseño target |
| 5 | Clasificación: ✅ Consistente / ⚠️ Tensión / ❌ Contradicción |

---

## 3. Responsabilidades y límites de capas

| Tema | E1/E2 | E4 | E5 | Veredicto |
|------|-------|----|----|-----------|
| L5 ignora Installation Mode | ✅ P5, G-05 | ✅ RD-03, RI-32 | ✅ TD-08 | ⚠️ **Tensión AS-IS:** middleware y IAM/RBAC L5 aún consumen `database_type` |
| L6 único resolutor | ✅ E2 Capa 1 | ✅ RD-06 | ✅ 01_GATEWAY | ✅ Consistente en diseño target |
| IAM transversal | ✅ E1, E3 | ✅ Context model | ✅ operation_class | ✅ Consistente |
| Platform no opera ERP | ✅ E1 | ✅ RI-47+ | ✅ TB-05 | ⚠️ Onboarding AS-IS viola; target saga OK |
| ERP no resuelve conexión | ✅ G-09 | ✅ RI-31 | ✅ QL-02 | ⚠️ Repositories legacy pueden bypass |

**Contradicción detectada C-01:** E4 declara RI-32 (L5 no conoce mode) pero E0/E4 RR-81 documentan que TenantMiddleware expone `database_type` en ContextVar consumible por L5. E5 reconoce gap pero **no cierra** la contradicción — solo la difiere a Fase 3.

---

## 4. Ownership vs storage routing

| Dato (E3) | Ownership resuelto | Routing E5 | Veredicto |
|-----------|-------------------|------------|-----------|
| Product Permission | CP central | control_plane | ✅ |
| Role-Permission Grant | DP tenant | tenant_data | ✅ |
| User Session IAM | Transversal | **RD-11 abierta** | ❌ **C-02** |
| Auth Config tenant | DP | tenant_data | ⚠️ Login path no detallado en E5 |
| Catálogos geo (`cat_pais`) | CP Product Reference | ⚠️ GLOBAL_TABLES skip filter | ❌ **C-03** |
| auth_audit_log | Dual AS-IS | Híbrido no cerrado | ❌ **C-04** |

**C-03:** E3 clasifica catálogos como Product Reference (CP). E5 `GLOBAL_TABLES` permite acceso tenant_data sin filter. En dedicated sin réplica local, queries ERP a catálogos **fallarán** unless enrutadas a CP — no diseñado explícitamente.

**C-04:** AS-IS enruta `auth_audit_log` distinto por mode en services L5. E4 RD-07 exige operation_class; E5 §8 tablas híbridas dice "encapsular en gateway" pero **no define** regla final. Decisión huérfana.

---

## 5. Runtime vs infraestructura

| Tema | E4 | E5 | Veredicto |
|------|----|----|-----------|
| Resolución per-op | RD-01 | TD-01, TD-05 | ✅ Resuelto explícitamente |
| Once-per-request (wording E2) | RR-80 gap | L-A cache | ⚠️ Tensión semántica; funcionalmente mitigada |
| Context teardown | RI-02 | No SQL session scope | ✅ |
| Migración bloquea ERP | RD-13 | TB + F7 | ✅ |
| Saga onboarding | RD-12 | TD-12 semi-auto | ⚠️ Contrato pasos Q-030 no especificado |

---

## 6. Gateway, cache, engines

| Tema | Documentos | Veredicto |
|------|------------|-----------|
| Gateway como evolución AS-IS | E5 TD-11 vs E2 "no Connection Resolver class" | ✅ Consistente |
| Tres niveles cache L-A/L-B/L-C | 02, 10 | ✅ |
| Multi-worker eventual consistency | TD-09 | ⚠️ Tensión con RR-21 crítico en migración |
| Engine key shared | TD-03 MVP=AS-IS | ⚠️ Tensión con escalabilidad 500+ tenants |
| Shutdown async engines | E5 04 | ⚠️ Gap AS-IS; E5 lo exige Fase 1 |

---

## 7. Sessions (SQL vs IAM)

| Concepto | E4 | E5 | Veredicto |
|----------|----|----|-----------|
| AsyncSession per-op | Implícito E0 | 05 explícito | ✅ |
| IAM session store | RD-11 abierta | TD-13 gate | ❌ **C-02** bloqueante dedicated IAM |
| Redis bridge post-commit | E0 AS-IS | TB-04 | ✅ |

---

## 8. Provisioning y onboarding

| Tema | E1 ADR-004 | E3 Q-032 | E5 | Veredicto |
|------|------------|----------|----|-----------|
| Saga vs single TX | Recomienda saga | Seed DP | TD-12 | ✅ Target coherente |
| Metadata en onboarding | Q-031 P0 | — | Fase 4 | ❌ **C-05:** Q-031 sigue abierta; E3 no la cerró |
| Response POST /clientes/ unchanged | E2 protected | — | Fase 4 gate | ✅ |
| Idempotency keys | Q-030 | — | 07 TB parcial | ⚠️ Insuficiente detalle |

**C-05:** E0 R-C03 confirma que onboarding no crea `cliente_conexion`. E5 Fase 4 lo aborda pero **ningún documento cierra Q-031** con contrato de pasos.

---

## 9. Repositories vs query layer

| Tema | E0 | E5 09 | Veredicto |
|------|----|----|-----------|
| Dualidad queries/repositories | Hallazgo dualidad | Convivencia MVP | ⚠️ Policy nueva; no audit completo |
| ERP solo queries | E2 0% ERP change | QL-04 | ✅ |
| Repository bypass auditor | — | RP-G02 | ❌ **C-06:** Riesgo no mitigado en diseño |

---

## 10. ADR Etapa 1 vs decisiones posteriores

| ADR | Estado E1 | Resolución E3/E4/E5 | Veredicto |
|-----|-----------|---------------------|-----------|
| ADR-001 CP/DP split | Pendiente | E3 resuelve ownership | ⚠️ ADR nunca marcado **aprobado** |
| ADR-002 Session location | Pendiente | RD-11 abierta | ❌ **C-07** |
| ADR-003 RBAC catalog | Pendiente | E3 Q-020 resuelto ownership | ⚠️ ADR pendiente formalización |
| ADR-004 Saga | Pendiente | RD-12 + TD-12 | ⚠️ Parcial |
| ADR-005 database_type L5 | — | Fase 3 | ⚠️ |

**C-07:** E1 `05_OPEN_QUESTIONS.md` §15 dice: *"No avanzar a etapa técnica sin cerrar al menos todas las P0"*. Etapas 4–5 avanzaron con Q-010, Q-030, Q-031 abiertas. **Inconsistencia de proceso** entre E1 criterios y ejecución real.

---

## 11. Matriz de contradicciones

| ID | Severidad | Descripción | Documentos |
|----|-----------|-------------|------------|
| C-01 | Alta | L5 database_type vs RI-32 | E0, E4, E5 |
| C-02 | Crítica | Session store sin decisión | E1 ADR-002, E4 RD-11, E5 TD-13 |
| C-03 | Alta | Catálogos CP vs GLOBAL_TABLES dedicated | E3, E5 08 |
| C-04 | Media | auth_audit_log routing híbrido | E0, E5 03 |
| C-05 | Alta | Q-031 metadata onboarding abierta | E0, E1, E3 |
| C-06 | Media | Repository auditor bypass | E5 09 |
| C-07 | Proceso | P0 gate E1 vs ejecución E4/E5 | E1 05 |

---

## 12. Elementos consistentes (fortalezas)

1. **Infrastructure Encapsulation** coherente E1→E2→E5.
2. **Single codebase / no fork** reforzado en guardrails y decisiones.
3. **execute_* API estable** alineada E2 protected + E5 08.
4. **Impersonation tenant operativo** consistente E0→E4→deps pattern.
5. **Migración offline MVP** alineada E1 ADR-008, E4 RD-13, E5 F7.
6. **62 invariantes runtime** cubren mayoría escenarios adversariales.

---

## 13. Conclusión

El diseño es **mayormente coherente en el target state**, pero presenta **7 contradicciones/tensiones documentadas**, siendo **C-02 (session store)** y **C-03 (catálogos dedicated)** las más impactantes para dedicated production.

**Veredicto consistencia:** ⚠️ **Aceptable con condiciones** — no bloquea Fase 0–1 infra shared; **bloquea** dedicated end-to-end sin cerrar C-02, C-03, C-05.
