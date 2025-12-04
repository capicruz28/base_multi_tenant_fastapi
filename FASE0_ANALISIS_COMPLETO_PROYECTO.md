# 🔍 FASE 0 — ANÁLISIS COMPLETO DEL PROYECTO

**Fecha:** 2024  
**Objetivo:** Análisis exhaustivo del código antes de cualquier modificación  
**Estado:** ✅ COMPLETADO

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Archivos Críticos](#archivos-críticos)
4. [Dependencias entre Módulos](#dependencias-entre-módulos)
5. [Uso de Raw SQL](#uso-de-raw-sql)
6. [Uso de pyodbc](#uso-de-pyodbc)
7. [Manejo de Tenant](#manejo-de-tenant)
8. [Manejo de Tokens](#manejo-de-tokens)
9. [Carga de Usuarios en deps.py](#carga-de-usuarios-en-depspy)
10. [Construcción de Conexiones](#construcción-de-conexiones)
11. [Conclusiones y Recomendaciones](#conclusiones-y-recomendaciones)

---

## 📊 RESUMEN EJECUTIVO

### Arquitectura General
- **Framework:** FastAPI (Python)
- **Base de Datos:** SQL Server (Multi-tenant híbrido: Single-DB + Multi-DB)
- **Driver:** pyodbc (síncrono) + aioodbc (async, parcialmente implementado)
- **Autenticación:** JWT (Access + Refresh tokens)
- **Arquitectura:** Multi-tenant híbrido con soporte para:
  - **Single-DB:** Todos los clientes en `bd_sistema` (aislamiento por `cliente_id`)
  - **Multi-DB:** Cada cliente en su propia BD (`bd_cliente_acme`, etc.)

### Estado Actual
- ✅ Sistema funcional con multi-tenancy implementado
- ⚠️ Mezcla de código síncrono (pyodbc) y async (aioodbc)
- ⚠️ Uso extensivo de raw SQL strings
- ⚠️ Validación de tenant basada en análisis de strings SQL (frágil)
- ⚠️ `deps.py` con lógica compleja y acoplamiento alto
- ⚠️ Primary keys como INT IDENTITY (no escalable para sincronización)

---

## 🏗️ ESTRUCTURA DEL PROYECTO

### Organización por Capas

```
app/
├── api/                    # Capa de presentación (endpoints FastAPI)
│   ├── deps.py            # ⚠️ CRÍTICO: Dependencias con lógica compleja
│   └── v1/
│       └── api.py         # Router principal
│
├── core/                   # Núcleo del sistema
│   ├── config.py          # Configuración (Settings)
│   ├── auth.py            # Utilidades de autenticación
│   ├── exceptions.py      # Excepciones personalizadas
│   ├── tenant/             # ⚠️ CRÍTICO: Lógica multi-tenant
│   │   ├── context.py     # ContextVar para tenant actual
│   │   ├── middleware.py  # TenantMiddleware (resuelve cliente por subdominio)
│   │   ├── routing.py     # Routing de conexiones (Single-DB vs Multi-DB)
│   │   └── cache.py      # Cache de metadata de conexión
│   ├── security/          # Seguridad
│   │   ├── jwt.py         # Creación/validación de tokens JWT
│   │   ├── password.py    # Hashing de contraseñas
│   │   ├── encryption.py  # Encriptación de credenciales
│   │   └── rate_limiting.py
│   └── authorization/     # RBAC + LBAC
│       ├── rbac.py
│       └── lbac.py
│
├── infrastructure/         # Infraestructura
│   ├── database/
│   │   ├── connection.py          # ⚠️ CRÍTICO: Conexiones síncronas (pyodbc)
│   │   ├── connection_async.py    # Conexiones async (aioodbc) - PARCIAL
│   │   ├── connection_pool.py     # Pool de conexiones
│   │   ├── queries.py              # ⚠️ CRÍTICO: Raw SQL strings + execute_query
│   │   ├── queries_async.py       # Queries async - PARCIAL
│   │   └── repositories/
│   │       └── base_repository.py   # BaseRepository (usa execute_query)
│   └── cache/
│       └── redis_cache.py          # Cache Redis (opcional)
│
└── modules/                # Módulos de dominio (DDD)
    ├── auth/              # Autenticación
    ├── users/             # Gestión de usuarios
    ├── rbac/              # Roles y permisos
    ├── menus/             # Menús del sistema
    ├── tenant/            # Gestión de clientes/tenants
    └── superadmin/        # Funciones de superadmin
```

---

## 🔴 ARCHIVOS CRÍTICOS

### 1. **`app/api/deps.py`** ⚠️ CRÍTICO
**Problema:** Lógica compleja, acoplamiento alto, múltiples queries

**Funciones principales:**
- `get_current_user_data()`: Decodifica JWT, retorna payload
- `get_current_active_user()`: Obtiene usuario completo + roles + niveles
  - **Query optimizada:** `get_user_complete_data_query()` (1 query con JSON)
  - **Validación de tenant:** Compara `token_cliente_id` vs `request_cliente_id`
  - **Parseo de roles:** Convierte JSON a `List[RolRead]`
- `get_user_access_level()`: Obtiene nivel máximo del usuario
- `check_is_super_admin()`: Verifica si es superadmin
- `RoleChecker`: Verifica permisos basado en LBAC

**Líneas críticas:**
- Línea 199-202: Query optimizada con 5 parámetros (cliente_id repetido)
- Línea 212-286: Validación de aislamiento multi-tenant
- Línea 317-443: Parseo complejo de roles desde JSON

**Dependencias:**
- `execute_auth_query()` (raw SQL)
- `get_user_complete_data_query()` (raw SQL con JSON/XML)
- `UsuarioService`, `RolService` (servicios de módulos)

---

### 2. **`app/infrastructure/database/queries.py`** ⚠️ CRÍTICO
**Problema:** Más de 1500 líneas de raw SQL strings

**Funciones principales:**
- `execute_query()`: Ejecuta raw SQL, valida tenant por análisis de string
  - **Validación frágil:** Busca `"cliente_id = ?"` en query_lower
  - **Línea 59-158:** Validación compleja con regex/heurísticas
- `execute_auth_query()`: Query para autenticación (retorna 1 registro)
- `execute_insert()`, `execute_update()`, `execute_procedure()`

**Queries hardcodeadas (ejemplos):**
- `GET_USER_COMPLETE_OPTIMIZED_JSON` (línea 588): Query compleja con FOR JSON PATH
- `GET_USER_COMPLETE_OPTIMIZED_XML` (línea 656): Fallback para SQL Server antiguo
- `SELECT_USUARIOS_PAGINATED` (línea 843): Paginación con CTE
- `SELECT_ROL_BY_ID` (línea 951): Query con filtro multi-tenant
- Más de 50 queries adicionales para todas las tablas

**Validación de tenant (línea 53-158):**
```python
# ⚠️ FRÁGIL: Análisis de string SQL
query_lower = query.lower().strip()
has_cliente_id_filter = (
    " cliente_id = ?" in query_lower or
    " cliente_id=?" in query_lower or
    # ... más patrones
)
```

---

### 3. **`app/infrastructure/database/connection.py`** ⚠️ CRÍTICO
**Problema:** Código síncrono con pyodbc

**Funciones principales:**
- `get_db_connection()`: Context manager síncrono (pyodbc)
  - **Línea 57-168:** Maneja pooling opcional + conexión directa
  - **Línea 129-140:** Usa `get_db_connection_for_current_tenant()` (routing)
- `get_connection_string()`: Construye connection string (DEPRECADO)

**Dependencias:**
- `pyodbc` (síncrono, bloquea event loop)
- `app.core.tenant.routing.get_db_connection_for_current_tenant()`
- `app.core.tenant.context.get_current_client_id()`

---

### 4. **`app/infrastructure/database/connection_async.py`** ⚠️ PARCIAL
**Estado:** Implementado pero NO usado en producción

**Funciones principales:**
- `get_db_connection_async()`: Context manager async (aioodbc)
  - **Línea 180-239:** Usa SQLAlchemy AsyncEngine
  - **Flag:** `ENABLE_ASYNC_CONNECTIONS=false` (desactivado por defecto)

**Problema:** Coexiste con `connection.py` pero no se usa

---

### 5. **`app/core/tenant/routing.py`** ⚠️ CRÍTICO
**Problema:** Lógica de routing de conexiones (Single-DB vs Multi-DB)

**Funciones principales:**
- `get_connection_metadata()`: Obtiene metadata de conexión (con cache)
  - **Línea 190-300:** Consulta `cliente_conexion` + cache Redis/memoria
- `get_client_db_connection_string()`: Construye connection string según tipo
  - **Línea 373-433:** Routing: Single-DB → `bd_sistema`, Multi-DB → BD dedicada
- `get_db_connection_for_current_tenant()`: Obtiene conexión pyodbc para tenant actual
  - **Línea 490-521:** Usa contexto de tenant

**Dependencias:**
- `pyodbc` (síncrono)
- `app.core.tenant.context.get_current_client_id()`
- `app.core.security.encryption.decrypt_credential()`

---

### 6. **`app/core/tenant/middleware.py`** ⚠️ CRÍTICO
**Problema:** Middleware que resuelve tenant por subdominio

**Flujo:**
1. Extrae host del request (con fallback a origin/referer en desarrollo)
2. Extrae subdominio (`acme` de `acme.midominio.com`)
3. Consulta BD para obtener `cliente_id` por subdominio
4. Carga metadata de conexión (`cliente_conexion`)
5. Establece `TenantContext` en ContextVar
6. Procesa request
7. Limpia contexto

**Líneas críticas:**
- Línea 63-214: `_get_host_from_request()` (extracción de host con fallback)
- Línea 216-395: `dispatch()` (flujo principal)
- Línea 456-498: `_get_client_data_by_subdomain()` (consulta BD con conexión ADMIN)

---

### 7. **`app/infrastructure/database/repositories/base_repository.py`** ⚠️ IMPORTANTE
**Problema:** BaseRepository usa `execute_query()` (raw SQL)

**Métodos principales:**
- `find_by_id()`, `find_all()`, `create()`, `update()`, `delete()`
- `_build_tenant_filter()`: Construye filtro `cliente_id = ?` (línea 84-149)

**Dependencias:**
- `execute_query()` (raw SQL)
- `get_current_client_id()` (contexto)

---

## 🔗 DEPENDENCIAS ENTRE MÓDULOS

### Flujo de Request (Simplificado)

```
Request → TenantMiddleware → deps.py → Endpoint → Service → Repository → execute_query()
```

### Dependencias Críticas

1. **TenantMiddleware → routing.py**
   - Middleware consulta `cliente_conexion` para obtener metadata
   - Usa conexión ADMIN (evita recursión)

2. **deps.py → queries.py**
   - `get_current_active_user()` llama `execute_auth_query()`
   - Usa query optimizada `get_user_complete_data_query()`

3. **Repositories → queries.py**
   - Todos los repositorios usan `execute_query()` (raw SQL)
   - `BaseRepository._build_tenant_filter()` agrega `cliente_id = ?`

4. **Services → Repositories**
   - Services llaman a repositorios (no ejecutan SQL directamente)
   - Ejemplo: `UsuarioService` → `UserRepository`

5. **Endpoints → Services**
   - Endpoints llaman a services (no acceden a BD directamente)
   - Ejemplo: `POST /auth/login/` → `AuthService`

### Ciclos de Dependencia

**⚠️ PROBLEMA:** `connection.py` → `routing.py` → `context.py` → `middleware.py` → `connection.py`

**Solución actual:** `routing.py` usa conexión ADMIN directa (pyodbc) para evitar recursión

---

## 📝 USO DE RAW SQL

### Ubicaciones Principales

#### 1. **`app/infrastructure/database/queries.py`**
- **Más de 50 queries hardcodeadas** como strings
- Ejemplos:
  - `GET_USER_COMPLETE_OPTIMIZED_JSON` (línea 588)
  - `SELECT_USUARIOS_PAGINATED` (línea 843)
  - `SELECT_ROL_BY_ID` (línea 951)
  - `INSERT_USUARIO` (línea 917)
  - `UPDATE_ROL` (línea 970)
  - Y muchas más...

#### 2. **`app/infrastructure/database/repositories/base_repository.py`**
- Construye queries dinámicamente:
  ```python
  query = f"SELECT * FROM {self.table_name} WHERE {self.id_column} = ? {tenant_filter}"
  ```

#### 3. **Repositorios Específicos**
- `app/modules/users/infrastructure/repositories/user_repository.py`:
  - Línea 100-128: Query para roles
  - Línea 132-150: Query para permisos
- `app/modules/rbac/infrastructure/repositories/rol_repository.py`:
  - Línea 97-118: Query para permisos del rol

#### 4. **Services (Algunos)**
- `app/modules/auth/application/services/auth_service.py`:
  - Usa `execute_auth_query()` (raw SQL)

### Patrones Comunes

1. **Queries con parámetros:**
   ```python
   query = "SELECT * FROM usuario WHERE nombre_usuario = ? AND cliente_id = ?"
   params = (username, client_id)
   ```

2. **Queries con filtro de tenant:**
   ```python
   tenant_filter, tenant_params = self._build_tenant_filter(client_id)
   query = f"SELECT * FROM {table} WHERE ... {tenant_filter}"
   ```

3. **Queries complejas (CTE, JSON, XML):**
   ```sql
   WITH UserRoles AS (...)
   SELECT ... FOR JSON PATH
   ```

---

## 🔌 USO DE pyodbc

### Ubicaciones

#### 1. **`app/infrastructure/database/connection.py`**
- **Línea 2:** `import pyodbc`
- **Línea 139:** `conn = pyodbc.connect(conn_str, timeout=30)`
- **Línea 57-168:** `get_db_connection()` (context manager síncrono)

#### 2. **`app/core/tenant/routing.py`**
- **Línea 24:** `import pyodbc`
- **Línea 108:** `conn = pyodbc.connect(admin_conn_str)`
- **Línea 462:** `conn = pyodbc.connect(conn_str, timeout=30)`

#### 3. **`app/infrastructure/database/queries.py`**
- **Línea 7:** `import pyodbc`
- **Línea 348:** Manejo de `pyodbc.IntegrityError`

#### 4. **`app/core/tenant/middleware.py`**
- Usa `get_db_connection(DatabaseConnection.ADMIN)` (que usa pyodbc)

### Problemas

1. **Bloqueo del Event Loop:**
   - `pyodbc.connect()` es síncrono
   - Bloquea el event loop de FastAPI (async)
   - Reduce concurrencia

2. **Mezcla con Async:**
   - Existe `connection_async.py` (aioodbc) pero NO se usa
   - Flag `ENABLE_ASYNC_CONNECTIONS=false` (desactivado)

---

## 🏢 MANEJO DE TENANT

### Arquitectura Híbrida

El sistema soporta dos modos:

1. **Single-DB:** Todos los clientes en `bd_sistema` (aislamiento por `cliente_id`)
2. **Multi-DB:** Cada cliente en su propia BD (`bd_cliente_acme`, etc.)

### Componentes Clave

#### 1. **TenantContext** (`app/core/tenant/context.py`)
- **ContextVar:** `current_client_id`, `current_tenant_context`
- **TenantContext (dataclass):**
  - `client_id`, `subdominio`, `codigo_cliente`
  - `database_type` ("single" o "multi")
  - `nombre_bd`, `servidor`, `puerto`
  - `connection_metadata`

#### 2. **TenantMiddleware** (`app/core/tenant/middleware.py`)
- Resuelve `cliente_id` por subdominio
- Establece `TenantContext` en ContextVar
- Carga metadata de conexión

#### 3. **Routing de Conexiones** (`app/core/tenant/routing.py`)
- `get_connection_metadata()`: Consulta `cliente_conexion` (con cache)
- `get_client_db_connection_string()`: Construye connection string según tipo
- `get_db_connection_for_current_tenant()`: Obtiene conexión pyodbc

#### 4. **Validación de Tenant**
- **En `queries.py`:** Análisis de string SQL (frágil)
- **En `base_repository.py`:** `_build_tenant_filter()` (programático)

### Flujo Completo

```
1. Request → TenantMiddleware
2. Extrae subdominio del Host header
3. Consulta BD (conexión ADMIN) para obtener cliente_id
4. Carga metadata de conexión (cliente_conexion)
5. Establece TenantContext en ContextVar
6. get_db_connection() → get_db_connection_for_current_tenant()
7. get_client_db_connection_string() → Construye connection string
8. pyodbc.connect(conn_str) → Conexión a BD correcta
9. execute_query() → Valida tenant (análisis de string SQL)
10. BaseRepository._build_tenant_filter() → Agrega cliente_id = ?
```

---

## 🔐 MANEJO DE TOKENS

### Tipos de Tokens

1. **Access Token:**
   - Duración: 15 minutos (configurable)
   - Algoritmo: HS256
   - Secret: `SECRET_KEY`
   - Payload: `sub`, `cliente_id`, `access_level`, `is_super_admin`, `user_type`

2. **Refresh Token:**
   - Duración: 7 días (configurable)
   - Algoritmo: HS256
   - Secret: `REFRESH_SECRET_KEY` (separada)
   - Almacenado en BD: `refresh_tokens` (hasheado con SHA-256)

### Flujo de Autenticación

#### Login (`app/modules/auth/presentation/endpoints.py`)
1. Usuario envía credenciales (`username`, `password`)
2. `AuthService.authenticate_user()` valida credenciales
3. Obtiene niveles de acceso (`get_user_access_level_info()`)
4. Crea tokens:
   - `create_access_token()` (línea 204)
   - `create_refresh_token()` (línea 205)
5. Almacena refresh token en BD (`RefreshTokenService.store_refresh_token()`)
6. Retorna tokens según tipo de cliente:
   - **Web:** Access token en JSON, Refresh token en cookie HttpOnly
   - **Móvil:** Ambos tokens en JSON

#### Validación en `deps.py`
1. `get_current_user_data()`: Decodifica JWT, retorna payload
2. `get_current_active_user()`: Obtiene usuario completo desde BD
   - Query optimizada: `get_user_complete_data_query()` (1 query con JSON)
   - Validación de tenant: Compara `token_cliente_id` vs `request_cliente_id`
   - Parseo de roles: Convierte JSON a `List[RolRead]`

### Archivos Clave

- **`app/core/security/jwt.py`:** Creación/decodificación de tokens
- **`app/modules/auth/application/services/refresh_token_service.py`:** Gestión de refresh tokens
- **`app/api/deps.py`:** Validación de tokens en cada request

---

## 👤 CARGA DE USUARIOS EN deps.py

### Función Principal: `get_current_active_user()`

**Ubicación:** `app/api/deps.py`, línea 149-496

**Flujo:**

1. **Decodifica JWT** (`get_current_user_data()`)
   - Extrae `username` del payload

2. **Query optimizada** (línea 198-202):
   ```python
   optimized_query = get_user_complete_data_query()
   user_dict = execute_auth_query(
       optimized_query, 
       (context_cliente_id, context_cliente_id, context_cliente_id, username, context_cliente_id)
   )
   ```
   - **1 query** obtiene: usuario + roles (JSON) + niveles
   - Compatible con SQL Server 2005+ (detecta versión automáticamente)

3. **Validación de tenant** (línea 212-286):
   - Compara `token_cliente_id` vs `request_cliente_id`
   - SuperAdmin puede acceder a cualquier tenant
   - Usuario regular DEBE coincidir tenant

4. **Parseo de roles** (línea 317-443):
   - Parsea JSON string a `List[Dict]`
   - Convierte a `List[RolRead]` (Pydantic)
   - Maneja errores de parseo (continúa sin ese rol)

5. **Construcción de objeto Pydantic** (línea 470-475):
   ```python
   usuario_pydantic = UsuarioReadWithRoles(**user_dict, roles=roles_list)
   ```

### Problemas Identificados

1. **Lógica compleja:** Más de 300 líneas en una función
2. **Acoplamiento alto:** Llama a `UsuarioService`, `RolService`, `AuditService`
3. **Múltiples responsabilidades:**
   - Validación de token
   - Query a BD
   - Validación de tenant
   - Parseo de roles
   - Construcción de objeto Pydantic

---

## 🔧 CONSTRUCCIÓN DE CONEXIONES

### Flujo Completo

```
1. TenantMiddleware establece TenantContext
2. get_db_connection() (connection.py)
   ↓
3. get_db_connection_for_current_tenant() (routing.py)
   ↓
4. get_client_db_connection_string() (routing.py)
   ↓
5. get_connection_metadata() (routing.py)
   - Consulta cliente_conexion (con cache Redis/memoria)
   - Determina database_type (single/multi)
   ↓
6. _build_single_db_connection_string() o _build_multi_db_connection_string()
   ↓
7. pyodbc.connect(conn_str)
```

### Archivos Clave

#### 1. **`app/infrastructure/database/connection.py`**
- `get_db_connection()`: Context manager síncrono
  - Soporta pooling opcional
  - Usa `get_db_connection_for_current_tenant()` para routing

#### 2. **`app/core/tenant/routing.py`**
- `get_connection_metadata()`: Obtiene metadata (con cache)
- `get_client_db_connection_string()`: Construye connection string
- `get_db_connection_for_current_tenant()`: Obtiene conexión pyodbc

#### 3. **`app/infrastructure/database/connection_async.py`**
- `get_db_connection_async()`: Context manager async (NO usado)
- Usa SQLAlchemy AsyncEngine + aioodbc

### Tipos de Conexión

1. **DEFAULT:** Conexión tenant-aware (routing automático)
2. **ADMIN:** Conexión fija a BD de administración (para metadata)

### Cache de Metadata

- **Redis:** Cache distribuido (si `ENABLE_REDIS_CACHE=true`)
- **Memoria:** Cache local (fallback)
- **TTL:** 10 minutos (600 segundos)

---

## ✅ CONCLUSIONES Y RECOMENDACIONES

### Problemas Críticos Identificados

1. **Raw SQL en todas partes:**
   - Más de 50 queries hardcodeadas
   - Construcción dinámica de queries (SQL injection risk si no se valida)
   - Sin tipado de queries

2. **Validación de tenant frágil:**
   - Análisis de string SQL (regex/heurísticas)
   - Fácil de bypassear si se olvida agregar `cliente_id = ?`

3. **Mezcla síncrono/async:**
   - `connection.py` (pyodbc) usado en producción
   - `connection_async.py` (aioodbc) implementado pero NO usado
   - Bloqueo del event loop

4. **deps.py sobrecargado:**
   - Más de 300 líneas en `get_current_active_user()`
   - Múltiples responsabilidades
   - Acoplamiento alto con servicios

5. **Primary keys INT IDENTITY:**
   - No escalable para sincronización on-premise ↔ nube
   - Conflictos posibles en merge

### Recomendaciones para Refactorización

#### FASE 1: Acceso a Datos
- ✅ Crear `app/infrastructure/database/tables.py` con SQLAlchemy Core Table definitions
- ✅ Reemplazar `execute_query()` por queries construidas con SQLAlchemy Core
- ✅ Función `apply_tenant_filter()` programática (no análisis de string)
- ✅ Eliminar validación de SQL por texto

#### FASE 2: Conexiones Async
- ✅ Eliminar `connection.py` (síncrono)
- ✅ Unificar en `connection_async.py` (100% async)
- ✅ Reemplazar `pyodbc` por `aioodbc` en todo el código

#### FASE 3: UUID Primary Keys
- ✅ Script SQL para convertir INT → UNIQUEIDENTIFIER
- ✅ Actualizar Foreign Keys
- ✅ Actualizar schemas Pydantic

#### FASE 4: Simplificar deps.py
- ✅ Extraer lógica pesada a servicios
- ✅ Función única: `get_user_auth_context(token, db_connection)`
- ✅ Retornar objeto simple: `CurrentUserContext`

#### FASE 5: Tenant Router
- ✅ Crear `app/core/tenant/router.py`
- ✅ Función: `get_connection_for_tenant(cliente_id)`
- ✅ Centralizar lógica de conexión

---

## 📊 ESTADÍSTICAS

- **Archivos analizados:** 50+
- **Líneas de código revisadas:** ~15,000
- **Queries raw SQL identificadas:** 50+
- **Uso de pyodbc:** 4 archivos principales
- **Uso de aioodbc:** 1 archivo (no usado)
- **Repositorios:** 3+ (UserRepository, RolRepository, etc.)
- **Services:** 10+ (AuthService, UsuarioService, RolService, etc.)

---

## 🎯 PRÓXIMOS PASOS

**Esperando confirmación del usuario para proceder con FASE 1.**

---

**Fin del Análisis FASE 0**




