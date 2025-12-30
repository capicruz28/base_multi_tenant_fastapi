# Flujo Completo del Endpoint de Roles Paginados

## 📋 Resumen del Flujo

```
GET /api/v1/roles/
    ↓
Endpoint: read_roles_paginated (app/modules/rbac/presentation/endpoints.py)
    ↓
Servicio: RolService.obtener_roles_paginados (app/modules/rbac/application/services/rol_service.py)
    ↓
Query: SELECT_ROLES_PAGINATED (app/infrastructure/database/queries.py)
    ↓
Respuesta: Lista paginada de roles del cliente
```

## 🔍 Detalle del Flujo

### 1. **Endpoint** (`app/modules/rbac/presentation/endpoints.py`)

**Ruta:** `GET /api/v1/roles/`

**Línea:** 133-210

**Función:** `read_roles_paginated`

**Parámetros:**
- `page`: Número de página (default: 1)
- `limit`: Límite de resultados por página (default: 10)
- `search`: Término de búsqueda opcional

**Validaciones:**
- Verifica que `current_user.cliente_id` sea válido
- Verifica que no sea UUID nulo

**Llamada al servicio:**
```python
paginated_response = await RolService.obtener_roles_paginados(
    cliente_id=current_user.cliente_id,
    page=page,
    limit=limit,
    search=search
)
```

---

### 2. **Servicio** (`app/modules/rbac/application/services/rol_service.py`)

**Método:** `obtener_roles_paginados`

**Línea:** 412-617

**Parámetros:**
- `cliente_id`: UUID del cliente
- `page`: Número de página
- `limit`: Límite de resultados
- `search`: Término de búsqueda opcional

**Lógica:**

1. **Validación de parámetros:**
   - Verifica que `page >= 1`
   - Verifica que `limit >= 1`
   - Verifica que `cliente_id` sea válido

2. **Determinación del tipo de BD:**
   ```python
   tenant_context = try_get_tenant_context()
   database_type = tenant_context.database_type if tenant_context else "single"
   ```

3. **Conteo de roles:**
   - **BD Dedicada (multi):** No filtra por `cliente_id` (todos los roles pertenecen al mismo tenant)
   - **BD Compartida (single):** Filtra SOLO por `cliente_id` (NO incluye roles del sistema)

4. **Obtención de roles:**
   - Usa `SELECT_ROLES_PAGINATED` para BD compartida
   - Usa query inline para BD dedicada

5. **Procesamiento:**
   - Convierte cada rol a `RolRead` usando Pydantic
   - Retorna diccionario con metadatos de paginación

---

### 3. **Query SQL** (`app/infrastructure/database/queries.py`)

**Query:** `SELECT_ROLES_PAGINATED`

**Línea:** 755-769

**SQL Actualizado (después de la corrección):**
```sql
SELECT
    rol_id, nombre, descripcion, es_activo, fecha_creacion, cliente_id, codigo_rol
FROM
    dbo.rol
WHERE 
    cliente_id = ?  -- ✅ SOLO roles del cliente (NO incluye roles del sistema)
    AND (? IS NULL OR (
        LOWER(nombre) LIKE LOWER(?) OR
        LOWER(descripcion) LIKE LOWER(?)
    ))
ORDER BY
    rol_id 
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
```

**Query de Conteo:** `COUNT_ROLES_PAGINATED`

**Línea:** 744-753

**SQL Actualizado:**
```sql
SELECT COUNT(rol_id) as total 
FROM dbo.rol
WHERE 
    cliente_id = ?  -- ✅ SOLO roles del cliente (NO incluye roles del sistema)
    AND (? IS NULL OR (
        LOWER(nombre) LIKE LOWER(?) OR
        LOWER(descripcion) LIKE LOWER(?)
    ));
```

---

## ✅ Corrección Aplicada

### **Problema Identificado:**

La query original incluía roles del sistema (`cliente_id IS NULL`) incluso cuando el cliente no tenía roles propios:

```sql
WHERE (cliente_id IS NULL OR cliente_id = ?)
```

Esto causaba que:
- Clientes sin roles propios veían roles del sistema
- Se forzaba el `cliente_id` del tenant en roles del sistema que no pertenecían a ese cliente

### **Solución Implementada:**

1. **Query actualizada:** Ahora filtra SOLO por `cliente_id = ?` (sin incluir roles del sistema)
2. **Servicio simplificado:** Eliminada la lógica de forzar `cliente_id` en roles del sistema
3. **Comportamiento esperado:**
   - Si el cliente tiene roles propios → muestra solo esos roles
   - Si el cliente NO tiene roles propios → muestra lista vacía `[]`

---

## 📊 Comparación con Endpoint de Usuarios

### **Endpoint de Usuarios** (`GET /api/v1/usuarios/`)

**Query:** `SELECT_USUARIOS_PAGINATED`

**Comportamiento:**
- Filtra SOLO por `u.cliente_id = ?`
- NO incluye usuarios de otros clientes
- Si el cliente no tiene usuarios → lista vacía

**Diferencia clave:**
- Los usuarios siempre pertenecen a un cliente específico
- Los roles pueden ser del sistema (`cliente_id IS NULL`) o del cliente (`cliente_id = ?`)

---

## 🎯 Comportamiento Esperado Después de la Corrección

### **Caso 1: Cliente con roles propios**
```json
{
  "roles": [
    {
      "rol_id": "...",
      "nombre": "Rol del Cliente",
      "cliente_id": "3d34486f-05a9-4acb-8590-f76cde7a748a",
      ...
    }
  ],
  "total_roles": 1,
  "pagina_actual": 1,
  "total_paginas": 1
}
```

### **Caso 2: Cliente sin roles propios**
```json
{
  "roles": [],
  "total_roles": 0,
  "pagina_actual": 1,
  "total_paginas": 0
}
```

---

## 🔧 Archivos Modificados

1. **`app/infrastructure/database/queries.py`**
   - `COUNT_ROLES_PAGINATED`: Removido `(cliente_id IS NULL OR ...)`
   - `SELECT_ROLES_PAGINATED`: Removido `(cliente_id IS NULL OR ...)`

2. **`app/modules/rbac/application/services/rol_service.py`**
   - `obtener_roles_paginados`: Simplificada lógica de procesamiento
   - Eliminada lógica de forzar `cliente_id` en roles del sistema

3. **`app/modules/rbac/presentation/endpoints.py`**
   - `read_roles_paginated`: Cambiado `response_model` a `dict` para evitar validación estricta

---

## 📝 Notas Importantes

1. **Roles del Sistema:** Los roles del sistema (`cliente_id IS NULL`) ya NO se muestran en el endpoint de roles paginados. Si necesitas acceder a ellos, deberás crear un endpoint específico para administración global.

2. **BD Dedicada:** En BD dedicadas (multi-DB), todos los roles pertenecen al mismo tenant, por lo que no se filtra por `cliente_id`.

3. **BD Compartida:** En BD compartidas (single-DB), ahora solo se muestran roles del cliente específico.

4. **Consistencia:** El comportamiento ahora es consistente con el endpoint de usuarios, donde solo se muestran entidades del cliente actual.

