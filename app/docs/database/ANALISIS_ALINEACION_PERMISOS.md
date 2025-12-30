# Análisis de Alineación: Entidades de Permisos vs Tabla `rol_menu_permiso`

## 📋 Resumen Ejecutivo

**Estado:** ❌ **NO COMPLETAMENTE ALINEADO**

Los schemas de permisos (`PermisoBase`, `PermisoRead`, `RolMenuPermisoBase`, `RolMenuPermisoRead`) **NO incluyen todos los campos** definidos en la tabla `rol_menu_permiso` de `estructura_bd.sql`.

---

## 🔍 Comparación Detallada

### Tabla `rol_menu_permiso` (estructura_bd.sql)

```sql
CREATE TABLE rol_menu_permiso (
    permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    menu_id UNIQUEIDENTIFIER NOT NULL,
    
    -- PERMISOS GRANULARES (CRUD extendido)
    puede_ver BIT DEFAULT 1 NOT NULL,
    puede_crear BIT DEFAULT 0,
    puede_editar BIT DEFAULT 0,
    puede_eliminar BIT DEFAULT 0,
    puede_exportar BIT DEFAULT 0,
    puede_imprimir BIT DEFAULT 0,
    puede_aprobar BIT DEFAULT 0,
    
    -- PERMISOS PERSONALIZADOS POR MÓDULO
    permisos_extra NVARCHAR(MAX) NULL,
    
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    
    CONSTRAINT UQ_rol_menu UNIQUE (cliente_id, rol_id, menu_id)
);
```

---

## 📊 Campos por Schema

### 1. `PermisoBase` (app/modules/rbac/presentation/schemas.py:352)

**Campos presentes:**
- ✅ `menu_id` (UUID)
- ✅ `puede_ver` (bool, default=True)
- ✅ `puede_editar` (bool, default=False)
- ✅ `puede_eliminar` (bool, default=False)

**Campos faltantes:**
- ❌ `cliente_id` (UUID, NOT NULL)
- ❌ `rol_id` (UUID, NOT NULL)
- ❌ `puede_crear` (bool, default=False)
- ❌ `puede_exportar` (bool, default=False)
- ❌ `puede_imprimir` (bool, default=False)
- ❌ `puede_aprobar` (bool, default=False)
- ❌ `permisos_extra` (str, nullable)
- ❌ `fecha_creacion` (datetime)
- ❌ `fecha_actualizacion` (datetime, nullable)

**Estado:** ⚠️ **INCOMPLETO** - Solo incluye 3 de los 7 permisos granulares

---

### 2. `PermisoRead` (app/modules/rbac/presentation/schemas.py:389)

**Campos presentes:**
- ✅ Hereda de `PermisoBase` (menu_id, puede_ver, puede_editar, puede_eliminar)
- ✅ `rol_menu_id` (UUID) - Equivale a `permiso_id`
- ✅ `rol_id` (UUID)

**Campos faltantes:**
- ❌ `cliente_id` (UUID, NOT NULL) - **CRÍTICO para multi-tenant**
- ❌ `puede_crear` (bool)
- ❌ `puede_exportar` (bool)
- ❌ `puede_imprimir` (bool)
- ❌ `puede_aprobar` (bool)
- ❌ `permisos_extra` (str)
- ❌ `fecha_creacion` (datetime)
- ❌ `fecha_actualizacion` (datetime)

**Estado:** ⚠️ **INCOMPLETO** - Falta `cliente_id` y permisos extendidos

---

### 3. `RolMenuPermisoBase` (app/modules/rbac/presentation/schemas.py:454)

**Campos presentes:**
- ✅ `rol_id` (UUID)
- ✅ `menu_id` (UUID)
- ✅ `puede_ver` (bool, default=True)
- ✅ `puede_editar` (bool, default=False)
- ✅ `puede_eliminar` (bool, default=False)

**Campos faltantes:**
- ❌ `cliente_id` (UUID, NOT NULL) - **CRÍTICO para multi-tenant**
- ❌ `puede_crear` (bool, default=False)
- ❌ `puede_exportar` (bool, default=False)
- ❌ `puede_imprimir` (bool, default=False)
- ❌ `puede_aprobar` (bool, default=False)
- ❌ `permisos_extra` (str, nullable)
- ❌ `fecha_creacion` (datetime)
- ❌ `fecha_actualizacion` (datetime)

**Estado:** ⚠️ **INCOMPLETO** - Falta `cliente_id` y permisos extendidos

---

### 4. `RolMenuPermisoRead` (app/modules/rbac/presentation/schemas.py:585)

**Campos presentes:**
- ✅ Hereda de `RolMenuPermisoBase` (rol_id, menu_id, puede_ver, puede_editar, puede_eliminar)
- ✅ `rol_menu_id` (UUID) - Equivale a `permiso_id`

**Campos faltantes:**
- ❌ `cliente_id` (UUID, NOT NULL) - **CRÍTICO para multi-tenant**
- ❌ `puede_crear` (bool)
- ❌ `puede_exportar` (bool)
- ❌ `puede_imprimir` (bool)
- ❌ `puede_aprobar` (bool)
- ❌ `permisos_extra` (str)
- ❌ `fecha_creacion` (datetime)
- ❌ `fecha_actualizacion` (datetime)

**Estado:** ⚠️ **INCOMPLETO** - Falta `cliente_id` y permisos extendidos

---

### 5. `RolMenuPermisoUpdate` (app/modules/rbac/presentation/schemas.py:527)

**Campos presentes:**
- ✅ `puede_ver` (Optional[bool])
- ✅ `puede_editar` (Optional[bool])
- ✅ `puede_eliminar` (Optional[bool])

**Campos faltantes:**
- ❌ `puede_crear` (Optional[bool])
- ❌ `puede_exportar` (Optional[bool])
- ❌ `puede_imprimir` (Optional[bool])
- ❌ `puede_aprobar` (Optional[bool])
- ❌ `permisos_extra` (Optional[str])

**Estado:** ⚠️ **INCOMPLETO** - Solo permite actualizar 3 de los 7 permisos granulares

---

## 🚨 Problemas Críticos Identificados

### 1. **Falta `cliente_id` en todos los schemas**
   - **Impacto:** ❌ **CRÍTICO** - Los schemas no reflejan la arquitectura multi-tenant
   - **Riesgo:** No se puede validar ni filtrar permisos por cliente en el nivel de schema
   - **Ubicación:** Todos los schemas de permisos

### 2. **Faltan permisos extendidos**
   - **Campos faltantes:** `puede_crear`, `puede_exportar`, `puede_imprimir`, `puede_aprobar`
   - **Impacto:** ⚠️ **ALTO** - No se pueden gestionar todos los permisos definidos en la BD
   - **Ubicación:** Todos los schemas base

### 3. **Falta campo `permisos_extra`**
   - **Impacto:** ⚠️ **MEDIO** - No se pueden gestionar permisos personalizados por módulo
   - **Ubicación:** Todos los schemas

### 4. **Faltan campos de auditoría**
   - **Campos faltantes:** `fecha_creacion`, `fecha_actualizacion`
   - **Impacto:** ⚠️ **BAJO** - No se pueden mostrar fechas en respuestas de lectura
   - **Ubicación:** Schemas de lectura (`PermisoRead`, `RolMenuPermisoRead`)

---

## ✅ Verificación de Tabla SQLAlchemy

**Tabla:** `RolMenuPermisoTable` (app/infrastructure/database/tables.py:225)

**Estado:** ✅ **COMPLETAMENTE ALINEADA**

La tabla SQLAlchemy incluye todos los campos:
- ✅ `permiso_id`
- ✅ `cliente_id`
- ✅ `rol_id`
- ✅ `menu_id`
- ✅ `puede_ver`
- ✅ `puede_crear`
- ✅ `puede_editar`
- ✅ `puede_eliminar`
- ✅ `puede_exportar`
- ✅ `puede_imprimir`
- ✅ `puede_aprobar`
- ✅ `permisos_extra`
- ✅ `fecha_creacion`

**Nota:** La tabla SQLAlchemy tiene un pequeño problema: el `UniqueConstraint` solo incluye `rol_id` y `menu_id`, pero debería incluir también `cliente_id` según la BD (`UQ_rol_menu UNIQUE (cliente_id, rol_id, menu_id)`).

---

## 📝 Recomendaciones

### Prioridad ALTA (Crítico)

1. **Agregar `cliente_id` a todos los schemas de permisos**
   - `PermisoBase`
   - `PermisoRead`
   - `RolMenuPermisoBase`
   - `RolMenuPermisoRead`
   - `RolMenuPermisoCreate`

2. **Agregar permisos extendidos faltantes**
   - `puede_crear` (bool, default=False)
   - `puede_exportar` (bool, default=False)
   - `puede_imprimir` (bool, default=False)
   - `puede_aprobar` (bool, default=False)

### Prioridad MEDIA

3. **Agregar campo `permisos_extra`**
   - Tipo: `Optional[str]` o `Optional[Dict[str, Any]]`
   - Validación: JSON válido si se proporciona

4. **Agregar campos de auditoría en schemas de lectura**
   - `fecha_creacion` (datetime)
   - `fecha_actualizacion` (Optional[datetime])

### Prioridad BAJA

5. **Corregir `UniqueConstraint` en SQLAlchemy**
   - Incluir `cliente_id` en el constraint único

---

## 🔧 Archivos a Modificar

1. **`app/modules/rbac/presentation/schemas.py`**
   - Actualizar `PermisoBase`
   - Actualizar `PermisoRead`
   - Actualizar `RolMenuPermisoBase`
   - Actualizar `RolMenuPermisoRead`
   - Actualizar `RolMenuPermisoCreate`
   - Actualizar `RolMenuPermisoUpdate`

2. **`app/infrastructure/database/tables.py`**
   - Corregir `UniqueConstraint` en `RolMenuPermisoTable`

3. **Servicios que usan estos schemas** (revisar impacto)
   - `app/modules/rbac/application/services/permiso_service.py`
   - Endpoints que usan estos schemas

---

## 📊 Resumen de Campos por Schema

| Campo | BD | PermisoBase | PermisoRead | RolMenuPermisoBase | RolMenuPermisoRead | RolMenuPermisoUpdate |
|-------|----|-------------|-------------|-------------------|-------------------|---------------------|
| `permiso_id` | ✅ | ❌ | ✅ (rol_menu_id) | ❌ | ✅ (rol_menu_id) | ❌ |
| `cliente_id` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `rol_id` | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| `menu_id` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `puede_ver` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `puede_crear` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `puede_editar` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `puede_eliminar` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `puede_exportar` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `puede_imprimir` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `puede_aprobar` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `permisos_extra` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `fecha_creacion` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `fecha_actualizacion` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Leyenda:**
- ✅ Campo presente
- ❌ Campo faltante
- ⚠️ Campo presente pero con nombre diferente

---

## 🎯 Conclusión

Los schemas de permisos **NO están completamente alineados** con la tabla `rol_menu_permiso`. Se requiere una actualización completa de los schemas para incluir:

1. **Campos críticos faltantes:** `cliente_id` (multi-tenant)
2. **Permisos extendidos:** `puede_crear`, `puede_exportar`, `puede_imprimir`, `puede_aprobar`
3. **Permisos personalizados:** `permisos_extra`
4. **Campos de auditoría:** `fecha_creacion`, `fecha_actualizacion`

La tabla SQLAlchemy está correcta, pero el `UniqueConstraint` necesita incluir `cliente_id`.

