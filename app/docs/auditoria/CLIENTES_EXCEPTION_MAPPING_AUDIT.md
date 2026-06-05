# Auditoría: mapeo de excepciones — POST /clientes/ (Administración de Clientes)

**Fecha:** 2026-06-02  
**Alcance:** flujo de creación de clientes (tenant / Super Admin)  
**Síntoma reportado:** `ConflictError` correcta en logs, respuesta HTTP **500** al cliente  
**Modo:** solo lectura — sin cambios de código

---

## 1. Resumen ejecutivo

| Pregunta | Conclusión |
|----------|------------|
| ¿Por qué `ConflictError` devuelve HTTP 500? | El endpoint `crear_cliente` captura **`except Exception`** y reemplaza cualquier excepción de negocio por `HTTPException(500)` genérico, **antes** de que el handler global de `CustomException` pueda responder. |
| ¿Dónde se transforma? | `app/modules/tenant/presentation/endpoints_clientes.py`, líneas **86–91** (`crear_cliente`). |
| ¿Es inconsistente con el resto del backend? | **Sí.** Módulos como ORG mapean `ConflictError` / `CustomException` → `HTTPException(status_code=e.status_code)`. El módulo tenant/clientes no. |
| HTTP correcto para código duplicado | **409 Conflict** (ya definido en `ConflictError` y documentado en OpenAPI del endpoint). |
| ¿Hay más endpoints con el mismo patrón? | **Sí:** 9 handlers más en `endpoints_clientes.py` y 6 en `endpoints_conexiones.py`. |

---

## 2. Flujo trazado (caso: código de cliente duplicado)

### 2.1 Ruta y capas

```
POST /api/v1/clientes/
  → endpoints_clientes.crear_cliente()
    → ClienteService.crear_cliente()
      → ClienteService._validar_codigo_cliente()  ← ConflictError aquí
```

Registro del router: `app/api/v1/api.py` — `prefix="/clientes"`.

### 2.2 Servicio — detección correcta de negocio

**`ClienteService._validar_codigo_cliente()`** (`app/modules/tenant/application/services/cliente_service.py`):

```python
resultado = await execute_query(query, (codigo_cliente,))
if resultado:
    raise ConflictError(
        detail=f"El código de cliente '{codigo_cliente}' ya está en uso.",
        internal_code="CLIENT_CODE_CONFLICT"
    )
```

**`ClienteService.crear_cliente()`** invoca validaciones antes del onboarding:

```python
await ClienteService._validar_subdominio_cliente(cliente_data.subdominio)
await ClienteService._validar_codigo_cliente(cliente_data.codigo_cliente)
resultado = await ClienteOnboardingService.crear_cliente_con_onboarding(cliente_data)
```

Ambos métodos llevan `@BaseService.handle_service_errors`, que **re-lanza** `ConflictError` sin alterarla:

```python
except (ValidationError, NotFoundError, ConflictError, ServiceError):
    raise
```

**Conclusión capa servicio:** la regla de negocio y el tipo de excepción son correctos; el `status_code` heredado de `ConflictError` es **409**.

### 2.3 Definición de `ConflictError`

**`app/core/exceptions.py`:**

```python
class ConflictError(CustomException):
    def __init__(self, detail: str, internal_code: str = "CONFLICT_ERROR"):
        super().__init__(status_code=409, detail=detail, internal_code=internal_code)
```

`ConflictError` **es** una `CustomException` con `status_code=409`.

### 2.4 Handler global (no alcanzado en este flujo)

**`configure_exception_handlers(app)`** en `app/main.py` registra:

```python
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": response_detail, "error_code": exc.internal_code}
    )
```

Si `ConflictError` **bubbling** sin ser capturada en el endpoint, la respuesta sería:

- **HTTP 409**
- Body: `{"detail": "El código de cliente 'CLI003' ya está en uso.", "error_code": "CLIENT_CODE_CONFLICT"}`

Ese handler **existe y es correcto**, pero **no se ejecuta** para `POST /clientes/` por el `try/except` del endpoint.

### 2.5 Endpoint — punto exacto de degradación a 500

**`crear_cliente`** (`app/modules/tenant/presentation/endpoints_clientes.py`):

```python
from app.core.exceptions import ValidationError, NotFoundError
# ConflictError y CustomException NO importados

try:
    resultado = await ClienteService.crear_cliente(cliente_data)
    ...
    return ClienteCreateResponse(...)
except HTTPException:
    raise
except Exception as e:
    logger.exception(f"Error inesperado en crear_cliente: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno del servidor al crear el cliente."
    )
```

**Cadena causal:**

1. `_validar_codigo_cliente` lanza `ConflictError` (subclase de `Exception`, no de `HTTPException`).
2. No coincide con `except HTTPException`.
3. Entra en `except Exception as e`.
4. `logger.exception(...)` registra el traceback — en logs aparece **`ConflictError`** con el mensaje de negocio (comportamiento observado en QA).
5. Se emite **`HTTP 500`** con mensaje genérico, **descartando** `exc.status_code` (409) y `exc.detail` específico.

**Transformación:** `ConflictError (409, detail específico)` → `HTTPException (500, "Error interno del servidor al crear el cliente.")`.

---

## 3. Clasificación HTTP recomendada por escenario

| Escenario | Excepción en servicio | `status_code` en clase | OpenAPI documentado en POST / | HTTP que debería salir |
|-----------|----------------------|------------------------|-------------------------------|-------------------------|
| Código de cliente duplicado | `ConflictError` (`CLIENT_CODE_CONFLICT`) | 409 | 409 (línea 59) | **409** |
| Subdominio duplicado | `ConflictError` (`SUBDOMAIN_CONFLICT`) | 409 | 409 | **409** |
| Campo obligatorio / formato subdominio | `ValidationError` | 400 | 422* | **400** (o 422 si es validación Pydantic previa) |
| Error inesperado real | `Exception` genérica / `ServiceError` 500 | 500 | 500 | **500** |

\* El docstring del endpoint menciona 422 para validación de entrada; `ValidationError` del dominio usa **400** en `exceptions.py`. Es una inconsistencia menor de documentación vs dominio, distinta del bug 500/409.

**`BusinessRuleError`:** no existe en el repositorio. Reglas de negocio usan `ValidationError`, `ConflictError`, `NotFoundError` o `ServiceError(status_code=...)`.

---

## 4. Comparación con el estándar del backend

### 4.1 Patrón recomendado (referencia ORG)

**`app/modules/org/presentation/endpoints_empresa.py` — `crear_empresa`:**

```python
from app.core.exceptions import ConflictError, CustomException, NotFoundError

try:
    return await empresa_service.create_empresa_servicio(...)
except (ConflictError, CustomException) as e:
    raise HTTPException(status_code=e.status_code, detail=e.detail) from e
```

Equivalente: propagar `e.status_code` y `e.detail` al cliente.

### 4.2 Otros patrones observados

| Módulo | Patrón | `ConflictError` → HTTP |
|--------|--------|-------------------------|
| ORG (`endpoints_empresa`, departamentos, etc.) | `except (NotFoundError, ConflictError, CustomException)` → `HTTPException(e.status_code, e.detail)` | Correcto |
| MNT (`endpoints_orden_trabajo`) | `except ConflictError` → `HTTPException(409, str(e))` | Correcto (usa `str(e)` en lugar de `e.detail`) |
| Superadmin catálogos | `except CustomException` → `HTTPException(ce.status_code, ce.detail)` | Correcto |
| **Tenant clientes** | `except Exception` → **500 genérico** | **Incorrecto** |
| Tenant branding (parcial) | `except ValidationError` / `NotFoundError` mapeados; resto → 500 | Parcial |

### 4.3 Inconsistencia documentación vs implementación

El OpenAPI inline de `POST /clientes/` declara explícitamente **409** para conflicto de subdominio/código, pero la implementación del `except Exception` hace imposible devolver 409 para `ConflictError`.

---

## 5. Otros endpoints afectados por el mismo patrón

### 5.1 `endpoints_clientes.py` (todos usan `except Exception` → 500)

| Endpoint | Método servicio | Excepciones de negocio posibles tragadas |
|----------|-----------------|------------------------------------------|
| `POST /` | `crear_cliente` | `ConflictError`, `ValidationError` |
| `GET /` | `listar_clientes` | Varias |
| `GET /{cliente_id}/` | `obtener_cliente_por_id` | — (404 manual en endpoint) |
| `PUT /{cliente_id}/` | `actualizar_cliente` | **`ConflictError`**, `NotFoundError`, `ValidationError` |
| `DELETE /{cliente_id}/` | `eliminar_cliente` | `NotFoundError`, `ValidationError` |
| `PUT /{cliente_id}/suspender/` | `suspender_cliente` | `NotFoundError`, `ValidationError` |
| `PUT /{cliente_id}/activar/` | `activar_cliente` | `NotFoundError`, `ValidationError` |
| `GET /{cliente_id}/estadisticas/` | `obtener_estadisticas` | `NotFoundError` |
| `GET /branding` | `get_branding_by_subdomain` | Parcial: mapea `ValidationError`/`NotFoundError`; **no** `ConflictError` |
| `GET /tenant/branding` | `get_branding_by_cliente` | `NotFoundError` vía `Exception` genérico |

**Caso crítico adicional:** `PUT /clientes/{id}/` con `codigo_cliente` o `subdominio` duplicado — el servicio lanza `ConflictError` (líneas 314–337 de `cliente_service.py`), pero el endpoint aplica el mismo `except Exception` → **500**.

### 5.2 `endpoints_conexiones.py`

Seis bloques `except Exception` → 500 (crear/actualizar conexión, listados, test). Mismo anti-patrón; fuera del alcance estricto de creación de cliente, pero mismo módulo tenant.

---

## 6. Diagrama de flujo (excepción)

```
_validar_codigo_cliente()
        │
        ▼
  ConflictError (status_code=409)
        │
        ▼
@handle_service_errors  ──►  re-raise ConflictError
        │
        ▼
crear_cliente() endpoint
        │
        ├─ except HTTPException → (no aplica)
        │
        └─ except Exception ──► logger.exception(ConflictError...)
                              └── HTTPException 500  ◄── BUG
                              
  (ruta no tomada) CustomException handler global → 409 JSON  ◄── CORRECTO pero bloqueado
```

---

## 7. Evidencia alineada con el caso QA

| Observación QA | Explicación en código |
|----------------|----------------------|
| Log: `ConflictError: El código de cliente 'CLI003' ya está en uso.` | Generado en `_validar_codigo_cliente` línea 95–97 |
| Log nivel exception / traceback | `logger.exception` en endpoint línea 87 — trata el conflicto como "error inesperado" |
| Cliente recibe 500 | `HTTPException(status_code=500, detail="Error interno del servidor...")` línea 88–91 |
| Negocio detectado correctamente | Sí, en servicio; falla solo la capa HTTP del endpoint |

---

## 8. Recomendaciones (solo diseño — sin implementar)

1. **Corrección mínima alineada a ORG:** en `crear_cliente` (y `actualizar_cliente`), capturar `CustomException` o tupla `(ValidationError, NotFoundError, ConflictError, ...)` y mapear `HTTPException(status_code=e.status_code, detail=e.detail)`.
2. **Alternativa arquitectónica:** eliminar `except Exception` en endpoints que delegan en servicios con excepciones tipadas, y dejar que el **handler global** de `CustomException` responda (como en el análisis de login documentado en `LOGIN_NO_ROLES_500_ROOT_CAUSE_AUDIT.md`).
3. **No usar `except Exception` para errores de negocio esperados** — reservarlo solo si se re-loguea y re-lanza, o para envoltorio final tras agotar tipos conocidos.
4. **Prueba de regresión sugerida:** POST `/clientes/` con `codigo_cliente` existente → assert **409**, body `detail` contiene mensaje de negocio, `error_code` = `CLIENT_CODE_CONFLICT` (si se usa handler global) o equivalente vía `HTTPException`.

---

## 9. Archivos revisados

| Archivo | Rol en la auditoría |
|---------|---------------------|
| `app/modules/tenant/presentation/endpoints_clientes.py` | Endpoint POST — causa del 500 |
| `app/modules/tenant/application/services/cliente_service.py` | `crear_cliente`, `_validar_codigo_cliente` |
| `app/core/exceptions.py` | Definición `ConflictError`, handler global |
| `app/core/application/base_service.py` | `handle_service_errors` — preserva `ConflictError` |
| `app/main.py` | Registro `configure_exception_handlers` |
| `app/api/v1/api.py` | Montaje `/clientes` |
| `app/modules/org/presentation/endpoints_empresa.py` | Patrón de referencia correcto |

---

## 10. Conclusión

La causa exacta del HTTP 500 ante un código de cliente duplicado **no** es un fallo en la validación de negocio ni en la definición de `ConflictError` (409). Es un **anti-patrón en el endpoint** `crear_cliente`: el bloque `except Exception` intercepta `ConflictError` y la sustituye por una respuesta 500 genérica, anulando el handler global y contradiciendo la documentación OpenAPI del propio endpoint.

La corrección es acotada a la capa de presentación (mapeo explícito o delegación al handler global), sin cambios en FK, BD ni reglas de unicidad del servicio.
