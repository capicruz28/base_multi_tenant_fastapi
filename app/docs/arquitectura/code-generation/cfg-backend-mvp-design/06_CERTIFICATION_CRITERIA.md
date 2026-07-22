# Criterios de certificación — MVP Backend `cfg`

**Paquete:** `cfg-backend-mvp-design`  
**Fecha:** 2026-07-17  
**Gate:** Certificación Backend MVP Administrador del Motor

---

## 1. Propósito

Definir el checklist objetivo para declarar el MVP Backend del módulo `cfg` **certificado** y apto para iniciar el paquete de contrato Frontend (fase siguiente).

---

## 2. Checklist funcional (CU)

| CU | Criterio API | Estado cert. |
|----|--------------|--------------|
| CU-01 | GET list tenant-scoped + filtros | ☐ |
| CU-02 | GET detail enriquecido Catalog | ☐ |
| CU-03 | PATCH campos B con validación | ☐ |
| CU-04 | POST activar | ☐ |
| CU-05 | POST desactivar (no org_empresa) | ☐ |
| CU-06 | POST preview sin consumo | ☐ |
| CU-07 | org_empresa PATCH/desactivar → 422 locked | ☐ |
| CU-08 | Campos A/C/D no editables | ☐ |

---

## 3. Checklist arquitectónico

| Criterio | Evidencia | ☐ |
|----------|-----------|---|
| Módulo en `app/modules/cfg/` (ERP V4) | Estructura carpetas | ☐ |
| Sin `domain/` ni infra por módulo | Review | ☐ |
| `cfg_deps` impersonación-safe | Test U-D01 | ☐ |
| `require_cfg_tenant_erp_session` en router | Código | ☐ |
| Queries en `queries/cfg/` dual-path session | Código | ☐ |
| Mutaciones vía `get_connection_for_tenant` | Test U-M05 | ☐ |
| Preview solo Gateway.preview | Test U-P05 | ☐ |
| Catalog solo read enrich | Review | ☐ |
| Motor / ORG / INV no modificados | `git diff` scope | ☐ |
| No Path ADMIN write | Review ADJ-03 | ☐ |

---

## 4. Checklist seguridad

| Criterio | ☐ |
|----------|---|
| Permisos `cfg.secuencias.consultar` / `actualizar` sembrados | ☐ |
| Endpoints con `require_permission` correcto | ☐ |
| Cross-tenant → 404 | ☐ |
| Sin `cliente_id` autorizando desde body/query | ☐ |
| Soft-disable only (no DELETE) | ☐ |

---

## 5. Checklist OpenAPI / contrato

| Criterio | ☐ |
|----------|---|
| 6 operationIds MVP presentes | ☐ |
| Schemas Read/Update/Preview/Paginated | ☐ |
| Union listado con/sin `page` | ☐ |
| Errores documentados (`ORG_EMPRESA_CFG_LOCKED`, …) | ☐ |
| Sin endpoints align/diagnóstico en MVP | ☐ |

---

## 6. Checklist pruebas

| Criterio | ☐ |
|----------|---|
| Plan `05_TEST_PLAN.md` U-* obligatorias en verde | ☐ |
| Smoke integración mínimo | ☐ |
| CI Motor + ORG + INV sin regresiones | ☐ |

---

## 7. Checklist Shared / Dedicated

| Criterio | ☐ |
|----------|---|
| Misma semántica de servicios | ☐ |
| Escritura siempre con session UoW | ☐ |
| Test o review Dedicated path | ☐ |

---

## 8. Criterios de rechazo (no certificar)

- Cualquier escritura a `ultimo_numero` desde admin  
- Preview que llame `allocate` / `increment_and_get`  
- Endpoints montados bajo `/clientes` o `/superadmin`  
- Dependencia de services ORG/INV  
- `extra` permitiendo policy/scope en PATCH  
- Ausencia de seed RBAC en entorno de certificación  

---

## 9. Dictamen de certificación (plantilla)

```text
MVP Backend módulo cfg — CERTIFICADO | NO CERTIFICADO

Fecha:
Evidencia tests:
Evidencia OpenAPI:
Alcance git (archivos):
Firmas / aprobación:
```

Tras **CERTIFICADO** → autorizar paquete `cfg-frontend-contract` (docs) según roadmap funcional.

---

## 10. Cierre del Blueprint Técnico

> El **Blueprint Técnico del MVP Backend** (`cfg-backend-mvp-design/`) se declara **completo y listo para iniciar la implementación** cuando el usuario lo autorice explícitamente.  
> Hasta esa autorización: **no modificar código, no crear endpoints, no actualizar OpenAPI**.

### Lectura obligatoria para implementadores

1. `00_EXECUTIVE_SUMMARY.md`  
2. `01_MODULE_ARCHITECTURE.md`  
3. `02_OPENAPI_DESIGN.md`  
4. `03_DATA_FLOW.md`  
5. `04_IMPLEMENTATION_PLAN.md` (orden de pasos)  
6. `05_TEST_PLAN.md`  
7. `06_CERTIFICATION_CRITERIA.md` (este documento)  

Referencias de producto/arquitectura: `cfg-functional-design/`, `cfg-platform-architecture/`, `cfg-admin-audit/`.
