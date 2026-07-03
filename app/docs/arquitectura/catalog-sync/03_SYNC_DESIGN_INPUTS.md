# 03 — Inputs de Diseño para Sincronización Manual Platform → Dedicated

**Fecha:** 2026-07-02  
**Modo:** Solo auditoría — **sin algoritmo, sin pseudocódigo, sin implementación**  
**Objetivo:** Delimitar restricciones, dependencias y estructura arquitectónica mínima para Fase 2

---

## 1. Restricciones innegociables (ticket)

| Restricción | Implicación arquitectónica |
|-------------|---------------------------|
| Sincronización **siempre manual** | Endpoint o acción explícita Platform Admin; sin lifespan, sin scheduler, sin colas |
| Origen: **BD Platform** | Lector debe apuntar al store SSOT Product Reference (BD ERP shared con datos maestros) |
| Destino: **clientes Dedicated** | Escritor debe usar sesión dedicated (`provisioning_dedicated_session` o equivalente) |
| Alcance: **solo 5 tablas** `cat_*` | Fuera de scope: `permiso`, `modulo`, menús, seeds S010–S066 |
| Sin replicación SQL Server | Sync aplicación — INSERT/UPDATE vía código |
| Sin modificar DDL | UPSERT sobre esquema V010 existente |

---

## 2. Precedente arquitectónico interno

El patrón **Permission Catalog Sync** (F12-B / ADR-011) es la referencia más cercana:

| Capa | Permission sync (existente) | Product Reference sync (futuro) |
|------|----------------------------|--------------------------------|
| **Core** | `app/core/authorization/permission_catalog_sync_core.py` | `app/core/catalog/` (propuesto — ver §4) |
| **Tipos** | `permission_catalog_sync_types.py` | `product_reference_catalog_sync_types.py` |
| **Infra dedicated executor** | `dedicated_permission_catalog_sync_service.py` | `dedicated_product_reference_catalog_sync_service.py` |
| **Orquestación manual** | Solo en provisioning S6 (flag) | **Manual Platform Admin** (nuevo) |
| **Fuente datos** | `PermissionRegistry` (código) | Tablas `cat_*` (BD Platform) |
| **Idempotencia marker** | `bootstrap_applied` (`permission_catalog_sync`) | Por definir — recomendado tabla/log de sync manual |

**Diferencia clave:** Permission sync es code-first y automático en provisioning; Product Reference sync es **data-first** y **manual**.

---

## 3. Origen y destino de datos

### 3.1 Origen (Platform SSOT)

| Atributo | Valor auditado |
|----------|----------------|
| Store físico | BD ERP shared (`V010`) — misma que resuelve `execute_query` para tenants shared |
| Tablas | `cat_moneda`, `cat_pais`, `cat_departamento`, `cat_provincia`, `cat_distrito` |
| Acceso actual | `CatalogosGlobalesService` con `client_id` → DEFAULT shared |
| Contenido | Mantenido por Superadmin; sin seed SQL automático |
| Filtro tenant | Ninguno (`GLOBAL_TABLES`) |

**Decisión pendiente Fase 2:** Definir `platform_reference_cliente_id` fijo (ej. tenant SYSTEM) vs conexión explícita shared sin impersonation. Hoy el SSOT efectivo es el contenido de `cat_*` en la BD ERP compartida.

### 3.2 Destino (Dedicated Data Plane)

| Atributo | Valor auditado |
|----------|----------------|
| Store físico | BD dedicada del tenant (`cliente_conexion.database_name`) |
| Esquema | V010 idéntico — tablas ya creadas en S4 |
| Estado inicial | 0 filas (verificado S6) |
| Sesión | Patrón `provisioning_dedicated_session(database_name)` — credenciales DDL provisioning |
| Metadata routing | `cliente_conexion` en Control Plane |

---

## 4. Ubicación propuesta de `CatalogSyncService`

### 4.1 Estructura de capas (propuesta)

```
app/core/catalog/
  product_reference_catalog_sync_types.py    # SyncMode, SyncResult, CatalogTable, Executor Protocol
  product_reference_catalog_sync_core.py     # Orquestación pura (sin SQL directo)
  product_reference_catalog_definitions.py   # Orden FK, columnas compare, nombres tablas

app/infrastructure/provisioning/
  dedicated_product_reference_catalog_sync_service.py   # Executor dedicated (SQL)
  platform_product_reference_catalog_reader.py          # Executor platform (lectura SSOT)

app/modules/superadmin/application/services/
  catalog_sync_orchestrator_service.py       # Caso de uso manual: validar tenant, invocar core, persistir log

app/modules/superadmin/presentation/
  endpoints_catalog_sync.py                  # Endpoints manuales (Fase 2)
  schemas_catalog_sync.py                    # Request/Response diff preview, resultado sync
```

### 4.2 Justificación por capa

| Ubicación | Razón |
|-----------|-------|
| **`app/core/catalog/`** | Lógica de dominio Product Reference independiente de HTTP y de SQL Server; paralelo a `core/authorization/` |
| **`app/infrastructure/provisioning/`** | Acceso a BD dedicated con credenciales provisioning ya establecidas; coherente con `DedicatedPermissionCatalogSyncService` |
| **`app/modules/superadmin/`** | Único consumidor autorizado — sync manual iniciada desde Platform Admin (ADR-011 post-MVP) |
| **No en `app/modules/catalogos/`** | Ese módulo es lectura tenant ERP; mezclar sync Platform contaminaría frontera CP/DP |

### 4.3 Nombre del servicio

| Opción | Recomendación |
|--------|---------------|
| `CatalogSyncService` | Genérico — aceptable si documentado como Product Reference only |
| `ProductReferenceCatalogSyncService` | **Preferido** — alinea terminología ADR-011 / canonical data model |
| `DedicatedCatalogSyncService` | Ambiguo — colisiona semánticamente con `DedicatedCatalogSeedService` (S6 RBAC) |

---

## 5. Router propuesto para endpoints futuros

### 5.1 Opción recomendada

| Atributo | Valor |
|----------|-------|
| Archivo | `app/modules/superadmin/presentation/endpoints_catalog_sync.py` |
| Prefix | `/catalogos-globales/sync` |
| Montaje en `api.py` | Bajo mismo tag o sub-tag `Catálogos Globales (Super Admin)` |
| Autorización | `@require_super_admin()` |

**Razón:** Agrupa operaciones de administración de catálogos Product Reference sin mezclar con CRUD de filas individuales. El prefijo padre `/catalogos-globales` ya existe y está en menú Platform (`S020__seed_admin_menu.sql`).

### 5.2 Alternativas descartadas

| Router | Motivo descarte |
|--------|-----------------|
| `/catalogos/*` (módulo tenant) | Sync es operación Platform → Dedicated, no consumo ERP tenant |
| `/clientes/{id}/provisioning/*` | Sync no es step de saga automática — es operación manual post-provisioning |
| `/superadmin/auditoria/*` | Auditoría es lectura de logs; sync es mutación controlada |

### 5.3 Operaciones endpoint (solo estructura — Fase 2)

| Operación conceptual | Propósito |
|---------------------|-----------|
| Preview / diff | Comparar Platform vs dedicated sin escribir |
| Execute sync | Aplicar UPSERT manual para un `cliente_id` dedicated |
| Status / last sync | Última ejecución, conteos, hash de catálogo |

---

## 6. Orden de sincronización obligatorio

Por FK intra-catálogo (ver `01_CATALOG_INVENTORY.md` §4):

1. `cat_moneda` (paralelo con paso 2)
2. `cat_pais`
3. `cat_departamento`
4. `cat_provincia`
5. `cat_distrito`

Cada nivel debe completarse antes del siguiente para evitar violaciones `FK_*`.

---

## 7. Semántica de operaciones (inputs, no algoritmo)

| Operación | Semántica esperada | Evidencia en CRUD actual |
|-----------|-------------------|--------------------------|
| **Insert** | Preservar PK Platform (`*_id`) | `create_*` genera `uuid4()` local — sync debe **sobrescribir** este comportamiento |
| **Update** | Actualizar columnas funcionales si diff | Campos mutables en `Cat*Update` schemas |
| **Deactivate** | `es_activo = 0` si registro Platform inactivo | Patrón uniforme en los 5 catálogos |
| **Delete físico** | **Prohibido** | Alineado a reglas ERP y servicios actuales |

**Registros en dedicated no presentes en Platform:** Decisión Fase 2 — ADR-011 implica réplica read-only desde Platform; candidato: desactivar (`es_activo=0`) o reportar en diff sin mutar.

---

## 8. Columnas de comparación (resumen)

Ver detalle en `01_CATALOG_INVENTORY.md` §7. Hash de catálogo futuro debería construirse solo con columnas **Comparar** ordenadas determinísticamente por PK.

---

## 9. Conexiones y resolutores requeridos

| Plano | Resolución | Componente existente |
|-------|------------|---------------------|
| Lectura Platform | DEFAULT shared (tenant reference) o intent explícito | `execute_query` + `client_id` shared |
| Escritura Dedicated | Sesión por `database_name` | `provisioning_dedicated_session` |
| Metadata dedicated | `cliente_conexion` | `ConexionService` / routing |
| Validación perfil | Solo `tipo_instalacion = dedicated` | `get_installation_profile` |

**No reutilizar** `CatalogosGlobalesService` directamente para sync dedicated — mezcla semántica CRUD tenant con escritura cross-plane.

---

## 10. Observabilidad y trazabilidad (inputs)

| Necesidad | Estado actual | Input Fase 2 |
|-----------|---------------|--------------|
| Log de sync manual | No existe para `cat_*` | Tabla CP o extensión de `log_sincronizacion_*` — evaluar |
| Marker idempotencia | `bootstrap_applied` usado en permisos | Nuevo `script_code` por sync manual |
| Auditoría Superadmin | `endpoints_auditoria.py` | Exponer resultado sync en API status |

---

## 11. Dependencias externas al sync

| Dependencia | Impacto |
|-------------|---------|
| FK ERP → `cat_*` en dedicated | Tras sync, `org_empresa.moneda_id`, direcciones, etc. deben referenciar UUIDs Platform |
| Onboarding sin datos cat_* | Primera sync manual obligatoria antes de operar módulos que resuelven `moneda_id` / ubigeo |
| Tenant shared | **Fuera de alcance** — ya comparten SSOT físico en BD shared |
