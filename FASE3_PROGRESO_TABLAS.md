# FASE 3 — PROGRESO DE ACTUALIZACIÓN DE TABLAS SQLALCHEMY CORE

## ✅ Completado

### **app/infrastructure/database/tables.py**

Todas las primary keys y foreign keys han sido actualizadas de `Integer` a `UNIQUEIDENTIFIER`:

#### Primary Keys Actualizadas (15):
1. ✅ `ClienteTable.cliente_id`
2. ✅ `UsuarioTable.usuario_id`
3. ✅ `RolTable.rol_id`
4. ✅ `UsuarioRolTable.usuario_rol_id`
5. ✅ `AreaMenuTable.area_id`
6. ✅ `MenuTable.menu_id`
7. ✅ `RolMenuPermisoTable.permiso_id`
8. ✅ `RefreshTokensTable.token_id`
9. ✅ `ClienteModuloTable.modulo_id`
10. ✅ `ClienteConexionTable.conexion_id`
11. ✅ `ClienteModuloActivoTable.cliente_modulo_activo_id`
12. ✅ `ClienteAuthConfigTable.config_id`
13. ✅ `FederacionIdentidadTable.federacion_id`
14. ✅ `LogSincronizacionUsuarioTable.log_id`
15. ✅ `AuthAuditLogTable.log_id`

#### Foreign Keys Actualizadas (48):
- ✅ Todas las referencias a `cliente_id`
- ✅ Todas las referencias a `usuario_id`
- ✅ Todas las referencias a `rol_id`
- ✅ Todas las referencias a `menu_id`
- ✅ Todas las referencias a `area_id`
- ✅ Todas las referencias a `modulo_id`
- ✅ Todas las referencias a `conexion_id`
- ✅ Todas las referencias a `permiso_id`
- ✅ Todas las referencias a `token_id`
- ✅ Todas las referencias a `config_id`
- ✅ Todas las referencias a `federacion_id`
- ✅ Todas las referencias a `log_id`
- ✅ Referencias a `padre_menu_id`
- ✅ Referencias a `asignado_por_usuario_id`
- ✅ Referencias a `creado_por_usuario_id`
- ✅ Referencias a `usuario_eliminacion_id`
- ✅ Referencias a `usuario_ejecutor_id`
- ✅ Referencias a `cliente_origen_id`
- ✅ Referencias a `cliente_destino_id`
- ✅ Referencias a `referencia_sincronizacion_id`

## 🔧 Cambios Realizados

1. **Import agregado**: `from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER`
2. **Tipo de columna**: `Integer` → `UNIQUEIDENTIFIER` para todas las PKs y FKs
3. **Autoincrement eliminado**: `autoincrement=True` removido de todas las PKs (UUIDs se generan con `NEWID()` o en Python)

## ⚠️ Notas Importantes

1. **Generación de UUIDs**: Los UUIDs se generarán automáticamente en la base de datos usando `NEWID()` (definido en el script de migración SQL) o en Python usando `uuid.uuid4()`
2. **Compatibilidad**: SQLAlchemy manejará automáticamente la conversión entre UUID de Python y UNIQUEIDENTIFIER de SQL Server
3. **Queries**: Las queries SQLAlchemy Core seguirán funcionando igual, pero ahora trabajarán con UUIDs en lugar de enteros

## 🚀 Próximos Pasos

1. Actualizar repositorios para trabajar con UUID
2. Actualizar servicios para trabajar con UUID
3. Actualizar endpoints para aceptar UUID en parámetros
4. Testing exhaustivo




