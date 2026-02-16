# 📊 ORGANIZACIÓN DE TABLAS: BD CENTRAL vs BD DEDICADA

**Propósito:** Documentación clara de qué tablas van en cada base de datos en la arquitectura multi-tenant híbrida.

**Fecha:** Diciembre 2024

---

## 🎯 PRINCIPIOS DE ORGANIZACIÓN

### **BD CENTRAL** (`bd_hybrid_sistema_central`)
- ✅ Tablas **GLOBALES** del sistema (catálogos maestros)
- ✅ Configuración y metadata de **CLIENTES**
- ✅ Información de **MÓDULOS** y **LICENCIAS**
- ✅ Datos **OPERATIVOS** de clientes con `tipo_instalacion = 'shared'`
  - Usuarios, roles, permisos, tokens, logs
  - Se filtran por `cliente_id` en todas las queries

### **BD DEDICADA** (por cliente: `bd_cliente_acme`, `bd_cliente_innova`, etc.)
- ✅ Datos **OPERATIVOS** del tenant (solo si `tipo_instalacion = 'dedicated'` o `'onpremise'`)
- ✅ **USUARIOS** y **ROLES** específicos del cliente
- ✅ **PERMISOS** y **CONFIGURACIÓN** del cliente
- ✅ Datos de **NEGOCIO** (planillas, almacén, ventas, etc.)

### ⚠️ **IMPORTANTE:**
- **Clientes con BD compartida (`shared`)**: Sus datos operativos están en **BD CENTRAL**
- **Clientes con BD dedicada (`dedicated`/`onpremise`)**: Sus datos operativos están en **BD DEDICADA**
- Las tablas operativas (`usuario`, `rol`, etc.) existen en **AMBAS** bases de datos
- El sistema rutea automáticamente según `cliente.tipo_instalacion`

---

## 📋 TABLAS EN BD CENTRAL

### ✅ **1. ADMINISTRACIÓN DE CLIENTES**

> **Nota:** La BD central contiene TODAS estas tablas, incluyendo las operativas, porque debe soportar clientes con `tipo_instalacion = 'shared'`.

#### `cliente`
**Propósito:** Información de cada cliente/tenant del sistema  
**Alcance:** GLOBAL - Un registro por cliente  
**Campos clave:**
- `cliente_id` (PK)
- `codigo_cliente`, `subdominio` (UNIQUE)
- `tipo_instalacion` ('shared', 'dedicated', 'onpremise', 'hybrid')
- `plan_suscripcion`, `estado_suscripcion`
- Branding (logo, colores, tema)

**¿Por qué aquí?**
- Necesario para routing y configuración inicial
- Metadata compartida entre todas las instalaciones

---

#### `cliente_conexion`
**Propósito:** Configuración de conexiones a BD dedicadas  
**Alcance:** GLOBAL - Metadata de conexiones  
**Campos clave:**
- `cliente_id` (FK → cliente)
- `servidor`, `nombre_bd`, `puerto`
- `usuario_encriptado`, `password_encriptado`
- `es_conexion_principal` (solo una por cliente)

**¿Por qué aquí?**
- El sistema necesita saber cómo conectarse a BD dedicadas
- Credenciales encriptadas centralmente

---

#### `cliente_auth_config`
**Propósito:** Políticas de autenticación por cliente  
**Alcance:** GLOBAL - Una configuración por cliente  
**Campos clave:**
- `cliente_id` (FK → cliente, UNIQUE)
- Políticas de contraseña (longitud, complejidad, expiración)
- Control de sesiones, tokens JWT
- Configuración 2FA

**¿Por qué aquí?**
- Configuración administrativa del cliente
- No es dato operativo del día a día

---

#### `federacion_identidad`
**Propósito:** Configuración SSO (Azure AD, Google, Okta, SAML)  
**Alcance:** GLOBAL - Configuración por cliente  
**Campos clave:**
- `cliente_id` (FK → cliente)
- `proveedor` ('azure_ad', 'google', 'okta', 'oidc', 'saml')
- `client_id`, `client_secret_encrypted`
- `authority_url`, `redirect_uri`

**¿Por qué aquí?**
- Configuración administrativa
- No es dato operativo

---

### ✅ **2. CATÁLOGO DE MÓDULOS ERP**

#### `modulo`
**Propósito:** Catálogo maestro de módulos disponibles  
**Alcance:** GLOBAL - Definido por el proveedor SaaS  
**Campos clave:**
- `modulo_id` (PK)
- `codigo` (UNIQUE: 'LOGISTICA', 'ALMACEN', 'PLANILLAS')
- `nombre`, `descripcion`, `icono`, `color`
- `categoria`, `es_core`, `requiere_licencia`
- `precio_mensual`, `modulos_requeridos` (JSON)

**¿Por qué aquí?**
- Catálogo único para todos los clientes
- No cambia por tenant

---

#### `modulo_seccion`
**Propósito:** Secciones dentro de módulos (ej: "Rutas", "Vehículos" en Logística)  
**Alcance:** GLOBAL - Definido por el proveedor  
**Campos clave:**
- `seccion_id` (PK)
- `modulo_id` (FK → modulo)
- `codigo`, `nombre`, `orden`
- `es_seccion_sistema` (TRUE = no editable por cliente)

**¿Por qué aquí?**
- Estructura global de módulos
- No es específico de un cliente

---

#### `modulo_menu`
**Propósito:** Opciones de menú/pantallas de módulos  
**Alcance:** GLOBAL + Personalizable por cliente  
**Campos clave:**
- `menu_id` (PK)
- `modulo_id` (FK → modulo)
- `seccion_id` (FK → modulo_seccion, nullable)
- `cliente_id` (FK → cliente, nullable)
  - NULL = Menú global del sistema
  - Con valor = Menú personalizado del cliente
- `codigo`, `nombre`, `ruta`, `orden`
- `es_menu_sistema` (TRUE = no editable)

**¿Por qué aquí?**
- Menús base definidos globalmente
- Permite personalización por cliente (cliente_id)

---

#### `modulo_rol_plantilla`
**Propósito:** Plantillas de roles predefinidos al activar módulo  
**Alcance:** GLOBAL - Plantillas del sistema  
**Campos clave:**
- `plantilla_id` (PK)
- `modulo_id` (FK → modulo)
- `nombre_rol`, `descripcion`, `nivel_acceso`
- `permisos_json` (JSON con permisos por defecto)

**¿Por qué aquí?**
- Plantillas globales para crear roles automáticamente
- No es específico de un cliente

---

#### `cliente_modulo`
**Propósito:** Módulos activados por cada cliente  
**Alcance:** GLOBAL - Relación cliente ↔ módulo  
**Campos clave:**
- `cliente_modulo_id` (PK)
- `cliente_id` (FK → cliente)
- `modulo_id` (FK → modulo)
- `esta_activo`, `fecha_activacion`, `fecha_vencimiento`
- `modo_prueba`, `configuracion_json`
- Límites: `limite_usuarios`, `limite_registros`

**¿Por qué aquí?**
- Relación administrativa cliente-módulo
- Control de licencias y activaciones

---

### ✅ **3. AUDITORÍA Y SINCRONIZACIÓN**

#### `log_sincronizacion_usuario`
**Propósito:** Log de sincronización de usuarios entre instalaciones  
**Alcance:** GLOBAL - Auditoría de sincronizaciones  
**Campos clave:**
- `log_id` (PK)
- `cliente_origen_id`, `cliente_destino_id`
- `usuario_id` (FK → usuario en BD del cliente)
- `tipo_sincronizacion`, `direccion`, `operacion`
- `estado`, `mensaje_error`

**¿Por qué aquí?**
- Log centralizado de todas las sincronizaciones
- No es dato operativo del cliente

### ✅ **4. TABLAS OPERATIVAS (Para clientes con tipo_instalacion = 'shared')**

Estas tablas también existen en BD dedicada. En BD central se usan cuando el cliente tiene `tipo_instalacion = 'shared'`.

#### `usuario`
**Propósito:** Usuarios del cliente (solo si `tipo_instalacion = 'shared'`)  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`  
**Campos clave:** (mismos que en BD dedicada)

**¿Por qué aquí?**
- Clientes con BD compartida almacenan sus usuarios aquí
- Se filtra por `cliente_id` para aislamiento

---

#### `rol`
**Propósito:** Roles del cliente (solo si `tipo_instalacion = 'shared'`)  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`  
**Campos clave:** (mismos que en BD dedicada)

---

#### `usuario_rol`
**Propósito:** Asignación de roles a usuarios  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`

---

#### `rol_menu_permiso`
**Propósito:** Permisos granulares de roles sobre menús  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`  
**Nota:** `menu_id` referencia `modulo_menu` en la misma BD (BD central)

---

#### `refresh_tokens`
**Propósito:** Refresh tokens JWT  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`

---

#### `auth_audit_log`
**Propósito:** Log de eventos de autenticación  
**Alcance:** POR CLIENTE - Filtrado por `cliente_id`

---

## 📋 TABLAS EN BD DEDICADA (Por Cliente)

> **Nota:** Estas tablas solo se crean si el cliente tiene `tipo_instalacion = 'dedicated'` o `'onpremise'`.

### ✅ **1. AUTENTICACIÓN Y SEGURIDAD**

#### `usuario`
**Propósito:** Usuarios del cliente  
**Alcance:** POR CLIENTE - Datos operativos  
**Campos clave:**
- `usuario_id` (PK)
- `cliente_id` (FK → cliente, siempre el mismo valor en toda la BD)
- `nombre_usuario` (UNIQUE por cliente)
- `contrasena` (hash bcrypt)
- `correo`, `dni`, `telefono`
- `proveedor_autenticacion` ('local', 'azure_ad', 'google')
- `es_activo`, `intentos_fallidos`, `fecha_bloqueo`

**¿Por qué aquí?**
- Datos operativos del día a día
- Cada cliente tiene sus propios usuarios
- Aislamiento completo de datos

---

#### `rol`
**Propósito:** Roles del cliente  
**Alcance:** POR CLIENTE  
**Campos clave:**
- `rol_id` (PK)
- `cliente_id` (FK → cliente)
- `codigo_rol` (NULL para roles personalizados)
- `nombre` (UNIQUE por cliente)
- `es_rol_sistema` (FALSE = creado por cliente)
- `nivel_acceso`

**¿Por qué aquí?**
- Roles específicos del cliente
- Pueden ser creados desde plantillas (`modulo_rol_plantilla`)

---

#### `usuario_rol`
**Propósito:** Asignación de roles a usuarios  
**Alcance:** POR CLIENTE  
**Campos clave:**
- `usuario_rol_id` (PK)
- `usuario_id` (FK → usuario)
- `rol_id` (FK → rol)
- `cliente_id` (desnormalizado)
- `fecha_asignacion`, `fecha_expiracion`
- `es_activo`

**¿Por qué aquí?**
- Relación operativa usuario-rol
- Específica del cliente

---

#### `rol_menu_permiso`
**Propósito:** Permisos granulares de roles sobre menús  
**Alcance:** POR CLIENTE  
**Campos clave:**
- `permiso_id` (PK)
- `cliente_id` (FK → cliente)
- `rol_id` (FK → rol)
- `menu_id` (FK → modulo_menu en BD central)
- `puede_ver`, `puede_crear`, `puede_editar`, `puede_eliminar`
- `permisos_extra` (JSON con permisos específicos del módulo)

**⚠️ NOTA IMPORTANTE:**
- `menu_id` referencia `modulo_menu` en BD CENTRAL
- Requiere cross-database query o queries separadas
- Ver: `app/docs/database/SOLUCION_QUERIES_SEPARADAS.md`

**¿Por qué aquí?**
- Permisos específicos del cliente
- Cada cliente configura sus propios permisos

---

#### `refresh_tokens`
**Propósito:** Refresh tokens JWT para autenticación  
**Alcance:** POR CLIENTE  
**Campos clave:**
- `token_id` (PK)
- `cliente_id` (FK → cliente)
- `usuario_id` (FK → usuario)
- `token_hash` (SHA-256 del token)
- `expires_at`, `is_revoked`
- `device_name`, `ip_address`, `user_agent`

**¿Por qué aquí?**
- Tokens específicos de usuarios del cliente
- Datos operativos de sesiones

---

#### `auth_audit_log`
**Propósito:** Log de eventos de autenticación  
**Alcance:** POR CLIENTE  
**Campos clave:**
- `log_id` (PK)
- `cliente_id` (FK → cliente)
- `usuario_id` (FK → usuario, nullable)
- `evento` ('login_success', 'login_failed', 'logout', etc.)
- `ip_address`, `user_agent`, `device_info`
- `exito`, `codigo_error`

**¿Por qué aquí?**
- Logs específicos del cliente
- Datos operativos de seguridad

---

### ✅ **2. TABLAS DE NEGOCIO (Ejemplos - Módulos ERP)**

Estas tablas se crean **SOLO** en BD dedicada cuando el cliente activa el módulo correspondiente.

#### **Módulo PLANILLAS**
```sql
CREATE TABLE empleado (
    empleado_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    codigo_empleado NVARCHAR(20) NOT NULL,
    nombre NVARCHAR(100) NOT NULL,
    -- ... más campos
);

CREATE TABLE planilla (
    planilla_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    periodo DATE NOT NULL,
    total_ingresos DECIMAL(12,2),
    -- ... más campos
);
```

#### **Módulo ALMACÉN**
```sql
CREATE TABLE producto (
    producto_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    codigo_producto NVARCHAR(50) NOT NULL,
    nombre NVARCHAR(200) NOT NULL,
    stock_actual INT DEFAULT 0,
    -- ... más campos
);

CREATE TABLE movimiento_inventario (
    movimiento_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    producto_id UNIQUEIDENTIFIER NOT NULL,
    tipo_movimiento NVARCHAR(20),
    cantidad INT NOT NULL,
    -- ... más campos
);
```

#### **Módulo LOGÍSTICA**
```sql
CREATE TABLE ruta (
    ruta_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    codigo_ruta NVARCHAR(20) NOT NULL,
    -- ... más campos
);

CREATE TABLE vehiculo (
    vehiculo_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    placa NVARCHAR(10) NOT NULL,
    -- ... más campos
);
```

**¿Por qué aquí?**
- Datos operativos específicos del cliente
- Aislamiento completo entre clientes
- Escalabilidad: cada cliente puede tener millones de registros

---

## 📊 RESUMEN VISUAL

```
┌─────────────────────────────────────────────────────────┐
│         BD CENTRAL (bd_hybrid_sistema_central)          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ADMINISTRACIÓN DE CLIENTES:                            │
│  ✅ cliente                                              │
│  ✅ cliente_conexion                                     │
│  ✅ cliente_auth_config                                  │
│  ✅ federacion_identidad                                 │
│                                                          │
│  CATÁLOGO DE MÓDULOS:                                   │
│  ✅ modulo                                               │
│  ✅ modulo_seccion                                       │
│  ✅ modulo_menu                                          │
│  ✅ modulo_rol_plantilla                                 │
│  ✅ cliente_modulo                                       │
│                                                          │
│  DATOS OPERATIVOS (clientes 'shared'):                  │
│  ✅ usuario (filtrado por cliente_id)                    │
│  ✅ rol (filtrado por cliente_id)                        │
│  ✅ usuario_rol                                          │
│  ✅ rol_menu_permiso                                     │
│  ✅ refresh_tokens                                       │
│  ✅ auth_audit_log                                       │
│                                                          │
│  AUDITORÍA:                                             │
│  ✅ log_sincronizacion_usuario                           │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│    BD DEDICADA (bd_cliente_acme, bd_cliente_innova)    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  AUTENTICACIÓN Y SEGURIDAD:                             │
│  ✅ usuario                                              │
│  ✅ rol                                                  │
│  ✅ usuario_rol                                          │
│  ✅ rol_menu_permiso                                     │
│  ✅ refresh_tokens                                       │
│  ✅ auth_audit_log                                       │
│                                                          │
│  DATOS DE NEGOCIO (según módulos activos):              │
│  ✅ empleado, planilla (Módulo Planillas)               │
│  ✅ producto, movimiento_inventario (Módulo Almacén)    │
│  ✅ ruta, vehiculo (Módulo Logística)                    │
│  ✅ ... (más módulos según necesidad)                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔗 RELACIONES CRUZADAS

### ⚠️ **Casos Especiales**

#### 1. `rol_menu_permiso.menu_id` → `modulo_menu.menu_id`
- **Problema:** FK cruzada entre BD central y BD dedicada
- **Solución:** 
  - Opción A: Queries separadas (recomendado)
  - Opción B: Cross-database query con nombre completo
  - Ver: `app/docs/database/SOLUCION_QUERIES_SEPARADAS.md`

#### 2. `modulo_menu.cliente_id` (nullable)
- **Problema:** Menús pueden ser globales o personalizados
- **Solución:** 
  - `cliente_id = NULL` → Menú global (BD central)
  - `cliente_id = UUID` → Menú personalizado (BD central, pero filtrado por cliente)

---

## 📝 REGLAS DE DECISIÓN

### ¿Una tabla va en BD CENTRAL o BD DEDICADA?

**✅ BD CENTRAL SIEMPRE si:**
- Es un **catálogo maestro** usado por todos los clientes
- Contiene **metadata** o **configuración** de clientes
- Es **administrativa** (no operativa del día a día)
- Necesita ser **compartida** entre instalaciones

**✅ BD CENTRAL Y BD DEDICADA (ambas) si:**
- Contiene **datos operativos** del cliente
- Es específica del **tenant** (usuarios, roles, permisos)
- **En BD central:** Para clientes con `tipo_instalacion = 'shared'`
- **En BD dedicada:** Para clientes con `tipo_instalacion = 'dedicated'` o `'onpremise'`

**✅ SOLO BD DEDICADA si:**
- Son datos de **negocio** (planillas, almacén, ventas)
- Solo existen cuando el cliente activa el módulo correspondiente
- Puede tener **millones de registros** por cliente

---

## 🚀 SCRIPTS DE CREACIÓN

### Script BD Central
**Archivo:** `app/docs/database/estructura_bd.sql`  
**Uso:** Ejecutar una sola vez al crear la BD central

### Script BD Dedicada
**Archivo:** `app/docs/database/MULTITENANT_SCHEMA_DEDICATED_UUID.sql`  
**Uso:** Ejecutar al crear cada BD dedicada de cliente

---

## ✅ CHECKLIST DE VALIDACIÓN

Al crear una nueva tabla, verifica:

- [ ] ¿La tabla es un catálogo maestro global? → **SOLO BD CENTRAL**
- [ ] ¿La tabla contiene datos operativos básicos (usuario, rol, permisos)? → **BD CENTRAL Y BD DEDICADA** (ambas)
- [ ] ¿La tabla contiene datos de negocio (planillas, almacén)? → **SOLO BD DEDICADA**
- [ ] ¿La tabla tiene `cliente_id` como FK? → Verificar según tipo de datos
- [ ] ¿La tabla referencia otras tablas en BD central? → Verificar si requiere cross-database queries
- [ ] ¿La tabla puede tener millones de registros por cliente? → **SOLO BD DEDICADA**

### Regla de Oro:
- **BD CENTRAL:** Siempre tiene todas las tablas (globales + operativas para clientes 'shared')
- **BD DEDICADA:** Solo tiene tablas operativas (no tiene catálogos globales)

---

**Última actualización:** Diciembre 2024  
**Mantenido por:** Arquitectura del Sistema
