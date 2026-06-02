# Remediación P0 — Manejo de excepciones en módulo Tenant

**Fecha:** 2026-06-02  
**Alcance:** `app/modules/tenant/presentation/endpoints_clientes.py`, `endpoints_conexiones.py`  
**Referencia:** `BACKEND_EXCEPTION_HANDLING_STANDARD_AUDIT.md`, `CLIENTES_EXCEPTION_MAPPING_AUDIT.md`  
**Restricciones:** Sin cambios de contrato API, sin lógica de negocio nueva, sin tocar otros módulos.

---

## 1. Inventario de handlers corregidos

### `endpoints_clientes.py` (10 handlers)

| Handler | Anti-patrón eliminado | Notas |
|---------|----------------------|-------|
| `crear_cliente` | `except Exception` → 500 | Delegación directa a servicio |
| `listar_clientes` | `except Exception` → 500 | Idem |
| `obtener_cliente` | `except Exception` → 500 | Conserva `HTTPException(404)` solo cuando el servicio devuelve `None` |
| `actualizar_cliente` | `except Exception` → 500 | Idem |
| `eliminar_cliente` | `except Exception` → 500 | Idem |
| `suspender_cliente` | `except Exception` → 500 | Idem |
| `activar_cliente` | `except Exception` → 500 | Idem |
| `obtener_estadisticas_cliente` | `except Exception` → 500 | Idem |
| `obtener_branding_por_subdominio` | `except ValidationError/NotFoundError` manual + `except Exception` → 500 | Unificado: propagación al handler global |
| `obtener_branding_tenant` | `except Exception` → 500 | Conserva solo `RuntimeError` → `HTTPException(400)` (contexto de tenant sin `CustomException`) |

**Sin cambios (diagnóstico):** `debug_user_info`, `debug_access_levels`.

### `endpoints_conexiones.py` (6 handlers)

| Handler | Anti-patrón eliminado |
|---------|----------------------|
| `listar_conexiones_cliente` | `except Exception` → 500 |
| `obtener_conexion_principal` | `except Exception` → 500 |
| `crear_conexion` | `except Exception` → 500 |
| `actualizar_conexion` | `except Exception` → 500 |
| `desactivar_conexion` | `except Exception` → 500 |
| `test_conexion` | `except Exception` → 500 |

**Total:** 16 bloques `except Exception: raise HTTPException(500)` eliminados en Presentation Tenant.

---

## 2. Patrón final adoptado

### Regla principal (handlers de negocio con `ClienteService` / `ConexionService`)

No envolver la llamada al servicio en `try/except Exception`. Las subclases de `CustomException` lanzadas en Application **ascienden sin transformación** hasta el handler global registrado en `configure_exception_handlers` (`app/core/exceptions.py`).

```python
# Patrón adoptado — delegación sin degradación
async def crear_cliente(...):
    logger.info(...)
    resultado = await ClienteService.crear_cliente(cliente_data)
    return ClienteCreateResponse(...)
```

### Excepciones locales permitidas en Presentation

| Caso | Patrón | Motivo |
|------|--------|--------|
| Recurso `None` sin excepción de servicio | `raise HTTPException(404, detail=...)` | Contrato histórico en `obtener_cliente` |
| Fallo de contexto de tenant (`RuntimeError`) | `except RuntimeError` → `HTTPException(400)` | No es `CustomException`; mensaje de infraestructura de contexto |

### Anti-patrón prohibido en rutas de negocio Tenant

```python
# ❌ NO usar cuando el servicio lanza CustomException
except Exception:
    raise HTTPException(status_code=500, ...)
```

### Respuesta HTTP del handler global

```json
{
  "detail": "<mensaje de negocio>",
  "error_code": "<internal_code>"
}
```

---

## 3. Confirmación de mapeo HTTP

El servicio Tenant ya lanza las excepciones correctas; Presentation ya no las enmascara.

| Excepción | `status_code` | HTTP |
|-----------|---------------|------|
| `ConflictError` | 409 | **409 Conflict** |
| `ValidationError` | 400 | **400 Bad Request** |
| `NotFoundError` | 404 | **404 Not Found** |
| `AuthorizationError` | 403 | **403 Forbidden** |
| `AuthenticationError` | 401 | **401 Unauthorized** |

Códigos internos relevantes en `ClienteService` (sin cambio):

- `CLIENT_CODE_CONFLICT`, `SUBDOMAIN_CONFLICT` → 409
- `CLIENT_CODE_REQUIRED`, validaciones de subdominio → 400
- `CLIENT_NOT_FOUND` y afines → 404

Errores no previstos (`Exception` genérica) siguen resolviéndose en el handler global de último recurso → **500** con `error_code: INTERNAL_ERROR`.

---

## 4. Casos QA ejecutados

### Tests unitarios (`tests/unit/test_tenant_exception_propagation.py`)

| Caso | Verificación | Resultado |
|------|--------------|-----------|
| Código cliente duplicado | `crear_cliente` propaga `ConflictError` 409 + `CLIENT_CODE_CONFLICT` | ✅ |
| Subdominio duplicado (update) | `actualizar_cliente` propaga `ConflictError` 409 + `SUBDOMAIN_CONFLICT` | ✅ |
| Recurso inexistente | `obtener_estadisticas_cliente` propaga `NotFoundError` 404 | ✅ |
| Validaciones de negocio (branding) | `obtener_branding_por_subdominio` propaga `ValidationError` 400 | ✅ |
| Subdominio no encontrado (branding) | Propaga `NotFoundError` 404 | ✅ |
| Conflicto conexión principal | `crear_conexion` propaga `ConflictError` 409 | ✅ |
| Handler global preserva `error_code` | `TestClient` + `ConflictError` → JSON con `error_code` | ✅ |

**Comando:**

```bash
pytest tests/unit/test_tenant_exception_propagation.py -q
```

### QA HTTP en vivo (opcional)

Requiere API en `localhost:8000` y credenciales de superadmin del tenant de prueba. Escenarios:

1. `POST /api/v1/clientes/` con `codigo_cliente` existente → **409** (no 500).
2. `POST` con `subdominio` existente → **409**.
3. `PUT /api/v1/clientes/{id}/` cambiando a código/subdominio en uso → **409**.
4. `GET /api/v1/clientes/{uuid_inexistente}/` → **404**.
5. `GET /api/v1/clientes/branding?subdominio=` inválido → **400**.
6. Validación Pydantic (body inválido) → **422** (handler `RequestValidationError`, sin cambio).

---

## 5. Impacto y siguientes pasos

| Área | Estado |
|------|--------|
| Módulo Tenant Presentation | ✅ P0 completado |
| Otros módulos (users, rbac, menus, …) | Pendiente — fases P1/P2 de auditoría sistémica |
| Servicios / contratos API | Sin cambios |

**Criterio de aceptación cumplido:** `ConflictError` en `POST /clientes/` deja de convertirse en HTTP 500; el cliente recibe 409 con `detail` y `error_code` del handler global.
