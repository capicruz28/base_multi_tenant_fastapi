# Auditoría — Capacidades Backend para Dashboard Platform Administration

**Fecha:** 2026-06-03  
**Alcance:** Exclusivamente Backend (`base_multi_tenant_fastapi`). Sin Frontend, sin UX, sin repositorios externos.  
**Referencias obligatorias:**

| Documento | Uso |
|-----------|-----|
| `PLATFORM_BACKEND_CAPABILITY_AUDIT.md` | Inventario API Platform, brechas, métricas dashboard §5.5 y §10 |
| `PLATFORM_ADMIN_USE_CASE_AUDIT.md` | Casos de uso UC-D01/D02, UC-C*, UC-A*, flujos operador |
| `PLATFORM_BACKEND_FINAL_CLOSURE_AUDIT.md` | Hallazgos F-001–F-019, criterio “Platform Ready”, arquitectura datos |
| `PLATFORM_BACKEND_READY_PHASE_A_AUDIT.md` | Estado P0/P1 (reactivación, UUID, paginación módulos, auth-config) |
| `app/docs/database/1.- TABLAS_BD_CENTRAL.sql` | Modelo de datos canónico para KPIs y alertas |

**Modo:** Solo lectura — sin cambios de código, sin commits, sin implementación.

---

## 1. Resumen ejecutivo

| Pregunta | Veredicto |
|----------|-----------|
| ¿Existe API de dashboard Platform? | **No** — no hay `GET /superadmin/dashboard` ni equivalente |
| ¿Hay KPIs de negocio listos en un solo endpoint? | **Parcial** — auditoría global sí; clientes/módulos/licencias requieren composición o agregación nueva |
| ¿BD Central alimenta dashboard operativo? | **Sí**, con datos suficientes para salud tenants, auth, sync, licencias y conexiones |
| ¿BD Central alimenta dashboard ejecutivo (MRR/churn)? | **No** — sin tablas de facturación/uso comercial |
| ¿BD Central + `/metrics` alimentan dashboard técnico? | **Parcial** — campos en `cliente_conexion` sí; `/api/v1/metrics/*` es runtime in-process, no persistido en central |

**Conclusión:** El Backend puede soportar un **Dashboard operativo** y un **Dashboard técnico (limitado)** mediante composición de endpoints existentes más un **BFF agregador** recomendado. Un **Dashboard ejecutivo comercial** no es viable con el esquema actual sin ampliar el modelo de datos.

**Cobertura estimada de indicadores Platform (catálogo §4):**

| Clasificación | Proporción orientativa |
|---------------|------------------------|
| Disponible hoy | ~35% |
| Reutilizable sin cambios | ~25% |
| Requiere desarrollo Backend | ~30% |
| No recomendable | ~10% |

---

## 2. Metodología y leyenda de clasificación

### 2.1 Cadena evaluada

```
TABLAS_BD_CENTRAL.sql
  → Servicios (ClienteService, SuperadminAuditoriaService, ConexionService, …)
    → Endpoints FastAPI (/api/v1/…)
      → KPI / alerta / widget Dashboard Platform
```

### 2.2 Leyenda por indicador

| Etiqueta | Significado |
|----------|-------------|
| **Disponible hoy** | El consumidor obtiene el dato con un endpoint publicado sin agregación adicional en Backend |
| **Reutilizable sin cambios** | Nuevo método de servicio o query interna sobre tablas/endpoints actuales; **no rompe** contratos OpenAPI existentes |
| **Requiere desarrollo Backend** | Nuevo endpoint, BFF, servicio de agregación o corrección funcional (p. ej. test conexión real) |
| **No recomendable** | Sin datos en BD central, métrica engañosa, o fuera del dominio Platform MVP |

### 2.3 Autenticación y prefijo

- Base API: `/api/v1/`
- Platform: `@require_super_admin()` + permisos `tenant.*`, `modulos.menu.*` según ruta
- Login operador: `user_type=platform_admin`, Origin plataforma (referencia auditorías previas)

---

## 3. Respuestas estructuradas (objetivo del encargo)

### 3.1 Métricas que ya pueden obtenerse hoy mediante endpoints existentes

| KPI / indicador | Endpoint | Servicio | Notas |
|-----------------|----------|----------|-------|
| Total clientes (con filtro `solo_activos`) | `GET /api/v1/clientes/` | `ClienteService.listar_clientes` | Campo `pagination.total` usa `COUNT(*)` real |
| Detalle y atributos por cliente | `GET /api/v1/clientes/{id}/` | `ClienteService.obtener_cliente_por_id` | Incluye `plan_suscripcion`, `estado_suscripcion`, `tipo_instalacion`, fechas, branding |
| Estadísticas por tenant | `GET /api/v1/clientes/{id}/estadisticas/` | `ClienteService.obtener_estadisticas` | Usuarios activos/inactivos, módulos activos/contratados, conexiones activas, días activo |
| Auditoría auth — agregados globales o por tenant | `GET /api/v1/superadmin/auditoria/estadisticas/` | `SuperadminAuditoriaService.obtener_estadisticas` | `total_eventos`, logins ok/fail, sync ok/fail, top IPs/usuarios; filtros `cliente_id`, `fecha_desde/hasta` |
| Logs auth (drill-down) | `GET /api/v1/superadmin/auditoria/autenticacion/` | `SuperadminAuditoriaService.get_logs_autenticacion` | Paginación `page/limit` |
| Logs sync | `GET /api/v1/superadmin/auditoria/sincronizacion/` | `SuperadminAuditoriaService.get_logs_sincronizacion` | Filtros origen/destino, estado, fechas |
| Usuarios globales / por cliente | `GET /api/v1/superadmin/usuarios/`, `…/clientes/{id}/usuarios/` | `SuperadminUsuarioService` | Conteo vía `total` paginado |
| Actividad y sesiones de un usuario | `GET …/usuarios/{id}/actividad/`, `…/sesiones/` | `SuperadminUsuarioService` | `refresh_tokens` |
| Módulos activos por cliente | `GET /api/v1/cliente-modulo/cliente/{cliente_id}/` | `ClienteModuloService` | Licencias, `fecha_vencimiento`, `modo_prueba` en respuesta |
| Catálogo módulos (página) | `GET /api/v1/modulos-v2/` | `ModuloService.obtener_modulos` | Lista; ver §3.3 paginación `total` |
| Conexiones por cliente (salud básica) | `GET /api/v1/conexiones/clientes/{cliente_id}/`, `…/principal/` | `ConexionService` | `ultima_conexion_exitosa`, `ultimo_error`, `fecha_ultimo_error`, `es_activo` |
| Políticas auth por cliente | `GET /api/v1/auth-config/clientes/{cliente_id}` | `AuthConfigService` | Guard distinto (`SUPER_ADMIN` rol código) — ver F-006 |
| Branding tenant | `GET /api/v1/clientes/branding`, `GET /api/v1/clientes/tenant/branding` | `ClienteService.get_branding_*` | Lectura pública/tenant |
| Métricas runtime API (técnico) | `GET /api/v1/metrics/summary`, `GET /api/v1/metrics/slow-queries` | `basic_metrics` | **No** son KPIs SaaS de BD central |

---

### 3.2 Métricas reutilizables sin romper contratos actuales

Implementación típica: métodos estáticos nuevos en servicios existentes, queries `COUNT`/`GROUP BY` sobre ADMIN, **sin** alterar schemas de respuesta de endpoints actuales.

| KPI / indicador | Tabla(s) | Servicio a extender | Patrón |
|-----------------|----------|---------------------|--------|
| Clientes por `estado_suscripcion` | `cliente` | `ClienteService` | `GROUP BY estado_suscripcion` |
| Clientes por `plan_suscripcion` | `cliente` | `ClienteService` | `GROUP BY plan_suscripcion` |
| Clientes por `tipo_instalacion` | `cliente` | `ClienteService` | `GROUP BY tipo_instalacion` |
| Nuevos clientes últimos N días | `cliente` | `ClienteService` | `WHERE fecha_creacion >= @desde` |
| Clientes trial próximos a vencer | `cliente` | `ClienteService` | `plan_suscripcion='trial'`, `fecha_fin_trial` |
| Clientes demo | `cliente` | `ClienteService` | `es_demo=1` |
| Módulos más activados (top N) | `cliente_modulo` | `ClienteModuloService` o nuevo `PlatformDashboardService` | `COUNT` por `modulo_id` |
| Licencias por vencer (7/30 días) | `cliente_modulo` | `ClienteModuloService` | `fecha_vencimiento` entre hoy y @hasta |
| Módulos en modo prueba | `cliente_modulo` | `ClienteModuloService` | `modo_prueba=1` |
| Conexiones con error reciente | `cliente_conexion` | `ConexionService` | `ultimo_error IS NOT NULL` o `fecha_ultimo_error` reciente |
| Conexiones sin éxito reciente | `cliente_conexion` | `ConexionService` | `ultima_conexion_exitosa` antigua o NULL |
| Clientes dedicated sin conexión principal activa | `cliente`, `cliente_conexion` | `ConexionService` + `ClienteService` | JOIN + filtro `tipo_instalacion` |
| Usuarios bloqueados (intentos) | `usuario` | `SuperadminUsuarioService` | `fecha_bloqueo IS NOT NULL` |
| Sesiones activas globales | `refresh_tokens` | `SuperadminUsuarioService` | `is_revoked=0`, `expires_at > now` |
| Top tenants por eventos auth | `auth_audit_log` | `SuperadminAuditoriaService` | Extensión de agregación ya parcial en stats |
| SSO configurado por cliente | `federacion_identidad`, `cliente.modo_autenticacion` | — | Solo lectura; CRUD SSO sigue 501 |
| Operadores Platform (SYSTEM) | `usuario`, `usuario_rol`, `rol` | `SuperadminUsuarioService` | Filtro `cliente_id` = SYSTEM + rol `ADMIN_PLATFORM` |
| Catálogos globales activos/inactivos | `cat_*` | `CatalogosGlobalesService` | COUNT por entidad — bajo valor en dashboard principal |

**Composición cliente-side (sin nuevo endpoint):** UC-D02 documenta que el Frontend puede paralelizar `GET /clientes/?solo_activos=false&limit=1000`, `GET /superadmin/auditoria/estadisticas/?fecha_desde=…` y N× `GET /clientes/{id}/estadisticas/` — viable pero **costoso** y frágil en bases grandes.

---

### 3.3 Métricas que requieren nuevos endpoints o servicios

| KPI / indicador | Motivo | Prioridad sugerida |
|-----------------|--------|-------------------|
| Payload único dashboard Platform | No existe BFF; UC-D01 **Imposible** como flujo único | **P1** |
| Distribución global clientes (estado/plan/tipo) sin paginar todo el listado | `GET /clientes/` no expone `GROUP BY` ni filtros `estado_suscripcion` | **P1** |
| Top módulos activados (global) | Sin endpoint agregado sobre `cliente_modulo` | **P2** |
| Alertas licencias vencidas (lista accionable) | Solo listado por cliente vía `cliente-modulo` | **P2** |
| Panel salud conexiones global | Conexiones solo anidadas bajo `cliente_id` | **P1** |
| Health check batch conexiones | `POST /conexiones/test` simulado (random) — no válido para alertas | **P1** |
| Conteo correcto catálogo módulos en UI paginada | `GET /modulos-v2/` — `total = len(página)` (F-004) | **P1** |
| Empresas por tenant desde Platform | `org_empresa` en ERP; sin API SA nativa (F-007) | **P1** si KPI “empresas activas” en dashboard |
| Métricas facturación (MRR, ARR, churn revenue) | Sin tablas en central | **No recomendable** hasta modelo billing |
| Uso ERP (transacciones, documentos) | Datos en BD tenant, no central | **Requiere** pipeline/telemetría aparte |
| Export CSV auditoría masiva | No implementado | **P3** |
| `ConexionConEstadisticas` (schema existe) | No expuesto en router conexiones | **P2** |

---

### 3.4 Alertas operativas que debería soportar una plataforma SaaS profesional

Basadas en datos **disponibles en BD Central** y capacidad Backend actual o reutilizable.

| Alerta | Fuente BD | Detección hoy | Detección recomendada |
|--------|-----------|---------------|------------------------|
| Cliente eliminado lógico pero “reactivado” solo en suscripción | `cliente.es_activo`, `estado_suscripcion` | Manual (listado + detalle) | **Regla negocio** post F-001: alerta si `estado_suscripcion='activo' AND es_activo=0` |
| Cliente suspendido prolongado | `cliente.estado_suscripcion`, `fecha_actualizacion` | Parcial vía listado | Query programada + webhook/email (fuera scope BE mínimo) |
| Trial vencido sin conversión | `fecha_fin_trial`, `plan_suscripcion` | **Reutilizable** | Job + endpoint alertas |
| Licencia módulo vencida o por vencer | `cliente_modulo.fecha_vencimiento`, `esta_activo` | Por cliente en API módulo | Agregación global licencias |
| Módulo activo en tenant pero desactivado en catálogo | `cliente_modulo`, `modulo.es_activo` | **Reutilizable** | Query inconsistencia |
| Conexión principal con `ultimo_error` reciente | `cliente_conexion` | **Disponible hoy** por tenant en GET conexiones | Panel global + severidad por antigüedad |
| Sin `ultima_conexion_exitosa` en dedicated/onpremise | `cliente_conexion`, `cliente.tipo_instalacion` | **Reutilizable** | Alerta crítica onboarding |
| Login fallidos elevados (24h) | `auth_audit_log` | **Disponible hoy** vía `GET …/auditoria/estadisticas/` | Umbral configurable en BFF |
| IP con alto ratio de fallos | `auth_audit_log` + `top_ips` en stats | **Disponible hoy** | Regla `eventos_fallidos / total_eventos` |
| Sincronización usuario fallida | `log_sincronizacion_usuario.estado` | Stats + listado sync | Umbral `fallidas` en ventana |
| Usuario bloqueado por intentos | `usuario.intentos_fallidos`, `fecha_bloqueo` | **Reutilizable** | Listado superadmin filtrado |
| Sesiones refresh anómalas / revocación masiva | `refresh_tokens` | Por usuario vía sesiones | Agregación global sesiones activas |
| SSO configurado en cliente pero federación vacía | `cliente.modo_autenticacion`, `federacion_identidad` | **Reutilizable** | Alerta configuración incompleta |
| Cliente `shared` sin usuarios activos | `usuario` | Por `GET …/estadisticas/` | Batch reutilizable |
| Sync habilitado sin actividad | `cliente.sincronizacion_habilitada`, `ultima_sincronizacion` | **Reutilizable** | Stale sync alert |

**Alertas no recomendables con datos actuales:** MRR bajo umbral, churn de ingresos, SLA API global (sin APM persistido), latencia BD por tenant (sin probe real en `test_conexion`).

---

### 3.5 Información de conexiones para administración global de plataforma

Campos en `cliente_conexion` (central) relevantes para consola Platform:

| Campo | Uso operativo |
|-------|---------------|
| `servidor`, `puerto`, `nombre_bd`, `tipo_bd` | Inventario y diagnóstico |
| `es_conexion_principal`, `es_activo`, `es_solo_lectura` | Estado operativo y routing |
| `usa_ssl`, `timeout_segundos`, `max_pool_size` | Configuración y hardening |
| `ultima_conexion_exitosa` | Salud — último éxito conocido |
| `ultimo_error`, `fecha_ultimo_error` | Incidentes — **clave para alertas** |
| `fecha_creacion`, `fecha_actualizacion`, `creado_por_usuario_id` | Auditoría cambios |
| Credenciales encriptadas en DTO | Solo administración; no exponer en dashboard público |

**API hoy:**

| Operación | Endpoint |
|-----------|----------|
| Listar todas las conexiones de un tenant | `GET /api/v1/conexiones/clientes/{cliente_id}/` |
| Conexión principal | `GET /api/v1/conexiones/clientes/{cliente_id}/principal/` |
| CRUD / reactivación | `POST`, `PUT`, `DELETE /api/v1/conexiones/…` |
| Test (no fiable) | `POST /api/v1/conexiones/test` — **simulado** |

**Brecha global:** no existe `GET /api/v1/superadmin/conexiones/resumen` ni vista cross-tenant. Para administración global se requiere **desarrollo Backend** (agregación JOIN `cliente` + `cliente_conexion`) o iteración N+1 sobre listado de clientes (no recomendable en producción).

**Schema `ConexionConEstadisticas`:** definido en `schemas.py` (`total_conexiones`, `conexiones_activas`, `tiempo_promedio_respuesta`, `tasa_errores`) pero **no** cableado a endpoints — candidato a dashboard técnico tras instrumentación real.

---

### 3.6 Viabilidad de tres tipos de dashboard

#### Dashboard operativo (NOC / soporte Platform)

| Dimensión | ¿Datos suficientes? | ¿API suficiente hoy? |
|-----------|---------------------|----------------------|
| Inventario tenants (activos, suspendidos, cancelados) | **Sí** — `cliente` | **Parcial** — requiere agregación o múltiples listados |
| Salud auth 24h / fallos | **Sí** — `auth_audit_log` | **Sí** — `GET /superadmin/auditoria/estadisticas/` |
| Sync fallidas | **Sí** — `log_sincronizacion_usuario` | **Sí** — idem |
| Licencias y vencimientos | **Sí** — `cliente_modulo` | **Parcial** — por tenant, no global |
| Conexiones degradadas | **Sí** — `cliente_conexion` | **Parcial** — sin vista global |
| Usuarios / sesiones incidente | **Sí** — `usuario`, `refresh_tokens` | **Sí** — superadmin usuarios |

**Veredicto:** **Construible** con composición FE o **BFF**; datos en central son suficientes. Bloqueadores de calidad: test conexión mock (F-003), reactivación cliente ambigua (F-001) para métricas “activos” fiables.

#### Dashboard ejecutivo (negocio / dirección)

| Dimensión | ¿Datos suficientes? |
|-----------|---------------------|
| MRR, ARR, facturación | **No** — sin tablas billing |
| Churn revenue / expansión | **No** |
| Clientes por plan (conteo) | **Sí** — derivable de `cliente` |
| Nuevos logos / altas 30d | **Sí** — `fecha_creacion` |
| Adopción módulos (ranking) | **Sí** — `cliente_modulo` |
| NPS / satisfacción | **No** |

**Veredicto:** **No construible** como dashboard ejecutivo financiero completo. Solo **subconjunto comercial-lite** (conteos, planes, altas, módulos activados) — clasificar widgets de ingresos como **No recomendable** hasta nuevo dominio de datos.

#### Dashboard técnico (SRE / plataforma)

| Dimensión | ¿Datos suficientes? | ¿API suficiente hoy? |
|-----------|---------------------|----------------------|
| Slow queries / latencia API | In-memory `basic_metrics` | **Parcial** — `/metrics/*` no es histórico ni multi-instancia |
| Errores por tenant en runtime | `tenant_queries` en memoria | **Parcial** |
| Salud BD por tenant | `cliente_conexion` timestamps/errores | **Parcial** — sin probe automático |
| Tipo instalación / routing | `cliente.tipo_instalacion` | **Sí** en `ClienteRead` |
| SSO técnico | `federacion_identidad` | **No** — API 501 |

**Veredicto:** **Parcialmente construible** — útil para troubleshooting conexiones y auth; **no** sustituye APM/observabilidad externa. `/api/v1/metrics/*` debe documentarse como complemento de proceso, no fuente de verdad SaaS.

---

### 3.7 Contrato Backend recomendado — API Dashboard Platform

#### Opción recomendada: BFF bajo prefijo superadmin

```
GET /api/v1/superadmin/dashboard
GET /api/v1/superadmin/dashboard/alertas   (opcional, fase 2)
```

**Rationale frente a `GET /superadmin/dashboard` sin versión:**

- Coherente con rutas existentes: `/api/v1/superadmin/auditoria/`, `/api/v1/superadmin/usuarios/`
- Evita colisión con menú FE `/super-admin/*` (ruta UI, no API)
- Permite evolución v2 sin romper clientes

**Autorización:** `@require_super_admin()` + permiso dedicado `platform.dashboard.leer` (nuevo) o reutilizar `tenant.cliente.leer`.

#### Query parameters propuestos

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `fecha_desde` | datetime ISO | now - 24h | Ventana para métricas auth/sync |
| `fecha_hasta` | datetime ISO | now | Fin ventana |
| `incluir_inactivos` | bool | false | Conteos clientes con `es_activo=0` |
| `top_n` | int | 10 | Límite tops (módulos, tenants, IPs) |
| `secciones` | string[] | all | Filtrar bloques: `clientes`, `auditoria`, `licencias`, `conexiones`, `usuarios_platform` |

#### Response 200 — esquema lógico (propuesta)

```json
{
  "generado_en": "2026-06-03T12:00:00Z",
  "periodo": { "fecha_desde": "...", "fecha_hasta": "..." },
  "clientes": {
    "total": 120,
    "activos": 98,
    "inactivos": 22,
    "por_estado_suscripcion": { "activo": 90, "suspendido": 8, "cancelado": 22 },
    "por_plan": { "trial": 15, "basic": 80, "enterprise": 25 },
    "por_tipo_instalacion": { "shared": 100, "dedicated": 18, "onpremise": 2 },
    "nuevos_ultimos_30_dias": 7,
    "trials_por_vencer_7d": 3
  },
  "auditoria": {
    "autenticacion": { "total_eventos": 5000, "login_exitosos": 4800, "login_fallidos": 120, "eventos_por_tipo": {} },
    "sincronizacion": { "total": 200, "exitosas": 190, "fallidas": 10, "por_tipo": {} },
    "top_ips": [],
    "top_usuarios": []
  },
  "licencias": {
    "modulos_activos_total": 450,
    "por_vencer_30d": 12,
    "vencidas": 4,
    "top_modulos_activados": [{ "modulo_id": "...", "codigo": "INV", "clientes": 80 }]
  },
  "conexiones": {
    "total_activas": 115,
    "con_error_reciente_24h": 2,
    "sin_exito_reciente_7d": 5,
    "items_criticos": [
      {
        "cliente_id": "...",
        "razon_social": "...",
        "conexion_id": "...",
        "ultimo_error": "...",
        "fecha_ultimo_error": "..."
      }
    ]
  },
  "usuarios_platform": {
    "operadores_activos": 8,
    "operadores_inactivos": 1
  },
  "alertas": [
    { "codigo": "CONN_ERROR_RECENT", "severidad": "critical", "cliente_id": "...", "mensaje": "..." }
  ],
  "meta": {
    "fuentes": [
      "ClienteService.agregar_dashboard",
      "SuperadminAuditoriaService.obtener_estadisticas",
      "PlatformDashboardService"
    ],
    "limitaciones": ["mrr_no_disponible", "metrics_runtime_no_persistido"]
  }
}
```

#### Implementación interna sugerida (sin romper contratos)

| Componente | Responsabilidad |
|------------|-----------------|
| `PlatformDashboardService` (nuevo) | Orquesta queries paralelas ADMIN |
| Reuso | `SuperadminAuditoriaService.obtener_estadisticas()` — misma lógica, sin duplicar SQL |
| Reuso | Queries tipo `ClienteService.listar_clientes` COUNT — extraer a métodos `contar_por_*` |
| Caché opcional | TTL 60–120s para reducir carga en dashboard home |

#### Alternativa MVP (solo documentación — F-010)

Si no se implementa BFF en fase 1, publicar **contrato de composición** (OpenAPI adjunct o markdown):

1. `GET /clientes/?solo_activos=false&limit=1` → `total`
2. `GET /clientes/?solo_activos=true&limit=1` → `total` activos
3. `GET /superadmin/auditoria/estadisticas/?fecha_desde=…`
4. Opcional: script batch interno para tops de `cliente_modulo`

Estado actual según auditorías: **UC-D02 Parcial**, **UC-D01 Imposible** como un solo flujo.

---

## 4. Catálogo de métricas e indicadores clasificados

### 4.1 Clientes y tenant

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Total clientes | **Disponible hoy** | `GET /clientes/` → `total` |
| Clientes activos (`es_activo=1`) | **Disponible hoy** | `GET /clientes/?solo_activos=true` → `total` |
| Clientes inactivos/eliminados | **Disponible hoy** | `GET /clientes/?solo_activos=false` + agregación FE o diff |
| Por `estado_suscripcion` | **Reutilizable sin cambios** | SQL `GROUP BY` en servicio nuevo |
| Por `plan_suscripcion` | **Reutilizable sin cambios** | idem |
| Por `tipo_instalacion` | **Reutilizable sin cambios** | idem |
| Nuevos últimos 7/30 días | **Reutilizable sin cambios** | `fecha_creacion` |
| Trials por vencer | **Reutilizable sin cambios** | `fecha_fin_trial` |
| Último acceso plataforma tenant | **Disponible hoy** | Campo en `ClienteRead` / stats |
| Branding configurado | **Disponible hoy** | `GET /clientes/{id}/` |
| MRR / ingresos | **No recomendable** | Sin tabla facturación |

### 4.2 `cliente_conexion`

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Conexiones activas por tenant | **Disponible hoy** | `GET /conexiones/clientes/{id}/` |
| Principal definida | **Disponible hoy** | `GET …/principal/` |
| Último error / fecha | **Disponible hoy** | Campos en `ConexionRead` |
| Resumen global conexiones críticas | **Requiere desarrollo Backend** | BFF o `GET /superadmin/conexiones/resumen` |
| Test conectividad confiable | **Requiere desarrollo Backend** | F-003 — probe SQL real |
| Pool / latencia histórica | **No recomendable** | Sin telemetría persistida |

### 4.3 `cliente_modulo` (licencias)

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Módulos activos por tenant | **Disponible hoy** | `GET /cliente-modulo/cliente/{id}/` o `GET /clientes/{id}/estadisticas/` |
| Módulos contratados vs activos | **Disponible hoy** | `ClienteStatsResponse` |
| Vencimientos próximos (global) | **Reutilizable sin cambios** | Query central |
| Top módulos activados | **Reutilizable sin cambios** | `GROUP BY modulo_id` |
| Ingreso por `precio_mensual` catálogo | **No recomendable** como revenue real | `modulo.precio_mensual` es catálogo, no facturación |

### 4.4 Auditoría (`auth_audit_log`, `log_sincronizacion_usuario`)

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Eventos auth total / ok / fail | **Disponible hoy** | `GET /superadmin/auditoria/estadisticas/` |
| Sync total / ok / fail | **Disponible hoy** | idem |
| Top IPs / usuarios | **Disponible hoy** | idem |
| Serie temporal por hora | **Requiere desarrollo Backend** | `GROUP BY DATEPART` — no expuesto |
| Export masivo compliance | **Requiere desarrollo Backend** | CSV/stream |

### 4.5 Usuarios Platform y tenant

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Usuarios globales (conteo) | **Disponible hoy** | `GET /superadmin/usuarios/` → `total` |
| Usuarios por tenant | **Disponible hoy** | `GET …/clientes/{id}/usuarios/` |
| Usuarios activos/inactivos tenant | **Disponible hoy** | `GET /clientes/{id}/estadisticas/` |
| Operadores `ADMIN_PLATFORM` | **Reutilizable sin cambios** | Filtro SYSTEM + rol |
| Sesiones activas usuario | **Disponible hoy** | `GET …/usuarios/{id}/sesiones/` |
| CRUD operadores Platform | **Requiere desarrollo Backend** (formalización) | Hoy vía `/usuarios` en SYSTEM — UC-P01 Parcial |

### 4.6 Módulos catálogo (`modulo`, secciones, menús, plantillas)

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Total módulos catálogo | **Requiere desarrollo Backend** | F-004 paginación incorrecta |
| Módulos activos/inactivos catálogo | **Reutilizable sin cambios** | `COUNT` con filtros de `ModuloService` |
| Menús / secciones / plantillas | **No recomendable** en dashboard home | Bajo valor operativo salvo QA catálogo |

### 4.7 Auth, branding, SSO

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Políticas auth por cliente | **Disponible hoy** | `GET /auth-config/clientes/{id}` |
| 2FA / lockout config | **Disponible hoy** | Campos en `cliente_auth_config` |
| Federación SSO | **No recomendable** (operativo) | API `/sso/*` → 501 |
| `modo_autenticacion` por cliente | **Disponible hoy** | `ClienteRead` |

### 4.8 Métricas runtime (`/api/v1/metrics`)

| Indicador | Clasificación | Endpoint / vía |
|-----------|---------------|------------------|
| Query counts / slow queries | **Disponible hoy** (limitado) | `/metrics/summary`, `/slow-queries` |
| KPI negocio SaaS | **No recomendable** | No lee BD central |
| SLA multi-instancia | **No recomendable** | Estado en memoria del proceso |

---

## 5. Matriz Tabla BD Central → Servicio → Endpoint → KPI → Alerta

| Tabla BD Central | Servicio Backend | Endpoint existente | Posible KPI | Posible alerta |
|------------------|------------------|-------------------|-------------|----------------|
| `cliente` | `ClienteService` | `GET/POST/PUT/DELETE /api/v1/clientes/*` | Totales activos/inactivos; por plan/estado/tipo; nuevos 30d; trials | Incoherencia `es_activo` vs `estado_suscripcion`; trial vencido; suspendido prolongado |
| `cliente` | `ClienteService` | `GET /clientes/{id}/estadisticas/` | Usuarios, módulos, conexiones, días activo por tenant | Tenant sin usuarios activos |
| `cliente` | `ClienteService` | `GET /clientes/branding`, `tenant/branding` | Branding configurado | — |
| `cliente_conexion` | `ConexionService` | `GET/POST/PUT/DELETE /api/v1/conexiones/*` | Conexiones activas; errores recientes | `ultimo_error` reciente; sin éxito en dedicated |
| `cliente_auth_config` | `AuthConfigService` | `GET/PUT /api/v1/auth-config/clientes/{id}` | Políticas password/sesión/2FA | 2FA requerido admins sin cumplimiento (manual) |
| `federacion_identidad` | — (501) | `/api/v1/sso/*` | SSO configs activas | Cliente en modo SSO sin federación |
| `modulo` | `ModuloService` | `GET /api/v1/modulos-v2/*` | Tamaño catálogo; por categoría | Core desactivado (regla negocio) |
| `modulo_seccion` | `ModuloSeccionService` | `GET /api/v1/secciones/*` | — | — |
| `modulo_menu` | `ModuloMenuService` | `GET /api/v1/modulos-menus/*` | Menús por módulo | — |
| `modulo_rol_plantilla` | `ModuloRolPlantillaService` | `GET /api/v1/plantillas-roles/*` | Plantillas por módulo | — |
| `cliente_modulo` | `ClienteModuloService` | `GET/POST/DELETE /api/v1/cliente-modulo/*` | Licencias activas; vencimientos; modo prueba | Licencia vencida; prueba expirada |
| `usuario` | `SuperadminUsuarioService`, `UsuarioService` | `GET /superadmin/usuarios/*`, `/usuarios/*` | Usuarios globales; bloqueados | Usuario bloqueado; alto inactivos |
| `rol` / `usuario_rol` | `UsuarioService`, RBAC | `/roles/*`, `/usuarios/{id}/roles/*` | Roles por tenant; operadores Platform | Operador sin `ADMIN_PLATFORM` |
| `rol_menu_permiso` | RBAC permisos | `/permisos/*` | — | — |
| `refresh_tokens` | `SuperadminUsuarioService` | `GET …/usuarios/{id}/sesiones/` | Sesiones activas | Sesiones expiradas no revocadas (cleanup) |
| `auth_audit_log` | `SuperadminAuditoriaService` | `GET /superadmin/auditoria/autenticacion/`, `…/estadisticas/` | Logins ok/fail; eventos por tipo; top IP/user | Pico login fallidos; IP abusiva |
| `log_sincronizacion_usuario` | `SuperadminAuditoriaService` | `GET /superadmin/auditoria/sincronizacion/`, `…/estadisticas/` | Sync ok/fail por tipo | Sync fallida repetida |
| `cat_moneda` | `CatalogosGlobalesService` | `GET /catalogos-globales/monedas/*` | Registros activos catálogo | — |
| `cat_pais` | `CatalogosGlobalesService` | `GET /catalogos-globales/paises/*` | Idem | — |
| `cat_departamento` | `CatalogosGlobalesService` | `GET /catalogos-globales/departamentos/*` | Idem | Padre inactivo hijo activo (F-012) |
| `cat_provincia` | `CatalogosGlobalesService` | `GET /catalogos-globales/provincias/*` | Idem | idem |
| `cat_distrito` | `CatalogosGlobalesService` | `GET /catalogos-globales/distritos/*` | Idem | idem |
| *(runtime, no BD)* | `basic_metrics` | `GET /api/v1/metrics/*` | Slow queries proceso | Query >500ms (log local) |

**Tablas ERP (`org_empresa`, etc.):** definidas con FK en central pero datos operativos en BD tenant — KPI “empresas por cliente” requiere impersonación o API SA futura (F-007); **no** en matriz central como fuente directa.

---

## 6. Dependencias y hallazgos que afectan métricas del dashboard

| ID | Hallazgo | Impacto en dashboard |
|----|----------|----------------------|
| F-001 | `PUT /clientes/{id}/activar/` no restaura `es_activo` | KPI “clientes activos” subestimado si operadores usan solo `/activar/` |
| F-002 | UUID `cliente_id` superadmin | Referencia P0; revisión código 2026-06-03: endpoints auditoría/usuarios usan `UUID` — validar en QA filtros |
| F-003 | Test conexión simulado | Widget “salud conexiones” no fiable con `POST /conexiones/test` |
| F-004 | Paginación módulos `total` incorrecto | Widget “módulos en catálogo” erróneo si usa solo `GET /modulos-v2/` |
| F-007 | Sin API empresas cross-tenant | KPI empresas en dashboard operativo limitado |
| F-010 | Sin BFF dashboard | UC-D01 imposible; composición UC-D02 parcial |
| F-019 | `/metrics` ≠ KPI SaaS | Separar dashboard técnico de negocio en contrato |

---

## 7. Roadmap Backend sugerido (solo diseño)

| Fase | Entregable | Clasificación métricas desbloqueadas |
|------|------------|--------------------------------------|
| **A** | Documentar composición UC-D02 (si no BFF) | Disponible hoy + guía integración |
| **B** | `GET /api/v1/superadmin/dashboard` + `PlatformDashboardService` | Reutilizable → Disponible hoy (agregados globales) |
| **C** | F-001 fix + filtros `estado_suscripcion` en listado | Conteos clientes fiables |
| **D** | Resumen global conexiones + probe real | Alertas conexión |
| **E** | F-004 COUNT módulos | KPI catálogo |
| **F** | Dominio billing (si ejecutivo requerido) | MRR — hoy **No recomendable** |

---

## 8. Conclusión

El Backend **dispone de datos suficientes en BD Central** para un **Dashboard operativo** y alertas de seguridad/salud tenant, apoyándose principalmente en `cliente`, `cliente_conexion`, `cliente_modulo`, `auth_audit_log` y `log_sincronizacion_usuario`. La exposición actual es **fragmentada**: el único agregador robusto es `GET /api/v1/superadmin/auditoria/estadisticas/`; el resto exige composición o un **BFF** `GET /api/v1/superadmin/dashboard`.

Un **Dashboard ejecutivo** con métricas financieras **no** debe implementarse sobre el esquema actual. Un **Dashboard técnico** debe combinar campos de `cliente_conexion` y auditoría, tratando `/api/v1/metrics/*` como señal auxiliar de proceso, no como fuente analítica multi-tenant.

**Recomendación principal:** implementar `PlatformDashboardService` + `GET /api/v1/superadmin/dashboard` reutilizando `SuperadminAuditoriaService.obtener_estadisticas` y nuevas queries `COUNT/GROUP BY` en `ClienteService` / `ConexionService` / `ClienteModuloService`, sin modificar contratos de endpoints existentes.

---

## 9. Documentos relacionados (contexto, no ampliados en este entregable)

| Documento | Relación |
|-----------|----------|
| `PLATFORM_FINAL_SURFACE_AUDIT.md` | Menú `/super-admin/dashboard` sin contrato BE |
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Calidad errores en rutas Platform |
| `ORGANIZACION_TABLAS_CENTRAL_VS_DEDICADA.md` | Routing shared vs dedicated para métricas usuario |

---

*Fin del documento — auditoría exclusiva Backend Dashboard Platform Administration.*
