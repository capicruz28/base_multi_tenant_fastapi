# 04 — Recomendaciones para Fase 2 (Implementación)

**Fecha:** 2026-07-02  
**Modo:** Solo auditoría — recomendaciones arquitectónicas, sin implementación  
**Prerequisito:** `01_CATALOG_INVENTORY.md`, `02_CURRENT_ARCHITECTURE.md`, `03_SYNC_DESIGN_INPUTS.md`

---

## 1. Resumen ejecutivo

| Dimensión | Veredicto |
|-----------|-----------|
| Esquema dedicated | **Listo** — V010 crea las 5 tablas correctamente |
| Datos dedicated | **Vacío por diseño** — brecha funcional crítica para ERP |
| CRUD Platform | **Operativo** — Superadmin sobre BD ERP shared |
| Sync Platform → Dedicated | **No existe** — ADR-011 post-MVP pendiente |
| Precedente interno | `DedicatedPermissionCatalogSyncService` — patrón a replicar |
| PK para UPSERT | **Apto** — UUID estable si se preserva PK Platform |

---

## 2. Riesgos identificados

### R-01 — Dedicated sin datos cat_* post-onboarding (P0)

**Descripción:** S6 verifica tablas `cat_*` con 0 filas. Módulos INV/FIN/ORG resuelven `moneda_id` y FK geo contra tablas vacías en dedicated.

**Impacto:** Fallos runtime al procesar movimientos, asientos, direcciones en tenants dedicated.

**Mitigación Fase 2:** Sync manual obligatorio antes de operación ERP; documentar en flujo provisioning Platform Admin.

---

### R-02 — Divergencia de PK si se crean catálogos independientemente (P0)

**Descripción:** `CatalogosGlobalesService.create_*` asigna `uuid4()` local. Si un operador crea monedas en Platform y dedicated por separado, las PK no coinciden.

**Impacto:** UPSERT por PK falla; FK ERP inconsistentes cross-plane.

**Mitigación Fase 2:** Sync siempre inserta con PK Platform; prohibir CRUD manual `cat_*` en dedicated (solo lectura tenant).

---

### R-03 — Ambigüedad SSOT Platform (P1)

**Descripción:** Documentación legacy (`1.- TABLAS_BD_CENTRAL.sql`) ubica `cat_*` en central; `V020` actual no las incluye. CRUD Superadmin usa `client_id` tenant, no conexión ADMIN explícita.

**Impacto:** Implementación incorrecta del lector Platform si asume BD central.

**Mitigación Fase 2:** Fijar contrato: SSOT = tablas `cat_*` en BD ERP shared; lector con `client_id` de tenant reference (SYSTEM) o intent documentado.

---

### R-04 — FK jerárquica ubigeo (P1)

**Descripción:** Cadena `pais → departamento → provincia → distrito` con FK UUID. Sync fuera de orden causa violaciones.

**Impacto:** Transacción sync fallida parcialmente.

**Mitigación Fase 2:** Orden estricto en core; transacción única por nivel o saga con rollback.

---

### R-05 — Ausencia UNIQUE en niveles intermedios ubigeo (P2)

**Descripción:** Solo `ubigeo` (distrito) y `codigo_iso2` (país) tienen UNIQUE. Departamento/provincia permiten duplicados lógicos `(parent_id, codigo)`.

**Impacto:** Diff ambiguo si existen duplicados en Platform.

**Mitigación Fase 2:** UPSERT por PK UUID; validar integridad Platform pre-sync; no usar clave compuesta sin UNIQUE.

---

### R-06 — Índices V011 no aplicados en dedicated (P3)

**Descripción:** `V011__cat_ubigeo_es_activo.sql` añade `IDX_*_activo` pero no está en manifiesto provisioning. V010 ya incluye columnas `es_activo`.

**Impacto:** Solo performance — sin impacto funcional sync.

**Mitigación:** Opcional — incorporar índices V011 en manifiesto v2.2 o consolidar en V010 futuro (fuera de alcance sync).

---

### R-07 — `cliente_id` en endpoints tenant catalogos (P2)

**Descripción:** `CatalogosService` usa `current_user.cliente_id` — anti-patrón impersonación documentado en estándares ERP.

**Impacto:** Lectura catálogos en impersonación podría resolver BD incorrecta.

**Mitigación:** Separado de sync; corregir en ticket impersonación si aplica.

---

### R-08 — Sin GET by id en API Superadmin (P3)

**Descripción:** Servicio tiene `get_moneda` etc.; endpoints públicos no exponen GET `/{id}`.

**Impacto:** UX Platform Admin; no bloquea sync.

---

### R-09 — Sin tests de paridad cat_* (P1)

**Descripción:** Tests existentes cubren listados y seed vacío; no hay integración Platform↔Dedicated.

**Mitigación Fase 2:** Tests unitarios del core + integración con BD dedicada mock.

---

## 3. Diferencias estructurales consolidadas

| # | Platform (shared) | Dedicated | Severidad |
|---|-------------------|-----------|-----------|
| D-01 | Datos cat_* poblados (manual) | 0 filas | **Alta** — funcional |
| D-02 | Mismo DDL V010 | Mismo DDL V010 | Ninguna |
| D-03 | Posibles índices V011 si migración manual | Solo índices V010 | Baja |
| D-04 | `cat_*` en ERP shared | `cat_*` en BD dedicada aislada | **Alta** — por diseño ADR-011 |
| D-05 | Legacy central SQL documenta cat_* | V020 no las crea | Documental |

---

## 4. Recomendaciones arquitectónicas Fase 2

### 4.1 Estructura (prioridad alta)

1. Crear paquete `app/core/catalog/` con motor sync desacoplado de HTTP/SQL.
2. Crear executor dedicated en `app/infrastructure/provisioning/` siguiendo `DedicatedPermissionCatalogSyncService`.
3. Crear orquestador en `app/modules/superadmin/application/services/`.
4. Exponer endpoints bajo `/catalogos-globales/sync` en nuevo router Superadmin.

### 4.2 Contrato de sync (prioridad alta)

1. **Manual only** — POST explícito con `cliente_id` dedicated target.
2. **Preservar PK Platform** en INSERT — nunca generar `uuid4()` en destino.
3. **Soft deactivate** — `es_activo=0`; sin DELETE físico.
4. **Orden FK** — moneda∥país → departamento → provincia → distrito.
5. **Transacción** — por tabla o global con rollback ante FK error.

### 4.3 Fuente Platform (prioridad alta)

1. Documentar y fijar `platform_reference_cliente_id` en config o constante.
2. Lector usa `execute_query` contra shared DEFAULT — no ADMIN (tablas no están en V020).
3. Opcional: hash de catálogo Platform (`sha256` de filas compare columns) para skip sync idempotente.

### 4.4 Validaciones pre-sync (prioridad media)

1. Verificar `tipo_instalacion = dedicated` y `cliente_conexion` activa.
2. Verificar tablas `cat_*` existen (`COUNT` ≥ 0 permitido).
3. Preview/diff endpoint antes de execute (operación controlada).

### 4.5 Observabilidad (prioridad media)

1. Registrar resultado en log estructurado (inserted/updated/deactivated por tabla).
2. Evaluar reutilizar patrón `bootstrap_applied` con `script_code = product_reference_catalog_sync`.
3. Exponer última sync en status provisioning o endpoint dedicado.

### 4.6 Qué no hacer (prioridad alta)

| Prohibido | Razón |
|-----------|-------|
| Sync automático en lifespan/scheduler | Requisito ticket |
| Replicación SQL Server | Requisito ticket |
| Modificar DDL / V010 | Reglas integridad proyecto |
| Extender alcance a permisos/menús | Fuera de scope 5 catálogos |
| Usar `CatalogosGlobalesService` como sync writer | Mezcla CRUD tenant con cross-plane |

---

## 5. Checklist Fase 2 sugerido

| # | Tarea | Depende de |
|---|-------|------------|
| 1 | ADR-012 o addendum ADR-011 — sync manual cat_* | Esta auditoría |
| 2 | `product_reference_catalog_definitions.py` — tablas, columnas, orden | §01 |
| 3 | `product_reference_catalog_sync_core.py` — motor + tipos | Precedente F12-B |
| 4 | `platform_product_reference_catalog_reader.py` | R-03 resuelto |
| 5 | `dedicated_product_reference_catalog_sync_service.py` | `provisioning_dedicated_session` |
| 6 | `catalog_sync_orchestrator_service.py` | Validación dedicated |
| 7 | `endpoints_catalog_sync.py` — preview + execute | `require_super_admin` |
| 8 | Tests unitarios core + integración dedicated mock | — |
| 9 | Documentar en runbook Platform Admin: sync post-provisioning | — |
| 10 | Validación staging: INV `get_moneda_by_codigo` en dedicated post-sync | E2E |

---

## 6. Criterios de aceptación Fase 2 (propuestos)

1. Operador Platform puede ejecutar sync manual para un tenant dedicated específico.
2. Tras sync, `COUNT(*)` dedicated = `COUNT(*)` Platform por tabla (activos e inactivos).
3. PKs idénticas fila a fila entre Platform y dedicated.
4. `get_moneda_by_codigo` y listados `/catalogos/*` retornan datos en dedicated.
5. Segunda ejecución sin cambios Platform produce 0 inserts (idempotencia).
6. Tenant shared no es afectado por sync dedicated.
7. Sin ejecución automática en startup, scheduler ni colas.

---

## 7. Referencias de código

| Tema | Archivo |
|------|---------|
| DDL canónico | `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql` |
| ORM tablas | `app/infrastructure/database/tables_erp/tables_org.py` |
| GLOBAL_TABLES | `app/infrastructure/database/query_helpers.py` |
| CRUD Superadmin | `app/modules/superadmin/application/services/catalogos_globales_service.py` |
| Endpoints CRUD | `app/modules/superadmin/presentation/endpoints_catalogos_globales.py` |
| Lectura tenant | `app/modules/catalogos/application/services/catalogos_service.py` |
| Onboarding S6 | `app/infrastructure/provisioning/dedicated_catalog_seed_service.py` |
| Precedente sync | `app/infrastructure/provisioning/dedicated_permission_catalog_sync_service.py` |
| ADR réplica | `app/docs/arquitectura/hybrid-platform/architecture-baseline/02_ADR_STATUS.md` (ADR-011) |
