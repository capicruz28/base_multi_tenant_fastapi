# Checklist final — DoD MVP Backend `cfg` v1.0

**Paquete:** `cfg-implementation-spec`  
**Versión:** 1.0

---

## 1. Cumplimiento de especificación

- [x] Única guía usada: `cfg-implementation-spec/` v1.0  
- [x] G-01…G-06 aplicados (DELETE/reactivar; sin colisión; numero_inicial ≥1; list G-04; preview inactiva 200; solo queries/cfg)  
- [x] Motor / ORG / INV / Repo sin cambios de este MVP  

---

## 2. Funcional (API)

- [x] GET list + filtros + page in-memory  
- [x] GET detail + enrich + `config_locked` / `policy_drift`  
- [x] PATCH campos B  
- [x] DELETE soft + POST reactivar  
- [x] POST preview sin consumo  
- [x] Lock `org_empresa` en PATCH y DELETE  
- [x] RBAC consultar / actualizar  

---

## 3. Arquitectura

- [x] `app/modules/cfg/` V4  
- [x] `cfg_deps` impersonación-safe  
- [x] `require_cfg_tenant_erp_session`  
- [x] `queries/cfg/` canónicas  
- [x] Mutaciones con `get_connection_for_tenant` + `session.begin()`  
- [x] Preview solo `Gateway.preview`  
- [x] Catalog solo enrich  

---

## 4. OpenAPI

- [x] 6 operationIds de `02_API_SPEC`  
- [x] Schemas Read / Update / Preview / Paginated  
- [x] Sin activar/desactivar legacy  
- [x] Sin align/diagnóstico en MVP  

---

## 5. Pruebas

- [x] `05_TESTING_GUIDE` unitarias obligatorias  
- [x] Smoke integración mínimo  
- [x] Sin regresiones Motor/ORG/INV  

---

## 6. Shared / Dedicated

- [x] Misma semántica de servicios  
- [x] Sin Path ADMIN en admin HTTP  

---

## 7. Criterios de rechazo

No certificar si existe cualquiera de:

- POST activar/desactivar en lugar de DELETE/reactivar  
- Validación `CFG_FORMAT_COLLISION`  
- Preview que llama allocate o muta contador  
- Extensión Repo en el path HTTP  
- Escritura sin session tenant  
- Modificaciones a Motor/ORG/INV  

**Evaluación Etapa 8:** ninguno de los criterios de rechazo aplica.

---

## 8. Dictamen de certificación

```text
MVP Backend cfg v1.0 — CERTIFICADO
Fecha: 2026-07-17
Evidencia tests: 31/31 cfg + 182/182 Motor/ORG/INV related — PASS
Evidencia OpenAPI: 6 operationIds; DELETE + /reactivar; sin /activar/align/diagnóstico
Alcance Etapa 8: tests de certificación + informe (sin defectos de producción)
Aprobación: Etapa 8 según 05_TESTING_GUIDE + este checklist
```

Informe detallado: `07_CERTIFICATION_REPORT.md`.

Tras **CERTIFICADO** → fase contrato Frontend (fuera de esta spec).

---

## 9. Cierre oficial v1.0

> Esta es la **especificación consolidada oficial v1.0** del MVP Backend del módulo `cfg`.  
> Toda implementación debe seguir **exclusivamente** este paquete.  
> Paquetes previos quedan como archivo histórico, no como guía de implementación.

> **Cierre de implementación Backend MVP `cfg` (2026-07-17):** CERTIFICADO.  
> Etapas 1–8 completadas. No se autorizan más cambios de producto Backend en este MVP salvo defectos críticos post-certificación.
