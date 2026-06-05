# Fase B — Auditoría y plan técnico Backend: BFF Dashboard Platform

**Fecha:** 2026-06-03  
**Referencia principal:** `PLATFORM_DASHBOARD_BACKEND_CAPABILITY_AUDIT.md`  
**Alcance:** Diseño e implementación futura de `GET /api/v1/superadmin/dashboard` — **sin código**, **sin commits**, **sin modificar contratos OpenAPI de endpoints existentes**.  
**Objetivo:** Dejar definido el Backend del Dashboard Platform Administration antes de cualquier trabajo Frontend.

---

## 1. Resumen de la Fase B

| Elemento | Decisión |
|----------|----------|
| Endpoint | `GET /api/v1/superadmin/dashboard` |
| Orquestador | `PlatformDashboardService` (nuevo módulo `superadmin`) |
| Presentation | `endpoints_dashboard.py` (nuevo router) |
| Schemas | `schemas_dashboard.py` o sección en `schemas.py` |
| Registro router | `app/api/v1/api.py` → `prefix="/superadmin/dashboard"` **o** incluir en router padre `/superadmin` |
| Contratos existentes | **Intactos** — solo métodos **nuevos** en servicios y archivos nuevos |
| Fuera de MVP BFF | MRR, `/api/v1/metrics/*`, empresas cross-tenant (`org_empresa`), probe SQL conexiones |

**Recomendación de registro de ruta:**

```text
api_router.include_router(
    endpoints_dashboard.router,
    prefix="/superadmin/dashboard",
    tags=["Dashboard Platform (Super Admin)"]
)
```

Ruta final: `GET /api/v1/superadmin/dashboard/` (trailing slash según convención del proyecto en otros routers superadmin).

---

## 2. Contrato completo request / response

### 2.1 Request

**Método y ruta:** `GET /api/v1/superadmin/dashboard/`

**Headers obligatorios (heredados del stack Platform):**

| Header | Requisito |
|--------|-----------|
| `Authorization` | `Bearer <access_token>` — operador `platform_admin` / super admin |
| `Origin` | Origin plataforma (p. ej. `https://platform.app.local`) según política auth existente |

**Query parameters:**

| Parámetro | Tipo OpenAPI | Obligatorio | Default | Validación | Descripción |
|-----------|--------------|-------------|---------|------------|-------------|
| `fecha_desde` | `datetime` (ISO 8601) | No | `now_utc - 24h` | `fecha_desde <= fecha_hasta` | Ventana para bloque `auditoria` y alertas derivadas de auth/sync |
| `fecha_hasta` | `datetime` | No | `now_utc` | idem | Fin de ventana (inclusivo en SQL con `<=`) |
| `incluir_inactivos` | `boolean` | No | `false` | — | Si `false`, conteos de `clientes` excluyen `es_activo=0`; alertas de estado incoherente pueden seguir incluyéndose |
| `excluir_system` | `boolean` | No | `true` | — | Excluir cliente SYSTEM (`codigo_cliente = SUPERADMIN_CLIENTE_CODIGO`) de conteos y tops |
| `top_n` | `integer` | No | `10` | `1 <= top_n <= 50` | Límite para listas `top_*` e `items_criticos` |
| `dias_nuevos_clientes` | `integer` | No | `30` | `1 <= dias <= 365` | Ventana para `nuevos_en_periodo` |
| `dias_alerta_trial` | `integer` | No | `7` | `1 <= dias <= 90` | Trials con `fecha_fin_trial` en rango |
| `dias_alerta_licencia` | `integer` | No | `30` | `1 <= dias <= 365` | Licencias `cliente_modulo` por vencer |
| `horas_error_conexion` | `integer` | No | `24` | `1 <= horas <= 168` | Umbral “error reciente” en `cliente_conexion` |
| `dias_sin_exito_conexion` | `integer` | No | `7` | `1 <= dias <= 90` | Umbral “sin éxito reciente” |
| `umbral_login_fallidos` | `integer` | No | `50` | `>= 1` | Dispara alerta `AUTH_LOGIN_FAILURES_HIGH` si `login_fallidos >= umbral` en periodo |
| `secciones` | `array[string]` | No | todas | Valores permitidos: ver §2.3 | Carga parcial del payload (optimización) |

**Respuestas HTTP:**

| Código | Condición |
|--------|-----------|
| `200` | Payload generado correctamente |
| `403` | Sin `require_super_admin` / permiso |
| `422` | Rango fechas inválido, `top_n` fuera de rango, `secciones` con valor desconocido |
| `500` | Error no controlado (mantener patrón `CustomException` / handler global en implementación) |

**Autorización propuesta:**

```text
@require_super_admin()
dependencies=[Depends(require_permission("platform.dashboard.leer"))]
```

| Alternativa MVP | Permiso existente |
|-----------------|-------------------|
| Sin permiso nuevo | `Depends(require_permission("tenant.cliente.leer"))` |

Registro en bootstrap RBAC: permiso `platform.dashboard.leer` en seed menú Platform (fase implementación, no bloquea diseño).

### 2.2 Response `200` — estructura raíz

```json
{
  "generado_en": "2026-06-03T15:00:00.000Z",
  "periodo": {
    "fecha_desde": "2026-06-02T15:00:00.000Z",
    "fecha_hasta": "2026-06-03T15:00:00.000Z"
  },
  "clientes": { },
  "auditoria": { },
  "licencias": { },
  "conexiones": { },
  "usuarios_platform": { },
  "alertas": [ ],
  "meta": { }
}
```

Si `secciones` filtra bloques, los omitidos pueden devolverse como `null` **o** omitirse del JSON — **recomendación:** omitir claves (menor payload) y documentar en OpenAPI con `optional` por bloque.

### 2.3 Valores permitidos de `secciones`

| Valor | Bloque response |
|-------|-----------------|
| `clientes` | `clientes` |
| `auditoria` | `auditoria` |
| `licencias` | `licencias` |
| `conexiones` | `conexiones` |
| `usuarios_platform` | `usuarios_platform` |
| `alertas` | `alertas` (siempre recomendado calcular si hay otras secciones; puede ser sección independiente) |
| `meta` | `meta` — **siempre presente** |

Default (sin query): todas las secciones + `meta` + `alertas`.

### 2.4 Bloques de response (detalle contractual)

#### 2.4.1 `clientes` — `DashboardClientesBlock`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total` | `int` | `COUNT(*)` con filtros `incluir_inactivos`, `excluir_system` |
| `activos` | `int` | `es_activo = 1` (mismos filtros) |
| `inactivos` | `int` | `total - activos` |
| `por_estado_suscripcion` | `Dict[str, int]` | Claves: `activo`, `suspendido`, `cancelado`, otros en BD |
| `por_plan` | `Dict[str, int]` | `plan_suscripcion` |
| `por_tipo_instalacion` | `Dict[str, int]` | `shared`, `dedicated`, `onpremise`, `hybrid` |
| `demo` | `int` | `es_demo = 1` |
| `nuevos_en_periodo` | `int` | `fecha_creacion >= fecha_hasta - dias_nuevos_clientes` |
| `trials_por_vencer` | `int` | `plan_suscripcion = 'trial'` y `fecha_fin_trial` entre hoy y hoy + `dias_alerta_trial` |
| `trials_vencidos` | `int` | `plan_suscripcion = 'trial'` y `fecha_fin_trial < hoy` |
| `estado_incoherente` | `int` | `estado_suscripcion = 'activo' AND es_activo = 0` (pre/post F-001) |
| `suspendidos` | `int` | Atajo: `por_estado_suscripcion['suspendido']` |

#### 2.4.2 `auditoria` — `DashboardAuditoriaBlock`

Reutiliza semántica de `AuditoriaEstadisticasResponse` + extensiones:

| Campo | Tipo | Origen |
|-------|------|--------|
| `autenticacion` | `AutenticacionStats` | Reuso schema existente |
| `sincronizacion` | `SincronizacionStats` | Reuso schema existente |
| `top_ips` | `List[IPStats]` | Reuso |
| `top_usuarios` | `List[UsuarioStats]` | Reuso |
| `top_clientes` | `List[DashboardClienteActividadItem]` | **Nuevo** — `TOP N` por `COUNT(*)` en `auth_audit_log` agrupado por `cliente_id` |

`DashboardClienteActividadItem`:

| Campo | Tipo |
|-------|------|
| `cliente_id` | `UUID` |
| `razon_social` | `string` |
| `codigo_cliente` | `string` |
| `total_eventos` | `int` |
| `login_fallidos` | `int` |

#### 2.4.3 `licencias` — `DashboardLicenciasBlock`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `activaciones_activas` | `int` | `cliente_modulo.esta_activo = 1` |
| `activaciones_totales` | `int` | Todas las filas (histórico) |
| `modo_prueba_activas` | `int` | `modo_prueba = 1 AND esta_activo = 1` |
| `por_vencer` | `int` | `fecha_vencimiento` en `(hoy, hoy + dias_alerta_licencia]` |
| `vencidas_activas` | `int` | `esta_activo = 1` y `fecha_vencimiento < hoy` |
| `top_modulos` | `List[DashboardTopModuloItem]` | `modulo_id`, `modulo_codigo`, `modulo_nombre`, `clientes_con_modulo_activo` |

#### 2.4.4 `conexiones` — `DashboardConexionesBlock`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total_activas` | `int` | `cliente_conexion.es_activo = 1` |
| `total_inactivas` | `int` | `es_activo = 0` |
| `con_error_reciente` | `int` | `fecha_ultimo_error >= now - horas_error_conexion` |
| `sin_exito_reciente` | `int` | `ultima_conexion_exitosa IS NULL OR ultima_conexion_exitosa < now - dias_sin_exito_conexion` (solo `es_activo=1`) |
| `dedicated_sin_principal_activa` | `int` | Clientes `tipo_instalacion IN ('dedicated','onpremise')` sin fila `es_conexion_principal=1 AND es_activo=1` |
| `items_criticos` | `List[DashboardConexionCriticaItem]` | Top por severidad (error reciente primero) |

`DashboardConexionCriticaItem`:

| Campo | Tipo | Notas |
|-------|------|-------|
| `cliente_id` | `UUID` | |
| `razon_social` | `string` | JOIN `cliente` |
| `codigo_cliente` | `string` | |
| `conexion_id` | `UUID` | |
| `servidor` | `string` | Sin credenciales |
| `nombre_bd` | `string` | |
| `es_conexion_principal` | `bool` | |
| `ultima_conexion_exitosa` | `datetime?` | |
| `ultimo_error` | `string?` | Truncar a 500 chars en API |
| `fecha_ultimo_error` | `datetime?` | |
| `severidad` | `enum` | `critical`, `warning`, `info` |

#### 2.4.5 `usuarios_platform` — `DashboardUsuariosPlatformBlock`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cliente_system_id` | `UUID` | Resuelto vía `SUPERADMIN_CLIENTE_ID` o lookup por `SUPERADMIN_CLIENTE_CODIGO` |
| `operadores_activos` | `int` | Usuarios SYSTEM con rol `ADMIN_PLATFORM` o `SUPER_ADMIN` y `es_activo=1` |
| `operadores_inactivos` | `int` | idem `es_activo=0` |
| `sesiones_activas_globales` | `int` | `refresh_tokens` con `is_revoked=0` y `expires_at > now` (opcional fase B3) |

#### 2.4.6 `alertas` — `List[DashboardAlertaItem]`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `codigo` | `string` | Constante estable (ver §5) |
| `severidad` | `enum` | `critical`, `warning`, `info` |
| `mensaje` | `string` | Texto humano ES |
| `cliente_id` | `UUID?` | Nullable para alertas globales |
| `entidad_tipo` | `string?` | `cliente`, `conexion`, `cliente_modulo`, `auditoria` |
| `entidad_id` | `UUID?` | |
| `detectado_en` | `datetime` | `generado_en` o timestamp del dato |
| `metadata` | `Dict[str, Any]?` | Valores umbral, conteos, etc. |

**Orden de salida:** `critical` → `warning` → `info`; dentro de cada severidad por `codigo` ASC.

**Límite:** máximo `50` alertas en payload (configurable); el resto en `meta.alertas_omitidas`.

#### 2.4.7 `meta` — `DashboardMetaBlock`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `version` | `string` | `"1.0"` — versión contrato BFF |
| `secciones_incluidas` | `List[string]` | |
| `duracion_ms` | `int` | Tiempo total orchestration |
| `cache` | `DashboardCacheMeta?` | `hit`, `key`, `ttl_segundos` |
| `limitaciones` | `List[string]` | p. ej. `mrr_no_disponible`, `auditoria_solo_bd_central_shared` |
| `alertas_omitidas` | `int` | Si se truncó lista |

---

## 3. DTOs sugeridos (Pydantic)

**Ubicación propuesta:** `app/modules/superadmin/presentation/schemas_dashboard.py`

### 3.1 Reutilización de DTOs existentes

Importar desde `app/modules/superadmin/presentation/schemas.py`:

| Schema existente | Uso en BFF |
|------------------|------------|
| `PeriodoInfo` | `periodo` raíz (o duplicar `DashboardPeriodo` alias) |
| `AutenticacionStats` | `auditoria.autenticacion` |
| `SincronizacionStats` | `auditoria.sincronizacion` |
| `IPStats` | `auditoria.top_ips` |
| `UsuarioStats` | `auditoria.top_usuarios` |

### 3.2 DTOs nuevos (lista)

```python
# Esquema raíz
class PlatformDashboardResponse(BaseModel): ...

# Bloques
class DashboardClientesBlock(BaseModel): ...
class DashboardAuditoriaBlock(BaseModel): ...
class DashboardLicenciasBlock(BaseModel): ...
class DashboardConexionesBlock(BaseModel): ...
class DashboardUsuariosPlatformBlock(BaseModel): ...
class DashboardMetaBlock(BaseModel): ...
class DashboardCacheMeta(BaseModel): ...

# Ítems de listas
class DashboardClienteActividadItem(BaseModel): ...
class DashboardTopModuloItem(BaseModel): ...
class DashboardConexionCriticaItem(BaseModel): ...
class DashboardAlertaItem(BaseModel): ...

# Enums
class AlertaSeveridad(str, Enum): critical = "critical"; warning = "warning"; info = "info"
class DashboardSeccion(str, Enum): clientes = "clientes"; ...
```

### 3.3 Ejemplo de definición raíz (referencia implementación)

```python
class PlatformDashboardResponse(BaseModel):
    generado_en: datetime
    periodo: PeriodoInfo
    clientes: Optional[DashboardClientesBlock] = None
    auditoria: Optional[DashboardAuditoriaBlock] = None
    licencias: Optional[DashboardLicenciasBlock] = None
    conexiones: Optional[DashboardConexionesBlock] = None
    usuarios_platform: Optional[DashboardUsuariosPlatformBlock] = None
    alertas: List[DashboardAlertaItem] = Field(default_factory=list)
    meta: DashboardMetaBlock
```

**OpenAPI tag:** `Dashboard Platform (Super Admin)`  
**response_model:** `PlatformDashboardResponse`

---

## 4. Servicios reutilizables y extensiones

### 4.1 Principio de orquestación

```
endpoints_dashboard.get_dashboard()
    → PlatformDashboardService.build_dashboard(params)
        → asyncio.gather por sección (paralelo)
        → PlatformDashboardAlertService.evaluar_alertas(bloques, params)
        → ensamblar PlatformDashboardResponse
```

**No llamar** en loop:

- `ClienteService.obtener_estadisticas(cliente_id)` por cada tenant (N+1).
- `ConexionService.obtener_conexiones_cliente(cliente_id)` por cada tenant.
- `ClienteModuloService.obtener_modulos_activos_cliente(cliente_id)` por cada tenant.

### 4.2 `ClienteService` — reutilización

| Método existente | ¿Reutilizar en BFF? | Motivo |
|------------------|---------------------|--------|
| `listar_clientes(skip, limit, solo_activos, buscar)` | **No** para agregados | Devuelve página, no `GROUP BY`; dos llamadas solo darían total parcial |
| `obtener_cliente_por_id` | **No** en dashboard global | Solo detalle unitario |
| `obtener_estadisticas` | **No** en orquestación global | Diseñado per-tenant; 1 cliente = 3 queries |
| `obtener_cliente_por_id` | **Sí** puntual | Enriquecer `top_clientes` / alertas si falta `razon_social` en JOIN |

**Métodos nuevos propuestos** (no alteran contratos existentes):

| Método nuevo | Retorno | Responsabilidad |
|--------------|---------|-----------------|
| `ClienteService.obtener_resumen_dashboard_clientes(incluir_inactivos, excluir_system, dias_nuevos, dias_trial)` | `DashboardClientesBlock` o `dict` | Todas las agregaciones §2.4.1 en 1–3 queries |
| `ClienteService._where_dashboard_clientes(...)` | `str, dict` | Helper SQL compartido (privado) |

**Patrón SQL reutilizado de `listar_clientes`:**

- `execute_query(..., connection_type=DatabaseConnection.ADMIN, client_id=None)`
- Mismo estilo `text(...).bindparams(...)` que `count_query` en líneas 503–510 de `cliente_service.py`

**Query ejemplo — distribución estado:**

```sql
SELECT estado_suscripcion, COUNT(*) AS total
FROM cliente
WHERE (:incluir_inactivos = 1 OR es_activo = 1)
  AND (:excluir_system = 0 OR codigo_cliente <> :system_codigo)
GROUP BY estado_suscripcion
```

### 4.3 `ConexionService` — reutilización

| Método existente | ¿Reutilizar? | Motivo |
|------------------|--------------|--------|
| `obtener_conexiones_cliente` | **No** en global | Per-tenant |
| `obtener_conexion_principal` | **No** en global | Per-tenant |
| `test_conexion` | **No** | Simulado — no apto alertas |
| `crear/actualizar/desactivar_conexion` | **No** | Mutaciones |

**Métodos nuevos propuestos:**

| Método nuevo | Responsabilidad |
|--------------|-----------------|
| `ConexionService.obtener_resumen_dashboard_conexiones(horas_error, dias_sin_exito, top_n, excluir_system)` | Conteos + `items_criticos` con JOIN `cliente` |
| `ConexionService.contar_dedicated_sin_principal_activa(excluir_system)` | Query §4.5 Q-CONN-04 |

**Campos BD ya mapeados en `ConexionRead`:** `ultima_conexion_exitosa`, `ultimo_error`, `fecha_ultimo_error` — suficientes para KPI sin `ConexionConEstadisticas` en MVP.

### 4.4 `ClienteModuloService` — reutilización

| Método existente | ¿Reutilizar? | Motivo |
|------------------|--------------|--------|
| `obtener_modulos_activos_cliente` | **No** en global | Lista por tenant |
| `validar_licencia` | **No** | Unitario |
| `activar/desactivar_modulo_cliente` | **No** | Mutaciones |

**Métodos nuevos propuestos:**

| Método nuevo | Responsabilidad |
|--------------|-----------------|
| `ClienteModuloService.obtener_resumen_dashboard_licencias(dias_alerta_licencia, top_n)` | Conteos + `top_modulos` |
| `ClienteModuloService.listar_licencias_vencidas_activas(limit)` | Alimentar alertas `LICENSE_EXPIRED_ACTIVE` |

**JOIN recomendado** (mismo estilo que `obtener_modulos_activos_cliente`):

```sql
SELECT cm.modulo_id, m.codigo AS modulo_codigo, m.nombre AS modulo_nombre,
       COUNT(DISTINCT cm.cliente_id) AS clientes_activos
FROM cliente_modulo cm
INNER JOIN modulo m ON cm.modulo_id = m.modulo_id
WHERE cm.esta_activo = 1
GROUP BY cm.modulo_id, m.codigo, m.nombre
ORDER BY clientes_activos DESC
OFFSET 0 ROWS FETCH NEXT :top_n ROWS ONLY
```

### 4.5 `SuperadminAuditoriaService` — reutilización

| Método existente | ¿Reutilizar? | Motivo |
|------------------|--------------|--------|
| `obtener_estadisticas(cliente_id, fecha_desde, fecha_hasta)` | **Condicional** | Misma forma de respuesta (`AuditoriaEstadisticasResponse`); ver riesgo R-01 |
| `get_logs_autenticacion` | **No** en MVP | Drill-down — pantalla Auditoría |
| `get_logs_sincronizacion` | **No** en MVP | idem |

**Estrategia recomendada (sin romper contrato del endpoint `/estadisticas/`):**

1. **Opción A (preferida):** Extraer SQL a métodos privados compartidos, p. ej. `_query_auth_stats_admin(where, params)`, y que:
   - `obtener_estadisticas` siga llamando como hoy (comportamiento preservado).
   - `PlatformDashboardService` llame a `SuperadminAuditoriaService.obtener_estadisticas_para_dashboard(...)` **nuevo**, forzando `connection_type=DatabaseConnection.ADMIN` cuando `cliente_id is None`.

2. **Opción B (mínima):** `PlatformDashboardService` invoca `obtener_estadisticas(None, ...)` y documenta limitación en `meta.limitaciones` hasta corregir routing.

**Método nuevo:**

| Método | Responsabilidad |
|--------|-----------------|
| `obtener_estadisticas_para_dashboard(fecha_desde, fecha_hasta, top_n)` | Envuelve stats + `top_clientes` query Q-AUD-03 |
| `obtener_top_clientes_por_eventos(...)` | Solo si no se fusiona en un solo SQL |

**Extensión `top_clientes`:** no existe en `obtener_estadisticas` actual — **query nueva obligatoria** (§6).

### 4.6 `SuperadminUsuarioService` — reutilización opcional (fase B3)

| Método existente | ¿Reutilizar? |
|------------------|--------------|
| `get_usuarios_globales(cliente_id=SYSTEM_UUID, ...)` | **Ineficiente** — paginación para contar |
| `obtener_sesiones_usuario` | **No** en global |

**Método nuevo:**

| Método | Responsabilidad |
|--------|-----------------|
| `SuperadminUsuarioService.contar_operadores_platform()` | COUNT con JOIN `usuario_rol` + `rol` WHERE `codigo_rol IN ('ADMIN_PLATFORM','SUPER_ADMIN')` |

### 4.7 `PlatformDashboardService` (nuevo)

**Ruta:** `app/modules/superadmin/application/services/platform_dashboard_service.py`

| Método | Descripción |
|--------|-------------|
| `build_dashboard(params: DashboardQueryParams) -> PlatformDashboardResponse` | Orquestador principal |
| `_resolve_periodo(fecha_desde, fecha_hasta)` | Defaults 24h |
| `_resolve_system_cliente_id()` | Cache en request desde env |

### 4.8 `PlatformDashboardAlertService` (nuevo)

**Ruta:** `app/modules/superadmin/application/services/platform_dashboard_alert_service.py`

| Método | Descripción |
|--------|-------------|
| `evaluar(bloques, params) -> List[DashboardAlertaItem]` | Motor reglas §5 |
| `_add(codigo, severidad, mensaje, ...)` | Helper |

Separar alertas del orquestador mantiene tests unitarios por regla.

---

## 5. Alertas operativas en el payload

### 5.1 Catálogo de códigos MVP

| Código | Severidad default | Condición | Fuente |
|--------|-------------------|-----------|--------|
| `CLIENT_STATE_INCOHERENT` | `critical` | `estado_incoherente > 0` | `clientes.estado_incoherente` |
| `CLIENT_TRIAL_EXPIRED` | `warning` | `trials_vencidos > 0` | `clientes.trials_vencidos` |
| `CLIENT_TRIAL_EXPIRING` | `info` | `trials_por_vencer > 0` | `clientes.trials_por_vencer` |
| `AUTH_LOGIN_FAILURES_HIGH` | `warning` | `login_fallidos >= umbral_login_fallidos` | `auditoria.autenticacion` |
| `AUTH_SYNC_FAILURES` | `warning` | `sincronizacion.fallidas > 0` en periodo | `auditoria.sincronizacion` |
| `LICENSE_EXPIRING` | `info` | `licencias.por_vencer > 0` | `licencias` |
| `LICENSE_EXPIRED_ACTIVE` | `critical` | `licencias.vencidas_activas > 0` | `licencias` |
| `CONN_ERROR_RECENT` | `critical` | `conexiones.con_error_reciente > 0` | `conexiones` + ítems |
| `CONN_NO_SUCCESS_RECENT` | `warning` | `sin_exito_reciente > 0` | `conexiones` |
| `CONN_DEDICATED_NO_PRINCIPAL` | `critical` | `dedicated_sin_principal_activa > 0` | `conexiones` |
| `MODULE_CATALOG_INACTIVE_WITH_ACTIVE_LICENSES` | `warning` | Query Q-LIC-05 > 0 | SQL nueva |
| `SSO_MODE_WITHOUT_FEDERATION` | `info` | Query Q-CLI-06 > 0 | SQL nueva |
| `SYNC_ENABLED_STALE` | `info` | Query Q-CLI-07 > 0 | `cliente.sincronizacion_habilitada` |

### 5.2 Alertas fase B2+ (no MVP)

| Código | Notas |
|--------|-------|
| `IP_HIGH_FAILURE_RATIO` | Por cada IP en `top_ips` con ratio > 0.7 y `total_eventos >= 10` |
| `TENANT_NO_ACTIVE_USERS` | Requiere agregación `usuario` global |
| `PLATFORM_OPERATOR_NONE_ACTIVE` | `operadores_activos == 0` |

### 5.3 Alertas explícitamente excluidas

| Código | Motivo |
|--------|--------|
| `MRR_BELOW_*` | Sin datos |
| `API_LATENCY_*` | `/metrics` no persistido |
| `CONN_TEST_FAILED` | Test simulado |

### 5.4 Generación de ítems detallados

Para alertas con entidad conocida, incluir hasta `top_n` ítems en `metadata.items` (además del conteo agregado), p. ej.:

```json
{
  "codigo": "CONN_ERROR_RECENT",
  "severidad": "critical",
  "mensaje": "2 conexiones con error en las últimas 24 horas",
  "entidad_tipo": "conexion",
  "metadata": {
    "total": 2,
    "items": [ /* DashboardConexionCriticaItem[] */ ]
  }
}
```

---

## 6. Queries nuevas necesarias

Todas ejecutan con **`connection_type=DatabaseConnection.ADMIN`** y `client_id=None`, salvo nota explícita para auditoría multi-BD dedicated.

### 6.1 Clientes (`ClienteService`)

| ID | Nombre | SQL / lógica |
|----|--------|--------------|
| Q-CLI-01 | Conteos base | `COUNT` total / activos con filtros `incluir_inactivos`, `excluir_system` |
| Q-CLI-02 | GROUP BY | `estado_suscripcion`, `plan_suscripcion`, `tipo_instalacion` |
| Q-CLI-03 | Nuevos | `fecha_creacion >= DATEADD(day, -@dias, GETDATE())` |
| Q-CLI-04 | Trials | `plan_suscripcion = 'trial'` + ventanas `fecha_fin_trial` |
| Q-CLI-05 | Estado incoherente | `estado_suscripcion = 'activo' AND es_activo = 0` |
| Q-CLI-06 | SSO sin federación | `c.modo_autenticacion IN ('sso','hybrid')` AND NOT EXISTS (SELECT 1 FROM federacion_identidad f WHERE f.cliente_id = c.cliente_id AND f.es_activo = 1) |
| Q-CLI-07 | Sync stale | `sincronizacion_habilitada = 1` AND (`ultima_sincronizacion IS NULL` OR `ultima_sincronizacion < DATEADD(day, -7, GETDATE()))` |

### 6.2 Licencias (`ClienteModuloService`)

| ID | Nombre | SQL / lógica |
|----|--------|--------------|
| Q-LIC-01 | Conteos activas/totales/prueba | `SUM/COUNT` sobre `cliente_modulo` |
| Q-LIC-02 | Por vencer / vencidas activas | Filtro `fecha_vencimiento` vs `GETDATE()` |
| Q-LIC-03 | Top módulos | JOIN `modulo`, `GROUP BY`, `TOP :top_n` |
| Q-LIC-04 | Lista vencidas activas (alertas) | SELECT con `cliente_id`, `modulo_id`, `fecha_vencimiento` LIMIT |
| Q-LIC-05 | Catálogo inactivo con licencia activa | `cliente_modulo.esta_activo=1` JOIN `modulo` WHERE `modulo.es_activo=0` |

### 6.3 Conexiones (`ConexionService`)

| ID | Nombre | SQL / lógica |
|----|--------|--------------|
| Q-CONN-01 | Conteos activas/inactivas | `cliente_conexion` |
| Q-CONN-02 | Error reciente | `fecha_ultimo_error >= DATEADD(hour, -@horas, GETDATE())` |
| Q-CONN-03 | Sin éxito reciente | `es_activo=1` AND (`ultima_conexion_exitosa` NULL o antigua) |
| Q-CONN-04 | Dedicated sin principal | `cliente c` LEFT JOIN `cliente_conexion cc` ON principal activa — `HAVING COUNT(cc.conexion_id)=0` |
| Q-CONN-05 | Ítems críticos | SELECT TOP (:top_n) JOIN `cliente`, ORDER BY `fecha_ultimo_error DESC` |

### 6.4 Auditoría (`SuperadminAuditoriaService` / dashboard)

| ID | Nombre | SQL / lógica |
|----|--------|--------------|
| Q-AUD-01 | Auth stats global | Reutilizar SQL de `obtener_estadisticas` con **ADMIN** |
| Q-AUD-02 | Sync stats global | idem |
| Q-AUD-03 | Top clientes | `SELECT TOP (@n) a.cliente_id, c.razon_social, COUNT(*) ... GROUP BY a.cliente_id` JOIN `cliente c` |
| Q-AUD-04 | Top IPs / usuarios | Reutilizar queries existentes con ADMIN |

### 6.5 Usuarios Platform (`SuperadminUsuarioService`)

| ID | Nombre | SQL / lógica |
|----|--------|--------------|
| Q-USR-01 | Operadores platform | COUNT `usuario u` JOIN `usuario_rol ur` JOIN `rol r` WHERE `u.cliente_id = @system_id` AND `r.codigo_rol IN (...)` |
| Q-USR-02 | Sesiones activas globales | `COUNT refresh_tokens WHERE is_revoked=0 AND expires_at > GETDATE()` (fase B3) |

### 6.6 Estimación de round-trips BD (MVP)

| Escenario | Queries paralelas (~) |
|-----------|------------------------|
| Todas las secciones | 8–12 |
| Solo `clientes` + `auditoria` | 4–6 |

Objetivo implementación: **≤ 12** queries por request completo (gather async).

---

## 7. Riesgos

| ID | Riesgo | Prob. | Impacto | Mitigación en implementación |
|----|--------|-------|---------|--------------------------------|
| R-01 | `obtener_estadisticas` usa `execute_query` sin `ADMIN` cuando `cliente_id=None` | Alta | Stats auth/sync incompletos o contexto SYSTEM erróneo | Método nuevo `obtener_estadisticas_para_dashboard` con `ADMIN` explícito; documentar en `meta.limitaciones` hasta validar |
| R-02 | Tenants `dedicated` con `auth_audit_log` solo en BD tenant | Media | Dashboard global subestima eventos | Fase 2: agregación federada multi-BD o replicación a central; MVP: `limitacion` + métricas solo central/shared |
| R-03 | F-001 estado `es_activo` vs `estado_suscripcion` distorsiona KPI “activos” | Alta | Widgets incorrectos | Alerta `CLIENT_STATE_INCOHERENT`; corregir F-001 en paralelo a Fase B |
| R-04 | Carga en BD central con gather sin caché | Media | Latencia > 2s con muchos tenants | Caché Redis TTL 60–120s; `secciones` parciales |
| R-05 | `SUPERADMIN_CLIENTE_ID` vacío en env | Media | Conteos incluyen SYSTEM o fallan | Fallback lookup por `SUPERADMIN_CLIENTE_CODIGO` |
| R-06 | Duplicación SQL entre BFF y auditoría | Baja | Deuda mantenimiento | Extraer `_dashboard_queries.py` o métodos privados compartidos |
| R-07 | Alertas como spam (muchas `info`) | Media | UX ruido | Cap 50 alertas; umbrales query params |
| R-08 | Exposición `ultimo_error` con datos sensibles | Baja | Fuga info | Truncar mensaje; no loguear credenciales |
| R-09 | Permiso `platform.dashboard.leer` no seedeado | Media | 403 en prod | Usar `tenant.cliente.leer` en MVP o incluir seed D010 |
| R-10 | Tests sin BD integration | Media | Regresiones SQL | Tests integración con fixtures mínimos por bloque |

---

## 8. Estrategia de caché

### 8.1 Obetivo

Reducir presión sobre BD central en la “home” Platform que refrescará cada 30–60s por operador.

### 8.2 Clave de caché

```text
platform:dashboard:v1:{hash_parametros_normalizados}
```

**`hash_parametros_normalizados`:** SHA256 de JSON ordenado de:

- `fecha_desde` (bucket redondeado a minuto opcional),
- `fecha_hasta`,
- `incluir_inactivos`, `excluir_system`,
- `top_n`, `dias_*`, `horas_error_conexion`, `dias_sin_exito_conexion`,
- `umbral_login_fallidos`,
- `secciones` ordenadas.

**No incluir** `usuario_id` en clave — dashboard es global Platform (mismo payload para todos los super admins). Si en futuro hay filtros por operador, versionar a `v2`.

### 8.3 Backend de caché

| Capa | Implementación existente | Uso |
|------|--------------------------|-----|
| Primaria | `app/infrastructure/cache/redis_cache.py` (`get_cached` / `set_cached`) | TTL 90s default |
| Fallback | Dict en memoria del módulo (como `connection_cache`) | Si `ENABLE_REDIS_CACHE=false` |

### 8.4 TTL recomendado

| Bloque | TTL | Invalidación |
|--------|-----|--------------|
| Completo | 90s | Manual: `DELETE platform:dashboard:v1:*` en deploy |
| Solo `auditoria` | 60s | Ventana temporal — datos más volátiles |
| `clientes` / `licencias` | 120s | Tras `POST/PUT/DELETE /clientes`, `cliente-modulo` — invalidación opcional fase B2 |

**MVP:** TTL fijo global 90s sin invalidación fina (aceptable para Fase B).

### 8.5 Cabeceras HTTP (opcional fase B3)

```http
Cache-Control: private, max-age=60
X-Dashboard-Cache: HIT | MISS
```

### 8.6 Stale-while-revalidate (opcional)

No MVP. Documentar para fase posterior si latencia p99 > SLA.

### 8.7 Contenido de `meta.cache`

```json
{ "hit": true, "key": "platform:dashboard:v1:abc...", "ttl_segundos": 90 }
```

---

## 9. Esfuerzo estimado

Estimación para **1 desarrollador** familiarizado con el repo, incluyendo tests unitarios + 1 integración por bloque.

| Entregable | Días | Notas |
|------------|------|-------|
| Schemas + endpoint + router + permiso | 1.0 | OpenAPI generado |
| `PlatformDashboardService` + Q-CLI | 1.0 | Bloque clientes |
| Q-LIC + bloque licencias | 1.0 | Top módulos |
| Q-CONN + bloque conexiones | 1.0 | Ítems críticos |
| Auditoría reuse + Q-AUD-03 + ADMIN fix | 1.5 | R-01 |
| `PlatformDashboardAlertService` | 1.0 | 10–12 reglas MVP |
| Caché Redis + meta | 0.5 | |
| Tests (unit + integración ligera) | 1.5 | |
| Documentación OpenAPI / runbook | 0.5 | |
| **Total Fase B MVP** | **8.0 días** | |
| B3: usuarios platform + sesiones + IP alerts | +1.5 | |
| Invalidación caché fina | +0.5 | |
| Agregación auditoría multi-BD dedicated | +3.0 | Fuera MVP |

**Story points orientativos:** 13 SP (MVP) + 5 SP (B3/hardening).

---

## 10. Plan de implementación por fases

### Fase B0 — Preparación (0.5 día)

| # | Tarea | Criterio de salida |
|---|-------|-------------------|
| B0.1 | Crear `schemas_dashboard.py` con DTOs §3 | Models importables |
| B0.2 | Crear stubs `platform_dashboard_service.py`, `platform_dashboard_alert_service.py`, `endpoints_dashboard.py` | Router registrado en `api.py` (404/501 temporal aceptable) |
| B0.3 | Decidir permiso: `platform.dashboard.leer` vs `tenant.cliente.leer` | Documentado en PR |
| B0.4 | Alinear con equipo si F-001 se despliega antes del dashboard | KPI coherentes |

### Fase B1 — MVP núcleo (3 días)

| # | Tarea | Dependencias |
|---|-------|--------------|
| B1.1 | Implementar Q-CLI-01..05 → `DashboardClientesBlock` | B0 |
| B1.2 | `obtener_estadisticas_para_dashboard` (Q-AUD-01/02/04 + ADMIN) | B0 |
| B1.3 | `PlatformDashboardService.build_dashboard` con `clientes` + `auditoria` | B1.1, B1.2 |
| B1.4 | `PlatformDashboardAlertService` reglas: AUTH_*, CLIENT_STATE_*, CLIENT_TRIAL_* | B1.3 |
| B1.5 | Endpoint `GET /superadmin/dashboard/` funcional mínimo | B1.4 |
| B1.6 | Tests unitarios alertas + clientes (mock DB) | B1.5 |

**Criterio aceptación B1:**

- Response 200 con `clientes`, `auditoria`, `alertas`, `meta`.
- `fecha_desde/hasta` validados.
- 403 sin super admin.

### Fase B2 — Licencias y conexiones (2.5 días)

| # | Tarea |
|---|-------|
| B2.1 | Q-LIC-01..05 + `DashboardLicenciasBlock` |
| B2.2 | Q-CONN-01..05 + `DashboardConexionesBlock` |
| B2.3 | Alertas LICENSE_*, CONN_* |
| B2.4 | Q-CLI-06, Q-CLI-07 (SSO, sync stale) |
| B2.5 | Tests integración SQL (containers o BD dev) |

**Criterio aceptación B2:**

- Payload completo §2.4 excepto `usuarios_platform` opcional.
- `items_criticos` ≤ `top_n`.
- Sin credenciales en JSON.

### Fase B3 — Operadores Platform y optimización (2 días)

| # | Tarea |
|---|-------|
| B3.1 | Q-USR-01 + `DashboardUsuariosPlatformBlock` |
| B3.2 | Q-AUD-03 `top_clientes` |
| B3.3 | Query param `secciones` + `asyncio.gather` condicional |
| B3.4 | Caché Redis §8 |
| B3.5 | Q-USR-02 sesiones (opcional) |
| B3.6 | Tests carga: p95 < 1.5s con caché warm |

### Fase B4 — Cierre Platform Backend Dashboard (0.5 día)

| # | Tarea |
|---|-------|
| B4.1 | Actualizar `PLATFORM_DASHBOARD_BACKEND_CAPABILITY_AUDIT.md` — marcar BFF implementado |
| B4.2 | Contrato consumo Frontend (solo documento): campos obligatorios por widget |
| B4.3 | Runbook operaciones: interpretación alertas |
| B4.4 | QA checklist smoke Platform |

---

## 11. Estructura de archivos propuesta

```text
app/modules/superadmin/
  application/services/
    platform_dashboard_service.py          # NEW
    platform_dashboard_alert_service.py    # NEW
    platform_dashboard_queries.py          # NEW (opcional — SQL strings)
  presentation/
    endpoints_dashboard.py                 # NEW
    schemas_dashboard.py                   # NEW
```

**Registro en `api.py`:**

```python
from app.modules.superadmin.presentation import endpoints_dashboard as superadmin_dashboard_endpoints

api_router.include_router(
    superadmin_dashboard_endpoints.router,
    prefix="/superadmin/dashboard",
    tags=["Dashboard Platform (Super Admin)"]
)
```

---

## 12. Criterios de aceptación globales (Fase B cerrada)

1. `GET /api/v1/superadmin/dashboard/` documentado en OpenAPI con `PlatformDashboardResponse`.
2. Ningún endpoint existente cambia schema ni status codes.
3. Todas las agregaciones central usan `DatabaseConnection.ADMIN`.
4. Payload incluye `meta.limitaciones` explícitas (MRR, dedicated audit, metrics).
5. Al menos 10 reglas de alerta activas en catálogo §5.1.
6. Tests automatizados cubren: validación fechas, ensamblado bloques, 3 reglas críticas de alerta.
7. Caché configurable vía Redis con fallback documentado.
8. Frontend puede implementar dashboard solo consumiendo este endpoint (UC-D01 **Completo** a nivel Backend).

---

## 13. Relación con cierre Platform Administration

| Hallazgo previo | Cómo lo resuelve Fase B |
|---------------|-------------------------|
| F-010 Dashboard sin contrato | Contrato §2 + endpoint |
| H-007 (capability audit) | BFF agregador |
| UC-D01 Imposible | Pasa a **Completo** (Backend) |
| UC-D02 Parcial | FE deja de componer N endpoints |

**No resuelve:** F-001, F-003, F-004 (módulos), F-007 (empresas), F-005 (SSO CRUD), facturación ejecutiva.

---

## 14. Checklist pre-implementación para el desarrollador

- [ ] Confirmar en staging que `auth_audit_log` global para dashboard usa BD ADMIN
- [ ] Confirmar UUID `SUPERADMIN_CLIENTE_ID` en `.env`
- [ ] Validar planes reales en BD (`trial`, `basic`, etc.) para mapeo `por_plan`
- [ ] Acordar umbrales default alertas con operaciones
- [ ] Definir si `secciones` omitidas retornan `null` o ausencia de clave
- [ ] Revisar F-001 timeline vs release dashboard

---

*Fin del documento — Fase B plan técnico BFF Dashboard Platform Administration.*
