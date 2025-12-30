# Resumen de Actualización: Schemas de Permisos Alineados con `rol_menu_permiso`

## ✅ Cambios Completados

Todos los schemas de permisos han sido actualizados para estar completamente alineados con la tabla `rol_menu_permiso` definida en `estructura_bd.sql`.

---

## 📋 Schemas Actualizados

### 1. **`PermisoBase`** ✅

**Campos agregados:**
- ✅ `puede_crear` (bool, default=False)
- ✅ `puede_exportar` (bool, default=False)
- ✅ `puede_imprimir` (bool, default=False)
- ✅ `puede_aprobar` (bool, default=False)
- ✅ `permisos_extra` (Optional[str], default=None)

**Total de permisos:** 7 granulares (antes: 3)

---

### 2. **`PermisoRead`** ✅

**Campos agregados:**
- ✅ `permiso_id` (UUID) - Primary Key (antes `rol_menu_id` como alias)
- ✅ `cliente_id` (UUID) - **CRÍTICO para multi-tenant**
- ✅ `fecha_creacion` (datetime)
- ✅ `fecha_actualizacion` (Optional[datetime])
- ✅ Hereda todos los permisos extendidos de `PermisoBase`

**Compatibilidad:** Se mantiene el alias `rol_menu_id` para compatibilidad con código existente.

---

### 3. **`RolMenuPermisoBase`** ✅

**Campos agregados:**
- ✅ `cliente_id` (UUID) - **CRÍTICO para multi-tenant**
- ✅ `puede_crear` (bool, default=False)
- ✅ `puede_exportar` (bool, default=False)
- ✅ `puede_imprimir` (bool, default=False)
- ✅ `puede_aprobar` (bool, default=False)
- ✅ `permisos_extra` (Optional[str], default=None)

**Validaciones actualizadas:**
- ✅ Valida que todos los permisos extendidos requieren `puede_ver=True`
- ✅ Valida que `puede_eliminar` requiere `puede_editar=True`

---

### 4. **`RolMenuPermisoRead`** ✅

**Campos agregados:**
- ✅ `permiso_id` (UUID) - Primary Key (antes `rol_menu_id` como alias)
- ✅ `fecha_creacion` (datetime)
- ✅ `fecha_actualizacion` (Optional[datetime])
- ✅ Hereda todos los campos de `RolMenuPermisoBase` (incluyendo `cliente_id` y permisos extendidos)

**Compatibilidad:** Se mantiene el alias `rol_menu_id` para compatibilidad con código existente.

---

### 5. **`RolMenuPermisoUpdate`** ✅

**Campos agregados (todos opcionales):**
- ✅ `puede_crear` (Optional[bool])
- ✅ `puede_exportar` (Optional[bool])
- ✅ `puede_imprimir` (Optional[bool])
- ✅ `puede_aprobar` (Optional[bool])
- ✅ `permisos_extra` (Optional[str])

**Validaciones actualizadas:**
- ✅ Valida que todos los permisos extendidos requieren `puede_ver=True`
- ✅ Valida que `puede_eliminar` requiere `puede_editar=True`

---

### 6. **`RolMenuPermisoTable` (SQLAlchemy)** ✅

**Corrección aplicada:**
- ✅ `UniqueConstraint` actualizado para incluir `cliente_id`
- ✅ Antes: `UniqueConstraint('rol_id', 'menu_id')`
- ✅ Ahora: `UniqueConstraint('cliente_id', 'rol_id', 'menu_id')`

**Alineación:** ✅ Completamente alineado con `estructura_bd.sql`

---

## 📊 Comparación Antes/Después

### Campos por Schema

| Campo | BD | Antes | Después |
|-------|----|-------|---------|
| `permiso_id` | ✅ | ❌ | ✅ |
| `cliente_id` | ✅ | ❌ | ✅ |
| `rol_id` | ✅ | ✅ | ✅ |
| `menu_id` | ✅ | ✅ | ✅ |
| `puede_ver` | ✅ | ✅ | ✅ |
| `puede_crear` | ✅ | ❌ | ✅ |
| `puede_editar` | ✅ | ✅ | ✅ |
| `puede_eliminar` | ✅ | ✅ | ✅ |
| `puede_exportar` | ✅ | ❌ | ✅ |
| `puede_imprimir` | ✅ | ❌ | ✅ |
| `puede_aprobar` | ✅ | ❌ | ✅ |
| `permisos_extra` | ✅ | ❌ | ✅ |
| `fecha_creacion` | ✅ | ❌ | ✅ |
| `fecha_actualizacion` | ✅ | ❌ | ✅ |

---

## 🔧 Archivos Modificados

1. **`app/modules/rbac/presentation/schemas.py`**
   - ✅ `PermisoBase` - Actualizado
   - ✅ `PermisoRead` - Actualizado
   - ✅ `RolMenuPermisoBase` - Actualizado
   - ✅ `RolMenuPermisoRead` - Actualizado
   - ✅ `RolMenuPermisoUpdate` - Actualizado

2. **`app/infrastructure/database/tables.py`**
   - ✅ `RolMenuPermisoTable` - `UniqueConstraint` corregido

---

## ⚠️ Notas de Compatibilidad

### Alias `rol_menu_id`

Se mantiene el alias `rol_menu_id` en `PermisoRead` y `RolMenuPermisoRead` para compatibilidad con código existente:

```python
@property
def rol_menu_id(self) -> UUID:
    """Alias para permiso_id para compatibilidad con código existente."""
    return self.permiso_id
```

**Recomendación:** Migrar gradualmente al uso de `permiso_id` en lugar de `rol_menu_id`.

---

## 🎯 Validaciones Implementadas

### Reglas de Negocio

1. **Permisos que requieren `puede_ver=True`:**
   - `puede_crear`
   - `puede_editar`
   - `puede_eliminar`
   - `puede_exportar`
   - `puede_imprimir`
   - `puede_aprobar`

2. **Permisos que requieren `puede_editar=True`:**
   - `puede_eliminar`

---

## 📝 Próximos Pasos Recomendados

1. **Revisar servicios que usan estos schemas:**
   - `app/modules/rbac/application/services/permiso_service.py`
   - Verificar que las queries incluyan todos los campos nuevos

2. **Revisar endpoints que usan estos schemas:**
   - Verificar que las respuestas incluyan todos los campos nuevos
   - Actualizar documentación de API si es necesario

3. **Migrar código existente:**
   - Reemplazar `rol_menu_id` por `permiso_id` gradualmente
   - Actualizar queries para incluir `cliente_id` en filtros

4. **Testing:**
   - Probar creación de permisos con todos los campos nuevos
   - Probar actualización de permisos extendidos
   - Verificar validaciones de consistencia

---

## ✅ Estado Final

**Alineación:** ✅ **100% COMPLETA**

Todos los schemas de permisos están ahora completamente alineados con la tabla `rol_menu_permiso` definida en `estructura_bd.sql`.

