# 📊 ANÁLISIS PROFESIONAL: MÓDULOS SUPERADMIN
## Sistema Multi-Tenant Híbrido - FastAPI + Python

## ⚠️ GARANTÍAS DE IMPLEMENTACIÓN

### ✅ FILTRADO POR `cliente_id` EN TODOS LOS ENDPOINTS
**Todos los endpoints del Superadmin tendrán la capacidad de filtrar por `cliente_id` como parámetro opcional:**
- Si se proporciona `cliente_id`: Filtra usuarios/logs de ese cliente específico
- Si NO se proporciona: Muestra usuarios/logs de TODOS los clientes
- Siempre incluye información del cliente en la respuesta para contexto

### ✅ NO SE MODIFICARÁ NINGÚN ARCHIVO EXISTENTE
**Estrategia de implementación:**
- ❌ **NO se modificarán** archivos existentes (`usuarios.py`, `usuario.py`, `usuario_service.py`, etc.)
- ✅ **Solo se crearán** archivos nuevos:
  - `app/api/v1/endpoints/superadmin_usuarios.py` (NUEVO)
  - `app/api/v1/endpoints/superadmin_auditoria.py` (NUEVO)
  - `app/schemas/superadmin_usuario.py` (NUEVO)
  - `app/schemas/superadmin_auditoria.py` (NUEVO)
  - `app/services/superadmin_usuario_service.py` (NUEVO)
  - `app/services/superadmin_auditoria_service.py` (NUEVO)
- ✅ **Solo se agregarán** líneas en `app/api/v1/api.py` (no se modificarán existentes)
- ✅ Los endpoints existentes seguirán funcionando exactamente igual

**Ver documento `ESTRATEGIA_IMPLEMENTACION.md` para detalles completos.**

---

## ✅ 1. ANÁLISIS PROFUNDO DE LA BASE DE DATOS REAL

### 1.1 Tablas Relacionadas con Usuarios

#### **Tabla: `usuario`**
**Propósito:** Almacena todos los usuarios del sistema, segmentados por `cliente_id`.

**Campos Críticos para Superadmin:**
- `usuario_id` (PK): Identificador único
- `cliente_id` (FK): **CRÍTICO** - Aislamiento multi-tenant
- `nombre_usuario`: Identificador flexible (username/DNI/email/código)
- `correo`: Email del usuario
- `nombre`, `apellido`: Datos personales
- `dni`, `telefono`: Información adicional
- `es_activo`: Estado de activación
- `es_eliminado`: Soft delete
- `proveedor_autenticacion`: Método de autenticación (local/azure_ad/google/etc)
- `referencia_externa_id`, `referencia_externa_email`: Para SSO
- `fecha_creacion`, `fecha_actualizacion`: Auditoría temporal
- `fecha_ultimo_acceso`: Último login exitoso
- `intentos_fallidos`, `fecha_bloqueo`: Seguridad
- `correo_confirmado`: Estado de verificación
- `requiere_cambio_contrasena`: Flag de seguridad
- `ultimo_ip`: IP del último acceso
- `sincronizado_desde`, `fecha_ultima_sincronizacion`: Para instalaciones híbridas

**Índices Relevantes:**
- `IDX_usuario_cliente`: Optimizado para queries por cliente
- `IDX_usuario_correo`: Búsqueda por email
- `IDX_usuario_dni`: Búsqueda por DNI
- `IDX_usuario_referencia_externa`: Para usuarios SSO

---

#### **Tabla: `usuario_rol`**
**Propósito:** Relación N:N entre usuarios y roles.

**Campos Críticos:**
- `usuario_rol_id` (PK)
- `usuario_id` (FK)
- `rol_id` (FK)
- `cliente_id` (FK): Desnormalizado para queries rápidas
- `fecha_asignacion`: Cuándo se asignó el rol
- `fecha_expiracion`: Para roles temporales (NULL = permanente)
- `es_activo`: Si la asignación está activa
- `asignado_por_usuario_id`: Auditoría de quién asignó

**Índices:**
- `IDX_usuario_rol_usuario`: Optimizado para obtener roles de un usuario
- `IDX_usuario_rol_cliente`: Para queries por cliente

---

#### **Tabla: `rol`**
**Propósito:** Roles del sistema (globales y por cliente).

**Campos Críticos:**
- `rol_id` (PK)
- `cliente_id` (FK, NULL = rol global del sistema)
- `codigo_rol`: Código único para roles del sistema (ej: 'SUPER_ADMIN', 'ADMIN')
- `nombre`: Nombre descriptivo
- `descripcion`: Descripción del rol
- `es_rol_sistema`: Si es rol del sistema (no editable)
- `nivel_acceso`: Nivel jerárquico (1-5)
- `es_activo`: Estado del rol
- `fecha_creacion`, `fecha_actualizacion`: Auditoría

**Índices:**
- `IDX_rol_cliente`: Para roles por cliente
- `IDX_rol_codigo`: Para roles del sistema

---

### 1.2 Tablas Relacionadas con Auditoría

#### **Tabla: `auth_audit_log`**
**Propósito:** Log completo de eventos de autenticación y seguridad.

**Campos Críticos:**
- `log_id` (PK)
- `cliente_id` (FK): **CRÍTICO** - Aislamiento multi-tenant
- `usuario_id` (FK, NULL si evento anónimo)
- `evento`: Tipo de evento (login_success, login_failed, logout, token_refresh, password_change, etc.)
- `nombre_usuario_intento`: Para logins fallidos
- `descripcion`: Descripción detallada
- `exito`: Si el evento fue exitoso
- `codigo_error`: Código de error si aplica
- `ip_address`: IP desde donde se originó
- `user_agent`: User agent del navegador/app
- `device_info`: Información del dispositivo
- `geolocation`: País/ciudad (si se implementa)
- `metadata_json`: JSON con datos adicionales
- `fecha_evento`: Timestamp del evento

**Índices Optimizados:**
- `IDX_audit_cliente_fecha`: Para queries por cliente y fecha
- `IDX_audit_usuario_fecha`: Para auditoría por usuario
- `IDX_audit_evento`: Para filtrar por tipo de evento
- `IDX_audit_exito`: Para filtrar éxitos/fallos
- `IDX_audit_ip`: Para análisis de IPs

**Eventos Registrados:**
- **Login:** `login_success`, `login_failed`, `login_blocked`
- **SSO:** `sso_login_success`, `sso_login_failed`
- **Logout:** `logout`, `logout_forced`, `logout_timeout`
- **Tokens:** `token_refresh`, `token_revoked`, `token_expired`
- **Contraseña:** `password_change`, `password_reset_request`, `password_reset_complete`
- **Cuenta:** `account_locked`, `account_unlocked`, `account_activated`, `account_deactivated`
- **Seguridad:** `email_verified`, `2fa_enabled`, `2fa_disabled`, `2fa_verified`, `2fa_failed`
- **Anomalías:** `suspicious_activity`, `ip_blocked`

---

#### **Tabla: `refresh_tokens`**
**Propósito:** Almacena refresh tokens JWT para tracking de sesiones.

**Campos Críticos para Superadmin:**
- `token_id` (PK)
- `cliente_id` (FK)
- `usuario_id` (FK)
- `token_hash`: SHA-256 del token (nunca texto plano)
- `expires_at`: Fecha de expiración
- `is_revoked`: Si fue revocado
- `revoked_at`, `revoked_reason`: Información de revocación
- `client_type`: Tipo de cliente (web/mobile/desktop)
- `device_name`: Nombre del dispositivo
- `device_id`: ID único del dispositivo
- `ip_address`: IP desde donde se creó
- `user_agent`: User agent
- `created_at`: Fecha de creación
- `last_used_at`: Última vez usado
- `uso_count`: Cuántas veces se usó

**Índices:**
- `IDX_refresh_token_usuario_cliente`: Para sesiones por usuario
- `IDX_refresh_token_active`: Para tokens activos
- `IDX_refresh_token_device`: Para tracking por dispositivo

---

#### **Tabla: `log_sincronizacion_usuario`**
**Propósito:** Auditoría de sincronización de usuarios entre instalaciones (cloud/onpremise/hybrid).

**Campos Críticos:**
- `log_id` (PK)
- `cliente_origen_id` (FK): De dónde viene
- `cliente_destino_id` (FK): Hacia dónde va
- `usuario_id` (FK): Usuario sincronizado
- `tipo_sincronizacion`: 'manual', 'push_auto', 'pull_auto', 'scheduled'
- `direccion`: 'push', 'pull', 'bidireccional'
- `operacion`: 'create', 'update', 'delete'
- `estado`: 'exitoso', 'fallido', 'parcial', 'pendiente'
- `mensaje_error`: Si falló
- `campos_sincronizados`: JSON array con campos actualizados
- `cambios_detectados`: JSON con diff antes/después
- `hash_antes`, `hash_despues`: Para validación de integridad
- `fecha_sincronizacion`: Timestamp
- `usuario_ejecutor_id`: Quién ejecutó (NULL = automático)
- `duracion_ms`: Tiempo de la operación

**Índices:**
- `IDX_log_sync_usuario`: Para auditoría por usuario
- `IDX_log_sync_origen`: Para sincronizaciones desde un cliente
- `IDX_log_sync_destino`: Para sincronizaciones hacia un cliente
- `IDX_log_sync_fecha`: Para queries temporales

---

### 1.3 Tablas Relacionadas con Clientes

#### **Tabla: `cliente`**
**Propósito:** Core del sistema multi-tenant.

**Campos Relevantes para Superadmin:**
- `cliente_id` (PK)
- `codigo_cliente`: Código único
- `subdominio`: Subdominio único
- `razon_social`, `nombre_comercial`: Información del cliente
- `tipo_instalacion`: 'cloud', 'onpremise', 'hybrid'
- `estado_suscripcion`: 'trial', 'activo', 'suspendido', 'cancelado', 'moroso'
- `plan_suscripcion`: 'trial', 'basico', 'profesional', 'enterprise'
- `fecha_ultimo_acceso`: Última vez que algún usuario accedió
- `sincronizacion_habilitada`: Si permite sincronización
- `ultima_sincronizacion`: Última sincronización

---

### 1.4 Análisis de Capacidades Actuales

#### ✅ **Lo que SÍ está preparado:**

1. **Ver usuarios por tenant:**
   - ✅ Tabla `usuario` tiene `cliente_id` con índice optimizado
   - ✅ Queries existentes ya filtran por `cliente_id`

2. **Ver roles del usuario:**
   - ✅ Tabla `usuario_rol` relaciona usuarios con roles
   - ✅ Tabla `rol` tiene información completa
   - ✅ Índices optimizados para JOINs

3. **Ver estado y actividad:**
   - ✅ Campo `es_activo` en usuario
   - ✅ Campo `fecha_ultimo_acceso` en usuario
   - ✅ Campo `es_eliminado` para soft delete

4. **Auditar últimos accesos:**
   - ✅ Campo `fecha_ultimo_acceso` en `usuario`
   - ✅ Tabla `auth_audit_log` con eventos de login
   - ✅ Tabla `refresh_tokens` con `last_used_at`

5. **Auditar movimientos relevantes:**
   - ✅ Tabla `auth_audit_log` con múltiples tipos de eventos
   - ✅ Campos de auditoría en `usuario` (fecha_creacion, fecha_actualizacion)
   - ✅ Campo `asignado_por_usuario_id` en `usuario_rol`

6. **Auditar autenticaciones:**
   - ✅ Tabla `auth_audit_log` con eventos: `login_success`, `login_failed`, `sso_login_success`, etc.
   - ✅ Campos `ip_address`, `user_agent`, `device_info` para contexto

7. **Manejar sincronización:**
   - ✅ Tabla `log_sincronizacion_usuario` completa
   - ✅ Campos de sincronización en `usuario` (sincronizado_desde, fecha_ultima_sincronizacion)
   - ✅ Campos en `cliente` (sincronizacion_habilitada, ultima_sincronizacion)

---

#### ⚠️ **Lo que FALTA o necesita atención:**

1. **Sesiones activas:**
   - ⚠️ Existe `refresh_tokens` pero falta endpoint para listar sesiones activas por usuario/cliente
   - ⚠️ No hay campo directo de "sesión activa" - se debe calcular con `is_revoked = 0 AND expires_at > NOW()`

2. **Auditoría de cambios en datos:**
   - ⚠️ No hay tabla de auditoría de cambios en campos de usuario (solo `fecha_actualizacion`)
   - ⚠️ No se registra quién hizo cambios (solo en `usuario_rol.asignado_por_usuario_id`)

3. **Actividad detallada (no solo autenticación):**
   - ⚠️ `auth_audit_log` solo cubre autenticación/seguridad
   - ⚠️ No hay log de acciones de negocio (crear/editar/eliminar registros)

4. **Geolocalización:**
   - ⚠️ Campo `geolocation` existe pero probablemente no está poblado

---

### 1.5 Riesgos e Inconsistencias Multi-Tenant

#### ✅ **Buenas Prácticas Implementadas:**

1. **Aislamiento por cliente_id:**
   - ✅ Todas las tablas críticas tienen `cliente_id`
   - ✅ Índices optimizados para queries por cliente
   - ✅ Constraints UNIQUE incluyen `cliente_id` (ej: `UQ_usuario_cliente_nombre`)

2. **Soft Delete:**
   - ✅ Campo `es_eliminado` en `usuario` preserva auditoría

3. **Auditoría temporal:**
   - ✅ Campos `fecha_creacion`, `fecha_actualizacion` en tablas principales

#### ⚠️ **Riesgos Identificados:**

1. **Roles globales vs por cliente:**
   - ⚠️ `rol.cliente_id` puede ser NULL (rol global)
   - ⚠️ Superadmin debe validar que roles globales no se asignen incorrectamente a usuarios de clientes específicos

2. **Sincronización en instalaciones híbridas:**
   - ⚠️ `log_sincronizacion_usuario` puede tener `cliente_origen_id` y `cliente_destino_id` diferentes
   - ⚠️ Superadmin debe poder ver sincronizaciones cruzadas entre clientes

3. **Tokens compartidos:**
   - ⚠️ `refresh_tokens` tiene `cliente_id` pero un token podría teóricamente usarse en múltiples clientes si hay vulnerabilidad

---

### 1.6 Campos que Deben Mostrarse en UI del Superadmin

#### **Vista: Listado Global de Usuarios**
- `usuario_id`
- `nombre_usuario`
- `correo`
- `nombre`, `apellido`
- `cliente_id` + `razon_social` (JOIN con `cliente`)
- `es_activo`
- `fecha_ultimo_acceso`
- `proveedor_autenticacion`
- `fecha_creacion`
- **Roles:** Lista de nombres de roles (JOIN con `usuario_rol` y `rol`)

#### **Vista: Detalle de Usuario**
- Todos los campos de listado +
- `dni`, `telefono`
- `correo_confirmado`
- `intentos_fallidos`
- `fecha_bloqueo`
- `ultimo_ip`
- `sincronizado_desde`, `fecha_ultima_sincronizacion`
- `es_eliminado`
- **Sesiones activas:** De `refresh_tokens` (is_revoked=0, expires_at > NOW())
- **Historial de roles:** De `usuario_rol` con `fecha_asignacion`, `asignado_por_usuario_id`

#### **Vista: Auditoría de Autenticación**
- `log_id`
- `fecha_evento`
- `evento`
- `usuario_id` + `nombre_usuario` (JOIN)
- `cliente_id` + `razon_social` (JOIN)
- `exito`
- `ip_address`
- `user_agent`
- `device_info`
- `codigo_error` (si aplica)

#### **Vista: Auditoría de Sincronización**
- `log_id`
- `fecha_sincronizacion`
- `usuario_id` + `nombre_usuario` (JOIN)
- `cliente_origen_id` + `razon_social_origen` (JOIN)
- `cliente_destino_id` + `razon_social_destino` (JOIN)
- `tipo_sincronizacion`
- `direccion`
- `operacion`
- `estado`
- `mensaje_error` (si aplica)
- `duracion_ms`

---

## ✅ 2. MAPPING TABLA → ENTIDAD → USO UI

| Tabla | Campo | Descripción | Vista donde se usa (Superadmin) |
|-------|-------|-------------|--------------------------------|
| **usuario** | usuario_id | ID único del usuario | Todas las vistas |
| **usuario** | cliente_id | ID del cliente (tenant) | Listado Global, Detalle Usuario, Filtros |
| **usuario** | nombre_usuario | Identificador del usuario | Listado Global, Detalle Usuario, Búsqueda |
| **usuario** | correo | Email del usuario | Listado Global, Detalle Usuario, Búsqueda |
| **usuario** | nombre | Nombre real | Listado Global, Detalle Usuario, Búsqueda |
| **usuario** | apellido | Apellido real | Listado Global, Detalle Usuario, Búsqueda |
| **usuario** | dni | DNI del usuario | Detalle Usuario |
| **usuario** | telefono | Teléfono | Detalle Usuario |
| **usuario** | es_activo | Estado activo/inactivo | Listado Global (filtro), Detalle Usuario |
| **usuario** | es_eliminado | Soft delete | Listado Global (excluir), Detalle Usuario |
| **usuario** | proveedor_autenticacion | Método de auth (local/SSO) | Listado Global (filtro), Detalle Usuario |
| **usuario** | fecha_creacion | Fecha de creación | Listado Global (ordenar), Detalle Usuario |
| **usuario** | fecha_ultimo_acceso | Último login | Listado Global (ordenar), Detalle Usuario, Actividad |
| **usuario** | fecha_actualizacion | Última modificación | Detalle Usuario |
| **usuario** | correo_confirmado | Email verificado | Detalle Usuario |
| **usuario** | intentos_fallidos | Intentos fallidos de login | Detalle Usuario, Seguridad |
| **usuario** | fecha_bloqueo | Fecha de bloqueo | Detalle Usuario, Seguridad |
| **usuario** | ultimo_ip | IP del último acceso | Detalle Usuario, Seguridad |
| **usuario** | sincronizado_desde | Origen de sincronización | Detalle Usuario, Sincronización |
| **usuario** | fecha_ultima_sincronizacion | Última sincronización | Detalle Usuario, Sincronización |
| **usuario** | referencia_externa_id | ID en proveedor SSO | Detalle Usuario (si SSO) |
| **usuario** | referencia_externa_email | Email en proveedor SSO | Detalle Usuario (si SSO) |
| **usuario_rol** | usuario_rol_id | ID de asignación | Detalle Usuario (historial roles) |
| **usuario_rol** | usuario_id | FK a usuario | Detalle Usuario |
| **usuario_rol** | rol_id | FK a rol | Detalle Usuario (lista roles) |
| **usuario_rol** | cliente_id | FK a cliente | Validación multi-tenant |
| **usuario_rol** | fecha_asignacion | Cuándo se asignó | Detalle Usuario (historial) |
| **usuario_rol** | fecha_expiracion | Expiración del rol | Detalle Usuario (si temporal) |
| **usuario_rol** | es_activo | Si la asignación está activa | Detalle Usuario (roles actuales) |
| **usuario_rol** | asignado_por_usuario_id | Quién asignó | Detalle Usuario (auditoría) |
| **rol** | rol_id | ID único del rol | Detalle Usuario (lista roles) |
| **rol** | cliente_id | FK a cliente (NULL = global) | Detalle Usuario, Validación |
| **rol** | codigo_rol | Código del rol (SUPER_ADMIN, etc) | Detalle Usuario (tipo de rol) |
| **rol** | nombre | Nombre del rol | Listado Global, Detalle Usuario |
| **rol** | descripcion | Descripción del rol | Detalle Usuario |
| **rol** | nivel_acceso | Nivel jerárquico (1-5) | Detalle Usuario (privilegios) |
| **rol** | es_rol_sistema | Si es rol del sistema | Detalle Usuario (no editable) |
| **rol** | es_activo | Estado del rol | Detalle Usuario (validación) |
| **cliente** | cliente_id | ID único del cliente | Listado Global, Filtros |
| **cliente** | codigo_cliente | Código del cliente | Listado Global, Búsqueda |
| **cliente** | subdominio | Subdominio único | Listado Global, Búsqueda |
| **cliente** | razon_social | Razón social | Listado Global, Detalle Usuario (contexto) |
| **cliente** | nombre_comercial | Nombre comercial | Listado Global |
| **cliente** | tipo_instalacion | cloud/onpremise/hybrid | Listado Global (filtro), Sincronización |
| **cliente** | estado_suscripcion | Estado de suscripción | Listado Global (filtro) |
| **cliente** | fecha_ultimo_acceso | Último acceso del cliente | Listado Global (ordenar) |
| **auth_audit_log** | log_id | ID único del log | Auditoría Autenticación |
| **auth_audit_log** | cliente_id | FK a cliente | Auditoría Autenticación (filtro) |
| **auth_audit_log** | usuario_id | FK a usuario | Auditoría Autenticación (filtro) |
| **auth_audit_log** | evento | Tipo de evento | Auditoría Autenticación (filtro) |
| **auth_audit_log** | nombre_usuario_intento | Usuario intentado (login fallido) | Auditoría Autenticación |
| **auth_audit_log** | descripcion | Descripción del evento | Auditoría Autenticación |
| **auth_audit_log** | exito | Si fue exitoso | Auditoría Autenticación (filtro) |
| **auth_audit_log** | codigo_error | Código de error | Auditoría Autenticación |
| **auth_audit_log** | ip_address | IP del evento | Auditoría Autenticación, Seguridad |
| **auth_audit_log** | user_agent | User agent | Auditoría Autenticación |
| **auth_audit_log** | device_info | Info del dispositivo | Auditoría Autenticación |
| **auth_audit_log** | geolocation | Geolocalización | Auditoría Autenticación (si disponible) |
| **auth_audit_log** | fecha_evento | Timestamp del evento | Auditoría Autenticación (ordenar, filtro) |
| **auth_audit_log** | metadata_json | JSON adicional | Auditoría Autenticación (detalles) |
| **refresh_tokens** | token_id | ID único del token | Sesiones Activas |
| **refresh_tokens** | cliente_id | FK a cliente | Sesiones Activas (filtro) |
| **refresh_tokens** | usuario_id | FK a usuario | Sesiones Activas (filtro) |
| **refresh_tokens** | token_hash | Hash del token | NO EXPONER (seguridad) |
| **refresh_tokens** | expires_at | Fecha de expiración | Sesiones Activas (calcular activas) |
| **refresh_tokens** | is_revoked | Si fue revocado | Sesiones Activas (filtro) |
| **refresh_tokens** | revoked_at | Cuándo fue revocado | Sesiones Activas |
| **refresh_tokens** | revoked_reason | Motivo de revocación | Sesiones Activas |
| **refresh_tokens** | client_type | Tipo de cliente (web/mobile/desktop) | Sesiones Activas |
| **refresh_tokens** | device_name | Nombre del dispositivo | Sesiones Activas |
| **refresh_tokens** | device_id | ID del dispositivo | Sesiones Activas |
| **refresh_tokens** | ip_address | IP de creación | Sesiones Activas |
| **refresh_tokens** | user_agent | User agent | Sesiones Activas |
| **refresh_tokens** | created_at | Fecha de creación | Sesiones Activas (ordenar) |
| **refresh_tokens** | last_used_at | Última vez usado | Sesiones Activas (ordenar) |
| **refresh_tokens** | uso_count | Cuántas veces se usó | Sesiones Activas |
| **log_sincronizacion_usuario** | log_id | ID único del log | Auditoría Sincronización |
| **log_sincronizacion_usuario** | cliente_origen_id | FK a cliente origen | Auditoría Sincronización |
| **log_sincronizacion_usuario** | cliente_destino_id | FK a cliente destino | Auditoría Sincronización |
| **log_sincronizacion_usuario** | usuario_id | FK a usuario | Auditoría Sincronización (filtro) |
| **log_sincronizacion_usuario** | tipo_sincronizacion | Tipo (manual/auto/scheduled) | Auditoría Sincronización (filtro) |
| **log_sincronizacion_usuario** | direccion | push/pull/bidireccional | Auditoría Sincronización (filtro) |
| **log_sincronizacion_usuario** | operacion | create/update/delete | Auditoría Sincronización (filtro) |
| **log_sincronizacion_usuario** | estado | exitoso/fallido/parcial/pendiente | Auditoría Sincronización (filtro) |
| **log_sincronizacion_usuario** | mensaje_error | Error si falló | Auditoría Sincronización |
| **log_sincronizacion_usuario** | campos_sincronizados | JSON array de campos | Auditoría Sincronización (detalles) |
| **log_sincronizacion_usuario** | cambios_detectados | JSON diff antes/después | Auditoría Sincronización (detalles) |
| **log_sincronizacion_usuario** | fecha_sincronizacion | Timestamp | Auditoría Sincronización (ordenar, filtro) |
| **log_sincronizacion_usuario** | usuario_ejecutor_id | Quién ejecutó | Auditoría Sincronización |
| **log_sincronizacion_usuario** | duracion_ms | Duración en ms | Auditoría Sincronización |

---

## ✅ 3. DEFINICIÓN DE ENDPOINTS NECESARIOS

### 3.1 Módulo Usuarios (Superadmin)

#### **GET `/api/v1/superadmin/usuarios/`**
**Método:** GET  
**Descripción:** Listado global de usuarios con filtro opcional por cliente (solo Superadmin).

**Parámetros de Query:**
- `cliente_id` (int, **optional**): **FILTRAR por cliente específico** - Si se proporciona, solo muestra usuarios de ese cliente. Si NO se proporciona, muestra usuarios de TODOS los clientes.
- `page` (int, default=1, ge=1): Número de página
- `limit` (int, default=20, ge=1, le=100): Registros por página
- `search` (str, optional): Búsqueda en nombre_usuario, correo, nombre, apellido
- `es_activo` (bool, optional): Filtrar por estado activo/inactivo
- `proveedor_autenticacion` (str, optional): Filtrar por método de autenticación
- `ordenar_por` (str, optional): Campo para ordenar (fecha_creacion, fecha_ultimo_acceso, nombre_usuario)
- `orden` (str, optional): 'asc' o 'desc' (default: 'desc')

**Consideraciones Multi-Tenant:**
- ✅ **FILTRADO POR CLIENTE:** Parámetro `cliente_id` opcional permite filtrar por cliente específico
- ✅ Si `cliente_id` es proporcionado: Valida que el cliente existe y filtra usuarios de ese cliente
- ✅ Si `cliente_id` NO es proporcionado: Muestra usuarios de TODOS los clientes
- ✅ Siempre incluye información del cliente (razon_social, subdominio) en respuesta
- ✅ Filtrar automáticamente `es_eliminado = 0` (o permitir incluir eliminados con flag)

**Ejemplo de Respuesta JSON:**
```json
{
  "usuarios": [
    {
      "usuario_id": 1,
      "nombre_usuario": "juan.perez",
      "correo": "juan@empresa.com",
      "nombre": "Juan",
      "apellido": "Pérez",
      "cliente_id": 2,
      "cliente": {
        "cliente_id": 2,
        "razon_social": "ACME Corporation",
        "subdominio": "acme"
      },
      "es_activo": true,
      "proveedor_autenticacion": "local",
      "fecha_ultimo_acceso": "2024-01-15T10:30:00Z",
      "fecha_creacion": "2024-01-01T08:00:00Z",
      "roles": [
        {
          "rol_id": 5,
          "nombre": "Administrador",
          "nivel_acceso": 4
        }
      ]
    }
  ],
  "total_usuarios": 150,
  "pagina_actual": 1,
  "total_paginas": 8
}
```

---

#### **GET `/api/v1/superadmin/usuarios/{usuario_id}/`**
**Método:** GET  
**Descripción:** Detalle completo de un usuario específico (solo Superadmin).

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario

**Consideraciones Multi-Tenant:**
- Superadmin puede ver usuarios de cualquier cliente
- Incluir información completa del cliente
- Incluir historial de roles (no solo activos)

**Ejemplo de Respuesta JSON:**
```json
{
  "usuario_id": 1,
  "nombre_usuario": "juan.perez",
  "correo": "juan@empresa.com",
  "nombre": "Juan",
  "apellido": "Pérez",
  "dni": "42799662",
  "telefono": "+51987654321",
  "cliente_id": 2,
  "cliente": {
    "cliente_id": 2,
    "razon_social": "ACME Corporation",
    "subdominio": "acme",
    "tipo_instalacion": "cloud",
    "estado_suscripcion": "activo"
  },
  "es_activo": true,
  "es_eliminado": false,
  "proveedor_autenticacion": "local",
  "referencia_externa_id": null,
  "correo_confirmado": true,
  "intentos_fallidos": 0,
  "fecha_bloqueo": null,
  "ultimo_ip": "192.168.1.100",
  "fecha_creacion": "2024-01-01T08:00:00Z",
  "fecha_ultimo_acceso": "2024-01-15T10:30:00Z",
  "fecha_actualizacion": "2024-01-10T14:20:00Z",
  "sincronizado_desde": null,
  "fecha_ultima_sincronizacion": null,
  "roles": [
    {
      "rol_id": 5,
      "nombre": "Administrador",
      "nivel_acceso": 4,
      "fecha_asignacion": "2024-01-01T08:00:00Z",
      "asignado_por_usuario_id": 1,
      "es_activo": true
    }
  ],
  "access_level": 4,
  "is_super_admin": false,
  "user_type": "tenant_admin"
}
```

---

#### **GET `/api/v1/superadmin/usuarios/{usuario_id}/roles/`**
**Método:** GET  
**Descripción:** Lista de roles (activos e históricos) de un usuario.

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario

**Parámetros de Query:**
- `solo_activos` (bool, default=false): Si solo mostrar roles activos

**Ejemplo de Respuesta JSON:**
```json
{
  "usuario_id": 1,
  "roles": [
    {
      "usuario_rol_id": 10,
      "rol_id": 5,
      "rol": {
        "rol_id": 5,
        "nombre": "Administrador",
        "codigo_rol": null,
        "nivel_acceso": 4,
        "es_rol_sistema": false
      },
      "fecha_asignacion": "2024-01-01T08:00:00Z",
      "fecha_expiracion": null,
      "es_activo": true,
      "asignado_por_usuario_id": 1,
      "asignado_por": {
        "usuario_id": 1,
        "nombre_usuario": "admin"
      }
    }
  ]
}
```

---

#### **GET `/api/v1/superadmin/usuarios/{usuario_id}/actividad/`**
**Método:** GET  
**Descripción:** Actividad reciente del usuario (últimos accesos, cambios, etc.).

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario

**Parámetros de Query:**
- `limite` (int, default=50, ge=1, le=200): Número de eventos a retornar
- `tipo_evento` (str, optional): Filtrar por tipo de evento

**Ejemplo de Respuesta JSON:**
```json
{
  "usuario_id": 1,
  "ultimo_acceso": "2024-01-15T10:30:00Z",
  "ultimo_ip": "192.168.1.100",
  "total_eventos": 150,
  "eventos": [
    {
      "log_id": 1001,
      "fecha_evento": "2024-01-15T10:30:00Z",
      "evento": "login_success",
      "exito": true,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "device_info": "Chrome en Windows 11"
    }
  ]
}
```

---

#### **GET `/api/v1/superadmin/usuarios/{usuario_id}/sesiones/`**
**Método:** GET  
**Descripción:** Sesiones activas del usuario (tokens refresh no revocados).

**Parámetros de Ruta:**
- `usuario_id` (int): ID del usuario

**Parámetros de Query:**
- `solo_activas` (bool, default=true): Si solo mostrar sesiones activas

**Ejemplo de Respuesta JSON:**
```json
{
  "usuario_id": 1,
  "total_sesiones": 3,
  "sesiones_activas": 2,
  "sesiones": [
    {
      "token_id": 50,
      "client_type": "web",
      "device_name": "Chrome en Windows 11",
      "device_id": null,
      "ip_address": "192.168.1.100",
      "created_at": "2024-01-15T08:00:00Z",
      "last_used_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-02-15T08:00:00Z",
      "is_revoked": false,
      "uso_count": 15
    }
  ]
}
```

---

#### **GET `/api/v1/superadmin/clientes/{cliente_id}/usuarios/`**
**Método:** GET  
**Descripción:** Listado de usuarios de un cliente específico.

**Parámetros de Ruta:**
- `cliente_id` (int): ID del cliente

**Parámetros de Query:**
- `page` (int, default=1): Número de página
- `limit` (int, default=20): Registros por página
- `search` (str, optional): Búsqueda
- `es_activo` (bool, optional): Filtrar por estado

**Consideraciones Multi-Tenant:**
- Validar que el cliente existe
- Incluir información del cliente en respuesta

---

### 3.2 Módulo Auditoría (Superadmin)

#### **GET `/api/v1/superadmin/auditoria/autenticacion/`**
**Método:** GET  
**Descripción:** Logs de autenticación con filtros avanzados y filtro opcional por cliente.

**Parámetros de Query:**
- `cliente_id` (int, **optional**): **FILTRAR por cliente específico** - Si se proporciona, solo muestra logs de ese cliente. Si NO se proporciona, muestra logs de TODOS los clientes.
- `page` (int, default=1): Número de página
- `limit` (int, default=50): Registros por página
- `usuario_id` (int, optional): Filtrar por usuario
- `evento` (str, optional): Filtrar por tipo de evento (login_success, login_failed, etc.)
- `exito` (bool, optional): Filtrar por éxito/fallo
- `fecha_desde` (datetime, optional): Fecha inicial
- `fecha_hasta` (datetime, optional): Fecha final
- `ip_address` (str, optional): Filtrar por IP
- `ordenar_por` (str, default='fecha_evento'): Campo para ordenar
- `orden` (str, default='desc'): 'asc' o 'desc'

**Consideraciones Multi-Tenant:**
- ✅ **FILTRADO POR CLIENTE:** Parámetro `cliente_id` opcional permite filtrar por cliente específico
- ✅ Si `cliente_id` es proporcionado: Valida que el cliente existe y filtra logs de ese cliente
- ✅ Si `cliente_id` NO es proporcionado: Muestra logs de TODOS los clientes
- ✅ Siempre incluye información del cliente en respuesta

**Ejemplo de Respuesta JSON:**
```json
{
  "logs": [
    {
      "log_id": 1001,
      "fecha_evento": "2024-01-15T10:30:00Z",
      "cliente_id": 2,
      "cliente": {
        "cliente_id": 2,
        "razon_social": "ACME Corporation"
      },
      "usuario_id": 1,
      "usuario": {
        "usuario_id": 1,
        "nombre_usuario": "juan.perez"
      },
      "evento": "login_success",
      "descripcion": "Login exitoso",
      "exito": true,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "device_info": "Chrome en Windows 11",
      "geolocation": "Lima, Peru"
    }
  ],
  "total_logs": 5000,
  "pagina_actual": 1,
  "total_paginas": 100
}
```

---

#### **GET `/api/v1/superadmin/auditoria/autenticacion/{log_id}/`**
**Método:** GET  
**Descripción:** Detalle completo de un log de autenticación.

**Parámetros de Ruta:**
- `log_id` (int): ID del log

**Ejemplo de Respuesta JSON:**
```json
{
  "log_id": 1001,
  "fecha_evento": "2024-01-15T10:30:00Z",
  "cliente_id": 2,
  "cliente": {
    "cliente_id": 2,
    "razon_social": "ACME Corporation",
    "subdominio": "acme"
  },
  "usuario_id": 1,
  "usuario": {
    "usuario_id": 1,
    "nombre_usuario": "juan.perez",
    "correo": "juan@empresa.com"
  },
  "evento": "login_success",
  "nombre_usuario_intento": null,
  "descripcion": "Login exitoso",
  "exito": true,
  "codigo_error": null,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "device_info": "Chrome en Windows 11",
  "geolocation": "Lima, Peru",
  "metadata_json": {
    "session_duration": 3600,
    "pages_visited": 15
  }
}
```

---

#### **GET `/api/v1/superadmin/auditoria/sincronizacion/`**
**Método:** GET  
**Descripción:** Logs de sincronización entre instalaciones (cloud/onpremise/hybrid) con filtros por cliente.

**Parámetros de Query:**
- `cliente_origen_id` (int, **optional**): **FILTRAR por cliente origen** - Si se proporciona, solo muestra sincronizaciones desde ese cliente
- `cliente_destino_id` (int, **optional**): **FILTRAR por cliente destino** - Si se proporciona, solo muestra sincronizaciones hacia ese cliente
- `page` (int, default=1): Número de página
- `limit` (int, default=50): Registros por página
- `usuario_id` (int, optional): Filtrar por usuario
- `tipo_sincronizacion` (str, optional): manual/push_auto/pull_auto/scheduled
- `direccion` (str, optional): push/pull/bidireccional
- `operacion` (str, optional): create/update/delete
- `estado` (str, optional): exitoso/fallido/parcial/pendiente
- `fecha_desde` (datetime, optional): Fecha inicial
- `fecha_hasta` (datetime, optional): Fecha final
- `ordenar_por` (str, default='fecha_sincronizacion'): Campo para ordenar
- `orden` (str, default='desc'): 'asc' o 'desc'

**Consideraciones Multi-Tenant:**
- ✅ **FILTRADO POR CLIENTE:** Parámetros `cliente_origen_id` y `cliente_destino_id` opcionales permiten filtrar por cliente
- ✅ Si se proporcionan filtros de cliente: Valida que los clientes existen y filtra logs de sincronización
- ✅ Si NO se proporcionan filtros: Muestra sincronizaciones entre TODOS los clientes
- ✅ Siempre incluye información de clientes origen y destino en respuesta

**Ejemplo de Respuesta JSON:**
```json
{
  "logs": [
    {
      "log_id": 2001,
      "fecha_sincronizacion": "2024-01-15T09:00:00Z",
      "cliente_origen_id": 2,
      "cliente_origen": {
        "cliente_id": 2,
        "razon_social": "ACME Corporation"
      },
      "cliente_destino_id": 1,
      "cliente_destino": {
        "cliente_id": 1,
        "razon_social": "Sistema Central"
      },
      "usuario_id": 1,
      "usuario": {
        "usuario_id": 1,
        "nombre_usuario": "juan.perez"
      },
      "tipo_sincronizacion": "push_auto",
      "direccion": "push",
      "operacion": "update",
      "estado": "exitoso",
      "mensaje_error": null,
      "campos_sincronizados": ["nombre", "correo", "es_activo"],
      "cambios_detectados": {
        "nombre": {
          "antes": "Juan",
          "despues": "Juan Carlos"
        }
      },
      "duracion_ms": 250,
      "usuario_ejecutor_id": null
    }
  ],
  "total_logs": 200,
  "pagina_actual": 1,
  "total_paginas": 4
}
```

---

#### **GET `/api/v1/superadmin/auditoria/actividad/`**
**Método:** GET  
**Descripción:** Logs de actividad general (combinación de autenticación y otros eventos).

**Parámetros de Query:**
- Similar a `/auditoria/autenticacion/` pero puede incluir eventos adicionales
- `tipo_actividad` (str, optional): 'autenticacion', 'sincronizacion', 'todos'

**Nota:** Este endpoint puede combinar datos de `auth_audit_log` y `log_sincronizacion_usuario` en una vista unificada.

---

#### **GET `/api/v1/superadmin/auditoria/estadisticas/`**
**Método:** GET  
**Descripción:** Estadísticas agregadas de auditoría con filtro opcional por cliente.

**Parámetros de Query:**
- `cliente_id` (int, **optional**): **FILTRAR por cliente específico** - Si se proporciona, solo muestra estadísticas de ese cliente. Si NO se proporciona, muestra estadísticas de TODOS los clientes.
- `fecha_desde` (datetime, optional): Fecha inicial
- `fecha_hasta` (datetime, optional): Fecha final

**Consideraciones Multi-Tenant:**
- ✅ **FILTRADO POR CLIENTE:** Parámetro `cliente_id` opcional permite filtrar por cliente específico
- ✅ Si `cliente_id` es proporcionado: Valida que el cliente existe y calcula estadísticas solo de ese cliente
- ✅ Si `cliente_id` NO es proporcionado: Calcula estadísticas agregadas de TODOS los clientes

**Ejemplo de Respuesta JSON:**
```json
{
  "periodo": {
    "fecha_desde": "2024-01-01T00:00:00Z",
    "fecha_hasta": "2024-01-31T23:59:59Z"
  },
  "autenticacion": {
    "total_eventos": 10000,
    "login_exitosos": 9500,
    "login_fallidos": 500,
    "eventos_por_tipo": {
      "login_success": 9500,
      "login_failed": 500,
      "logout": 8000,
      "password_change": 50
    }
  },
  "sincronizacion": {
    "total_sincronizaciones": 200,
    "exitosas": 180,
    "fallidas": 20,
    "por_tipo": {
      "push_auto": 150,
      "pull_auto": 30,
      "manual": 20
    }
  },
  "top_ips": [
    {
      "ip_address": "192.168.1.100",
      "total_eventos": 500,
      "eventos_fallidos": 10
    }
  ],
  "top_usuarios": [
    {
      "usuario_id": 1,
      "nombre_usuario": "juan.perez",
      "total_eventos": 200
    }
  ]
}
```

---

## ✅ 4. SCHEMAS PYDANTIC RECOMENDADOS

### 4.1 Schemas para Módulo Usuarios (Superadmin)

#### **Schema: `UsuarioSuperadminRead`**
**Propósito:** Vista completa de usuario para Superadmin (incluye información del cliente).

**Campos Obligatorios:**
- `usuario_id` (int)
- `cliente_id` (int)
- `nombre_usuario` (str)
- `es_activo` (bool)
- `fecha_creacion` (datetime)
- `cliente` (ClienteInfo): Información básica del cliente

**Campos Opcionales:**
- `correo` (Optional[str])
- `nombre` (Optional[str])
- `apellido` (Optional[str])
- `dni` (Optional[str])
- `telefono` (Optional[str])
- `proveedor_autenticacion` (str, default='local')
- `referencia_externa_id` (Optional[str])
- `referencia_externa_email` (Optional[str])
- `correo_confirmado` (bool, default=False)
- `intentos_fallidos` (int, default=0)
- `fecha_bloqueo` (Optional[datetime])
- `ultimo_ip` (Optional[str])
- `fecha_ultimo_acceso` (Optional[datetime])
- `fecha_actualizacion` (Optional[datetime])
- `es_eliminado` (bool, default=False)
- `sincronizado_desde` (Optional[str])
- `fecha_ultima_sincronizacion` (Optional[datetime])
- `roles` (List[RolInfo]): Lista de roles activos
- `access_level` (int, default=1)
- `is_super_admin` (bool, default=False)
- `user_type` (str, default='user')

**Justificación:**
- Unifica datos de `usuario` + `cliente` (JOIN) para mostrar contexto completo
- Incluye roles para vista rápida
- Incluye niveles de acceso calculados

**Tablas de Origen:**
- `usuario` (principal)
- `cliente` (JOIN)
- `usuario_rol` + `rol` (JOIN para roles)

---

#### **Schema: `ClienteInfo`**
**Propósito:** Información básica del cliente para incluir en respuestas de usuarios.

**Campos Obligatorios:**
- `cliente_id` (int)
- `razon_social` (str)
- `subdominio` (str)

**Campos Opcionales:**
- `codigo_cliente` (Optional[str])
- `nombre_comercial` (Optional[str])
- `tipo_instalacion` (str, default='cloud')
- `estado_suscripcion` (str, default='activo')

**Justificación:**
- Evita exponer todos los campos de `cliente` en listados
- Proporciona contexto suficiente para identificar el tenant

**Tablas de Origen:**
- `cliente`

---

#### **Schema: `RolInfo`**
**Propósito:** Información básica del rol para incluir en respuestas de usuarios.

**Campos Obligatorios:**
- `rol_id` (int)
- `nombre` (str)

**Campos Opcionales:**
- `codigo_rol` (Optional[str])
- `nivel_acceso` (int, default=1)
- `es_rol_sistema` (bool, default=False)
- `fecha_asignacion` (Optional[datetime]): Desde `usuario_rol`
- `es_activo` (bool, default=True): Desde `usuario_rol`

**Justificación:**
- Información esencial del rol sin sobrecargar la respuesta
- Incluye fecha de asignación para contexto

**Tablas de Origen:**
- `rol` (principal)
- `usuario_rol` (para fecha_asignacion y es_activo de la asignación)

---

#### **Schema: `PaginatedUsuarioSuperadminResponse`**
**Propósito:** Respuesta paginada de listado global de usuarios.

**Campos Obligatorios:**
- `usuarios` (List[UsuarioSuperadminRead])
- `total_usuarios` (int, ge=0)
- `pagina_actual` (int, ge=1)
- `total_paginas` (int, ge=0)

**Justificación:**
- Sigue el patrón existente de `PaginatedUsuarioResponse`
- Compatible con el estilo del backend actual

---

#### **Schema: `UsuarioActividadResponse`**
**Propósito:** Actividad reciente de un usuario.

**Campos Obligatorios:**
- `usuario_id` (int)
- `total_eventos` (int, ge=0)
- `eventos` (List[AuthAuditLogRead])

**Campos Opcionales:**
- `ultimo_acceso` (Optional[datetime]): Desde `usuario.fecha_ultimo_acceso`
- `ultimo_ip` (Optional[str]): Desde `usuario.ultimo_ip`

**Justificación:**
- Combina datos de `usuario` (último acceso) con `auth_audit_log` (eventos recientes)
- Proporciona vista unificada de actividad

**Tablas de Origen:**
- `usuario` (para ultimo_acceso, ultimo_ip)
- `auth_audit_log` (para eventos)

---

#### **Schema: `UsuarioSesionesResponse`**
**Propósito:** Sesiones activas de un usuario.

**Campos Obligatorios:**
- `usuario_id` (int)
- `total_sesiones` (int, ge=0)
- `sesiones_activas` (int, ge=0)
- `sesiones` (List[RefreshTokenInfo])

**Justificación:**
- Agrupa información de sesiones del usuario
- Calcula automáticamente sesiones activas

**Tablas de Origen:**
- `refresh_tokens`

---

#### **Schema: `RefreshTokenInfo`**
**Propósito:** Información de un token refresh (sesión).

**Campos Obligatorios:**
- `token_id` (int)
- `client_type` (str)
- `created_at` (datetime)
- `expires_at` (datetime)
- `is_revoked` (bool)

**Campos Opcionales:**
- `device_name` (Optional[str])
- `device_id` (Optional[str])
- `ip_address` (Optional[str])
- `user_agent` (Optional[str])
- `last_used_at` (Optional[datetime])
- `uso_count` (int, default=0)
- `revoked_at` (Optional[datetime])
- `revoked_reason` (Optional[str])

**Justificación:**
- NO incluye `token_hash` (seguridad)
- Información suficiente para mostrar sesiones al usuario

**Tablas de Origen:**
- `refresh_tokens`

---

### 4.2 Schemas para Módulo Auditoría (Superadmin)

#### **Schema: `AuthAuditLogRead`**
**Propósito:** Vista completa de un log de autenticación.

**Campos Obligatorios:**
- `log_id` (int)
- `cliente_id` (int)
- `evento` (str)
- `exito` (bool)
- `fecha_evento` (datetime)

**Campos Opcionales:**
- `usuario_id` (Optional[int])
- `usuario` (Optional[UsuarioInfo]): Información básica del usuario
- `cliente` (Optional[ClienteInfo]): Información básica del cliente
- `nombre_usuario_intento` (Optional[str])
- `descripcion` (Optional[str])
- `codigo_error` (Optional[str])
- `ip_address` (Optional[str])
- `user_agent` (Optional[str])
- `device_info` (Optional[str])
- `geolocation` (Optional[str])
- `metadata_json` (Optional[Dict]): JSON parseado

**Justificación:**
- Incluye información relacionada (usuario, cliente) para contexto
- Parsea `metadata_json` a Dict para fácil acceso

**Tablas de Origen:**
- `auth_audit_log` (principal)
- `usuario` (JOIN opcional)
- `cliente` (JOIN opcional)

---

#### **Schema: `UsuarioInfo`**
**Propósito:** Información mínima del usuario para incluir en logs.

**Campos Obligatorios:**
- `usuario_id` (int)
- `nombre_usuario` (str)

**Campos Opcionales:**
- `correo` (Optional[str])

**Justificación:**
- Información esencial sin sobrecargar respuestas de auditoría

**Tablas de Origen:**
- `usuario`

---

#### **Schema: `LogSincronizacionRead`**
**Propósito:** Vista completa de un log de sincronización.

**Campos Obligatorios:**
- `log_id` (int)
- `usuario_id` (int)
- `tipo_sincronizacion` (str)
- `direccion` (str)
- `operacion` (str)
- `estado` (str)
- `fecha_sincronizacion` (datetime)

**Campos Opcionales:**
- `cliente_origen_id` (Optional[int])
- `cliente_origen` (Optional[ClienteInfo])
- `cliente_destino_id` (Optional[int])
- `cliente_destino` (Optional[ClienteInfo])
- `usuario` (Optional[UsuarioInfo])
- `mensaje_error` (Optional[str])
- `campos_sincronizados` (Optional[List[str]]): JSON array parseado
- `cambios_detectados` (Optional[Dict]): JSON parseado
- `hash_antes` (Optional[str])
- `hash_despues` (Optional[str])
- `usuario_ejecutor_id` (Optional[int])
- `usuario_ejecutor` (Optional[UsuarioInfo])
- `duracion_ms` (Optional[int])

**Justificación:**
- Incluye información de clientes origen y destino para contexto
- Parsea JSON fields a tipos Python nativos

**Tablas de Origen:**
- `log_sincronizacion_usuario` (principal)
- `cliente` (JOIN para origen y destino)
- `usuario` (JOIN para usuario sincronizado y ejecutor)

---

#### **Schema: `PaginatedAuthAuditLogResponse`**
**Propósito:** Respuesta paginada de logs de autenticación.

**Campos Obligatorios:**
- `logs` (List[AuthAuditLogRead])
- `total_logs` (int, ge=0)
- `pagina_actual` (int, ge=1)
- `total_paginas` (int, ge=0)

**Justificación:**
- Sigue el patrón de paginación existente

---

#### **Schema: `PaginatedLogSincronizacionResponse`**
**Propósito:** Respuesta paginada de logs de sincronización.

**Campos Obligatorios:**
- `logs` (List[LogSincronizacionRead])
- `total_logs` (int, ge=0)
- `pagina_actual` (int, ge=1)
- `total_paginas` (int, ge=0)

**Justificación:**
- Sigue el patrón de paginación existente

---

#### **Schema: `AuditoriaEstadisticasResponse`**
**Propósito:** Estadísticas agregadas de auditoría.

**Campos Obligatorios:**
- `periodo` (PeriodoInfo)
- `autenticacion` (AutenticacionStats)
- `sincronizacion` (SincronizacionStats)

**Campos Opcionales:**
- `top_ips` (Optional[List[IPStats]])
- `top_usuarios` (Optional[List[UsuarioStats]])

**Justificación:**
- Estructura anidada para organizar estadísticas por categoría

**Tablas de Origen:**
- `auth_audit_log` (agregaciones)
- `log_sincronizacion_usuario` (agregaciones)

---

#### **Schema: `PeriodoInfo`**
**Propósito:** Período de tiempo para estadísticas.

**Campos Obligatorios:**
- `fecha_desde` (datetime)
- `fecha_hasta` (datetime)

---

#### **Schema: `AutenticacionStats`**
**Propósito:** Estadísticas de autenticación.

**Campos Obligatorios:**
- `total_eventos` (int, ge=0)
- `login_exitosos` (int, ge=0)
- `login_fallidos` (int, ge=0)
- `eventos_por_tipo` (Dict[str, int])

---

#### **Schema: `SincronizacionStats`**
**Propósito:** Estadísticas de sincronización.

**Campos Obligatorios:**
- `total_sincronizaciones` (int, ge=0)
- `exitosas` (int, ge=0)
- `fallidas` (int, ge=0)
- `por_tipo` (Dict[str, int])

---

#### **Schema: `IPStats`**
**Propósito:** Estadísticas por IP.

**Campos Obligatorios:**
- `ip_address` (str)
- `total_eventos` (int, ge=0)
- `eventos_fallidos` (int, ge=0)

---

#### **Schema: `UsuarioStats`**
**Propósito:** Estadísticas por usuario.

**Campos Obligatorios:**
- `usuario_id` (int)
- `nombre_usuario` (str)
- `total_eventos` (int, ge=0)

---

## ✅ 5. PLAN DE IMPLEMENTACIÓN (BACKLOG DE TRABAJO)

### EPIC 1: Usuarios (Superadmin)

#### **H1: Endpoint Listado Global de Usuarios**
**Objetivo:** Permitir al Superadmin ver todos los usuarios del sistema con paginación y filtros.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/usuarios/` implementado
- ✅ Paginación funcional (page, limit)
- ✅ Filtros: cliente_id, search, es_activo, proveedor_autenticacion
- ✅ Ordenamiento por fecha_creacion, fecha_ultimo_acceso, nombre_usuario
- ✅ Incluye información del cliente (razon_social, subdominio)
- ✅ Incluye roles activos del usuario
- ✅ Respuesta sigue formato `PaginatedUsuarioSuperadminResponse`
- ✅ Solo accesible por Superadmin (nivel 5)

**Consideraciones Multi-Tenant:**
- Superadmin puede ver usuarios de TODOS los clientes
- Validar que `cliente_id` en filtro existe
- Incluir `cliente_id` en todas las queries para contexto

**Dependencias:**
- Schema `UsuarioSuperadminRead` creado
- Schema `ClienteInfo` creado
- Schema `PaginatedUsuarioSuperadminResponse` creado
- Servicio `SuperadminUsuarioService.get_usuarios_globales()` implementado

**Validaciones:**
- Validar que `page >= 1`
- Validar que `limit` entre 1 y 100
- Validar que `cliente_id` existe si se proporciona
- Validar que `proveedor_autenticacion` es válido si se proporciona

---

#### **H2: Endpoint Detalle de Usuario**
**Objetivo:** Obtener información completa de un usuario específico.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/usuarios/{usuario_id}/` implementado
- ✅ Incluye todos los campos del usuario
- ✅ Incluye información completa del cliente
- ✅ Incluye roles activos e históricos
- ✅ Incluye niveles de acceso calculados (access_level, is_super_admin, user_type)
- ✅ Respuesta sigue formato `UsuarioSuperadminRead`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Superadmin puede ver usuarios de cualquier cliente
- No requiere validación de `cliente_id` del usuario actual

**Dependencias:**
- Schema `UsuarioSuperadminRead` creado
- Servicio `SuperadminUsuarioService.obtener_usuario_completo()` implementado
- Método `UsuarioService.get_user_level_info()` ya existe

**Validaciones:**
- Validar que `usuario_id` existe
- Retornar 404 si usuario no existe o está eliminado (a menos que se permita ver eliminados)

---

#### **H3: Integrar Roles en Respuestas**
**Objetivo:** Incluir información de roles en respuestas de usuarios.

**Criterios de Aceptación:**
- ✅ Roles activos incluidos en listado global
- ✅ Roles activos e históricos en detalle de usuario
- ✅ Información completa del rol (nombre, nivel_acceso, codigo_rol)
- ✅ Fecha de asignación y quién asignó (si disponible)
- ✅ Schema `RolInfo` creado y usado

**Consideraciones Multi-Tenant:**
- Incluir roles globales (cliente_id NULL) y roles del cliente
- Validar que roles mostrados pertenecen al contexto correcto

**Dependencias:**
- Schema `RolInfo` creado
- Query optimizada con JOINs a `usuario_rol` y `rol`

**Validaciones:**
- Solo mostrar roles activos en listado (a menos que se especifique lo contrario)
- Validar integridad de relaciones usuario_rol

---

#### **H4: Actividad y Auditoría del Usuario**
**Objetivo:** Mostrar actividad reciente y auditoría de un usuario.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/usuarios/{usuario_id}/actividad/` implementado
- ✅ Combina datos de `usuario.fecha_ultimo_acceso` con eventos de `auth_audit_log`
- ✅ Filtro por tipo de evento opcional
- ✅ Límite configurable de eventos (default 50, max 200)
- ✅ Respuesta sigue formato `UsuarioActividadResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Filtrar eventos por `cliente_id` del usuario (aunque Superadmin puede ver todos)

**Dependencias:**
- Schema `UsuarioActividadResponse` creado
- Schema `AuthAuditLogRead` creado
- Servicio `SuperadminUsuarioService.obtener_actividad_usuario()` implementado

**Validaciones:**
- Validar que `usuario_id` existe
- Validar que `limite` entre 1 y 200
- Validar que `tipo_evento` es válido si se proporciona

---

#### **H5: Estado y Sesiones Activas**
**Objetivo:** Mostrar sesiones activas y estado de seguridad del usuario.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/usuarios/{usuario_id}/sesiones/` implementado
- ✅ Lista tokens refresh no revocados y no expirados
- ✅ Incluye información de dispositivo, IP, user agent
- ✅ Calcula automáticamente sesiones activas vs totales
- ✅ Opción de incluir sesiones revocadas
- ✅ Respuesta sigue formato `UsuarioSesionesResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Filtrar tokens por `cliente_id` del usuario
- NO exponer `token_hash` (seguridad)

**Dependencias:**
- Schema `UsuarioSesionesResponse` creado
- Schema `RefreshTokenInfo` creado
- Servicio `SuperadminUsuarioService.obtener_sesiones_usuario()` implementado

**Validaciones:**
- Validar que `usuario_id` existe
- Calcular sesiones activas: `is_revoked = 0 AND expires_at > NOW()`

---

#### **H6: Endpoint Usuarios por Cliente**
**Objetivo:** Listar usuarios de un cliente específico.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/clientes/{cliente_id}/usuarios/` implementado
- ✅ Paginación y búsqueda funcional
- ✅ Incluye información del cliente en respuesta
- ✅ Respuesta sigue formato `PaginatedUsuarioSuperadminResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Validar que `cliente_id` existe
- Filtrar automáticamente por `cliente_id`

**Dependencias:**
- Schema `PaginatedUsuarioSuperadminResponse` creado
- Servicio `SuperadminUsuarioService.get_usuarios_por_cliente()` implementado

**Validaciones:**
- Validar que `cliente_id` existe
- Validar parámetros de paginación

---

### EPIC 2: Auditoría (Superadmin)

#### **H1: Auditoría de Autenticación - Listado**
**Objetivo:** Listar logs de autenticación con filtros avanzados.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/auditoria/autenticacion/` implementado
- ✅ Paginación funcional
- ✅ Filtros: cliente_id, usuario_id, evento, exito, fecha_desde, fecha_hasta, ip_address
- ✅ Ordenamiento por fecha_evento (default desc)
- ✅ Incluye información de usuario y cliente (JOINs)
- ✅ Respuesta sigue formato `PaginatedAuthAuditLogResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Superadmin puede ver logs de todos los clientes
- Filtrar por `cliente_id` si se proporciona
- Incluir `cliente_id` en todas las queries para contexto

**Dependencias:**
- Schema `AuthAuditLogRead` creado
- Schema `PaginatedAuthAuditLogResponse` creado
- Schema `UsuarioInfo` creado
- Servicio `SuperadminAuditoriaService.get_logs_autenticacion()` implementado

**Validaciones:**
- Validar que `cliente_id` existe si se proporciona
- Validar que `usuario_id` existe si se proporciona
- Validar que `evento` es válido si se proporciona
- Validar que `fecha_desde <= fecha_hasta` si ambas se proporcionan
- Validar formato de `ip_address` si se proporciona

---

#### **H2: Auditoría de Autenticación - Detalle**
**Objetivo:** Obtener detalle completo de un log de autenticación.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/auditoria/autenticacion/{log_id}/` implementado
- ✅ Incluye todos los campos del log
- ✅ Incluye información completa de usuario y cliente
- ✅ Parsea `metadata_json` a Dict
- ✅ Respuesta sigue formato `AuthAuditLogRead`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Superadmin puede ver logs de cualquier cliente
- No requiere validación de `cliente_id` del usuario actual

**Dependencias:**
- Schema `AuthAuditLogRead` creado
- Servicio `SuperadminAuditoriaService.obtener_log_autenticacion()` implementado

**Validaciones:**
- Validar que `log_id` existe
- Retornar 404 si log no existe

---

#### **H3: Auditoría de Sincronización**
**Objetivo:** Listar logs de sincronización entre instalaciones.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/auditoria/sincronizacion/` implementado
- ✅ Paginación funcional
- ✅ Filtros: cliente_origen_id, cliente_destino_id, usuario_id, tipo_sincronizacion, direccion, operacion, estado, fecha_desde, fecha_hasta
- ✅ Incluye información de clientes origen y destino (JOINs)
- ✅ Incluye información del usuario sincronizado
- ✅ Parsea `campos_sincronizados` y `cambios_detectados` a tipos nativos
- ✅ Respuesta sigue formato `PaginatedLogSincronizacionResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Superadmin puede ver sincronizaciones entre cualquier cliente
- Validar que `cliente_origen_id` y `cliente_destino_id` existen si se proporcionan
- Mostrar claramente el flujo origen → destino

**Dependencias:**
- Schema `LogSincronizacionRead` creado
- Schema `PaginatedLogSincronizacionResponse` creado
- Servicio `SuperadminAuditoriaService.get_logs_sincronizacion()` implementado

**Validaciones:**
- Validar que `cliente_origen_id` existe si se proporciona
- Validar que `cliente_destino_id` existe si se proporciona
- Validar que `usuario_id` existe si se proporciona
- Validar que `tipo_sincronizacion`, `direccion`, `operacion`, `estado` son válidos si se proporcionan
- Validar que `fecha_desde <= fecha_hasta` si ambas se proporcionan

---

#### **H4: Estadísticas de Auditoría**
**Objetivo:** Obtener estadísticas agregadas de auditoría.

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/auditoria/estadisticas/` implementado
- ✅ Agregaciones de autenticación (total, exitosos, fallidos, por tipo)
- ✅ Agregaciones de sincronización (total, exitosas, fallidas, por tipo)
- ✅ Top IPs con más eventos
- ✅ Top usuarios con más eventos
- ✅ Filtros por cliente_id y período de tiempo
- ✅ Respuesta sigue formato `AuditoriaEstadisticasResponse`
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Filtrar por `cliente_id` si se proporciona
- Agregaciones deben respetar filtros multi-tenant

**Dependencias:**
- Schema `AuditoriaEstadisticasResponse` creado
- Schema `PeriodoInfo` creado
- Schema `AutenticacionStats` creado
- Schema `SincronizacionStats` creado
- Schema `IPStats` creado
- Schema `UsuarioStats` creado
- Servicio `SuperadminAuditoriaService.obtener_estadisticas()` implementado

**Validaciones:**
- Validar que `cliente_id` existe si se proporciona
- Validar que `fecha_desde <= fecha_hasta` si ambas se proporcionan
- Validar que período no excede límite razonable (ej: 1 año)

---

#### **H5: Auditoría de Actividad General (Opcional)**
**Objetivo:** Vista unificada de actividad (autenticación + sincronización).

**Criterios de Aceptación:**
- ✅ Endpoint `GET /api/v1/superadmin/auditoria/actividad/` implementado
- ✅ Combina eventos de `auth_audit_log` y `log_sincronizacion_usuario`
- ✅ Filtro por tipo de actividad (autenticacion, sincronizacion, todos)
- ✅ Ordenamiento unificado por fecha
- ✅ Respuesta unificada con tipo de evento identificado
- ✅ Solo accesible por Superadmin

**Consideraciones Multi-Tenant:**
- Filtrar por `cliente_id` si se proporciona
- Identificar claramente el origen de cada evento

**Dependencias:**
- Servicio `SuperadminAuditoriaService.get_actividad_unificada()` implementado

**Validaciones:**
- Validar que `tipo_actividad` es válido si se proporciona

---

## ✅ 6. REGLAS DE SEGURIDAD MULTI-TENANT

### 6.1 Qué NO Debe Exponerse al Superadmin

#### **Campos Sensibles que NUNCA deben exponerse:**
1. **Contraseñas:**
   - ❌ `usuario.contrasena` (hash bcrypt) - NUNCA exponer
   - ❌ Cualquier campo relacionado con contraseñas en texto plano

2. **Tokens y Secrets:**
   - ❌ `refresh_tokens.token_hash` - NUNCA exponer
   - ❌ `cliente.api_key_sincronizacion` - NUNCA exponer
   - ❌ `federacion_identidad.client_secret_encrypted` - NUNCA exponer
   - ❌ `cliente_modulo_conexion.usuario_encriptado` - NUNCA exponer
   - ❌ `cliente_modulo_conexion.password_encriptado` - NUNCA exponer
   - ❌ `cliente_modulo_conexion.connection_string_encriptado` - NUNCA exponer

3. **Datos de Configuración Sensibles:**
   - ❌ Certificados X.509 completos (solo metadatos)
   - ❌ Configuraciones de conexión a BD encriptadas

---

### 6.2 Cómo Evitar Revelar Información Sensible

#### **En Schemas Pydantic:**
```python
class UsuarioSuperadminRead(BaseModel):
    # ✅ INCLUIR campos seguros
    usuario_id: int
    nombre_usuario: str
    correo: Optional[str]
    
    # ❌ NUNCA incluir:
    # contrasena: str  # NUNCA
    
    class Config:
        # Excluir campos automáticamente
        fields = {
            'contrasena': {'exclude': True}
        }
```

#### **En Queries SQL:**
```sql
-- ✅ CORRECTO: No seleccionar campos sensibles
SELECT 
    usuario_id, nombre_usuario, correo, nombre, apellido
    -- ❌ NO incluir: contrasena
FROM usuario
WHERE cliente_id = ?

-- ✅ CORRECTO: Para tokens, solo metadatos
SELECT 
    token_id, client_type, device_name, created_at, expires_at
    -- ❌ NO incluir: token_hash
FROM refresh_tokens
WHERE usuario_id = ?
```

#### **En Servicios:**
```python
# ✅ CORRECTO: Filtrar campos sensibles antes de retornar
def obtener_usuario_superadmin(usuario_id: int):
    usuario = execute_query("SELECT * FROM usuario WHERE usuario_id = ?", (usuario_id,))
    # Remover campo sensible
    usuario.pop('contrasena', None)
    return usuario
```

---

### 6.3 Cómo Evitar que un Tenant Vea Datos de Otro

#### **Validaciones en Endpoints:**
```python
# ❌ INCORRECTO: Endpoint sin validación multi-tenant
@router.get("/usuarios/{usuario_id}/")
async def get_usuario(usuario_id: int):
    # PELIGRO: Podría retornar usuario de otro cliente
    usuario = get_usuario_by_id(usuario_id)
    return usuario

# ✅ CORRECTO: Endpoint con validación (para usuarios normales)
@router.get("/usuarios/{usuario_id}/")
async def get_usuario(
    usuario_id: int,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user)
):
    # Validar que el usuario pertenece al mismo cliente
    usuario = get_usuario_by_id_and_cliente(usuario_id, current_user.cliente_id)
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado")
    return usuario

# ✅ CORRECTO: Endpoint Superadmin (puede ver todos)
@require_super_admin()
@router.get("/superadmin/usuarios/{usuario_id}/")
async def get_usuario_superadmin(usuario_id: int):
    # Superadmin puede ver usuarios de cualquier cliente
    usuario = get_usuario_by_id(usuario_id)  # Sin filtro de cliente
    return usuario
```

#### **Validaciones en Servicios:**
```python
# ✅ CORRECTO: Servicio con validación multi-tenant
async def obtener_usuario_por_id(cliente_id: int, usuario_id: int):
    query = """
    SELECT * FROM usuario
    WHERE usuario_id = ? AND cliente_id = ? AND es_eliminado = 0
    """
    return execute_query(query, (usuario_id, cliente_id))

# ✅ CORRECTO: Servicio Superadmin (sin filtro de cliente)
async def obtener_usuario_global(usuario_id: int):
    query = """
    SELECT * FROM usuario
    WHERE usuario_id = ? AND es_eliminado = 0
    """
    return execute_query(query, (usuario_id,))
```

---

### 6.4 Recomendaciones para Endpoints Centralizados

#### **1. Validación de Permisos:**
```python
# ✅ Usar decorador de nivel de acceso
@require_super_admin()
@router.get("/superadmin/usuarios/")
async def list_usuarios_global():
    # Solo Superadmin (nivel 5) puede acceder
    pass
```

#### **2. Filtrado por Cliente (Opcional):**
```python
# ✅ Permitir filtrar por cliente, pero no requerirlo
@require_super_admin()
@router.get("/superadmin/usuarios/")
async def list_usuarios_global(
    cliente_id: Optional[int] = Query(None)
):
    if cliente_id:
        # Validar que cliente existe
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")
        # Filtrar por cliente
        usuarios = await get_usuarios_por_cliente(cliente_id)
    else:
        # Mostrar todos los usuarios
        usuarios = await get_usuarios_globales()
    return usuarios
```

#### **3. Incluir Contexto del Cliente:**
```python
# ✅ Incluir información del cliente en respuestas
def enrich_usuario_with_cliente(usuario: Dict) -> Dict:
    cliente = get_cliente_by_id(usuario['cliente_id'])
    usuario['cliente'] = {
        'cliente_id': cliente['cliente_id'],
        'razon_social': cliente['razon_social'],
        'subdominio': cliente['subdominio']
    }
    return usuario
```

---

### 6.5 Riesgos de Auditoría en Instalaciones Híbridas

#### **Riesgo 1: Sincronización de Datos Sensibles**
**Problema:** En instalaciones híbridas, datos pueden sincronizarse entre servidor central y local.

**Mitigación:**
- ✅ Validar que `log_sincronizacion_usuario` NO incluya campos sensibles en `cambios_detectados`
- ✅ No sincronizar contraseñas (cada instalación maneja su propia autenticación)
- ✅ Validar integridad con `hash_antes` y `hash_despues`

#### **Riesgo 2: Auditoría Incompleta en Instalaciones Locales**
**Problema:** Instalaciones on-premise pueden no enviar logs de auditoría al servidor central.

**Mitigación:**
- ✅ Documentar que `auth_audit_log` puede estar incompleto para clientes on-premise
- ✅ Mostrar claramente en UI si los logs provienen de instalación local o central
- ✅ Considerar campo `origen_log` en `auth_audit_log` (futuro)

#### **Riesgo 3: Conflictos de Sincronización**
**Problema:** Múltiples sincronizaciones simultáneas pueden causar inconsistencias.

**Mitigación:**
- ✅ Revisar `log_sincronizacion_usuario.estado` para detectar fallos
- ✅ Alertar al Superadmin si hay muchos `estado = 'fallido'`
- ✅ Mostrar `mensaje_error` en UI para troubleshooting

#### **Riesgo 4: Exposición de IPs y Geolocalización**
**Problema:** IPs pueden revelar ubicación de instalaciones on-premise.

**Mitigación:**
- ✅ Considerar anonimizar IPs en logs (último octeto)
- ✅ Validar que `geolocation` no se use para clientes on-premise sin consentimiento
- ✅ Documentar políticas de privacidad

---

### 6.6 Mejores Prácticas Adicionales

#### **1. Logging de Accesos Superadmin:**
```python
# ✅ Registrar todos los accesos Superadmin a datos sensibles
logger.info(
    f"Superadmin {current_user.usuario_id} accedió a usuario {usuario_id} "
    f"del cliente {cliente_id} - IP: {request.client.host}"
)
```

#### **2. Rate Limiting:**
```python
# ✅ Aplicar rate limiting a endpoints Superadmin
@router.get("/superadmin/usuarios/")
@rate_limit(max_calls=100, period=60)  # 100 requests por minuto
async def list_usuarios_global():
    pass
```

#### **3. Validación de Entrada:**
```python
# ✅ Validar todos los parámetros de entrada
@router.get("/superadmin/usuarios/")
async def list_usuarios_global(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    cliente_id: Optional[int] = Query(None, gt=0)
):
    # Validaciones adicionales
    if cliente_id:
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")
    # ...
```

#### **4. Caché con Precaución:**
```python
# ⚠️ Cuidado con caché en datos multi-tenant
# NO cachear datos que incluyan información de múltiples clientes
# Cachear solo si se filtra por cliente_id específico
```

---

## 📋 RESUMEN EJECUTIVO

### Estructura de Base de Datos: ✅ PREPARADA
- Tablas necesarias existen y están bien diseñadas
- Índices optimizados para queries multi-tenant
- Campos de auditoría presentes
- Tablas de sincronización completas

### Endpoints Necesarios: 📝 DISEÑADOS
- 6 endpoints para módulo Usuarios
- 5 endpoints para módulo Auditoría
- Todos con paginación, filtros y validaciones

### Schemas Pydantic: 📝 DISEÑADOS
- 15+ schemas propuestos
- Compatibles con estilo actual del backend
- Incluyen validaciones y documentación

### Plan de Implementación: 📝 ESTRUCTURADO
- 2 EPICs principales
- 11 Historias de Usuario detalladas
- Criterios de aceptación claros
- Dependencias identificadas

### Seguridad Multi-Tenant: ✅ DOCUMENTADA
- Reglas claras de qué NO exponer
- Validaciones necesarias
- Riesgos identificados y mitigaciones

---

**Este análisis está 100% basado en la estructura real de tu base de datos y arquitectura actual. Listo para implementación.**

