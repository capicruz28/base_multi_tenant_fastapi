# Auditoría final — Superficie activa Platform Administration

**Fecha:** 2026-06-02  
**Modo:** solo lectura — sin implementación, sin repair, sin commit  
**Alcance FE (rutas activas):**

| Ruta FE | Módulo menú (`SYS_ADMIN.PLATFORM.*`) |
|---------|--------------------------------------|
| `/super-admin/dashboard` | Dashboard |
| `/super-admin/clientes` | Gestión de Clientes |
| `/super-admin/modulos` | Módulos del Sistema |
| `/super-admin/auditoria` | Auditoría Global |
| `/super-admin/catalogos/paises` | Países |
| `/super-admin/catalogos/departamentos` | Departamentos |
| `/super-admin/catalogos/provincias` | Provincias |
| `/super-admin/catalogos/distritos` | Distritos |
| `/super-admin/catalogos/monedas` | Monedas |

**Repositorio analizado:** Backend (`base_multi_tenant_fastapi`) únicamente.  
**Repositorio Frontend:** separado — **no disponible en este workspace**.

---

## 1. Metodología y limitaciones

### 1.1 Fuentes utilizadas

| Fuente | Uso |
|--------|-----|
| Menú plataforma | `app/docs/database/6.- SEED_ADMIN_MENU.sql`, `app/bootstrap_v2/02_catalog/S020__seed_admin_menu.sql` |
| Contratos API | `app/api/v1/api.py`, módulos `tenant`, `superadmin`, `modulos` |
| Alineación menú SaaS | `ONBOARDING_MENU_SAAS_ALIGNMENT_AUDIT.md` |
| Mejoras Platform recientes | `TENANT_EXCEPTION_HANDLING_REMEDIATION.md`, `DELETE_CLIENTE_500_*`, commit `0ad1e26` (ubigeo `es_activo`) |
| Referencia Tenant Admin | `M4_FRONTEND_BACKEND_CONTRACT_AUDIT.md`, `docs/frontend/org/etapa-a/*`, `FLUJO_AUTH_MULTIEMPRESA_FE.md` |
| Smoke plataforma | `smoke_platform_RC1_final.json` |
| Estándar UX | **`ERP_FRONTEND_STANDARDS_V2.md`** — referenciado por el usuario; **no localizado en este repo** |

### 1.2 Criterios de evaluación (inferidos)

Dado que el estándar V2 no está en el repositorio Backend, la matriz evalúa **alineación contractual y de producto** usando:

1. **Checklist típico ERP V2** (toolbar, filtros, búsqueda, empty/skeleton, ConfirmDialog, acciones fila, reactivación coherente con API).
2. **Patrones Tenant Administration** documentados (`/admin/usuarios`, `/admin/roles`, ORG etapa-A: guards, `error_code`, query keys, empresa scope).
3. **Capacidades reales del API** Platform (lo que BE permite o impide).

**Leyenda de evidencia en recomendaciones:**

| Etiqueta | Significado |
|----------|-------------|
| **BE** | Confirmado en código Backend |
| **BE-QA** | Validado en QA Backend (evidencia en repo) |
| **INFER-FE** | Requiere verificación en repo Frontend |
| **GAP-BE** | Brecha de contrato o lógica en Backend |

### 1.3 Mapa API por pantalla

| Pantalla FE | Prefijo API principal | Notas |
|-------------|----------------------|-------|
| Dashboard | *Sin endpoint dedicado* | Agregación vía múltiples GET (inferido FE) |
| Clientes | `/api/v1/clientes/` | CRUD + suspender/activar + estadísticas |
| Módulos | `/api/v1/modulos-v2/` | Catálogo global + activar/desactivar |
| Auditoría | `/api/v1/superadmin/auditoria/` | Auth logs, sincronización, estadísticas |
| Catálogos ×5 | `/api/v1/catalogos-globales/` | CRUD + DELETE soft + `solo_activos` |

**Origin esperado:** `http://platform.app.local:{puerto}` (smoke / scripts plataforma).

---

## 2. Estado Backend relevante para UX (resumen)

| Área Platform | Estado Backend |
|---------------|----------------|
| Excepciones negocio en **clientes/conexiones** | P0 cerrado — propagación al handler global (`error_code` + HTTP correcto) |
| **DELETE cliente** | Corregido (`await execute_update`) — QA 200/404/400 |
| **POST cliente** conflicto código/subdominio | 409 tras P0 (antes 500 en Presentation) |
| **Catálogos** países/monedas | Soft delete completo Clase A (`es_activo`, PUT reactivación, `solo_activos`) |
| **Catálogos** dpto/prov/distrito | Tras `V011` — alineados a Clase A (misma API que países/monedas) |
| **Módulos** listado paginado | `total` = `len(página)` — paginación incorrecta (TODO en código) |
| **Cliente** reactivación post-DELETE | `PUT /activar/` no restaura `es_activo`; reactivación completa vía `PUT` con `es_activo: true` |
| **Auditoría / Módulos** Presentation | Patrón B (`CustomException` + `except Exception` → 500) — riesgo residual P3 |

---

## 3. Matriz consolidada de hallazgos

| ID | Pantalla | Área (#) | Hallazgo | Sev. | Tipo | Recomendación |
|----|----------|----------|----------|------|------|---------------|
| F-001 | **Todas** | 10 Navegación | Menú plataforma en BD expone 9 rutas `/super-admin/*` bajo `SYS_ADMIN.PLATFORM.*`; tenant admin no ve catálogos (scope correcto post-S020). | — | — | Mantener guards FE `platform_admin` + ruta exacta del menú. **BE** |
| F-002 | **Todas** | 9 Consistencia visual | Estándar `ERP_FRONTEND_STANDARDS_V2.md` no versionado en repo Backend; no se puede certificar tokens/layout sin FE. | P2 | Deuda técnica | Incorporar estándar al monorepo docs o enlace CI doc-sync FE↔BE. **INFER-FE** |
| F-003 | **Todas** | 7 ConfirmDialogs | API usa DELETE/PUT destructivos con semántica de desactivación; estándar V2 exige copy “Desactivar” no “Eliminar”. | P1 | Mejora UX | Unificar copy ConfirmDialog con semántica soft delete por entidad. **BE** + **INFER-FE** |
| F-004 | **Todas** | 8 Reactivación | Catálogos y módulos: reactivación vía `PUT` + `es_activo: true` o endpoint `activar`. Clientes: modelo dual `es_activo` + `estado_suscripcion`. | P1 | Mejora UX | Matriz de reactivación por pantalla (tabla §4). **BE** |
| F-005 | **Dashboard** | 11 Dashboard | No existe `GET /super-admin/dashboard`; menú es shell FE. Datos probables: conteos clientes, `GET .../auditoria/estadisticas/`. | P2 | Deuda técnica | Documentar contrato dashboard o crear BFF agregador. **BE** |
| F-006 | **Dashboard** | 5 Skeletons | Sin contrato de carga parcial; riesgo de pantalla vacía si FE no compone skeletons por widget. | P2 | Mejora UX | Skeleton por tarjeta + error boundary por widget. **INFER-FE** |
| F-007 | **Dashboard** | 4 Estados vacíos | Sin API de “primer uso”; empty state depende 100% de FE. | P3 | Mejora UX | Empty state con CTA a Clientes / Auditoría. **INFER-FE** |
| F-008 | **Dashboard** | 9 Consistencia | Tenant `/admin` no tiene dashboard equivalente; Platform puede divergir sin guía V2. | P2 | Mejora UX | Alinear cards/métricas con tokens V2 y densidad ERP. **INFER-FE** |
| F-009 | **Clientes** | 1 Toolbars | API: POST crear, listado paginado; toolbar esperada: “Nuevo cliente” + búsqueda. Permiso `tenant.cliente.crear`. | — | — | Toolbar primaria + permiso RBAC. **BE** |
| F-010 | **Clientes** | 2 Filtros | `solo_activos=true` por defecto en `GET /clientes/` — clientes desactivados ocultos sin toggle. | P1 | Mejora UX | Toggle “Incluir inactivos” → `solo_activos=false`. **BE** + **INFER-FE** |
| F-011 | **Clientes** | 3 Búsquedas | `buscar` en query (razón social, nombre comercial, código, subdominio). | — | — | Debounce + limpiar búsqueda; alinear a Tenant listados. **INFER-FE** |
| F-012 | **Clientes** | 6 Acciones tabla | Acciones BE: PUT update, DELETE (soft), PUT suspender, PUT activar, GET estadísticas. | — | — | Menú fila con iconos y permisos por acción. **INFER-FE** |
| F-013 | **Clientes** | 7 ConfirmDialogs | DELETE devuelve 200 + mensaje “marcado como inactivo” (no 204). SYSTEM → 400. | P1 | Mejora UX | ConfirmDialog: desactivar; bloquear SYSTEM en UI. **BE-QA** |
| F-014 | **Clientes** | 8 Reactivación | `DELETE` pone `es_activo=0`; `PUT .../activar/` solo cambia `estado_suscripcion` **sin** `es_activo=1`. Reactivación completa: `PUT /clientes/{id}/` con `es_activo: true`. | **P0** | **Bug funcional** | FE: reactivar con PUT `es_activo`+`estado_suscripcion`; o BE: extender `activar_cliente` para restaurar `es_activo`. **GAP-BE** |
| F-015 | **Clientes** | 8 Reactivación | Confusión suspender (`estado_suscripcion=suspendido`) vs eliminar (`es_activo=0` + cancelado). | P1 | Mejora UX | Tres estados visuales: Activo / Suspendido / Inactivo (eliminado). **INFER-FE** |
| F-016 | **Clientes** | 4 Estados vacíos | Lista vacía legítima; POST onboarding devuelve credenciales iniciales — empty state debe invitar a crear. | P2 | Mejora UX | Empty + modal crear; mostrar credenciales post-201. **INFER-FE** |
| F-017 | **Clientes** | 5 Skeletons | Listado paginado; sin endpoint skeleton — patrón tabla Tenant. | P2 | Mejora UX | TableSkeleton filas + header. **INFER-FE** |
| F-018 | **Clientes** | 9 Consistencia | Mejoras BE: 409 ConflictError visible (P0); DELETE 200 (fix `await`). FE debe mapear `error_code` (`CLIENT_CODE_CONFLICT`, etc.). | P1 | Mejora UX | Toast/inline por `error_code`; no mensaje genérico 500. **BE-QA** + **INFER-FE** |
| F-019 | **Clientes** | 1 Toolbars | Crear cliente: validación 409 subdominio/código — coherente con estándar duplicados. | — | — | Verificar formulario muestra 409 en campo correcto. **INFER-FE** |
| F-020 | **Módulos** | 1 Toolbars | `GET /modulos-v2/` — permiso `modulos.menu.leer`; mutaciones superadmin. | — | — | Toolbar “Nuevo módulo” solo superadmin. **BE** |
| F-021 | **Módulos** | 2 Filtros | `solo_activos` default **false** (lista todos) — distinto a clientes/catálogos (default true). | P2 | Mejora UX | Default “Solo activos” = true para consistencia Platform. **INFER-FE** |
| F-022 | **Módulos** | 2 Filtros | Filtro `categoria` en API. | P2 | Mejora UX | Select categoría en toolbar. **INFER-FE** |
| F-023 | **Módulos** | 3 Búsquedas | Sin parámetro `buscar` en listado módulos. | P2 | Mejora UX | Búsqueda cliente o ampliar API con `q`. **GAP-BE** / **INFER-FE** |
| F-024 | **Módulos** | 6 Acciones tabla | `PUT activar` / `desactivar` dedicados; desactivar = soft (`es_activo=false`). | — | — | Acciones Activar/Desactivar coherentes con BE. **BE** |
| F-025 | **Módulos** | 7 ConfirmDialogs | No eliminar módulo core ni si activo en clientes — errores de negocio. | P1 | Mejora UX | ConfirmDialog + deshabilitar si regla negocio. **BE** |
| F-026 | **Módulos** | 8 Reactivación | `activar_modulo` restaura `es_activo=true` — patrón referencia para catálogos. | — | — | Replicar patrón UI en catálogos/clientes. **BE** |
| F-027 | **Módulos** | 12 Módulos | Paginación: `total = len(modulos)` en página actual — **metadata falsa**. | **P1** | **Bug funcional** | Implementar `COUNT(*)` en servicio; FE no confiar en `total_pages` hasta fix. **GAP-BE** |
| F-028 | **Módulos** | 5 Skeletons / 4 Empty | Catálogo puede ser corto; empty distinto a ERP. | P3 | Mejora UX | Empty “Sin módulos” + skeleton tabla. **INFER-FE** |
| F-029 | **Módulos** | 9 Consistencia | Presentation Patrón B — errores negocio OK; sin `error_code` en JSON si solo HTTPException. | P2 | Deuda técnica | Migrar a handler global (P3 programa excepciones). **BE** |
| F-030 | **Auditoría** | 1 Toolbars | Tabs probables: Autenticación / Sincronización / Estadísticas. | P2 | Mejora UX | Tab bar + export CSV (opcional). **INFER-FE** |
| F-031 | **Auditoría** | 2 Filtros | Auth: `cliente_id`, `usuario_id`, `evento`, `exito`, rango fechas, IP. Sync: origen/destino, tipo, estado, etc. | — | — | Panel filtros colapsable; persistir en URL query. **INFER-FE** |
| F-032 | **Auditoría** | 3 Búsquedas | Búsqueda libre no expuesta — solo filtros estructurados. | P2 | Mejora UX | Búsqueda por IP/usuario o documentar solo filtros. **INFER-FE** |
| F-033 | **Auditoría** | 6 Acciones tabla | Logs append-only — sin editar/borrar (correcto auditoría). | — | — | Solo ver detalle / copiar correlación. **INFER-FE** |
| F-034 | **Auditoría** | 11 Auditoría | `page`+`limit` (no skip) — distinto a clientes/módulos (`skip`+`limit`). | P1 | Mejora UX | Adapter paginación FE unificado (page vs skip). **BE** |
| F-035 | **Auditoría** | 5 Skeletons | Tablas grandes (limit max 200) — skeleton crítico. | P1 | Mejora UX | Skeleton + paginación server-side. **INFER-FE** |
| F-036 | **Auditoría** | 4 Estados vacíos | Filtros restrictivos → 0 filas; distinguir de error. | P2 | Mejora UX | Empty “Sin eventos en el período”. **INFER-FE** |
| F-037 | **Auditoría** | 11 Dashboard | `GET .../estadisticas/` alimenta widgets; alinear con dashboard global. | P2 | Mejora UX | Reutilizar estadísticas en `/super-admin/dashboard`. **INFER-FE** |
| F-038 | **Auditoría** | 9 Consistencia | `except Exception` → 500 en sync/estadísticas — riesgo P3 auth. | P2 | Deuda técnica | Alinear P3 auth/superadmin presentation. **BE** |
| F-039 | **Catálogos / Países** | 2–3 Filtros/búsqueda | `solo_activos=true` default; sin `buscar` en API. | P2 | Mejora UX | Toggle inactivos; búsqueda cliente en tabla o API `q`. **INFER-FE** |
| F-040 | **Catálogos / Países** | 8 Reactivación | DELETE → `es_activo=0`; reactivar `PUT` con `es_activo: true`. | — | — | Acción “Reactivar” + badge Inactivo. **BE** |
| F-041 | **Catálogos / Países** | 7 ConfirmDialogs | DELETE → 204 sin body. | P2 | Mejora UX | Confirm desactivar; toast éxito. **INFER-FE** |
| F-042 | **Catálogos / Monedas** | 8–9 | Misma API que países (Clase A post-mejoras). | — | — | Misma plantilla UI que Países. **BE** |
| F-043 | **Catálogos / Departamentos** | 2 Filtros | `pais_id` requerido para listar — jerarquía ubigeo. | P1 | Mejora UX | Selector país obligatorio antes de tabla; cascada. **BE** |
| F-044 | **Catálogos / Provincias** | 2 Filtros | `departamento_id` en listado. | P1 | Mejora UX | Cascada País → Departamento → Provincias. **BE** |
| F-045 | **Catálogos / Distritos** | 2 Filtros | `provincia_id` (+ `departamento_id` opcional en API). | P1 | Mejora UX | Cascada completa hasta distritos. **BE** |
| F-046 | **Catálogos / Ubigeo** | 8 Reactivación | Tras `V011`: soft delete alineado; FE legacy podía asumir DELETE físico. | P1 | Mejora UX | Verificar FE usa `solo_activos=false` + PUT reactivar post-migración. **BE** + **INFER-FE** |
| F-047 | **Catálogos / Todos** | 6 Acciones | Columna `es_activo` en DTO — badge en tabla. | P2 | Mejora UX | Badge Activo/Inactivo; filtrar columna. **BE** |
| F-048 | **Catálogos / Todos** | 9 Consistencia | `CustomException` → `HTTPException` sin `error_code` en catálogos globales. | P2 | Deuda técnica | Propagar handler global o incluir `error_code` en mapping. **BE** |
| F-049 | **Catálogos / Todos** | 10 Navegación | 5 ítems hermanos bajo `/super-admin/catalogos/*` — breadcrumb esperado. | P2 | Mejora UX | `Platform > Catálogos > {entidad}` consistente. **INFER-FE** |
| F-050 | **Clientes vs Tenant Admin** | 9 Consistencia | Tenant `/admin/usuarios`: filtro `es_activo`, soft delete, reactivación documentada; Platform clientes más complejo (suscripción + activo). | P1 | Mejora UX | Guía de paridad: copiar patrón toggle inactivos + reactivación de usuarios. **INFER-FE** |
| F-051 | **Platform global** | 9 Consistencia | Mapeo errores: Tenant Admin beneficiado por P0 clientes; auditoría/módulos aún Patrón B. | P2 | Deuda técnica | FE centralizar `parseApiError(detail, error_code)`. **INFER-FE** |
| F-052 | **Platform global** | 10 Navegación | Login plataforma: Origin `platform.app.local`; distinto a tenant subdomain. | — | — | No reutilizar Origin tenant en llamadas Platform. **BE-QA** |
| F-053 | **Clientes** | Bug funcional histórico | DELETE 500 por `execute_update` sin `await` — **corregido** (`dc5fea1`). | — | — | Verificar FE en QA regresión DELETE. **BE-QA** |
| F-054 | **Clientes** | Bug funcional histórico | POST 409 mostrado como 500 — **corregido** P0 Presentation. | — | — | QA regresión crear duplicado. **BE-QA** |

---

## 4. Matriz de reactivación / desactivación (contrato BE)

| Pantalla | Desactivar (API) | Reactivar (API) | Listar inactivos |
|----------|------------------|-----------------|------------------|
| Clientes | `DELETE /clientes/{id}/` → `es_activo=0`, `estado_suscripcion=cancelado` | `PUT` con `es_activo: true` (+ estado); **no** solo `PUT .../activar/` | `solo_activos=false` |
| Clientes (suspender) | `PUT .../suspender/` | `PUT .../activar/` (solo suscripción) | Sigue en lista si `es_activo=1` |
| Módulos | `desactivar` / soft delete | `PUT .../activar/` → `es_activo=true` | `solo_activos=false` (default actual: todos) |
| Países / Monedas / Ubigeo | `DELETE` → `es_activo=0` | `PUT` con `es_activo: true` | `solo_activos=false` |
| Auditoría | N/A (logs inmutables) | N/A | N/A |

**Hallazgo crítico:** F-014 — desalineación semántica en clientes entre DELETE, activar y listado.

---

## 5. Resumen por severidad

| Severidad | Cantidad | IDs representativos |
|-----------|----------|---------------------|
| **P0** | 1 | F-014 (reactivación cliente incompleta vía `/activar/`) |
| **P1** | 14 | F-003, F-004, F-010, F-013–F-015, F-018, F-025, F-027, F-034, F-043–F-046, F-050 |
| **P2** | 18 | F-002, F-005–F-008, F-016–F-017, F-021–F-023, F-029, F-030, F-032, F-036–F-038, F-039, F-041, F-047–F-049, F-051 |
| **P3** | 3 | F-007, F-028, F-029 (parcial) |
| **Cerrados (BE)** | 2 | F-053, F-054 |

---

## 6. Mejoras Platform ya implementadas (Backend)

| Mejora | Impacto en superficie |
|--------|------------------------|
| P0 excepciones Tenant Presentation | Clientes/conexiones: 409/400/404 visibles; FE deja de recibir 500 espurios en negocio |
| Fix `await` DELETE cliente | `/super-admin/clientes` DELETE operativo (200) |
| Ubigeo `es_activo` (V011) | Catálogos dpto/prov/distrito: paridad con países/monedas |
| Menú SaaS S020 | Solo platform ve `/super-admin/*`; tenant admin en `/admin/*` |
| Smoke platform RC1 | Login, menú, permisos `tenant.cliente.*` OK |

---

## 7. Comparación con Tenant Administration

| Patrón Tenant (`/admin/*`, `/app/org/*`) | Estado en Platform |
|----------------------------------------|-------------------|
| Guards sesión / tipo usuario | Platform: `platform_admin` + Origin platform (**INFER-FE**) |
| Toggle registros inactivos | Parcial — API lo soporta en clientes/catálogos; módulos default opuesto |
| Soft delete + reactivación explícita | Catálogos/módulos OK; **clientes con gap F-014** |
| Mapeo `error_code` en UI | Documentado en ORG etapa-A; Platform debe replicar post-P0 |
| Paginación consistente | Platform mixto: `skip` vs `page`; módulos con total incorrecto |
| Confirmación acciones destructivas | Estándar V2 — verificar en FE (**INFER-FE**) |

---

## 8. Riesgo de no abordar hallazgos

| Si no se corrige | Riesgo |
|------------------|--------|
| F-014 (P0) | Operador “reactiva” cliente pero permanece invisible (`es_activo=0`) |
| F-027 (P1) | Paginación módulos rota en UI — páginas vacías o duplicadas |
| F-010 + F-046 (P1) | Inactivos invisibles sin toggle — imposible reactivar desde UI |
| F-034 (P1) | Bugs de paginación copiados entre auditoría y otras tablas |
| F-002, F-051 (P2) | Deriva visual y mensajes de error inconsistentes entre pantallas |

---

## 9. Priorización recomendada (solo auditoría)

| Orden | ID / tema | Acción sugerida | Repo |
|-------|-----------|-----------------|------|
| 1 | F-014 | Extender `activar_cliente` o documentar PUT `es_activo` como única reactivación | BE + FE |
| 2 | F-027 | Fix `COUNT` paginación módulos | BE |
| 3 | F-010, F-046 | Toggle “Incluir inactivos” en todas las tablas Platform | FE |
| 4 | F-003, F-013 | Copy ConfirmDialog “Desactivar” | FE |
| 5 | F-043–F-045 | Cascada ubigeo en filtros | FE |
| 6 | F-018, F-051 | Parser central `error_code` | FE |
| 7 | F-005–F-008 | Dashboard contrato datos | FE (+ opcional BFF BE) |
| 8 | F-048, F-029 | Handler global catálogos/módulos (P3 programa) | BE |

---

## 10. Verificación pendiente en repositorio Frontend

Para cerrar la auditoría al 100% se requiere en el **repo Frontend** (no disponible aquí):

1. Lectura de `ERP_FRONTEND_STANDARDS_V2.md` y checklist por pantalla.
2. Inspección de componentes: `PageToolbar`, `DataTable`, `ConfirmDialog`, `EmptyState`, `TableSkeleton`.
3. QA visual regresión post-`dc5fea1` y P0 excepciones en `/super-admin/clientes`.
4. Confirmar cascada ubigeo y toggles `solo_activos` en catálogos.

---

## 11. Conclusión

La superficie Platform Administration está **operativamente soportada por el Backend** en las 9 rutas activas, con mejoras recientes claras en **clientes** (excepciones y DELETE). Los principales gaps para paridad con **ERP_FRONTEND_STANDARDS_V2** y **Tenant Administration** son:

1. **Bug funcional P0** en reactivación de clientes (F-014).  
2. **Paginación incorrecta** en módulos (F-027).  
3. **Consistencia UX** (toggles inactivos, ConfirmDialog, cascada ubigeo, dashboard sin contrato) — mayormente verificación e implementación **Frontend**.

Esta auditoría **no sustituye** una revisión visual del repo Frontend; clasifica hallazgos trazables desde Backend y estándares documentados del proyecto.

---

## 12. Documentos relacionados

| Documento | Relación |
|-----------|----------|
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Estado P0 Tenant / P1–P3 |
| `DELETE_CLIENTE_500_AUDIT.md` | Incidencia DELETE (cerrada BE) |
| `ONBOARDING_MENU_SAAS_ALIGNMENT_AUDIT.md` | Menú `/super-admin/*` |
| `M4_FRONTEND_BACKEND_CONTRACT_AUDIT.md` | Referencia Tenant Admin |
