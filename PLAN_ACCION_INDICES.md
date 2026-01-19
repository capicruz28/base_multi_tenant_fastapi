# 📋 Plan de Acción: Aplicar Índices Compuestos

**FASE 4A: QUICK WINS - Performance**  
**Fecha:** Diciembre 2024

---

## ✅ VERIFICACIÓN COMPLETADA

**Resultado:** Todos los índices propuestos son **compatibles** con la estructura actual de BD.

- ✅ 6 índices propuestos
- ✅ Todos compatibles con índices existentes
- ✅ No hay conflictos
- ✅ Son complementarios y mejoran performance

Ver detalles en: `VERIFICACION_INDICES_BD.md`

---

## 🚀 PASOS PARA APLICAR ÍNDICES

### PASO 1: Backup de Base de Datos (CRÍTICO)

```sql
-- Crear backup completo antes de cualquier cambio
BACKUP DATABASE [tu_base_datos] 
TO DISK = 'C:\Backups\backup_antes_indices_' + CONVERT(VARCHAR, GETDATE(), 112) + '.bak'
WITH FORMAT, COMPRESSION;

-- Verificar que el backup se creó correctamente
RESTORE VERIFYONLY 
FROM DISK = 'C:\Backups\backup_antes_indices_' + CONVERT(VARCHAR, GETDATE(), 112) + '.bak';
```

**⏱️ Tiempo estimado:** 5-30 minutos (dependiendo del tamaño de BD)

---

### PASO 2: Verificar Índices Existentes

```sql
-- Verificar qué índices ya existen
SELECT 
    OBJECT_NAME(object_id) AS tabla,
    name AS indice,
    type_desc AS tipo,
    is_unique,
    is_primary_key
FROM sys.indexes
WHERE OBJECT_NAME(object_id) IN (
    'usuario', 'rol', 'refresh_tokens', 
    'rol_menu_permiso', 'usuario_rol', 'auth_audit_log'
)
AND name LIKE 'IDX_%'
ORDER BY tabla, name;
```

**Guardar resultado** para comparar después.

---

### PASO 3: Ejecutar Script de Índices

**Opción A: Desde SQL Server Management Studio (SSMS)**

1. Abrir SSMS
2. Conectar a tu servidor SQL Server
3. Seleccionar la base de datos
4. Abrir archivo: `app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql`
5. **IMPORTANTE:** Cambiar línea 18:
   ```sql
   USE [tu_base_datos];  -- ⚠️ CAMBIAR por el nombre real de tu BD
   ```
   Por ejemplo:
   ```sql
   USE [MiBaseDatosMultiTenant];
   ```
6. Ejecutar script (F5)
7. Verificar mensajes de éxito

**Opción B: Desde sqlcmd**

```bash
sqlcmd -S localhost -U sa -P "YourPassword" -d "tu_base_datos" -i "app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql"
```

**⏱️ Tiempo estimado:** 5-15 minutos (dependiendo del tamaño de las tablas)

---

### PASO 4: Verificar que los Índices se Crearon

```sql
-- Verificar índices creados
SELECT 
    OBJECT_NAME(object_id) AS tabla,
    name AS indice,
    type_desc AS tipo,
    is_unique
FROM sys.indexes
WHERE name IN (
    'IDX_usuario_cliente_activo_fecha',
    'IDX_rol_cliente_activo_nivel',
    'IDX_refresh_token_usuario_cliente_revoked_expires',
    'IDX_permiso_cliente_rol_menu',
    'IDX_usuario_rol_usuario_cliente_activo',
    'IDX_audit_cliente_evento_fecha'
)
AND OBJECT_NAME(object_id) IN (
    'usuario', 'rol', 'refresh_tokens', 
    'rol_menu_permiso', 'usuario_rol', 'auth_audit_log'
)
ORDER BY tabla, name;
```

**Resultado esperado:** 6 índices encontrados

---

### PASO 5: Actualizar MULTITENANT_SCHEMA_UUID.sql

**IMPORTANTE:** Actualizar el archivo de schema para mantenerlo sincronizado con la BD real.

**Ubicaciones donde agregar los índices:**

1. **Después de línea 312** (después de índices de `usuario`):
   ```sql
   -- Índice compuesto para queries con fecha_creacion
   CREATE INDEX IDX_usuario_cliente_activo_fecha 
   ON usuario(cliente_id, es_activo, fecha_creacion DESC)
   WHERE es_eliminado = 0;
   ```

2. **Después de línea 371** (después de índices de `rol`):
   ```sql
   -- Índice compuesto para queries con nivel_acceso
   CREATE INDEX IDX_rol_cliente_activo_nivel 
   ON rol(cliente_id, es_activo, nivel_acceso);
   ```

3. **Después de línea 657** (después de índices de `refresh_tokens`):
   ```sql
   -- Índice compuesto para validación de tokens activos
   CREATE INDEX IDX_refresh_token_usuario_cliente_revoked_expires 
   ON refresh_tokens(usuario_id, cliente_id, is_revoked, expires_at);
   ```

4. **Después de línea 578** (después de índices de `rol_menu_permiso`):
   ```sql
   -- Índice compuesto para queries de permisos por cliente+rol+menu
   CREATE INDEX IDX_permiso_cliente_rol_menu 
   ON rol_menu_permiso(cliente_id, rol_id, menu_id);
   ```

5. **Después de línea 418** (después de índices de `usuario_rol`):
   ```sql
   -- Índice compuesto para queries de roles activos por usuario+cliente
   CREATE INDEX IDX_usuario_rol_usuario_cliente_activo 
   ON usuario_rol(usuario_id, cliente_id, es_activo);
   ```

6. **Después de línea 1284** (después de índices de `auth_audit_log`):
   ```sql
   -- Índice compuesto para reportes de auditoría por cliente+evento+fecha
   CREATE INDEX IDX_audit_cliente_evento_fecha 
   ON auth_audit_log(cliente_id, evento, fecha_evento DESC);
   ```

---

### PASO 6: Verificar Performance

**Antes de índices:**
```sql
SET STATISTICS TIME ON;
SET STATISTICS IO ON;

-- Query de prueba 1: Listado de usuarios activos
SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id-uuid' 
  AND es_activo = 1 
  AND es_eliminado = 0
ORDER BY fecha_creacion DESC;

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
```

**Anotar:**
- CPU time
- Elapsed time
- Logical reads

**Después de índices:**
```sql
-- Ejecutar la misma query
SET STATISTICS TIME ON;
SET STATISTICS IO ON;

SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id-uuid' 
  AND es_activo = 1 
  AND es_eliminado = 0
ORDER BY fecha_creacion DESC;

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
```

**Comparar resultados** (debería ser 30-50% más rápido)

---

### PASO 7: Verificar Query Plans

```sql
-- Ver query plan mejorado
SET SHOWPLAN_ALL ON;
GO

SELECT * FROM usuario 
WHERE cliente_id = 'tu-cliente-id-uuid' 
  AND es_activo = 1 
  AND es_eliminado = 0
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

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Backup de BD creado y verificado
- [ ] Índices existentes documentados
- [ ] Script ejecutado sin errores
- [ ] 6 índices verificados como creados
- [ ] `MULTITENANT_SCHEMA_UUID.sql` actualizado
- [ ] Query plans verificados (usando índices)
- [ ] Performance mejorada (comparar tiempos)
- [ ] Sin errores en logs de aplicación
- [ ] Tests ejecutados y pasando

---

## 📊 MÉTRICAS ESPERADAS

### Mejora de Performance

| Query | Antes | Después | Mejora Esperada |
|-------|-------|---------|----------------|
| Listado de usuarios activos | ~200ms | <100ms | 50% |
| Validación de tokens | ~100ms | <50ms | 50% |
| Consultas de permisos | ~150ms | <80ms | 47% |
| Reportes de auditoría | ~300ms | <150ms | 50% |

### Uso de Recursos

- **Espacio adicional:** ~10-20% del tamaño de tablas
- **Memoria:** Aumento mínimo (índices se cargan según uso)
- **Tiempo de INSERT/UPDATE:** Aumento mínimo (~5-10ms por operación)

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

4. **Continuar con FASE 4B:**
   - Una vez verificados los índices, proceder con mejoras estructurales

---

**Última actualización:** Diciembre 2024


