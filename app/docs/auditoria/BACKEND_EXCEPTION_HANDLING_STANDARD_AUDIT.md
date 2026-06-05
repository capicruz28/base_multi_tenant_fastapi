# Auditoría: consistencia de manejo de excepciones — capa Presentation

**Fecha:** 2026-06-02  
**Contexto:** hallazgo en `POST /clientes/` (`ConflictError` → HTTP 500) documentado en `CLIENTES_EXCEPTION_MAPPING_AUDIT.md`  
**Alcance:** `app/modules/**/presentation/**` (endpoints FastAPI)  
**Modo:** solo lectura — sin implementación

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---------|-------|
| Archivos `presentation` con `except Exception` | **16** |
| Bloques `except Exception` (total) | **108** |
| Módulos con endpoints y **sin** `except Exception` en presentation | **28** (referencia sana) |
| Handler global `CustomException` registrado | **Sí** (`app/main.py` → `configure_exception_handlers`) |

**Hallazgo central:** el handler global responde correctamente (`status_code` + `error_code` de cada `CustomException`), pero **decenas de endpoints lo anulan** con `except Exception` + `HTTPException(500)`, impidiendo que `ConflictError`, `ValidationError`, `NotFoundError`, etc. lleguen al cliente con su código HTTP real.

**Módulo más grave:** `tenant` — **ningún** archivo de presentation importa ni captura `CustomException`.

---

## 2. Infraestructura existente (correcta)

### 2.1 Jerarquía de excepciones (`app/core/exceptions.py`)

| Clase | HTTP por defecto | Uso típico |
|-------|------------------|------------|
| `ValidationError` | 400 | Entrada / regla de formato |
| `NotFoundError` | 404 | Recurso inexistente |
| `ConflictError` | 409 | Duplicados / unicidad |
| `AuthorizationError` | 403 | Permisos |
| `AuthenticationError` | 401 | Credenciales / token |
| `SecurityError` | 403 | Queries inseguras |
| `ServiceError` | configurable | Fallo de servicio |
| `DatabaseError` | 500 | Errores de BD |

No existe `BusinessRuleError` en el repositorio.

### 2.2 Handler global

```python
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.internal_code}
    )
```

**Condición para que actúe:** la excepción debe **propagar sin ser capturada** en el endpoint (o re-lanzarse explícitamente, p. ej. `raise` sin convertir a 500).

### 2.3 Servicios (`BaseService.handle_service_errors`)

Re-lanza `ValidationError`, `NotFoundError`, `ConflictError`, `ServiceError` sin alterar `status_code`. El problema **no** está en la capa de aplicación en el caso tenant/clientes.

---

## 3. Patrones observados en Presentation

| Patrón | Descripción | ¿`CustomException` llega al cliente? |
|--------|-------------|--------------------------------------|
| **A — Anti-patrón** | `except HTTPException: raise` + `except Exception` → 500 genérico. Sin `CustomException`. | **No** → siempre 500 |
| **B — Dual (parcialmente correcto)** | `except CustomException as ce` → `HTTPException(ce.status_code, ce.detail)` + `except Exception` → 500 | **Sí** para subclases de `CustomException` |
| **C — Re-raise** | `except CustomException: raise` (delega al handler global) | **Sí** (+ `error_code` en JSON) |
| **D — Mapeo explícito por tipo** | `except ConflictError`, `except NotFoundError`, etc. | **Sí** |
| **E — Sin try/except de ruta** | Confía en handler global | **Sí** |
| **F — Solo HTTPException** | `except CustomException` → `HTTPException` (superadmin catálogos) | **Sí** (sin `error_code` en body salvo que se copie) |

**Referencia sana (ERP):** ORG, INV, SLS, MNT, catálogos tenant — Patrones D/E.  
**Referencia admin/plataforma con anti-patrón:** tenant completo.

---

## 4. Inventario completo de archivos afectados

### 4.1 Crítico — sin captura de `CustomException` (reglas de negocio → 500)

#### Módulo `tenant`

| Archivo | Bloques `except Exception` | Rutas / handlers |
|---------|---------------------------|-------------------|
| `endpoints_clientes.py` | 10 | Ver tabla 4.1.1 |
| `endpoints_conexiones.py` | 6 | Ver tabla 4.1.2 |

**Servicios tenant que lanzan excepciones de negocio tragadas:**

- `ClienteService`: `ConflictError`, `ValidationError`, `NotFoundError`
- `ConexionService`: `ConflictError`, `ValidationError`, `NotFoundError`

##### 4.1.1 `endpoints_clientes.py` (prefijo API: `/clientes`)

| # | Método | Ruta | Handler | Excepciones de negocio típicas tragadas |
|---|--------|------|---------|--------------------------------------|
| 1 | POST | `/` | `crear_cliente` | **`ConflictError`** (código/subdominio), `ValidationError` |
| 2 | GET | `/` | `listar_clientes` | Varias |
| 3 | GET | `/{cliente_id}/` | `obtener_cliente` | — (404 manual en endpoint) |
| 4 | PUT | `/{cliente_id}/` | `actualizar_cliente` | **`ConflictError`**, `NotFoundError`, `ValidationError` |
| 5 | DELETE | `/{cliente_id}/` | `eliminar_cliente` | `NotFoundError`, `ValidationError` |
| 6 | PUT | `/{cliente_id}/suspender/` | `suspender_cliente` | `NotFoundError`, `ValidationError` |
| 7 | PUT | `/{cliente_id}/activar/` | `activar_cliente` | `NotFoundError`, `ValidationError` |
| 8 | GET | `/{cliente_id}/estadisticas/` | `obtener_estadisticas_cliente` | `NotFoundError` |
| 9 | GET | `/branding` | `obtener_branding_por_subdominio` | Parcial: mapea `ValidationError`/`NotFoundError`; **resto** → 500 |
| 10 | GET | `/tenant/branding` | `obtener_branding_tenant` | `NotFoundError` vía `Exception` genérico |

*Endpoints `debug/*` sin `except Exception` en handler — fuera del problema.*

**Caso QA origen:** fila #1 (`POST /` / `crear_cliente`).

##### 4.1.2 `endpoints_conexiones.py` (prefijo API: `/conexiones`)

| # | Método | Ruta (resumen) | Handler | Excepciones tragadas |
|---|--------|----------------|---------|---------------------|
| 1 | GET | `/clientes/{cliente_id}` | listar conexiones | Varias |
| 2 | GET | `/clientes/{cliente_id}/principal` | conexión principal | Varias |
| 3 | POST | (crear conexión) | `crear_conexion` | **`ConflictError`**, `ValidationError` |
| 4 | PUT | `/{conexion_id}` | actualizar | `NotFoundError`, etc. |
| 5 | DELETE | `/{conexion_id}` | desactivar | `NotFoundError`, etc. |
| 6 | POST | `/test` | test conexión | Varias |

---

#### Módulo `auth` (subconjunto crítico)

| Archivo | Bloques | Rutas (resumen) |
|---------|---------|-----------------|
| `endpoints_auth_config.py` | 3 | `GET/PUT /auth-config/clientes/{id}`, `GET /auth-config/global` |
| `endpoints_sso.py` | 4 | Flujos SSO (todos con `except Exception` → 500, sin `CustomException`) |

---

### 4.2 Medio — patrón dual (`CustomException` capturado, pero `except Exception` redundante y riesgoso)

Capturan `CustomException` **antes** del `except Exception`, por lo que **hoy** las reglas de negocio suelen responder bien. Riesgo: regresiones si alguien elimina el bloque `CustomException` o lanza excepciones que no heredan de `CustomException`.

| Módulo | Archivo | Bloques `except Exception` | Bloques `CustomException` |
|--------|---------|---------------------------|---------------------------|
| **users** | `endpoints.py` | 8 | 8 (pares 1:1) |
| **rbac** | `endpoints.py` | 11 | 11 |
| **rbac** | `endpoints_permisos.py` | 4 | 4 |
| **rbac** | `endpoints_permisos_catalogo.py` | 1 | 1 |
| **menus** | `endpoints.py` | 8 | 8 |
| **menus** | `endpoints_areas.py` | 7 | 7 |
| **modulos** | `endpoints_modulos.py` | 6 | 6+ |
| **modulos** | `endpoints_cliente_modulo.py` | 2 | 8+ |
| **modulos** | `endpoints_menus.py` | 3 | 11+ |
| **superadmin** | `endpoints_usuarios.py` | 5 | 5 |
| **superadmin** | `endpoints_auditoria.py` | 4 | 4 |

**Nota:** `modulos/endpoints_plantillas.py` y `endpoints_secciones.py` usan **solo** `CustomException` (sin `except Exception`) — más alineados al estándar objetivo.

---

### 4.3 Medio-alto — módulo `auth` (`endpoints.py`)

| Bloques `except Exception` | ~26 (incluye anidados) |
| Comportamiento en `/login/` | `except CustomException: raise` → **correcto** (delega al global) |
| Otros handlers de ruta | Muchos solo `HTTPException` + `Exception` → 500 |

**Handlers de ruta con anti-patrón A (sin `CustomException` previo):**

| Handler (función) | Riesgo |
|-------------------|--------|
| `seleccionar_empresa_post_login` | `CustomException` del servicio → 500 |
| `cambiar_empresa_sesion` | idem |
| `iniciar_impersonacion` | idem |
| `finalizar_impersonacion` | idem |
| `get_me` / `read_users_me` | idem |
| `get_permissions_me` | idem |
| `get_menu_me` | idem |
| `refresh_token` (handler principal) | Parcial: `AuthenticationError` mapeado; resto → 500 |
| `logout` | fail-soft en perform_logout (intencional) |
| `get_sessions` / `logout_all_sessions` / `get_all_sessions_admin` | idem |

---

### 4.4 Bajo — `except Exception` no bloquea reglas de negocio del response

| Ubicación | Motivo |
|-----------|--------|
| `auth/endpoints.py` — bloques internos de auditoría (`login_failed`, `login_success`, `token_refresh`, `logout_forced`) | Fail-soft; no alteran status HTTP del endpoint |
| `auth/endpoints.py` — revocación token en refresh (`revoke_err`) | Warning no crítico |
| `modulos/endpoints_menus.py` — un `except Exception` interno | Contexto acotado |
| `auth` — `lookup_db` en `/me` | Detección de contexto; no es handler de ruta |

---

### 4.5 Módulos sin `except Exception` en Presentation (referencia — 28 módulos)

Estos módulos **no** presentan el anti-patrón A en archivos `presentation/endpoints*.py` analizados:

`aud`, `bdg`, `bi`, `catalogos`, `crm`, `cst`, `dms`, `fin`, `hcm`, `inv`, `invbill`, `log`, `mfg`, `mnt`, `mps`, `mrp`, `org`, `pm`, `pos`, `prc`, `pur`, `qms`, `sls`, `svc`, `tax`, `tkt`, `wfl`, `wms`

**Subpatrones dentro de estos módulos:**

| Subpatrón | Ejemplo | Evaluación |
|-----------|---------|------------|
| Sin try en ruta | Muchos endpoints INV/SLS | Handler global atiende `CustomException` |
| Mapeo explícito | `org/endpoints_empresa.py`, `inv/endpoints_productos.py` | Correcto |
| Solo `CustomException` → `HTTPException` | `superadmin/endpoints_catalogos_globales.py` | Correcto (pierde `error_code` en JSON a menos que se añada) |
| `CustomException` + tipos concretos | `org/endpoints_departamentos.py` | Correcto |

---

## 5. Clasificación por severidad (resumen)

| Severidad | Criterio | Módulos / alcance | Endpoints aprox. |
|-----------|----------|-------------------|------------------|
| **Crítico** | `except Exception` → 500 **sin** manejo previo de `CustomException` | `tenant` (clientes + conexiones), `auth` (auth_config, sso) | **~19 rutas** administración plataforma |
| **Medio** | Dual: funciona hoy, pero duplica lógica y oculta el handler global | `users`, `rbac`, `menus`, `modulos`, `superadmin` (usuarios, auditoría) | **~50 handlers** |
| **Medio-alto** | `auth/endpoints.py` — mezcla re-raise correcto en login con 500 en otros flujos | `auth` | **~10+ handlers** de sesión/RBAC |
| **Bajo** | `except Exception` solo en auditoría / fail-soft interno | `auth` (anidados) | N/A |

---

## 6. Por qué `ConflictError` termina en 500 (cadena causal genérica)

```
Servicio lanza ConflictError (status_code=409)
        ↓
@handle_service_errors → re-raise
        ↓
Endpoint Patrón A:
  except HTTPException: raise     # no aplica
  except Exception:               # captura ConflictError
      logger.exception(...)       # log correcto, status incorrecto
      raise HTTPException(500)    # degrada respuesta
        ↓
Handler global CustomException   # NUNCA se ejecuta
```

En Patrón B, la cadena se interrumpe en `except CustomException` → HTTP 409.

---

## 7. Comparación con estándar documentado del proyecto

`.cursorrules` indica:

- Mapear duplicados a excepción que responde **409**
- No dejar errores SQL al cliente como 500

Los servicios tenant **cumplen** la regla; la capa presentation de `tenant` **la viola** al convertir todo `Exception` en 500.

---

## 8. Clasificación HTTP recomendada (referencia única)

| Escenario | Excepción | HTTP |
|-----------|-----------|------|
| Código/subdominio duplicado | `ConflictError` | **409** |
| Cliente/recurso no existe | `NotFoundError` | **404** |
| Validación de negocio (dominio) | `ValidationError` | **400** |
| Sin permiso | `AuthorizationError` | **403** |
| Credenciales inválidas | `AuthenticationError` | **401** |
| Body inválido (Pydantic) | `RequestValidationError` | **422** (handler global) |
| Error realmente inesperado | `Exception` no tipada | **500** |

---

## 9. Decisión arquitectónica: ¿mapeo explícito o handler global?

### 9.1 Opción 1 — Delegar al handler global (recomendada como estándar primario)

**En endpoints de negocio:**

- Eliminar `try/except Exception` que envuelve la llamada al servicio.
- Opcional: `try/except HTTPException: raise` solo si el mismo handler lanza `HTTPException` directamente.
- Dejar propagar `CustomException` → handler en `exceptions.py`.

**Ventajas:**

- Un solo lugar para `error_code`, logging y formato JSON.
- Imposible “olvidar” mapear `ConflictError` en un endpoint nuevo.
- Menos código duplicado (~108 bloques eliminables a largo plazo).

**Desventajas:**

- Menos control local del mensaje HTTP en casos muy específicos (mitigable con subclases o `detail` en la excepción).

### 9.2 Opción 2 — Mapeo explícito en cada endpoint

```python
except CustomException as e:
    raise HTTPException(status_code=e.status_code, detail=e.detail) from e
```

**Ventajas:**

- Explícito en OpenAPI por archivo; familiar para el equipo.

**Desventajas:**

- Duplicación en 50+ handlers (ya existe en menus/rbac/users).
- Suele olvidarse `error_code` del handler global.
- Coexiste con `except Exception` → 500 y genera falsa sensación de “ya está manejado”.

### 9.3 Opción 3 — Híbrido pragmático (transición)

1. **Prohibir Patrón A** en módulos críticos (`tenant`, `auth_config`, `auth_sso`) — corrección inmediata.
2. **Nuevos endpoints:** sin `except Exception` en ruta; solo handler global.
3. **Módulos Patrón B:** mantener temporalmente; migrar a Opción 1 por módulo.
4. **Helper opcional** (si se desea explícito sin duplicar):

   ```python
   # Conceptual — no implementado
   def raise_http_from_domain(exc: CustomException): ...
   ```

### 9.4 Recomendación final

| Pregunta | Recomendación |
|----------|---------------|
| ¿Estandarizar mapeo explícito en todos los endpoints? | **No** como regla universal |
| ¿Delegar al handler global? | **Sí**, como estándar primario para `CustomException` |
| ¿Corrección puntual POST /clientes? | Aplicar estándar al **módulo `tenant` completo** (16 handlers), no solo un endpoint |
| ¿Superadmin catálogos? | Ya usa `CustomException` → `HTTPException`; opcional alinear a re-raise global para incluir `error_code` |

---

## 10. Propuesta arquitectónica única (evitar recurrencia)

### 10.1 Regla de presentación (normativa)

1. **Prohibido** en handlers de ruta:

   ```python
   except Exception as e:
       raise HTTPException(status_code=500, ...)
   ```

   salvo bloques **internos** documentados como fail-soft (auditoría, cleanup).

2. **Permitido** para endpoints que llaman servicios con `CustomException`:

   - Sin try/except, o
   - `except HTTPException: raise` + propagación natural.

3. **Servicios:** seguir usando `ValidationError`, `ConflictError`, `NotFoundError`, etc.; no lanzar `HTTPException` desde servicios.

4. **Respuesta JSON estándar** (handler global):

   ```json
   {"detail": "...", "error_code": "CLIENT_CODE_CONFLICT"}
   ```

### 10.2 Gobernanza en repo

| Mecanismo | Acción |
|-----------|--------|
| `.cursorrules` | Añadir regla: “Presentation no convierte CustomException en 500” |
| CI / pre-commit | Script grep: fallar si `except Exception` + `HTTP_500` en mismo handler sin `CustomException` previo |
| Plantilla de endpoint | Snippet sin try/except o con re-raise documentado |
| PR checklist | “¿El endpoint deja propagar CustomException?” |

### 10.3 Script de detección sugerido (concepto)

Buscar en `presentation/endpoints*.py`:

- Presencia de `except Exception`
- Ausencia de `CustomException` o `ConflictError` en los 30 líneas anteriores del mismo `async def`
- Presencia de `HTTP_500_INTERNAL_SERVER_ERROR`

Salida: lista de handlers “candidatos a Crítico” para CI.

### 10.4 Orden de remediación sugerido (cuando se implemente)

| Prioridad | Alcance | Motivo |
|-----------|---------|--------|
| P0 | `tenant/presentation/*` | Administración de clientes; bug confirmado en QA |
| P1 | `auth/presentation/endpoints_auth_config.py`, `endpoints_sso.py` | Misma plataforma admin |
| P2 | `auth/presentation/endpoints.py` (handlers de sesión sin re-raise) | Alto tráfico |
| P3 | Módulos Patrón B (users, rbac, menus, modulos, superadmin usuarios) | Funciona hoy; simplificar a handler global |

---

## 11. Relación con auditoría previa

| Documento | Relación |
|-----------|----------|
| `CLIENTES_EXCEPTION_MAPPING_AUDIT.md` | Caso puntual P0: `POST /clientes/` |
| Este documento | Alcance sistémico: **108** bloques, **16** archivos, clasificación y estándar |

La corrección de `POST /clientes/` sin abordar `PUT /clientes/{id}/` o `endpoints_conexiones.py` dejaría **inconsistencia residual** en el mismo módulo tenant.

---

## 12. Conclusión

1. **Causa sistémica:** no es un bug de `ConflictError`, sino un **anti-patrón de presentation** (`except Exception` → 500) que **bypasea** el handler global ya implementado y correcto.

2. **Alcance real:** concentrado en **plataforma/admin** (`tenant`, partes de `auth`) y redundante en **users/rbac/menus/modulos/superadmin**; módulos ERP (ORG, INV, SLS, …) están mayormente alineados.

3. **Estándar recomendado:** **delegar `CustomException` al handler global**; prohibir el Patrón A en rutas nuevas y en remediación P0.

4. **Para POST /clientes:** clasificación **Crítico**; la corrección mínima es parte de alinear **todo el módulo `tenant` presentation** (19 rutas), no un parche aislado.

---

## 13. Archivos analizados (lista)

```
app/modules/tenant/presentation/endpoints_clientes.py
app/modules/tenant/presentation/endpoints_conexiones.py
app/modules/auth/presentation/endpoints.py
app/modules/auth/presentation/endpoints_auth_config.py
app/modules/auth/presentation/endpoints_sso.py
app/modules/users/presentation/endpoints.py
app/modules/rbac/presentation/endpoints.py
app/modules/rbac/presentation/endpoints_permisos.py
app/modules/rbac/presentation/endpoints_permisos_catalogo.py
app/modules/menus/presentation/endpoints.py
app/modules/menus/presentation/endpoints_areas.py
app/modules/modulos/presentation/endpoints_modulos.py
app/modules/modulos/presentation/endpoints_cliente_modulo.py
app/modules/modulos/presentation/endpoints_menus.py
app/modules/superadmin/presentation/endpoints_usuarios.py
app/modules/superadmin/presentation/endpoints_auditoria.py
app/core/exceptions.py
app/core/application/base_service.py
app/main.py
```

Muestreo de referencia positiva: `org/presentation/endpoints_*.py`, `inv/presentation/endpoints_productos.py`, `superadmin/presentation/endpoints_catalogos_globales.py`.
