# 📊 Análisis de Raw SQL Pendiente

**Fecha:** Diciembre 2024  
**Objetivo:** Identificar y clasificar raw SQL restante para migración

---

## 🔍 ARCHIVOS CON RAW SQL IDENTIFICADOS

### 1. `app/modules/users/application/services/user_service.py`

**Ubicación:** Líneas 1402-1456

**Query:**
```python
SELECT_QUERY = """
WITH UserRoles AS (
    SELECT ... FROM usuario u
    WHERE u.es_eliminado = 0
      AND (? IS NULL OR ...)
)
SELECT * FROM UserRoles
ORDER BY usuario_id 
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
"""
```

**Clasificación:** 
- **Tipo:** Query compleja con CTE
- **Uso:** BD dedicadas (multi-DB)
- **Migración:** Media complejidad
- **Acción:** Mantener como raw SQL (usa parámetros posicionales para BD dedicadas)

**Nota:** Ya existe versión en `sql_constants.py` para BD compartidas. Esta es específica para BD dedicadas.

---

### 2. `app/modules/modulos/application/services/modulo_menu_service.py`

**Ubicación:** Líneas 445-454

**Query:**
```python
query_raw = text("""
    SELECT 
        menu_id, modulo_id, seccion_id, cliente_id,
        codigo, nombre, descripcion, icono, ruta,
        menu_padre_id, nivel, tipo_menu, orden,
        requiere_autenticacion, es_visible, es_menu_sistema, es_activo,
        fecha_creacion, fecha_actualizacion, configuracion_json
    FROM modulo_menu 
    WHERE menu_id = :menu_id
""").bindparams(menu_id=str(menu_id))
```

**Clasificación:**
- **Tipo:** Query simple SELECT
- **Uso:** Fallback cuando SQLAlchemy no funciona
- **Migración:** Baja complejidad (ya usa text().bindparams())
- **Acción:** ✅ Ya está bien implementado (usa parámetros nombrados)

---

### 3. `app/modules/auth/application/services/auth_service.py`

**Ubicación:** Líneas 273-296

**Query:**
```python
query = """
SELECT u.*, r.rol_id, r.nombre as rol_nombre, r.nivel_acceso
FROM usuario u
LEFT JOIN usuario_rol ur ON u.usuario_id = ur.usuario_id AND ur.es_activo = 1
LEFT JOIN rol r ON ur.rol_id = r.rol_id AND r.es_activo = 1
WHERE u.nombre_usuario = :nombre_usuario
  AND u.cliente_id = :cliente_id
  AND u.es_eliminado = 0
"""
```

**Clasificación:**
- **Tipo:** Query con JOINs
- **Uso:** Autenticación de usuarios
- **Migración:** Media complejidad
- **Acción:** ✅ Ya usa text().bindparams() correctamente

---

## 📋 CLASIFICACIÓN GENERAL

### ✅ Ya Bien Implementados (No Requieren Cambio)
- `modulo_menu_service.py` - Usa text().bindparams() correctamente
- `auth_service.py` - Usa text().bindparams() correctamente

### 🔄 Requieren Revisión (Pero Son Aceptables)
- `user_service.py` - Query específica para BD dedicadas (usa parámetros posicionales)
  - **Justificación:** Diferencia entre BD compartidas y dedicadas
  - **Acción:** Documentar mejor o crear constante específica

---

## 🎯 RECOMENDACIONES

### Prioridad Alta
1. **Documentar excepciones:**
   - Por qué se mantiene raw SQL en ciertos casos
   - Diferencia entre BD compartidas y dedicadas

### Prioridad Media
2. **Crear constantes para queries de BD dedicadas:**
   - Mover query de `user_service.py` a `sql_constants.py`
   - Nombre: `SELECT_USUARIOS_PAGINATED_MULTI_DB`

### Prioridad Baja
3. **Migrar queries simples a SQLAlchemy Core:**
   - Solo si no hay justificación para mantener raw SQL

---

## ✅ CONCLUSIÓN

**Estado Actual:**
- ✅ La mayoría del raw SQL ya está bien implementado
- ✅ Usa parámetros nombrados correctamente
- ✅ Solo quedan casos específicos justificados

**Acción Recomendada:**
- Documentar excepciones
- Crear constantes para queries específicas de BD dedicadas
- No es crítico migrar todo a SQLAlchemy Core (algunos casos requieren raw SQL)

---

**Última actualización:** Diciembre 2024


