# 06 — Riesgos para Futura Implementación Dedicated Database

**Tipo:** Auditoría técnica (estado actual)  
**Fecha:** 2026-06-25  
**Alcance:** Identificación de puntos de fricción arquitectónica  
**Restricción:** Solo riesgos. Sin propuestas de solución.

---

## 1. Resumen

El backend ya contiene **infraestructura parcial** para multi-DB (`cliente_conexion`, `database_type`, `get_connection_for_tenant`), pero la operación actual, el onboarding y la mayoría de módulos asumen **una BD compartida con filtro `cliente_id`**.

La transición a Dedicated Database enfrentará riesgos en: **fronteras de conexión**, **transacciones cross-database**, **tablas globales vs tenant**, **IAM centralizado**, y **consistencia del filtro tenant**.

---

## 2. Riesgos críticos

### R-C01 — Onboarding transaccional cross-boundary

**Ubicación:** `cliente_onboarding_service.py`

**Descripción:** Una sola transacción `session.begin()` sobre `ADMIN` inserta simultáneamente:

- Tablas centrales (`cliente`, `usuario`, `rol`, RBAC)
- Tablas ERP (`org_empresa`, `cfg_codigo_secuencia`)

**Riesgo:** En Dedicated Database, datos ERP deberían residir en BD del tenant. Una transacción SQL única **no puede abarcar** BD central + BD dedicada. El onboarding actual no tiene mecanismo de compensación multi-BD.

---

### R-C02 — ADMIN y DEFAULT apuntan a la misma BD física hoy

**Ubicación:** `connection_async.py`, `config.py`

**Descripción:** Código y operadores asumen que tablas centrales y ERP coexisten. Servicios platform usan `ADMIN`; ERP usa `DEFAULT` — ambos contra BD compartida.

**Riesgo:** Lógica que mezcla conexiones en un mismo flujo (onboarding, repair scripts, algunos servicios tenant) puede fallar silenciosamente o leer/escribir en BD incorrecta cuando las conexiones diverjan físicamente.

---

### R-C03 — Metadata `cliente_conexion` no creada en onboarding

**Ubicación:** `cliente_onboarding_service.py`, `conexion_service.py`

**Descripción:** Onboarding crea `cliente` pero **no** inserta fila en `cliente_conexion`. El routing multi-DB depende de esa metadata.

**Riesgo:** Tenant dedicated requerirá provisioning separado de metadata de conexión; ventana de inconsistencia entre cliente existente y conexión resoluble.

---

### R-C04 — Catálogo `permiso` global en BD central

**Ubicación:** `permission_sync_service.py`, `onboarding_rbac_service.py`

**Descripción:** Tabla `permiso` vive en BD central, poblada en startup. Onboarding valida que no esté vacía y asigna `rol_permiso` referenciando permisos globales.

**Riesgo:** En dedicated DB, ¿dónde vive el catálogo de permisos? Queries RBAC en tenant DB referencian `permiso_id` — acoplamiento cross-DB si permisos permanecen centralizados.

---

### R-C05 — IAM sessions en BD central

**Ubicación:** `user_session`, `token_family`, `refresh_tokens`; servicios Session V2

**Descripción:** Sesiones y tokens se persisten vía queries auth con conexión que resuelve a datos centrales. Redis complementa pero no reemplaza persistencia.

**Riesgo:** Usuario de tenant dedicated: sesiones en central vs datos operativos en dedicated — refresh/probe debe coordinar ambas resoluciones. Fallo de routing en un lado invalida sesión válida en el otro.

---

## 3. Riesgos importantes

### R-I01 — Filtro `cliente_id` omnipresente asume shared DB

**Ubicación:** `query_helpers.py`, todas las queries ERP

**Descripción:** `apply_tenant_filter` inyecta `WHERE cliente_id = :id` en tablas no globales. En dedicated DB sin columna `cliente_id` (o con valor constante), el filtro es redundante o incorrecto.

**Riesgo:** Migración de schema dedicated puede divergir del shared. Código que siempre filtra puede ocultar bugs o fallar si columna ausente.

---

### R-I02 — Tratamiento `database_type=multi` parcial e inconsistente

**Ubicación:** `user_context.py`, `rol_service.py`, `middleware.py`

**Descripción:** Algunos servicios IAM/RBAC omiten filtro `cliente_id` cuando `database_type == "multi"`. La mayoría de módulos ERP **no** tienen esta rama.

**Riesgo:** Comportamiento heterogéneo al activar dedicated — módulos migrados vs no migrados tendrán semánticas distintas de aislamiento.

---

### R-I03 — Solo 3 módulos ERP con `{cod}_deps` impersonation-safe

**Ubicación:** `org_deps.py`, `inv_deps.py`, `rbac_deps.py`

**Descripción:** Patrón `require_session_cliente_id` solo en ORG, INV, RBAC. Otros módulos pueden usar `current_user.cliente_id`.

**Riesgo:** Bajo dedicated + impersonación o superadmin cross-tenant, módulos sin deps pueden resolver tenant incorrecto para conexión DEFAULT.

---

### R-I04 — `GLOBAL_TABLES` asume ubicación de catálogos

**Ubicación:** `query_helpers.py`

**Descripción:** Lista incluye `cat_moneda`, `cat_pais`, etc. como globales sin filtro tenant. En dedicated DB, catálogos deben existir localmente o resolverse cross-DB.

**Riesgo:** Queries a catálogos en BD dedicada sin réplica local fallarán o retornarán vacío.

---

### R-I05 — Transacciones `execute_*` con commit por operación

**Ubicación:** `queries_async.py`

**Descripción:** Operaciones multi-paso sin `UnitOfWork` commitean independientemente.

**Riesgo:** Provisioning dedicated (crear BD, aplicar DDL, insertar seed, registrar metadata central) requiere atomicidad cross-sistema. Patrón actual no garantiza rollback distribuido.

---

### R-I06 — Chicken-and-egg metadata resolution

**Ubicación:** `routing.py` → `_query_connection_metadata_from_db_async`

**Descripción:** Para resolver conexión dedicated, se consulta `cliente_conexion` en BD **ADMIN**. Primera conexión a tenant dedicated depende de cache o query central.

**Riesgo:** Latencia adicional, punto único de fallo, y dependencia de disponibilidad BD central para cada request tenant dedicated.

---

### R-I07 — Escritura ERP desde servicios platform (ADMIN)

**Ubicación:** `minimal_erp_tenant_bootstrap_service.py`, onboarding

**Descripción:** `org_empresa` insertada con sesión ADMIN, no DEFAULT.

**Riesgo:** En dedicated, empresa inicial debe escribirse en BD tenant. Cambiar solo `connection_type` sin refactor de servicio escribiría en BD central.

---

### R-I08 — Cache de engines por `tenant_{client_id}`

**Ubicación:** `connection_async.py` → `_async_engines`

**Descripción:** Engines cacheados por cliente. Cambio de metadata `cliente_conexion` (migración shared → dedicated) no invalida engine cacheado automáticamente.

**Riesgo:** Tenant migrado podría seguir usando conexión shared hasta restart del worker.

---

### R-I09 — Permission cache por tenant en memoria proceso

**Ubicación:** `permission_resolver.py`

**Descripción:** Cache permisos asume catálogo central coherente. Invalidación manual dispersa.

**Riesgo:** Dedicated DB con grants locales vs central — stale cache o permisos incorrectos post-migración.

---

### R-I10 — V1/V2 session coexistence

**Ubicación:** `auth_service.py`, `session_v2_feature.py`

**Descripción:** Bifurcación de código por tenant en creación, rotación, revocación, probe.

**Riesgo:** Cutover dedicated debe considerar flag V2 por tenant y compatibilidad de tokens durante migración.

---

## 4. Riesgos menores

### R-M01 — `close_all_async_engines()` no invocado en shutdown

**Ubicación:** `main.py`

**Riesgo:** En despliegues con muchos tenants dedicated, pools no liberados limpiamente entre restarts.

---

### R-M02 — Vía pyodbc legacy (`routing.get_db_connection_for_client`)

**Ubicación:** `routing.py`

**Riesgo:** Scripts/repair podrían bypassar router async y conectar a BD incorrecta.

---

### R-M03 — `connection.py` sync deprecated con imports residuales

**Ubicación:** `auth/endpoints.py` (flujo Azure AD potencial)

**Riesgo:** Código muerto o roto si se activa flujo SSO no migrado.

---

### R-M04 — `DatabaseConnection` enum duplicado

**Ubicación:** `connection.py`, `connection_async.py`

**Riesgo:** Confusión en imports; comportamiento inconsistente si se importa versión deprecated.

---

### R-M05 — Menús legacy (`area_menu`) vs `modulo_menu`

**Ubicación:** `queries/menus/`

**Riesgo:** Dedicated provisioning debe decidir qué sistema de menú seedear.

---

### R-M06 — `request.state.cliente_id` documentado pero no poblado

**Ubicación:** `session_scope.py`, `middleware.py`

**Riesgo:** Hook legacy podría activarse incorrectamente si se implementa sin alinear con ContextVar.

---

### R-M07 — Errores RBAC MANAGER/USER tragados en onboarding

**Ubicación:** `onboarding_rbac_service.py`

**Riesgo:** Tenant dedicated provisionado con RBAC incompleto sin señal de fallo.

---

### R-M08 — `ENABLE_UNIT_OF_WORK` sin enforcement

**Ubicación:** `config.py`, `unit_of_work.py`

**Riesgo:** Nuevos flujos provisioning podrían omitir UoW sin flag que lo impida.

---

## 5. Riesgos por categoría (matriz)

| Categoría | IDs | Cantidad |
|-----------|-----|----------|
| Frontera conexión / routing | R-C02, R-C03, R-I06, R-I08, R-M02 | 5 |
| Transacciones / atomicidad | R-C01, R-I05, R-I07 | 3 |
| IAM / sesiones | R-C05, R-I10 | 2 |
| RBAC / permisos | R-C04, R-I02, R-I09 | 3 |
| Aislamiento tenant / filtros | R-I01, R-I03, R-I04 | 3 |
| Infraestructura / ops | R-M01, R-M03, R-M04, R-M07, R-M08 | 5 |
| Datos / schema | R-M05, R-M06 | 2 |

---

## 6. Dependencias externas al routing de conexión

Elementos que **no** resuelven conexión dinámica pero acoplan tenants:

| Elemento | Acoplamiento |
|----------|--------------|
| Redis session keys | Incluyen `cliente_id` / `session_id` — independiente de BD |
| TenantMiddleware | Siempre consulta `cliente` en ADMIN por subdominio |
| JWT claims | `cliente_id` embebido — no indica tipo de BD |
| Subdominio DNS | Un subdominio → un tenant → una resolución de conexión |
| Bootstrap DDL V010 | Schema ERP completo debe existir en cada BD dedicated |
| `permission_sync` startup | Central — no per-tenant DB |

---

## 7. Preguntas abiertas (para etapa de diseño)

Estas preguntas **no tienen respuesta** en el código actual y deben resolverse antes de implementar:

1. ¿Qué tablas permanecen exclusivamente en BD central vs se replican en dedicated?
2. ¿El catálogo `permiso` se replica por tenant o se resuelve cross-DB en runtime?
3. ¿Las sesiones IAM permanecen centralizadas para todos los modelos?
4. ¿Dedicated DB conserva columna `cliente_id` en tablas ERP o se elimina?
5. ¿Cómo se provisiona DDL (V010) en BD dedicated — pipeline separado o parte de onboarding?
6. ¿Migración shared → dedicated es online o requiere downtime por tenant?
7. ¿`cliente_conexion` se crea automáticamente en onboarding dedicated o manualmente?
8. ¿Superadmin e impersonación operan siempre contra central + dedicated del target?
9. ¿Catálogos `cat_*` se seedean por dedicated o se consultan desde central?
10. ¿Invalidación de engine cache forma parte del contrato de cambio de `database_type`?

---

## 8. Inventario de código con hooks multi-DB existentes

Referencias encontradas (preparación parcial, no completitud):

| Archivo | Hook |
|---------|------|
| `core/tenant/routing.py` | `get_connection_for_tenant`, `database_type` |
| `core/tenant/middleware.py` | Carga metadata, setea `TenantContext.database_type` |
| `core/tenant/context.py` | `is_multi_db()` |
| `core/auth/user_context.py` | Rama `database_type == "multi"` |
| `modules/rbac/application/services/rol_service.py` | Rama `database_type == "multi"` |
| `infrastructure/database/connection_async.py` | `connection_metadata` param |
| `modules/tenant/application/services/conexion_service.py` | CRUD `cliente_conexion` |

**Ausente:** ramas multi-DB en módulos ERP (INV, PUR, SLS, etc.), onboarding, majority of queries.

---

## 9. Conclusión de auditoría de riesgos

La base de código **no está lista** para Dedicated Database sin trabajo significativo, aunque **no parten de cero**: el router de conexión y la tabla `cliente_conexion` existen.

Los riesgos **críticos** se concentran en:

1. Transaccionalidad onboarding (central + ERP en una TX)
2. Ubicación de IAM y RBAC global
3. Ausencia de provisioning `cliente_conexion` en flujo estándar
4. Inconsistencia del tratamiento `database_type=multi`

Esta auditoría documenta el estado AS-IS. Las decisiones de diseño y mitigación corresponden a la etapa siguiente, tras revisión y aprobación de estos documentos.
