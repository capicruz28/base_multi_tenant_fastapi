# 📋 Instrucciones para Aplicar Índices Compuestos

**FASE 4A: QUICK WINS - Performance**  
**Archivo:** `app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql`

---

## ⚠️ IMPORTANTE: ANTES DE EJECUTAR

### 1. Backup de Base de Datos (CRÍTICO)

```sql
-- Crear backup completo
BACKUP DATABASE [tu_base_datos] 
TO DISK = 'C:\Backups\backup_antes_indices.bak'
WITH FORMAT, COMPRESSION;
```

### 2. Verificar Espacio en Disco

Los índices ocupan espacio adicional. Verificar que hay suficiente espacio:
- Estimación: ~10-20% del tamaño actual de las tablas
- Verificar espacio disponible antes de ejecutar

### 3. Ejecutar en Horario de Bajo Tráfico

- Recomendado: Horario de mantenimiento
- Tiempo estimado: 5-15 minutos (dependiendo del tamaño de las tablas)

---

## 🚀 PASOS PARA APLICAR

### Paso 1: Conectar a SQL Server

```bash
# Usar SQL Server Management Studio (SSMS) o sqlcmd
sqlcmd -S localhost -U sa -P "YourPassword" -d "tu_base_datos"
```

### Paso 2: Verificar Índices Existentes

```sql
-- Ver índices actuales
SELECT 
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.name LIKE 'IDX_%'
ORDER BY t.name, i.name;
```

### Paso 3: Ejecutar Script de Índices

**Opción A: Desde SSMS**
```sql
-- En SQL Server Management Studio
USE [tu_base_datos];
GO

-- Ejecutar el script completo
:r app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql
```

**Opción B: Desde sqlcmd**
```bash
sqlcmd -S localhost -U sa -P "YourPassword" -d "tu_base_datos" -i app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql
```

**Opción C: Copiar y pegar**
1. Abrir el archivo `FASE2_INDICES_COMPUESTOS.sql`
2. Copiar todo el contenido
3. Pegar en SSMS
4. Ejecutar

---

## ✅ VERIFICACIÓN DESPUÉS DE EJECUTAR

### 1. Verificar que los Índices se Crearon

```sql
-- Verificar índices creados
SELECT 
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    i.is_unique,
    i.is_primary_key
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.name IN (
    'IDX_usuario_cliente_activo_fecha',
    'IDX_rol_cliente_activo_nivel',
    'IDX_refresh_token_usuario_cliente_revoked_expires',
    'IDX_permiso_cliente_rol_menu',
    'IDX_usuario_rol_usuario_cliente_activo',
    'IDX_audit_cliente_evento_fecha'
)
ORDER BY t.name, i.name;
```

**Resultado esperado:** 6 índices encontrados

### 2. Verificar Estadísticas de Índices

```sql
-- Ver estadísticas de uso (después de algunas queries)
SELECT 
    OBJECT_NAME(s.object_id) AS TableName,
    i.name AS IndexName,
    s.user_seeks,
    s.user_scans,
    s.user_lookups,
    s.user_updates
FROM sys.dm_db_index_usage_stats s
INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE i.name LIKE 'IDX_%'
ORDER BY s.user_seeks DESC;
```

### 3. Comparar Performance

**Antes de índices:**
```sql
-- Ejecutar query de prueba
SET STATISTICS TIME ON;
SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id' 
  AND es_activo = 1 
ORDER BY fecha_creacion DESC;
SET STATISTICS TIME OFF;
-- Anotar tiempo de ejecución
```

**Después de índices:**
```sql
-- Ejecutar la misma query
SET STATISTICS TIME ON;
SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id' 
  AND es_activo = 1 
ORDER BY fecha_creacion DESC;
SET STATISTICS TIME OFF;
-- Comparar tiempo (debería ser 30-50% más rápido)
```

---

## 🔍 QUERY PLANS

### Ver Query Plan Mejorado

```sql
-- Ver query plan con índices
SET SHOWPLAN_ALL ON;
GO

SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id' 
  AND es_activo = 1 
ORDER BY fecha_creacion DESC;

SET SHOWPLAN_ALL OFF;
GO
```

**Verificar:**
- ✅ Índice `IDX_usuario_cliente_activo_fecha` aparece en el plan
- ✅ No hay "Table Scan" (debería ser "Index Seek")
- ✅ Costo estimado reducido

---

## ⚠️ ROLLBACK (Si es Necesario)

Si hay problemas, eliminar índices:

```sql
-- Eliminar índices (solo si es necesario)
DROP INDEX IF EXISTS IDX_usuario_cliente_activo_fecha ON usuario;
DROP INDEX IF EXISTS IDX_rol_cliente_activo_nivel ON rol;
DROP INDEX IF EXISTS IDX_refresh_token_usuario_cliente_revoked_expires ON refresh_tokens;
DROP INDEX IF EXISTS IDX_permiso_cliente_rol_menu ON rol_menu_permiso;
DROP INDEX IF EXISTS IDX_usuario_rol_usuario_cliente_activo ON usuario_rol;
DROP INDEX IF EXISTS IDX_audit_cliente_evento_fecha ON auth_audit_log;
```

---

## 📊 MÉTRICAS ESPERADAS

### Mejora de Performance

| Query | Antes | Después | Mejora Esperada |
|-------|-------|---------|-----------------|
| Listado de usuarios activos | ~200ms | <100ms | 50% |
| Validación de tokens | ~100ms | <50ms | 50% |
| Consultas de permisos | ~150ms | <80ms | 47% |

### Uso de Recursos

- **Espacio adicional:** ~10-20% del tamaño de tablas
- **Memoria:** Aumento mínimo (índices se cargan según uso)
- **Tiempo de INSERT/UPDATE:** Aumento mínimo (~5-10ms por operación)

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Backup de BD creado
- [ ] Espacio en disco verificado
- [ ] Horario de bajo tráfico seleccionado
- [ ] Script ejecutado sin errores
- [ ] 6 índices verificados como creados
- [ ] Query plans verificados (usando índices)
- [ ] Performance mejorada (comparar tiempos)
- [ ] Sin errores en logs de aplicación

---

## 🎯 PRÓXIMOS PASOS

Después de aplicar índices:

1. **Monitorear performance:**
   - Revisar métricas en `/api/v1/metrics/summary`
   - Verificar tiempos de queries

2. **Ajustar si es necesario:**
   - Si algún índice no se usa, considerar eliminarlo
   - Si hay fragmentación, reorganizar índices

3. **Documentar resultados:**
   - Anotar mejoras de performance observadas
   - Actualizar métricas en documentación

---

**Última actualización:** Diciembre 2024


