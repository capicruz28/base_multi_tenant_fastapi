# Informe de Análisis: Conexiones a Base de Datos en Endpoints

## 📋 RESUMEN EJECUTIVO

Se analizaron 5 endpoints (`areas.py`, `menus.py`, `roles.py`, `permisos.py`, `usuarios.py`) para identificar diferencias en cómo se conectan a la base de datos. El problema reportado indica que algunos endpoints devuelven datos (areas) mientras otros no (roles).

**Hallazgo Principal:** Todos los endpoints analizados usan el mismo tipo de conexión (`DatabaseConnection.DEFAULT` - tenant-aware), pero hay **inconsistencias en cómo otros servicios del sistema manejan las conexiones**, lo que podría estar afectando indirectamente.

---

## 🔍 ANÁLISIS DETALLADO POR ENDPOINT

### 1. **areas.py** ✅ (FUNCIONA)

**Servicio:** `AreaService`

**Tipo de Conexión:**
- Usa `execute_query()` **sin especificar `connection_type`**
- Por defecto usa `DatabaseConnection.DEFAULT` (tenant-aware)
- **NO usa `DatabaseConnection.ADMIN`**

**Llamadas a BD identificadas:**
```python
# Todas usan DEFAULT (tenant-aware)
execute_query(CHECK_AREA_EXISTS_BY_NAME_QUERY, params)
execute_query(GET_AREA_BY_ID_QUERY, (area_id,))
execute_query(COUNT_AREAS_QUERY, where_params)
execute_query(GET_AREAS_PAGINATED_QUERY, pagination_params)
execute_query(GET_ACTIVE_AREAS_SIMPLE_LIST_QUERY, params)
```

**Filtrado Multi-Tenant:**
- ✅ Todas las queries filtran por `cliente_id`
- ✅ El endpoint pasa `current_user.cliente_id` al servicio

---

### 2. **roles.py** ❌ (NO FUNCIONA)

**Servicio:** `RolService`

**Tipo de Conexión:**
- Usa `execute_query()` **sin especificar `connection_type`**
- Por defecto usa `DatabaseConnection.DEFAULT` (tenant-aware)
- **NO usa `DatabaseConnection.ADMIN`**

**Llamadas a BD identificadas:**
```python
# Todas usan DEFAULT (tenant-aware)
execute_query(QUERY, tuple(role_names))  # get_min_required_access_level
execute_query(GET_USER_MAX_ACCESS_LEVEL, (usuario_id, cliente_id))
execute_query(query, tuple(params))  # crear_rol
execute_query(query, tuple(params))  # actualizar_rol
execute_query(COUNT_ROLES_PAGINATED, count_params)  # obtener_roles_paginados
execute_query(SELECT_ROLES_PAGINATED, select_params)  # obtener_roles_paginados
execute_query(query, (cliente_id,))  # get_all_active_roles
execute_query(SELECT_PERMISOS_POR_ROL, (rol_id,))
```

**Filtrado Multi-Tenant:**
- ✅ La mayoría de queries filtran por `cliente_id`
- ✅ El endpoint pasa `current_user.cliente_id` al servicio
- ⚠️ **PROBLEMA POTENCIAL:** `get_min_required_access_level()` NO filtra por `cliente_id` (busca roles del sistema y del cliente)

**Query Problemática Identificada:**
```python
# Línea 67-70 en rol_service.py
QUERY = f"""
SELECT MIN(nivel_acceso) AS min_level
FROM rol
WHERE nombre IN ({placeholders}) AND es_activo = 1;
"""
```
Esta query **NO filtra por `cliente_id`**, lo que significa que busca roles del sistema Y roles del cliente. Esto podría estar causando problemas si hay roles con el mismo nombre en diferentes clientes.

---

### 3. **menus.py** ✅ (FUNCIONA)

**Servicio:** `MenuService`

**Tipo de Conexión:**
- Usa `execute_query()` **sin especificar `connection_type`**
- Por defecto usa `DatabaseConnection.DEFAULT` (tenant-aware)
- **NO usa `DatabaseConnection.ADMIN`**

**Llamadas a BD identificadas:**
```python
# Todas usan DEFAULT (tenant-aware)
execute_query(SELECT_MENU_BY_ID, (menu_id,))
execute_query(padre_query, (menu_data.padre_menu_id,))
execute_query(area_query, (menu_data.area_id,))
execute_query(max_orden_result, ...)
execute_query(area_info, ...)
execute_query(CHECK_MENU_EXISTS, (menu_id,))
execute_query(GET_MENUS_BY_AREA_FOR_TREE_QUERY, params)
```

**Filtrado Multi-Tenant:**
- ✅ Todas las queries filtran por `cliente_id`
- ✅ El endpoint pasa `current_user.cliente_id` al servicio

---

### 4. **permisos.py** ✅ (FUNCIONA)

**Servicio:** `PermisoService`

**Tipo de Conexión:**
- Usa `execute_query()` **sin especificar `connection_type`**
- Por defecto usa `DatabaseConnection.DEFAULT` (tenant-aware)
- **NO usa `DatabaseConnection.ADMIN`**

**Llamadas a BD identificadas:**
```python
# Todas usan DEFAULT (tenant-aware)
execute_query(check_query, (cliente_id, rol_id, menu_id))
execute_query(get_query, (perm_id,))
execute_query(query, (cliente_id, rol_id))
execute_query(query, (cliente_id, rol_id, menu_id))
```

**Filtrado Multi-Tenant:**
- ✅ Todas las queries filtran por `cliente_id`
- ✅ El endpoint pasa `current_user.cliente_id` al servicio

---

### 5. **usuarios.py** ✅ (FUNCIONA)

**Servicio:** `UsuarioService`

**Tipo de Conexión:**
- Usa `execute_query()` y `execute_auth_query()` **sin especificar `connection_type`**
- Por defecto usa `DatabaseConnection.DEFAULT` (tenant-aware)
- **NO usa `DatabaseConnection.ADMIN`**

**Llamadas a BD identificadas:**
```python
# Todas usan DEFAULT (tenant-aware)
execute_auth_query(query, (usuario_id, cliente_id))
execute_auth_query(query, (usuario_id,))
execute_query(query, params)
execute_query(query, (user_id, cliente_id))
execute_query(query, (usuario_id, cliente_id))
execute_query(COUNT_USUARIOS_PAGINATED, count_params)
execute_query(SELECT_USUARIOS_PAGINATED, data_params)
```

**Filtrado Multi-Tenant:**
- ✅ Todas las queries filtran por `cliente_id`
- ✅ El endpoint pasa `current_user.cliente_id` al servicio

---

## 🔴 PROBLEMAS IDENTIFICADOS

### Problema 1: Query sin Filtro de Cliente en `RolService.get_min_required_access_level()`

**Ubicación:** `app/services/rol_service.py:67-70`

**Descripción:**
La query que obtiene el nivel mínimo requerido de roles **NO filtra por `cliente_id`**:

```python
QUERY = f"""
SELECT MIN(nivel_acceso) AS min_level
FROM rol
WHERE nombre IN ({placeholders}) AND es_activo = 1;
"""
```

**Impacto:**
- Si hay roles con el mismo nombre en diferentes clientes, la query podría devolver el nivel incorrecto
- Podría estar mezclando roles del sistema con roles del cliente sin intención

**Solución Recomendada:**
```python
QUERY = f"""
SELECT MIN(nivel_acceso) AS min_level
FROM rol
WHERE nombre IN ({placeholders}) 
  AND es_activo = 1
  AND (cliente_id = ? OR cliente_id IS NULL);
"""
```

---

### Problema 2: Inconsistencia en Uso de `DatabaseConnection.ADMIN` vs `DEFAULT`

**Descripción:**
Mientras que los endpoints analizados usan `DatabaseConnection.DEFAULT` (tenant-aware), otros servicios del sistema usan `DatabaseConnection.ADMIN` explícitamente:

**Servicios que usan `ADMIN`:**
- `ClienteService` - Todas las queries usan `connection_type=DatabaseConnection.ADMIN`
- `ModuloService` - Todas las queries usan `connection_type=DatabaseConnection.ADMIN`
- `ModuloActivoService` - Todas las queries usan `connection_type=DatabaseConnection.ADMIN`
- `ConexionService` - Todas las queries usan `connection_type=DatabaseConnection.ADMIN`
- `AuthConfigService` - Todas las queries usan `connection_type=DatabaseConnection.ADMIN`

**Servicios que usan `DEFAULT` (tenant-aware):**
- `AreaService` ✅
- `RolService` ⚠️
- `MenuService` ✅
- `PermisoService` ✅
- `UsuarioService` ✅

**Impacto:**
- Si el contexto del tenant no está establecido correctamente, los servicios que usan `DEFAULT` podrían fallar
- Los servicios que usan `ADMIN` siempre se conectan a la BD de administración, que puede no tener los datos del tenant

---

### Problema 3: Posible Falta de Contexto de Tenant

**Descripción:**
Si el middleware `TenantMiddleware` no está estableciendo correctamente el contexto del tenant, los servicios que usan `DatabaseConnection.DEFAULT` podrían:
1. No poder resolver el `cliente_id` del contexto
2. Conectarse a la BD incorrecta
3. Devolver datos vacíos o incorrectos

**Verificación Necesaria:**
- Confirmar que `TenantMiddleware` está activo y funcionando
- Verificar que `get_current_client_id()` devuelve el `cliente_id` correcto
- Revisar logs para ver si hay errores de conexión o contexto

---

## 🔍 ANÁLISIS DE QUERIES EN `RolService.obtener_roles_paginados()`

**Ubicación:** `app/services/rol_service.py:360-409`

**Query de Conteo:**
```python
COUNT_ROLES_PAGINATED = """
SELECT COUNT(*) as total
FROM rol
WHERE (cliente_id = ? OR cliente_id IS NULL)
  AND es_activo = 1
  AND (nombre LIKE ? OR descripcion LIKE ? OR codigo_rol LIKE ?)
"""
```

**Query de Selección:**
```python
SELECT_ROLES_PAGINATED = """
SELECT rol_id, nombre, descripcion, codigo_rol, nivel_acceso, 
       es_activo, cliente_id, fecha_creacion
FROM rol
WHERE (cliente_id = ? OR cliente_id IS NULL)
  AND es_activo = 1
  AND (nombre LIKE ? OR descripcion LIKE ? OR codigo_rol LIKE ?)
ORDER BY cliente_id DESC, nombre ASC
OFFSET ? ROWS
FETCH NEXT ? ROWS ONLY
"""
```

**Análisis:**
- ✅ Las queries SÍ filtran por `cliente_id` (incluyendo roles del sistema con `cliente_id IS NULL`)
- ✅ El ordenamiento prioriza roles del sistema (`ORDER BY cliente_id DESC`)
- ⚠️ **PROBLEMA POTENCIAL:** Si `cliente_id` no se está pasando correctamente, la query podría devolver resultados vacíos

---

## 📊 COMPARACIÓN: ENDPOINTS QUE FUNCIONAN vs NO FUNCIONAN

| Endpoint | Servicio | Conexión | Filtra por cliente_id | Estado |
|----------|----------|----------|----------------------|--------|
| areas.py | AreaService | DEFAULT | ✅ Sí | ✅ Funciona |
| menus.py | MenuService | DEFAULT | ✅ Sí | ✅ Funciona |
| permisos.py | PermisoService | DEFAULT | ✅ Sí | ✅ Funciona |
| usuarios.py | UsuarioService | DEFAULT | ✅ Sí | ✅ Funciona |
| roles.py | RolService | DEFAULT | ⚠️ Parcial | ❌ No funciona |

**Diferencia Clave:**
- `RolService` tiene una query (`get_min_required_access_level`) que **NO filtra por `cliente_id`**
- `RolService.obtener_roles_paginados()` filtra correctamente, pero podría estar recibiendo parámetros incorrectos

---

## 🎯 CAUSAS PROBABLES DEL PROBLEMA

### Causa 1: Parámetros Incorrectos en `obtener_roles_paginados()`

**Hipótesis:**
El método `obtener_roles_paginados()` podría estar recibiendo un `cliente_id` incorrecto o `None`.

**Verificación Necesaria:**
```python
# En roles.py línea 177
paginated_response = await RolService.obtener_roles_paginados(
    cliente_id=current_user.cliente_id,  # ¿Este valor es correcto?
    page=page,
    limit=limit,
    search=search
)
```

### Causa 2: Contexto de Tenant No Establecido

**Hipótesis:**
Si el `TenantMiddleware` no está estableciendo el contexto correctamente, `get_db_connection(DatabaseConnection.DEFAULT)` podría fallar o conectarse a la BD incorrecta.

**Verificación Necesaria:**
- Revisar logs del middleware para ver si está resolviendo el `cliente_id` correctamente
- Verificar que `get_current_client_id()` no lanza `RuntimeError`

### Causa 3: Query Devuelve Resultados Vacíos por Filtros Incorrectos

**Hipótesis:**
La query `SELECT_ROLES_PAGINATED` podría estar devolviendo resultados vacíos porque:
- El `cliente_id` pasado no existe en la BD
- No hay roles activos para ese cliente
- Los parámetros de búsqueda están filtrando todos los resultados

---

## 🔧 RECOMENDACIONES

### Recomendación 1: Corregir Query en `get_min_required_access_level()`

**Acción:**
Agregar filtro por `cliente_id` o roles del sistema:

```python
QUERY = f"""
SELECT MIN(nivel_acceso) AS min_level
FROM rol
WHERE nombre IN ({placeholders}) 
  AND es_activo = 1
  AND (cliente_id = ? OR cliente_id IS NULL);
"""
```

### Recomendación 2: Agregar Logging Detallado

**Acción:**
Agregar logs en `RolService.obtener_roles_paginados()` para verificar:
- El `cliente_id` recibido
- Los parámetros de la query
- El resultado de la query (número de filas)
- El resultado final

### Recomendación 3: Verificar Contexto del Tenant

**Acción:**
Agregar validación en el endpoint para asegurar que `current_user.cliente_id` no sea `None`:

```python
if not current_user.cliente_id:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cliente ID no disponible en el contexto del usuario."
    )
```

### Recomendación 4: Estandarizar Uso de Conexiones

**Acción:**
Decidir si todos los servicios deben usar `DatabaseConnection.DEFAULT` (tenant-aware) o `DatabaseConnection.ADMIN` (BD de administración), y aplicar consistentemente.

**Recomendación:**
- **Datos del tenant** (areas, menus, roles, permisos, usuarios) → `DatabaseConnection.DEFAULT`
- **Datos del sistema** (clientes, módulos, conexiones) → `DatabaseConnection.ADMIN`

---

## 📝 CHECKLIST DE VERIFICACIÓN

Para diagnosticar el problema específico con `roles.py`, verificar:

- [ ] ¿El `current_user.cliente_id` tiene un valor válido cuando se llama al endpoint?
- [ ] ¿La query `SELECT_ROLES_PAGINATED` está devolviendo resultados vacíos?
- [ ] ¿Hay roles activos en la BD para ese `cliente_id`?
- [ ] ¿El contexto del tenant está establecido correctamente por el middleware?
- [ ] ¿Hay errores en los logs relacionados con conexiones a BD?
- [ ] ¿La query `get_min_required_access_level()` está causando problemas?

---

## 🎯 CONCLUSIÓN

**Todos los endpoints analizados usan el mismo tipo de conexión (`DatabaseConnection.DEFAULT`)**, por lo que el problema **NO es el tipo de conexión en sí**, sino probablemente:

1. **Parámetros incorrectos** pasados a las queries
2. **Contexto del tenant no establecido** correctamente
3. **Query sin filtro de cliente** en `get_min_required_access_level()`

**Próximos Pasos:**
1. Agregar logging detallado en `RolService.obtener_roles_paginados()`
2. Verificar que `current_user.cliente_id` tiene un valor válido
3. Corregir la query en `get_min_required_access_level()` para filtrar por cliente
4. Comparar los logs de `areas.py` (que funciona) con `roles.py` (que no funciona) para identificar diferencias

