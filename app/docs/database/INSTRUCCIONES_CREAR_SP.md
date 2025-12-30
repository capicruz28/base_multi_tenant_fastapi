# Instrucciones para Crear Stored Procedures

## ⚠️ PROBLEMA DETECTADO

El stored procedure `sp_obtener_menu_usuario` no existe en la base de datos del cliente, causando el error:
```
Could not find stored procedure 'sp_obtener_menu_usuario'
```

## 🔧 SOLUCIÓN

Debes crear los stored procedures en **TODAS** las bases de datos:

1. **Base de datos central** (`bd_hybrid_sistema_central` o similar)
2. **Cada base de datos de cliente** (Multi-DB) - Ejemplo: `bd_cliente_acme`

## 📋 PASOS A SEGUIR

### Paso 1: Crear SP en Base de Datos Central

1. Conectarte a la base de datos central
2. Ejecutar el script: `SP_OBTENER_MENU_USUARIO.sql`
3. Ejecutar el script: `SP_VALIDAR_ACCESO_MENU.sql` (opcional pero recomendado)

### Paso 2: Crear SP en Cada Base de Datos de Cliente

Para cada cliente con BD dedicada (Multi-DB):

1. Conectarte a la BD del cliente (ej: `bd_cliente_acme`)
2. Ejecutar el script: `SP_OBTENER_MENU_USUARIO.sql`
3. Ejecutar el script: `SP_VALIDAR_ACCESO_MENU.sql` (opcional)

### Paso 3: Verificar

Ejecutar en cada BD:
```sql
-- Verificar que el SP existe
SELECT 
    ROUTINE_NAME,
    ROUTINE_TYPE,
    CREATED,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_NAME IN ('sp_obtener_menu_usuario', 'sp_validar_acceso_menu')
ORDER BY ROUTINE_NAME;
```

## 📝 SCRIPTS DISPONIBLES

1. **`SP_OBTENER_MENU_USUARIO.sql`** - SP principal para obtener menú del usuario
2. **`SP_VALIDAR_ACCESO_MENU.sql`** - SP para validar acceso a menú específico

## ⚠️ IMPORTANTE

- Los SPs deben crearse en **TODAS** las bases de datos (central y clientes)
- Si agregas un nuevo cliente con BD dedicada, debes crear los SPs también
- Los SPs usan las nuevas tablas: `modulo`, `modulo_seccion`, `modulo_menu`, `cliente_modulo`

## 🔍 VERIFICACIÓN RÁPIDA

Después de crear los SPs, prueba con:
```sql
-- Probar el SP (reemplaza los UUIDs con valores reales)
EXEC sp_obtener_menu_usuario 
    @usuario_id = '2458d1ea-816b-4c3c-8d13-b90271f59558',
    @cliente_id = 'c090bcb2-1175-407b-8d9b-60709aaa7dfe';
```

Si retorna filas (aunque estén vacías), el SP está funcionando correctamente.

