# ANÁLISIS EXHAUSTIVO: Queries de Servicios vs Schemas en Endpoints

## Metodología

Para cada método de servicio que realiza un SELECT, se compara:
1. Campos devueltos por el query SQL
2. Tipo de retorno del servicio
3. Schema usado en el endpoint correspondiente
4. Campos que se pierden o no se mapean correctamente

---

## 1. ENTIDAD: MODULO

### 1.1 `obtener_modulos()` → `GET /modulos/`

**Query SQL:**
```sql
SELECT modulo_id, codigo_modulo, nombre, descripcion, icono,
       es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
FROM cliente_modulo
```

**Campos devueltos:** 10 campos
- modulo_id, codigo_modulo, nombre, descripcion, icono
- es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion

**Retorno del servicio:** `List[ModuloRead]`

**Schema usado en endpoint:** `PaginatedModuloResponse` → contiene `List[ModuloRead]`

**Campos en ModuloRead:**
- modulo_id ✅
- codigo_modulo ✅
- nombre ✅
- descripcion ✅
- icono ✅
- es_modulo_core ✅
- requiere_licencia ✅
- orden ✅
- es_activo ✅
- fecha_creacion ✅

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 1.2 `obtener_modulo_por_id()` → `GET /modulos/{modulo_id}/`

**Query SQL:**
```sql
SELECT modulo_id, codigo_modulo, nombre, descripcion, icono,
       es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
FROM cliente_modulo WHERE modulo_id = ?
```

**Campos devueltos:** 10 campos (igual que arriba)

**Retorno del servicio:** `Optional[ModuloRead]`

**Schema usado en endpoint:** `ModuloResponse` → contiene `ModuloRead`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 1.3 `obtener_modulo_por_codigo()` → (No tiene endpoint directo)

**Query SQL:**
```sql
SELECT modulo_id, codigo_modulo, nombre, descripcion, icono,
       es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
FROM cliente_modulo WHERE codigo_modulo = ?
```

**Retorno del servicio:** `Optional[ModuloRead]`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 1.4 `obtener_modulos_core()` → (No tiene endpoint directo)

**Query SQL:**
```sql
SELECT modulo_id, codigo_modulo, nombre, descripcion, icono,
       es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
FROM cliente_modulo WHERE es_modulo_core = 1 AND es_activo = 1
```

**Retorno del servicio:** `List[ModuloRead]`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 1.5 `buscar_modulos()` → `GET /modulos/search/`

**Query SQL:**
```sql
SELECT modulo_id, codigo_modulo, nombre, descripcion, icono,
       es_modulo_core, requiere_licencia, orden, es_activo, fecha_creacion
FROM cliente_modulo WHERE ...
```

**Retorno del servicio:** `List[ModuloRead]`

**Schema usado en endpoint:** `PaginatedModuloResponse` → contiene `List[ModuloRead]`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 1.6 `obtener_modulos_por_cliente()` → `GET /clientes/{cliente_id}/modulos/` ⚠️ **PROBLEMA CRÍTICO**

**Query SQL:**
```sql
SELECT 
    m.modulo_id,
    m.codigo_modulo,
    m.nombre,
    m.descripcion,
    m.icono,
    m.es_modulo_core,
    m.requiere_licencia,
    m.orden,
    m.es_activo as modulo_activo,  -- ⚠️ Alias diferente
    m.fecha_creacion,
    ISNULL(cma.esta_activo, 0) as activo_en_cliente,
    cma.cliente_modulo_activo_id,
    cma.fecha_activacion,
    cma.fecha_vencimiento,  -- ⚠️ FALTA en schema
    cma.configuracion_json,
    cma.limite_usuarios,
    cma.limite_registros
FROM cliente_modulo m
LEFT JOIN cliente_modulo_activo cma ON m.modulo_id = cma.modulo_id AND cma.cliente_id = ?
```

**Campos devueltos:** 17 campos
- Del módulo: modulo_id, codigo_modulo, nombre, descripcion, icono, es_modulo_core, requiere_licencia, orden, modulo_activo (alias), fecha_creacion
- De activación: activo_en_cliente, cliente_modulo_activo_id, fecha_activacion, **fecha_vencimiento**, configuracion_json, limite_usuarios, limite_registros

**Retorno del servicio:** `List[Dict[str, Any]]` ⚠️ **PROBLEMA** - Retorna dicts sin tipado

**Schema usado en endpoint:** `ModuloListResponse` → contiene `List[ModuloRead]` ⚠️ **PROBLEMA**

**Campos en ModuloRead (lo que el endpoint intenta usar):**
- modulo_id ✅
- codigo_modulo ✅
- nombre ✅
- descripcion ✅
- icono ✅
- es_modulo_core ✅
- requiere_licencia ✅
- orden ✅
- es_activo ✅ (pero el query devuelve `modulo_activo` como alias)
- fecha_creacion ✅

**Campos que se PIERDEN porque no están en ModuloRead:**
- ❌ `activo_en_cliente` - Se pierde
- ❌ `cliente_modulo_activo_id` - Se pierde
- ❌ `fecha_activacion` - Se pierde
- ❌ `fecha_vencimiento` - Se pierde
- ❌ `configuracion_json` - Se pierde
- ❌ `limite_usuarios` - Se pierde
- ❌ `limite_registros` - Se pierde

**Schema correcto que debería usarse:** `ModuloConInfoActivacion`

**Campos en ModuloConInfoActivacion:**
- Hereda todos de ModuloRead ✅
- activo_en_cliente ✅
- cliente_modulo_activo_id ✅
- fecha_activacion ✅
- **fecha_vencimiento** ❌ **FALTA** - Está en el query pero no en el schema
- configuracion_json ✅ (pero como `Optional[str]`, el query devuelve string JSON)
- limite_usuarios ✅
- limite_registros ✅

**Problemas identificados:**
1. ❌ El servicio retorna `List[Dict[str, Any]]` en lugar de objetos tipados
2. ❌ El endpoint usa `ModuloListResponse` con `List[ModuloRead]` en lugar de `ModuloConInfoActivacion`
3. ❌ El schema `ModuloConInfoActivacion` le falta `fecha_vencimiento`
4. ❌ El query usa alias `modulo_activo` pero `ModuloRead` espera `es_activo`
5. ⚠️ El query devuelve `configuracion_json` como string, pero `ModuloConInfoActivacion` lo define como `Optional[str]` (correcto, pero debería deserializarse)

**Estado:** ❌ **CRÍTICO** - Se pierden 7 campos de información de activación

---

## 2. ENTIDAD: MODULO_ACTIVO

### 2.1 `obtener_modulos_activos_cliente()` → (No tiene endpoint directo, pero se usa internamente)

**Query SQL:**
```sql
SELECT 
    cma.cliente_modulo_activo_id,
    cma.cliente_id,
    cma.modulo_id,
    cma.esta_activo,
    cma.fecha_activacion,
    cma.fecha_vencimiento,
    cma.configuracion_json,  -- String JSON de BD
    cma.limite_usuarios,
    cma.limite_registros,
    cm.nombre as modulo_nombre,
    cm.codigo_modulo,
    cm.descripcion as modulo_descripcion
FROM cliente_modulo_activo cma
INNER JOIN cliente_modulo cm ON cma.modulo_id = cm.modulo_id
```

**Campos devueltos:** 12 campos

**Retorno del servicio:** `List[ModuloActivoRead]`

**Campos en ModuloActivoRead:**
- cliente_modulo_activo_id ✅
- cliente_id ✅
- modulo_id ✅
- esta_activo ✅
- fecha_activacion ✅
- fecha_vencimiento ✅
- configuracion_json ✅ (pero viene como string de BD, schema espera `Dict[str, Any]`)
- limite_usuarios ✅
- limite_registros ✅
- modulo_nombre ✅
- codigo_modulo ✅
- modulo_descripcion ✅

**Problema:** ⚠️ `configuracion_json` viene como string JSON de BD, pero el schema `ModuloActivoRead` lo define como `Optional[Dict[str, Any]]`. El servicio debería deserializar el JSON.

**Estado:** ⚠️ **INCONSISTENCIA DE TIPO** - configuracion_json necesita deserialización

---

### 2.2 `obtener_modulo_activo_por_id()` → (Usado internamente)

**Query SQL:** Igual que arriba (12 campos)

**Retorno del servicio:** `Optional[ModuloActivoRead]`

**Estado:** ⚠️ **MISMO PROBLEMA** - configuracion_json necesita deserialización

---

### 2.3 `obtener_modulo_activo_por_cliente_y_modulo()` → (Usado en endpoints)

**Query SQL:** Igual que arriba (12 campos)

**Retorno del servicio:** `Optional[ModuloActivoRead]`

**Estado:** ⚠️ **MISMO PROBLEMA** - configuracion_json necesita deserialización

---

### 2.4 `activar_modulo()` → `POST /clientes/{cliente_id}/modulos/{modulo_id}/activar/`

**Problema en el servicio (línea 204):**
```python
configuracion_json = json.dumps(modulo_data.configuracion) if modulo_data.configuracion else None
```

**Error:** El schema `ModuloActivoCreate` tiene `configuracion_json: Optional[Dict[str, Any]]`, NO tiene campo `configuracion`.

**Estado:** ❌ **ERROR** - El servicio intenta acceder a `modulo_data.configuracion` que no existe

---

### 2.5 `actualizar_modulo_activo()` → `PUT /clientes/{cliente_id}/modulos/{modulo_id}/`

**Problema en el servicio (línea 282):**
```python
if field == "configuracion":
    update_fields.append("configuracion_json = ?")
    params.append(json.dumps(value))
```

**Error:** El schema `ModuloActivoUpdate` tiene `configuracion_json: Optional[Dict[str, Any]]`, NO tiene campo `configuracion`.

**Estado:** ❌ **ERROR** - El servicio busca `configuracion` pero el schema tiene `configuracion_json`

---

## 3. ENTIDAD: CLIENTE

### 3.1 `obtener_cliente_por_id()` → `GET /clientes/{cliente_id}/`

**Query SQL:**
```sql
SELECT 
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
    favicon_url, color_primario, color_secundario, tema_personalizado,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
FROM cliente WHERE cliente_id = ?
```

**Campos devueltos:** 25 campos

**Campos FALTANTES en el query (presentes en BD pero NO consultados):**
- ❌ `api_key_sincronizacion`
- ❌ `sincronizacion_habilitada`
- ❌ `ultima_sincronizacion`
- ❌ `metadata_json` (aunque se usa en UPDATE, no se consulta en SELECT)

**Retorno del servicio:** `Optional[ClienteRead]`

**Schema usado en endpoint:** `ClienteRead`

**Campos en ClienteRead:**
- Hereda de ClienteBase (todos los campos editables) ✅
- cliente_id ✅
- fecha_creacion ✅
- fecha_actualizacion ✅
- fecha_ultimo_acceso ✅

**Campos que se PIERDEN porque no están en ClienteBase ni ClienteRead:**
- ❌ `api_key_sincronizacion` - No está en schema, no se consulta
- ❌ `sincronizacion_habilitada` - No está en schema, no se consulta
- ❌ `ultima_sincronizacion` - No está en schema, no se consulta
- ❌ `metadata_json` - Está en ClienteBase pero no se consulta en este SELECT

**Estado:** ❌ **CRÍTICO** - Faltan 3 campos de sincronización en query y schema

---

### 3.2 `listar_clientes()` → `GET /clientes/`

**Query SQL:**
```sql
SELECT 
    cliente_id, codigo_cliente, subdominio, razon_social, nombre_comercial, ruc,
    tipo_instalacion, servidor_api_local, modo_autenticacion, logo_url,
    favicon_url, color_primario, color_secundario, tema_personalizado,
    plan_suscripcion, estado_suscripcion, fecha_inicio_suscripcion,
    fecha_fin_trial, contacto_nombre, contacto_email, contacto_telefono,
    es_activo, es_demo, fecha_creacion, fecha_actualizacion, fecha_ultimo_acceso
FROM cliente WHERE ...
```

**Mismos problemas que `obtener_cliente_por_id()`**

**Estado:** ❌ **CRÍTICO** - Faltan 3 campos de sincronización

---

### 3.3 `crear_cliente()` → `POST /clientes/`

**Campos insertados (línea 103-109):**
```python
fields = [
    'codigo_cliente', 'subdominio', 'razon_social', 'nombre_comercial', 'ruc',
    'tipo_instalacion', 'servidor_api_local', 'modo_autenticacion', 'logo_url',
    'favicon_url', 'color_primario', 'color_secundario', 'tema_personalizado',
    'plan_suscripcion', 'estado_suscripcion', 'fecha_inicio_suscripcion',
    'fecha_fin_trial', 'contacto_nombre', 'contacto_email', 'contacto_telefono',
    'es_activo', 'es_demo'
]
```

**Campos FALTANTES en INSERT:**
- ❌ `api_key_sincronizacion` - No se inserta
- ❌ `sincronizacion_habilitada` - No se inserta
- ❌ `ultima_sincronizacion` - No se inserta (correcto, es automático)
- ❌ `metadata_json` - No se inserta (aunque está en ClienteBase)

**Estado:** ❌ **CRÍTICO** - No se pueden crear clientes con configuración de sincronización

---

### 3.4 `actualizar_cliente()` → `PUT /clientes/{cliente_id}/`

**Campos actualizables (línea 350-356):**
```python
campos_actualizables = [
    'codigo_cliente', 'subdominio', 'razon_social', 'nombre_comercial', 'ruc',
    'tipo_instalacion', 'servidor_api_local', 'modo_autenticacion', 'logo_url',
    'favicon_url', 'color_primario', 'color_secundario', 'tema_personalizado',
    'plan_suscripcion', 'estado_suscripcion', 'fecha_inicio_suscripcion',
    'fecha_fin_trial', 'contacto_nombre', 'contacto_email', 'contacto_telefono',
    'es_activo', 'es_demo', 'metadata_json'
]
```

**Campos FALTANTES en UPDATE:**
- ❌ `api_key_sincronizacion` - No se puede actualizar
- ❌ `sincronizacion_habilitada` - No se puede actualizar
- ❌ `ultima_sincronizacion` - No se puede actualizar (correcto, es automático)

**Estado:** ❌ **CRÍTICO** - No se pueden actualizar campos de sincronización

---

## 4. ENTIDAD: CONEXION

### 4.1 `obtener_conexiones_cliente()` → `GET /conexiones/clientes/{cliente_id}/`

**Query SQL:**
```sql
SELECT 
    conexion_id, cliente_id, modulo_id, servidor, puerto, nombre_bd,
    usuario_encriptado, password_encriptado, connection_string_encriptado,
    tipo_bd, usa_ssl, timeout_segundos, max_pool_size,
    es_solo_lectura, es_conexion_principal, es_activo,
    ultima_conexion_exitosa, ultimo_error, fecha_ultimo_error,
    fecha_creacion, fecha_actualizacion, creado_por_usuario_id
FROM cliente_modulo_conexion
```

**Campos devueltos:** 22 campos

**Retorno del servicio:** `List[ConexionRead]`

**Schema usado en endpoint:** `List[ConexionRead]`

**Campos en ConexionRead:**
- Hereda de ConexionBase (campos básicos) ✅
- conexion_id ✅
- usuario_encriptado ✅
- password_encriptado ✅
- connection_string_encriptado ✅
- es_activo ✅
- ultima_conexion_exitosa ✅
- ultimo_error ✅
- fecha_ultimo_error ✅
- fecha_creacion ✅
- fecha_actualizacion ✅
- creado_por_usuario_id ✅

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 4.2 `obtener_conexion_por_id()` → (Usado internamente)

**Query SQL:** Igual que arriba (22 campos)

**Retorno del servicio:** `Optional[ConexionRead]`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

### 4.3 `obtener_conexion_principal()` → `GET /conexiones/clientes/{cliente_id}/modulos/{modulo_id}/principal/`

**Query SQL:** Igual que arriba (22 campos)

**Retorno del servicio:** `Optional[ConexionRead]`

**Schema usado en endpoint:** `Optional[ConexionRead]`

**Estado:** ✅ **CORRECTO** - Todos los campos coinciden

---

## RESUMEN DE PROBLEMAS ENCONTRADOS

### ❌ CRÍTICOS (Deben corregirse inmediatamente)

1. **MODULO - `obtener_modulos_por_cliente()`:**
   - Query devuelve 17 campos (incluyendo info de activación)
   - Servicio retorna `List[Dict[str, Any]]` sin tipado
   - Endpoint usa `ModuloListResponse` con `List[ModuloRead]` (solo 10 campos)
   - **Se pierden 7 campos:** activo_en_cliente, cliente_modulo_activo_id, fecha_activacion, fecha_vencimiento, configuracion_json, limite_usuarios, limite_registros
   - **Solución:** Usar `ModuloConInfoActivacion` y agregar `fecha_vencimiento` al schema

2. **MODULO_ACTIVO - `activar_modulo()`:**
   - Línea 204: `modulo_data.configuracion` → Campo no existe
   - Schema tiene `configuracion_json: Optional[Dict[str, Any]]`
   - **Solución:** Cambiar a `modulo_data.configuracion_json`

3. **MODULO_ACTIVO - `actualizar_modulo_activo()`:**
   - Línea 282: `if field == "configuracion"` → Campo no existe
   - Schema tiene `configuracion_json: Optional[Dict[str, Any]]`
   - **Solución:** Cambiar a `if field == "configuracion_json"`

4. **CLIENTE - Todos los métodos SELECT:**
   - No consultan: `api_key_sincronizacion`, `sincronizacion_habilitada`, `ultima_sincronizacion`
   - Estos campos no están en `ClienteBase` ni `ClienteRead`
   - **Solución:** Agregar campos a schemas y a queries SELECT

5. **CLIENTE - `crear_cliente()`:**
   - No inserta: `api_key_sincronizacion`, `sincronizacion_habilitada`, `metadata_json`
   - **Solución:** Agregar campos a INSERT

6. **CLIENTE - `actualizar_cliente()`:**
   - No actualiza: `api_key_sincronizacion`, `sincronizacion_habilitada`
   - **Solución:** Agregar campos a UPDATE

### ⚠️ IMPORTANTES (Deben corregirse pronto)

1. **MODULO_ACTIVO - Todos los métodos SELECT:**
   - Query devuelve `configuracion_json` como string JSON
   - Schema espera `Optional[Dict[str, Any]]`
   - **Solución:** Deserializar JSON en el servicio antes de crear `ModuloActivoRead`

2. **MODULO - `obtener_modulos_por_cliente()`:**
   - Query usa alias `modulo_activo` pero `ModuloRead` espera `es_activo`
   - **Solución:** Cambiar alias o mapear en el servicio

3. **MODULO_CON_INFO_ACTIVACION:**
   - Le falta campo `fecha_vencimiento` (está en el query)
   - **Solución:** Agregar `fecha_vencimiento: Optional[datetime]`

### ✅ CORRECTOS

- ✅ MODULO - `obtener_modulos()`, `obtener_modulo_por_id()`, `obtener_modulo_por_codigo()`, `obtener_modulos_core()`, `buscar_modulos()`
- ✅ CONEXION - Todos los métodos están correctamente alineados

---

## TABLA COMPARATIVA: Campos del Query vs Schema del Endpoint

| Método Servicio | Endpoint | Campos Query | Campos Schema | Campos Perdidos | Estado |
|----------------|----------|--------------|---------------|-----------------|--------|
| `obtener_modulos()` | `GET /modulos/` | 10 | 10 | 0 | ✅ |
| `obtener_modulo_por_id()` | `GET /modulos/{id}/` | 10 | 10 | 0 | ✅ |
| `obtener_modulos_por_cliente()` | `GET /clientes/{id}/modulos/` | 17 | 10 | **7** | ❌ |
| `obtener_cliente_por_id()` | `GET /clientes/{id}/` | 25 | 25* | **3** | ❌ |
| `listar_clientes()` | `GET /clientes/` | 25 | 25* | **3** | ❌ |
| `obtener_modulos_activos_cliente()` | (interno) | 12 | 12 | 0** | ⚠️ |
| `obtener_conexiones_cliente()` | `GET /conexiones/clientes/{id}/` | 22 | 22 | 0 | ✅ |
| `obtener_conexion_principal()` | `GET /conexiones/.../principal/` | 22 | 22 | 0 | ✅ |

*Nota: Los 25 campos incluyen los que están en ClienteRead, pero faltan 3 de sincronización que no están en el schema ni se consultan.

**Nota: El campo `configuracion_json` viene como string pero el schema espera Dict, necesita deserialización.

---

## CHECKLIST DE CORRECCIONES

### MODULO

- [ ] Agregar `fecha_vencimiento: Optional[datetime]` a `ModuloConInfoActivacion`
- [ ] Cambiar `obtener_modulos_por_cliente()` para retornar `List[ModuloConInfoActivacion]`
- [ ] Cambiar endpoint `GET /clientes/{cliente_id}/modulos/` para usar `ModuloConInfoActivacion`
- [ ] Crear nuevo `ModuloListResponse` con `List[ModuloConInfoActivacion]` o reutilizar existente
- [ ] Mapear alias `modulo_activo` → `es_activo` en el servicio
- [ ] Deserializar `configuracion_json` de string a Dict antes de crear objetos

### MODULO_ACTIVO

- [ ] Corregir línea 204: `modulo_data.configuracion` → `modulo_data.configuracion_json`
- [ ] Corregir línea 282: `if field == "configuracion"` → `if field == "configuracion_json"`
- [ ] Agregar deserialización de `configuracion_json` en todos los métodos SELECT
- [ ] Verificar que `configuracion_json` se serializa correctamente antes de INSERT/UPDATE

### CLIENTE

- [ ] Agregar `api_key_sincronizacion` a `ClienteBase`
- [ ] Agregar `sincronizacion_habilitada` a `ClienteBase`
- [ ] Agregar `ultima_sincronizacion` a `ClienteBase` (o solo a `ClienteRead`)
- [ ] Agregar campos de sincronización a `ClienteUpdate`
- [ ] Agregar campos de sincronización a queries SELECT (`obtener_cliente_por_id`, `listar_clientes`)
- [ ] Agregar campos de sincronización a INSERT (`crear_cliente`)
- [ ] Agregar campos de sincronización a UPDATE (`actualizar_cliente`)
- [ ] Verificar que `metadata_json` se incluye en INSERT/UPDATE

---

## CONCLUSIÓN

**Total de problemas críticos encontrados:** 6
**Total de problemas importantes encontrados:** 3
**Total de métodos correctos:** 8

**El problema más grave es `obtener_modulos_por_cliente()` que pierde 7 campos de información de activación, haciendo que el endpoint no pueda devolver información completa sobre el estado de activación de módulos por cliente.**



