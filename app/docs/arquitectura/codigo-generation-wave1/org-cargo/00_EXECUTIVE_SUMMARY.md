# Ola 1.2 — org_cargo: Resumen ejecutivo

**Proyecto:** Primer consumidor real del Motor de Generación de Códigos  
**Entidad:** ORG Cargo (`org_cargo`)  
**Fecha:** 2026-07-11  
**Estado:** Auditoría — sin implementación  
**Motor:** `app/core/codigo` **congelado**

---

## Veredicto

### org_cargo está **LISTO PARA IMPLEMENTACIÓN**

No existe bloqueo arquitectónico. La integración es viable con el motor en estado actual (P0 + P1A + P2 + MANUAL_ONLY).

### Prerequisitos técnicos identificados (no bloqueantes del diseño)

| # | Prerequisito | Tipo | Notas |
|---|--------------|------|-------|
| P1 | **UoW + dual-path session** en `cargo_queries.py` | Implementación ORG | Obligatorio — `allocate` consume contador; INSERT debe ser atómico |
| P2 | Fila cfg `org_cargo` scope EMPRESA | Bootstrap existente | Sembrada por EBS V1 / onboarding — verificar en entorno |
| P3 | Llamada a `OrgCodigoGenerationService.resolve_codigo_for_create` | Implementación ORG | Sin modificar el helper (congelado) |

### Fuera de alcance Ola 1.2 cargo

- Modificar `app/core/codigo/**`
- Modificar Bootstrap / OrgCodigoGenerationService
- Otras entidades ORG (departamento, sucursal, …)
- Preview endpoint UX
- Endurecimiento UPDATE (código solo lectura)

---

## Respuestas rápidas (17 preguntas)

| # | Respuesta corta |
|---|-----------------|
| 1 | `POST /api/v1/org/cargos` |
| 2 | Endpoint → `create_cargo_servicio` → pre-check → `create_cargo` → INSERT |
| 3 | `CargoCreate` / `CargoRead` — `codigo` required hoy |
| 4 | Schema `CargoCreate.codigo` + formulario frontend |
| 5 | Pydantic `normalize_upper` + service pre-check + SQL UNIQUE |
| 6 | `get_cargo_by_codigo` en service (409 ConflictError) |
| 7 | `insert(OrgCargoTable).values(**payload)` vía `execute_insert` |
| 8 | **No** — solo path auto-commit legacy |
| 9 | **Sí** — patrón `create_empresa_servicio` obligatorio |
| 10 | `CargoCreate.codigo` → optional |
| 11 | Eliminar input obligatorio en alta; mostrar código post-guardado |
| 12 | Sin tests dedicados create cargo; infra motor parcial |
| 13 | UoW queries + service allocate + optional/manual/409 |
| 14 | Drift contador, TX parcial, cfg ausente |
| 15 | Strangler: schema optional → UoW → allocate → INSERT |
| 16 | Checklist en `03_IMPLEMENTATION_PLAN.md` |
| 17 | Gates en `03_IMPLEMENTATION_PLAN.md` |

---

## Documentos del paquete

| # | Archivo |
|---|---------|
| 00 | Este resumen |
| 01 | `01_FUNCTIONAL_AUDIT.md` — flujo, schemas, queries |
| 02 | `02_TESTS_AND_RISKS.md` — pruebas y regresión |
| 03 | `03_IMPLEMENTATION_PLAN.md` — Strangler, checklist, gates |

---

## Decisión de go/no-go

| Criterio | Estado |
|----------|--------|
| Motor funcional completo | ✅ |
| sequence_key `org_cargo` en catálogo | ✅ AUTO_DEFAULT / EMPRESA / CAR |
| Infra ORG Ola 1.1 | ✅ `OrgCodigoGenerationService` |
| cfg seed EMPRESA | ✅ vía bootstrap existente |
| UoW cargo queries | ❌ Pendiente implementación |
| Tests cargo create | ❌ Pendiente implementación |

**Go condicional:** iniciar implementación Ola 1.2 cargo tras aprobar este paquete. Primera tarea de código: dual-path + UoW en queries, luego service + schema.
