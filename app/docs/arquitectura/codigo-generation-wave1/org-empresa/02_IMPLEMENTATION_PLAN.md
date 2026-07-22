# Plan de integración — `org_empresa` (Ola 1 ORG — fase final)

**Tipo:** Plan técnico — sin implementación en este documento  
**Fecha:** 2026-07-12  
**Prerequisito:** Arquitectura bootstrap **cerrada** (`BR-BOOT-04`, `BR-M-02`)  
**Patrón referencia:** cargo / departamento / centro_costo / sucursal (Ola 1.2–1.5)

---

## 1. Alcance de implementación

### Incluido

| # | Tarea |
|---|-------|
| 1 | **Bootstrap seed:** `org_empresa` TENANT con `ultimo_numero=1` en onboarding (`onboarding_seed` / `cfg_codigo_onboarding_seed`) |
| 2 | Integrar `OrgCodigoGenerationService.resolve_codigo_for_create("org_empresa", ...)` en `create_empresa_servicio` |
| 3 | `_normalize_manual_codigo` + `_SEQUENCE_KEY = "org_empresa"` |
| 4 | `EmpresaCreate.codigo_empresa` → `Optional[str]` |
| 5 | Pre-check duplicate `codigo_empresa` **solo si manual** |
| 6 | Mapeo `payload["codigo_empresa"] = codigo_resuelto` antes de `create_empresa` |
| 7 | Tests motor + ampliación bootstrap/uow (assert `ultimo_numero=1` post-onboarding) |
| 8 | Verificar `git diff app/core/codigo` vacío |

### Excluido

| Item | Motivo |
|------|--------|
| `app/core/codigo/**` | Motor congelado |
| `OrgCodigoGenerationService`, Gateway, SequenceCatalog | Congelado |
| `MinimalErpTenantBootstrapService.ensure_empresa_inicial` | Sigue insertando EMP001 — sin cambio |
| Guard / `align_counter` en `create_empresa_servicio` | **Prohibido** (greenfield; BR-BOOT-04) |
| Scripts ENSURE / repair | **No aplica** greenfield |
| `empresa_queries.py` | Dual-path ya completo |
| Endpoints, RBAC, `EmpresaRead` | Sin cambio |

---

## 2. Diff mínimo esperado en `create_empresa_servicio`

### AS-IS (L109–130)

```
session.begin()
  → get_empresa_by_codigo(data.codigo_empresa)     # siempre
  → get_empresa_by_ruc(data.ruc)
  → create_empresa(payload con codigo del body)
  → insertar_secuencias_codigo
```

### TO-BE

```
session.begin()
  → manual = normalize(data.codigo_empresa)
  → if manual: get_empresa_by_codigo(manual)       # solo manual
  → get_empresa_by_ruc(data.ruc)                   # siempre
  → codigo = resolve_codigo_for_create("org_empresa", empresa_id=None, manual_code=manual)
  → payload["codigo_empresa"] = codigo
  → create_empresa(payload, session=session)
  → insertar_secuencias_codigo(session, client_id, row["empresa_id"])
```

**Sin** paso de alineación ni repair.

---

## 3. Bootstrap seed (prerequisito de gate EMP002)

### Normativa (BR-BOOT-04)

Tras `ensure_empresa_inicial` (EMP001), el seed cfg TENANT debe insertar:

| Campo | Valor |
|-------|-------|
| `sequence_key` | `org_empresa` |
| `scope_type` | TENANT |
| `ultimo_numero` | **`1`** |
| `numero_inicial` | `1` |

### Implementación sugerida

En `OnboardingSequenceSeed.from_definition` (o equivalente en `_seed_cfg_rows`):

```python
ultimo_numero = 1 if defn.sequence_key == "org_empresa" else 0
```

### Verificación

| Test | Assert |
|------|--------|
| Post-onboarding | cfg TENANT `org_empresa.ultimo_numero == 1` |
| Primer create ORG auto | `codigo_empresa == "EMP002"` |

---

## 4. Tests

### Nuevo: `test_org_empresa_motor_integration.py`

Patrón idéntico a cargo/sucursal/CC/dpto:

- create sin código → EMP002 (con bootstrap seed correcto)
- create manual válido → aceptado
- duplicado → 409
- rollback TX

### Ampliar: `test_org_empresa_bootstrap_v1.py`

- Assert post-onboarding: `ultimo_numero=1` para cfg TENANT `org_empresa`

### Mantener: `test_org_empresa_uow.py`

---

## 5. Checklist gate

- [ ] Bootstrap seed `ultimo_numero=1` implementado
- [ ] Motor integrado en `create_empresa_servicio`
- [ ] `EmpresaCreate.codigo_empresa` Optional
- [ ] Gate EMP002 auto sin colisión EMP001
- [ ] `test_org_empresa_bootstrap_v1` + motor integration verdes
- [ ] `git diff app/core/codigo` vacío

---

## 6. Cierre Ola 1 ORG

| Entidad | sequence_key | Estado |
|---------|--------------|--------|
| org_cargo | org_cargo | ✅ |
| org_departamento | org_departamento | ✅ |
| org_centro_costo | org_centro_costo | ✅ |
| org_sucursal | org_sucursal | ✅ |
| org_empresa | org_empresa | ⏳ esta fase |

**Ola 1 ORG = COMPLETA** cuando org_empresa cumple gate.

---

## 7. Riesgos residuales

| ID | Riesgo | Mitigación |
|----|--------|------------|
| R-E01 | Seed sigue en `ultimo_numero=0` | Tests bootstrap obligatorios |
| R-E02 | Prefijo/pad cfg ≠ EMP001 bootstrap | Mantener defaults catálogo bloqueados para org_empresa |
