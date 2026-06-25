# 06 — Implementation Readiness Score

**Etapa:** 6.0 — Repository Readiness  
**Fecha:** 2026-06-25  
**Metodología:** Ponderación por dimensión × fase

---

## 1. Criterios de scoring

Cada dimensión se califica 0–100:

| Rango | Significado |
|-------|-------------|
| 90–100 | Listo — sin bloqueos |
| 75–89 | Listo con condiciones menores |
| 60–74 | Riesgos mitigables en fase |
| 40–59 | Replan parcial requerido |
| 0–39 | No listo |

---

## 2. Dimensiones evaluadas

| ID | Dimensión | Peso global |
|----|-----------|-------------|
| D-01 | Whitelist BL files exist | 10% |
| D-02 | Gateway infra stability (execute_*, UoW) | 15% |
| D-03 | SQL routing compliance (G-09) | 10% |
| D-04 | database_type debt scope (G-10) | 10% |
| D-05 | IP doc consistency | 5% |
| D-06 | Test harness readiness | 15% |
| D-07 | CI/CD gates readiness | 10% |
| D-08 | ERP isolation (no drift) | 10% |
| D-09 | OpenAPI baseline | 5% |
| D-10 | BL/IP/Repo alignment | 10% |

---

## 3. Scores por dimensión

| Dimensión | Score | Justificación |
|-----------|-------|---------------|
| D-01 Whitelist files | **100** | 9/9 exist |
| D-02 Gateway stability | **95** | execute_* + UoW intact; shutdown gap minor |
| D-03 SQL routing | **85** | 2 SLS bypass; rest compliant |
| D-04 database_type | **55** | 15 L5 files vs 3 planned F3 |
| D-05 IP consistency | **70** | 18/20/22 count drift |
| D-06 Test harness | **75** | Tests absent but F0 creates; fixtures IAM reusable |
| D-07 CI gates | **60** | All gates to build F0–F3 |
| D-08 ERP isolation | **95** | 32 modules unchanged; no hybrid drift |
| D-09 OpenAPI | **90** | Snapshot exists; diff gate pending |
| D-10 Alignment | **80** | F3 scope gap only material issue |

---

## 4. Score global ponderado

```
Global = Σ (score × weight)

= 100×0.10 + 95×0.15 + 85×0.10 + 55×0.10 + 70×0.05
  + 75×0.15 + 60×0.10 + 95×0.10 + 90×0.05 + 80×0.10

= 10 + 14.25 + 8.5 + 5.5 + 3.5 + 11.25 + 6 + 9.5 + 4.5 + 8

= 81.0 → redondeado 81/100
```

**Ajuste conservador F0–F3 full path:** penalización F3 → **72/100** (ver §5)

---

## 5. Scores por fase

| Fase | Score | Nivel | Bloqueos |
|------|-------|-------|----------|
| **F0** | **88/100** | Listo | Ninguno |
| **F1** | **82/100** | Listo c/ condiciones | RR-H01, RR-M01 |
| **F2** | **75/100** | Listo c/ condiciones | CI gates |
| **F3** | **58/100** | Replan scope | RR-H02 |
| **Global F0–F3** | **72/100** | Ejecutable secuencial | F3 scope ampliar |

### Desglose F0 (88/100)

| Factor | Puntos |
|--------|--------|
| Infra estable para mock | +40 |
| Zero prod change F0 | +25 |
| Tests ausentes (expected) | −10 |
| CI job pending | −7 |
| IAM parallel work risk | −5 |
| IP doc minor drift | −5 |

### Desglose F3 (58/100)

| Factor | Puntos |
|--------|--------|
| 3 archivos IP planificados OK | +30 |
| 12+ archivos L5 extra | −25 |
| grep gate will fail partial | −10 |
| rol_service complexity | −7 |

---

## 6. Umbral Go/No-Go

| Umbral | Valor | F0 actual |
|--------|-------|-----------|
| Mínimo GO F0 | ≥ 75 | **88 ✅** |
| Mínimo GO F1 | ≥ 70 | **82 ✅** |
| Mínimo GO F3 | ≥ 65 | **58 ❌** (pre-F3 replan) |

---

## 7. Evolución esperada post-fases

| Post-fase | Score proyectado |
|-----------|------------------|
| Post G-F0 | 78 global |
| Post G-F1 | 84 global |
| Post G-F2 | 86 global |
| Post G-F3 (scope ampliado) | 92 global |

---

## 8. Conclusión

| Veredicto | Score |
|-----------|-------|
| **F0 Ready** | **88/100 — GO** |
| **Full F0–F3 Ready (today)** | **72/100 — GO WITH CONDITIONS** |

El score **no bloquea F0**. F3 requiere ampliación scope antes de G-F2 checkpoint para alcanzar umbral 65+.
