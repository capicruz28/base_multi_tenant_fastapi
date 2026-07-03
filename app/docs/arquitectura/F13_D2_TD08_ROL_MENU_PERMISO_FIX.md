# F13-D2 — Fix TD-08 en PermisoService (`rol_menu_permiso`)

**Fecha:** 2026-06-28  
**Prerequisito:** F13-D1 (auditoría)  
**Alcance:** Una corrección mínima en `PermisoService.obtener_permisos_por_rol()`  
**Estado:** Completado — sin commits

---

## 1. Problema (recapitulación F13-D1)

Dedicated → Administración → Roles → Permisos fallaba con:

```text
SecurityError — Filter defensivo cliente_id obligatorio en dedicated (TD-08)
This text() construct doesn't define a bound parameter named 'cliente_id'
```

**Causa:** `qmark_sql_text` generaba `p.cliente_id = :p0`; `_has_tenant_filter` no reconocía el filtro → TD-08 re-intentaba inyección defensiva y fallaba.

---

## 2. Cambio implementado

**Archivo único:** `app/modules/rbac/application/services/permiso_service.py`

### Antes

```python
WHERE p.cliente_id = ? AND p.rol_id = ?
...
permisos = await execute_query(
    qmark_sql_text(query, (cliente_id, rol_id)),
)
```

### Después (patrón `RolService.obtener_permisos_por_rol`)

```python
WHERE p.cliente_id = :cliente_id AND p.rol_id = :rol_id
...
from sqlalchemy import text

permisos = await execute_query(
    text(query).bindparams(
        cliente_id=cliente_id,
        rol_id=rol_id,
    ),
    client_id=cliente_id,
)
```

### Invariantes respetadas

| Restricción | Cumplido |
|-------------|:--------:|
| SQL funcional (SELECT, JOIN, WHERE, ORDER BY) | ✅ |
| Sin cambios en `query_helpers.py` | ✅ |
| Sin cambios en `execute_query()` | ✅ |
| Sin cambios en routing / TD-08 | ✅ |
| Sin bypass / sin `identity_scope` | ✅ |
| Solo mecanismo de parámetros | ✅ |

---

## 3. Diff arquitectónico

```text
PermisoService.obtener_permisos_por_rol
  ANTES: qmark_sql_text → :p0/:p1 → TD-08 false negative → SecurityError
  DESPUÉS: text().bindparams(:cliente_id/:rol_id) + client_id= → TD-08 satisfied → execute
```

`_has_tenant_filter` detecta substring `cliente_id = :cliente_id` en `p.cliente_id = :cliente_id` → no re-inyección defensiva.

---

## 4. Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `app/modules/rbac/application/services/permiso_service.py` | Método `obtener_permisos_por_rol` (~8 LOC) |

**No modificados:** `query_helpers.py`, `queries_async.py`, `routing.py`, endpoints, frontend.

---

## 5. Validación HTTP

**Entorno:** Docker `http://localhost:8000`

| Escenario | Endpoint | Resultado |
|-----------|----------|-----------|
| **Dedicated** `acce` — login + roles + permisos | `GET /api/v1/permisos/roles/{rol_id}/permisos/` | **HTTP 200** — 18 permisos |
| **Shared** `acme` — regresión | Idem | **HTTP 200** — 18 permisos |

**Rol probado Dedicated:** `37fa2ec5-b953-4245-98a1-56a111855808` (ADMIN_TENANT)

### Verificaciones

| Criterio | Resultado |
|----------|:---------:|
| Sin `SecurityError` TD-08 | ✅ |
| Sin modificar `query_helpers` | ✅ |
| Shared sin regresión | ✅ |
| OpenAPI / Frontend | Sin cambios |

---

## 6. Riesgos residuales

| ID | Riesgo | Notas |
|----|--------|-------|
| R-D2-01 | `p.fecha_actualizacion` en SELECT | Columna no declarada en `RolMenuPermisoTable` ORM (F13-D1); no bloqueó en entorno probado — vigilar si schema DP difiere |
| R-D2-02 | Otros métodos `PermisoService` siguen con `qmark_sql_text` | Mismo patrón TD-08 posible en Dedicated (`obtener_permiso_especifico`, etc.) — fuera de alcance D2 |

---

## 7. Referencias

| Documento | Uso |
|-----------|-----|
| F13-D1 | Diagnóstico y Opción A recomendada |
| `RolService.obtener_permisos_por_rol` | Patrón de referencia |

---

*Fix F13-D2 — detenido.*
