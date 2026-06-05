# Auditoría de casos de uso — Platform Administration (Backend)

**Fecha:** 2026-06-02  
**Base:** `PLATFORM_BACKEND_CAPABILITY_AUDIT.md`, `1.- TABLAS_BD_CENTRAL.sql`, servicios, endpoints y reglas de negocio actuales.  
**Alcance:** Capacidad funcional real para un **Platform Admin** (operador con `platform_admin` / Super Admin, Origin plataforma).  
**No es:** inventario de endpoints, revisión OpenAPI aislada ni catálogo de tablas sin flujo.  
**Frontend:** repositorio separado — no analizado; se indica **Frontend** solo cuando el hueco es de orquestación/UX sin bloqueo Backend.  
**Modo:** Solo lectura — sin código, sin repair, sin commit.

---

## 1. Actor y contexto de sesión

| Elemento | Comportamiento real |
|----------|---------------------|
| Actor | Usuario autenticado en Origin plataforma (`platform.app.local`), típicamente cliente SYSTEM, rol `ADMIN_PLATFORM` y/o `is_super_admin` + `access_level >= 5` |
| Operaciones globales | `require_super_admin()` + permisos `tenant.*`, `modulos.menu.*` en rutas `/clientes`, `/modulos-v2`, `/superadmin/*`, etc. |
| Operaciones en tenant ajeno | **No nativas** en sesión plataforma: requieren **`POST /auth/impersonate/{cliente_id}/`** y luego APIs tenant (`/usuarios`, `/org/empresas`) con JWT de impersonación |
| BD central (ADMIN) | `cliente`, `cliente_conexion`, `cliente_auth_config`, `modulo*`, `cliente_modulo`, `usuario` (shared), `auth_audit_log`, `log_sincronizacion_usuario` |
| BD tenant (ERP) | `org_empresa` y resto ORG — vía conexión `client_id` o impersonación |

**Leyenda de estado de flujo**

| Estado | Significado |
|--------|-------------|
| **Completo** | El operador puede terminar el caso de uso solo con Backend actual, sin trucos documentados |
| **Parcial** | Parte del flujo funciona; hay paso roto, ambiguo o dependiente de otro mecanismo |
| **Imposible** | No existe camino Backend viable hoy para cerrar el caso de uso |

**Clasificación:** Backend | Frontend | Mixto

---

## 2. Resumen ejecutivo por dominio

| Dominio | Completos | Parciales | Imposibles |
|---------|-----------|-----------|------------|
| Clientes | 6 | 6 | 0 |
| Módulos | 5 | 2 | 0 |
| Catálogos globales | 4 | 1 | 0 |
| Auditoría global | 4 | 1 | 0 |
| Dashboard | 0 | 1 | 1 |
| Usuarios Platform | 2 | 4 | 0 |
| Auth / SSO | 1 | 1 | 2 |

**Bloqueadores Backend antes de fase FE-only:** reactivación cliente post-DELETE, administración empresas/usuarios tenant **sin** impersonación, SSO/federación, dashboard KPIs negocio, test conexión real.

---

## 3. Clientes

### UC-C01 — Crear cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

**Flujo esperado del operador**

1. Completa formulario (código, subdominio, razón social, contacto, plan, tipo instalación, etc.).
2. Confirma creación.
3. Recibe cliente activo + credenciales admin inicial + empresa sede + roles base + auth config + RBAC onboarding.

**Cadena real**

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Validación unicidad | `cliente` | `ClienteService._validar_*` | — (previo a POST) |
| Transacción onboarding | `cliente`, `rol`, `usuario`, `usuario_rol`, `cliente_auth_config`, `cfg_codigo_secuencia` | `ClienteOnboardingService.crear_cliente_con_onboarding` | `POST /api/v1/clientes/` |
| Empresa inicial | `org_empresa` | `MinimalErpTenantBootstrapService.ensure_empresa_inicial` | *(misma transacción ADMIN)* |
| RBAC menú tenant | `cliente_modulo`, `rol_permiso` (vía onboarding) | `OnboardingRbacService.bootstrap_cliente_rbac` | *(misma transacción)* |

**Punto de quiebre:** Ninguno en Backend para `tipo_instalacion=shared`. Para `dedicated`/`onpremise`, la empresa inicial se inserta en la misma sesión ADMIN; validar en staging que ERP del tenant dedicado quede alineado con conexión posterior.

---

### UC-C02 — Editar cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

**Flujo:** listar/obtener → `PUT` con campos parciales → persistencia con validación subdominio/código.

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Lectura | `cliente` | `ClienteService.obtener_cliente_por_id` | `GET /api/v1/clientes/{id}/` |
| Actualización | `cliente` | `ClienteService.actualizar_cliente` | `PUT /api/v1/clientes/{id}/` |

**Punto de quiebre:** Ninguno.

---

### UC-C03 — Desactivar cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

**Flujo:** confirmar → soft delete lógico.

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Regla SYSTEM | `cliente` | `eliminar_cliente` | — |
| Persistencia | `cliente` | `ClienteService.eliminar_cliente` | `DELETE /api/v1/clientes/{id}/` |

**Efecto real:** `es_activo=0`, `estado_suscripcion='cancelado'`. Cliente SYSTEM bloqueado (400).

**Punto de quiebre:** Ninguno.

---

### UC-C04 — Reactivar cliente (tras desactivar / DELETE lógico)

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** |

**Flujo esperado:** operador reactiva cliente desactivado → vuelve a listados activos y usuarios pueden acceder.

**Flujo real**

| Paso | ¿Funciona? | Tabla | Servicio | Endpoint |
|------|------------|-------|----------|----------|
| 1. Localizar inactivo | Sí, si FE usa `solo_activos=false` | `cliente` | `ClienteService.listar_clientes` | `GET /api/v1/clientes/?solo_activos=false` |
| 2. “Activar” con endpoint dedicado | **No completa el caso** | `cliente` | `ClienteService.activar_cliente` | `PUT /api/v1/clientes/{id}/activar/` |
| 3. Reactivación completa | Sí, si operador conoce contrato | `cliente` | `ClienteService.actualizar_cliente` | `PUT /api/v1/clientes/{id}/` con `es_activo: true` y estado deseado |

**Punto exacto donde se rompe**

- **Paso 2:** `activar_cliente` solo ejecuta `UPDATE ... SET estado_suscripcion = 'activo'` **sin** `es_activo = 1`.
- Tras UC-C03, `es_activo` permanece en `0` → el cliente **sigue excluido** de `listar_clientes` con `solo_activos=true` (default) y de validaciones que exigen cliente activo (p. ej. branding público).

**Impacto funcional:** El operador cree que “reactivó” el tenant, pero el registro sigue lógicamente eliminado.

---

### UC-C05 — Suspender cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Suspensión | `cliente` | `ClienteService.suspender_cliente` | `PUT /api/v1/clientes/{id}/suspender/` |

**Efecto:** `estado_suscripcion='suspendido'`, `es_activo` sin cambio (sigue visible en listado activo).

**Punto de quiebre:** Ninguno en Backend; FE debe distinguir “suspendido” vs “inactivo/eliminado”.

---

### UC-C06 — Reactivar suscripción (cliente suspendido, no eliminado)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** (si `es_activo=1`) |
| **Clasificación** | Backend |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Activar suscripción | `cliente` | `ClienteService.activar_cliente` | `PUT /api/v1/clientes/{id}/activar/` |

**Condición:** Aplica cuando el cliente **no** pasó por UC-C03. Si pasó por DELETE lógico, ver UC-C04.

---

### UC-C07 — Administrar branding del cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Leer (SA / detalle) | `cliente` | `ClienteService.obtener_cliente_por_id` / `get_branding_by_cliente` | `GET /clientes/{id}/`, `GET /clientes/tenant/branding` (tenant) |
| Escribir | `cliente` (`logo_url`, `favicon_url`, colores, `tema_personalizado`) | `ClienteService.actualizar_cliente` | `PUT /clientes/{id}/` |
| Preview login (subdominio) | `cliente` | `get_branding_by_subdomain` | `GET /clientes/branding?subdominio=` (público) |

**Punto de quiebre:** Ninguno. No hay upload de archivos en Backend (solo URLs); almacenamiento de binarios sería **Mixto** (FE + storage externo).

---

### UC-C08 — Administrar conexiones del cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** (test); **Mixto** (validar conectividad en UI) |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Listar | `cliente_conexion` | `ConexionService.obtener_conexiones_cliente` | `GET /conexiones/clientes/{cliente_id}/` |
| Principal | `cliente_conexion` | `obtener_conexion_principal` | `GET .../principal/` |
| Crear | `cliente_conexion` | `crear_conexion` | `POST /conexiones/clientes/{cliente_id}/` |
| Editar / reactivar | `cliente_conexion` | `actualizar_conexion` (incl. `es_activo`) | `PUT /conexiones/{conexion_id}/` |
| Desactivar | `cliente_conexion` | `desactivar_conexion` | `DELETE /conexiones/{conexion_id}/` |
| Probar antes de guardar | — | `test_conexion` | `POST /conexiones/test` |

**Punto exacto donde se rompe (parcial)**

- **Paso “Probar conexión”:** `ConexionService.test_conexion` devuelve éxito/fallo **simulado** (`random`), no abre socket SQL real.
- El operador puede **crear y guardar** credenciales creyendo que el test fue fiable → fallo operativo en producción.

**Flujo completo para alta/edición/baja:** sí, salvo confianza en test.

---

### UC-C09 — Administrar módulos del cliente (licencias / activación)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Ver activos | `cliente_modulo` + `modulo` | `ClienteModuloService.obtener_modulos_activos_cliente` | `GET /cliente-modulo/cliente/{cliente_id}/` |
| Activar + plantillas | `cliente_modulo`, `rol`, `rol_menu_permiso` | `activar_modulo_cliente` → `aplicar_plantillas_roles` | `POST /cliente-modulo/activar/` |
| Desactivar | `cliente_modulo` | `desactivar_modulo_cliente` | `DELETE /cliente-modulo/cliente/{cid}/modulo/{mid}/` |
| Límites / vencimiento / config | `cliente_modulo` | `actualizar_configuracion`, `extender_vencimiento` (si aplica) | `PUT .../configuracion/`, otros PUT del router |

**Punto de quiebre:** Dependencias entre módulos y módulo core no activables — errores de negocio esperados (400/409), no hueco de API.

---

### UC-C10 — Administrar empresas del cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** (impersonación); **Backend** (falta API SA nativa) |

**Flujo esperado:** desde consola Platform, sin “entrar como tenant”, listar/crear/editar empresas del cliente X.

**Flujos reales**

| Camino | Estado | Detalle |
|--------|--------|---------|
| A. Solo sesión plataforma | **Imposible** para CRUD adicional | No existe `GET/POST /clientes/{id}/empresas` |
| B. Tras crear cliente | **Completo** solo 1 empresa | `MinimalErpTenantBootstrapService` crea `org_empresa` EMP001 en onboarding |
| C. Impersonación | **Completo** | `POST /auth/impersonate/{cliente_id}/` → `GET/POST/PUT /api/v1/org/empresas` con sesión tenant |

| Paso roto (camino A) | Tabla | Servicio | Endpoint |
|----------------------|-------|----------|----------|
| Listar empresas de cliente X | `org_empresa` | `empresa_service.list_empresas_servicio` | `GET /org/empresas` — exige `client_id` de **sesión**, no parámetro SA |

**Punto exacto:** `get_org_session_client_id` resuelve tenant del JWT; en Origin plataforma sin impersonar es cliente SYSTEM, no el cliente objetivo.

---

### UC-C11 — Administrar usuarios del cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** |

| Acción | Sesión plataforma nativa | Tras impersonación |
|--------|--------------------------|-------------------|
| Listar / buscar | **Completo** | **Completo** |
| Ver detalle | **Completo** | **Completo** |
| Crear | **Imposible** | **Completo** |
| Editar / desactivar / roles | **Imposible** | **Completo** |

**Lectura (nativa)**

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `usuario` (+ joins roles) | `SuperadminUsuarioService.get_usuarios_globales` | `GET /superadmin/usuarios/?cliente_id=`, `GET .../clientes/{cid}/usuarios/` |

**Escritura (requiere impersonación)**

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `usuario` | `UsuarioService.crear_usuario` | `POST /api/v1/usuarios/` — fuerza `cliente_id = current_user.cliente_id` |

**Punto exacto donde se rompe (camino nativo)**

- **Paso crear/editar:** `crear_usuario` asigna `usuario_dict['cliente_id'] = current_user.cliente_id` (SYSTEM), no el tenant objetivo.

**Nota `dedicated`:** superadmin lectura usa `client_id` en query hacia BD dedicada; coherente si conexión está configurada.

---

### UC-C12 — Consultar auditoría del cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** (lectura y agregados) |
| **Clasificación** | Backend |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Logs auth | `auth_audit_log` | `SuperadminAuditoriaService.get_logs_autenticacion` | `GET /superadmin/auditoria/autenticacion/?cliente_id=` |
| Detalle evento | `auth_audit_log` | `obtener_log_autenticacion` | `GET .../autenticacion/{log_id}/` |
| Sync | `log_sincronizacion_usuario` | `get_logs_sincronizacion` | `GET .../sincronizacion/?cliente_origen_id=` / `cliente_destino_id=` |
| KPIs cliente | agregación | `obtener_estadisticas` | `GET .../estadisticas/?cliente_id=` |

**Punto de quiebre:** No hay ruta anidada `/clientes/{id}/auditoria`; es **Frontend** ensamblar la misma pantalla con query `cliente_id`. Backend soporta el caso de uso.

**Riesgo menor:** servicios tipan `cliente_id` como `int` internamente mientras el endpoint expone `UUID` — validar en QA (**Backend**).

---

## 4. Módulos (catálogo global del sistema)

> En este menú, “Roles” = **plantillas de rol por módulo** (`modulo_rol_plantilla`) y su aplicación al activar módulo en un cliente, **no** administración de roles `ADMIN_PLATFORM` ni RBAC tenant completo.

### UC-M01 — CRUD completo del catálogo de módulos

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** (paginación); **Frontend** (listado páginas) |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Listar | `modulo` | `ModuloService.obtener_modulos` | `GET /modulos-v2/` |
| Detalle | `modulo` | `obtener_modulo_por_id` | `GET /modulos-v2/{id}/` |
| Crear | `modulo` | `crear_modulo` | `POST /modulos-v2/` |
| Editar | `modulo` | `actualizar_modulo` | `PUT /modulos-v2/{id}/` |
| Eliminar (soft) | `modulo` | `eliminar_modulo` | `DELETE /modulos-v2/{id}/` |

**Punto exacto donde se rompe**

- **Paso listar paginado:** en `listar_modulos` (presentation), `total = len(modulos)` de la página actual → el operador no puede recorrer catálogo grande de forma fiable (páginas vacías/duplicadas).

**Reglas de negocio:** no eliminar `es_core`; no eliminar si activo en `cliente_modulo`.

---

### UC-M02 — Activar / desactivar módulo en catálogo

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Acción | Tabla | Servicio | Endpoint |
|--------|-------|----------|----------|
| Activar | `modulo` | `ModuloService.activar_modulo` | `PATCH /modulos-v2/{id}/activar/` |
| Desactivar | `modulo` | `desactivar_modulo` | `PATCH /modulos-v2/{id}/desactivar/` |

---

### UC-M03 — Gestionar secciones del módulo

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Router |
|-------|----------|--------|
| `modulo_seccion` | `ModuloSeccionService` | `/api/v1/secciones/` (CRUD, orden, soft delete) |

---

### UC-M04 — Gestionar menús del módulo

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Router |
|-------|----------|--------|
| `modulo_menu` | `ModuloMenuService` | `/api/v1/modulos-menus/` |

Incluye jerarquía (`menu_padre_id`), visibilidad, rutas, menús por `cliente_id` opcional.

---

### UC-M05 — Gestionar plantillas de roles (y permisos JSON)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Router |
|-------|----------|--------|
| `modulo_rol_plantilla` | `ModuloRolPlantillaService` | `/api/v1/plantillas-roles/` |

**Aplicación al cliente:** al activar módulo (UC-C09), `rol_plantilla_applier` crea roles y permisos en tenant.

---

### UC-M06 — “Roles” como entidad RBAC del catálogo

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** |

No hay pantalla/API “roles del módulo” separada de plantillas. Los roles runtime viven en `rol` / `usuario_rol` por cliente.

| Necesidad | Camino |
|-----------|--------|
| Definir permisos estándar del módulo | Plantillas — **Completo** |
| Ver/editar roles ya creados en un tenant | Impersonación + `/roles`, `/permisos` — **Parcial** |
| Roles globales plataforma (`ADMIN_PLATFORM`) | Bootstrap / SQL seed — fuera flujo UI |

---

## 5. Catálogos globales

### UC-G01 — CRUD monedas y países

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Entidad | Tabla | Servicio | Endpoint base |
|---------|-------|----------|-----------------|
| Moneda | `cat_moneda` | `CatalogosGlobalesService` | `/catalogos-globales/monedas` |
| País | `cat_pais` | idem | `/catalogos-globales/paises` |

**Condición operativa:** operaciones usan `client_id` del operador (SYSTEM). Confirmar en staging que es la BD donde deben vivir los catálogos globales del producto.

---

### UC-G02 — CRUD ubigeo (departamento → provincia → distrito)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | **Mixto** (jerarquía en FE) |

| Nivel | Tabla | Filtro obligatorio listado |
|-------|-------|----------------------------|
| Departamento | `cat_departamento` | `pais_id` |
| Provincia | `cat_provincia` | `departamento_id` |
| Distrito | `cat_distrito` | `provincia_id` |

**Flujo completo Backend:** sí, si FE respeta cascada. No hay búsqueda textual en API.

---

### UC-G03 — Soft delete catálogo

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Desactivar | `cat_*`.`es_activo` | `deactivate_*` | `DELETE /catalogos-globales/{entidad}/{id}` → 204 |

No hay validación de hijos activos al desactivar país (p. ej. departamentos siguen activos) — **deuda de integridad referencial lógica** (P2 Backend).

---

### UC-G04 — Reactivación catálogo

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Listar inactivos | `cat_*` | `list_*` con `solo_activos=false` | `GET ...?solo_activos=false` |
| Reactivar | `cat_*` | `update_*` con `es_activo: true` | `PUT .../{id}` |

---

### UC-G05 — Dependencias jerárquicas (integridad de negocio)

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** |

| Escenario | Comportamiento |
|-----------|----------------|
| Crear distrito bajo provincia activa | OK si FK válido |
| Desactivar país con hijos activos | **Permitido** (solo flag en padre) |
| Impedir uso de hijos de padre inactivo en ERP | Depende de validaciones en módulos consumidores — no centralizado en catálogo SA |

**Punto de quiebre:** operador puede dejar jerarquía incoherente (padre inactivo, hijos activos).

---

## 6. Auditoría global

### UC-A01 — Consultar eventos de autenticación

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `auth_audit_log` | `SuperadminAuditoriaService.get_logs_autenticacion` | `GET /superadmin/auditoria/autenticacion/` |

Incluye enriquecimiento `cliente` / `usuario` en respuesta.

---

### UC-A02 — Filtrar eventos

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | **Mixto** (UX filtros) |

Filtros soportados: `cliente_id`, `usuario_id`, `evento`, `exito`, `fecha_desde`/`fecha_hasta`, `ip_address`, `page`, `limit`, ordenación.

**Punto de quiebre:** sin búsqueda libre por texto — solo **Frontend** si se exige “buscar como Google”.

---

### UC-A03 — Navegar por cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Frontend (drill-down); Backend provee filtro |

Mismo endpoint con `cliente_id` obligatorio en drill-down.

---

### UC-A04 — Navegar por usuario

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Frontend + Backend |

`usuario_id` en query de listado auth.

---

### UC-A05 — Estadísticas / tablero de auditoría

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `auth_audit_log`, `log_sincronizacion_usuario` | `obtener_estadisticas` | `GET /superadmin/auditoria/estadisticas/` |

**Entregables:** totales auth, logins ok/fail, sync por tipo, top IPs/usuarios.

**Punto parcial:** sin export masivo (CSV) — operador que necesita extraer todo para compliance: **Imposible** en un solo flujo API.

---

### UC-A06 — Logs de sincronización (flujo relacionado)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

`GET /superadmin/auditoria/sincronizacion/` con filtros origen/destino/estado.

---

## 7. Dashboard Platform

### UC-D01 — Ver KPIs operativos del SaaS en un solo flujo

| Campo | Valor |
|-------|-------|
| **Estado** | **Imposible** (como caso de uso único) |
| **Clasificación** | **Mixto** |

**Flujo esperado:** abrir `/super-admin/dashboard` → Backend devuelve payload agregado listo.

**Punto exacto donde se rompe**

- No existe servicio ni endpoint “dashboard plataforma”.
- **Paso 1 fallido:** ninguna llamada única devuelve KPIs de negocio.

---

### UC-D02 — Componer dashboard con APIs existentes

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** |

| KPI | ¿Real? | Origen |
|-----|--------|--------|
| Total clientes / activos / suspendidos | Derivables | Múltiples `GET /clientes/` o agregación FE (sin endpoint COUNT global) |
| Nuevos clientes (30 d) | Derivable | Campo `fecha_creacion` en listado |
| Logins fallidos / auth 24h | **Real** | `GET /superadmin/auditoria/estadisticas/` |
| Sync fallidas | **Real** | idem |
| Módulos activados por tenant | Derivable | `GET /clientes/{id}/estadisticas/` por cliente o SQL futuro |
| MRR / ingresos / churn | **Inexistente** | Sin tablas facturación |
| Latencia / salud API | **Mock** | `GET /api/v1/metrics/summary` — memoria local, no BD |

---

## 8. Usuarios Platform (operadores del sistema)

> Distinto de “usuarios de un cliente” (UC-C11). Aquí: cuentas que operan la consola (`ADMIN_PLATFORM`, `superadmin`, etc.) en cliente SYSTEM.

### UC-P01 — Crear operador Platform

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** |

| Camino | Detalle |
|--------|---------|
| Seed / SQL bootstrap | **Completo** (D010, scripts repair) |
| UI Platform “invitar operador” | **Parcial** |

**Flujo API posible hoy:** sesión en SYSTEM → `POST /api/v1/usuarios/` → crea en `usuario` con `cliente_id` del operador actual → asignar rol `ADMIN_PLATFORM` vía `POST /usuarios/{id}/roles/{rol_id}/`.

**Punto de quiebre**

- No hay caso de uso documentado “crear operador platform” (validación de rol, email, permisos mínimos).
- Operador sin permiso `admin.usuario.crear` en SYSTEM no completa el flujo.
- No hay endpoint dedicado `/superadmin/platform-usuarios`.

---

### UC-P02 — Editar operador Platform

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | Backend |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `usuario` | `UsuarioService.actualizar_usuario` | `PUT /api/v1/usuarios/{id}/` (mismo `cliente_id` sesión) |

Mismo alcance que UC-P01: solo tenant SYSTEM de la sesión actual.

---

### UC-P03 — Desactivar operador Platform

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | Backend |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `usuario` | `UsuarioService.eliminar_usuario` | `DELETE /api/v1/usuarios/{id}/` (`es_eliminado=1`, `es_activo=0`) |

**Punto de quiebre:** auto-desactivación del único superadmin SYSTEM — reglas de negocio deben impedirlo (validar en servicio).

---

### UC-P04 — Reactivar operador Platform

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Backend** |

Reactivación vía `PUT /usuarios/{id}/` con `es_activo: true` (y posiblemente limpiar `es_eliminado` si el servicio lo permite). No hay endpoint `reactivar` dedicado.

**Lectura global cross-tenant:** no aplica a reactivación; solo usuarios SYSTEM.

---

### UC-P05 — Consultar actividad de un usuario (cualquier tenant)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `auth_audit_log` | `SuperadminUsuarioService.obtener_actividad_usuario` | `GET /superadmin/usuarios/{id}/actividad/?cliente_id=` |

---

### UC-P06 — Consultar sesiones de un usuario

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

| Tabla | Servicio | Endpoint |
|-------|----------|----------|
| `refresh_tokens` | `obtener_sesiones_usuario` | `GET /superadmin/usuarios/{id}/sesiones/?cliente_id=` |

Revocación masiva de sesiones desde SA: **no verificado** como flujo dedicado — **Parcial** si FE necesita “cerrar todas las sesiones”.

---

## 9. Auth / SSO

### UC-AU01 — Configurar políticas de autenticación de un cliente

| Campo | Valor |
|-------|-------|
| **Estado** | **Parcial** |
| **Clasificación** | **Mixto** |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Leer (crea default si falta) | `cliente_auth_config` | `AuthConfigService.obtener_config_cliente` | `GET /auth-config/clientes/{cliente_id}` |
| Actualizar | `cliente_auth_config` | `actualizar_config_cliente` | `PUT /auth-config/clientes/{cliente_id}` |

**Punto exacto donde puede romperse**

- Guard `RoleChecker(["SUPER_ADMIN"])` compara **código de rol** / nivel, no `require_super_admin` + `platform_admin`.
- Operador con solo `ADMIN_PLATFORM` y sin bypass `is_super_admin` puede recibir **403** aunque pase en `/clientes`.

Onboarding ya inserta fila en `cliente_auth_config` al crear cliente (UC-C01).

---

### UC-AU02 — Configurar federación / SSO (Azure, Google, SAML)

| Campo | Valor |
|-------|-------|
| **Estado** | **Imposible** |
| **Clasificación** | **Backend** |

| Paso | Tabla | Servicio | Endpoint |
|------|-------|----------|----------|
| Cualquier operación | `federacion_identidad` | — | `POST /sso/azure/config/`, `/google/config/`, `GET /sso/providers/`, `DELETE /sso/{id}/` |

**Punto exacto:** todos devuelven **501 NOT IMPLEMENTED** (o no ejecutan query real).

---

### UC-AU03 — Gestionar identidad federada (listar, activar, mapping)

| Campo | Valor |
|-------|-------|
| **Estado** | **Imposible** |
| **Clasificación** | **Backend** |

Tabla `federacion_identidad` existe en BD central; no hay servicio productivo conectado al flujo del operador.

---

### UC-AU04 — Flujo impersonación (soporte cross-tenant)

| Campo | Valor |
|-------|-------|
| **Estado** | **Completo** |
| **Clasificación** | Backend |

Casos de uso habilitados **solo** tras impersonar: UC-C10, UC-C11 (escritura), configuración tenant-scoped, etc.

| Paso | Servicio | Endpoint |
|------|----------|----------|
| Iniciar | `ImpersonationService.iniciar_impersonacion` | `POST /auth/impersonate/{cliente_id}/` |
| Finalizar | `ImpersonationService` | `POST /auth/impersonate/end/` |

Requisito: Super Admin. TTL ~120 min. Audit: eventos `impersonation_*` en `auth_audit_log`.

---

## 10. Matriz consolidada de casos de uso

| ID | Caso de uso | Estado | Clasificación |
|----|-------------|--------|---------------|
| UC-C01 | Crear cliente | Completo | Backend |
| UC-C02 | Editar cliente | Completo | Backend |
| UC-C03 | Desactivar cliente | Completo | Backend |
| UC-C04 | Reactivar cliente (post-DELETE) | Parcial | Backend |
| UC-C05 | Suspender cliente | Completo | Backend |
| UC-C06 | Reactivar suscripción | Completo | Backend |
| UC-C07 | Administrar branding | Completo | Backend |
| UC-C08 | Administrar conexiones | Parcial | Backend |
| UC-C09 | Administrar módulos del cliente | Completo | Backend |
| UC-C10 | Administrar empresas del cliente | Parcial | Mixto |
| UC-C11 | Administrar usuarios del cliente | Parcial | Mixto |
| UC-C12 | Consultar auditoría del cliente | Completo | Backend |
| UC-M01 | CRUD catálogo módulos | Parcial | Backend |
| UC-M02 | Activar/desactivar módulo catálogo | Completo | Backend |
| UC-M03 | Secciones | Completo | Backend |
| UC-M04 | Menús | Completo | Backend |
| UC-M05 | Plantillas roles | Completo | Backend |
| UC-M06 | Roles RBAC (fuera plantillas) | Parcial | Mixto |
| UC-G01 | CRUD monedas/países | Completo | Backend |
| UC-G02 | CRUD ubigeo | Completo | Mixto |
| UC-G03 | Soft delete catálogos | Completo | Backend |
| UC-G04 | Reactivación catálogos | Completo | Backend |
| UC-G05 | Integridad jerárquica | Parcial | Backend |
| UC-A01 | Consultar eventos auditoría | Completo | Backend |
| UC-A02 | Filtrar eventos | Completo | Mixto |
| UC-A03 | Navegar por cliente | Completo | Mixto |
| UC-A04 | Navegar por usuario | Completo | Mixto |
| UC-A05 | Estadísticas auditoría | Parcial | Mixto |
| UC-D01 | Dashboard KPI (un shot) | Imposible | Mixto |
| UC-D02 | Dashboard compuesto | Parcial | Mixto |
| UC-P01 | Crear usuario Platform | Parcial | Backend |
| UC-P02 | Editar usuario Platform | Parcial | Backend |
| UC-P03 | Desactivar usuario Platform | Parcial | Backend |
| UC-P04 | Reactivar usuario Platform | Parcial | Backend |
| UC-P05 | Actividad usuario | Completo | Backend |
| UC-P06 | Sesiones usuario | Completo | Backend |
| UC-AU01 | Config auth cliente | Parcial | Mixto |
| UC-AU02 | Config SSO proveedores | Imposible | Backend |
| UC-AU03 | Identidad federada | Imposible | Backend |
| UC-AU04 | Impersonación soporte | Completo | Backend |

---

## 11. Últimos huecos Backend (cerrar antes de FE-only)

Prioridad para que un Platform Admin **no encuentre callejones sin salida** en QA Backend:

| Prioridad | Caso | Acción Backend esperada |
|-----------|------|-------------------------|
| **P0** | UC-C04 | Unificar reactivación: `activar_cliente` debe restaurar `es_activo=1` o nuevo `PUT .../reactivar/` |
| **P0** | UC-C12 / UC-A* | Corregir tipos `cliente_id` (`UUID`) en servicios superadmin |
| **P1** | UC-C10 | API empresas bajo `/clientes/{id}/empresas` **o** documento normativo “solo vía impersonación” |
| **P1** | UC-C11 escritura | API SA mutación usuarios por `cliente_id` **o** formalizar impersonación como único camino |
| **P1** | UC-C08 test | Implementar test SQL real |
| **P1** | UC-M01 | COUNT paginación módulos |
| **P1** | UC-AU02/03 | SSO o retirar del producto / OpenAPI |
| **P1** | UC-AU01 | Alinear guard auth-config con `platform_admin` |
| **P2** | UC-D01 | BFF dashboard o especificación de agregación |
| **P2** | UC-G05 | Validar hijos al desactivar padre en ubigeo |
| **P2** | UC-P01–04 | Endpoint explícito gestión operadores Platform |

---

## 12. Qué puede asumir Frontend sin nuevo Backend

- Ensamblar dashboard (UC-D02) con llamadas paralelas documentadas.
- Drill-down auditoría y cliente con query params existentes.
- Cascada ubigeo y toggles `solo_activos`.
- Flujo “entrar como cliente” usando impersonación para empresas/usuarios.
- Copy UX que distinga suspender / desactivar / reactivar (mientras UC-C04 no se cierre).

---

## 13. Conclusión

Un Platform Admin puede completar **de principio a fin** los flujos centrales de **alta de cliente**, **edición**, **suspensión**, **branding**, **licencias por módulo**, **catálogo global**, **lectura de auditoría** y **lectura global de usuarios**. 

**No puede** completar sin fricción: **reactivar cliente eliminado** (UC-C04), **SSO/federación** (UC-AU02/03), **dashboard unificado** (UC-D01), ni **administrar empresas y usuarios tenant** desde sesión plataforma pura (UC-C10/C11) sin **impersonación** (UC-AU04).

Tras cerrar el backlog §11, la fase Frontend/UX/QA puede concentrarse en presentación y orquestación, con expectativa clara de qué caminos Backend garantiza y cuáles dependen de impersonación o quedan fuera de alcance (SSO, MRR).

---

## 14. Documentos relacionados

| Documento | Relación |
|-----------|----------|
| `PLATFORM_BACKEND_CAPABILITY_AUDIT.md` | Auditoría de capacidad y matrices previas |
| `PLATFORM_FINAL_SURFACE_AUDIT.md` | Alineación menú `/super-admin/*` vs API |
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Errores negocio visibles en clientes |
