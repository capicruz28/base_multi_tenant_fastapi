# ✅ CHECKLIST DE ACCIÓN INMEDIATA
## Refactorización Multi-Tenant - Modelo `cliente_conexion`

---

## 🎯 ANTES DE EMPEZAR

### 1. Revisar Documentación Completa
- [ ] Leer `AUDITORIA_ARQUITECTONICA_Y_PLAN_REFACTORIZACION.md`
- [ ] Revisar `RESUMEN_EJECUTIVO_REFACTORIZACION.md`
- [ ] Entender el nuevo modelo de datos

### 2. Preparar Ambiente
- [ ] Crear backup completo de base de datos
- [ ] Verificar que tienes acceso a staging/producción
- [ ] Preparar herramientas de monitoreo

---

## 📋 CHECKLIST POR FASE

### FASE 1: PREPARACIÓN (Día 1)

#### Backup y Seguridad
- [ ] Crear backup completo de BD: `backup_pre_refactor.bak`
- [ ] Verificar que el backup es restaurable
- [ ] Documentar procedimiento de rollback

#### Scripts de Migración
- [ ] Crear script SQL para migrar datos:
  ```sql
  -- Migrar de cliente_modulo_conexion a cliente_conexion
  -- Solo conexiones principales (es_conexion_principal = 1)
  ```
- [ ] Probar script en ambiente de desarrollo
- [ ] Validar que los datos migrados son correctos

#### Git y Branching
- [ ] Crear branch: `git checkout -b refactor/cliente-conexion-model`
- [ ] Crear branch de backup: `git checkout -b backup/pre-refactor`
- [ ] Documentar cambios en CHANGELOG.md

---

### FASE 2: NUEVOS COMPONENTES (Día 2-3)

#### TenantManager
- [ ] Crear `app/core/tenant/tenant_manager.py`
- [ ] Implementar `get_tenant_connection_config(cliente_id)`
- [ ] Implementar `resolve_database_type(cliente_id)`
- [ ] Implementar `get_connection_string(cliente_id)`
- [ ] Agregar tests unitarios (cobertura > 80%)
- [ ] Documentar métodos

#### ConnectionResolver
- [ ] Crear `app/core/tenant/connection_resolver.py`
- [ ] Implementar `resolve_for_shared(cliente_id)`
- [ ] Implementar `resolve_for_dedicated(cliente_id)`
- [ ] Implementar `resolve_for_onpremise(cliente_id)`
- [ ] Implementar `resolve_for_hybrid(cliente_id)`
- [ ] Agregar fallbacks robustos
- [ ] Agregar tests unitarios

#### ConexionRepository
- [ ] Crear `app/modules/tenant/infrastructure/repositories/conexion_repository.py`
- [ ] Implementar `find_by_cliente_id(cliente_id)`
- [ ] Implementar `find_by_id(conexion_id)`
- [ ] Implementar `create(conexion)`
- [ ] Implementar `update(conexion_id, conexion)`
- [ ] Integrar encriptación/desencriptación
- [ ] Agregar tests unitarios

#### Entidad de Dominio
- [ ] Crear `app/modules/tenant/domain/entities/conexion.py`
- [ ] Definir value objects necesarios
- [ ] Agregar validaciones de dominio
- [ ] Agregar tests unitarios

---

### FASE 3: ACTUALIZAR EXISTENTES (Día 4-5)

#### Schemas
- [ ] Abrir `app/modules/tenant/presentation/schemas.py`
- [ ] Eliminar `modulo_id: int` de `ConexionBase`
- [ ] Agregar `tipo_instalacion: Literal["shared", "dedicated", "onpremise", "hybrid"]`
- [ ] Actualizar `ConexionCreate` (eliminar `modulo_id`)
- [ ] Actualizar `ConexionUpdate` (eliminar `modulo_id`)
- [ ] Actualizar `ConexionRead` (eliminar `modulo_id`)
- [ ] Actualizar documentación de schemas
- [ ] Validar que los schemas compilan sin errores

#### ConexionService
- [ ] Abrir `app/modules/tenant/application/services/conexion_service.py`
- [ ] Eliminar método `obtener_conexion_principal(cliente_id, modulo_id)`
- [ ] Crear método `obtener_conexion_principal(cliente_id)` (sin modulo_id)
- [ ] Eliminar método `_validar_conexion_unica(cliente_id, modulo_id)`
- [ ] Crear método `validar_conexion_unica(cliente_id)` (sin modulo_id)
- [ ] Actualizar `crear_conexion()` para no requerir `modulo_id`
- [ ] Actualizar `actualizar_conexion()` para no usar `modulo_id`
- [ ] Integrar `ConexionRepository` en lugar de queries directas
- [ ] Agregar validación de `tipo_instalacion`
- [ ] Actualizar todos los logs para no mencionar `modulo_id`
- [ ] Ejecutar tests y corregir errores

#### Routing
- [ ] Abrir `app/core/tenant/routing.py`
- [ ] Cambiar query en `_query_connection_metadata_from_db()`:
  ```python
  # ANTES: FROM cliente_modulo_conexion
  # DESPUÉS: FROM cliente_conexion
  ```
- [ ] Eliminar cualquier referencia a `modulo_id`
- [ ] Integrar `TenantManager` en lugar de queries directas
- [ ] Integrar `ConnectionResolver` para construir connection strings
- [ ] Actualizar cache para nuevo modelo
- [ ] Validar que el cache funciona correctamente

#### Middleware
- [ ] Abrir `app/core/tenant/middleware.py`
- [ ] Integrar `TenantManager` en `TenantMiddleware`
- [ ] Actualizar carga de metadata para usar nuevo modelo
- [ ] Agregar soporte para tipos de instalación
- [ ] Validar que el contexto se establece correctamente

---

### FASE 4: ENDPOINTS (Día 6)

#### Eliminar Endpoints Obsoletos
- [ ] Abrir `app/modules/tenant/presentation/endpoints_conexiones.py`
- [ ] Eliminar endpoint:
  ```python
  @router.get("/clientes/{cliente_id}/modulos/{modulo_id}/principal/")
  ```
- [ ] Documentar breaking change en CHANGELOG.md
- [ ] Actualizar documentación OpenAPI

#### Crear Nuevos Endpoints
- [ ] Crear endpoint:
  ```python
  @router.get("/clientes/{cliente_id}/principal/")
  async def obtener_conexion_principal(cliente_id: int, ...)
  ```
- [ ] Actualizar `POST /conexiones/clientes/{cliente_id}/` (eliminar `modulo_id` del body)
- [ ] Actualizar `PUT /conexiones/{conexion_id}/` (eliminar `modulo_id` del body)
- [ ] Crear endpoint:
  ```python
  @router.get("/clientes/{cliente_id}/tipo-instalacion/")
  async def obtener_tipo_instalacion(cliente_id: int, ...)
  ```
- [ ] Agregar validación de permisos en todos los endpoints
- [ ] Agregar tests de endpoints

#### Actualizar Workflows
- [ ] Abrir `app/modules/tenant/presentation/endpoints_modulos.py`
- [ ] Actualizar `activar_modulo_completo()`:
  - Eliminar `modulo_id` de `conexion_data`
  - Separar activación de módulo de configuración de conexión
- [ ] Validar que el workflow funciona correctamente

---

### FASE 5: DATABASE (Día 7)

#### Queries SQL
- [ ] Abrir `app/infrastructure/database/queries.py`
- [ ] Actualizar `SELECT_CLIENT_CONNECTION_METADATA`:
  ```sql
  -- ANTES: FROM cliente_modulo_conexion
  -- DESPUÉS: FROM cliente_conexion
  ```
- [ ] Eliminar cualquier filtro de `modulo_id`
- [ ] Validar que las queries funcionan correctamente

#### Schema SQL
- [ ] Abrir `app/docs/database/MULTITENANT_SCHEMA.sql`
- [ ] Crear script de migración:
  ```sql
  -- Renombrar tabla
  EXEC sp_rename 'cliente_modulo_conexion', 'cliente_conexion';
  
  -- Eliminar columna modulo_id
  ALTER TABLE cliente_conexion DROP COLUMN modulo_id;
  
  -- Actualizar constraints
  -- Actualizar índices
  ```
- [ ] Probar script en ambiente de desarrollo
- [ ] Actualizar `MULTITENANT_SCHEMA.sql` con nuevo schema

#### Migración de Datos
- [ ] Ejecutar script de migración de datos (Fase 1)
- [ ] Validar que los datos migrados son correctos
- [ ] Verificar que no hay datos duplicados
- [ ] Validar que `es_conexion_principal = 1` para todos los registros

---

### FASE 6: TESTS Y DOCUMENTACIÓN (Día 8)

#### Tests
- [ ] Actualizar tests de `ConexionService`:
  - Eliminar tests que usan `modulo_id`
  - Agregar tests para nuevo modelo
- [ ] Actualizar tests de endpoints:
  - Eliminar tests de endpoints obsoletos
  - Agregar tests para nuevos endpoints
- [ ] Actualizar tests de routing:
  - Validar que usa `cliente_conexion`
  - Validar tipos de instalación
- [ ] Agregar tests para nuevos componentes:
  - `TenantManager`
  - `ConnectionResolver`
  - `ConexionRepository`
- [ ] Ejecutar suite completa de tests
- [ ] Corregir tests que fallen
- [ ] Validar cobertura > 80%

#### Documentación
- [ ] Actualizar README.md con nuevo modelo
- [ ] Actualizar documentación de API (OpenAPI/Swagger)
- [ ] Crear guía de migración para desarrolladores
- [ ] Actualizar diagramas de arquitectura
- [ ] Documentar breaking changes en CHANGELOG.md

---

### FASE 7: VALIDACIÓN Y DEPLOYMENT (Día 9-10)

#### Testing Completo
- [ ] Ejecutar suite completa de tests (todos deben pasar)
- [ ] Testing manual de endpoints:
  - [ ] Crear conexión (sin modulo_id)
  - [ ] Obtener conexión principal
  - [ ] Actualizar conexión
  - [ ] Validar tipos de instalación
- [ ] Validar cache funciona correctamente:
  - [ ] Cache hit/miss ratio
  - [ ] Invalidación de cache
- [ ] Validar tipos de instalación:
  - [ ] `shared` → BD central
  - [ ] `dedicated` → BD propia en SaaS
  - [ ] `onpremise` → BD en infraestructura cliente
  - [ ] `hybrid` → BD propia + sincronización

#### Deployment Gradual
- [ ] Configurar feature flag:
  ```python
  ENABLE_NEW_CONNECTION_MODEL = False  # Inicialmente desactivado
  ```
- [ ] Deploy en ambiente de staging
- [ ] Validar con datos reales en staging
- [ ] Monitorear logs y métricas en staging
- [ ] Activar feature flag para 10% de clientes (testing)
- [ ] Monitorear por 24 horas
- [ ] Activar feature flag para 50% de clientes
- [ ] Monitorear por 24 horas
- [ ] Activar feature flag para 100% de clientes
- [ ] Monitorear por 48 horas
- [ ] Eliminar código legacy (si todo está bien)

#### Monitoreo Post-Deployment
- [ ] Revisar logs cada hora (primeras 24 horas)
- [ ] Revisar métricas cada 2 horas:
  - [ ] Tiempo de resolución de conexión
  - [ ] Cache hit/miss ratio
  - [ ] Pool usage
  - [ ] Errores de conexión
- [ ] Validar que no hay errores relacionados con `modulo_id`
- [ ] Validar que todos los clientes pueden conectarse
- [ ] Recopilar feedback de usuarios

---

## 🔍 VALIDACIONES CRÍTICAS

### Antes de Merge
- [ ] Todos los tests pasan
- [ ] No hay referencias a `modulo_id` en código nuevo
- [ ] No hay referencias a `cliente_modulo_conexion` en código nuevo
- [ ] Documentación actualizada
- [ ] CHANGELOG.md actualizado

### Antes de Deploy a Producción
- [ ] Backup de BD creado
- [ ] Feature flag configurado
- [ ] Scripts de migración probados
- [ ] Rollback plan documentado
- [ ] Monitoreo configurado

### Después de Deploy
- [ ] Todos los clientes conectan correctamente
- [ ] Cache funciona correctamente
- [ ] No hay errores en logs
- [ ] Métricas dentro de rangos normales
- [ ] Performance aceptable

---

## 🚨 SEÑALES DE ALERTA

Si observas alguno de estos problemas, **DETENER** y revisar:

- ❌ Errores relacionados con `modulo_id` en logs
- ❌ Errores relacionados con `cliente_modulo_conexion` en logs
- ❌ Aumento significativo en tiempo de respuesta
- ❌ Cache hit ratio < 50%
- ❌ Errores de conexión > 1% de requests
- ❌ Clientes que no pueden conectarse

---

## 📞 CONTACTOS Y RECURSOS

- **Documentación Completa:** `AUDITORIA_ARQUITECTONICA_Y_PLAN_REFACTORIZACION.md`
- **Resumen Ejecutivo:** `RESUMEN_EJECUTIVO_REFACTORIZACION.md`
- **Rollback Plan:** Ver sección en documentación completa

---

**¡Éxito en la refactorización! 🚀**



