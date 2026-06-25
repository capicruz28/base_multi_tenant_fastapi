# 02 — Auditoría SQLAlchemy y Ciclo de Vida de Conexiones

**Tipo:** Auditoría técnica (estado actual)  
**Fecha:** 2026-06-25  
**Alcance:** Engine, Session, transacciones, UoW, puntos de nacimiento de conexión SQL

---

## 1. Resumen ejecutivo

El backend **no utiliza el patrón FastAPI clásico** (`SessionLocal` global + `Depends(get_db)` + ORM `session.add()`).

La vía canónica es:

1. **SQLAlchemy Core** (`select`, `insert`, `update`) ejecutado sobre `AsyncSession`
2. **Context managers** (`get_db_connection`, `get_connection_for_tenant`, `UnitOfWork`)
3. **Driver async:** `mssql+aioodbc` vía `create_async_engine`
4. **Cache de engines** por proceso: claves `"admin"` y `"tenant_{client_id}"`

No existe `SessionLocal`, `scoped_session`, ni `session.flush()` en código de aplicación.

---

## 2. Creación del Engine

### 2.1 Archivo canónico

`app/infrastructure/database/connection_async.py`

### 2.2 Enum `DatabaseConnection`

```python
class DatabaseConnection(Enum):
    DEFAULT = "default"   # tenant-aware
    ADMIN = "admin"       # BD central / metadata
```

**Duplicado legacy:** `connection.py` (DEPRECATED) redefine el mismo enum.

### 2.3 Función `_get_async_engine()`

| Parámetro | Comportamiento |
|-----------|----------------|
| `connection_type=ADMIN` | Engine key `"admin"`; URL desde `settings.DB_ADMIN_*` |
| `connection_type=DEFAULT` | Engine key `"tenant_{client_id}"`; URL desde settings o metadata |

**Pool (desde `settings`):**

| Setting | Default |
|---------|---------|
| `DB_POOL_SIZE` | 10 |
| `DB_MAX_OVERFLOW` | 5 |
| `DB_POOL_RECYCLE` | 3600 s |
| `DB_POOL_TIMEOUT` | 30 s |
| `pool_pre_ping` | True |

**Cache global:** `_async_engines: dict[str, AsyncEngine]` — vive durante todo el proceso worker.

### 2.4 Construcción de connection string

`_build_async_connection_string()`:

- **ADMIN:** credenciales `DB_ADMIN_SERVER`, `DB_ADMIN_NAME`, etc.
- **DEFAULT single-DB:** credenciales `DB_SERVER`, `DB_NAME`, etc. (BD compartida actual)
- **DEFAULT multi-DB:** metadata de `cliente_conexion` (servidor, nombre_bd, usuario/password desencriptados)

---

## 3. Session Factory

**No hay factory global.**

En cada `get_db_connection()`:

```python
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async with async_session() as session:
    yield session
```

Implicación: se instancia un `sessionmaker` nuevo en cada apertura de contexto (sobre engine cacheado).

---

## 4. Ciclo de vida de Session

### 4.1 `get_db_connection()` — `connection_async.py`

```
async with get_db_connection(connection_type, client_id, connection_metadata) as session:
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Importante:** NO hace commit automático. El caller debe commitear explícitamente o usar `session.begin()` / `UnitOfWork`.

### 4.2 `get_connection_for_tenant()` — `routing.py`

Router centralizado (FASE 5):

```
get_connection_for_tenant(cliente_id)
  ├─ cliente_id == SYSTEM_CLIENT_ID → get_db_connection(ADMIN)
  ├─ database_type == "multi"       → get_db_connection(DEFAULT, metadata=...)
  └─ else (single)                  → get_db_connection(DEFAULT, client_id=...)
```

Usado por `queries_async._get_connection_context()` cuando `connection_type=DEFAULT`.

### 4.3 Dependency injection FastAPI

**No existe `Depends(get_db)`.**

Las sesiones se abren dentro de:

- `execute_query` / `execute_insert` / `execute_update` (una sesión por llamada)
- `UnitOfWork` (una sesión por transacción multi-paso)
- Servicios que usan `async with get_db_connection(ADMIN) as session` directamente (onboarding, platform bootstrap)

### 4.4 Compartición de sesión

**No hay sesión compartida por request HTTP.**

Múltiples `execute_*` en un mismo endpoint = múltiples conexiones/sesiones independientes, salvo que el service use explícitamente `UnitOfWork` o pase `AsyncSession` (caso `CfgCodigoSecuenciaRepository` con sesión externa).

---

## 5. Punto central: `queries_async.py`

### 5.1 `execute_query()`

Flujo:

1. Resolver `client_id` (parámetro o `ContextVar`)
2. Aplicar `apply_tenant_filter()` salvo `skip_tenant_validation` o tabla global
3. Auditar con `QueryAuditor` (producción)
4. `async with _get_connection_context(...) as session`
5. `await session.execute(query)`
6. SELECT → fetchall, sin commit
7. UPDATE/INSERT/DELETE detectado → **`await session.commit()`**
8. `session.close()` al salir del context

### 5.2 `execute_insert()` / `execute_update()`

- Abren sesión propia
- Ejecutan mutación
- **`commit()` explícito** al finalizar
- `rollback()` en excepción

### 5.3 Matriz de transacciones

| Mecanismo | SELECT | INSERT/UPDATE/DELETE | Error |
|-----------|--------|----------------------|-------|
| `get_db_connection` (raw) | Sin commit | Sin commit (caller) | rollback + close |
| `execute_query` SELECT | Sin commit | — | rollback |
| `execute_query` mutación | — | commit inmediato | rollback |
| `execute_insert/update` | — | commit inmediato | rollback |
| `UnitOfWork` | Sin commit intermedio | commit en `__aexit__` | rollback en `__aexit__` |
| `session.begin()` (onboarding) | — | commit al salir de `begin()` | rollback automático SQLAlchemy |

### 5.4 `flush()`

**No se usa** en aplicación. Persistencia vía `execute` + `commit`.

---

## 6. Unit of Work

**Archivo:** `app/core/application/unit_of_work.py`

```python
async with UnitOfWork(client_id=..., connection_type=DEFAULT) as uow:
    await uow.execute(query1)
    await uow.execute(query2)
# → commit automático si no hubo excepción
```

| Aspecto | Comportamiento |
|---------|----------------|
| Obtención `client_id` | Parámetro o `get_current_client_id()` |
| Sesión | `get_db_connection(...).__aenter__()` |
| `execute()` | `session.execute()`; SELECT retorna list[dict] |
| Éxito | `session.commit()` |
| Error | `session.rollback()` |
| Flag config | `ENABLE_UNIT_OF_WORK=true` definido pero **no consultado** en runtime |

**Consumidores:** IAM sessions V2, INV procesos transaccionales, PUR creación transaccional, MNT.

---

## 7. Dónde nace una conexión SQL

```
┌─────────────────────────────────────────────────────────────┐
│              PUNTOS DE NACIMIENTO DE CONEXIÓN               │
└─────────────────────────────────────────────────────────────┘

[A] CANÓNICO — AsyncEngine + AsyncSession
    connection_async._get_async_engine()
      → create_async_engine("mssql+aioodbc://...")
      → checkout del pool al abrir AsyncSession
    Disparadores:
      - get_db_connection()
      - get_connection_for_tenant()
      - UnitOfWork.__aenter__()
      - execute_*() vía _get_connection_context()

[B] LEGACY SYNC — connection_pool.py
    create_engine("mssql+pyodbc://...")
    Disparador: get_connection_from_pool()
    Estado: consumidor sync (connection.py) lanza NotImplementedError

[C] RAW PYODBC — routing.py
    pyodbc.connect(conn_str, timeout=30)
    Funciones: get_db_connection_for_client(), get_db_connection_for_current_tenant()
    Uso: scripts, tests, código legacy no migrado

[D] BOOTSTRAP METADATA (chicken-and-egg)
    _query_connection_metadata_from_db_async()
      → get_db_connection(ADMIN) para leer cliente_conexion
    Disparador: primer acceso tenant sin metadata en cache
```

### 7.1 Diagrama flujo request ERP típico

```
HTTP Request
  → TenantMiddleware (ContextVar client_id)
  → Endpoint → Service
      → execute_query(Select(...), client_id=...)
          → apply_tenant_filter
          → get_connection_for_tenant(cliente_id)
              → get_connection_metadata_async() [cache / query ADMIN]
              → get_db_connection(DEFAULT)
                  → _get_async_engine() [cache hit | create]
                  → sessionmaker() → AsyncSession
          → session.execute(query)
          → [SELECT: sin commit] → session.close()
```

### 7.2 Diagrama flujo transaccional IAM V2

```
SessionCreationService.create()
  → async with UnitOfWork(client_id) as uow
      → session_transaction_core.create_session_with_token_tx(uow, ...)
          → uow.execute(INSERT/UPDATE) × N
  → __aexit__: commit | rollback
  → SessionRedisBridge (post-commit, fuera de UoW)
```

---

## 8. Scope y dispose

### 8.1 Scope de proceso

| Recurso | Scope | Limpieza |
|---------|-------|----------|
| `_async_engines` | Proceso worker | `close_all_async_engines()` — **existe pero no se invoca en shutdown** |
| `_pools` (sync legacy) | Proceso worker | `close_all_pools()` — **sí se invoca en `main.py` shutdown** |
| `AsyncSession` | Operación / UoW | `session.close()` al salir del context |
| `ContextVar` tenant | Request HTTP | `reset_tenant_context()` en middleware finally |

### 8.2 Shutdown (`app/main.py`)

```python
async def shutdown_event():
    close_all_pools()  # solo pools sync legacy
    # close_all_async_engines() NO llamado
```

---

## 9. Vías legacy / deprecated

| Archivo | Estado |
|---------|--------|
| `connection.py` | DEPRECATED; `get_db_connection` sync → `NotImplementedError` |
| `queries.py` | DEPRECATED; reemplazado por `queries_async.py` |
| `connection_pool.py` | Pool sync; inicialización al import si `ENABLE_CONNECTION_POOLING=true` |
| `routing.get_db_connection_for_client()` | pyodbc directo |

**Riesgo documentado:** `auth/endpoints.py` puede importar `get_db_connection` desde `connection.py` en flujo Azure AD (código potencialmente roto si se ejecuta).

---

## 10. Configuración relevante (`config.py`)

| Variable | Rol |
|----------|-----|
| `DB_*` | Conexión BD compartida (DEFAULT single) |
| `DB_ADMIN_*` | BD central |
| `ENABLE_CONNECTION_POOLING` | Pool sync legacy |
| `ENABLE_UNIT_OF_WORK` | Definido; sin enforcement |
| `ALLOW_TENANT_FILTER_BYPASS` | Bypass filtro tenant (scripts) |
| `SUPERADMIN_CLIENTE_ID` | UUID cliente sistema |

---

## 11. Archivos clave (índice)

| Rol | Ruta |
|-----|------|
| Conexión async canónica | `app/infrastructure/database/connection_async.py` |
| Router tenant | `app/core/tenant/routing.py` |
| Ejecución queries | `app/infrastructure/database/queries_async.py` |
| Filtro tenant | `app/infrastructure/database/query_helpers.py` |
| Unit of Work | `app/core/application/unit_of_work.py` |
| Pool sync legacy | `app/infrastructure/database/connection_pool.py` |
| Conexión sync deprecated | `app/infrastructure/database/connection.py` |
| Cache metadata conexión | `app/core/tenant/cache.py` |
| Tests UoW | `tests/unit/test_unit_of_work.py` |

---

## 12. Hallazgos (descriptivos)

| # | Hallazgo | Severidad |
|---|----------|-----------|
| 1 | No hay sesión por request; múltiples round-trips por endpoint sin UoW | Importante |
| 2 | `execute_*` hace commit por operación — transacciones multi-paso requieren UoW explícito | Importante |
| 3 | `close_all_async_engines()` nunca se llama en shutdown | Menor |
| 4 | Dos sistemas de pool (async + sync) coexisten | Menor |
| 5 | `DatabaseConnection` duplicado en archivos deprecated | Menor |
| 6 | `session.flush()` ausente — diseño intencional Core+commit | Informativo |
| 7 | Multi-DB routing implementado en `get_connection_for_tenant` pero no ejercitado en producción actual | Importante (contexto futuro) |
