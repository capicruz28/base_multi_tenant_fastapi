# DIAGNÓSTICO DE ALINEACIÓN: Base de Datos, Schemas, Servicios y Endpoints

## Resumen Ejecutivo

Este documento presenta un análisis detallado de las inconsistencias encontradas entre la estructura de la base de datos (MULTITENANT_SCHEMA.sql) y los schemas Pydantic, servicios y endpoints del backend FastAPI multi-tenant.

**Alcance del análisis:**
- Tabla: `cliente`
- Tabla: `cliente_modulo`
- Tabla: `cliente_modulo_activo`
- Tabla: `cliente_modulo_conexion`

---

## 1. ENTIDAD: CLIENTE

### 1.1 Campos Faltantes en Schemas

#### Campos de la BD NO presentes en `ClienteBase`:

| Campo BD | Tipo BD | Descripción | Impacto |
|----------|---------|-------------|---------|
| `api_key_sincronizacion` | NVARCHAR(255) NULL | API Key para sincronización con servidor central | **ALTO** - No se puede gestionar sincronización |
| `sincronizacion_habilitada` | BIT DEFAULT 0 | Flag para habilitar sincronización bidireccional | **ALTO** - No se puede configurar sincronización |
| `ultima_sincronizacion` | DATETIME NULL | Última vez que se sincronizó | **MEDIO** - No se puede trackear sincronización |

#### Campos presentes en `ClienteRead` pero NO en `ClienteBase`:
- ✅ `fecha_creacion` - Correcto (campo de auditoría)
- ✅ `fecha_actualizacion` - Correcto (campo de auditoría)
- ✅ `fecha_ultimo_acceso` - Correcto (campo de auditoría)

### 1.2 Inconsistencias de Tipos

| Campo | BD | Schema | Estado |
|-------|----|--------|--------|
| `ruc` | NVARCHAR(11) | max_length=15 | ⚠️ **INCONSISTENCIA** - BD permite 11, schema 15 |
| `metadata_json` | NVARCHAR(MAX) | Optional[str] | ✅ Correcto |

### 1.3 Campos Usados en Servicios pero NO en Schemas

**En `cliente_service.py`:**
- ❌ **NO se insertan** los campos de sincronización (`api_key_sincronizacion`, `sincronizacion_habilitada`, `ultima_sincronizacion`)
- ✅ Todos los demás campos están correctamente mapeados

**En queries SELECT:**
- ❌ **NO se consultan** los campos de sincronización
- ✅ Los demás campos están correctamente incluidos

### 1.4 Campos en Endpoints pero NO en Schemas

**En `clientes.py`:**
- ✅ Todos los endpoints usan correctamente los schemas definidos
- ⚠️ **PROBLEMA**: Los endpoints no pueden devolver información de sincronización porque los schemas no la incluyen

### 1.5 Recomendaciones para CLIENTE

1. **Agregar campos de sincronización a `ClienteBase`:**
   ```python
   api_key_sincronizacion: Optional[str] = Field(None, max_length=255, description="API Key para sincronización")
   sincronizacion_habilitada: bool = Field(False, description="Habilita sincronización bidireccional")
   ultima_sincronizacion: Optional[datetime] = Field(None, description="Última sincronización")
   ```

2. **Corregir longitud de RUC:**
   ```python
   ruc: Optional[str] = Field(None, max_length=11, description="RUC del cliente (11 dígitos)")
   ```

3. **Actualizar `ClienteUpdate`** para incluir campos de sincronización

4. **Actualizar `cliente_service.py`** para manejar estos campos en INSERT/UPDATE/SELECT

---

## 2. ENTIDAD: MODULO (cliente_modulo)

### 2.1 Campos Faltantes en Schemas

**Todos los campos de la BD están presentes en `ModuloBase`** ✅

### 2.2 Inconsistencias de Tipos

| Campo | BD | Schema | Estado |
|-------|----|--------|--------|
| `fecha_creacion` | DATETIME | Optional[datetime] | ✅ Correcto (puede ser NULL en BD) |

### 2.3 Campos Usados en Servicios pero NO en Schemas

**En `modulo_service.py`:**
- ✅ Todos los campos están correctamente mapeados
- ✅ Las queries SELECT incluyen todos los campos necesarios

### 2.4 Campos en Endpoints pero NO en Schemas

**En `modulos.py`:**
- ✅ Todos los endpoints usan correctamente los schemas
- ✅ No hay campos faltantes

### 2.5 Recomendaciones para MODULO

**✅ NO SE REQUIEREN CAMBIOS** - La entidad está correctamente alineada.

---

## 3. ENTIDAD: MODULO_ACTIVO (cliente_modulo_activo)

### 3.1 Campos Faltantes en Schemas

**Todos los campos de la BD están presentes en `ModuloActivoBase` o `ModuloActivoRead`** ✅

### 3.2 Inconsistencias de Tipos

| Campo | BD | Schema | Estado |
|-------|----|--------|--------|
| `configuracion_json` | NVARCHAR(MAX) | Optional[Dict[str, Any]] | ⚠️ **INCONSISTENCIA** - BD es string, schema es Dict |
| `fecha_activacion` | DATETIME DEFAULT GETDATE() | datetime en Read | ✅ Correcto |

### 3.3 Campos Usados en Servicios pero NO en Schemas

**En `modulo_activo_service.py`:**

**Línea 204:** 
```python
configuracion_json = json.dumps(modulo_data.configuracion) if modulo_data.configuracion else None
```
- ⚠️ **PROBLEMA**: El servicio usa `modulo_data.configuracion` pero el schema tiene `configuracion_json`
- ⚠️ **PROBLEMA**: El servicio intenta acceder a un campo que no existe en el schema

**Línea 282-284:**
```python
if field == "configuracion":
    update_fields.append("configuracion_json = ?")
    params.append(json.dumps(value))
```
- ⚠️ **PROBLEMA**: El servicio busca `configuracion` pero el schema tiene `configuracion_json`

### 3.4 Campos en Endpoints pero NO en Schemas

**En `modulos.py`:**
- ✅ Los endpoints usan correctamente los schemas
- ⚠️ **PROBLEMA**: El servicio no puede procesar correctamente `configuracion_json` debido a la inconsistencia de nombres

### 3.5 Recomendaciones para MODULO_ACTIVO

1. **Corregir inconsistencia de nombre en servicio:**
   - El schema usa `configuracion_json: Optional[Dict[str, Any]]`
   - El servicio debe usar `modulo_data.configuracion_json` (no `configuracion`)

2. **Manejo correcto de JSON:**
   ```python
   # En activar_modulo:
   configuracion_json = json.dumps(modulo_data.configuracion_json) if modulo_data.configuracion_json else None
   
   # En actualizar_modulo_activo:
   if field == "configuracion_json":
       update_fields.append("configuracion_json = ?")
       params.append(json.dumps(value) if isinstance(value, dict) else value)
   ```

3. **Validar que el schema maneje correctamente la conversión:**
   - El schema acepta `Dict[str, Any]` que es correcto
   - El servicio debe serializar a JSON string antes de guardar en BD
   - El servicio debe deserializar de JSON string a Dict al leer de BD

---

## 4. ENTIDAD: CONEXION (cliente_modulo_conexion)

### 4.1 Campos Faltantes en Schemas

**Todos los campos de la BD están presentes en `ConexionBase` o `ConexionRead`** ✅

### 4.2 Inconsistencias de Tipos

| Campo | BD | Schema | Estado |
|-------|----|--------|--------|
| `usuario_encriptado` | NVARCHAR(500) | str en Read | ✅ Correcto |
| `password_encriptado` | NVARCHAR(500) | str en Read | ✅ Correcto |
| `connection_string_encriptado` | NVARCHAR(MAX) | Optional[str] | ✅ Correcto |

### 4.3 Campos Usados en Servicios pero NO en Schemas

**En `conexion_service.py`:**
- ✅ Todos los campos están correctamente mapeados
- ✅ El servicio maneja correctamente la encriptación de credenciales
- ✅ Las queries SELECT incluyen todos los campos necesarios

### 4.4 Campos en Endpoints pero NO en Schemas

**En `conexiones.py`:**
- ✅ Todos los endpoints usan correctamente los schemas
- ✅ No hay campos faltantes

### 4.5 Recomendaciones para CONEXION

**✅ NO SE REQUIEREN CAMBIOS** - La entidad está correctamente alineada.

---

## 5. RESUMEN DE INCONSISTENCIAS CRÍTICAS

### 5.1 Críticas (Deben corregirse inmediatamente)

1. **CLIENTE - Campos de sincronización faltantes:**
   - `api_key_sincronizacion`
   - `sincronizacion_habilitada`
   - `ultima_sincronizacion`
   - **Impacto**: No se puede gestionar sincronización multi-instalación

2. **MODULO_ACTIVO - Inconsistencia de nombre de campo:**
   - Schema usa `configuracion_json`
   - Servicio busca `configuracion`
   - **Impacto**: El servicio falla al procesar actualizaciones

3. **CLIENTE - Longitud incorrecta de RUC:**
   - BD: NVARCHAR(11)
   - Schema: max_length=15
   - **Impacto**: Puede permitir valores inválidos

### 5.2 Importantes (Deben corregirse pronto)

1. **MODULO_ACTIVO - Manejo de JSON:**
   - El servicio debe validar que `configuracion_json` se serializa/deserializa correctamente
   - **Impacto**: Puede causar errores al guardar/leer configuraciones

### 5.3 Menores (Mejoras recomendadas)

1. **CLIENTE - Validación de campos de sincronización:**
   - Agregar validadores para `api_key_sincronizacion` (formato, longitud)
   - **Impacto**: Mejora la calidad de datos

---

## 6. PROPUESTA DE ESTRUCTURA ESTÁNDAR PARA SCHEMAS

### 6.1 Estructura Recomendada

Para cada entidad, se recomienda tener:

1. **Base Schema** (`*Base`):
   - Todos los campos editables por el usuario
   - Campos de configuración
   - Validaciones básicas
   - **NO incluye**: IDs, campos de auditoría, campos calculados

2. **Create Schema** (`*Create`):
   - Hereda de `*Base`
   - Puede agregar campos específicos para creación
   - **NO incluye**: Campos con valores por defecto de BD

3. **Update Schema** (`*Update`):
   - Todos los campos opcionales
   - Permite actualizaciones parciales
   - **NO incluye**: Campos inmutables (IDs, fechas de creación)

4. **Read Schema** (`*Read`):
   - Hereda de `*Base`
   - Agrega campos de auditoría (IDs, fechas)
   - Campos calculados o derivados
   - **Incluye**: Todos los campos que se pueden leer de la BD

5. **Response Schema** (Opcional):
   - Para respuestas de endpoints específicos
   - Puede incluir datos relacionados (joins)
   - Metadatos adicionales

### 6.2 Ejemplo: Cliente

```python
class ClienteBase(BaseModel):
    """Campos editables y configuración"""
    # Identificación
    codigo_cliente: str
    subdominio: str
    razon_social: str
    # ... otros campos editables ...
    
    # Sincronización (AGREGAR)
    api_key_sincronizacion: Optional[str] = None
    sincronizacion_habilitada: bool = False
    ultima_sincronizacion: Optional[datetime] = None

class ClienteCreate(ClienteBase):
    """Para creación - hereda todo de Base"""
    pass

class ClienteUpdate(BaseModel):
    """Todos los campos opcionales para actualización"""
    codigo_cliente: Optional[str] = None
    # ... todos opcionales ...
    api_key_sincronizacion: Optional[str] = None
    sincronizacion_habilitada: Optional[bool] = None
    ultima_sincronizacion: Optional[datetime] = None

class ClienteRead(ClienteBase):
    """Incluye campos de auditoría"""
    cliente_id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    fecha_ultimo_acceso: Optional[datetime]
```

---

## 7. PROPUESTA DE ESTRUCTURA PARA ENDPOINTS

### 7.1 Estructura Recomendada

1. **GET /{resource}/** - Listar con paginación
   - Response: `Paginated*Response`
   - Query params: `skip`, `limit`, `filters`

2. **GET /{resource}/{id}/** - Obtener por ID
   - Response: `*Read`

3. **POST /{resource}/** - Crear
   - Request: `*Create`
   - Response: `*Read` o `*Response` con mensaje

4. **PUT /{resource}/{id}/** - Actualizar completo
   - Request: `*Update` (todos los campos)
   - Response: `*Read`

5. **PATCH /{resource}/{id}/** - Actualizar parcial
   - Request: `*Update` (campos opcionales)
   - Response: `*Read`

6. **DELETE /{resource}/{id}/** - Eliminar (soft delete)
   - Response: `*DeleteResponse`

### 7.2 Endpoints Especiales

- **GET /{resource}/search/** - Búsqueda avanzada
- **GET /{resource}/{id}/estadisticas/** - Estadísticas
- **POST /{resource}/{id}/accion/** - Acciones específicas (activar, suspender, etc.)

---

## 8. CHECKLIST DE CORRECCIONES

### 8.1 CLIENTE

- [ ] Agregar `api_key_sincronizacion` a `ClienteBase`
- [ ] Agregar `sincronizacion_habilitada` a `ClienteBase`
- [ ] Agregar `ultima_sincronizacion` a `ClienteBase`
- [ ] Corregir `max_length` de `ruc` de 15 a 11
- [ ] Agregar campos de sincronización a `ClienteUpdate`
- [ ] Actualizar `cliente_service.py` para manejar campos de sincronización en INSERT
- [ ] Actualizar `cliente_service.py` para manejar campos de sincronización en UPDATE
- [ ] Actualizar `cliente_service.py` para incluir campos de sincronización en SELECT
- [ ] Agregar validadores para `api_key_sincronizacion`

### 8.2 MODULO_ACTIVO

- [ ] Corregir `modulo_activo_service.py` línea 204: usar `configuracion_json` en lugar de `configuracion`
- [ ] Corregir `modulo_activo_service.py` línea 282: usar `configuracion_json` en lugar de `configuracion`
- [ ] Agregar validación de serialización JSON en el servicio
- [ ] Agregar deserialización JSON al leer de BD en `ModuloActivoRead`

### 8.3 VALIDACIONES GENERALES

- [ ] Verificar que todos los campos de BD tengan correspondencia en schemas
- [ ] Verificar que todos los campos usados en servicios existan en schemas
- [ ] Verificar que todos los tipos coincidan entre BD y schemas
- [ ] Agregar tests unitarios para validar mapeo BD ↔ Schema

---

## 9. NOTAS ADICIONALES

### 9.1 Campos de Auditoría

Los campos de auditoría (`fecha_creacion`, `fecha_actualizacion`, etc.) están correctamente manejados:
- ✅ NO están en `*Base` (no son editables)
- ✅ SÍ están en `*Read` (se pueden leer)
- ✅ Se generan automáticamente en BD

### 9.2 Campos Encriptados

Los campos encriptados (`usuario_encriptado`, `password_encriptado`) están correctamente manejados:
- ✅ NO se exponen en schemas de creación (se usan campos temporales `usuario`, `password`)
- ✅ SÍ se exponen en schemas de lectura (como strings encriptados)
- ✅ El servicio maneja la encriptación/desencriptación correctamente

### 9.3 Campos JSON

Los campos JSON (`configuracion_json`, `metadata_json`, `tema_personalizado`) deben:
- ✅ Aceptar `Dict[str, Any]` en schemas (más amigable para APIs)
- ✅ Serializar a string JSON antes de guardar en BD
- ✅ Deserializar de string JSON a Dict al leer de BD

---

## 10. CONCLUSIÓN

### Estado General: ⚠️ **REQUIERE CORRECCIONES**

**Puntos Positivos:**
- ✅ La mayoría de las entidades están bien alineadas
- ✅ La estructura de schemas sigue buenas prácticas
- ✅ Los servicios manejan correctamente la mayoría de los casos

**Puntos a Mejorar:**
- ⚠️ Faltan campos de sincronización en CLIENTE (crítico)
- ⚠️ Inconsistencia de nombres en MODULO_ACTIVO (crítico)
- ⚠️ Longitud incorrecta de RUC en CLIENTE (importante)

**Prioridad de Correcciones:**
1. **ALTA**: Corregir campos de sincronización en CLIENTE
2. **ALTA**: Corregir inconsistencia de nombres en MODULO_ACTIVO
3. **MEDIA**: Corregir longitud de RUC
4. **BAJA**: Mejoras en validaciones y documentación

---

**Fecha del Diagnóstico:** 2024
**Versión del Schema BD:** Revisión completa de MULTITENANT_SCHEMA.sql
**Versión del Backend:** FastAPI con Pydantic v2



