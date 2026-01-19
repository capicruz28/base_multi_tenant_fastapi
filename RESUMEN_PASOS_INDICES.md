# 📋 Resumen: Pasos Correctos para Aplicar Índices

**FASE 4A: QUICK WINS - Performance**  
**Fecha:** Diciembre 2024

---

## ✅ VERIFICACIÓN COMPLETADA

**Resultado:** Todos los índices propuestos son **100% compatibles** con tu estructura actual de BD.

- ✅ 6 índices propuestos
- ✅ Todos compatibles con índices existentes
- ✅ No hay conflictos
- ✅ Son complementarios y mejoran performance

---

## 🚀 PASOS CORRECTOS (En Orden)

### 1️⃣ **Ejecutar Script en BD** (PRIMERO)

**Archivo:** `app/docs/database/migrations/FASE2_INDICES_COMPUESTOS.sql`

**Pasos:**
1. Abrir SQL Server Management Studio (SSMS)
2. Conectar a tu servidor
3. Abrir el archivo `FASE2_INDICES_COMPUESTOS.sql`
4. **Cambiar línea 18:** `USE [tu_base_datos];` por el nombre real de tu BD
5. Ejecutar (F5)
6. Verificar mensajes de éxito

**⏱️ Tiempo:** 5-15 minutos

---

### 2️⃣ **Verificar que los Índices se Crearon**

```sql
SELECT 
    OBJECT_NAME(object_id) AS tabla,
    name AS indice
FROM sys.indexes
WHERE name IN (
    'IDX_usuario_cliente_activo_fecha',
    'IDX_rol_cliente_activo_nivel',
    'IDX_refresh_token_usuario_cliente_revoked_expires',
    'IDX_permiso_cliente_rol_menu',
    'IDX_usuario_rol_usuario_cliente_activo',
    'IDX_audit_cliente_evento_fecha'
)
ORDER BY tabla, name;
```

**Resultado esperado:** 6 índices encontrados

---

### 3️⃣ **Actualizar MULTITENANT_SCHEMA_UUID.sql** (DESPUÉS)

**IMPORTANTE:** Mantener el schema sincronizado con la BD real.

**Agregar estos índices en las ubicaciones indicadas:**

#### A. Después de línea 312 (tabla `usuario`):
```sql
-- Índice compuesto para queries con fecha_creacion
CREATE INDEX IDX_usuario_cliente_activo_fecha 
ON usuario(cliente_id, es_activo, fecha_creacion DESC)
WHERE es_eliminado = 0;
```

#### B. Después de línea 371 (tabla `rol`):
```sql
-- Índice compuesto para queries con nivel_acceso
CREATE INDEX IDX_rol_cliente_activo_nivel 
ON rol(cliente_id, es_activo, nivel_acceso);
```

#### C. Después de línea 657 (tabla `refresh_tokens`):
```sql
-- Índice compuesto para validación de tokens activos
CREATE INDEX IDX_refresh_token_usuario_cliente_revoked_expires 
ON refresh_tokens(usuario_id, cliente_id, is_revoked, expires_at);
```

#### D. Después de línea 578 (tabla `rol_menu_permiso`):
```sql
-- Índice compuesto para queries de permisos por cliente+rol+menu
CREATE INDEX IDX_permiso_cliente_rol_menu 
ON rol_menu_permiso(cliente_id, rol_id, menu_id);
```

#### E. Después de línea 418 (tabla `usuario_rol`):
```sql
-- Índice compuesto para queries de roles activos por usuario+cliente
CREATE INDEX IDX_usuario_rol_usuario_cliente_activo 
ON usuario_rol(usuario_id, cliente_id, es_activo);
```

#### F. Después de línea 1284 (tabla `auth_audit_log`):
```sql
-- Índice compuesto para reportes de auditoría por cliente+evento+fecha
CREATE INDEX IDX_audit_cliente_evento_fecha 
ON auth_audit_log(cliente_id, evento, fecha_evento DESC);
```

---

### 4️⃣ **Verificar Performance**

Ejecutar queries de prueba antes y después para comparar tiempos.

---

## ✅ CHECKLIST FINAL

- [ ] Backup de BD creado
- [ ] Script ejecutado en BD
- [ ] 6 índices verificados como creados
- [ ] `MULTITENANT_SCHEMA_UUID.sql` actualizado
- [ ] Performance mejorada verificada
- [ ] Sin errores en aplicación

---

## 📚 DOCUMENTOS DE REFERENCIA

- `VERIFICACION_INDICES_BD.md` - Análisis detallado de compatibilidad
- `PLAN_ACCION_INDICES.md` - Plan completo paso a paso
- `INSTRUCCIONES_APLICAR_INDICES.md` - Guía detallada con rollback

---

**Después de completar estos pasos, puedes proceder con FASE 4B.**


