# Auditoría — HTTP 500 en `DELETE /clientes/{cliente_id}`

**Fecha:** 2026-06-02  
**Contexto:** QA funcional Platform Clientes (repositorio Backend)  
**Modo:** solo lectura — sin implementación, sin repair, sin commit  
**Evidencia QA:** `DELETE /clientes/{cliente_id}` → **HTTP 500**; cuerpo genérico `"Error interno del servidor"` (Frontend refleja correctamente la respuesta Backend)

**Referencias relacionadas:**

| Documento | Relación |
|-----------|----------|
| `TENANT_EXCEPTION_HANDLING_REMEDIATION.md` | P0 cerrado — Presentation ya no degrada `CustomException` a 500 |
| `USER_DEACTIVATE_500_RUNTIME_ROOT_CAUSE.md` | Mismo patrón de defecto (`execute_update` sin `await`) en soft-delete de usuarios |
| `BACKEND_EXCEPTION_REMEDIATION_STATUS.md` | Estado global de excepciones |

---

## 1. Resumen ejecutivo

| Campo | Valor |
|-------|-------|
| **Ruta HTTP** | `DELETE /api/v1/clientes/{cliente_id}/` |
| **Clasificación** | **Bug Backend real** (async/await) |
| **Causa raíz** | `ClienteService.eliminar_cliente` invoca `execute_update(...)` **sin `await`** (L453) |
| **Excepción probable en runtime** | `AttributeError: 'coroutine' object has no attribute 'get'` → envuelta por `@handle_service_errors` → `ServiceError` 500 |
| **¿Anti-patrón Presentation (P0)?** | **No** — endpoint ya delega al servicio sin `except Exception` → 500 |
| **¿Error de negocio no mapeado?** | **No** (en el escenario típico QA) |
| **¿Infraestructura / Frontend?** | **No** asumido — síntoma coherente con fallo en capa Application |
| **Soft delete** | **Sí** — `es_activo = 0`, `estado_suscripcion = 'cancelado'` |
| **Remediación recomendada** | Añadir `await` en L453 (alineado a `suspender_cliente`, `activar_cliente`, `actualizar_cliente`) |

---

## 2. Ruta exacta del flujo

### 2.1 Cadena de llamadas

```
HTTP DELETE /api/v1/clientes/{cliente_id}/
    ↓
app/main.py
    app.include_router(api_router, prefix=settings.API_V1_STR)   # /api/v1
    ↓
app/api/v1/api.py
    api_router.include_router(endpoints_clientes.router, prefix="/clientes")
    ↓
app/modules/tenant/presentation/endpoints_clientes.py
    eliminar_cliente()                    # handler
    ↓
app/modules/tenant/application/services/cliente_service.py
    ClienteService.eliminar_cliente()     # lógica de negocio + SQL
    ↓
app/infrastructure/database/queries_async.py
    execute_update()                      # async — BD central (ADMIN)
```

**No existe capa Repository** en el módulo `tenant` para clientes: el servicio ejecuta SQL directamente vía `queries_async` (patrón Fase 2 del proyecto).

### 2.2 Endpoint (Presentation)

| Elemento | Valor |
|----------|-------|
| Archivo | `app/modules/tenant/presentation/endpoints_clientes.py` |
| Handler | `eliminar_cliente` (aprox. L254–268) |
| Método / ruta OpenAPI | `DELETE /{cliente_id}/` bajo prefijo `/clientes` |
| `response_model` | `ClienteDeleteResponse` |
| Status éxito documentado | `200 OK` (no 204) |
| Permiso RBAC | `tenant.cliente.eliminar` (`Depends(require_permission(...))`) |
| Restricción LBAC | `@require_super_admin()` |
| Auth | `get_current_active_user` |

**Código del handler (estado post-P0):**

```python
await ClienteService.eliminar_cliente(cliente_id)
return ClienteDeleteResponse(success=True, message=..., cliente_id=cliente_id)
```

No hay `try/except Exception` que envuelva la llamada al servicio.

### 2.3 Service (Application)

| Elemento | Valor |
|----------|-------|
| Archivo | `app/modules/tenant/application/services/cliente_service.py` |
| Método | `ClienteService.eliminar_cliente(cliente_id: UUID) -> bool` (aprox. L418–462) |
| Decorador | `@BaseService.handle_service_errors` |
| Imports BD | `from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update` |
| Conexión | `DatabaseConnection.ADMIN` (BD central / SaaS) |

### 2.4 Infraestructura (equivalente a “repository”)

| Elemento | Valor |
|----------|-------|
| Archivo | `app/infrastructure/database/queries_async.py` |
| Función | `async def execute_update(...)` → retorna `Dict` con `rows_affected` (y opcionalmente filas `OUTPUT`) |
| Tabla | `cliente` (BD central, ver `app/docs/database/1.- TABLAS_BD_CENTRAL.sql`) |

---

## 3. Comportamiento de negocio (soft delete y validaciones)

### 3.1 Semántica de “eliminar”

No es `DELETE` físico. El servicio ejecuta **eliminación lógica**:

```sql
UPDATE cliente
SET es_activo = 0,
    estado_suscripcion = 'cancelado',
    fecha_actualizacion = GETDATE()
WHERE cliente_id = ?
```

| Campo | Valor tras operación |
|-------|----------------------|
| `es_activo` | `0` |
| `estado_suscripcion` | `'cancelado'` |
| `fecha_actualizacion` | `GETDATE()` |

Alineado con documentación del endpoint (“marcado como inactivo”) y esquema central (`es_activo`, `estado_suscripcion`).

### 3.2 Validaciones previas al UPDATE

| Orden | Validación | Excepción | HTTP esperado (handler global) |
|-------|------------|-----------|--------------------------------|
| 1 | Cliente existe (`obtener_cliente_por_id`) | `NotFoundError` (`CLIENT_NOT_FOUND`) | **404** |
| 2 | No es cliente SYSTEM (`SUPERADMIN_CLIENTE_ID`) | `ValidationError` (`CANNOT_DELETE_SYSTEM_CLIENT`) | **400** |
| 3 | UPDATE ejecutado y `rows_affected > 0` | `ServiceError` (`CLIENT_DELETE_FAILED`) si falla | **500** |

Las validaciones 1 y 2 **funcionarían correctamente** con P0 (propagación al handler global). El fallo QA en cliente **existente y no SYSTEM** apunta al paso 3 con defecto de `await`, no a reglas de negocio.

### 3.3 Cambios recientes de estado

- **P0 excepciones Tenant:** corrige Presentation; **no modifica** `eliminar_cliente` en servicio.
- **Migración Fase 2 async:** el mismo archivo usa `await execute_update` en `suspender_cliente` (L204), `activar_cliente` (L270), `actualizar_cliente` (L407), pero **omite `await` en `eliminar_cliente` (L453)** — inconsistencia intra-archivo, probable regresión de migración parcial.

---

## 4. Excepción real, stack y degradación a HTTP 500

### 4.1 Cadena causal (escenario QA típico)

```
ClienteService.eliminar_cliente()
    cliente = await obtener_cliente_por_id()     ✅ OK
    validación SYSTEM                            ✅ OK (si no es SYSTEM)
    resultado = execute_update(...)              ❌ SIN await → objeto coroutine
    if not resultado or resultado.get(...):      ❌ AttributeError en .get()
        ↓
@handle_service_errors except Exception:
    raise ServiceError(500, "Error interno del servidor en eliminar_cliente",
                       INTERNAL_SERVICE_ERROR)
        ↓
Handler global CustomException (status >= 500):
    response detail sanitizado → "Error interno del servidor"
    error_code → INTERNAL_SERVICE_ERROR (o internal_code del ServiceError)
```

### 4.2 Excepciones probables

| Excepción | Origen | ¿Llega al cliente como? |
|-----------|--------|-------------------------|
| `AttributeError: 'coroutine' object has no attribute 'get'` | L454 — uso de coroutine como dict | **500** vía `ServiceError` wrapper |
| `RuntimeWarning: coroutine 'execute_update' was never awaited` | asyncio (logs) | — |
| `NotFoundError` | Cliente inexistente | **404** (no explica 500 en QA con cliente visible) |
| `ValidationError` | Cliente SYSTEM | **400** (no explica 500 salvo QA contra SYSTEM) |
| `DatabaseError` | Fallo SQL (FK, timeout, etc.) | **500** con `DB_UPDATE_ERROR` — posible pero secundario |
| `ServiceError` (`CLIENT_DELETE_FAILED`) | `rows_affected == 0` **con** `await` correcto | **500** con mensaje “No se pudo eliminar el cliente” — escenario distinto |

### 4.3 ¿Captura incorrecta de excepciones en Presentation?

| Capa | Estado | Conclusión |
|------|--------|------------|
| Presentation (`eliminar_cliente`) | Post-P0: sin `except Exception` | **No** degrada `CustomException` |
| `handle_service_errors` | Convierte `Exception` genérica → `ServiceError` 500 | **Sí** enmascara el `AttributeError` real |
| Handler global | Sanitiza `detail` en 5xx | Explica mensaje genérico en Frontend |

El síntoma QA (**500 + “Error interno del servidor”**) es **coherente con bug de servicio**, no con el anti-patrón Presentation corregido en P0.

### 4.4 Evidencia estática (defecto confirmado en código)

```453:459:app/modules/tenant/application/services/cliente_service.py
        resultado = execute_update(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
        if not resultado or resultado.get('rows_affected', 0) == 0:
            raise ServiceError(
                status_code=500,
                detail="No se pudo eliminar el cliente.",
                internal_code="CLIENT_DELETE_FAILED"
            )
```

**Comparación — mismo archivo, patrón correcto:**

```407:407:app/modules/tenant/application/services/cliente_service.py
        resultado = await execute_update(query, tuple(params), connection_type=DatabaseConnection.ADMIN)
```

```204:204:app/modules/tenant/application/services/cliente_service.py
        resultado = await execute_update(query, (cliente_id,))
```

---

## 5. Clasificación

| Hipótesis | Veredicto | Justificación |
|-----------|-----------|---------------|
| **Bug Backend real** | **Confirmado (principal)** | `execute_update` async llamado sin `await` en soft-delete |
| **Error de negocio no mapeado** | Descartado (escenario QA habitual) | 404/400 están implementados y propagan tras P0 |
| **Problema de infraestructura** | Poco probable como causa primaria | Conexión ADMIN usada igual en GET cliente (funciona en listado/detalle) |
| **Falso positivo / Frontend** | Descartado | Frontend muestra el `detail` del Backend; no hay indicio de malinterpretación |
| **Regresión P0 excepciones** | Descartado | P0 no introduce el defecto; el 500 nace **antes** en Application |

---

## 6. Causa raíz, impacto y remediación

### 6.1 Causa raíz

**Omisión de `await` en la llamada a `queries_async.execute_update` dentro de `ClienteService.eliminar_cliente` (L453).**

Efecto: el UPDATE **no se ejecuta**; el código evalúa un objeto `coroutine` como si fuera el diccionario de resultado y falla con `AttributeError`, transformado en HTTP 500.

### 6.2 Impacto

| Área | Impacto |
|------|---------|
| **Funcional** | Imposible desactivar clientes desde Platform Clientes vía DELETE |
| **Operaciones** | Clientes quedan activos en BD central pese a acción UI “eliminar” |
| **UX / soporte** | Mensaje genérico 500; logs con `ERROR INESPERADO en eliminar_cliente` |
| **Seguridad / datos** | No hay borrado físico accidental; riesgo es **estado inconsistente** (UI falla, dato no cambia) |
| **Alcance** | Solo ruta DELETE; crear/actualizar/listar usan `await` correctamente en la mayoría de métodos |

### 6.3 Remediación recomendada (sin implementar en esta auditoría)

| Prioridad | Acción |
|-----------|--------|
| **P0 fix puntual** | Cambiar L453 a `resultado = await execute_update(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)` |
| **QA regresión** | Test unitario espejo de `test_user_deactivate_execute_update_await.py`: verificar `await_count` y éxito con mock de `execute_update` |
| **QA funcional** | `DELETE /api/v1/clientes/{id}/` sobre cliente de prueba no SYSTEM → **200** + `es_activo=0` en BD |
| **Opcional** | Revisión grep en `cliente_service.py` / módulo tenant por otras llamadas `execute_*` sin `await` |

**Respuestas HTTP esperadas tras fix:**

| Caso | HTTP |
|------|------|
| Cliente desactivado OK | **200** + `ClienteDeleteResponse` |
| ID inexistente | **404** + `error_code: CLIENT_NOT_FOUND` |
| Cliente SYSTEM | **400** + `error_code: CANNOT_DELETE_SYSTEM_CLIENT` |
| Fallo BD real | **500** + `DB_UPDATE_ERROR` o `INTERNAL_SERVICE_ERROR` |

### 6.4 Relación con auditorías previas

| Tema | Relación con DELETE cliente |
|------|----------------------------|
| P0 Tenant Presentation | Resuelve ConflictError/NotFound en POST/PUT; **no aplica** a este 500 |
| USER deactivate 500 | **Misma clase de bug** (`execute_update` sin `await` en soft-delete) |
| Programa P1/P2/P3 | Sin relación directa con esta incidencia |

---

## 7. Checklist de verificación para QA post-fix

1. Autenticarse como superadmin con permiso `tenant.cliente.eliminar`.
2. `DELETE /api/v1/clientes/{uuid_cliente_activo_no_system}/` → **200**, body `success: true`.
3. `GET /api/v1/clientes/{uuid}/` o listado → cliente con `es_activo: false`, `estado_suscripcion: cancelado`.
4. Repetir DELETE sobre mismo ID → según diseño: puede seguir existiendo con `es_activo=0` (UPDATE idempotente con `rows_affected >= 1`) o validación adicional futura.
5. `DELETE` sobre `SUPERADMIN_CLIENTE_ID` → **400**, no 500.
6. `DELETE` sobre UUID inexistente → **404**, no 500.

---

## 8. Conclusión

La incidencia **`DELETE /clientes/{cliente_id}` → HTTP 500** es un **bug Backend real** en `ClienteService.eliminar_cliente`, causado por **`execute_update` sin `await`**, no por el Frontend ni por el anti-patrón de excepciones en Presentation (ya remediado en P0). La operación está diseñada como **soft delete** (`es_activo = 0`, `estado_suscripcion = 'cancelado'`); las validaciones de negocio (404/400) están implementadas pero no se alcanzan en el escenario de fallo por el error previo al commit SQL.

**Fix mínimo:** una línea (`await`) alineada al resto de métodos del mismo servicio.
