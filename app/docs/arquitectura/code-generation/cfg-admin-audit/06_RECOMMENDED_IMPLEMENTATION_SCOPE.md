# Alcance recomendado de implementación (MVP y fases)

**Paquete:** `cfg-admin-audit`  
**Fecha:** 2026-07-17  
**Estado:** **recomendación de alcance** — no es autorización para implementar.

---

## 1. Principios de alcance

1. **No modificar** Motor, Gateway, SequenceCatalog, ORG, INV.
2. Admin **orquesta**; Gateway **ejecuta** preview/align/validate.
3. Solo mutar campos **clase B**; nunca A/D vía PATCH genérico; policy clase C read-only.
4. Dedicated/Shared: siempre UoW con `session` tenant.
5. Reutilizar diseño `codigo-generation-admin/` como contrato base.

---

## 2. MVP — Administrador del Motor v1

### Incluye

| Capacidad | Detalle |
|-----------|---------|
| Módulo ERP `cfg` | Estructura V4: schemas → queries → services → routers |
| `GET /cfg/secuencias` | Listado tenant-scoped; filtros básicos (key, scope, empresa, activo); paginación ERP |
| `GET /cfg/secuencias/{id}` | Detalle + enrich Catalog (policy nominal, módulo, defaults) |
| `PATCH /cfg/secuencias/{id}` | Solo B: prefijo, separador, longitud_numero, numero_inicial (si se extiende repo), es_activo |
| `POST .../preview` | Delegado a `Gateway.preview` |
| RBAC | `cfg.secuencias.consultar` + `cfg.secuencias.actualizar` |
| Session | `cfg_deps` impersonación-safe |
| Tests | Tenant isolation, immutable reject, preview sin side-effect, Dedicated session path |
| OpenAPI | Snapshot del recurso nuevo |

### Excluye (explícito)

| Capacidad | Motivo |
|-----------|--------|
| Align HTTP | Requiere `mantener` + UX confirmación; post-MVP |
| Diagnóstico drift / MAX negocio | Complejidad; Fase D |
| Cambio `generation_policy` | Gobernanza Catalog |
| CRUD `ultimo_numero` | SC-GOV-01 |
| Admin series fiscales | Store distinto |
| Frontend React completo | Contrato FE posterior (como ORG/INV FE packages) |
| Crear/borrar sequence_key | Solo Catalog + seed/lazy |
| Nuevas Strategy classes | No existen; no inventar |

### Gate de aceptación MVP

> Un ADMIN_TENANT autenticado puede listar y ver secuencias de su tenant, ajustar formato/activo con validaciones, y obtener preview del próximo código **sin consumir correlativo** y **sin** poder alterar el contador ni el catálogo.

---

## 3. Fases posteriores (fuera de MVP)

Alineadas a `codigo-generation-admin/00`:

| Fase | Contenido |
|------|-----------|
| **C** | Align + `cfg.secuencias.mantener` |
| **D** | Diagnóstico DGN-* + `diagnosticar` |
| **E** | Hardening: historial audit, anti-colisión avanzada, reportes |
| **F** | Frontend admin + menú |

---

## 4. Extensiones mínimas permitidas a infraestructura existente

Sin tocar Gateway/Catalog/ORG/INV:

| Cambio | Justificación |
|--------|----------------|
| Extender `update_secuencia` con `numero_inicial` + audit columns | Cerrar gap B + auditoría |
| Nuevas queries en `queries/cfg/` | Listado paginado dual-path |
| Seed SQL permisos `cfg.secuencias.*` | RBAC |

Cualquier cambio al Motor requiere **nueva autorización explícita** fuera de este alcance.

---

## 5. Orden de implementación sugerido (cuando se autorice)

1. Permisos RBAC + esqueleto módulo + deps.
2. Queries list/detail + schemas Read.
3. Servicios GET + tests aislamiento.
4. OpenAPI gate lectura.
5. Validator + PATCH B + tests.
6. Preview vía Gateway + tests.
7. Certificación Backend CFG MVP → paquete FE contract (docs) → FE.

---

## 6. Dictamen final

| Pregunta | Dictamen |
|----------|----------|
| ¿% módulo CFG ya existe? | **~30%** del producto admin (ponderado); **~0%** del módulo ERP; **~90%** de la fundación |
| ¿% por implementar? | **~70%** producto; **~100%** capa ERP admin |
| ¿Reutilizable sin modificar Motor? | Table, Repo, Gateway ops, Catalog, seed, patrones session/pagination, diseño admin docs |
| ¿Desarrollo nuevo? | Módulo `cfg` completo, queries, schemas, services, routers, RBAC, validators, tests, OpenAPI |
| ¿Alcance primera versión? | **MVP = lectura + PATCH B + preview** (Fases A+B diseño); align/diagnóstico después |

---

## 7. Relación con documentación previa

| Paquete | Relación |
|---------|----------|
| `codigo-generation-admin/` | Especificación funcional/API — **sigue vigente** como input de implementación |
| `cfg-admin-audit/` (este) | Auditoría AS-IS post Ola 1 — **cuantifica gaps y fija MVP** |
| Baseline V1 / ORG-INV cert | Congelados; no se reabren por CFG admin |

---

*Fin del paquete de auditoría. No se modificó código de aplicación.*
