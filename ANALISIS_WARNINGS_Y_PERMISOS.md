# Análisis de Warnings y Problema de Permisos

## 📋 RESUMEN EJECUTIVO

Se identificaron **8 problemas** en total:
- **4 warnings** en `auth.py`
- **3 warnings** en `sso.py`
- **1 warning** en `usuarios.py`
- **1 problema crítico** de permisos que impide el acceso a endpoints

---

## 🔴 PROBLEMA 1: WARNINGS EN `auth.py` (4 warnings)

### Warning 1-2: Función `resolve_cliente_id` no definida (Líneas 797, 895)

**Ubicación:**
- Línea 797: `cliente_id = await resolve_cliente_id(cliente_id, subdominio)`
- Línea 895: `cliente_id = await resolve_cliente_id(cliente_id, subdominio)`

**Problema:**
La función `resolve_cliente_id` no está definida ni importada en el archivo. Se usa en los endpoints SSO (`/sso/azure/` y `/sso/google/`), pero no existe.

**Solución:**
1. **Opción A (Recomendada):** Usar `get_current_client_id()` del contexto, como se hace en el endpoint `/login/` (línea 115).
2. **Opción B:** Crear la función `resolve_cliente_id` que resuelva `cliente_id` desde `subdominio` o use el valor proporcionado.

**Código actual (incorrecto):**
```python
async def sso_azure_login(...):
    cliente_id = await resolve_cliente_id(cliente_id, subdominio)  # ❌ No existe
```

**Código corregido (Opción A):**
```python
async def sso_azure_login(...):
    # Usar el contexto del middleware
    try:
        cliente_id = get_current_client_id()
    except RuntimeError:
        if not cliente_id and not subdominio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere cliente_id o subdominio, o acceso desde subdominio válido."
            )
        # Si se proporciona subdominio, resolverlo
        if subdominio:
            cliente = await ClienteService.obtener_cliente_por_subdominio(subdominio)
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            cliente_id = cliente.cliente_id
```

### Warning 3: `AuthenticationError` no importado (Línea 398)

**Ubicación:**
- Línea 398: `except AuthenticationError:`

**Problema:**
`AuthenticationError` se usa en el bloque `except` pero no está importado.

**Solución:**
Agregar el import o usar `HTTPException` directamente.

**Código actual:**
```python
except AuthenticationError:  # ❌ No importado
    raise HTTPException(...)
```

**Código corregido:**
```python
# AuthenticationError existe en app.core.exceptions
from app.core.exceptions import AuthenticationError

# El código actual está correcto, solo falta el import
except AuthenticationError:  # ✅ Ahora importado
    raise HTTPException(...)
```

---

## 🔴 PROBLEMA 2: WARNINGS EN `sso.py` (3 warnings)

### Warning 1: `BaseModel` no importado (Línea 19)

**Ubicación:**
- Línea 19: `class SSOConfigBase(BaseModel):`

**Problema:**
`BaseModel` se usa pero no está importado de `pydantic`.

**Solución:**
```python
from pydantic import BaseModel
```

### Warning 2: `datetime` no importado (Línea 41)

**Ubicación:**
- Línea 41: `fecha_creacion: datetime`

**Problema:**
`datetime` se usa en el schema pero no está importado.

**Solución:**
```python
from datetime import datetime
```

### Warning 3: Estructura de schemas incorrecta

**Problema:**
Los schemas están definidos dentro del archivo de endpoints, lo cual no es una buena práctica. Deberían estar en `app/schemas/sso.py`.

**Solución recomendada:**
1. Crear `app/schemas/sso.py` con los schemas.
2. Importarlos en `sso.py`.

---

## 🔴 PROBLEMA 3: WARNING EN `usuarios.py` (1 warning)

### Warning: Variable `update_` no definida (Línea 330)

**Ubicación:**
- Línea 330: `if not update_:`

**Problema:**
La variable se llama `update_data` (línea 329), pero se verifica como `update_`.

**Solución:**
```python
# Línea 329-330
update_data = usuario_in.model_dump(exclude_unset=True)
if not update_data:  # ✅ Corregir: update_data en lugar de update_
```

---

## 🔴 PROBLEMA 4: PROBLEMA CRÍTICO DE PERMISOS

### Descripción del Problema

Un usuario con rol **"Administrador"** (nivel 4) no puede acceder a endpoints que requieren **"Super Administrador"** (nivel 5), aunque el sistema de niveles jerárquicos (LBAC) debería permitirlo si el usuario tiene un nivel igual o superior.

**Mensaje de error:**
```
Acceso denegado para usuario 'admin_tech'. 
Roles del usuario: ['Administrador']. 
Nivel Máximo: 4. 
Roles requeridos: ['Super Administrador']. 
Nivel Mínimo Requerido: 5
```

**Endpoints afectados:**
- `GET /api/v1/roles/` - Requiere "Super Administrador"
- `GET /api/v1/usuarios/` - Requiere "Administrador" (este sí funciona)

### Análisis de la Causa Raíz

#### 1. **Problema en `RolService.get_user_max_access_level()`**

**Ubicación:** `app/services/rol_service.py:95`

**Problema:**
El método `get_user_max_access_level()` **NO recibe `cliente_id`** como parámetro, pero la query `GET_USER_MAX_ACCESS_LEVEL` en `app/db/queries.py:238` **SÍ requiere `cliente_id`** como segundo parámetro.

**Código actual (incorrecto):**
```python
# app/services/rol_service.py:95
async def get_user_max_access_level(usuario_id: int) -> int:
    QUERY = """
    SELECT MAX(r.nivel_acceso) AS max_level
    FROM usuario_rol ur
    JOIN rol r ON ur.rol_id = r.rol_id
    WHERE ur.usuario_id = ? AND r.es_activo = 1;
    """
    result = execute_query(QUERY, (usuario_id,))  # ❌ Solo pasa usuario_id
```

**Query esperada (en queries.py):**
```python
GET_USER_MAX_ACCESS_LEVEL = """
SELECT ISNULL(MAX(r.nivel_acceso), 1) as max_level
FROM usuario_rol ur
INNER JOIN rol r ON ur.rol_id = r.rol_id
WHERE ur.usuario_id = ? 
  AND ur.es_activo = 1
  AND r.es_activo = 1
  AND (r.cliente_id = ? OR r.cliente_id IS NULL)  -- ❌ Requiere cliente_id
"""
```

#### 2. **Problema en `RoleChecker.__call__()`**

**Ubicación:** `app/api/deps.py:326`

**Problema:**
Cuando se llama a `get_user_max_access_level()`, no se pasa el `cliente_id` del usuario actual, aunque está disponible en `current_user.cliente_id`.

**Código actual (incorrecto):**
```python
# app/api/deps.py:326
user_max_level = await RolService.get_user_max_access_level(user_id)  # ❌ Falta cliente_id
```

**Código corregido:**
```python
user_max_level = await RolService.get_user_max_access_level(
    usuario_id=user_id,
    cliente_id=current_user.cliente_id  # ✅ Agregar cliente_id
)
```

#### 3. **Inconsistencia en la Query**

La query en `rol_service.py` no filtra por `cliente_id`, pero la query en `queries.py` sí lo hace. Esto causa que:
- El método no respete el contexto multi-tenant.
- Pueda devolver niveles de roles de otros clientes.

### Solución Propuesta

#### Paso 1: Corregir `RolService.get_user_max_access_level()`

```python
@staticmethod
async def get_user_max_access_level(usuario_id: int, cliente_id: int) -> int:
    """
    Consulta el nivel de acceso más alto (MAX) entre todos los roles asignados al usuario.
    
    Args:
        usuario_id: ID del usuario.
        cliente_id: ID del cliente (tenant) para filtrar roles.
    
    Returns:
        El nivel de acceso más alto que posee el usuario (int), o 1 si no tiene roles activos.
    """
    # Usar la query correcta que filtra por cliente_id
    from app.db.queries import execute_query, GET_USER_MAX_ACCESS_LEVEL
    
    try:
        result = execute_query(GET_USER_MAX_ACCESS_LEVEL, (usuario_id, cliente_id))
        
        if result and result[0]['max_level'] is not None:
            return int(result[0]['max_level'])
        
        # Si no tiene roles activos, nivel mínimo
        return 1
        
    except DatabaseError as db_err:
        logger.error(f"Error de BD en get_user_max_access_level: {db_err.detail}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail="Error de base de datos al obtener nivel máximo del usuario.",
            internal_code="USER_LEVEL_DB_ERROR"
        )
```

#### Paso 2: Corregir `RoleChecker.__call__()`

```python
# app/api/deps.py:326
user_max_level = await RolService.get_user_max_access_level(
    usuario_id=user_id,
    cliente_id=current_user.cliente_id  # ✅ Agregar cliente_id
)
```

#### Paso 3: Verificar Niveles de Roles en BD

Asegurarse de que los roles tengan los niveles correctos:
- **"Super Administrador"**: `nivel_acceso = 5`
- **"Administrador"**: `nivel_acceso = 4`

**Query de verificación:**
```sql
SELECT nombre, nivel_acceso, codigo_rol, cliente_id
FROM rol
WHERE nombre IN ('Super Administrador', 'Administrador')
ORDER BY nivel_acceso DESC;
```

### Nota Importante sobre el Comportamiento Esperado

Según el sistema LBAC (Level-Based Access Control):
- Un usuario con nivel **N** puede acceder a recursos que requieren nivel **M** si **N >= M**.
- Un usuario con nivel **4** (Administrador) **NO puede** acceder a recursos que requieren nivel **5** (Super Administrador).
- Esto es **comportamiento correcto** desde el punto de vista de seguridad.

**Sin embargo, el problema reportado indica que:**
- El usuario tiene rol "Administrador" (nivel 4).
- El endpoint `/api/v1/roles/` requiere "Super Administrador" (nivel 5).
- El endpoint `/api/v1/usuarios/` requiere "Administrador" (nivel 4) y **SÍ funciona**.

**Esto sugiere que:**
1. El sistema de permisos está funcionando correctamente (nivel 4 < nivel 5 = acceso denegado).
2. **PERO** el problema real es que `get_user_max_access_level()` no está filtrando por `cliente_id`, lo que puede causar que:
   - Se calculen niveles incorrectos en entornos multi-tenant.
   - Se incluyan roles de otros clientes en el cálculo.

**Si el usuario "Administrador" debe acceder a estos endpoints:**
1. **Opción A:** Cambiar el nivel del rol "Administrador" a 5 (no recomendado por seguridad).
2. **Opción B:** Cambiar los endpoints para requerir nivel 4 en lugar de 5.
3. **Opción C:** Asignar el rol "Super Administrador" al usuario.
4. **Opción D:** Verificar que el endpoint `/api/v1/roles/` realmente deba requerir nivel 5, o si debería requerir nivel 4.

---

## 📝 RESUMEN DE CORRECCIONES NECESARIAS

### `auth.py` (4 correcciones)
1. ✅ Línea 797: Reemplazar `resolve_cliente_id()` con `get_current_client_id()` o crear la función.
2. ✅ Línea 895: Reemplazar `resolve_cliente_id()` con `get_current_client_id()` o crear la función.
3. ✅ Línea 398: Importar `AuthenticationError` o usar `HTTPException` directamente.

### `sso.py` (3 correcciones)
1. ✅ Línea 19: Agregar `from pydantic import BaseModel`
2. ✅ Línea 41: Agregar `from datetime import datetime`
3. ⚠️ **Opcional:** Mover schemas a `app/schemas/sso.py` (mejora de arquitectura)

### `usuarios.py` (1 corrección)
1. ✅ Línea 330: Cambiar `if not update_:` por `if not update_data:`

### Problema de Permisos (2 correcciones críticas)
1. ✅ `RolService.get_user_max_access_level()`: Agregar parámetro `cliente_id` y usar query correcta.
2. ✅ `RoleChecker.__call__()`: Pasar `cliente_id` al llamar `get_user_max_access_level()`.

---

## ⚠️ NOTA SOBRE EL PROBLEMA DE PERMISOS

El mensaje de error indica que un usuario con nivel **4** intenta acceder a un recurso que requiere nivel **5**. Esto es **comportamiento esperado** del sistema de seguridad. 

**Si el usuario "Administrador" debe tener acceso a estos endpoints:**
- Verificar que el rol "Administrador" tenga `nivel_acceso = 4` (correcto).
- Verificar que los endpoints requieran nivel 4, no 5.
- O asignar el rol "Super Administrador" al usuario.

**El problema real es que `get_user_max_access_level()` no está filtrando correctamente por `cliente_id`, lo que puede causar resultados incorrectos en un entorno multi-tenant.**

