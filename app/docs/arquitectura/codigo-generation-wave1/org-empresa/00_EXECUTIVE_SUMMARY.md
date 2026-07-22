# Resumen ejecutivo — `org_empresa` (Ola 1 ORG)

**Tipo:** Decisión arquitectónica cerrada — listo para implementación  
**Fecha:** 2026-07-12  
**Estado:** **ARQUITECTURA CERRADA** — bootstrap normativo en Motor de Códigos (`BR-M-02`, `BR-BOOT-04`)  
**Contexto:** Cuatro entidades company-scoped migradas. `org_empresa` es la última entidad motor de Ola 1 ORG. Proyecto **greenfield** (sin legacy, sin ENSURE).

---

## 1. Veredicto

| Campo | Valor |
|-------|-------|
| **¿Bloquea la implementación?** | **No** — patrón UoW + motor definido; bootstrap normativo cerrado |
| **Complejidad relativa** | **Alta** — scope TENANT, bootstrap cfg, convivencia EMP001 |
| **Cambios en queries** | **No requeridos** — dual-path ya implementado (UoW-1) |
| **Cambios en service ORG** | **Sí** — integrar `OrgCodigoGenerationService` en `create_empresa_servicio` |
| **Cambios en bootstrap seed** | **Sí** — `org_empresa` cfg TENANT con `ultimo_numero=1` (BR-BOOT-04) |
| **Repair runtime / ENSURE / guard ORG** | **No** — prohibido greenfield |
| **Riesgo principal** | ~~Contador desalineado~~ → **Resuelto** por seed `ultimo_numero=1` |
| **Cierre Ola 1 ORG** | Tras implementar ORG + bootstrap seed + gate EMP002 |

---

## 2. Bootstrap `org_empresa` (normativa oficial)

| Paso | Comportamiento |
|------|----------------|
| Onboarding | `ensure_empresa_inicial` → INSERT `EMP001` (sin motor) |
| Seed cfg TENANT | `org_empresa` con **`ultimo_numero = 1`** |
| Runtime ORG create | `allocate` → **`EMP002`** (sin guard ni `align_counter`) |

**Referencias normativas:** `07_BUSINESS_RULES.md` (BR-M-02), `bootstrap/03_BOOTSTRAP_RULES.md` (BR-BOOT-04), `bootstrap/01_SEQUENCE_DEFAULT_CONFIGURATION.md` (BS-CFG-02 excepción), `08_CODE_POLICIES.md`.

---

## 3. Punto de integración del motor

Dentro del `session.begin()` existente en `create_empresa_servicio`, **después** de pre-checks (codigo manual + RUC) y **antes** de `create_empresa`:

```
session.begin()
  → [si manual] get_empresa_by_codigo
  → get_empresa_by_ruc
  → OrgCodigoGenerationService.resolve_codigo_for_create("org_empresa", empresa_id=None, ...)
  → payload["codigo_empresa"] = codigo resuelto
  → create_empresa(session=session)
  → EmpresaBootstrapService.insertar_secuencias_codigo(...)
→ commit / rollback
```

**Sin** paso de alineación ni repair.

---

## 4. Componentes modificables en implementación

| Artefacto | Acción |
|-----------|--------|
| `empresa_service.py` | Integrar motor |
| `schemas.py` | `EmpresaCreate.codigo_empresa` → Optional |
| `onboarding_seed.py` / `cfg_codigo_onboarding_seed.py` | `ultimo_numero=1` para `org_empresa` |
| `test_org_empresa_motor_integration.py` | **Nuevo** |
| Tests bootstrap/uow | Ampliar asserts post-onboarding `ultimo_numero=1` |

**Congelado:** `app/core/codigo/**`, Gateway, `OrgCodigoGenerationService`, `MinimalErpTenantBootstrapService.ensure_empresa_inicial` (sigue insertando EMP001).

---

## 5. Gate de cierre

- [ ] Post-onboarding: cfg TENANT `org_empresa.ultimo_numero = 1`
- [ ] Primer `create_empresa_servicio` auto → `EMP002` sin colisión
- [ ] `git diff app/core/codigo` vacío
- [ ] Tests ORG verdes

Tras cumplir gate: **Ola 1 ORG — Integración Motor de Códigos** declarada cerrada.

---

*Detalle técnico: [`01_INTEGRATION_AUDIT.md`](01_INTEGRATION_AUDIT.md)*  
*Plan implementación: [`02_IMPLEMENTATION_PLAN.md`](02_IMPLEMENTATION_PLAN.md)*  
*Auditoría histórica EMP001 (superseded): [`03_EMP001_ALIGNMENT_DECISION.md`](03_EMP001_ALIGNMENT_DECISION.md)*
