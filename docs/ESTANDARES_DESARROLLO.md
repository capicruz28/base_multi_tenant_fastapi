# 📘 Estándares de Desarrollo

**Proyecto:** FastAPI Multi-Tenant Backend  
**Última actualización:** Diciembre 2024

---

## 🎯 Principios Fundamentales

### 1. **Seguridad Multi-Tenant Primero**

✅ **SIEMPRE:**
- Incluir filtro de `cliente_id` en todas las queries
- Usar `get_current_client_id()` del contexto
- Validar tenant en cada operación de datos

❌ **NUNCA:**
- Usar `skip_tenant_validation=True` sin flag de configuración
- Bypass de validación de tenant en código de producción
- Queries sin filtro de tenant

---

### 2. **Async por Defecto**

✅ **SIEMPRE:**
- Usar `async/await` para operaciones de BD
- Importar de `queries_async`, no de `queries`
- Funciones async en endpoints FastAPI

❌ **NUNCA:**
- Usar funciones síncronas deprecated
- Llamar funciones async sin `await`
- Mezclar código síncrono/async

---

### 3. **SQLAlchemy Core Preferido**

✅ **PREFERIR:**
- SQLAlchemy Core para queries simples/complejas
- `select()`, `update()`, `delete()`, `insert()`
- CTEs nativas de SQLAlchemy

⚠️ **PERMITIDO:**
- `text()` con parámetros para sintaxis SQL Server específica
- Stored Procedures con `execute_procedure_params()`
- Query Hints cuando sea necesario

❌ **EVITAR:**
- Raw SQL strings sin parámetros
- Concatenación de strings para queries
- Queries sin validación de tenant

---

## 📝 Convenciones de Código

### Estructura de Archivos

```
app/
├── core/              # Lógica core (tenant, security, auth)
├── modules/           # Módulos de negocio
│   ├── auth/
│   │   ├── application/
│   │   │   └── services/
│   │   ├── infrastructure/
│   │   │   └── repositories/
│   │   └── presentation/
│   │       └── endpoints.py
├── infrastructure/    # Infraestructura (DB, cache, etc.)
└── api/              # Endpoints principales
```

### Nombres de Archivos

- **Servicios:** `*_service.py`
- **Repositorios:** `*_repository.py`
- **Endpoints:** `endpoints.py` o `*_endpoints.py`
- **Schemas:** `schemas.py` o `*_schemas.py`
- **Tests:** `test_*.py`

### Nombres de Funciones

- **Async:** `async def nombre_funcion()`
- **Sync (solo si es necesario):** `def nombre_funcion()`
- **Tests:** `def test_nombre_descripcion()`

---

## 🔒 Patrones de Seguridad

### Patrón: Query con Tenant Filter

```python
from sqlalchemy import select
from app.infrastructure.database.tables import UsuarioTable
from app.infrastructure.database.queries_async import execute_query
from app.core.tenant.context import get_current_client_id

async def get_users():
    client_id = get_current_client_id()
    
    query = select(UsuarioTable).where(
        UsuarioTable.c.cliente_id == client_id,
        UsuarioTable.c.es_activo == True
    )
    
    results = await execute_query(query, client_id=client_id)
    return results
```

### Patrón: Validación de Tenant

```python
from app.core.tenant.context import get_current_client_id
from app.core.exceptions import ValidationError

async def update_user(user_id: UUID, data: dict):
    client_id = get_current_client_id()
    
    # Verificar que el usuario pertenece al tenant
    user = await get_user(user_id)
    if user['cliente_id'] != client_id:
        raise ValidationError("Usuario no pertenece al tenant actual")
    
    # Proceder con actualización
    ...
```

---

## ⚡ Patrones de Performance

### Patrón: Batch Loading (Prevenir N+1)

```python
from app.infrastructure.database.query_optimizer import batch_load_roles_for_users

async def get_users_with_roles(user_ids: List[UUID]):
    client_id = get_current_client_id()
    
    # Cargar todos los roles en una query
    roles_map = await batch_load_roles_for_users(user_ids, client_id)
    
    # Usar el mapa en lugar de queries individuales
    for user_id in user_ids:
        user_roles = roles_map.get(user_id, [])
        ...
```

### Patrón: Cache Inteligente

```python
from app.infrastructure.cache.redis_cache import cached

@cached(ttl=300, key_prefix="user_")
async def get_user_cached(user_id: UUID):
    # Esta función se cachea automáticamente
    return await get_user(user_id)
```

---

## 🧪 Patrones de Testing

### Test de Aislamiento Multi-Tenant

```python
@pytest.mark.asyncio
async def test_tenant_isolation(mock_tenant_context):
    """Test: Datos de un tenant no son accesibles desde otro."""
    tenant_1_id = uuid4()
    tenant_2_id = uuid4()
    
    # Establecer contexto tenant 1
    context_1 = TenantContext(client_id=tenant_1_id, ...)
    tokens = set_tenant_context(context_1)
    
    try:
        # Query desde tenant 1
        results = await execute_query(query, client_id=tenant_1_id)
        # Verificar que solo retorna datos de tenant 1
        assert all(r['cliente_id'] == tenant_1_id for r in results)
    finally:
        reset_tenant_context(tokens)
```

---

## 📚 Documentación

### Docstrings

```python
async def get_user(user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por ID.
    
    Args:
        user_id: ID del usuario (UUID)
    
    Returns:
        Diccionario con datos del usuario o None si no existe
    
    Raises:
        ValidationError: Si el usuario no pertenece al tenant actual
    
    Example:
        >>> user = await get_user(uuid4())
        >>> print(user['nombre_usuario'])
    """
    ...
```

---

## 🔍 Checklist de Code Review

Antes de hacer merge, verificar:

- [ ] ¿Incluye filtro de `cliente_id` en queries?
- [ ] ¿Usa `async/await` correctamente?
- [ ] ¿Importa de `queries_async`, no de `queries`?
- [ ] ¿Tiene docstrings completos?
- [ ] ¿Maneja errores apropiadamente?
- [ ] ¿No usa `skip_tenant_validation=True` sin flag?
- [ ] ¿Tests pasan?
- [ ] ¿No introduce problemas N+1?

---

## 🚨 Errores Comunes a Evitar

### ❌ Error 1: Query sin filtro de tenant

```python
# MAL
query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
results = await execute_query(query)
```

```python
# BIEN
query = select(UsuarioTable).where(
    UsuarioTable.c.cliente_id == get_current_client_id(),
    UsuarioTable.c.es_activo == True
)
results = await execute_query(query, client_id=get_current_client_id())
```

### ❌ Error 2: Llamada síncrona a función async

```python
# MAL
def endpoint():
    user = get_user(user_id)  # Falta await
```

```python
# BIEN
async def endpoint():
    user = await get_user(user_id)
```

### ❌ Error 3: Import deprecated

```python
# MAL
from app.infrastructure.database.queries import execute_query
```

```python
# BIEN
from app.infrastructure.database.queries_async import execute_query
```

---

**Última actualización:** Diciembre 2024


