# 📘 Guía de Migración: Código Legacy → Async

**FASE 3: Mantenibilidad y Calidad**  
**Objetivo:** Estandarizar acceso a datos y eliminar código legacy

---

## 🎯 Objetivo

Migrar todo el código que usa funciones síncronas deprecated a la versión async moderna.

---

## 📋 Checklist de Migración

### 1. **Cambiar Imports**

**❌ ANTES (Deprecated):**
```python
from app.infrastructure.database.queries import execute_query, execute_insert, execute_update
```

**✅ DESPUÉS (Async):**
```python
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
```

---

### 2. **Agregar `await` a Llamadas**

**❌ ANTES (Síncrono):**
```python
def some_function():
    results = execute_query(query, params)
    return results
```

**✅ DESPUÉS (Async):**
```python
async def some_function():
    results = await execute_query(query, params)
    return results
```

---

### 3. **Migrar Funciones a Async**

**❌ ANTES:**
```python
def get_user(user_id: int):
    query = "SELECT * FROM usuario WHERE usuario_id = ?"
    result = execute_query(query, (user_id,))
    return result[0] if result else None
```

**✅ DESPUÉS:**
```python
async def get_user(user_id: int):
    from sqlalchemy import select
    from app.infrastructure.database.tables import UsuarioTable
    
    query = select(UsuarioTable).where(UsuarioTable.c.usuario_id == user_id)
    result = await execute_query(query, client_id=current_client_id)
    return result[0] if result else None
```

---

### 4. **Migrar Raw SQL a SQLAlchemy Core**

**❌ ANTES (Raw SQL):**
```python
query = """
    SELECT u.*, r.nombre as rol_nombre
    FROM usuario u
    LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id
    LEFT JOIN rol r ON ur.rol_id = r.rol_id
    WHERE u.cliente_id = ?
"""
results = await execute_query(query, (cliente_id,))
```

**✅ DESPUÉS (SQLAlchemy Core):**
```python
from sqlalchemy import select
from app.infrastructure.database.tables import UsuarioTable, UsuarioRolTable, RolTable

query = (
    select(
        UsuarioTable,
        RolTable.c.nombre.label('rol_nombre')
    )
    .select_from(
        UsuarioTable
        .outerjoin(UsuarioRolTable, UsuarioTable.c.usuario_id == UsuarioRolTable.c.usuario_id)
        .outerjoin(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
    )
    .where(UsuarioTable.c.cliente_id == cliente_id)
)
results = await execute_query(query, client_id=cliente_id)
```

**⚠️ NOTA:** Si la query es muy compleja (CTEs, hints específicos), puedes usar `text()`:
```python
from sqlalchemy import text

query = text("""
    WITH ComplexCTE AS (
        SELECT ...
    )
    SELECT * FROM ComplexCTE
    OPTION (MAXDOP 4)
""").bindparams(cliente_id=cliente_id)

results = await execute_query(query, client_id=cliente_id)
```

---

### 5. **Actualizar Llamadores**

Si una función se vuelve async, todos sus llamadores también deben ser async:

**❌ ANTES:**
```python
def endpoint():
    user = get_user(123)  # ❌ Error: get_user ahora es async
    return user
```

**✅ DESPUÉS:**
```python
async def endpoint():
    user = await get_user(123)  # ✅ Correcto
    return user
```

---

## 🔍 Cómo Identificar Código Legacy

### Script de Análisis

Ejecuta el script de análisis:
```bash
python scripts/analyze_legacy_code.py
```

Este script identifica:
- ✅ Imports deprecated
- ✅ Llamadas síncronas sin `await`
- ✅ Raw SQL que podría migrarse

---

## 📝 Ejemplos de Migración Completos

### Ejemplo 1: Servicio Simple

**❌ ANTES:**
```python
# app/modules/users/services/user_service.py
from app.infrastructure.database.queries import execute_query

def get_user_by_id(user_id: int):
    query = "SELECT * FROM usuario WHERE usuario_id = ?"
    result = execute_query(query, (user_id,))
    return result[0] if result else None
```

**✅ DESPUÉS:**
```python
# app/modules/users/services/user_service.py
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import UsuarioTable
from sqlalchemy import select
from app.core.tenant.context import get_current_client_id

async def get_user_by_id(user_id: int):
    client_id = get_current_client_id()
    query = select(UsuarioTable).where(UsuarioTable.c.usuario_id == user_id)
    result = await execute_query(query, client_id=client_id)
    return result[0] if result else None
```

---

### Ejemplo 2: Endpoint FastAPI

**❌ ANTES:**
```python
@router.get("/users/{user_id}")
def get_user_endpoint(user_id: int):
    user = get_user_by_id(user_id)  # ❌ Síncrono
    return user
```

**✅ DESPUÉS:**
```python
@router.get("/users/{user_id}")
async def get_user_endpoint(user_id: int):
    user = await get_user_by_id(user_id)  # ✅ Async
    return user
```

---

## ⚠️ Casos Especiales

### Stored Procedures

**✅ Ya está bien implementado:**
```python
from app.infrastructure.database.queries_async import execute_procedure_params

result = await execute_procedure_params(
    "sp_get_user_data",
    {"usuario_id": user_id, "cliente_id": client_id},
    client_id=client_id
)
```

### Queries con Query Hints

**✅ Usar `text()` con parámetros:**
```python
from sqlalchemy import text

query = text("""
    SELECT * FROM usuario
    WHERE cliente_id = :cliente_id
    OPTION (MAXDOP 4, FORCE ORDER)
""").bindparams(cliente_id=client_id)

results = await execute_query(query, client_id=client_id)
```

---

## ✅ Checklist de Verificación

Antes de marcar como completado, verifica:

- [ ] Todos los imports usan `queries_async`
- [ ] Todas las llamadas tienen `await`
- [ ] Todas las funciones son `async`
- [ ] Los endpoints FastAPI son `async`
- [ ] Se usa SQLAlchemy Core cuando es posible
- [ ] Se mantiene validación de tenant
- [ ] Tests actualizados (si existen)

---

## 🚀 Orden Recomendado de Migración

1. **Servicios críticos** (auth, users)
2. **Servicios de negocio** (rbac, modulos)
3. **Servicios de administración** (superadmin, tenant)
4. **Repositorios**
5. **Utilidades y helpers**

---

**Última actualización:** Diciembre 2024


