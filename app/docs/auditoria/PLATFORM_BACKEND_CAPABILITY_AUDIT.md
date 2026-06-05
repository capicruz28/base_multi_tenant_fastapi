# Auditoría integral — Cobertura funcional Platform Administration (Backend)

**Fecha:** 2026-06-02  
**Alcance:** Repositorio Backend `base_multi_tenant_fastapi` únicamente. Frontend en repositorio separado (no analizado).  
**Modo:** Solo lectura — sin código, sin repair, sin commit.  
**Objetivo:** Determinar si la superficie funcional de Platform Administration está completamente soportada por Backend, identificando brechas funcionales, contractuales y de administración para cerrar Backend antes de concentrar esfuerzo en Frontend/UX.

---

## 1. Resumen ejecutivo

| Dimensión | Veredicto |
|-----------|-----------|
| **Cadena BD → Servicio → Endpoint → OpenAPI** | **Parcialmente completa** — núcleo operativo existe; varias capacidades de BD no tienen API o están incompletas |
| **Pantallas menú Platform (`/super-admin/*`)** | **7 de 9** con API directa; Dashboard sin contrato dedicado |
| **Bloqueadores Backend (P0)** | 2 — reactivación cliente incompleta; posible fallo de filtro `cliente_id` en superadmin |
| **Deuda contractual P1** | Paginación módulos, empresas cross-tenant, usuarios platform CRUD, SSO/federación, test conexión simulado |
| **Clasificación global** | **~72% soportado**, **~18% parcial**, **~10% no soportado** en capacidades esperadas de administración de plataforma |

**Conclusión:** El Backend **no está listo** para asumir que Frontend/QA no descubrirán más brechas contractuales sin cerrar primero los ítems P0–P1 de este documento. La mayoría de gaps de **UX** (toggles, copy, cascadas) son Frontend, pero varios son **síntoma de semántica Backend ambigua** (cliente `es_activo` vs `estado_suscripcion`).

---

## 2. Metodología y fuentes

### 2.1 Cadena analizada

```
TABLAS_BD_CENTRAL.sql
    → Modelo SQLAlchemy / queries (tables.py, *_service.py)
        → DTOs / Schemas Pydantic
            → Endpoints FastAPI (OpenAPI)
                → Capacidad funcional real (reglas de negocio, multi-BD, RBAC)
```

### 2.2 Fuentes

| Fuente | Ruta / uso |
|--------|------------|
| Esquema BD central | `app/docs/database/1.- TABLAS_BD_CENTRAL.sql` |
| Router OpenAPI | `app/api/v1/api.py` |
| Clientes / Conexiones | `app/modules/tenant/` |
| Superadmin | `app/modules/superadmin/` |
| Módulos catálogo | `app/modules/modulos/` |
| Auth / SSO / Auth-config | `app/modules/auth/` |
| ORG (empresas tenant) | `app/modules/org/` |
| Métricas | `app/api/metrics_endpoint.py`, `app/core/metrics/basic_metrics.py` |
| Menú Platform | `app/bootstrap_v2/02_catalog/S020__seed_admin_menu.sql` |
| Auditorías previas | `PLATFORM_FINAL_SURFACE_AUDIT.md`, `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` |

### 2.3 Autenticación Platform

- Endpoints críticos usan `@require_super_admin()` + permisos `tenant.*`, `modulos.menu.*`.
- Login Platform: `user_type=platform_admin`, Origin `platform.app.local` (smoke RC1).
- **Inconsistencia:** `/auth-config` y `/sso` usan `RoleChecker(["SUPER_ADMIN"])` (código rol), no el mismo patrón que `require_super_admin` + `platform_admin`.

### 2.4 Limitaciones

- No se validó runtime contra BD real (solo código).
- Frontend no disponible — ítems “solo FE” se marcan como **Frontend** con inferencia de contrato OpenAPI.

---

## 3. Inventario BD central vs exposición API

### 3.1 Tablas en `TABLAS_BD_CENTRAL.sql`

| Tabla / grupo | En BD central | API Platform / Admin | Estado |
|---------------|---------------|----------------------|--------|
| `cat_moneda`, `cat_pais`, `cat_departamento`, `cat_provincia`, `cat_distrito` | Sí | `/api/v1/catalogos-globales/*` | **Parcial** — servicio ejecuta en BD **tenant** (`client_id`), no ADMIN central explícito |
| `cliente` | Sí | `/api/v1/clientes/*` | **Soportado** |
| `cliente_conexion` | Sí | `/api/v1/conexiones/*` | **Parcial** — test conexión simulado |
| `cliente_auth_config` | Sí | `/api/v1/auth-config/clientes/{id}` | **Soportado** (auth rol distinto) |
| `federacion_identidad` | Sí | `/api/v1/sso/*` | **No soportado** (501) |
| `modulo`, `modulo_seccion`, `modulo_menu`, `modulo_rol_plantilla` | Sí | `/modulos-v2`, `/secciones`, `/modulos-menus`, `/plantillas-roles` | **Soportado** |
| `cliente_modulo` | Sí | `/api/v1/cliente-modulo/*` | **Soportado** (licencias/activación) |
| `usuario`, `rol`, `usuario_rol`, `rol_menu_permiso` | Sí (shared) | `/usuarios`, `/roles`, `/superadmin/usuarios` | **Parcial** — platform sin CRUD dedicado |
| `refresh_tokens` | Sí | vía `/superadmin/usuarios/{id}/sesiones/` | **Soportado** (lectura) |
| `auth_audit_log` | Sí | `/superadmin/auditoria/autenticacion/` | **Soportado** |
| `log_sincronizacion_usuario` | Sí | `/superadmin/auditoria/sincronizacion/` | **Soportado** |
| `org_empresa` | FK en central, **DDL en ERP** (`3.- TABLAS_BD_ERP_COMPLETO.sql`) | `/api/v1/org/empresas` (tenant session) | **No soportado** cross-tenant desde Platform |

### 3.2 Nota arquitectónica catálogos

`CatalogosGlobalesService` documenta operaciones sobre catálogos en **BD del tenant** (`execute_query(..., client_id=target)`). El script central define las mismas tablas `cat_*` globalmente. Para Platform, el `client_id` resuelto es el del operador (típicamente cliente SYSTEM). **Validar en staging** que catálogos Platform lean/escriban la BD esperada (central vs ERP del tenant SYSTEM).

---

## 4. Mapa API Platform (OpenAPI)

Prefijo base: `/api/v1/`

| Área menú FE | Prefijo API | Tag OpenAPI |
|--------------|-------------|-------------|
| Dashboard | *(ninguno dedicado)* | — |
| Clientes | `/clientes/` | Clientes (Super Admin) |
| Módulos | `/modulos-v2/`, `/secciones/`, `/modulos-menus/`, `/plantillas-roles/`, `/cliente-modulo/` | Módulos / Activación |
| Auditoría | `/superadmin/auditoria/` | Auditoría (Super Admin) |
| Catálogos ×5 | `/catalogos-globales/` | Catálogos Globales (Super Admin) |
| *(no en menú, backend sí)* | `/conexiones/`, `/auth-config/`, `/sso/`, `/superadmin/usuarios/`, `/api/v1/metrics/` | Varios |

---

## 5. Análisis por superficie

### 5.1 Clientes

| Capacidad esperada | BD | Servicio | Endpoint | OpenAPI | Real | Matriz |
|--------------------|-----|----------|----------|---------|------|--------|
| Crear | `cliente` | `ClienteOnboardingService` | `POST /clientes/` | Sí | Sí + credenciales iniciales | **Soportada** |
| Editar | `cliente` | `ClienteService.actualizar_cliente` | `PUT /clientes/{id}/` | Sí | Sí (incl. branding en body) | **Soportada** |
| Desactivar (soft) | `es_activo`, `estado_suscripcion` | `eliminar_cliente` | `DELETE /clientes/{id}/` | Sí | `es_activo=0`, `cancelado` | **Soportada** |
| Reactivar registro | `es_activo` | `activar_cliente` **no** restaura `es_activo` | `PUT .../activar/` | Sí | **Solo** `estado_suscripcion=activo` | **Parcial** |
| Reactivar completo | `es_activo` | `actualizar_cliente` | `PUT /clientes/{id}/` | Sí | Requiere `es_activo: true` explícito | **Parcial** |
| Suspender | `estado_suscripcion` | `suspender_cliente` | `PUT .../suspender/` | Sí | Sí | **Soportada** |
| Activar suscripción | `estado_suscripcion` | `activar_cliente` | `PUT .../activar/` | Sí | No equivale a reactivar DELETE | **Parcial** |
| Branding lectura | campos branding | `get_branding_*` | `GET /clientes/branding`, `GET /tenant/branding` | Sí | Público + tenant | **Soportada** |
| Branding escritura SA | campos branding | vía `ClienteUpdate` | `PUT /clientes/{id}/` | Sí | Sin endpoint dedicado SA | **Soportada** |
| Conexiones | `cliente_conexion` | `ConexionService` | `/conexiones/*` | Sí | Ver §5.6 | **Soportada** |
| Empresas del cliente | `org_empresa` (ERP) | `empresa_service` | `/org/empresas` | Sí | **Solo tenant session**, no `cliente_id` param SA | **No soportada** |
| Licencias / módulos | `cliente_modulo` | `ClienteModuloService` | `/cliente-modulo/*` | Sí | Activación, límites, vencimiento | **Soportada** |
| Dashboard cliente | agregaciones | `obtener_estadisticas` | `GET /clientes/{id}/estadisticas/` | Sí | Usuarios, módulos, conexiones, días activo | **Soportada** |
| Auditoría asociada | `auth_audit_log` | `SuperadminAuditoriaService` | `/superadmin/auditoria/*?cliente_id=` | Sí | Filtro opcional, no ruta anidada | **Parcial** |
| Filtros listado | índices | `listar_clientes` | `GET /clientes/` | Sí | `solo_activos`, `buscar`, `skip/limit` — **sin** `estado_suscripcion`, `plan`, `tipo_instalacion` | **Parcial** |

**Semántica dual crítica (P0):**

| Acción | `es_activo` | `estado_suscripcion` | Visible con `solo_activos=true` |
|--------|-------------|----------------------|--------------------------------|
| `DELETE` cliente | 0 | cancelado | No |
| `PUT .../suspender/` | 1 | suspendido | Sí |
| `PUT .../activar/` | sin cambio | activo | Solo si `es_activo=1` |
| `PUT` con `es_activo: true` | 1 | (editable) | Sí |

---

### 5.2 Módulos (catálogo global)

| Capacidad | Endpoint(s) | Estado |
|-----------|-------------|--------|
| CRUD catálogo | `GET/POST/PUT/DELETE /modulos-v2/` | **Soportado** (DELETE = soft) |
| Soft delete | `DELETE`, `PATCH .../desactivar/` | **Soportado** |
| Reactivación | `PATCH .../activar/` → `es_activo=true` | **Soportado** |
| Secciones | `/secciones/*` CRUD + orden | **Soportado** |
| Menús módulo | `/modulos-menus/*` CRUD + visibilidad | **Soportado** |
| Plantillas roles | `/plantillas-roles/*` + `permisos_json` | **Soportado** |
| Permisos (aplicación) | `rol_plantilla_applier` al activar módulo cliente | **Soportado** (indirecto) |
| Roles catálogo (RBAC platform) | `rol` con `cliente_id NULL` | **Parcial** — gestión vía `/roles` tenant, no UI Platform dedicada |
| Filtros | `solo_activos` (default **false**), `categoria` | **Parcial** — sin `buscar` |
| Paginación | `skip/limit` | **Parcial** — `total = len(página)` (TODO en código) |

---

### 5.3 Catálogos globales

| Entidad | CRUD | Soft delete | Reactivación | Filtros |
|---------|------|-------------|--------------|---------|
| Monedas | Sí | `DELETE` → `es_activo=0` | `PUT` + `es_activo: true` | `solo_activos` (default true) |
| Países | Sí | Igual | Igual | Igual |
| Departamentos | Sí | Igual | Igual | `pais_id` **requerido** en listado |
| Provincias | Sí | Igual | Igual | `departamento_id` requerido |
| Distritos | Sí | Igual | Igual | `provincia_id` (+ `departamento_id` opcional) |

- Sin parámetro `buscar` en API.
- Excepciones: Patrón B (`CustomException` → `HTTPException` sin `error_code` estándar global).
- Migración `V011__cat_ubigeo_es_activo.sql` alinea ubigeo a Clase A.

---

### 5.4 Auditoría global

| Recurso | Tabla BD | Servicio | Endpoint | Filtros |
|---------|----------|----------|----------|---------|
| Auth logs | `auth_audit_log` | `SuperadminAuditoriaService` | `GET /superadmin/auditoria/autenticacion/` | `cliente_id`, `usuario_id`, `evento`, `exito`, fechas, `ip`, `page/limit` |
| Detalle log | idem | idem | `GET .../autenticacion/{log_id}/` | `cliente_id` opcional |
| Sync logs | `log_sincronizacion_usuario` | idem | `GET .../sincronizacion/` | origen/destino, tipo, estado, operación, fechas |
| Estadísticas | agregaciones | idem | `GET .../estadisticas/` | `cliente_id`, fechas; top IPs/usuarios |
| Export CSV | — | — | — | **No soportado** |

**Capacidad pantalla Auditoría Global:** **Sí** — listados paginados + stats alimentan widgets; logs append-only (correcto).

**Brechas:**

- Paginación `page/limit` vs `skip/limit` en otras áreas (**contractual P1**).
- Sin búsqueda libre (solo filtros estructurados).
- `except Exception` → 500 en presentation (**P2**).
- Servicios tipan `cliente_id: Optional[int]` mientras endpoints usan `UUID` (**P0/P1 contractual**).

---

### 5.5 Dashboard Platform

| Métrica | Fuente | Tipo |
|---------|--------|------|
| Total clientes activos/inactivos | `SELECT COUNT(*) FROM cliente` | **Derivable BD** — requiere agregación FE o nuevo endpoint |
| Clientes por `estado_suscripcion` | `cliente` | **Derivable BD** — sin endpoint |
| Clientes trial / plan | `cliente.plan_suscripcion` | **Derivable BD** |
| Eventos auth (24h, fallos) | `GET /superadmin/auditoria/estadisticas/` | **Soportado API** |
| Sync fallidas | idem | **Soportado API** |
| Módulos en catálogo | `GET /modulos-v2/` | **Parcial** — paginación rota |
| Performance queries | `GET /api/v1/metrics/summary` | **Mock/in-memory** — no métricas negocio |
| Slow queries | `GET /api/v1/metrics/slow-queries` | **Mock/in-memory** |
| Endpoint dedicado dashboard | — | **Inexistente** |

**Veredicto Dashboard:** FE debe componer con múltiples GET o Backend debe exponer **BFF** `GET /superadmin/dashboard` (**P2**).

---

### 5.6 Conexiones

| Capacidad | Endpoint | Estado |
|-----------|----------|--------|
| Listar por cliente | `GET /conexiones/clientes/{cliente_id}/` | **Soportado** (incl. inactivas — filtro `es_activo` comentado en query) |
| Conexión principal | `GET .../principal/` | **Soportado** |
| Crear | `POST /conexiones/clientes/{cliente_id}/` | **Soportado** |
| Actualizar | `PUT /conexiones/{conexion_id}/` | **Soportado** (incl. `es_activo` en schema → reactivación) |
| Desactivar | `DELETE /conexiones/{conexion_id}/` | **Soportado** (204) |
| Test conectividad | `POST /conexiones/test` | **Parcial** — lógica **simulada** (`random`), no test real |
| Federación SSO | `federacion_identidad` | **No soportado** (ver §5.8) |

---

### 5.7 Usuarios Platform

Interpretación: operadores Platform (`ADMIN_PLATFORM`, cliente SYSTEM) + vista global tenants.

| Capacidad | API | Estado |
|-----------|-----|--------|
| Listado global tenants | `GET /superadmin/usuarios/` | **Soportado** (lectura) |
| Detalle cross-tenant | `GET /superadmin/usuarios/{id}/` | **Soportado** |
| Por cliente | `GET /superadmin/usuarios/clientes/{cliente_id}/usuarios/` | **Soportado** |
| Actividad (auth audit) | `GET .../{id}/actividad/` | **Soportado** |
| Sesiones (refresh_tokens) | `GET .../{id}/sesiones/` | **Soportado** |
| Crear usuario Platform | — | **No soportado** en superadmin (usar `/usuarios` en contexto SYSTEM) |
| Editar / desactivar / reset password SA global | — | **No soportado** cross-tenant |
| CRUD tenant usuarios | `/usuarios/*` | **Soportado** solo con sesión tenant |

**Bug contractual:** `list_usuarios_global` declara `cliente_id: Optional[int]` en OpenAPI; servicio también usa `int`; rutas y BD usan **UUID** (**P1 Backend**).

---

### 5.8 Auth-config y SSO (relacionado a clientes)

| Capacidad | API | Estado |
|-----------|-----|--------|
| Políticas auth por cliente | `GET/PUT /auth-config/clientes/{cliente_id}` | **Soportado** |
| Config global default | `GET /auth-config/global` | **Soportado** |
| SSO / federación CRUD | `/sso/*` | **No soportado** — `501 NOT_IMPLEMENTED` |
| Tabla `federacion_identidad` | BD | Sin servicio productivo |

---

## 6. Matriz de capacidades (consolidada)

| Área | Capacidad esperada | Soportada | Parcial | No soportada |
|------|-------------------|-----------|---------|--------------|
| **Clientes** | Crear | ✓ | | |
| | Editar | ✓ | | |
| | Desactivar (soft) | ✓ | | |
| | Reactivar post-DELETE | | ✓ | |
| | Suspender / activar suscripción | ✓ | | |
| | Branding R/W | ✓ | | |
| | Conexiones (gestión) | ✓ | | |
| | Empresas del cliente (SA) | | | ✓ |
| | Licencias (`cliente_modulo`) | ✓ | | |
| | Dashboard por cliente | ✓ | | |
| | Auditoría por cliente | | ✓ | |
| | Filtros avanzados listado | | ✓ | |
| **Módulos** | CRUD catálogo | ✓ | | |
| | Soft delete / reactivar | ✓ | | |
| | Secciones / menús / plantillas | ✓ | | |
| | Permisos (vía plantillas) | ✓ | | |
| | Paginación correcta | | ✓ | |
| | Búsqueda listado | | | ✓ |
| **Catálogos** | CRUD 5 entidades | ✓ | | |
| | Soft delete / reactivar | ✓ | | |
| | Filtros jerárquicos ubigeo | ✓ | | |
| | Búsqueda texto | | | ✓ |
| **Auditoría** | Auth + sync logs | ✓ | | |
| | Estadísticas | ✓ | | |
| | Export / búsqueda libre | | | ✓ |
| **Dashboard** | Métricas negocio agregadas | | ✓ | |
| | Endpoint BFF | | | ✓ |
| **Conexiones** | CRUD + principal | ✓ | | |
| | Test real | | ✓ | |
| **Usuarios Platform** | Lectura global | ✓ | | |
| | CRUD operadores / cross-tenant write | | | ✓ |
| **SSO** | Federación identidad | | | ✓ |

---

## 7. Hallazgos priorizados

Clasificación: **Backend** | **Frontend** | **Mixto**

| ID | Hallazgo | Impacto | Clasificación | Recomendación |
|----|----------|---------|---------------|---------------|
| H-001 | `PUT /clientes/{id}/activar/` no restaura `es_activo=1` tras `DELETE` | **P0** | **Backend** | Extender `activar_cliente` para setear `es_activo=1` y documentar semántica única de “reactivar” |
| H-002 | `cliente_id` tipado `int` en superadmin usuarios/auditoría vs `UUID` en BD y paths | **P0** | **Backend** | Unificar tipos a `UUID` en endpoints, servicios y OpenAPI |
| H-003 | Sin API Platform para gestionar `org_empresa` de un cliente arbitrario | **P1** | **Backend** | `GET/POST /clientes/{id}/empresas` con `require_super_admin` o impersonation formal |
| H-004 | Paginación módulos: `total = len(página)` | **P1** | **Backend** | `COUNT(*)` en `ModuloService` |
| H-005 | SSO / `federacion_identidad`: endpoints 501 | **P1** | **Backend** | Implementar CRUD federación o remover de alcance producto |
| H-006 | Test conexión BD simulado (`random`) | **P1** | **Backend** | Implementar probe SQL real o marcar OpenAPI como experimental |
| H-007 | Sin endpoint dashboard Platform / métricas negocio | **P1** | **Mixto** | BFF `GET /superadmin/dashboard` o contrato FE de composición documentado |
| H-008 | Filtros clientes: sin `estado_suscripcion`, `plan`, `tipo_instalacion` | **P1** | **Backend** | Ampliar query params en `listar_clientes` |
| H-009 | Superadmin usuarios: solo lectura | **P1** | **Backend** | CRUD platform users o documentar flujo único vía cliente SYSTEM |
| H-010 | Catálogos: sin `buscar`; excepciones sin `error_code` | **P2** | **Mixto** | Query `q` opcional; propagar handler global |
| H-011 | Paginación heterogénea (`skip` vs `page`) | **P2** | **Mixto** | Estandarizar en OpenAPI v2 o adapters FE documentados |
| H-012 | `/auth-config` RBAC `SUPER_ADMIN` vs `platform_admin` | **P2** | **Backend** | Alinear con `require_super_admin` |
| H-013 | `GET /api/v1/metrics/*` — métricas runtime, no SaaS | **P2** | **Backend** | No usar para dashboard negocio; documentar |
| H-014 | Endpoints debug en `/clientes/debug/*` sin guard SA explícito | **P2** | **Backend** | Deshabilitar en producción o proteger |
| H-015 | Auditoría: sin export CSV | **P3** | **Mixto** | Endpoint export opcional |
| H-016 | Menú FE no lista Conexiones/Usuarios/Auth como rutas top-level | **P3** | **Frontend** | Sub-rutas en detalle cliente; BE ya expone APIs |

---

## 8. Matriz hallazgo → impacto → recomendación (resumen ejecutivo)

| Hallazgo | Impacto | Recomendación |
|----------|---------|---------------|
| Reactivación cliente incompleta (H-001) | P0 | Unificar activate + restore `es_activo` |
| UUID/int superadmin (H-002) | P0 | Fix tipos OpenAPI + servicios |
| Empresas cross-tenant (H-003) | P1 | API anidada bajo cliente o scope impersonation |
| Paginación módulos (H-004) | P1 | COUNT en servicio |
| SSO 501 (H-005) | P1 | Implementar o excluir de MVP |
| Test conexión mock (H-006) | P1 | Test real o disclaimer API |
| Dashboard sin contrato (H-007) | P1 | BFF o spec composición FE |
| Filtros clientes (H-008) | P1 | Query params adicionales |
| Platform users write (H-009) | P1 | Definir alcance y API |
| Catálogos búsqueda/errores (H-010) | P2 | Mejoras contractuales |
| Paginación mixta (H-011) | P2 | Estandarizar |
| Auth-config RBAC (H-012) | P2 | Alinear guards |
| Metrics mock (H-013) | P2 | No confundir con dashboard |
| Debug endpoints (H-014) | P2 | End sh o guard |
| Export auditoría (H-015) | P3 | Opcional |

---

## 9. OpenAPI / DTO — inconsistencias contractuales

| Tema | Detalle | Severidad |
|------|---------|-----------|
| Paginación | Clientes/módulos: `skip+limit`; auditoría/usuarios SA: `page+limit` | P2 |
| Respuesta DELETE cliente | 200 + body vs catálogos 204 | P2 |
| `cliente_id` en superadmin list | `int` en schema vs `UUID` real | P0 |
| Módulos paginación | `pagination.total` incorrecto | P1 |
| Branding | `BrandingRead` vs campos en `ClienteRead` — duplicación OK | — |
| Conexiones | Credenciales en DTO read (encriptadas) — validar que FE no exponga | P2 |

---

## 10. Dashboard — detalle métricas

| Métrica UI típica | Estado Backend |
|-------------------|----------------|
| Total clientes | Derivable — `GET /clientes/?solo_activos=false` + count (o SQL agregado) |
| Clientes activos / suspendidos / cancelados | Derivable — requiere filtro por campo o agregación (parcial en listado) |
| Nuevos clientes (30 días) | Derivable — `fecha_creacion` en `ClienteRead` |
| Logins fallidos (24h) | **Soportado** — `/superadmin/auditoria/estadisticas/` |
| Top tenants por actividad | **Parcial** — stats por `cliente_id` |
| Módulos más activados | Derivable — `cliente_modulo` sin endpoint agregado |
| Salud BD / latencia | **Mock** — `/metrics/summary` in-memory |
| Ingresos / MRR | **No soportado** — no hay tablas facturación en central |

---

## 11. Backlog Backend para cerrar antes de FE-only QA

Orden sugerido (solo Backend):

1. **H-001** — Fix `activar_cliente` / endpoint `reactivar` documentado  
2. **H-002** — UUID en superadmin services + OpenAPI  
3. **H-004** — COUNT paginación módulos  
4. **H-008** — Filtros listado clientes  
5. **H-003** — API empresas por `cliente_id` (Platform)  
6. **H-007** — Contrato dashboard (BFF o doc composición)  
7. **H-005, H-006** — SSO y test conexión (o degradar explícitamente en OpenAPI)  
8. **H-009** — Alcance CRUD usuarios Platform  
9. **H-010–H-014** — Deuda contractual y seguridad  

---

## 12. Qué puede quedar solo en Frontend

| Ítem | Motivo |
|------|--------|
| Toggle “incluir inactivos” | API ya expone `solo_activos=false` |
| Copy ConfirmDialog “Desactivar” | Semántica API ya es soft delete |
| Cascada ubigeo en filtros | API exige `pais_id` → `departamento_id` → `provincia_id` |
| Composición dashboard sin BFF | Viable si se documentan llamadas paralelas |
| Parser central `error_code` | Backend ya emite en clientes/conexiones post-P0 |

---

## 13. Documentos relacionados

| Documento | Relación |
|-----------|----------|
| `PLATFORM_FINAL_SURFACE_AUDIT.md` | Auditoría UX/FE inferida desde BE |
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Estado excepciones P0 Tenant |
| `DELETE_CLIENTE_500_AUDIT.md` | DELETE cliente (cerrado BE) |
| `CLIENTES_EXCEPTION_MAPPING_AUDIT.md` | Mapeo errores clientes |
| `ONBOARDING_MENU_SAAS_ALIGNMENT_AUDIT.md` | Menú `/super-admin/*` |
| `PLATFORM_RBAC_GAP_FIX.md` | Permisos ADMIN_PLATFORM |

---

## 14. Conclusión final

El Backend de Platform Administration cubre el **núcleo operativo** (clientes, módulos catálogo, catálogos globales, auditoría lectura, conexiones CRUD, licencias por módulo, lectura global de usuarios). **No está completo** para una fase FE-only sin sorpresas en QA:

- **P0:** semántica reactivación clientes y tipos `cliente_id` superadmin.  
- **P1:** empresas cross-tenant, paginación módulos, dashboard contrato, SSO, test conexión real, escritura usuarios platform.  
- **Mixto:** filtros y paginación requieren acuerdo FE+BE aunque el fix principal es Backend.

Tras cerrar el backlog §11, el Frontend puede enfocarse en UX, composición de pantallas y estándares visuales sin descubrir brechas estructurales de administración en cada ciclo de QA.
