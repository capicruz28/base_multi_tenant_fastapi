# 🛡️ PLAN DE MIGRACIÓN SEGURA - FASES 1 Y 2

## ⚠️ ADVERTENCIA IMPORTANTE

**SÍ, hay riesgos de romper el sistema si se implementa mal**, pero con este plan **NO se romperá** porque:

1. ✅ **Migración gradual** - No cambiamos todo de golpe
2. ✅ **Compatibilidad hacia atrás** - El código viejo sigue funcionando
3. ✅ **Feature flags** - Podemos activar/desactivar cambios
4. ✅ **Testing exhaustivo** - Validamos cada cambio
5. ✅ **Rollback inmediato** - Podemos volver atrás en segundos

---

## 📋 ESTRATEGIA GENERAL

### Principio: **"No romper lo que funciona"**

1. **Agregar código nuevo** sin tocar el existente
2. **Habilitar gradualmente** con feature flags
3. **Mantener código viejo** como fallback
4. **Testing en paralelo** antes de activar
5. **Rollback fácil** si algo falla

---

## 🔐 FASE 1: SEGURIDAD CRÍTICA (1-2 semanas)

### 1.1 Validación de Tenant en Tokens JWT

**RIESGO:** ⚠️ MEDIO - Puede bloquear usuarios legítimos si se implementa mal

**ESTRATEGIA SEGURA:**

#### Paso 1: Agregar validación OPCIONAL (sin romper nada)

```python
# app/core/auth.py - MODIFICACIÓN SEGURA

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Obtiene el usuario actual basado en el access token (Bearer).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)

        if not token_data.sub or token_data.type != "access":
            raise credentials_exception

        username = token_data.sub
        es_superadmin = payload.get("es_superadmin", False)
        target_cliente_id = payload.get("cliente_id")
        token_cliente_id = payload.get("cliente_id")  # ✅ NUEVO
        
        # ✅ NUEVO: Validación OPCIONAL con feature flag
        if settings.ENABLE_TENANT_TOKEN_VALIDATION:  # 🔄 Feature flag
            try:
                current_cliente_id = get_current_client_id()
                
                # Superadmin puede cambiar de tenant (comportamiento actual)
                if not es_superadmin and token_cliente_id != current_cliente_id:
                    logger.warning(
                        f"[SECURITY] Token de tenant {token_cliente_id} usado en tenant {current_cliente_id}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Token no válido para este tenant"
                    )
            except RuntimeError:
                # Si no hay contexto (script de fondo), permitir (comportamiento actual)
                logger.debug("[AUTH] Sin contexto de tenant, validación omitida")
        
        # ... resto del código existente sin cambios ...
```

#### Paso 2: Agregar feature flag en config

```python
# app/core/config.py - AGREGAR (no modificar existente)

class Settings(BaseSettings):
    # ... código existente ...
    
    # ✅ NUEVO: Feature flags para migración segura
    ENABLE_TENANT_TOKEN_VALIDATION: bool = os.getenv("ENABLE_TENANT_TOKEN_VALIDATION", "false").lower() == "true"
    ENABLE_QUERY_TENANT_VALIDATION: bool = os.getenv("ENABLE_QUERY_TENANT_VALIDATION", "false").lower() == "true"
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
```

#### Paso 3: Testing antes de activar

```python
# tests/test_tenant_token_validation.py - NUEVO ARCHIVO

def test_token_validation_disabled_by_default():
    """Verificar que por defecto NO se valida (comportamiento actual)"""
    # El sistema debe funcionar igual que antes
    pass

def test_token_validation_when_enabled():
    """Verificar que cuando se activa, funciona correctamente"""
    # Activar flag y probar
    pass
```

#### Paso 4: Activar gradualmente

1. **Semana 1:** Código agregado, flag en `false` (no cambia nada)
2. **Semana 2:** Activar en ambiente de desarrollo
3. **Semana 3:** Activar en staging
4. **Semana 4:** Activar en producción

**Si algo falla:** Cambiar flag a `false` y el sistema vuelve al comportamiento anterior.

---

### 1.2 Validación de Tenant en Queries

**RIESGO:** ⚠️ ALTO - Puede romper queries existentes

**ESTRATEGIA SEGURA:**

#### Paso 1: Crear función wrapper SEGURA

```python
# app/infrastructure/database/queries.py - AGREGAR (no modificar existente)

def execute_query_safe(
    query: str, 
    params: tuple = (), 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None,
    require_tenant_validation: bool = False  # ✅ NUEVO: Opcional
) -> List[Dict[str, Any]]:
    """
    Versión SEGURA de execute_query con validación opcional de tenant.
    
    IMPORTANTE: Por defecto NO valida (comportamiento actual).
    Solo valida si require_tenant_validation=True Y el flag está activo.
    """
    # Si la validación está desactivada, usar función original
    if not settings.ENABLE_QUERY_TENANT_VALIDATION or not require_tenant_validation:
        return execute_query(query, params, connection_type, client_id)
    
    # ✅ NUEVO: Validación opcional
    try:
        current_cliente_id = get_current_client_id()
        
        # Verificar que la query incluya filtro de tenant
        query_lower = query.lower()
        if "where" in query_lower and "cliente_id" not in query_lower:
            logger.warning(
                f"[SECURITY] Query sin filtro de tenant: {query[:100]}..."
            )
            # Opción 1: Agregar filtro automáticamente (más seguro)
            # Opción 2: Lanzar error (más estricto)
            # Por ahora: solo loggear (no romper)
        
        # Ejecutar query original
        return execute_query(query, params, connection_type, client_id)
        
    except RuntimeError:
        # Sin contexto, usar función original
        return execute_query(query, params, connection_type, client_id)
```

#### Paso 2: Migrar endpoints gradualmente

```python
# app/modules/users/presentation/endpoints.py - EJEMPLO

@router.get("/{usuario_id}")
async def get_usuario(
    usuario_id: int,
    current_user: Dict = Depends(get_current_user)
):
    # ✅ OPCIÓN 1: Usar función nueva con validación
    if settings.ENABLE_QUERY_TENANT_VALIDATION:
        result = execute_query_safe(
            SELECT_USUARIO_BY_ID,
            (usuario_id, get_current_client_id()),
            require_tenant_validation=True  # ✅ Activar validación
        )
    else:
        # ✅ OPCIÓN 2: Código original (fallback)
        result = execute_query(
            SELECT_USUARIO_BY_ID,
            (usuario_id, get_current_client_id())
        )
    
    # ... resto del código igual ...
```

#### Paso 3: Auditoría de queries

```python
# scripts/audit_queries.py - NUEVO SCRIPT

"""
Script para encontrar queries que NO filtran por cliente_id.
Ejecutar ANTES de activar validación.
"""

def audit_queries():
    # Buscar todas las queries en el código
    # Verificar que incluyan WHERE cliente_id = ?
    # Generar reporte
    pass
```

**Orden de migración:**
1. ✅ Endpoints de lectura primero (menos riesgo)
2. ✅ Endpoints de escritura después
3. ✅ Queries de autenticación al final (más críticas)

---

### 1.3 Rate Limiting

**RIESGO:** ⚠️ BAJO - Solo puede bloquear requests legítimos si se configura mal

**ESTRATEGIA SEGURA:**

#### Paso 1: Implementar con límites GENEROSOS

```python
# app/core/security/rate_limiting.py - NUEVO ARCHIVO

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.core.config import settings

# ✅ Límites GENEROSOS por defecto (no bloquean uso normal)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"] if settings.ENABLE_RATE_LIMITING else []  # ✅ Desactivado por defecto
)

# Límites específicos (solo si flag activo)
if settings.ENABLE_RATE_LIMITING:
    LOGIN_LIMIT = "5/minute"  # ✅ Generoso: 5 intentos por minuto
    API_LIMIT = "100/minute"  # ✅ Generoso: 100 requests por minuto
else:
    LOGIN_LIMIT = None
    API_LIMIT = None
```

#### Paso 2: Aplicar solo a endpoints críticos

```python
# app/modules/auth/presentation/endpoints.py

@router.post("/login/")
@limiter.limit(LOGIN_LIMIT) if LOGIN_LIMIT else lambda x: x  # ✅ Decorador condicional
async def login(...):
    # ... código existente sin cambios ...
```

**Ventaja:** Si el decorador está desactivado, no hace nada (comportamiento actual).

---

## ⚡ FASE 2: PERFORMANCE (2-3 semanas)

### 2.1 Connection Pooling

**RIESGO:** ⚠️ MEDIO-ALTO - Cambia cómo se manejan conexiones

**ESTRATEGIA SEGURA:**

#### Paso 1: Implementar pool PARALELO (no reemplazar)

```python
# app/infrastructure/database/connection_pool.py - NUEVO ARCHIVO

from sqlalchemy import create_engine, pool
from sqlalchemy.pool import QueuePool
import pyodbc
from app.core.config import settings

# ✅ Pool opcional (solo si flag activo)
_pool_engine = None

def get_pool_engine():
    """Obtiene engine con pool (solo si está habilitado)"""
    global _pool_engine
    
    if not settings.ENABLE_CONNECTION_POOLING:
        return None  # ✅ Pool desactivado
    
    if _pool_engine is None:
        # Construir connection string
        conn_str = build_connection_string()
        
        # Crear engine con pool
        _pool_engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={conn_str}",
            poolclass=QueuePool,
            pool_size=10,  # ✅ Tamaño conservador
            max_overflow=5,
            pool_pre_ping=True,  # ✅ Verificar conexiones antes de usar
            pool_recycle=3600,  # ✅ Reciclar cada hora
            echo=False
        )
    
    return _pool_engine

def get_db_connection_with_pool(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT):
    """
    Obtiene conexión del pool (si está habilitado) o conexión normal (fallback).
    """
    if settings.ENABLE_CONNECTION_POOLING:
        engine = get_pool_engine()
        if engine:
            return engine.connect()  # ✅ Conexión del pool
    
    # ✅ FALLBACK: Usar función original (comportamiento actual)
    from app.infrastructure.database.connection import get_db_connection
    return get_db_connection(connection_type)
```

#### Paso 2: Modificar función existente con fallback

```python
# app/infrastructure/database/connection.py - MODIFICACIÓN SEGURA

@contextmanager
def get_db_connection(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> Iterator[pyodbc.Connection]:
    """
    Context manager para obtener y cerrar una conexión a BD.
    
    ✅ NUEVO: Intenta usar pool si está habilitado, sino usa conexión directa.
    """
    conn = None
    try:
        # ✅ INTENTAR POOL PRIMERO (si está habilitado)
        if settings.ENABLE_CONNECTION_POOLING:
            try:
                from app.infrastructure.database.connection_pool import get_db_connection_with_pool
                conn = get_db_connection_with_pool(connection_type)
                if conn:
                    logger.debug(f"Conexión desde pool ({connection_type.value})")
                    yield conn
                    return
            except Exception as pool_err:
                logger.warning(f"Error con pool, usando conexión directa: {pool_err}")
                # ✅ FALLBACK: Continuar con conexión directa
        
        # ✅ FALLBACK: Código original (comportamiento actual)
        if connection_type == DatabaseConnection.DEFAULT:
            conn = get_db_connection_for_current_tenant()
        else:
            conn_str = get_connection_string(connection_type)
            conn = pyodbc.connect(conn_str)
        
        yield conn

    except pyodbc.Error as e:
        logger.error(f"Error de conexión: {str(e)}", exc_info=True)
        raise DatabaseError(status_code=500, detail=f"Error de conexión: {str(e)}")
    finally:
        if conn:
            conn.close()
```

**Ventaja:** Si el pool falla, automáticamente usa conexión directa (comportamiento actual).

#### Paso 3: Monitoreo antes de activar

```python
# scripts/monitor_connections.py - NUEVO SCRIPT

"""
Monitorear uso de conexiones antes de activar pool.
"""

def monitor_connections():
    # Contar conexiones abiertas
    # Verificar tiempo de vida de conexiones
    # Detectar leaks
    pass
```

**Orden de activación:**
1. ✅ Desarrollo (1 semana de pruebas)
2. ✅ Staging (1 semana de pruebas)
3. ✅ Producción (monitoreo intensivo primera semana)

---

### 2.2 Cache Distribuido (Redis)

**RIESGO:** ⚠️ BAJO - Solo afecta performance, no funcionalidad

**ESTRATEGIA SEGURA:**

#### Paso 1: Cache OPCIONAL con fallback

```python
# app/infrastructure/cache/redis_cache.py - NUEVO ARCHIVO

import redis
from app.core.config import settings
from typing import Optional, Any
import json

_redis_client = None

def get_redis_client():
    """Obtiene cliente Redis (solo si está habilitado)"""
    global _redis_client
    
    if not settings.ENABLE_REDIS_CACHE:
        return None  # ✅ Cache desactivado
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            # Test de conexión
            _redis_client.ping()
            logger.info("Redis cache conectado")
        except Exception as e:
            logger.warning(f"Redis no disponible, cache desactivado: {e}")
            _redis_client = None
    
    return _redis_client

def get_cached(key: str) -> Optional[Any]:
    """Obtiene valor del cache (si está habilitado)"""
    if not settings.ENABLE_REDIS_CACHE:
        return None  # ✅ Sin cache (comportamiento actual)
    
    client = get_redis_client()
    if not client:
        return None  # ✅ Fallback: sin cache
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        logger.warning(f"Error leyendo cache para key: {key}")
    
    return None

def set_cached(key: str, value: Any, ttl: int = 300):
    """Guarda valor en cache (si está habilitado)"""
    if not settings.ENABLE_REDIS_CACHE:
        return  # ✅ Sin cache (comportamiento actual)
    
    client = get_redis_client()
    if not client:
        return  # ✅ Fallback: sin cache
    
    try:
        client.setex(key, ttl, json.dumps(value))
    except Exception:
        logger.warning(f"Error guardando cache para key: {key}")
```

#### Paso 2: Usar cache en funciones existentes (sin romper)

```python
# app/core/tenant/routing.py - MODIFICACIÓN SEGURA

def get_connection_metadata(client_id: int) -> Dict[str, Any]:
    """
    Obtiene metadata de conexión para un cliente (con cache).
    """
    # ✅ NUEVO: Intentar cache primero (si está habilitado)
    if settings.ENABLE_REDIS_CACHE:
        from app.infrastructure.cache.redis_cache import get_cached, set_cached
        cached = get_cached(f"connection_metadata:{client_id}")
        if cached:
            logger.debug(f"[CACHE] HIT para cliente {client_id}")
            return cached
    
    # ✅ Código original (comportamiento actual)
    # Intentar obtener del cache en memoria
    cached_metadata = connection_cache.get(client_id)
    
    if cached_metadata:
        logger.debug(f"[METADATA] Cache HIT para cliente {client_id}")
        return cached_metadata
    
    # ... resto del código sin cambios ...
    
    # ✅ NUEVO: Guardar en Redis también (si está habilitado)
    if settings.ENABLE_REDIS_CACHE and metadata:
        set_cached(f"connection_metadata:{client_id}", metadata, ttl=600)
    
    return metadata
```

**Ventaja:** Si Redis falla, usa cache en memoria (comportamiento actual).

---

### 2.3 Operaciones Async de BD

**RIESGO:** ⚠️ ALTO - Cambia completamente cómo se manejan queries

**ESTRATEGIA SEGURA:**

#### ⚠️ RECOMENDACIÓN: NO HACER EN FASE 2

**Razón:** Es un cambio muy grande que requiere refactorizar todo el código.

**Mejor estrategia:**
1. ✅ Dejar para Fase 3 (Arquitectura)
2. ✅ Hacer módulo por módulo
3. ✅ Mantener código síncrono como fallback

**Si se hace, hacerlo así:**

```python
# app/infrastructure/database/async_queries.py - NUEVO ARCHIVO

import asyncpg
from app.core.config import settings

async def execute_query_async(
    query: str,
    params: tuple = (),
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> List[Dict[str, Any]]:
    """
    Versión async de execute_query.
    
    ⚠️ SOLO usar si ENABLE_ASYNC_DB está activo.
    Si no, usar execute_query normal (síncrono).
    """
    if not settings.ENABLE_ASYNC_DB:
        # ✅ FALLBACK: Usar función síncrona
        from app.infrastructure.database.queries import execute_query
        return execute_query(query, params, connection_type)
    
    # ... implementación async ...
```

---

## 🧪 PLAN DE TESTING

### Testing por Fase

#### Fase 1: Seguridad

```python
# tests/test_phase1_security.py

def test_token_validation_disabled():
    """Sistema funciona igual que antes"""
    # Activar endpoints sin flags
    # Verificar que todo funciona

def test_token_validation_enabled():
    """Validación funciona correctamente"""
    # Activar flags
    # Probar casos válidos e inválidos

def test_query_validation_doesnt_break_existing():
    """Queries existentes siguen funcionando"""
    # Ejecutar todas las queries actuales
    # Verificar que no fallan
```

#### Fase 2: Performance

```python
# tests/test_phase2_performance.py

def test_connection_pool_fallback():
    """Si pool falla, usa conexión directa"""
    # Simular fallo de pool
    # Verificar que funciona igual

def test_redis_cache_fallback():
    """Si Redis falla, usa cache en memoria"""
    # Simular fallo de Redis
    # Verificar que funciona igual

def test_performance_improvements():
    """Verificar mejoras de performance"""
    # Medir tiempos antes/después
    # Verificar que mejoró
```

---

## 🔄 PLAN DE ROLLBACK

### Si algo falla en producción:

#### Opción 1: Desactivar feature flags (30 segundos)

```bash
# .env
ENABLE_TENANT_TOKEN_VALIDATION=false
ENABLE_QUERY_TENANT_VALIDATION=false
ENABLE_RATE_LIMITING=false
ENABLE_CONNECTION_POOLING=false
ENABLE_REDIS_CACHE=false
```

**Resultado:** Sistema vuelve al comportamiento anterior inmediatamente.

#### Opción 2: Rollback de código (Git)

```bash
git revert <commit-hash>
git push
```

**Resultado:** Código vuelve a versión anterior.

---

## 📅 CRONOGRAMA SEGURO

### Semana 1-2: Fase 1 (Seguridad)

**Día 1-3:** Implementar código con flags desactivados
- ✅ Código agregado, nada cambia
- ✅ Testing de que no rompe nada

**Día 4-5:** Testing exhaustivo
- ✅ Tests unitarios
- ✅ Tests de integración
- ✅ Tests de seguridad

**Día 6-7:** Activar en desarrollo
- ✅ Flags activados en dev
- ✅ Monitoreo intensivo

**Día 8-10:** Activar en staging
- ✅ Flags activados en staging
- ✅ Testing de usuarios reales

**Día 11-14:** Activar en producción (gradual)
- ✅ Día 11: 10% de tráfico
- ✅ Día 12: 50% de tráfico
- ✅ Día 13: 100% de tráfico
- ✅ Día 14: Monitoreo y ajustes

### Semana 3-5: Fase 2 (Performance)

**Misma estrategia gradual**

---

## ✅ CHECKLIST DE SEGURIDAD

Antes de activar cualquier cambio:

- [ ] ✅ Código implementado con flags desactivados
- [ ] ✅ Tests unitarios pasando
- [ ] ✅ Tests de integración pasando
- [ ] ✅ Testing manual en desarrollo
- [ ] ✅ Documentación actualizada
- [ ] ✅ Plan de rollback listo
- [ ] ✅ Monitoreo configurado
- [ ] ✅ Alertas configuradas
- [ ] ✅ Backup de BD realizado
- [ ] ✅ Equipo notificado

---

## 🎯 CONCLUSIÓN

**¿Se romperá el sistema?** 

**NO, si sigues este plan** porque:

1. ✅ **Código nuevo no toca código viejo**
2. ✅ **Feature flags permiten activar/desactivar**
3. ✅ **Fallbacks garantizan funcionamiento**
4. ✅ **Testing exhaustivo antes de activar**
5. ✅ **Rollback inmediato si algo falla**

**¿Funcionará correctamente?**

**SÍ**, porque:

1. ✅ **Migración gradual** - Un cambio a la vez
2. ✅ **Testing en cada paso** - Validamos antes de avanzar
3. ✅ **Monitoreo continuo** - Detectamos problemas rápido
4. ✅ **Rollback fácil** - Volvemos atrás si es necesario

**Riesgo residual:** ⚠️ BAJO (si sigues el plan)

---

**FIN DEL PLAN DE MIGRACIÓN SEGURA**

