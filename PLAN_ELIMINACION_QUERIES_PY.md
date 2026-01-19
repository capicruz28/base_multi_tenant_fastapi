# 📋 Plan de Eliminación de queries.py (Código Legacy)

**Fecha:** Diciembre 2024  
**Objetivo:** Eliminar `app/infrastructure/database/queries.py` completamente  
**Estado:** Análisis en progreso

---

## 🔍 ANÁLISIS DE USO

### Archivos que Importan queries.py

1. **`app/api/deps_backup.py`**
   - **Estado:** Archivo de backup
   - **Acción:** Verificar si se usa, si no, eliminar o actualizar

2. **`app/api/metrics_endpoint.py`**
   - **Estado:** Necesita verificación
   - **Acción:** Migrar imports si es necesario

3. **`app/infrastructure/database/queries.py`**
   - **Estado:** Archivo deprecated (se auto-referencia)
   - **Acción:** Eliminar después de verificar que no se use

---

## ✅ VERIFICACIÓN

### Estado Actual de queries.py

- ✅ Marcado como DEPRECATED
- ✅ Funciones lanzan `NotImplementedError`
- ✅ Todas las constantes SQL migradas a `sql_constants.py`
- ✅ Todas las funciones migradas a `queries_async.py`

### Archivos que Necesitan Migración

1. **`app/api/deps_backup.py`**
   - Si es backup, puede eliminarse o actualizarse
   - Si se usa, migrar imports a `queries_async.py`

2. **`app/api/metrics_endpoint.py`**
   - Verificar uso real
   - Migrar si es necesario

---

## 📋 PLAN DE ACCIÓN

### Paso 1: Verificar Archivos
- [x] Identificar archivos que importan queries.py
- [ ] Verificar si `deps_backup.py` se usa
- [ ] Verificar si `metrics_endpoint.py` necesita queries.py

### Paso 2: Migrar Imports
- [ ] Actualizar `deps_backup.py` (si se usa)
- [ ] Actualizar `metrics_endpoint.py` (si es necesario)

### Paso 3: Eliminar queries.py
- [ ] Hacer backup del archivo
- [ ] Eliminar archivo
- [ ] Verificar que aplicación funciona
- [ ] Ejecutar tests

### Paso 4: Limpiar Referencias
- [ ] Buscar referencias en documentación
- [ ] Actualizar documentación
- [ ] Limpiar imports obsoletos

---

## ⚠️ RIESGOS

- **Bajo:** queries.py ya lanza NotImplementedError
- **Bajo:** Todas las constantes migradas
- **Bajo:** Todas las funciones migradas

---

## ✅ CRITERIOS DE ÉXITO

- [ ] No hay imports de queries.py en código activo
- [ ] Aplicación funciona correctamente
- [ ] Tests pasan
- [ ] Archivo queries.py eliminado

---

**Última actualización:** Diciembre 2024


