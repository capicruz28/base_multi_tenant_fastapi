# Ola 1.2 — org_cargo: Plan de implementación

**Estado:** Diseño — sin implementación  
**Fecha:** 2026-07-11

---

## 15. Estrategia Strangler recomendada

### Principio

Migrar **solo create path** de cargo al motor, preservando rutas, RBAC, Read schema y compatibilidad manual (AUTO_DEFAULT).

### Fases incrementales

```
S0 — Queries dual-path (sin motor)
  └─ create_cargo / get_cargo_by_* aceptan session
  └─ Tests UoW queries (paridad empresa)

S1 — Service UoW shell
  └─ session.begin() sin motor — comportamiento idéntico AS-IS
  └─ Gate: tests regresión manual codigo required

S2 — Integración motor
  └─ CargoCreate.codigo optional
  └─ resolve_codigo_for_create antes INSERT
  └─ Pre-check duplicado solo si manual explícito

S3 — Validación E2E + OpenAPI
  └─ Swagger refleja optional
  └─ Coordinación frontend
```

### Qué NO hacer en Strangler cargo

| Anti-patrón | Razón |
|-------------|-------|
| Llamar `CodigoGeneracionGateway` desde service directo | Usar `OrgCodigoGenerationService` |
| Llamar `CfgSequenceStore` desde ORG | Violación capas |
| allocate fuera de UoW | Drift contador |
| Cambiar Read / rutas / permisos | Fuera alcance |
| Modificar motor | Congelado |

---

## 16. Checklist de implementación

### Fase S0 — Queries dual-path

- [ ] `get_cargo_by_codigo(..., session: Optional[AsyncSession] = None)`
- [ ] `get_cargo_by_id(..., session: Optional[AsyncSession] = None)`
- [ ] `create_cargo(..., session: Optional[AsyncSession] = None)`
- [ ] Path con session: `session.execute` + fetch sin commit
- [ ] Path sin session: legacy `execute_*` (sin regresión)
- [ ] Tests `test_org_cargo_uow.py`

### Fase S1 — Service UoW (sin motor)

- [ ] Import `get_connection_for_tenant`, `OPERATION_CLASS_TENANT_DATA`
- [ ] `create_cargo_servicio`: `async with session.begin()`
- [ ] Propagar session a queries create + get
- [ ] Comportamiento observable **idéntico** (codigo required)
- [ ] Tests regresión create con codigo manual

### Fase S2 — Motor integration

- [ ] `CargoCreate.codigo: Optional[str] = None`
- [ ] Invocar `OrgCodigoGenerationService.resolve_codigo_for_create("org_cargo", ...)`
- [ ] Asignar `payload["codigo"]` con resultado motor
- [ ] Pre-check `get_cargo_by_codigo` **solo si** manual explícito en body
- [ ] Catch UNIQUE SQL → ConflictError 409 (recomendado)
- [ ] Tests create sin codigo / manual / duplicado / cfg missing

### Fase S3 — Cierre

- [ ] OpenAPI generado coherente (optional codigo)
- [ ] Suite motor 105+ tests verde
- [ ] Suite ORG cargo nueva verde
- [ ] Documentar en changelog interno Ola 1.2
- [ ] Handoff frontend (eliminar input código alta)

---

## 17. Gates de aceptación

### Gate G-CARGO-01 — Queries UoW

| Criterio | Verificación |
|----------|--------------|
| Dual-path session | Tests query with/without session |
| Sin regresión legacy | Tests sin session pasan |

### Gate G-CARGO-02 — Paridad pre-motor

| Criterio | Verificación |
|----------|--------------|
| Create con codigo manual | 201, mismo comportamiento AS-IS |
| Duplicado | 409 |
| UoW | `session.begin()` una vez por request |

### Gate G-CARGO-03 — Motor integrado

| Criterio | Verificación |
|----------|--------------|
| Create **sin** codigo | 201, formato `CAR` + dígitos |
| Contador incrementado | cfg `ultimo_numero` +1 en misma TX |
| Rollback | INSERT falla → contador no persistido (test mock) |
| Manual válido | 201, codigo = body |
| cfg ausente | 404 `CFG_SEQUENCE_NOT_FOUND` |

### Gate G-CARGO-04 — No regresión

| Criterio | Verificación |
|----------|--------------|
| GET list / detail | Sin cambio |
| PUT / DELETE / reactivar | Sin cambio |
| Motor suite | 105+ passed |
| `app/core/codigo` | Cero diffs |

### Gate G-CARGO-05 — Listo para frontend

| Criterio | Verificación |
|----------|--------------|
| OpenAPI `codigo` optional en Create | Swagger UI |
| CargoRead.codigo siempre presente | POST response |

---

## Orden de archivos a tocar (implementación)

| Orden | Archivo | Tipo cambio |
|-------|---------|-------------|
| 1 | `cargo_queries.py` | Dual-path session |
| 2 | `tests/unit/test_org_cargo_uow.py` | Nuevo |
| 3 | `cargo_service.py` | UoW + motor |
| 4 | `schemas.py` | CargoCreate optional |
| 5 | `tests/unit/test_org_cargo_motor_integration.py` | Nuevo |
| 6 | — | OpenAPI auto-regenerado al arrancar |

**No tocar:** `endpoints_cargos.py` (firma estable), `OrgCodigoGenerationService`, motor, bootstrap.

---

## Veredicto final

**org_cargo está arquitectónicamente listo.** El único trabajo estructural previo a allocate es **UoW dual-path en queries** — mismo patrón ya validado en `empresa_queries` / `test_org_empresa_uow.py`.

No hay bloqueo en motor, catálogo, cfg seed ni infra ORG Ola 1.1.
