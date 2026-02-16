# 📘 Módulo de Queries SQL Modulares

**✅ FASE 2: Migración completada desde sql_constants.py monolítico**

---

## 🎯 Propósito

Este módulo organiza todas las queries SQL del sistema por dominio de negocio, reemplazando el archivo monolítico `sql_constants.py` (723 líneas) por una estructura modular y escalable.

---

## 📁 Estructura

```
queries/
├── __init__.py              # Re-exports centralizados
├── base/
│   └── common_queries.py    # Queries compartidas entre módulos
├── auth/
│   └── auth_queries.py      # Autenticación y niveles de acceso (12 queries)
├── users/
│   └── user_queries.py      # Gestión de usuarios (6 queries)
├── rbac/
│   └── rbac_queries.py      # Roles y permisos (7 queries)
├── menus/
│   └── menu_queries.py      # Menús y áreas (19 queries)
└── audit/
    └── audit_queries.py     # Auditoría (2 queries)
```

**Total:** 46 queries organizadas por dominio

---

## 📖 Uso

### Importar desde módulo específico (Recomendado)

```python
# ✅ RECOMENDADO: Importar desde módulo específico
from app.infrastructure.database.queries.auth.auth_queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE
)

from app.infrastructure.database.queries.users.user_queries import (
    SELECT_USUARIOS_PAGINATED,
    COUNT_USUARIOS_PAGINATED
)
```

### Importar desde queries/__init__.py (Alternativa)

```python
# ✅ ALTERNATIVA: Importar desde queries/__init__.py
from app.infrastructure.database.queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    SELECT_USUARIOS_PAGINATED,
)
```

### Compatibilidad con sql_constants.py (Durante migración)

```python
# ⚠️ DEPRECATED: Importar desde sql_constants.py (funciona pero muestra warning)
from app.infrastructure.database.sql_constants import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE  # Funciona gracias a re-exports
)
```

---

## 🔄 Migración desde sql_constants.py

### Mapeo de Queries

| Módulo Antiguo | Módulo Nuevo | Archivo |
|----------------|--------------|---------|
| `sql_constants` | `queries.auth` | `auth/auth_queries.py` |
| `sql_constants` | `queries.users` | `users/user_queries.py` |
| `sql_constants` | `queries.rbac` | `rbac/rbac_queries.py` |
| `sql_constants` | `queries.menus` | `menus/menu_queries.py` |
| `sql_constants` | `queries.audit` | `audit/audit_queries.py` |

### Guía de Migración

Ver: `docs/MIGRACION_QUERIES.md`

---

## ✅ Ventajas de la Estructura Modular

1. **Escalabilidad:** Cada módulo ERP nuevo (Planillas, Logística, Almacén) puede tener su propio módulo de queries
2. **Mantenibilidad:** Queries organizadas por dominio de negocio, fácil de encontrar
3. **Trabajo Paralelo:** Equipos pueden trabajar en módulos diferentes sin conflictos de merge
4. **Claridad:** Estructura clara y autodocumentada

---

## 🚀 Agregar Queries para Nuevos Módulos ERP

### Ejemplo: Módulo de Planillas

1. **Crear estructura:**
```
queries/
└── planillas/
    ├── __init__.py
    └── planilla_queries.py
```

2. **Agregar queries:**
```python
# queries/planillas/planilla_queries.py
SELECT_PLANILLAS_PAGINATED = """
SELECT ...
FROM planilla
WHERE cliente_id = :cliente_id
...
"""

INSERT_PLANILLA = """
INSERT INTO planilla ...
"""
```

3. **Re-exportar en __init__.py:**
```python
# queries/planillas/__init__.py
from .planilla_queries import (
    SELECT_PLANILLAS_PAGINATED,
    INSERT_PLANILLA,
)
```

4. **Usar en servicio:**
```python
from app.infrastructure.database.queries.planillas import (
    SELECT_PLANILLAS_PAGINATED
)
```

---

## 📝 Convenciones

1. **Nombres de queries:** UPPER_SNAKE_CASE
2. **Parámetros:** Siempre usar parámetros nombrados (`:param`)
3. **Ejecución:** Usar `text().bindparams()` para seguridad
4. **Filtros de tenant:** Incluir `cliente_id` en todas las queries (excepto tablas globales)

---

## ⚠️ Notas Importantes

- `sql_constants.py` está deprecated pero sigue funcionando gracias a re-exports
- Migrar imports gradualmente cuando sea conveniente
- No hay prisa en migrar todo de una vez (compatibilidad mantenida)

---

**Última actualización:** Diciembre 2024  
**Fase:** FASE 2 completada
