# 📘 Guía de Migración: sql_constants.py → Estructura Modular

**Fecha:** Diciembre 2024  
**Fase:** FASE 2 del Plan de Refactorización

---

## 🎯 Objetivo

Migrar imports de `sql_constants.py` a la nueva estructura modular por dominio.

---

## 📋 Mapeo de Queries

### Auth (Autenticación)

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    GET_USER_MAX_ACCESS_LEVEL,
    IS_USER_SUPER_ADMIN
)
```

**Después:**
```python
from app.infrastructure.database.queries.auth.auth_queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    GET_USER_MAX_ACCESS_LEVEL,
    IS_USER_SUPER_ADMIN
)
```

**Archivo:** `app/infrastructure/database/queries/auth/auth_queries.py`

---

### Users (Usuarios)

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    SELECT_USUARIOS_PAGINATED,
    COUNT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED_MULTI_DB,
    COUNT_USUARIOS_PAGINATED_MULTI_DB
)
```

**Después:**
```python
from app.infrastructure.database.queries.users.user_queries import (
    SELECT_USUARIOS_PAGINATED,
    COUNT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED_MULTI_DB,
    COUNT_USUARIOS_PAGINATED_MULTI_DB
)
```

**Archivo:** `app/infrastructure/database/queries/users/user_queries.py`

---

### RBAC (Roles y Permisos)

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    SELECT_ROLES_PAGINATED,
    COUNT_ROLES_PAGINATED,
    SELECT_PERMISOS_POR_ROL,
    DEACTIVATE_ROL,
    REACTIVATE_ROL,
    DELETE_PERMISOS_POR_ROL,
    INSERT_PERMISO_ROL
)
```

**Después:**
```python
from app.infrastructure.database.queries.rbac.rbac_queries import (
    SELECT_ROLES_PAGINATED,
    COUNT_ROLES_PAGINATED,
    SELECT_PERMISOS_POR_ROL,
    DEACTIVATE_ROL,
    REACTIVATE_ROL,
    DELETE_PERMISOS_POR_ROL,
    INSERT_PERMISO_ROL
)
```

**Archivo:** `app/infrastructure/database/queries/rbac/rbac_queries.py`

---

### Menus (Menús y Áreas)

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    GET_AREAS_PAGINATED_QUERY,
    COUNT_AREAS_QUERY,
    GET_AREA_BY_ID_QUERY,
    INSERT_MENU,
    SELECT_MENU_BY_ID,
    GET_ALL_MENUS_ADMIN
)
```

**Después:**
```python
from app.infrastructure.database.queries.menus.menu_queries import (
    GET_AREAS_PAGINATED_QUERY,
    COUNT_AREAS_QUERY,
    GET_AREA_BY_ID_QUERY,
    INSERT_MENU,
    SELECT_MENU_BY_ID,
    GET_ALL_MENUS_ADMIN
)
```

**Archivo:** `app/infrastructure/database/queries/menus/menu_queries.py`

---

### Audit (Auditoría)

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    INSERT_AUTH_AUDIT_LOG,
    INSERT_LOG_SINCRONIZACION_USUARIO
)
```

**Después:**
```python
from app.infrastructure.database.queries.audit.audit_queries import (
    INSERT_AUTH_AUDIT_LOG,
    INSERT_LOG_SINCRONIZACION_USUARIO
)
```

**Archivo:** `app/infrastructure/database/queries/audit/audit_queries.py`

---

### Refresh Tokens

**Antes:**
```python
from app.infrastructure.database.sql_constants import (
    INSERT_REFRESH_TOKEN,
    GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN,
    REVOKE_REFRESH_TOKEN_BY_USER
)
```

**Después:**
```python
from app.infrastructure.database.queries.auth.auth_queries import (
    INSERT_REFRESH_TOKEN,
    GET_REFRESH_TOKEN_BY_HASH,
    REVOKE_REFRESH_TOKEN,
    REVOKE_REFRESH_TOKEN_BY_USER
)
```

**Nota:** Refresh tokens están en `auth_queries.py` porque pertenecen al dominio de autenticación.

---

## 🔄 Proceso de Migración

### Paso 1: Identificar Imports
```bash
# Buscar todos los imports de sql_constants
python scripts/validate_no_sql_constants_imports.py
```

### Paso 2: Migrar Archivo por Archivo
1. Abrir archivo que importa `sql_constants`
2. Reemplazar import según mapeo arriba
3. Verificar que código compile
4. Ejecutar tests del módulo

### Paso 3: Validar
```bash
# Ejecutar tests de integración
pytest tests/integration -v

# Validar que no haya imports antiguos
python scripts/validate_no_sql_constants_imports.py
```

---

## ⚠️ Notas Importantes

1. **Compatibilidad Híbrida:** Durante FASE 2, ambos imports funcionan. No hay prisa en migrar todo de una vez.

2. **Deprecation Warnings:** `sql_constants.py` mostrará warnings pero no romperá código.

3. **Orden de Migración:** Migrar módulos en este orden:
   - auth (base)
   - users (depende de auth)
   - rbac (depende de users)
   - menus (independiente)
   - audit (depende de auth)

4. **Tests:** Siempre ejecutar tests después de migrar cada archivo.

---

## ✅ Checklist de Migración

- [ ] Identificar todos los imports de `sql_constants` en el módulo
- [ ] Reemplazar imports según mapeo
- [ ] Verificar que código compile sin errores
- [ ] Ejecutar tests del módulo
- [ ] Ejecutar tests de integración
- [ ] Validar con script de validación
- [ ] Actualizar documentación si es necesario

---

## 🆘 Troubleshooting

### Error: "Module not found"
**Solución:** Verificar que el archivo de queries existe en la nueva estructura.

### Error: "Import name not found"
**Solución:** Verificar que la query fue movida al archivo correcto según el mapeo.

### Warning: "DeprecationWarning"
**Solución:** Es normal durante FASE 2. Migrar el import para eliminar el warning.

---

**Última actualización:** Diciembre 2024
