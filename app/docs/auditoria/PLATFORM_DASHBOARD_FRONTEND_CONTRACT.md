# Contrato Backend — Dashboard Platform Administration (Frontend)

**Fecha:** 2026-06-03  
**Audiencia:** Equipo Frontend (repositorio separado).  
**Referencias Backend:** `PLATFORM_DASHBOARD_BACKEND_CAPABILITY_AUDIT.md`, `PLATFORM_DASHBOARD_BFF_IMPLEMENTATION_AUDIT.md`.  
**Estado:** Documento de integración — **no requiere leer el repositorio Backend**.

---

## 0. Convenciones globales

### 0.1 Base URL

```text
{API_BASE}/api/v1
```

Ejemplo desarrollo: `https://api.platform.local/api/v1`

### 0.2 Autenticación (obligatoria en todos los endpoints de este documento)

| Header | Valor |
|--------|-------|
| `Authorization` | `Bearer {access_token}` |
| `Origin` | Origin de la consola Platform (p. ej. `https://platform.app.local`) |
| `Content-Type` | `application/json` (solo en POST/PUT) |

**Requisitos del operador:**

- Sesión con privilegios **Super Admin** (`require_super_admin` / `platform_admin`).
- Permisos RBAC según endpoint (ver tabla por endpoint).

**Errores comunes:**

| HTTP | Significado |
|------|-------------|
| `401` | Token ausente o expirado |
| `403` | Sin rol/permiso Platform |
| `422` | Query params inválidos |
| `404` | Recurso no encontrado |
| `500` | Error interno |

### 0.3 Tipos de identificador

Todos los IDs de entidad son **UUID** (string en JSON), formato:

```text
"550e8400-e29b-41d4-a716-446655440000"
```

### 0.4 Fechas

- Request query: ISO 8601, p. ej. `2026-06-03T00:00:00` o con zona `2026-06-03T00:00:00Z`.
- Response: ISO 8601 en strings.

### 0.5 Dos estilos de paginación (importante)

| Estilo | Parámetros | Endpoints que lo usan |
|--------|------------|------------------------|
| **Offset** | `skip`, `limit` | Clientes, Módulos catálogo |
| **Página** | `page`, `limit` | Auditoría, Usuarios superadmin |

---

## 1. Endpoints disponibles hoy para Dashboard

> **Nota:** `GET /api/v1/superadmin/dashboard` **aún no existe**. Los endpoints siguientes son la API actual para componer el dashboard.

---

### 1.1 Clientes — listado paginado

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/clientes/` |
| **Permiso** | `tenant.cliente.leer` |
| **Super Admin** | Requerido |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `skip` | int | `0` | Registros a saltar (≥ 0) |
| `limit` | int | `100` | Máximo por página (1–1000) |
| `solo_activos` | bool | `true` | Si `true`, solo `es_activo=1` |
| `buscar` | string | — | Busca en razón social, nombre comercial, código, subdominio |

**Paginación:** offset (`skip` + `limit`).

**Request ejemplo:**

```http
GET /api/v1/clientes/?skip=0&limit=100&solo_activos=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Origin: https://platform.app.local
```

**Response `200` ejemplo:**

```json
{
  "clientes": [
    {
      "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "codigo_cliente": "ACME001",
      "subdominio": "acme",
      "razon_social": "ACME Corp S.A.",
      "nombre_comercial": "ACME",
      "tipo_instalacion": "shared",
      "modo_autenticacion": "local",
      "plan_suscripcion": "profesional",
      "estado_suscripcion": "activo",
      "fecha_inicio_suscripcion": "2025-01-15",
      "fecha_fin_trial": null,
      "es_activo": true,
      "es_demo": false,
      "fecha_creacion": "2025-01-10T14:30:00",
      "fecha_actualizacion": "2026-05-01T09:00:00",
      "fecha_ultimo_acceso": "2026-06-02T18:45:00",
      "sincronizacion_habilitada": false,
      "ultima_sincronizacion": null
    }
  ],
  "total_clientes": 42,
  "pagina_actual": 1,
  "total_paginas": 1,
  "items_por_pagina": 100
}
```

**Uso dashboard:** `total_clientes` es un **COUNT real** en BD. Para KPIs de distribución (plan, estado), el Frontend debe **agregar client-side** sobre la lista completa o paginar y acumular.

---

### 1.2 Clientes — detalle

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/clientes/{cliente_id}/` |
| **Permiso** | `tenant.cliente.leer` |

**Path:** `cliente_id` (UUID).

**Request ejemplo:**

```http
GET /api/v1/clientes/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**Response:** mismo shape que un ítem de `clientes[]` en §1.1 (`ClienteRead`), incluye branding (`logo_url`, `color_primario`, etc.).

---

### 1.3 Clientes — estadísticas por tenant

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/clientes/{cliente_id}/estadisticas/` |
| **Permiso** | `tenant.cliente.leer` |

**Request ejemplo:**

```http
GET /api/v1/clientes/a1b2c3d4-e5f6-7890-abcd-ef1234567890/estadisticas/
```

**Response `200` ejemplo:**

```json
{
  "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "razon_social": "ACME Corp S.A.",
  "total_usuarios": 25,
  "total_usuarios_inactivos": 3,
  "modulos_activos": 8,
  "modulos_contratados": 10,
  "ultimo_acceso": "2026-06-02T18:45:00",
  "estado_suscripcion": "activo",
  "plan_actual": "profesional",
  "fecha_creacion": "2025-01-10T14:30:00",
  "dias_activo": 509,
  "conexiones_bd": 1,
  "tipo_instalacion": "shared"
}
```

**Limitación:** una llamada **por cliente**. No usar en loop masivo para dashboard global (ver §6 Dashboard futuro).

---

### 1.4 Auditoría — estadísticas agregadas

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/superadmin/auditoria/estadisticas/` |
| **Permiso** | Super Admin (sin permiso RBAC adicional explícito en router) |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `cliente_id` | UUID | — | Si se omite: agregado **global** |
| `fecha_desde` | datetime | implícito amplio | Inicio ventana |
| `fecha_hasta` | datetime | `now` | Fin ventana |

**Request ejemplo (últimas 24 h, global):**

```http
GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=2026-06-02T00:00:00&fecha_hasta=2026-06-03T00:00:00
```

**Response `200` ejemplo:**

```json
{
  "periodo": {
    "fecha_desde": "2026-06-02T00:00:00",
    "fecha_hasta": "2026-06-03T00:00:00"
  },
  "autenticacion": {
    "total_eventos": 1250,
    "login_exitosos": 1180,
    "login_fallidos": 70,
    "eventos_por_tipo": {
      "login_success": 1180,
      "login_failed": 70
    }
  },
  "sincronizacion": {
    "total_sincronizaciones": 45,
    "exitosas": 42,
    "fallidas": 3,
    "por_tipo": {
      "manual": 10,
      "scheduled": 35
    }
  },
  "top_ips": [
    {
      "ip_address": "203.0.113.50",
      "total_eventos": 320,
      "eventos_fallidos": 15
    }
  ],
  "top_usuarios": [
    {
      "usuario_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "nombre_usuario": "admin.acme",
      "total_eventos": 89
    }
  ]
}
```

**Uso dashboard:** widget principal de **seguridad / auth** y **sync** sin composición adicional.

---

### 1.5 Auditoría — logs de autenticación (actividad reciente)

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/superadmin/auditoria/autenticacion/` |
| **Permiso** | Super Admin |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `cliente_id` | UUID | — | Filtro tenant |
| `usuario_id` | UUID | — | Filtro usuario |
| `evento` | string | — | p. ej. `login_success`, `login_failed` |
| `exito` | bool | — | `true` / `false` |
| `fecha_desde` | datetime | — | |
| `fecha_hasta` | datetime | — | |
| `ip_address` | string | — | |
| `page` | int | `1` | Página (≥ 1) |
| `limit` | int | `50` | 1–200 |
| `ordenar_por` | string | `fecha_evento` | |
| `orden` | `asc` \| `desc` | `desc` | |

**Paginación:** `page` + `limit`.

**Request ejemplo:**

```http
GET /api/v1/superadmin/auditoria/autenticacion/?page=1&limit=20&orden=desc&evento=login_failed
```

**Response `200` ejemplo:**

```json
{
  "logs": [
    {
      "log_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "cliente": {
        "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "razon_social": "ACME Corp S.A.",
        "subdominio": "acme",
        "codigo_cliente": "ACME001"
      },
      "usuario_id": null,
      "evento": "login_failed",
      "nombre_usuario_intento": "hacker@test.com",
      "exito": false,
      "codigo_error": "INVALID_CREDENTIALS",
      "ip_address": "198.51.100.10",
      "fecha_evento": "2026-06-03T08:12:33"
    }
  ],
  "total_logs": 70,
  "pagina_actual": 1,
  "total_paginas": 4
}
```

---

### 1.6 Auditoría — logs de sincronización

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/superadmin/auditoria/sincronizacion/` |
| **Permiso** | Super Admin |

**Filtros:** `cliente_origen_id`, `cliente_destino_id`, `usuario_id`, `tipo_sincronizacion`, `direccion`, `operacion`, `estado` (`exitoso`/`fallido`/…), `fecha_desde`, `fecha_hasta`, `page`, `limit`, `ordenar_por`, `orden`.

**Request ejemplo:**

```http
GET /api/v1/superadmin/auditoria/sincronizacion/?estado=fallido&page=1&limit=10&orden=desc
```

**Response:** `PaginatedLogSincronizacionResponse` — shape análogo a §1.5 con `logs[]` (`estado`, `mensaje_error`, `fecha_sincronizacion`, clientes origen/destino).

---

### 1.7 Usuarios — listado global

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/superadmin/usuarios/` |
| **Permiso** | Super Admin |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `cliente_id` | UUID | — | Filtrar por tenant |
| `page` | int | `1` | |
| `limit` | int | `20` | 1–100 |
| `search` | string | — | Nombre, apellido, correo, username |
| `es_activo` | bool | — | |
| `proveedor_autenticacion` | string | — | |
| `ordenar_por` | string | `fecha_creacion` | `fecha_creacion`, `fecha_ultimo_acceso`, `nombre_usuario` |
| `orden` | string | `desc` | |

**Request ejemplo (operadores SYSTEM / Platform):**

```http
GET /api/v1/superadmin/usuarios/?cliente_id={SYSTEM_CLIENTE_UUID}&es_activo=true&limit=50
```

**Response `200` ejemplo:**

```json
{
  "usuarios": [
    {
      "usuario_id": "d4e5f6a7-b8c9-0123-def0-234567890123",
      "cliente_id": "00000000-0000-0000-0000-000000000001",
      "cliente": {
        "cliente_id": "00000000-0000-0000-0000-000000000001",
        "razon_social": "Sistema Platform",
        "subdominio": "platform",
        "codigo_cliente": "SYSTEM"
      },
      "nombre_usuario": "admin.platform",
      "correo": "ops@platform.com",
      "es_activo": true,
      "intentos_fallidos": 0,
      "fecha_bloqueo": null,
      "fecha_creacion": "2024-06-01T10:00:00",
      "fecha_ultimo_acceso": "2026-06-03T07:30:00",
      "roles": [
        {
          "rol_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
          "nombre": "Administrador Platform",
          "codigo_rol": "ADMIN_PLATFORM",
          "nivel_acceso": 5,
          "es_rol_sistema": true
        }
      ],
      "is_super_admin": true,
      "user_type": "platform_admin"
    }
  ],
  "total_usuarios": 8,
  "pagina_actual": 1,
  "total_paginas": 1
}
```

**Nota:** el UUID del cliente SYSTEM debe obtenerse del entorno o listando clientes con `codigo_cliente=SYSTEM`.

---

### 1.8 Usuarios — listado por cliente

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/superadmin/usuarios/clientes/{cliente_id}/usuarios/` |
| **Query** | `page`, `limit`, `search`, `es_activo` |

Misma forma de respuesta que §1.7.

---

### 1.9 Módulos — catálogo global

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/modulos-v2/` |
| **Permiso** | `modulos.menu.leer` |

**Query parameters:**

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `skip` | int | `0` | |
| `limit` | int | `100` | 1–1000 |
| `solo_activos` | bool | `false` | |
| `categoria` | string | — | p. ej. `operaciones`, `finanzas` |

**Paginación:** offset + objeto `pagination` en respuesta.

**Request ejemplo:**

```http
GET /api/v1/modulos-v2/?solo_activos=true&limit=500
```

**Response `200` ejemplo:**

```json
{
  "success": true,
  "message": "Catálogo de módulos recuperado exitosamente.",
  "data": [
    {
      "modulo_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
      "codigo": "INV",
      "nombre": "Inventarios",
      "categoria": "operaciones",
      "es_core": false,
      "requiere_licencia": true,
      "precio_mensual": 99.0,
      "es_activo": true,
      "orden": 10
    }
  ],
  "pagination": {
    "total": 24,
    "skip": 0,
    "limit": 500,
    "total_pages": 1,
    "current_page": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

### 1.10 Licencias — módulos activos por cliente

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/cliente-modulo/cliente/{cliente_id}/` |
| **Permiso** | `modulos.menu.leer` |

**Request ejemplo:**

```http
GET /api/v1/cliente-modulo/cliente/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**Response `200` ejemplo:**

```json
{
  "success": true,
  "message": "Módulos activos para cliente ... obtenidos exitosamente.",
  "data": [
    {
      "cliente_modulo_id": "a7b8c9d0-e1f2-3456-0123-567890123456",
      "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "modulo_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
      "esta_activo": true,
      "fecha_activacion": "2025-03-01T10:00:00",
      "fecha_vencimiento": "2026-12-31T23:59:59",
      "modo_prueba": false,
      "fecha_fin_prueba": null,
      "limite_usuarios": 50,
      "modulo_codigo": "INV",
      "modulo_nombre": "Inventarios"
    }
  ]
}
```

**Limitación:** **por tenant** — no hay endpoint global de licencias hoy.

---

### 1.11 Conexiones — por cliente

| Campo | Valor |
|-------|-------|
| **Ruta listado** | `GET /api/v1/conexiones/clientes/{cliente_id}/` |
| **Ruta principal** | `GET /api/v1/conexiones/clientes/{cliente_id}/principal/` |
| **Permiso** | `tenant.conexion.leer` |

**Response listado (`ConexionRead[]`) ejemplo:**

```json
[
  {
    "conexion_id": "b8c9d0e1-f2a3-4567-1234-678901234567",
    "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "servidor": "sql-prod-01.database.windows.net",
    "puerto": 1433,
    "nombre_bd": "erp_acme",
    "tipo_bd": "sqlserver",
    "es_conexion_principal": true,
    "es_activo": true,
    "ultima_conexion_exitosa": "2026-06-03T06:00:00",
    "ultimo_error": null,
    "fecha_ultimo_error": null
  }
]
```

**Seguridad UI:** la respuesta incluye `usuario_encriptado` y `password_encriptado` — **no mostrar** en dashboard; usar solo campos de estado/servidor.

**Limitación:** no existe listado **global** cross-tenant de conexiones.

---

### 1.12 Métricas runtime API (opcional — no recomendado para dashboard negocio)

| Campo | Valor |
|-------|-------|
| **Ruta** | `GET /api/v1/metrics/summary` |
| **Ruta** | `GET /api/v1/metrics/slow-queries?threshold_ms=100&limit=10` |
| **Permiso** | Super Admin |

Datos **in-memory del proceso** API, no BD central. Útil solo para panel técnico interno, no para KPIs SaaS.

---

## 2. KPIs que pueden construirse hoy

Leyenda:

| Símbolo | Significado |
|---------|-------------|
| ✅ | Directo desde un endpoint (sin agregación FE) |
| 🔄 | Requiere agregación Frontend sobre listado(s) |
| ❌ | No disponible sin BFF o sin N+1 costoso |

### 2.1 Clientes

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Total clientes activos | ✅ | `GET /clientes/?solo_activos=true&limit=1` → `total_clientes` |
| Total clientes (incl. inactivos) | ✅ | `GET /clientes/?solo_activos=false&limit=1` → `total_clientes` |
| Clientes suspendidos | 🔄 | Listar (`solo_activos=false` o `true`) y contar `estado_suscripcion === 'suspendido'` |
| Clientes cancelados / inactivos | 🔄 | Contar `es_activo === false` o `estado_suscripcion === 'cancelado'` |
| Distribución por plan | 🔄 | Agrupar `plan_suscripcion` del listado completo |
| Distribución por tipo instalación | 🔄 | Agrupar `tipo_instalacion` |
| Nuevos clientes (30 días) | 🔄 | Filtrar `fecha_creacion >= hoy - 30d` en listado |
| Trials por vencer | 🔄 | `plan_suscripcion === 'trial'` y `fecha_fin_trial` en ventana |
| Clientes demo | 🔄 | Contar `es_demo === true` |
| Estado incoherente (activo suscripción pero inactivo registro) | 🔄 | `estado_suscripcion === 'activo' && es_activo === false` |
| Usuarios / módulos / conexiones por tenant | ✅ | `GET /clientes/{id}/estadisticas/` (por tenant) |

**Valores válidos (validación Backend):**

- `plan_suscripcion`: `trial`, `basico`, `profesional`, `enterprise`
- `estado_suscripcion`: `trial`, `activo`, `suspendido`, `cancelado`, `moroso`
- `tipo_instalacion`: `shared`, `dedicated`, `onpremise`, `hybrid`

---

### 2.2 Módulos

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Total módulos en catálogo | ✅ | `GET /modulos-v2/?limit=1` → `pagination.total` |
| Módulos activos en catálogo | ✅ | `GET /modulos-v2/?solo_activos=true&limit=1` → `pagination.total` |
| Módulos por categoría | 🔄 | Agrupar `data[].categoria` del listado |
| Módulos activos por tenant | ✅ | `GET /cliente-modulo/cliente/{id}/` → `data.length` |
| Top módulos más activados (global) | ❌ | Requiere BFF o iterar todos los tenants |
| Licencias vencidas (global) | ❌ | Requiere BFF o iterar `cliente-modulo` por tenant |

---

### 2.3 Usuarios Platform

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Total usuarios globales | ✅ | `GET /superadmin/usuarios/?limit=1` → `total_usuarios` |
| Usuarios por tenant | ✅ | `GET /superadmin/usuarios/clientes/{id}/usuarios/?limit=1` → `total_usuarios` |
| Operadores Platform activos | 🔄 | Filtrar `cliente_id=SYSTEM` + roles `ADMIN_PLATFORM` / `is_super_admin` |
| Usuarios bloqueados | 🔄 | Filtrar `fecha_bloqueo != null` en listado |
| Sesiones activas (global) | ❌ | Solo por usuario: `GET /superadmin/usuarios/{id}/sesiones/` |

---

### 2.4 Auditoría

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Eventos auth total (ventana) | ✅ | `GET /superadmin/auditoria/estadisticas/` |
| Logins exitosos / fallidos | ✅ | `autenticacion.login_exitosos`, `login_fallidos` |
| Eventos por tipo | ✅ | `autenticacion.eventos_por_tipo` |
| Sync total / exitosas / fallidas | ✅ | `sincronizacion.*` |
| Top IPs | ✅ | `top_ips[]` |
| Top usuarios por eventos | ✅ | `top_usuarios[]` |
| Top tenants por actividad | ❌ | No expuesto — BFF `top_clientes` |
| Serie temporal (por hora/día) | ❌ | No hay endpoint de series |

---

### 2.5 Conexiones

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Conexiones activas por tenant | ✅ | `GET /conexiones/clientes/{id}/` → filtrar `es_activo` |
| Conexión principal | ✅ | `GET /conexiones/clientes/{id}/principal/` |
| Último error / fecha | ✅ | Campos en `ConexionRead` |
| Conexiones críticas (global) | ❌ | Requiere BFF o iterar todos los clientes |
| Dedicated sin principal activa | ❌ | Requiere BFF |
| Test conectividad confiable | ❌ | `POST /conexiones/test` es simulado — no usar en alertas |

---

### 2.6 Licencias

| KPI | Fuente | Cómo obtenerlo |
|-----|--------|----------------|
| Módulos activos tenant | ✅ | `cliente-modulo/cliente/{id}/` |
| Vencimiento por tenant | ✅ | `data[].fecha_vencimiento` |
| Modo prueba | ✅ | `data[].modo_prueba`, `fecha_fin_prueba` |
| Límites (usuarios/registros) | ✅ | `limite_usuarios`, etc. |
| Activaciones activas global | ❌ | BFF |
| Licencias por vencer (global) | ❌ | BFF |

---

## 3. Actividad reciente

### 3.1 Widget “Últimos eventos de autenticación”

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/superadmin/auditoria/autenticacion/` |
| **Parámetros recomendados** | `page=1`, `limit=20`, `orden=desc`, `ordenar_por=fecha_evento` |
| **Filtro fallos** | `evento=login_failed` o `exito=false` |

**Datos por fila:** tenant (`cliente`), usuario intentado, evento, IP, fecha, código error.

**Drill-down:** `GET /api/v1/superadmin/auditoria/autenticacion/{log_id}/`

---

### 3.2 Widget “Últimas sincronizaciones”

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/superadmin/auditoria/sincronizacion/` |
| **Parámetros** | `page=1`, `limit=10`, `orden=desc` |
| **Solo fallos** | `estado=fallido` |

**Datos por fila:** origen/destino, usuario, operación, estado, `mensaje_error`, `duracion_ms`, fecha.

---

### 3.3 Widget “Clientes recientes”

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/clientes/?solo_activos=false&limit=10` |
| **Orden** | Backend ordena por `razon_social` — **no por fecha**. Para “últimos creados”, el Frontend debe paginar y ordenar client-side por `fecha_creacion` o esperar al BFF. |

**Limitación:** no hay `ordenar_por=fecha_creacion` en listado clientes hoy.

---

### 3.4 Widget “Usuarios con acceso reciente”

| Campo | Valor |
|-------|-------|
| **Endpoint** | `GET /api/v1/superadmin/usuarios/?ordenar_por=fecha_ultimo_acceso&orden=desc&limit=10` |

**Datos:** username, tenant, `fecha_ultimo_acceso`, roles.

---

### 3.5 Limitaciones actuales de actividad reciente

| Limitación | Impacto Frontend |
|------------|------------------|
| Sin feed unificado | Componer 2–4 llamadas paralelas |
| Sin WebSocket / push | Polling (recomendado 60–120 s) |
| Logs dedicated pueden estar en BD tenant | Eventos de tenants dedicated podrían no aparecer en vista global |
| Listado clientes sin sort por fecha | “Recientes” requiere sort local o BFF |
| Paginación heterogénea | Implementar adapters `skip/limit` vs `page/limit` |

---

## 4. Alertas

### 4.1 Alertas calculables hoy (Frontend)

El Frontend puede derivar alertas con reglas sobre datos de los endpoints actuales.

| Código sugerido UI | Severidad | Regla (datos actuales) |
|--------------------|-----------|-------------------------|
| `AUTH_LOGIN_FAILURES_HIGH` | warning | `auditoria/estadisticas` → `login_fallidos >= umbral` (p. ej. 50 en 24 h) |
| `AUTH_SYNC_FAILURES` | warning | `sincronizacion.fallidas > 0` en periodo |
| `CLIENT_TRIAL_EXPIRED` | warning | En listado clientes: `plan_suscripcion=trial` y `fecha_fin_trial < hoy` |
| `CLIENT_TRIAL_EXPIRING` | info | Trial con `fecha_fin_trial` en próximos 7 días |
| `CLIENT_STATE_INCOHERENT` | critical | `estado_suscripcion=activo` y `es_activo=false` |
| `CLIENT_SUSPENDED` | info | `estado_suscripcion=suspendido` |
| `CONN_ERROR_ON_TENANT` | critical | Tras cargar conexiones de un tenant: `ultimo_error != null` y `fecha_ultimo_error` reciente |
| `LICENSE_EXPIRING_TENANT` | info | En `cliente-modulo`: `fecha_vencimiento` en 30 días |
| `LICENSE_EXPIRED_TENANT` | critical | `fecha_vencimiento < hoy` y `esta_activo=true` |
| `USER_BLOCKED` | warning | En listado usuarios: `fecha_bloqueo != null` |
| `IP_SUSPICIOUS` | warning | En `top_ips`: ratio `eventos_fallidos/total_eventos > 0.5` |

**Implementación típica:** servicio FE `DashboardAlertService` que consume respuestas cacheadas de los GET principales.

---

### 4.2 Alertas que requieren Backend nuevo (BFF)

Estas alertas están diseñadas en `PLATFORM_DASHBOARD_BFF_IMPLEMENTATION_AUDIT.md` y llegarán en el array `alertas[]` del futuro endpoint.

| Código BFF | Motivo por el que no está hoy |
|------------|-------------------------------|
| `CONN_ERROR_RECENT` (global) | Sin vista cross-tenant de conexiones |
| `CONN_NO_SUCCESS_RECENT` | idem |
| `CONN_DEDICATED_NO_PRINCIPAL` | Requiere JOIN global cliente + conexión |
| `LICENSE_EXPIRED_ACTIVE` (global) | Sin agregación `cliente_modulo` global |
| `LICENSE_EXPIRING` (conteo global) | idem |
| `MODULE_CATALOG_INACTIVE_WITH_ACTIVE_LICENSES` | Requiere JOIN `modulo` + `cliente_modulo` |
| `SSO_MODE_WITHOUT_FEDERATION` | Requiere query `federacion_identidad` |
| `SYNC_ENABLED_STALE` | Query sobre `cliente.sincronizacion_habilitada` |
| `TENANT_NO_ACTIVE_USERS` | Agregación global `usuario` |
| `PLATFORM_OPERATOR_NONE_ACTIVE` | Conteo dedicado operadores |

**Recomendación:** no implementar reglas globales costosas en Frontend (iterar N tenants × M endpoints). Esperar al BFF.

---

## 5. Dashboard MVP — widgets implementables hoy (sin cambios Backend)

Lista cerrada de widgets que el Frontend puede entregar **solo con los endpoints de §1**.

| # | Widget | Endpoint(s) | Notas |
|---|--------|-------------|-------|
| W1 | **Tarjeta total clientes activos** | `GET /clientes/?solo_activos=true&limit=1` | `total_clientes` |
| W2 | **Tarjeta total clientes (todos)** | `GET /clientes/?solo_activos=false&limit=1` | |
| W3 | **Tarjeta logins fallidos (24 h)** | `GET /superadmin/auditoria/estadisticas/?fecha_desde=…` | Selector ventana en UI |
| W4 | **Tarjeta logins exitosos (24 h)** | idem | |
| W5 | **Tarjeta sync fallidas (24 h)** | idem → `sincronizacion.fallidas` | |
| W6 | **Gráfico barras eventos por tipo** | idem → `eventos_por_tipo` | |
| W7 | **Tabla top IPs** | idem → `top_ips` | |
| W8 | **Tabla top usuarios activos** | idem → `top_usuarios` | |
| W9 | **Feed últimos logins / fallos** | `GET /superadmin/auditoria/autenticacion/?limit=20` | |
| W10 | **Feed sync recientes / fallidas** | `GET /superadmin/auditoria/sincronizacion/?limit=10` | |
| W11 | **Tarjeta módulos en catálogo** | `GET /modulos-v2/?limit=1` | `pagination.total` |
| W12 | **Tarjeta usuarios globales** | `GET /superadmin/usuarios/?limit=1` | `total_usuarios` |
| W13 | **Lista clientes recientes** | `GET /clientes/` + sort FE por `fecha_creacion` | Paginar si >100 |
| W14 | **Donut planes / estados** | `GET /clientes/` (listado completo) | Agregación FE; excluir SYSTEM |
| W15 | **Alertas derivadas (banner)** | Composición W3–W14 | Ver §4.1 |
| W16 | **Detalle tenant (drill-down)** | `/clientes/{id}/`, `/estadisticas/`, `/conexiones/`, `/cliente-modulo/` | Pantalla detalle, no home |

**Composición mínima recomendada al cargar home (paralelo):**

```text
Promise.all([
  GET /clientes/?solo_activos=true&limit=1,
  GET /clientes/?solo_activos=false&limit=1,
  GET /superadmin/auditoria/estadisticas/?fecha_desde={hace24h},
  GET /superadmin/auditoria/autenticacion/?limit=15&orden=desc,
  GET /modulos-v2/?solo_activos=true&limit=1,
  GET /superadmin/usuarios/?limit=1
])
```

Opcional para donut distribución (si pocos tenants):

```text
GET /clientes/?solo_activos=false&limit=1000
```

---

## 6. Dashboard futuro — widgets que deben esperar al BFF

Endpoint planificado (aún **no implementado**):

```http
GET /api/v1/superadmin/dashboard/
```

Contrato detallado en `PLATFORM_DASHBOARD_BFF_IMPLEMENTATION_AUDIT.md`.

| # | Widget | Campo BFF | Por qué no hoy |
|---|--------|-----------|----------------|
| F1 | **Resumen clientes unificado** | `clientes.*` | Sin GROUP BY server-side |
| F2 | **Trials por vencer / vencidos (conteo)** | `clientes.trials_*` | Agregación global |
| F3 | **Estado incoherente (conteo)** | `clientes.estado_incoherente` | Query dedicada |
| F4 | **Top tenants por actividad** | `auditoria.top_clientes` | No existe en stats actual |
| F5 | **Resumen licencias global** | `licencias.*` | Sin endpoint global |
| F6 | **Top módulos activados** | `licencias.top_modulos` | idem |
| F7 | **Panel salud conexiones global** | `conexiones.*` | Solo per-tenant |
| F8 | **Lista conexiones críticas** | `conexiones.items_criticos` | idem |
| F9 | **Operadores Platform** | `usuarios_platform.*` | Sin conteo dedicado |
| F10 | **Panel alertas unificado** | `alertas[]` | Reglas server-side |
| F11 | **Meta / limitaciones** | `meta.limitaciones` | Documentación runtime |
| F12 | **Carga parcial por sección** | `?secciones=clientes,auditoria` | Optimización red |

**Migración Frontend:** cuando el BFF exista, reemplazar el bundle de §5 por **una sola llamada**; mantener mismos widgets visuales mapeando campos BFF.

---

## 7. Ejemplos JSON por widget

### W1 — Tarjeta “Clientes activos”

**Request:**

```http
GET /api/v1/clientes/?skip=0&limit=1&solo_activos=true
```

**UI mapping:**

```json
{
  "widget": "kpi_clientes_activos",
  "value": 38,
  "source": "total_clientes"
}
```

*(Valor `38` tomado de `response.total_clientes`.)*

---

### W3 — Tarjeta “Logins fallidos (24 h)”

**Request:**

```http
GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=2026-06-02T12:00:00Z&fecha_hasta=2026-06-03T12:00:00Z
```

**UI mapping:**

```json
{
  "widget": "kpi_login_fallidos",
  "value": 70,
  "periodo": {
    "desde": "2026-06-02T12:00:00Z",
    "hasta": "2026-06-03T12:00:00Z"
  },
  "source": "autenticacion.login_fallidos"
}
```

---

### W6 — Gráfico “Eventos por tipo”

**UI mapping (desde misma respuesta §W3):**

```json
{
  "widget": "chart_eventos_por_tipo",
  "chartType": "bar",
  "labels": ["login_success", "login_failed"],
  "series": [1180, 70],
  "source": "autenticacion.eventos_por_tipo"
}
```

---

### W7 — Tabla “Top IPs”

```json
{
  "widget": "table_top_ips",
  "columns": ["ip_address", "total_eventos", "eventos_fallidos"],
  "rows": [
    { "ip_address": "203.0.113.50", "total_eventos": 320, "eventos_fallidos": 15 },
    { "ip_address": "198.51.100.10", "total_eventos": 180, "eventos_fallidos": 45 }
  ]
}
```

---

### W9 — Feed “Actividad auth reciente”

**Request:**

```http
GET /api/v1/superadmin/auditoria/autenticacion/?page=1&limit=5&orden=desc
```

**UI mapping:**

```json
{
  "widget": "feed_auth_reciente",
  "items": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "tipo": "login_failed",
      "tenant": "ACME Corp S.A.",
      "usuario": "hacker@test.com",
      "ip": "198.51.100.10",
      "fecha": "2026-06-03T08:12:33",
      "exito": false
    }
  ]
}
```

---

### W14 — Donut “Clientes por plan” (agregación FE)

**Request:**

```http
GET /api/v1/clientes/?solo_activos=false&limit=1000&skip=0
```

**UI mapping (calculado en FE):**

```json
{
  "widget": "donut_planes",
  "segments": [
    { "label": "profesional", "value": 20 },
    { "label": "trial", "value": 8 },
    { "label": "enterprise", "value": 5 },
    { "label": "basico", "value": 9 }
  ],
  "note": "Excluir codigo_cliente=SYSTEM en agregación"
}
```

---

### W15 — Banner alertas (FE)

```json
{
  "widget": "alert_banner",
  "alertas": [
    {
      "codigo": "AUTH_LOGIN_FAILURES_HIGH",
      "severidad": "warning",
      "mensaje": "70 logins fallidos en las últimas 24 horas",
      "accion_url": "/super-admin/auditoria?evento=login_failed"
    },
    {
      "codigo": "CLIENT_STATE_INCOHERENT",
      "severidad": "critical",
      "mensaje": "2 clientes con suscripción activa pero registro inactivo",
      "cliente_ids": ["uuid-1", "uuid-2"]
    }
  ]
}
```

---

### F1 — Widget futuro “Resumen clientes” (BFF)

**Request (futuro):**

```http
GET /api/v1/superadmin/dashboard/
```

**UI mapping esperado:**

```json
{
  "widget": "kpi_clientes_resumen",
  "source": "clientes",
  "data": {
    "total": 120,
    "activos": 98,
    "inactivos": 22,
    "por_estado_suscripcion": {
      "activo": 90,
      "suspendido": 8,
      "cancelado": 22
    },
    "por_plan": {
      "trial": 15,
      "basico": 40,
      "profesional": 50,
      "enterprise": 15
    },
    "nuevos_en_periodo": 7,
    "trials_por_vencer": 3,
    "estado_incoherente": 2
  }
}
```

---

### F10 — Widget futuro “Alertas plataforma” (BFF)

```json
{
  "widget": "alert_panel",
  "source": "alertas",
  "items": [
    {
      "codigo": "CONN_ERROR_RECENT",
      "severidad": "critical",
      "mensaje": "2 conexiones con error en las últimas 24 horas",
      "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "entidad_tipo": "conexion",
      "metadata": { "total": 2 }
    },
    {
      "codigo": "LICENSE_EXPIRED_ACTIVE",
      "severidad": "critical",
      "mensaje": "4 licencias vencidas siguen marcadas como activas",
      "metadata": { "total": 4 }
    }
  ]
}
```

---

## 8. Estrategia de integración Frontend

### 8.1 Capa API sugerida

```typescript
// Ejemplo conceptual — adaptar al stack FE
platformDashboardApi.getHomeKpis()      // composición §5 hoy
platformDashboardApi.getAuditoriaStats(periodo)
platformDashboardApi.getRecentAuthLogs(limit)
// Futuro:
platformDashboardApi.getDashboard(params?)  // BFF único
```

### 8.2 Polling

| Dato | Intervalo sugerido |
|------|-------------------|
| KPIs auth | 60 s |
| Feed actividad | 60 s |
| Listado clientes | 120 s |
| BFF (futuro) | 90 s (alineado TTL cache Backend) |

### 8.3 Manejo de errores parciales

Si una llamada del bundle falla, mostrar widget en estado **degraded** con mensaje; no bloquear dashboard completo.

### 8.4 Exclusión cliente SYSTEM

En agregaciones de negocio (planes, trials, donuts), filtrar:

```text
codigo_cliente !== 'SYSTEM'
```

*(Código configurable en Backend: `SUPERADMIN_CLIENTE_CODIGO`, default `SYSTEM`.)*

---

## 9. Fuera de alcance del Dashboard Platform (no implementar)

| Widget / KPI | Motivo |
|--------------|--------|
| MRR, ARR, churn revenue | Sin API facturación |
| Empresas por tenant (global) | Sin API Platform cross-tenant |
| Uso ERP (documentos, transacciones) | Datos en BD tenant |
| SSO / federación CRUD | API `/sso/*` retorna 501 |
| Salud API multi-instancia | `/metrics` solo proceso local |
| Test conexión como semáforo | Endpoint simulado |

---

## 10. Checklist entrega Frontend

- [ ] Cliente HTTP con `Authorization` + `Origin` Platform
- [ ] Adapters paginación `skip/limit` vs `page/limit`
- [ ] Home MVP widgets W1–W15
- [ ] Servicio alertas §4.1
- [ ] Exclusión SYSTEM en agregaciones
- [ ] No renderizar credenciales conexión
- [ ] Placeholder / feature flag widgets §6 hasta BFF
- [ ] Abstracción para migrar a `GET /superadmin/dashboard/` sin reescribir UI

---

## 11. Referencias Backend (solo documentación)

| Documento | Contenido |
|-----------|-----------|
| `PLATFORM_DASHBOARD_BACKEND_CAPABILITY_AUDIT.md` | Inventario capacidades y matriz tablas |
| `PLATFORM_DASHBOARD_BFF_IMPLEMENTATION_AUDIT.md` | Contrato futuro BFF Fase B |

---

*Fin del contrato Frontend — Dashboard Platform Administration.*
