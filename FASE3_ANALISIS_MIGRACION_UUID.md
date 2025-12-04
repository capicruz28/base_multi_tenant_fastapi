# FASE 3 — MIGRACIÓN DE PRIMARY KEYS A UUID

## 📋 Objetivo

Habilitar sincronización escalable híbrida multi-tenant + on-premise ↔ cloud mediante la migración de todas las Primary Keys de `INT IDENTITY` a `UNIQUEIDENTIFIER` (UUID).

## 🔍 Análisis del Esquema Actual

### Tablas con PKs INT IDENTITY (15 tablas)

1. **cliente** → `cliente_id INT PRIMARY KEY IDENTITY(1,1)`
2. **usuario** → `usuario_id INT PRIMARY KEY IDENTITY(1,1)`
3. **rol** → `rol_id INT PRIMARY KEY IDENTITY(1,1)`
4. **usuario_rol** → `usuario_rol_id INT PRIMARY KEY IDENTITY(1,1)`
5. **area_menu** → `area_id INT PRIMARY KEY IDENTITY(1,1)`
6. **menu** → `menu_id INT PRIMARY KEY IDENTITY(1,1)`
7. **rol_menu_permiso** → `permiso_id INT PRIMARY KEY IDENTITY(1,1)`
8. **refresh_tokens** → `token_id INT IDENTITY(1,1) PRIMARY KEY`
9. **cliente_modulo** → `modulo_id INT PRIMARY KEY IDENTITY(1,1)`
10. **cliente_conexion** → `conexion_id INT PRIMARY KEY IDENTITY(1,1)`
11. **cliente_modulo_activo** → `cliente_modulo_activo_id INT PRIMARY KEY IDENTITY(1,1)`
12. **cliente_auth_config** → `config_id INT PRIMARY KEY IDENTITY(1,1)`
13. **federacion_identidad** → `federacion_id INT PRIMARY KEY IDENTITY(1,1)`
14. **log_sincronizacion_usuario** → `log_id INT PRIMARY KEY IDENTITY(1,1)`
15. **auth_audit_log** → `log_id INT PRIMARY KEY IDENTITY(1,1)`

### Foreign Keys que Referencian estas PKs (48 FKs)

#### Referencias a `cliente_id`:
- `usuario.cliente_id` → `cliente.cliente_id`
- `rol.cliente_id` → `cliente.cliente_id`
- `usuario_rol.cliente_id` → `cliente.cliente_id`
- `area_menu.cliente_id` → `cliente.cliente_id`
- `menu.cliente_id` → `cliente.cliente_id`
- `rol_menu_permiso.cliente_id` → `cliente.cliente_id`
- `refresh_tokens.cliente_id` → `cliente.cliente_id`
- `cliente_conexion.cliente_id` → `cliente.cliente_id`
- `cliente_modulo_activo.cliente_id` → `cliente.cliente_id`
- `cliente_auth_config.cliente_id` → `cliente.cliente_id`
- `federacion_identidad.cliente_id` → `cliente.cliente_id`
- `log_sincronizacion_usuario.cliente_origen_id` → `cliente.cliente_id`
- `log_sincronizacion_usuario.cliente_destino_id` → `cliente.cliente_id`
- `auth_audit_log.cliente_id` → `cliente.cliente_id`

#### Referencias a `usuario_id`:
- `usuario_rol.usuario_id` → `usuario.usuario_id`
- `usuario_rol.asignado_por_usuario_id` → `usuario.usuario_id`
- `refresh_tokens.usuario_id` → `usuario.usuario_id`
- `log_sincronizacion_usuario.usuario_id` → `usuario.usuario_id`
- `log_sincronizacion_usuario.usuario_ejecutor_id` → `usuario.usuario_id`
- `auth_audit_log.usuario_id` → `usuario.usuario_id`

#### Referencias a `rol_id`:
- `usuario_rol.rol_id` → `rol.rol_id`
- `rol_menu_permiso.rol_id` → `rol.rol_id`

#### Referencias a `menu_id`:
- `menu.padre_menu_id` → `menu.menu_id` (FK recursiva)
- `rol_menu_permiso.menu_id` → `menu.menu_id`

#### Referencias a `area_id`:
- `menu.area_id` → `area_menu.area_id`

#### Referencias a `modulo_id`:
- `cliente_modulo_activo.modulo_id` → `cliente_modulo.modulo_id`

## 📝 Estrategia de Migración

### Opción 1: Migración Completa (Recomendada para Nuevos Proyectos)
- Convertir todas las PKs a `UNIQUEIDENTIFIER`
- Generar UUIDs para registros existentes
- Actualizar todas las FKs
- **Ventaja**: Sincronización perfecta entre sistemas
- **Desventaja**: Requiere downtime y migración de datos

### Opción 2: Migración Híbrida (Recomendada para Producción)
- Agregar columna `uuid` a cada tabla (nullable inicialmente)
- Generar UUIDs para registros existentes
- Mantener `INT ID` como PK temporalmente
- Migrar gradualmente código a usar UUID
- **Ventaja**: Sin downtime, migración gradual
- **Desventaja**: Complejidad temporal durante transición

### Opción 3: Solo Nuevos Registros (Para este Proyecto)
- Cambiar `IDENTITY(1,1)` por `DEFAULT NEWID()` en nuevas tablas
- Mantener INT para tablas existentes
- **Ventaja**: Sin impacto en datos existentes
- **Desventaja**: No resuelve sincronización para datos existentes

## 🎯 Decisión: Opción 1 (Migración Completa)

Para este proyecto, implementaremos la **Opción 1** porque:
1. Es un sistema en desarrollo/refactoring
2. Permite sincronización perfecta desde el inicio
3. Facilita arquitectura híbrida multi-tenant
4. Mejor para escalabilidad a largo plazo

## 📦 Archivos a Generar

1. ✅ `FASE3_ANALISIS_MIGRACION_UUID.md` (este archivo)
2. ⏳ `app/docs/database/migrations/FASE3_MIGRACION_UUID.sql` (script DDL)
3. ⏳ `FASE3_PLAN_ACTUALIZACION_SCHEMAS.md` (plan de actualización de schemas)
4. ⏳ Actualización de schemas Pydantic
5. ⏳ Actualización de repositorios
6. ⏳ Actualización de servicios

## ⚠️ Consideraciones Importantes

### Performance
- UUIDs son 16 bytes vs 4 bytes INT
- Índices más grandes
- Joins ligeramente más lentos (marginal)
- **Aceptable** para la mayoría de casos de uso

### Compatibilidad
- SQL Server soporta `UNIQUEIDENTIFIER` nativamente
- Python `uuid` module genera UUIDv4
- Pydantic soporta `UUID` type nativamente

### Sincronización
- UUIDs permiten sincronización sin conflictos entre sistemas
- Útil para arquitectura híbrida (cloud + on-premise)
- Evita colisiones de IDs entre tenants

## 🚀 Próximos Pasos

1. Generar script SQL de migración DDL
2. Actualizar schemas Pydantic
3. Actualizar repositorios
4. Actualizar servicios
5. Actualizar endpoints
6. Testing exhaustivo




