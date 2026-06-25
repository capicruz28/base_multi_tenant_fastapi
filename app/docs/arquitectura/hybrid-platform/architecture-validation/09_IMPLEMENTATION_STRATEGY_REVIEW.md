# 09 — Implementation Strategy Review

**Etapa:** 5.5 — Architecture Validation  
**Fecha:** 2026-06-25  
**Alcance:** E5 `12_IMPLEMENTATION_ROADMAP.md` Fases 0–8

---

## 1. Propósito

Validar orden, dependencias y completitud del roadmap. Detectar dependencias ocultas y proponer ajustes **estratégicos** (no implementación).

---

## 2. Evaluación por fase

### Fase 0 — Test harness

| Aspecto | Evaluación |
|---------|------------|
| Posición | ✅ **Correcta** — first |
| Dependencias | Ninguna |
| Gap | Debe incluir **tenant isolation** + **wrong route** tests |
| Riesgo omitir | Alto — F1 sin red |

**Veredicto:** ✅ Mantener; **ampliar** scope tests adversariales AR-C02, AR-C04.

---

### Fase 1 — Gateway consolidation

| Aspecto | Evaluación |
|---------|------------|
| Posición | ✅ Correcta post-F0 |
| Dependencias | F0 |
| Gap | No incluye **catálogos CP routing** (AR-H01) |
| Riesgo | Medio-Alto — single point |

**Veredicto:** ✅ Mantener; **añadir** spike catálogos como F1.5 o blocker F4.

---

### Fase 2 — Shared regression

| Aspecto | Evaluación |
|---------|------------|
| Posición | ✅ Post-F1 |
| Dependencias | F1 |
| Gap | Performance baseline útil pero no gate dedicated |

**Veredicto:** ✅ Correcta.

---

### Fase 3 — L5 database_type cleanup

| Aspecto | Evaluación |
|---------|------------|
| Posición actual | Paralelo F4 start |
| **Problema detectado** | F3 **debería completarse antes** primer test dedicated real |
| Dependencia oculta | AR-H06 — IAM branches wrong until F3 |
| Conflicto | F4 onboarding puede depender de IAM paths |

**Veredicto:** ⚠️ **Reordenar: F3 inmediatamente después F2, antes F4.**

---

### Fase 4 — Provisioning saga

| Aspecto | Evaluación |
|---------|------------|
| Posición | Post F1 |
| Dependencias ocultas | Q-030, Q-031, catálogos, DDL Q-061 |
| Gap | No incluye **catalog seed/replica** decision |
| Riesgo | Alto — dedicated onboarding |

**Veredicto:** ⚠️ **No iniciar F4** sin cerrar §dependencias. Añadir **F3.5 Catalog policy** explícita.

---

### Fase 5 — Session store (RD-11)

| Aspecto | Evaluación |
|---------|------------|
| Posición | Post F4 |
| **Problema detectado** | Decisión ADR-002 debería **adelantarse** — no requiere F4 completa |
| Dependencia | IAM V2 tests |

**Veredicto:** ⚠️ **Paralelizar F5 decisión con F1** (decide early, implement after F4). TD-13 gate correcto para **implementación**, no para **decisión**.

---

### Fase 6 — Dedicated production

| Aspecto | Evaluación |
|---------|------------|
| Posición | Post F5 |
| Gap | No incluye **ops runbooks** (08 ops 42%) |
| Dependencia oculta | Staging soak 72h — good |

**Veredicto:** ✅ Secuencia OK si F5 closed; **añadir** ops deliverables gate F6.

---

### Fase 7 — Migration

| Aspecto | Evaluación |
|---------|------------|
| Posición | Post F6 |
| Evaluación | ✅ Correcto post-MVP |

---

### Fase 8 — Optimizations

| Aspecto | Evaluación |
|---------|------------|
| Posición | Post F6 |
| Evaluación | ✅ Correcto |

---

## 3. Dependencias ocultas no en roadmap

| ID | Dependencia | Impacto |
|----|-------------|---------|
| DS-01 | `{cod}_deps` ERP modules AR-C05 | Impersonation — no phased |
| DS-02 | Repository audit | Security |
| DS-03 | ADR formal approvals | Governance |
| DS-04 | DDL ops pipeline Q-061 | F4 blocker |
| DS-05 | Catalog CP strategy | F4 blocker |
| DS-06 | Runbooks F4–F6 | F6 blocker |
| DS-07 | Permission resolution impl | RBAC dedicated |

---

## 4. Roadmap propuesto (ajustado)

```
F0  Test harness (ampliado)
F1  Gateway consolidation
F2  Shared regression
F3  L5 cleanup database_type        ← MOVED UP (antes F4)
F3.5 Catalog CP policy spike       ← NEW (decisión AR-H01)
F4  Provisioning saga              ← blocked until Q-030/031 + F3.5
F5a ADR-002 decision (parallel F1)  ← DECISION EARLY
F5b Session route implementation   ← after F4
F6  Dedicated prod (+ ops runbooks)
F7  Migration
F8  Optimizations
```

---

## 5. Comparación orden actual vs propuesto

| Tema | E5 actual | Propuesto | Razón |
|------|-----------|-----------|-------|
| F3 timing | Parallel F4 | Secuencial pre-F4 | AR-H06 |
| Catalog decision | Ausente | F3.5 | AR-H01 |
| RD-11 decision | F5 | F5a parallel F1 | Desbloquea diseño IAM |
| Ops runbooks | Implícito | Gate F6 | 08 ops score 20% |

---

## 6. ¿Es correcto el roadmap general?

| Pregunta | Respuesta |
|----------|-----------|
| Infra before provisioning | ✅ Sí |
| Shared before dedicated | ✅ Sí |
| ERP untouched | ✅ Sí |
| Migration post-MVP | ✅ Sí |
| Missing phases | ⚠️ F3.5 catalog, ops, deps ERP |
| Order tweaks needed | ⚠️ F3 earlier; RD-11 decide earlier |

**Veredicto estrategia:** **Mayormente correcta** con **3 ajustes de orden** y **2 fases/spikes faltantes**.

---

## 7. Estimación esfuerzo post-ajuste

| Cambio | Impacto esfuerzo |
|--------|------------------|
| F3 earlier | Neutral |
| F3.5 spike | +S |
| F5a parallel | Neutral |
| Ops runbooks gate F6 | +M (parallel ops team) |

---

## 8. Conclusión

El roadmap E5 es **sólido en estructura macro** (F0→F1→F2→infra→provisioning→prod). Requiere **reordenación F3**, **spike catálogos**, **decisión RD-11 temprana**, y **ops explícitos** antes F6. Sin estos ajustes, riesgo de **implementar F4 sobre deuda L5** y **onboarding dedicated roto por catálogos**.
