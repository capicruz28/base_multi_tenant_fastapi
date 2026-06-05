# Auditoría runtime — HTTP 500 en `GET /api/v1/superadmin/auditoria/estadisticas/`

**Fecha:** 2026-06-03  
**Alcance:** Exclusivamente Backend — endpoint, servicio, queries, DTO response.  
**Contexto reportado:** Dashboard Platform P1-A consume  
`GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=...&fecha_hasta=...` → **HTTP 500**.  
Otros endpoints responden 200: `/superadmin/auditoria/autenticacion/`, `/clientes/`, `/superadmin/usuarios/`, `/modulos-v2/`.  
**Modo:** Solo lectura — sin código, sin commits.

---

## 1. Resumen ejecutivo

| Campo | Valor |
|-------|-------|
| **Causa raíz (P0 — reproducida)** | Fechas **timezone-aware** (`datetime` con `tzinfo=UTC`) provenientes de query ISO (`…Z`) se serializan a string con offset (`+00:00`) en el binding pyodbc; SQL Server rechaza la conversión (**error 241**) |
| **Archivo principal** | `app/modules/superadmin/application/services/superadmin_auditoria_service.py` |
| **Línea aproximada** | **972** (primera query que falla: `auth_stats_query`) |
| **Cadena de fallo** | `execute_query` → `DatabaseError` → `@handle_service_errors` → endpoint `HTTPException 500` |
| **Clasificación** | **Backend** (binding fechas) + **Contrato** (ISO Z aceptado por FastAPI pero incompatible con SQL Server vía string SQL) |
| **Por qué `/autenticacion/` “funciona”** | Suele llamarse **sin** `fecha_desde`/`fecha_hasta`; con los mismos parámetros de fecha **también falla** (verificado en runtime local) |

**Veredicto:** El 500 del dashboard no es un fallo exclusivo de “estadísticas agregadas”; es el **filtro de fechas ISO con zona horaria** en queries string contra SQL Server. El dashboard P1-A **siempre** envía ventana temporal; el listado de auth muchas veces no.

---

## 2. Cadena de implementación auditada

```
GET /api/v1/superadmin/auditoria/estadisticas/
  → endpoints_auditoria.get_estadisticas_auditoria (L321-358)
    → SuperadminAuditoriaService.obtener_estadisticas (L918-1105)
      → execute_query (string SQL, ? placeholders) × 4
        → pyodbc / SQL Server
  ← AuditoriaEstadisticasResponse (response_model)
```

| Capa | Archivo | Rol |
|------|---------|-----|
| Endpoint | `app/modules/superadmin/presentation/endpoints_auditoria.py` | Query params `cliente_id`, `fecha_desde`, `fecha_hasta`; try/except → 500 genérico en `Exception` |
| Servicio | `app/modules/superadmin/application/services/superadmin_auditoria_service.py` | `obtener_estadisticas` — 4 queries agregadas |
| Query layer | `app/infrastructure/database/queries_async.py` | Convierte `?` → `:paramN`; ejecuta string SQL (deprecated path) |
| DTO | `app/modules/superadmin/presentation/schemas.py` | `AuditoriaEstadisticasResponse`, `PeriodoInfo`, `AutenticacionStats`, etc. |
| Repository dedicado | **No existe** — SQL embebido en servicio |

---

## 3. Contrato del endpoint (actual)

### Request

```http
GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=2026-06-02T00:00:00Z&fecha_hasta=2026-06-03T00:00:00Z
Authorization: Bearer {token}
Origin: {platform_origin}
```

| Parámetro | Tipo FastAPI | Obligatorio |
|-----------|--------------|-------------|
| `cliente_id` | `UUID` | No |
| `fecha_desde` | `datetime` | No |
| `fecha_hasta` | `datetime` | No |

FastAPI/Pydantic parsea `…Z` como **datetime timezone-aware (UTC)**.

### Response esperado (`AuditoriaEstadisticasResponse`)

```json
{
  "periodo": { "fecha_desde": "...", "fecha_hasta": "..." },
  "autenticacion": {
    "total_eventos": 0,
    "login_exitosos": 0,
    "login_fallidos": 0,
    "eventos_por_tipo": {}
  },
  "sincronizacion": {
    "total_sincronizaciones": 0,
    "exitosas": 0,
    "fallidas": 0,
    "por_tipo": {}
  },
  "top_ips": null,
  "top_usuarios": null
}
```

El servicio devuelve `estadisticas.model_dump()` (dict); FastAPI revalida contra `response_model`.

---

## 4. Causa raíz — evidencia runtime

### 4.1 Reproducción local

**Entorno:** `SuperadminAuditoriaService.obtener_estadisticas` invocado directamente contra BD configurada en el repo.

| Escenario | `fecha_desde` / `fecha_hasta` | Resultado |
|-----------|-------------------------------|-----------|
| A | Naive `datetime(2026, 6, 2)` | **200 OK** — queries ejecutan, payload vacío válido |
| B | UTC aware `datetime(2026, 6, 2, tzinfo=timezone.utc)` | **500** — `DatabaseError` |

**Excepción SQL Server (escenario B):**

```text
pyodbc.DataError: ('22007', '... Conversion failed when converting date and/or time from character string. (241) ...')
```

**Parámetros enviados a ODBC (evidencia clave):**

```text
('2026-06-02 00:00:00.000000 +00:00', '2026-06-03 00:00:00.000000 +00:00')
```

**Query que falla primero** (`superadmin_auditoria_service.py` ~L959-972):

```sql
SELECT 
    COUNT(*) as total_eventos,
    SUM(CASE WHEN evento IN ('login_success', 'sso_login_success') AND exito = 1 THEN 1 ELSE 0 END) as login_exitosos,
    ...
FROM dbo.auth_audit_log a
WHERE a.fecha_evento >= ? AND a.fecha_evento <= ?
GROUP BY evento
```

### 4.2 Mecanismo técnico

1. Frontend envía ISO 8601 con sufijo `Z` (contrato dashboard P1-A).
2. FastAPI parsea → `datetime` **aware** UTC.
3. `obtener_estadisticas` añade fechas a `params_auth` sin normalizar (L950-955).
4. `execute_query` (path string SQL, `queries_async.py` ~L315-331) convierte `?` a bind params nombrados.
5. SQLAlchemy/pyodbc serializa el aware datetime como **string con offset** `+00:00`.
6. SQL Server compara contra columna `DATETIME` (`auth_audit_log.fecha_evento`) e **interpreta mal** el literal → **error 241**.
7. `execute_query` envuelve en `DatabaseError` (L360).
8. `@BaseService.handle_service_errors` re-lanza `DatabaseError` (`CustomException`, status 500).
9. Endpoint captura `CustomException` → `HTTPException(500, detail=…)` (L347-352).

**Nota:** Si el cuerpo expuesto al cliente es genérico, puede deberse al handler global que sanitiza 5xx; el log de servidor contiene el detalle SQL completo.

### 4.3 Correlación con dashboard vs listado auth

| Llamada típica | ¿Incluye fechas? | Resultado observado |
|----------------|------------------|---------------------|
| Dashboard KPI `estadisticas` | **Sí** (`fecha_desde`, `fecha_hasta` ISO Z) | **500** |
| Listado `autenticacion` (home feed sin filtro fecha) | **No** | **200** |
| Listado `autenticacion` con mismas fechas ISO Z | **Sí** | **500** (reproducido — misma causa) |

La aparente “asimetría” entre endpoints es **de uso**, no de implementación distinta del filtro de fechas.

---

## 5. Verificación por categoría solicitada

| Categoría | Hallazgo | ¿Causa el 500 reportado? |
|-----------|----------|---------------------------|
| **Manejo fechas ISO** | Aware UTC → string `+00:00` incompatible con SQL Server en path string SQL | **Sí — P0** |
| **Acceso BD ADMIN** | Queries usan `execute_query(..., client_id=cliente_id)` **sin** `connection_type=DatabaseConnection.ADMIN` | No en escenario reproducido (SYSTEM tenant enruta OK); **deuda arquitectónica** |
| **UUID/int inconsistentes** | Endpoint y servicio usan `Optional[UUID]` para `cliente_id` | **No** en este incidente |
| **JOINs** | `top_usuarios`: `INNER JOIN dbo.usuario` (L1060-1061) | No falla si la query previa ya abortó; con datos, riesgo de filas excluidas, no 500 |
| **Agregaciones** | `GROUP BY evento` / `tipo_sincronizacion`; `SUM(CASE…)` | No causa 500 pre-ejecución |
| **Serialización response** | `return model_dump()` + `response_model` | No alcanzado cuando falla query |
| **Null handling** | `row.get('login_exitosos', 0)` devuelve **None** si la clave existe con valor NULL → `TypeError` en `+=` (L982-984); `IPStats(eventos_fallidos=None)` falla Pydantic (L1046-1051) | **Riesgo P1** cuando hay datos y SUM devuelve NULL — **no es la causa del fallo con fechas ISO** |
| **División por cero** | No hay divisiones | N/A |
| **Tipos incompatibles** | `Decimal` desde SQL Server suele coerce en Pydantic int | Riesgo bajo |

---

## 6. Queries ejecutadas por `obtener_estadisticas`

| # | Línea aprox. | Tabla(s) | Propósito |
|---|--------------|----------|-----------|
| Q1 | 972 | `auth_audit_log` | Stats auth agrupadas por `evento` |
| Q2 | 1016 | `log_sincronizacion_usuario` | Stats sync por `tipo_sincronizacion` |
| Q3 | 1045 | `auth_audit_log` | Top 10 IPs |
| Q4 | 1068 | `auth_audit_log` ⋈ `usuario` | Top 10 usuarios |

Todas comparten `params_auth` con fechas cuando se filtran → **todas fallarían** con el mismo error 241 si Q1 falla.

**Conexión:** `client_id=cliente_id` (None en vista global → router usa `SYSTEM_CLIENT_ID`, log: `[ROUTER] Sin contexto de tenant, usando SYSTEM_CLIENT_ID`).

---

## 7. Análisis del endpoint — manejo de errores

```353:357:app/modules/superadmin/presentation/endpoints_auditoria.py
    except Exception as e:
        logger.exception("Error inesperado en endpoint GET /superadmin/auditoria/estadisticas/")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al obtener las estadísticas de auditoría."
        )
```

| Tipo excepción | Ruta | Mensaje cliente típico |
|----------------|------|------------------------|
| `DatabaseError` (fecha SQL) | `except CustomException` (L347) | `detail` con texto SQL (vía `HTTPException`) |
| `ValidationError` (rango fechas) | `CustomException` | 400 — no aplica si fechas ordenadas |
| `ResponseValidationError` | `except Exception` | Mensaje genérico L357 |
| `TypeError` / Pydantic (NULL agregados) | `ServiceError` → `CustomException` | 500 servicio |

**Deuda:** Patrón B — `DatabaseError` no expone `error_code` estándar al cliente; mezcla 500 genérico vs detalle SQL.

---

## 8. Hallazgos secundarios (post-fix fechas)

### H-S01 — NULL en agregaciones SQL

**Ubicación:** L980-986, L1046-1051.

```python
login_exitosos += row.get('login_exitosos', 0)  # None si clave existe y valor es NULL
```

SQL Server puede devolver `NULL` en columnas `SUM(...)` en edge cases. Efecto: `TypeError` o `ValidationError` en `IPStats` → 500 **después** de queries exitosas.

**Clasificación:** Backend  
**Severidad:** P1 (con datos reales en producción)

### H-S02 — Sin `connection_type=ADMIN`

**Ubicación:** L972, L1016, L1045, L1068.

Vista global depende del routing a BD del tenant SYSTEM, no de BD central ADMIN explícita. Contrasta con otras rutas del mismo servicio que sí usan `DatabaseConnection.ADMIN` (p. ej. lookup `cliente`, L227-230).

**Clasificación:** Backend (arquitectura)  
**Impacto:** Subconteo / datos incompletos en multi-BD dedicated — no el 500 ISO actual en entorno SYSTEM.

### H-S03 — `return model_dump()` vs instancia Pydantic

**Ubicación:** L1105.

Devolver dict obliga a doble validación FastAPI. Riesgo de `ResponseValidationError` si el dump incluye tipos no JSON-serializables. Con build exitoso del modelo, riesgo bajo.

**Clasificación:** Contrato / Backend menor

### H-S04 — `PeriodoInfo` con `datetime.min` sin fechas

**Ubicación:** L1078-1080.

Si no se envían fechas, `fecha_desde=datetime.min` (año 1). No causa 500 en prueba local; posible sorpresa contractual en UI.

**Clasificación:** Contrato

---

## 9. Impacto

| Área | Impacto |
|------|---------|
| **Dashboard P1-A** | Widgets KPI auth/sync (logins fallidos, eventos por tipo, top IPs) **bloqueados** |
| **Operaciones** | Imposible filtrar estadísticas por ventana temporal desde consola Platform |
| **Frontend** | Debe evitar `Z` / enviar naive **o** Backend debe normalizar — workaround FE frágil |
| **Otros consumidores** | Cualquier cliente que pase `fecha_desde`/`fecha_hasta` ISO UTC al endpoint |
| **Integridad datos** | Ninguna — fallo pre-persistencia |

---

## 10. Remediación recomendada (sin implementar)

### Fix P0 — Normalización de fechas antes de SQL

**Dónde:** `SuperadminAuditoriaService.obtener_estadisticas` (y **mismo helper** para `get_logs_autenticacion`, `get_logs_sincronizacion`).

**Acción:**

```python
def _sql_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)  # o .astimezone(UTC).replace(tzinfo=None)
    return dt
```

Aplicar a `fecha_desde` / `fecha_hasta` antes de `params.append`.

**Alternativa:** migrar queries a `text().bindparams()` con tipo explícito o `connection_type=ADMIN` + SQLAlchemy Core.

**Criterio aceptación:**

```http
GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=2026-06-02T00:00:00Z&fecha_hasta=2026-06-03T00:00:00Z
→ 200
```

### Fix P1 — Coalesce agregaciones

En procesamiento Python:

```python
int(row.get('login_exitosos') or 0)
```

O en SQL: `ISNULL(SUM(...), 0)`.

### Fix P2 — ADMIN explícito para vista global

Cuando `cliente_id is None`:

```python
connection_type=DatabaseConnection.ADMIN, client_id=None
```

Alinear con BFF dashboard (auditoría previa).

### Fix P2 — Contrato API

Documentar en OpenAPI:

- Fechas aceptadas: ISO 8601; se normalizan a **naive local/UTC** server-side.
- O declarar que solo se acepta formato sin offset (`2026-06-02T00:00:00`).

### Tests recomendados (post-fix)

- `test_estadisticas_accepts_utc_z_suffix_returns_200`
- `test_estadisticas_null_sum_columns_treated_as_zero`
- Integración con `fecha_desde`/`fecha_hasta` iguales al contrato FE dashboard

---

## 11. Workaround Frontend (temporal, no ideal)

| Opción | Acción | Riesgo |
|--------|--------|--------|
| A | Omitir `fecha_desde`/`fecha_hasta` | Stats sin ventana; periodo usa `datetime.min` / `now` |
| B | Enviar datetime **sin** `Z` (naive local) | Depende de TZ servidor |
| C | Enviar solo fecha `2026-06-02` si FastAPI lo acepta | Verificar parsing |

**Recomendación:** corregir Backend (P0); no depender de workaround FE.

---

## 12. Clasificación final

| ID | Hallazgo | Clasificación | Severidad |
|----|----------|---------------|-----------|
| **RC-001** | Binding datetime timezone-aware → SQL Server 241 | **Backend** + **Contrato** | **P0** |
| H-S01 | NULL en SUM no coalesced | **Backend** | P1 |
| H-S02 | Falta `connection_type=ADMIN` global | **Backend** | P2 |
| H-S03 | `model_dump()` en return | **Contrato** | P3 |
| H-S04 | `datetime.min` default periodo | **Contrato** | P3 |

---

## 13. Conclusión

El **HTTP 500** reportado desde Dashboard P1-A en `GET /api/v1/superadmin/auditoria/estadisticas/` con `fecha_desde`/`fecha_hasta` ISO **está causado por la incompatibilidad entre datetimes timezone-aware y el binding string SQL hacia SQL Server**, fallando en la **primera query de agregación** de `SuperadminAuditoriaService.obtener_estadisticas` (~**línea 972**).

No es un defecto exclusivo de las agregaciones `GROUP BY`, ni de UUID, ni de serialización del DTO en el escenario reproducido. El listado `/autenticacion/` responde 200 cuando **no** se envían filtros de fecha; con las mismas fechas ISO falla igual.

**Prioridad de corrección:** normalizar fechas a naive UTC (o bind tipado) en el servicio de auditoría superadmin — mínimo diff, máximo impacto para el dashboard.

---

*Fin de auditoría — sin cambios de código.*
