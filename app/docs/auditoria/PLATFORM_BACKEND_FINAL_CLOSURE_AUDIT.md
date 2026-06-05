# Auditoría final de cierre — Backend Platform Administration (Super Admin)

**Fecha:** 2026-06-02  
**Alcance:** Exclusivamente Backend — capacidades, reglas de negocio, contratos API, servicios, entidades y tablas. Sin Frontend, sin UX, sin componentes visuales.  
**Referencias:** `PLATFORM_BACKEND_CAPABILITY_AUDIT.md`, `PLATFORM_ADMIN_USE_CASE_AUDIT.md`, `1.- TABLAS_BD_CENTRAL.sql`, arquitectura BD central/tenant, router `app/api/v1/api.py`.  
**Modo:** Solo lectura — sin código, sin repair, sin commit.

---

## 1. Objetivo y criterio “Backend Platform Ready”

Un Backend se considera **funcionalmente completo y consistente** para Platform Administration en un SaaS multi-tenant cuando:

1. Un operador con privilegios de plataforma puede ejecutar los **casos de uso operativos MVP** sin callejones sin salida documentados.
2. Las **semánticas de ciclo de vida** (activo, suspendido, eliminado, reactivado) son coherentes entre tablas, servicios y endpoints.
3. Los **contratos API** reflejan tipos y paginación reales (sin metadata falsa).
4. Las capacidades **no implementadas** están explícitamente **retiradas del producto** o **aceptadas como limitación** con camino alternativo Backend (p. ej. impersonación).
5. La separación **BD central (ADMIN)** vs **BD tenant (ERP/dedicada)** está respetada en cada flujo.

Este documento define el **plan de cierre Backend** restante.

---

## 2. Arquitectura de datos relevante (resumen)

| Capa | Conexión | Tablas / dominio Platform |
|------|----------|-------------------------|
| **Central ADMIN** | `DatabaseConnection.ADMIN` | `cliente`, `cliente_conexion`, `cliente_auth_config`, `federacion_identidad`, `modulo`, `modulo_seccion`, `modulo_menu`, `modulo_rol_plantilla`, `cliente_modulo`, `usuario`/`rol`/`usuario_rol` (shared), `auth_audit_log`, `log_sincronizacion_usuario`, `cat_*` (definidas en script central) |
| **Tenant ERP** | `client_id` en query layer | `org_empresa` y resto ORG/ERP (`3.- TABLAS_BD_ERP_COMPLETO.sql`) |
| **Tenant dedicada** | `cliente_conexion` + routing | Mismas tablas operativas que shared, en BD del cliente |

**Flujo transversal de soporte:** `POST /api/v1/auth/impersonate/{cliente_id}/` emite sesión tenant efectiva para operar ORG/usuarios con reglas tenant sin duplicar APIs Platform.

---

## 3. Hallazgos pendientes (detalle de cierre)

Cada ítem incluye los 10 campos solicitados. Los ítems **cerrados** en auditorías previas (DELETE cliente `await`, excepciones P0 en clientes/conexiones) no se repiten salvo como contexto.

---

### F-001 — Reactivación de cliente incompleta tras desactivación lógica

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-C04 Reactivar cliente; UC-C06 confundido con reactivación post-DELETE |
| 2 | **Tablas:** `cliente` (`es_activo`, `estado_suscripcion`) |
| 3 | **Servicios:** `ClienteService.activar_cliente`, `ClienteService.eliminar_cliente`, `ClienteService.listar_clientes` |
| 4 | **Endpoints:** `PUT /api/v1/clientes/{id}/activar/`, `DELETE /api/v1/clientes/{id}/`, `GET /api/v1/clientes/` |
| 5 | **Riesgo operativo:** Alto — operador “reactiva” pero el tenant sigue invisible y bloqueado |
| 6 | **Riesgo de soporte:** Alto — tickets “cliente reactivado pero no aparece / no puede entrar” |
| 7 | **Riesgo integridad datos:** Medio — estados contradictorios (`estado_suscripcion=activo`, `es_activo=0`) |
| 8 | **Severidad:** **P0** |
| 9 | **Acción:** **Implementar** — `activar_cliente` y/o `PUT /reactivar/` debe setear `es_activo=1` y alinear `estado_suscripcion` |
| 10 | **Justificación:** Regla de negocio rota en el núcleo del producto multi-tenant; no es tema de presentación |

---

### F-002 — Tipado `cliente_id` inconsistente en capa Superadmin

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-C12, UC-A01–A05, UC-P05–P06 (filtros por cliente) |
| 2 | **Tablas:** `auth_audit_log`, `usuario`, `log_sincronizacion_usuario` (lectura con filtro) |
| 3 | **Servicios:** `SuperadminAuditoriaService`, `SuperadminUsuarioService` (firmas `cliente_id: Optional[int]`) |
| 4 | **Endpoints:** `GET /superadmin/auditoria/*`, `GET /superadmin/usuarios/` (OpenAPI/query `UUID`) |
| 5 | **Riesgo operativo:** Medio–Alto — filtros por cliente pueden fallar silenciosamente o en QA |
| 6 | **Riesgo de soporte:** Medio — “no encuentro logs del cliente X” intermitente |
| 7 | **Riesgo integridad datos:** Bajo — no corrompe datos; afecta lectura |
| 8 | **Severidad:** **P0** |
| 9 | **Acción:** **Implementar** — unificar `UUID` en servicios, queries parametrizadas y OpenAPI |
| 10 | **Justificación:** Contrato API declara UUID; BD usa `UNIQUEIDENTIFIER`; deuda de migración int→UUID incompleta |

---

### F-003 — Test de conexión BD no funcional (simulado)

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-C08 Administrar conexiones — validar antes de producción |
| 2 | **Tablas:** `cliente_conexion` (persistencia posterior al test) |
| 3 | **Servicios:** `ConexionService.test_conexion` |
| 4 | **Endpoints:** `POST /api/v1/conexiones/test` |
| 5 | **Riesgo operativo:** Alto — credenciales inválidas guardadas; tenants `dedicated` inoperativos |
| 6 | **Riesgo de soporte:** Alto — diagnóstico de conectividad no confiable |
| 7 | **Riesgo integridad datos:** Medio — registros de conexión “válidos” sin validación real |
| 8 | **Severidad:** **P1** |
| 9 | **Acción:** **Implementar** probe SQL real **o** **Documentar** + marcar OpenAPI `deprecated`/experimental y rechazar guardado sin test real |
| 10 | **Justificación:** Operación crítica para `tipo_instalacion` dedicated/onpremise; el mock contradice el contrato implícito del endpoint |

---

### F-004 — Paginación catálogo módulos con total incorrecto

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-M01 CRUD/listado catálogo módulos |
| 2 | **Tablas:** `modulo` |
| 3 | **Servicios:** `ModuloService.obtener_modulos` (falta `contar_modulos`); `endpoints_modulos.listar_modulos` |
| 4 | **Endpoints:** `GET /api/v1/modulos-v2/` |
| 5 | **Riesgo operativo:** Medio — administración de catálogo grande inusable |
| 6 | **Riesgo de soporte:** Bajo–Medio |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P1** |
| 9 | **Acción:** **Implementar** `COUNT(*)` con mismos filtros que listado |
| 10 | **Justificación:** Metadata de paginación falsa es defecto contractual objetivo |

---

### F-005 — SSO / federación de identidad no implementado

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-AU02, UC-AU03; campo `cliente.modo_autenticacion` en `sso`/`hybrid` |
| 2 | **Tablas:** `federacion_identidad`, `cliente` |
| 3 | **Servicios:** Ninguno productivo (placeholders en presentation) |
| 4 | **Endpoints:** `/api/v1/sso/*` → **501 NOT IMPLEMENTED** |
| 5 | **Riesgo operativo:** Medio — expectativa de SSO en contrato de datos sin Backend |
| 6 | **Riesgo de soporte:** Medio si se promete SSO en ventas |
| 7 | **Riesgo integridad datos:** Bajo — tabla vacía |
| 8 | **Severidad:** **P1** (si producto incluye SSO); **P3** (si MVP sin SSO) |
| 9 | **Acción:** **Retirar del producto** (MVP) **o** **Implementar** CRUD + flujo OIDC/SAML mínimo **o** **Aceptar como limitación** documentada |
| 10 | **Justificación:** Hueco funcional explícito; OpenAPI expone rutas que nunca funcionan |

---

### F-006 — Auth-config: guard distinto a resto de Platform

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-AU01 Configurar políticas auth por cliente |
| 2 | **Tablas:** `cliente_auth_config` |
| 3 | **Servicios:** `AuthConfigService` |
| 4 | **Endpoints:** `GET/PUT /api/v1/auth-config/clientes/{cliente_id}` — `RoleChecker(["SUPER_ADMIN"])` |
| 5 | **Riesgo operativo:** Medio — operador `ADMIN_PLATFORM` sin rol literal `SUPER_ADMIN` recibe 403 |
| 6 | **Riesgo de soporte:** Medio — “no puedo cambiar políticas del cliente” |
| 7 | **Riesgo integridad datos:** Bajo |
| 8 | **Severidad:** **P1** |
| 9 | **Acción:** **Implementar** alineación con `require_super_admin()` + `platform_admin` **o** **Documentar** que solo aplica a operadores con rol código `SUPER_ADMIN` |
| 10 | **Justificación:** Inconsistencia de autorización dentro del mismo dominio Platform |

---

### F-007 — Empresas del tenant sin API Platform nativa

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-C10 Administrar empresas del cliente (más allá de EMP001 onboarding) |
| 2 | **Tablas:** `org_empresa` (ERP/tenant); `cliente` (referencia) |
| 3 | **Servicios:** `empresa_service` (tenant scope); `MinimalErpTenantBootstrapService` (solo onboarding); `ImpersonationService` |
| 4 | **Endpoints:** `/api/v1/org/empresas` (sesión tenant); **no** `/clientes/{id}/empresas`; `POST /auth/impersonate/{cliente_id}/` |
| 5 | **Riesgo operativo:** Medio — dependencia obligatoria de impersonación no formalizada |
| 6 | **Riesgo de soporte:** Medio — equipos que no conozcan el flujo de soporte |
| 7 | **Riesgo integridad datos:** Bajo si se usa impersonación; medio si se intentan hacks con SYSTEM |
| 8 | **Severidad:** **P1** |
| 9 | **Acción:** **Documentar** impersonación como camino oficial MVP **o** **Implementar** APIs SA anidadas bajo cliente |
| 10 | **Justificación:** Onboarding crea EMP001; administración posterior requiere contexto tenant; arquitectura actual lo resuelve solo vía impersonación |

---

### F-008 — Usuarios del tenant: escritura solo en sesión tenant

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-C11 Administrar usuarios del cliente (crear/editar/desactivar) |
| 2 | **Tablas:** `usuario`, `usuario_rol`, `rol` |
| 3 | **Servicios:** `SuperadminUsuarioService` (lectura); `UsuarioService` (mutación con `current_user.cliente_id`) |
| 4 | **Endpoints:** Lectura `GET /superadmin/usuarios/*`; escritura `POST/PUT/DELETE /api/v1/usuarios/*` + impersonación |
| 5 | **Riesgo operativo:** Medio — mismo que F-007 |
| 6 | **Riesgo de soporte:** Medio |
| 7 | **Riesgo integridad datos:** Alto si se intenta crear usuario “desde plataforma” sin impersonar (quedaría en SYSTEM) |
| 8 | **Severidad:** **P1** |
| 9 | **Acción:** **Documentar** flujo impersonación + auditoría `impersonation_*` **o** **Implementar** mutación SA con `cliente_id` explícito y validación |
| 10 | **Justificación:** Patrón multi-tenant correcto en mutación; falta contrato Platform explícito |

---

### F-009 — Usuarios Platform (operadores): sin dominio API dedicado

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-P01–UC-P04 Crear/editar/desactivar/reactivar operadores `ADMIN_PLATFORM` |
| 2 | **Tablas:** `usuario`, `usuario_rol`, `rol` (cliente SYSTEM) |
| 3 | **Servicios:** `UsuarioService`; bootstrap D010 / `PlatformRbacBootstrapService` |
| 4 | **Endpoints:** `POST/PUT/DELETE /api/v1/usuarios/` en contexto SYSTEM (no `/superadmin/platform-usuarios`) |
| 5 | **Riesgo operativo:** Bajo–Medio — procedimiento no estándar para alta de operadores |
| 6 | **Riesgo de soporte:** Medio — onboarding de nuevo admin plataforma |
| 7 | **Riesgo integridad datos:** Medio — rol incorrecto si no se asigna `ADMIN_PLATFORM` |
| 8 | **Severidad:** **P1** (documentación mínima); **P2** (API dedicada) |
| 9 | **Acción:** **Documentar** runbook SYSTEM + asignación rol **o** **Implementar** endpoints Platform operators |
| 10 | **Justificación:** Funcional vía APIs genéricas; falta formalización para SaaS operado por terceros |

---

### F-010 — Dashboard Platform sin contrato Backend

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-D01, UC-D02 KPIs agregados |
| 2 | **Tablas:** `cliente`, `auth_audit_log`, `cliente_modulo` (agregables); no facturación |
| 3 | **Servicios:** `SuperadminAuditoriaService.obtener_estadisticas`; `ClienteService.listar_clientes`; `basic_metrics` (no negocio) |
| 4 | **Endpoints:** Parcial `GET /superadmin/auditoria/estadisticas/`; **no** `GET /superadmin/dashboard`; `GET /metrics/summary` (runtime mock) |
| 5 | **Riesgo operativo:** Bajo para MVP si se documenta composición |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Documentar** contrato de composición (lista de endpoints + campos) **o** **Implementar** BFF agregador |
| 10 | **Justificación:** KPIs derivables existen; falta unificación contractual, no capacidad de lectura |

---

### F-011 — Filtros de listado clientes limitados

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** Operaciones masivas / soporte por plan, estado suscripción, tipo instalación |
| 2 | **Tablas:** `cliente` |
| 3 | **Servicios:** `ClienteService.listar_clientes` |
| 4 | **Endpoints:** `GET /api/v1/clientes/` (`solo_activos`, `buscar` únicamente) |
| 5 | **Riesgo operativo:** Bajo–Medio |
| 6 | **Riesgo de soporte:** Medio en bases >100 clientes |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Implementar** query params `estado_suscripcion`, `plan_suscripcion`, `tipo_instalacion` |
| 10 | **Justificación:** Campos existen en tabla y DTO; filtro es extensión acotada |

---

### F-012 — Catálogos globales: integridad jerárquica al desactivar padre

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-G05 Dependencias ubigeo |
| 2 | **Tablas:** `cat_pais`, `cat_departamento`, `cat_provincia`, `cat_distrito` |
| 3 | **Servicios:** `CatalogosGlobalesService.deactivate_*` |
| 4 | **Endpoints:** `DELETE /catalogos-globales/{entidad}/{id}` |
| 5 | **Riesgo operativo:** Bajo — referencias inconsistentes en formularios ERP |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Medio — padre inactivo, hijos activos |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Implementar** validación hijos activos **o** **Aceptar como limitación** + cascada manual |
| 10 | **Justificación:** Soft delete por entidad sin reglas de árbol |

---

### F-013 — Catálogos: ejecución en BD tenant vs script central

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-G01–G04 Catálogos globales Platform |
| 2 | **Tablas:** `cat_*` (central script y ERP tenant) |
| 3 | **Servicios:** `CatalogosGlobalesService` (`client_id=target`) |
| 4 | **Endpoints:** `/api/v1/catalogos-globales/*` |
| 5 | **Riesgo operativo:** Medio — catálogos editados en BD equivocada en staging/prod |
| 6 | **Riesgo de soporte:** Alto si hay divergencia central vs SYSTEM tenant |
| 7 | **Riesgo integridad datos:** Alto en despliegues mal configurados |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Documentar** BD canónica para catálogos Platform + validación en bootstrap **o** **Implementar** conexión ADMIN explícita |
| 10 | **Justificación:** Ambigüedad arquitectónica entre `TABLAS_BD_CENTRAL` y `execute_query(..., client_id)` |

---

### F-014 — Excepciones Superadmin/módulos sin `error_code` estándar

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** Todos los dominios Platform con Patrón B (`CustomException` → `HTTPException`) |
| 2 | **Tablas:** N/A |
| 3 | **Servicios:** Presentation `superadmin`, `modulos`, `catalogos_globales` |
| 4 | **Endpoints:** Varios bajo `/superadmin/*`, `/modulos-v2/*`, `/catalogos-globales/*` |
| 5 | **Riesgo operativo:** Bajo |
| 6 | **Riesgo de soporte:** Medio — diagnóstico 500 genérico |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Implementar** propagación handler global (programa excepciones P3) |
| 10 | **Justificación:** Clientes/conexiones ya alineados; inconsistencia intra-Platform |

---

### F-015 — Paginación heterogénea (`skip` vs `page`)

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** Integradores y clientes API internos |
| 2 | **Tablas:** N/A |
| 3 | **Servicios:** Cliente/Modulo vs Superadmin |
| 4 | **Endpoints:** `/clientes/`, `/modulos-v2/` vs `/superadmin/auditoria/`, `/superadmin/usuarios/` |
| 5 | **Riesgo operativo:** Bajo |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Documentar** mapa de paginación **o** **Implementar** estandarización v2 |
| 10 | **Justificación:** Deuda contractual; no bloquea operación si está documentado |

---

### F-016 — Endpoints debug en router clientes

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** Seguridad Platform |
| 2 | **Tablas:** `usuario`, `rol` |
| 3 | **Servicios:** `debug_user_access_levels` en deps |
| 4 | **Endpoints:** `GET /api/v1/clientes/debug/user-info`, `.../debug/access-levels` |
| 5 | **Riesgo operativo:** Medio en producción |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Bajo |
| 8 | **Severidad:** **P2** |
| 9 | **Acción:** **Implementar** deshabilitación por entorno **o** **Retirar del producto** en prod |
| 10 | **Justificación:** Superficie de información sensible fuera de menú Platform formal |

---

### F-017 — Auditoría: export masivo ausente

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** Compliance / export CSV |
| 2 | **Tablas:** `auth_audit_log`, `log_sincronizacion_usuario` |
| 3 | **Servicios:** `SuperadminAuditoriaService` |
| 4 | **Endpoints:** Solo JSON paginado |
| 5 | **Riesgo operativo:** Bajo para MVP |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P3** |
| 9 | **Acción:** **Aceptar como limitación** MVP **o** **Implementar** export async |
| 10 | **Justificación:** No bloquea operación diaria Platform |

---

### F-018 — Búsqueda textual en catálogos globales

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-G01 listados grandes |
| 2 | **Tablas:** `cat_*` |
| 3 | **Servicios:** `CatalogosGlobalesService.list_*` |
| 4 | **Endpoints:** `GET /catalogos-globales/*` |
| 5 | **Riesgo operativo:** Bajo |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P3** |
| 9 | **Acción:** **Aceptar como limitación** **o** **Implementar** param `q` |
| 10 | **Justificación:** Jerarquía acotada; listados pequeños en muchos despliegues |

---

### F-019 — Métricas `/api/v1/metrics` no son KPIs SaaS

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-D02 confusión con dashboard negocio |
| 2 | **Tablas:** N/A (in-memory) |
| 3 | **Servicios:** `basic_metrics` |
| 4 | **Endpoints:** `GET /api/v1/metrics/summary`, `/slow-queries` |
| 5 | **Riesgo operativo:** Bajo si se documenta |
| 6 | **Riesgo de soporte:** Bajo |
| 7 | **Riesgo integridad datos:** Ninguno |
| 8 | **Severidad:** **P3** |
| 9 | **Acción:** **Documentar** alcance técnico (APM interno), no Platform KPI |
| 10 | **Justificación:** Evitar uso incorrecto en integraciones |

---

### F-020 — Impersonación: único camino — requiere normativa explícita

| # | Campo |
|---|--------|
| 1 | **Caso de uso:** UC-AU04; habilita UC-C10/C11 escritura |
| 2 | **Tablas:** N/A (+ audit `auth_audit_log` eventos `impersonation_*`) |
| 3 | **Servicios:** `ImpersonationService` |
| 4 | **Endpoints:** `POST /auth/impersonate/{cliente_id}/`, `POST /auth/impersonate/end/` |
| 5 | **Riesgo operativo:** Bajo — flujo **completo** hoy |
| 6 | **Riesgo de soporte:** Medio sin documentación |
| 7 | **Riesgo integridad datos:** Bajo — audit trail existe |
| 8 | **Severidad:** **P1** (documentación obligatoria MVP) |
| 9 | **Acción:** **Documentar** como **patrón oficial** Platform→Tenant (no es gap de código) |
| 10 | **Justificación:** Cierra F-007/F-008 sin duplicar APIs si se acepta modelo de soporte |

---

## 4. Backend Platform Completion Matrix

Clasificación por dominio mínimo solicitado.

| Dominio | Estado | MVP Platform | Notas |
|---------|--------|--------------|-------|
| **Clientes** | **Parcial** | Requerido | Ciclo vida casi completo; **P0** reactivación (F-001); filtros P2 (F-011) |
| **Conexiones** | **Parcial** | Requerido | CRUD + principal OK; test **P1** (F-003) |
| **Módulos** | **Parcial** | Requerido | CRUD + activar/desactivar OK; paginación **P1** (F-004) |
| **Secciones** | **Completa** | Requerido | `/secciones/*` + `modulo_seccion` |
| **Menús** | **Completa** | Requerido | `/modulos-menus/*` + `modulo_menu` |
| **Plantillas de roles** | **Completa** | Requerido | `/plantillas-roles/*` + aplicación en activación módulo |
| **Catálogos globales** | **Completa** | Requerido | CRUD + soft delete + reactivación; validar BD canónica P2 (F-013) |
| **Auditoría** | **Completa** | Requerido | Auth + sync + stats; fix UUID P0 (F-002); export P3 |
| **Dashboard Platform** | **Parcial** | No requerido MVP* | Composable vía APIs; BFF P2 (F-010); *requiere **documentación** obligatoria MVP |
| **Usuarios Platform** | **Parcial** | Requerido | Lectura global OK; CRUD vía SYSTEM — documentar P1 (F-009) |
| **Auth Config** | **Parcial** | Requerido | Servicio OK; guard P1 (F-006) |
| **Impersonación** | **Completa** | Requerido | Implementado; normativa P1 (F-020) |
| **SSO/Federación** | **No implementada** | No requerido MVP | Retirar o limitar (F-005) |
| **Empresas Tenant** | **Parcial** | Requerido | Onboarding EMP001 + impersonación + `/org/empresas` (F-007, F-020) |
| **Usuarios Tenant** | **Parcial** | Requerido | Lectura SA + mutación vía impersonación (F-008, F-020) |

**Leyenda MVP:** “No requerido MVP” = puede diferirse si se documenta alternativa Backend válida.

---

## 5. Criterio de madurez (estimación)

Método: promedio ponderado por dominio **requerido MVP** (13 dominios; excluye SSO del denominador MVP).

| Dominio MVP | Peso | Madurez actual (%) | Tras obligatorios (%) |
|-------------|------|--------------------|------------------------|
| Clientes | 12 | 82 | 98 |
| Conexiones | 8 | 72 | 88 |
| Módulos | 8 | 78 | 95 |
| Secciones | 5 | 100 | 100 |
| Menús | 5 | 100 | 100 |
| Plantillas | 6 | 100 | 100 |
| Catálogos globales | 8 | 90 | 92 |
| Auditoría | 10 | 88 | 96 |
| Dashboard (doc) | 4 | 45 | 75 |
| Usuarios Platform | 8 | 68 | 82 |
| Auth Config | 8 | 75 | 92 |
| Impersonación | 10 | 92 | 98 |
| Empresas Tenant | 9 | 62 | 85 |
| Usuarios Tenant | 9 | 70 | 88 |

**Fórmula:** Σ(peso × madurez) / Σ(peso) con pesos que suman 100.

| Métrica | Valor |
|---------|-------|
| **Madurez Backend Platform actual (MVP)** | **~78 %** |
| **Madurez tras pendientes obligatorios únicamente** | **~91 %** |
| **Madurez teórica máxima (incl. SSO + BFF + APIs SA nativas)** | **~96 %** |

Los porcentajes son estimaciones de auditoría estática, no medición de tests automatizados.

---

## 6. Listas de cierre

### 6.1 Pendientes obligatorios — “Backend Platform Ready”

Deben estar **implementados** o **formalmente documentados** (contrato publicado interno) antes de declarar cierre:

| ID | Acción | Tipo |
|----|--------|------|
| F-001 | Reactivación cliente unificada (`es_activo` + suscripción) | **Implementar** |
| F-002 | `cliente_id` UUID en superadmin servicios/OpenAPI | **Implementar** |
| F-003 | Test conexión real **o** contrato “no productivo” + bloqueo guardado | **Implementar** o **Documentar** + OpenAPI |
| F-004 | COUNT paginación módulos | **Implementar** |
| F-005 | SSO: **Retirar del producto** MVP (501→no expuesto) **o** documento de limitación firmado | **Retirar** / **Documentar** |
| F-006 | Auth-config guards alineados a `platform_admin` | **Implementar** o **Documentar** |
| F-020 | Impersonación como patrón oficial Platform→Tenant (F-007, F-008) | **Documentar** |
| F-010 | Contrato composición dashboard (endpoints + campos KPI) | **Documentar** |
| F-013 | BD canónica para `cat_*` en operación Platform | **Documentar** |

**Total obligatorio:** 9 ítems (4 implementación crítica P0/P1 código; 5 documentación arquitectónica contractual).

---

### 6.2 Pendientes recomendados (post-Ready, pre-escala)

| ID | Acción |
|----|--------|
| F-011 | Filtros listado clientes por plan/estado/tipo |
| F-012 | Validación jerárquica catálogos |
| F-014 | Handler global `error_code` en superadmin/módulos/catálogos |
| F-015 | Estandarizar paginación o guía integradores |
| F-016 | Proteger/retirar endpoints debug |
| F-009 | Runbook o API dedicada operadores Platform |
| F-007 / F-008 | APIs SA nativas bajo `/clientes/{id}/` (si se rechaza impersonación como único camino) |

---

### 6.3 Elementos diferibles sin afectar operación Platform diaria

| ID | Elemento | Motivo |
|----|----------|--------|
| F-017 | Export CSV auditoría | Lectura paginada suficiente MVP |
| F-018 | Búsqueda `q` en catálogos | Volúmenes pequeños / jerarquía |
| F-019 | Aclarar `/metrics` vs KPI SaaS | No usado en flujos operativos |
| F-005 (implementación SSO) | MVP sin SSO | Tabla preparada |
| BFF dashboard (implementación) | Si F-010 documentado | Composición cliente-side o script |
| APIs SA empresas/usuarios | Si F-020 aceptado | Impersonación cubre soporte |
| MRR / facturación | Sin tablas | Fuera alcance Platform actual |

---

## 7. Plan de cierre Backend (orden sugerido)

| Fase | Duración orientativa | Entregables |
|------|----------------------|-------------|
| **Fase A — Bloqueantes** | 1 sprint | F-001, F-002, F-004, F-006 (código) |
| **Fase B — Confianza operativa** | 1 sprint | F-003 (test real o contrato), F-005 (retirar SSO MVP), F-016 |
| **Fase C — Contratos** | Paralelo doc | F-020, F-010, F-013, F-005 limitación, F-003 si mock |
| **Fase D — Declaración Ready** | Gate QA | Smoke Platform: crear→suspender→reactivar cliente; impersonate→crear usuario; activar módulo; catálogo CRUD; auditoría filtrada |
| **Fase E — Recomendados** | Backlog | F-011–F-015, F-009 |

---

## 8. Declaración de consistencia multi-tenant

Para considerar el Backend **consistente**, además de los ítems anteriores debe quedar escrito (documentación arquitectónica):

| Tema | Decisión requerida |
|------|-------------------|
| Cliente `shared` vs `dedicated` | Dónde viven `usuario`/`org_empresa` y qué conexión usa cada servicio SA |
| Catálogos `cat_*` | BD única fuente de verdad para Platform |
| Mutación tenant | Impersonación vs APIs SA |
| SSO | Fuera de MVP o roadmap con tabla `federacion_identidad` |
| Semántica DELETE cliente | Soft delete = `es_activo=0` + `cancelado`; reactivar = restaurar ambos |

---

## 9. Resumen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Backend Platform está listo hoy? | **No** — ~**78 %** madurez MVP; **2 P0** y varios **P1** abiertos |
| ¿Qué impide declarar Ready? | Reactivación cliente, tipos superadmin, test conexión, paginación módulos, normativa impersonación/SSO/dashboard no escrita |
| ¿Qué está sólido? | Onboarding cliente, módulos/secciones/menús/plantillas, catálogos, auditoría lectura, impersonación, suspender/activar suscripción |
| ¿Tras obligatorios? | ~**91 %** — suficiente para fase centrada en consumidores API/FE sin redescubrir huecos estructurales |
| ¿SSO en MVP? | **No implementado** — debe **retirarse del producto** o aceptarse limitación explícita |

---

## 10. Documentos relacionados

| Documento | Uso |
|-----------|-----|
| `PLATFORM_BACKEND_CAPABILITY_AUDIT.md` | Capacidad BD→API |
| `PLATFORM_ADMIN_USE_CASE_AUDIT.md` | Flujos operador UC-* |
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Excepciones clientes |
| `PLATFORM_RBAC_GAP_FIX.md` | Permisos ADMIN_PLATFORM |
| `ORGANIZACION_TABLAS_CENTRAL_VS_DEDICADA.md` | (si existe) ref. arquitectura tenant |

---

## 11. Conclusión

El Backend de Platform Administration tiene un **núcleo operativo maduro** (~78 %) apto para soporte SaaS multi-tenant en escenarios principales (alta cliente, licencias, catálogo, auditoría, impersonación). **No debe declararse “Backend Platform Ready”** hasta cerrar los **9 obligatorios** de §6.1 — en particular **F-001** y **F-002** (código) y **F-020** + **F-010** + **F-013** (contratos arquitectónicos).

Tras esa cerrada, los pendientes recomendados y diferibles pueden ejecutarse sin bloquear la operación Platform ni generar deuda crítica en integridad de datos o soporte L2.
