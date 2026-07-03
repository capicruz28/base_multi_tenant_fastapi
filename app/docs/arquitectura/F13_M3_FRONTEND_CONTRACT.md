# F13-M3 — Contrato de integración: estadísticas globales de usuarios Platform

**Audiencia:** cualquier consumidor HTTP (SPA, mobile, BFF, scripts).  
**Backend:** FastAPI — ruta implementada en F13-M3.  
**Fecha:** 2026-06-25

---

## 1. Endpoint

| Campo | Valor |
|-------|-------|
| **Ruta** | `/api/v1/superadmin/usuarios/stats` |
| **Método HTTP** | `GET` |
| **Permisos requeridos** | Super Administrador / Platform Admin — mismo gate que `GET /superadmin/usuarios/` (`@require_super_admin()`) |
| **Autenticación** | `Authorization: Bearer <access_token>` |

---

## 2. Request

### 2.1 Query parameters

| Parámetro | Tipo | Obligatorio | Descripción |
|-----------|------|-------------|-------------|
| `cliente_id` | UUID | No | Acota estadísticas a un tenant. Shared: filtra por `cliente_id`. Dedicated: resuelve store del tenant vía OSR (solo routing, sin enriquecimiento). |
| `search` | string (1–50) | No | Búsqueda ILIKE en `nombre_usuario`, `correo`, `nombre`, `apellido`. |
| `proveedor_autenticacion` | string | No | Filtro exacto (ej. `local`, `azure_ad`). |

**No soportados en stats (a diferencia del listado):**

- `page`, `limit` — no hay paginación.
- `ordenar_por`, `orden` — no aplica a agregados.
- `es_activo` — el endpoint devuelve desglose activo/inactivo; no filtrar por uno solo.

### 2.2 Headers

| Header | Requerido | Valor |
|--------|-----------|-------|
| `Authorization` | Sí | `Bearer <JWT access>` |
| `X-Client-Type` | Recomendado | `web` o `mobile` (convención auth existente) |

### 2.3 Autenticación

Sesión Platform Admin válida. Token de impersonación tenant **no** es el caso de uso de este endpoint.

---

## 3. Response

### 3.1 Schema: `PlatformUsuariosStatsResponse`

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `total_usuarios` | integer ≥ 0 | Sí | Total usuarios no eliminados que cumplen filtros |
| `usuarios_activos` | integer ≥ 0 | Sí | `es_activo = true` |
| `usuarios_inactivos` | integer ≥ 0 | Sí | `es_activo = false` |
| `usuarios_bloqueados` | integer ≥ 0 | Sí | `fecha_bloqueo IS NOT NULL` |

**Campos opcionales:** ninguno — los cuatro contadores son siempre presentes.

### 3.2 Ejemplo JSON (200 OK)

```json
{
  "total_usuarios": 128,
  "usuarios_activos": 100,
  "usuarios_inactivos": 28,
  "usuarios_bloqueados": 5
}
```

### 3.3 Códigos HTTP

| Código | Condición |
|--------|-----------|
| 200 | Estadísticas calculadas |
| 401 | Token inválido o ausente |
| 403 | Sin privilegios Super Admin |
| 404 | `cliente_id` no encontrado |
| 422 | Query param inválido (ej. UUID malformado) |
| 500 | Error interno |

**Formato error:** `{ "detail": "<mensaje>" }` (estándar FastAPI).

---

## 4. Casos de uso

### 4.1 Qué métricas devuelve

- Conteo global de usuarios (identity store compartido o tenant filtrado).
- Desglose activos / inactivos.
- Conteo de usuarios bloqueados por intentos fallidos (`fecha_bloqueo`).

### 4.2 Qué métricas NO devuelve

- Lista de usuarios o filas individuales.
- Roles, `access_level`, `is_super_admin`.
- Información de cliente embebida por usuario.
- Campos J2 de degradación (`enrichment_degraded`, `tenant_data_status`, …).
- Sesiones activas, logins recientes, eventos de auditoría.
- Paginación (`pagina_actual`, `total_paginas`).

### 4.3 Qué reemplaza del contrato anterior

| Anti-patrón anterior | Reemplazo M3 |
|---------------------|--------------|
| `GET /superadmin/usuarios/?limit=1` solo para leer `total_usuarios` | `GET /superadmin/usuarios/stats` |
| Ignorar array `usuarios[]` del listado paginado | Stats no incluye `usuarios[]` |
| Asumir KPI sin side-effects de enriquecimiento | Stats no ejecuta reachability por fila |

---

## 5. Compatibilidad

### 5.1 Endpoints que siguen existiendo sin cambios

| Endpoint | Comportamiento |
|----------|----------------|
| `GET /api/v1/superadmin/usuarios/` | Listado paginado enriquecido (J2) — **sin modificación** |
| `GET /api/v1/superadmin/usuarios/{usuario_id}/` | Detalle usuario |
| `GET /api/v1/superadmin/usuarios/clientes/{cliente_id}/usuarios/` | Listado por tenant |

### 5.2 Comportamiento que permanece igual

- Semántica de `total_usuarios` en listado vs stats (mismo WHERE base, paridad con `count_usuarios_globales` M2).
- Fail-soft J2 en listado global.
- Filtros `search` y `proveedor_autenticacion` alineados con listado.

### 5.3 Endpoint recomendado a partir de ahora

Para **widgets KPI**, **tarjetas numéricas** y **bootstrap dashboard** que solo necesitan conteos:

```
GET /api/v1/superadmin/usuarios/stats
```

Para **tablas**, **detalle por fila**, **roles** y **estado reachability por tenant**:

```
GET /api/v1/superadmin/usuarios/
```

---

## 6. Guía de migración (agnóstica al consumidor)

### 6.1 Escenario: consumidor usaba listado paginado solo para KPI

**Antes:**

1. `GET /api/v1/superadmin/usuarios/?limit=1` (opcionalmente sin `page`).
2. Leer `response.total_usuarios`.
3. Descartar `response.usuarios`.

**Después:**

1. `GET /api/v1/superadmin/usuarios/stats`.
2. Leer `response.total_usuarios` (y opcionalmente activos/inactivos/bloqueados).

### 6.2 Pasos de migración

1. **Identificar** llamadas donde `limit=1` (o mínimo) y el consumidor no renderiza filas de `usuarios`.
2. **Sustituir** URL por `/api/v1/superadmin/usuarios/stats`.
3. **Eliminar** query params `page`, `limit`, `ordenar_por`, `orden` de esas llamadas.
4. **Actualizar** parser de respuesta: ya no esperar `usuarios`, `pagina_actual`, `total_paginas`.
5. **Opcional:** usar `usuarios_activos`, `usuarios_inactivos`, `usuarios_bloqueados` para tarjetas adicionales sin nuevas requests.
6. **Conservar** listado paginado donde se muestre tabla o se necesiten campos enriquecidos.

### 6.3 Filtros mono-tenant

Si el consumidor filtraba KPI por tenant:

**Antes:** `GET /superadmin/usuarios/?cliente_id={uuid}&limit=1`  
**Después:** `GET /superadmin/usuarios/stats?cliente_id={uuid}`

### 6.4 Validación post-migración

- Comparar `total_usuarios` stats vs listado con mismos filtros (deben coincidir).
- Confirmar ausencia de logs RI-39 / reachability en traza de la nueva llamada.
- Mantener listado enriquecido en pantallas que lo requieran.

### 6.5 Rollback

El listado legacy sigue disponible; revertir la URL del consumidor es suficiente. No hay breaking change en backend.

---

## 7. Notas operativas

- **Host / Origin:** invocar desde contexto Platform (mismo que otros endpoints superadmin).
- **Dedicated tenants:** stats respeta routing OSR para COUNT; no implica health check por fila.
- **Usuarios solo en DP** sin réplica en identity store compartido: misma limitación preexistente del COUNT global (ver F13-M1 §2.3).

---

**Documento de contrato FE — F13-M3. Backend implementado; sin commits en este ticket.**
