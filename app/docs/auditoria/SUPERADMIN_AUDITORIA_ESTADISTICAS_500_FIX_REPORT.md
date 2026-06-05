# SUPERADMIN_AUDITORIA_ESTADISTICAS — Informe de remediación P0

**Fix ID:** `SUPERADMIN_AUDITORIA_ESTADISTICAS_500`  
**Fecha:** 2026-06-03  
**Estado:** Implementado y validado  
**Auditoría origen:** `SUPERADMIN_AUDITORIA_ESTADISTICAS_500_AUDIT.md`

---

## Resumen

Se corrigió el HTTP 500 en endpoints de auditoría superadmin cuando el cliente envía `fecha_desde` / `fecha_hasta` en ISO 8601 con sufijo `Z`. La causa raíz **RC-001** queda resuelta normalizando datetimes timezone-aware a **naive UTC** antes del binding pyodbc hacia columnas SQL Server `DATETIME`. Se aplicó además la remediación secundaria **H-S01** para agregaciones `SUM` que devolvían `NULL`.

**Contrato API:** sin cambios (query params, schemas y códigos HTTP de negocio intactos).  
**Frontend:** sin workarounds.

---

## Causa raíz (RC-001) — confirmada y corregida

| Paso | Antes (fallo) | Después (fix) |
|------|---------------|---------------|
| FE Dashboard | `2026-06-02T16:59:00.233Z` | Sin cambio |
| FastAPI | `datetime` aware UTC | Sin cambio |
| Servicio | Pasaba aware a `execute_query` | `normalize_datetime_for_sql_server()` → naive UTC |
| pyodbc | `'2026-06-02 16:59:00.233000 +00:00'` | `'2026-06-02 16:59:00.233000'` |
| SQL Server | Error **241** → HTTP 500 | Comparación OK → HTTP 200 |

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/superadmin/application/datetime_sql.py` | **Nuevo.** Helpers `normalize_datetime_for_sql_server` y `sql_int_or_zero` |
| `app/modules/superadmin/application/services/superadmin_auditoria_service.py` | Normalización de fechas en 3 métodos; `ISNULL(SUM(...),0)` en queries de agregación; coerción Python con `sql_int_or_zero` |
| `tests/unit/test_superadmin_auditoria_datetime_sql.py` | **Nuevo.** 8 tests unitarios |
| `scripts/_run_auditoria_estadisticas_fix_qa.py` | **Nuevo.** Script QA HTTP con fechas ISO Z |
| `app/bootstrap_v2/00_manifest/evidence/SUPERADMIN_AUDITORIA_ESTADISTICAS_500_FIX_VALIDATION.json` | Evidencia QA runtime |

**Sin modificar:** `endpoints_auditoria.py`, schemas OpenAPI, contratos response.

---

## Implementación

### P0 — Normalización de fechas

Helper común en `datetime_sql.py`:

```python
def normalize_datetime_for_sql_server(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
```

Aplicado al inicio de (antes de validación de rango y construcción de `params`):

1. `SuperadminAuditoriaService.get_logs_autenticacion`
2. `SuperadminAuditoriaService.get_logs_sincronizacion`
3. `SuperadminAuditoriaService.obtener_estadisticas`

### H-S01 — Agregaciones NULL

En `obtener_estadisticas`:

- SQL: `ISNULL(SUM(CASE WHEN ... END), 0)` en `login_exitosos`, `login_fallidos`, `exitosas`, `fallidas`, `eventos_fallidos`
- Python: `sql_int_or_zero(row.get('campo'))` al acumular filas y construir `IPStats` / `UsuarioStats`

---

## Tests agregados

Archivo: `tests/unit/test_superadmin_auditoria_datetime_sql.py`

| Test | Verifica |
|------|----------|
| `test_normalize_datetime_for_sql_server_strips_utc_offset` | ISO Z → naive UTC |
| `test_normalize_datetime_for_sql_server_passthrough_naive` | Naive sin alteración |
| `test_normalize_datetime_for_sql_server_none` | `None` → `None` |
| `test_sql_int_or_zero_coerces_null` | `NULL` → `0` |
| `test_obtener_estadisticas_passes_naive_datetimes_to_execute_query` | Params sin `tzinfo` en estadísticas |
| `test_obtener_estadisticas_null_aggregates_coerced_to_zero` | H-S01 en agregaciones auth |
| `test_get_logs_autenticacion_passes_naive_datetimes` | Params naive en autenticación |
| `test_get_logs_sincronizacion_passes_naive_datetimes` | Params naive en sincronización |

**Resultado pytest:**

```
8 passed in 1.03s
```

Comando:

```bash
python -m pytest tests/unit/test_superadmin_auditoria_datetime_sql.py -v
```

---

## QA ejecutado

**Script:** `scripts/_run_auditoria_estadisticas_fix_qa.py`  
**Entorno:** Docker `fastapi_backend` → `http://localhost:8000`  
**Auth:** login platform `superadmin` / Origin `platform.app.local:5173`  
**Filtro fecha:** ventana 24h con `fecha_desde` y `fecha_hasta` en ISO con sufijo `Z` (mismo patrón Dashboard P1-A)

**Evidencia JSON:**  
`app/bootstrap_v2/00_manifest/evidence/SUPERADMIN_AUDITORIA_ESTADISTICAS_500_FIX_VALIDATION.json`

**Resultado global:** `"passed": true`

---

## Evidencia HTTP 200 (fechas ISO con Z)

### `/estadisticas/`

```
GET /api/v1/superadmin/auditoria/estadisticas/?fecha_desde=2026-06-02T17:03:09.233Z&fecha_hasta=2026-06-03T17:03:09.233Z
→ HTTP 200
```

Respuesta (extracto):

```json
{
  "periodo": {
    "fecha_desde": "2026-06-02T17:03:09.233000",
    "fecha_hasta": "2026-06-03T17:03:09.233000"
  },
  "autenticacion": {
    "total_eventos": 34,
    "login_exitosos": 6,
    "login_fallidos": 0
  },
  "sincronizacion": {
    "total_sincronizaciones": 0,
    "exitosas": 0,
    "fallidas": 0
  }
}
```

**Antes del fix:** HTTP 500, pyodbc error 241, params `('... +00:00', '... +00:00')`.

### `/autenticacion/`

```
GET /api/v1/superadmin/auditoria/autenticacion/?fecha_desde=...Z&fecha_hasta=...Z&limit=5
→ HTTP 200
```

Respuesta (extracto):

```json
{
  "total_logs": 34,
  "pagina_actual": 1,
  "total_paginas": 7,
  "logs": [ "... login_success ..." ]
}
```

### `/sincronizacion/`

```
GET /api/v1/superadmin/auditoria/sincronizacion/?fecha_desde=...Z&fecha_hasta=...Z&limit=5
→ HTTP 200
```

Respuesta (extracto):

```json
{
  "logs": [],
  "total_logs": 0,
  "pagina_actual": 1,
  "total_paginas": 0
}
```

---

## Verificación de regresión

| Escenario | Esperado | Resultado |
|-----------|----------|-----------|
| Estadísticas con ISO Z | 200 + KPIs numéricos | OK |
| Autenticación con ISO Z | 200 + paginación | OK |
| Sincronización con ISO Z | 200 + paginación | OK |
| Sin filtro de fecha | 200 (comportamiento previo) | No regresión esperada |
| Agregaciones vacías | Enteros `0`, no `null` | OK (H-S01) |

---

## Notas operativas

- Tras despliegue con `--reload`, conviene reiniciar el contenedor backend si algún worker quedó con módulo cacheado; el código en disco es correcto y los tests de servicio dentro del contenedor confirman params naive.
- El fix es local al módulo superadmin/auditoría; no altera el pipeline global de `execute_query`.

---

## Cierre

Remediación **P0 + H-S01** completada. Los tres endpoints de auditoría superadmin aceptan fechas ISO con `Z` sin HTTP 500. Contrato API preservado.
