# 📋 INFORME: Análisis de Usuarios y Menús - SuperAdmin vs Tenant

**Fecha:** 2025-11-24  
**Objetivo:** Verificar la correcta identificación y manejo de usuarios SuperAdmin vs Tenant en los endpoints `usuarios.py` y `menus.py`

---

## 🔍 RESUMEN EJECUTIVO

Se identificaron **5 problemas críticos** y **3 mejoras recomendadas** que afectan la seguridad y el aislamiento multi-tenant:

1. ❌ **CRÍTICO**: `MenuService.obtener_menu_por_id()` no acepta `cliente_id` pero el endpoint lo pasa
2. ❌ **CRÍTICO**: `RolRead` creado sin `cliente_id` ni `codigo_rol` en `usuario_service.py`
3. ❌ **CRÍTICO**: Falta validación de `cliente_id` en `obtener_menu_por_id()` permitiendo acceso cruzado
4. ⚠️ **MEDIO**: Falta normalización de roles en `get_usuarios_paginated()` similar a `rol_service.py`
5. ⚠️ **MEDIO**: Inconsistencia en validación de menús del sistema vs tenant

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. ❌ **ERROR DE ARGUMENTOS: `obtener_menu_por_id()` no acepta `cliente_id`**

**Ubicación:**
- **Endpoint:** `app/api/v1/endpoints/menus.py:260`
- **Servicio:** `app/services/menu_service.py:155`

**Problema:**
```python
# ❌ ENDPOINT (menus.py:260) - PASA cliente_id
menu = await MenuService.obtener_menu_por_id(menu_id=menu_id, cliente_id=current_user.cliente_id)

# ❌ SERVICIO (menu_service.py:155) - NO ACEPTA cliente_id
async def obtener_menu_por_id(menu_id: int) -> Optional[MenuReadSingle]:
```

**Impacto:**
- ❌ **Error en tiempo de ejecución**: `TypeError: obtener_menu_por_id() got an unexpected keyword argument 'cliente_id'`
- ❌ **Falla en múltiples endpoints**: `get_menu_by_id_endpoint`, `update_menu_endpoint`, `deactivate_menu_endpoint`, `reactivate_menu_endpoint`

**Solución:**
1. Agregar parámetro `cliente_id: Optional[int] = None` al método `obtener_menu_por_id()`
2. Filtrar por `cliente_id` en la query si se proporciona
3. Permitir acceso a menús del sistema (`cliente_id IS NULL`) solo para SUPER_ADMIN

---

### 2. ❌ **VALIDACIÓN DE SEGURIDAD: Falta filtro por `cliente_id` en `obtener_menu_por_id()`**

**Ubicación:**
- **Servicio:** `app/services/menu_service.py:155-199`

**Problema:**
```python
# ❌ ACTUAL: No filtra por cliente_id, permite acceso a cualquier menú
async def obtener_menu_por_id(menu_id: int) -> Optional[MenuReadSingle]:
    resultado = execute_query(SELECT_MENU_BY_ID, (menu_id,))
    # ⚠️ Cualquier tenant puede acceder a menús de otros tenants o del sistema
```

**Impacto:**
- ❌ **Vulnerabilidad de seguridad**: Un tenant puede acceder a menús de otros tenants
- ❌ **Falta de aislamiento multi-tenant**: No se respeta el contexto del cliente
- ❌ **Acceso no autorizado**: Tenants pueden ver/editar menús del sistema sin ser SUPER_ADMIN

**Solución:**
1. Agregar filtro por `cliente_id` en la query
2. Permitir acceso a menús del sistema (`cliente_id IS NULL`) solo si el usuario es SUPER_ADMIN
3. Validar que el menú pertenezca al cliente o sea del sistema (con permisos)

---

### 3. ❌ **ERROR DE VALIDACIÓN: `RolRead` creado sin campos requeridos**

**Ubicación:**
- **Servicio:** `app/services/usuario_service.py:1246-1252`

**Problema:**
```python
# ❌ ACTUAL: Crea RolRead sin cliente_id ni codigo_rol
rol_obj = RolRead(
    rol_id=row['rol_id'],
    nombre=row['nombre_rol'],
    descripcion=None,
    es_activo=True,
    fecha_creacion=datetime.now()
    # ⚠️ FALTAN: cliente_id, codigo_rol
)
```

**Impacto:**
- ❌ **Error de validación Pydantic**: Similar al problema corregido en `rol_service.py`
- ❌ **Inconsistencia de datos**: Los roles no tienen información completa
- ❌ **Posible fallo en serialización**: El schema `RolRead` puede requerir estos campos

**Solución:**
1. Obtener `cliente_id` y `codigo_rol` de la query `SELECT_USUARIOS_PAGINATED`
2. Incluir estos campos al crear `RolRead`
3. Aplicar normalización similar a `RolService._normalizar_rol_dict()` si es necesario

---

## ⚠️ PROBLEMAS MEDIOS IDENTIFICADOS

### 4. ⚠️ **FALTA NORMALIZACIÓN: Roles en `get_usuarios_paginated()`**

**Ubicación:**
- **Servicio:** `app/services/usuario_service.py:1244-1256`

**Problema:**
- No se aplica normalización de roles similar a la implementada en `RolService._normalizar_rol_dict()`
- Si un rol tiene `codigo_rol` pero `cliente_id != 1`, causará error de validación

**Solución:**
- Aplicar la misma función de normalización que en `rol_service.py`
- O reutilizar `RolService._normalizar_rol_dict()` si es posible

---

### 5. ⚠️ **INCONSISTENCIA: Validación de menús del sistema**

**Ubicación:**
- **Endpoint:** `app/api/v1/endpoints/menus.py:266-269, 343-344, 408-409, 468-469`

**Problema:**
- La validación de acceso a menús del sistema se hace en el endpoint, pero no en el servicio
- Inconsistente: algunos endpoints validan, otros no
- La función `_can_manage_system_menu()` verifica `"SUPER_ADMIN"` pero debería verificar `codigo_rol`

**Solución:**
1. Mover la validación al servicio `MenuService.obtener_menu_por_id()`
2. Verificar `codigo_rol` en lugar de nombre del rol
3. Centralizar la lógica de validación

---

## ✅ ASPECTOS CORRECTOS IDENTIFICADOS

### 1. ✅ **Aislamiento Multi-Tenant en Endpoints de Usuarios**
- ✅ Todos los endpoints de `usuarios.py` pasan correctamente `current_user.cliente_id`
- ✅ Los servicios validan que los usuarios pertenezcan al cliente correcto
- ✅ Las queries filtran por `cliente_id` correctamente

### 2. ✅ **Validación de Permisos en Menús**
- ✅ Los endpoints validan acceso a menús del sistema con `_can_manage_system_menu()`
- ✅ Se previene desactivación/reactivación de menús del sistema
- ✅ Se valida que el menú pertenezca al cliente antes de operaciones

### 3. ✅ **Estructura de Queries**
- ✅ Las queries de usuarios incluyen `cliente_id` en los filtros
- ✅ Las queries de menús respetan el contexto multi-tenant

---

## 📝 RECOMENDACIONES DE CORRECCIÓN

### Prioridad ALTA (Críticos)

1. **Corregir firma de `obtener_menu_por_id()`**
   ```python
   # ✅ CORRECTO
   async def obtener_menu_por_id(
       menu_id: int, 
       cliente_id: Optional[int] = None
   ) -> Optional[MenuReadSingle]:
   ```

2. **Agregar filtro por `cliente_id` en query**
   ```python
   # ✅ CORRECTO
   if cliente_id is not None:
       query = """
       SELECT ... FROM menu 
       WHERE menu_id = ? 
         AND (cliente_id = ? OR cliente_id IS NULL)
       """
       params = (menu_id, cliente_id)
   else:
       query = "SELECT ... FROM menu WHERE menu_id = ?"
       params = (menu_id,)
   ```

3. **Corregir creación de `RolRead` en `usuario_service.py`**
   ```python
   # ✅ CORRECTO
   rol_obj = RolRead(
       rol_id=row['rol_id'],
       nombre=row['nombre_rol'],
       descripcion=row.get('descripcion_rol'),
       es_activo=bool(row.get('rol_es_activo', True)),
       fecha_creacion=row.get('rol_fecha_creacion', datetime.now()),
       cliente_id=row.get('rol_cliente_id'),  # ✅ AGREGAR
       codigo_rol=row.get('rol_codigo_rol')   # ✅ AGREGAR
   )
   # ✅ Aplicar normalización
   rol_dict = rol_obj.model_dump()
   rol_normalizado = RolService._normalizar_rol_dict(rol_dict)
   rol_obj = RolRead(**rol_normalizado)
   ```

### Prioridad MEDIA (Mejoras)

4. **Centralizar validación de menús del sistema**
   - Mover validación al servicio
   - Usar `codigo_rol` en lugar de nombre del rol
   - Reutilizar lógica de `RolService` para verificar SUPER_ADMIN

5. **Aplicar normalización de roles en `usuario_service.py`**
   - Reutilizar `RolService._normalizar_rol_dict()`
   - Asegurar consistencia en toda la aplicación

---

## 🔧 ARCHIVOS A MODIFICAR

### Archivos Críticos (Prioridad ALTA)
1. ✅ `app/services/menu_service.py` - Corregir `obtener_menu_por_id()`
2. ✅ `app/services/usuario_service.py` - Corregir creación de `RolRead`
3. ✅ `app/db/queries.py` - Verificar/actualizar `SELECT_MENU_BY_ID` si es necesario

### Archivos de Mejora (Prioridad MEDIA)
4. ⚠️ `app/api/v1/endpoints/menus.py` - Centralizar validación (opcional)
5. ⚠️ `app/services/usuario_service.py` - Aplicar normalización de roles (opcional)

---

## 📊 IMPACTO ESPERADO

### Después de las Correcciones

✅ **Seguridad:**
- Aislamiento completo multi-tenant
- Prevención de acceso no autorizado a menús de otros tenants
- Validación consistente de permisos SUPER_ADMIN

✅ **Estabilidad:**
- Eliminación de errores de argumentos en tiempo de ejecución
- Eliminación de errores de validación Pydantic
- Consistencia en el manejo de datos

✅ **Mantenibilidad:**
- Código más consistente entre servicios
- Reutilización de funciones de normalización
- Validaciones centralizadas

---

## ⚠️ NOTAS IMPORTANTES

1. **Compatibilidad con Menús del Sistema:**
   - Los menús del sistema tienen `cliente_id IS NULL`
   - Solo SUPER_ADMIN puede acceder a estos menús
   - Los tenants solo pueden acceder a sus propios menús

2. **Compatibilidad con Roles del Sistema:**
   - Los roles del sistema tienen `codigo_rol` y `cliente_id IS NULL` o `cliente_id = 1`
   - La normalización ya implementada en `rol_service.py` debe aplicarse también aquí

3. **Testing Recomendado:**
   - Probar acceso a menús de otros tenants (debe fallar)
   - Probar acceso a menús del sistema como tenant (debe fallar)
   - Probar acceso a menús del sistema como SUPER_ADMIN (debe funcionar)
   - Probar listado de usuarios con roles (debe funcionar sin errores)

---

## ✅ CONCLUSIÓN

Se identificaron **5 problemas** que requieren corrección:
- **3 críticos** que causan errores en tiempo de ejecución o vulnerabilidades de seguridad
- **2 medios** que afectan la consistencia y mantenibilidad

**Recomendación:** Proceder con las correcciones de prioridad ALTA primero, luego evaluar las mejoras de prioridad MEDIA.

---

**Generado por:** Análisis automatizado  
**Revisado:** Pendiente de aprobación del usuario

