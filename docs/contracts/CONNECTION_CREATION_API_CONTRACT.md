# CONNECTION CREATION API CONTRACT

> ## ⚠ Legacy Flow for Dedicated (F4+)
>
> **Dedicated estándar (F4+):** el flujo oficial de alta de tenant Dedicated **no** usa este endpoint como happy path. Consultar **`docs/contracts/DEDICATED_PROVISIONING_API_CONTRACT.md`**: `POST /api/v1/clientes/` con `tipo_instalacion=dedicated` → saga S1–S10 → registro automático de `cliente_conexion` en **S8** → Tenant Ready en **S10**.
>
> **Este contrato permanece vigente para:**
> - **Shared:** registro opcional de `cliente_conexion` (sin cambio).
> - **Dedicated — escenarios manuales:** repair, migración, tenants legacy pre-F4, importación on-prem u operaciones SRE sin saga automática.
>
> **Prohibición de producto (post-F4):** el Frontend **no debe** invocar `POST /conexiones/` tras crear un cliente Dedicated nuevo en el flujo estándar de provisioning.

---

## Objetivo

Definir el contrato v1 para **crear manualmente** una conexión de base de datos (`cliente_conexion`) asociada a un tenant en la plataforma Hybrid.

Este documento describe el comportamiento **actual** del Backend (post-implementación Hybrid F0–F3) para la operación `POST /conexiones/`. No introduce cambios de comportamiento ni nuevas funcionalidades en el endpoint.

**Alcance:** únicamente la operación de **creación** (`POST`). Operaciones de listado, actualización, desactivación y test de conectividad quedan fuera de este contrato.

### Relación con otros contratos

| Escenario | Contrato canónico |
|-----------|-------------------|
| **Shared** — conexión opcional | **Este documento** |
| **Dedicated F4+** — happy path provisioning | `DEDICATED_PROVISIONING_API_CONTRACT.md` |
| **Dedicated** — manual / repair / legacy / on-prem | **Este documento** |

---

## Endpoint

| Atributo | Valor |
|----------|-------|
| **Método HTTP** | `POST` |
| **URL** | `/api/v1/conexiones/clientes/{cliente_id}/` |
| **URL completa (ejemplo)** | `https://{api-host}/api/v1/conexiones/clientes/a1b2c3d4-e5f6-7890-abcd-ef1234567890/` |
| **Content-Type** | `application/json` |
| **Status éxito** | `201 Created` |

### Autenticación requerida

| Requisito | Detalle |
|-----------|---------|
| **Esquema** | Bearer JWT (`Authorization: Bearer <access_token>`) |
| **Origen del token** | `POST /api/v1/auth/login/` (u otro flujo de autenticación vigente) |
| **Usuario** | Debe estar autenticado y activo |

### Permisos requeridos

Se aplican **dos capas** de autorización (ambas obligatorias):

| Capa | Requisito |
|------|-----------|
| **RBAC** | Permiso `tenant.conexion.crear` |
| **LBAC** | Super Administrador (nivel de acceso ≥ 5, rol `SuperAdministrador` y/o `is_super_admin=true`) |

### Parámetro de ruta

| Nombre | Tipo | Obligatorio | Descripción |
|--------|------|-------------|-------------|
| `cliente_id` | `UUID` (string) | Sí | Identificador del tenant al que se asocia la conexión |

> **Nota de implementación (auditoría):** el Backend recibe `cliente_id` en la ruta **y** en el body (`ConexionCreate.cliente_id`). El servicio persiste el valor del **body**, no valida que coincida con el de la ruta. El Frontend **debe enviar el mismo UUID en ambos lugares**.

---

## Request

Cuerpo JSON conforme al schema `ConexionCreate`.

### Tabla de campos

| nombre | tipo | obligatorio | nullable | valor por defecto | descripción | validaciones |
|--------|------|-------------|----------|-------------------|-------------|--------------|
| `cliente_id` | `string` (UUID v4) | **Sí** | No | — | ID del cliente propietario de la conexión | Formato UUID válido |
| `servidor` | `string` | **Sí** | No | — | Hostname o IP del servidor de BD | No vacío; max 255 chars; hostname, IPv4 o IPv6 válido (regex Pydantic) |
| `puerto` | `integer` | No | No | `1433` | Puerto TCP del motor de BD | Rango 1–65535 |
| `nombre_bd` | `string` | **Sí** | No | — | Nombre de la base de datos destino | No vacío; max 100 chars; patrón `^[a-zA-Z0-9_][a-zA-Z0-9_\-\.]*$`; se aplica `strip()` |
| `tipo_bd` | `string` | No | No | `"sqlserver"` | Motor de base de datos | Whitelist: `sqlserver`, `postgresql`, `mysql`, `oracle` |
| `usa_ssl` | `boolean` | No | No | `false` | Indica uso de SSL/TLS en la conexión | — |
| `timeout_segundos` | `integer` | No | No | `30` | Timeout de conexión en segundos | Rango 5–300 |
| `max_pool_size` | `integer` | No | No | `100` | Tamaño máximo del pool de conexiones | Rango 1–1000 |
| `es_solo_lectura` | `boolean` | No | No | `false` | Marca la conexión como solo lectura | — |
| `es_conexion_principal` | `boolean` | No | No | `false` | Marca como conexión principal del tenant | Ver reglas de negocio; validación de unicidad en servicio |
| `usuario` | `string` | **Sí** | No | — | Usuario de BD en texto plano (se cifra al persistir) | Sin validación de longitud en schema |
| `password` | `string` | **Sí** | No | — | Contraseña de BD en texto plano (se cifra al persistir) | Sin validación de longitud en schema |

### Campos que el Frontend NO envía (generados por Backend)

| Campo | Origen |
|-------|--------|
| `conexion_id` | Generado por BD (`NEWID()`) |
| `es_activo` | Forzado a `true` (`1`) en inserción |
| `creado_por_usuario_id` | `current_user.usuario_id` del JWT |
| `connection_string_encriptado` | `null` en creación (no se genera en este flujo) |
| `fecha_creacion` | `GETDATE()` en BD |
| `fecha_actualizacion` | `null` en creación |
| `ultima_conexion_exitosa` | `null` en creación |
| `ultimo_error` | `null` en creación |
| `fecha_ultimo_error` | `null` en creación |

---

## Campos exclusivos Shared

**No existen campos de request exclusivos para tenants Shared** en el contrato de creación.

La modalidad Shared se determina por `cliente.tipo_instalacion = "shared"` (configurado al crear el cliente, no en este endpoint).

### Comportamiento operativo Shared (post-creación)

| Aspecto | Comportamiento |
|---------|----------------|
| **Routing Hybrid** | `database_type = "single"` → datos ERP en BD central compartida |
| **Conexión en `cliente_conexion`** | Opcional; no es requisito para operar el tenant Shared |
| **`es_conexion_principal`** | Típicamente `false`; el gateway no depende de esta fila para enrutar |
| **`servidor` / `nombre_bd`** | Pueden registrarse, pero el routing Shared no los usa para resolver el engine tenant |

---

## Campos exclusivos Dedicated — Legacy / Manual / Repair

> **API:** no existen campos de request exclusivos para tenants Dedicated; el mismo schema `ConexionCreate` aplica a Shared y Dedicated.

**Flujo de producto:** para Dedicated **nuevo** post-F4, el Frontend **no debe** usar este endpoint en el happy path — ver banner **Legacy Flow for Dedicated** y `DEDICATED_PROVISIONING_API_CONTRACT.md`.

La modalidad Dedicated se determina por `cliente.tipo_instalacion = "dedicated"` (configurado al crear el cliente).

### Comportamiento operativo Dedicated (solo escenarios manuales)

Aplica cuando el tenant Dedicated **ya existe** y la BD dedicada **ya fue provisionada** fuera del flujo automático F4 (legacy pre-F4, repair SRE, migración puntual u on-prem futuro).

| Aspecto | Requisito |
|---------|-----------|
| **Prerequisito** | BD física dedicada ya creada y migrada (fuera de este endpoint) |
| **`es_conexion_principal`** | **Debe ser `true`** para que el Hybrid Gateway resuelva metadata (filtro `es_conexion_principal = 1 AND es_activo = 1`) |
| **`servidor`** | Obligatorio y debe ser alcanzable desde el Backend |
| **`nombre_bd`** | Debe coincidir con la BD dedicada provisionada |
| **`usuario` / `password`** | Credenciales válidas de la BD dedicada |
| **Routing Hybrid** | `database_type = "multi"` → engine `tenant_{cliente_id}` |

> El Backend **no valida** en `crear_conexion` que el cliente sea Dedicated ni que `es_conexion_principal` sea `true`. Son reglas operativas que el operador/Frontend debe aplicar en escenarios manuales según el `tipo_instalacion` del cliente.

---

## Response Success

**HTTP 201** — Body: objeto `ConexionRead`.

### Ejemplo JSON

```json
{
  "conexion_id": "b8c9d0e1-f2a3-4567-1234-678901234567",
  "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "servidor": "sql-dedicated-01.database.windows.net",
  "puerto": 1433,
  "nombre_bd": "erp_acme_dedicated",
  "tipo_bd": "sqlserver",
  "usa_ssl": true,
  "timeout_segundos": 30,
  "max_pool_size": 100,
  "es_solo_lectura": false,
  "es_conexion_principal": true,
  "usuario_encriptado": "gAAAAABl...",
  "password_encriptado": "gAAAAABl...",
  "connection_string_encriptado": null,
  "es_activo": true,
  "ultima_conexion_exitosa": null,
  "ultimo_error": null,
  "fecha_ultimo_error": null,
  "fecha_creacion": "2026-06-25T20:00:00",
  "fecha_actualizacion": null,
  "creado_por_usuario_id": "f6a7b8c9-d0e1-2345-f012-456789012345"
}
```

### Campos de respuesta

| Campo | Tipo | Siempre presente | Nullable | Notas Frontend |
|-------|------|------------------|----------|----------------|
| `conexion_id` | UUID | Sí | No | Identificador de la conexión creada |
| `cliente_id` | UUID | Sí | No | Debe coincidir con el tenant |
| `servidor` | string | Sí | No | — |
| `puerto` | integer | Sí | No | — |
| `nombre_bd` | string | Sí | No | — |
| `tipo_bd` | string | Sí | No | — |
| `usa_ssl` | boolean | Sí | No | — |
| `timeout_segundos` | integer | Sí | No | — |
| `max_pool_size` | integer | Sí | No | — |
| `es_solo_lectura` | boolean | Sí | No | — |
| `es_conexion_principal` | boolean | Sí | No | — |
| `usuario_encriptado` | string | Sí | No | **No mostrar en UI** — valor cifrado |
| `password_encriptado` | string | Sí | No | **No mostrar en UI** — valor cifrado |
| `connection_string_encriptado` | string | Sí | Sí (`null` en creación) | No mostrar en UI |
| `es_activo` | Sí | Sí | No | Siempre `true` al crear |
| `ultima_conexion_exitosa` | datetime | Sí | Sí | `null` en creación |
| `ultimo_error` | string | Sí | Sí | `null` en creación |
| `fecha_ultimo_error` | datetime | Sí | Sí | `null` en creación |
| `fecha_creacion` | datetime | Sí | No | — |
| `fecha_actualizacion` | datetime | Sí | Sí | `null` en creación |
| `creado_por_usuario_id` | UUID | Sí | Sí | Usuario autenticado que creó el registro |

---

## Response Error

### Formato de error

Existen **dos formatos** según el origen de la excepción:

**Formato A — `CustomException` y validación Pydantic (handler global):**

```json
{
  "detail": "<mensaje legible>",
  "error_code": "<CODIGO_INTERNO>"
}
```

**Formato B — `HTTPException` (auth/LBAC sin handler custom):**

```json
{
  "detail": "<mensaje legible>"
}
```

> El Frontend debe leer siempre `detail` (string o array de strings en 422). Usar `error_code` cuando esté presente.

### Códigos HTTP posibles

| código | mensaje (ejemplo) | causa | `error_code` (si aplica) |
|--------|-------------------|-------|--------------------------|
| **401** | `"No se pudieron validar las credenciales"` | Token ausente, inválido o expirado | — (Formato B) |
| **403** | `"Se requiere rol de Super Administrador para esta operación"` | Usuario autenticado sin nivel Super Admin | — (Formato B) |
| **403** | `"No tiene permisos suficientes para realizar esta acción. Se requiere: tenant.conexion.crear"` | Usuario sin permiso RBAC | — (Formato B; `internal_code` existe en código pero no se serializa) |
| **403** | `"Usuario inactivo"` | Cuenta desactivada | — (Formato B) |
| **409** | `"Ya existe una conexión principal activa para este cliente."` | `es_conexion_principal=true` y ya existe otra principal activa para el mismo `cliente_id` | `PRIMARY_CONNECTION_CONFLICT` |
| **422** | `"body.servidor: Format error..."` o mensaje de validación Pydantic | Campos inválidos según schema (`tipo_bd`, `puerto`, `servidor`, etc.) | `VALIDATION_ERROR` |
| **422** | `"El parámetro 'path.cliente_id' no es un UUID válido..."` | `cliente_id` de ruta malformado | `VALIDATION_ERROR` |
| **500** | `"Error interno del servidor"` | Fallo inesperado en servicio (`INTERNAL_SERVICE_ERROR`) | `INTERNAL_SERVICE_ERROR` |
| **500** | `"Error interno del servidor"` | Fallo al cifrar credenciales | `CREDENTIALS_ENCRYPTION_FAILED` |
| **500** | `"Error interno del servidor"` | INSERT sin filas retornadas | `CONNECTION_CREATION_FAILED` |
| **500** | `"Error interno del servidor"` | Violación FK (`cliente_id` inexistente), violación UNIQUE de BD, u otro error SQL | `DB_INSERT_ERROR` |

> En producción, respuestas **5xx** ocultan el detalle interno y devuelven siempre `"Error interno del servidor"` en `detail`, conservando `error_code`.

---

## Flujo Backend

```
Cliente (Frontend)
    │
    │  POST /api/v1/conexiones/clientes/{cliente_id}/
    │  Authorization: Bearer <JWT>
    │  Body: ConexionCreate
    ▼
API — endpoints_conexiones.crear_conexion
    │
    ├─► Depends(require_permission("tenant.conexion.crear"))  → 403 si falla RBAC
    ├─► @require_super_admin()                                → 403 si no es Super Admin
    ├─► get_current_active_user                              → 401 si token inválido
    ▼
Validaciones
    │
    ├─► Pydantic ConexionCreate (hostname, puerto, tipo_bd, timeout, pool, nombre_bd)
    ├─► Si es_conexion_principal=true → ConexionService._validar_conexion_unica()
    │       └─► ConflictError 409 si ya existe principal activa
    ▼
Persistencia — ConexionService.crear_conexion
    │
    ├─► encrypt_credential(usuario) + encrypt_credential(password)
    ├─► INSERT INTO cliente_conexion (BD ADMIN / central)
    │       es_activo=1, connection_string_encriptado=NULL, creado_por_usuario_id=<JWT>
    └─► OUTPUT → ConexionRead
    ▼
Metadata Hybrid (efecto diferido — no ejecutado en el POST)
    │
    ├─► La metadata de routing (routing.py) se resuelve en requests ERP posteriores
    ├─► Lee cliente_conexion WHERE es_conexion_principal=1 AND es_activo=1
    ├─► Cruza con cliente.tipo_instalacion → database_type single|multi
    └─► Cache L1 (connection_cache, TTL 300s) — no se invalida automáticamente al crear
    ▼
Gateway — queries_async / connection_async (requests subsiguientes)
    │
    ├─► Shared  → DatabaseConnection.DEFAULT (BD central)
    └─► Dedicated → engine tenant_{cliente_id} con credenciales desencriptadas
    ▼
Resultado
    │
    └─► HTTP 201 + ConexionRead al Frontend
```

---

## Reglas de negocio

| # | Regla | Capa | Enforced |
|---|-------|------|----------|
| R1 | Solo Super Admin con permiso `tenant.conexion.crear` puede crear conexiones | Router | Sí |
| R2 | Credenciales (`usuario`, `password`) se cifran antes de persistir (`ENCRYPTION_KEY`) | Service | Sí |
| R3 | `es_activo` se fuerza a `true` en creación (no es input del cliente) | Service | Sí |
| R4 | Máximo **una** conexión principal **activa** por `cliente_id` | Service (+ constraint BD) | Sí (409 en servicio) |
| R5 | Constraint BD `UQ_conexion_principal_cliente UNIQUE (cliente_id, es_conexion_principal)` limita combinaciones por valor de `es_conexion_principal` | BD | Sí (error 500 si se viola sin pre-check) |
| R6 | `connection_string_encriptado` queda `null` en creación; no hay test de conectividad en este flujo | Service | Sí (comportamiento actual) |
| R7 | `cliente_id` debe existir en tabla `cliente` (FK) | BD | Sí (500 si no existe; sin pre-validación) |
| R8 | Dedicated: routing Hybrid requiere fila con `es_conexion_principal=true` y credenciales válidas | Routing (post-creación) | No en POST |
| R9 | Shared: routing usa BD central; registro en `cliente_conexion` es opcional | Routing | N/A |
| R10 | `cliente_id` en ruta y body deben coincidir | — | **No enforced** (responsabilidad Frontend) |
| R11 | Cache de metadata Hybrid no se invalida tras creación | Cache | Comportamiento actual (TTL 300s) |

---

## Ejemplos

### Ejemplo completo Shared

Tenant con `tipo_instalacion: "shared"` ya creado. La conexión es **opcional** (registro informativo o futuro uso).

**Request:**

```http
POST /api/v1/conexiones/clientes/a1b2c3d4-e5f6-7890-abcd-ef1234567890/ HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "cliente_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "servidor": "sql-central.database.windows.net",
  "puerto": 1433,
  "nombre_bd": "bd_hybrid_sistema_central",
  "tipo_bd": "sqlserver",
  "usa_ssl": true,
  "timeout_segundos": 30,
  "max_pool_size": 50,
  "es_solo_lectura": false,
  "es_conexion_principal": false,
  "usuario": "app_shared_user",
  "password": "Str0ngP@ssw0rd!"
}
```

**Response 201:** (ver sección Response Success)

### Ejemplo Dedicated — legacy / manual / repair

> **No es el happy path F4+.** Para Dedicated nuevo usar `DEDICATED_PROVISIONING_API_CONTRACT.md`. Este ejemplo aplica a tenant `tipo_instalacion: "dedicated"` ya creado con BD dedicada provisionada **manualmente** (pre-F4, repair o migración).

**Request:**

```http
POST /api/v1/conexiones/clientes/d1e2f3a4-b5c6-7890-def1-234567890abc/ HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "cliente_id": "d1e2f3a4-b5c6-7890-def1-234567890abc",
  "servidor": "sql-dedicated-01.database.windows.net",
  "puerto": 1433,
  "nombre_bd": "erp_acme_dedicated",
  "tipo_bd": "sqlserver",
  "usa_ssl": true,
  "timeout_segundos": 30,
  "max_pool_size": 100,
  "es_solo_lectura": false,
  "es_conexion_principal": true,
  "usuario": "erp_dedicated_user",
  "password": "D3d1c@t3d_S3cur3!"
}
```

**Response 201:** `es_conexion_principal: true` — requerido para que el Hybrid Gateway enrute a la BD dedicada en requests posteriores.

---

## OpenAPI

| Aspecto | Estado |
|---------|--------|
| **Ruta documentada** | `POST /api/v1/conexiones/clientes/{cliente_id}/` |
| **operationId** | `crear_conexion_api_v1_conexiones_clientes__cliente_id___post` |
| **Request schema** | `ConexionCreate` — alineado con Pydantic |
| **Response 201 schema** | `ConexionRead` — alineado con Pydantic |
| **Security** | `OAuth2PasswordBearer` (Bearer JWT) |
| **Required fields** | `cliente_id`, `servidor`, `nombre_bd`, `usuario`, `password` |
| **Defaults** | `puerto=1433`, `tipo_bd=sqlserver`, `usa_ssl=false`, `timeout_segundos=30`, `max_pool_size=100`, `es_solo_lectura=false`, `es_conexion_principal=false` |

### Desalineaciones OpenAPI ↔ Backend (reporte auditoría)

| # | Hallazgo | Severidad |
|---|----------|-----------|
| O1 | OpenAPI solo declara respuestas `201` y `422`; el router documenta además `403`, `409` y `500` | Media |
| O2 | Errores `403`/`401` vía `HTTPException` no incluyen `error_code` en JSON; OpenAPI no documenta el formato dual | Media |
| O3 | Parámetro de ruta `cliente_id` no se refleja como restricción cruzada con `body.cliente_id` | Baja |
| O4 | No hay distinción OpenAPI Shared/Dedicated (correcto: mismo schema; reglas son operativas) | Info |

**Conclusión:** el schema de request/response en OpenAPI está **alineado** con los modelos Pydantic. La documentación de **códigos de error** en OpenAPI está **incompleta** respecto al comportamiento real del Backend.

---

## Compatibilidad Frontend

### Qué debe enviar el Frontend

1. **JWT válido** de un Super Administrador con permiso `tenant.conexion.crear`.
2. **`cliente_id` idéntico** en la URL y en el body.
3. **Campos obligatorios:** `cliente_id`, `servidor`, `nombre_bd`, `usuario`, `password`.
4. Para tenants **Shared:** conexión **opcional**; si se registra, `es_conexion_principal: false` es lo habitual — **este contrato sigue siendo válido**.
5. Para tenants **Dedicated F4+ (happy path):** **no usar este endpoint** — usar `POST /api/v1/clientes/` con `tipo_instalacion=dedicated` conforme `DEDICATED_PROVISIONING_API_CONTRACT.md`.
6. Para tenants **Dedicated legacy / manual / repair / on-prem:** `es_conexion_principal: true` y credenciales reales de la BD ya provisionada — **único caso Dedicated donde aplica este contrato**.
7. **Trailing slash** en la URL (`/clientes/{id}/`) — la app tiene `redirect_slashes=False`.

### Qué puede esperar recibir

| Escenario | Expectativa |
|-----------|-------------|
| Éxito | `201` + objeto `ConexionRead` completo |
| Validación | `422` + `detail` + `error_code: "VALIDATION_ERROR"` |
| Conflicto principal | `409` + `detail` + `error_code: "PRIMARY_CONNECTION_CONFLICT"` |
| Sin permisos | `403` + `detail` (string) |
| Sin autenticación | `401` + `detail` (string) |
| Error servidor | `500` + `detail: "Error interno del servidor"` + `error_code` |

### Restricciones UI

- **Nunca** mostrar `usuario_encriptado`, `password_encriptado` ni `connection_string_encriptado`.
- Las credenciales en texto plano (`usuario`, `password`) solo viajan en el **request**; no se devuelven en la respuesta.
- Este endpoint **no** valida conectividad; para pruebas previas existe `POST /api/v1/conexiones/test` (contrato separado).

---

## Versionado

| Campo | Valor |
|-------|-------|
| **Version** | v1 |
| **Fecha de generación** | 2026-06-25 |
| **Última alineación F4** | 2026-06-25 — banner Legacy Dedicated; happy path → `DEDICATED_PROVISIONING_API_CONTRACT.md` |
| **Estado** | APPROVED |
| **Endpoint versionado** | `/api/v1/...` |
| **Contrato complementario Dedicated F4+** | `docs/contracts/DEDICATED_PROVISIONING_API_CONTRACT.md` |
| **Fuente canónica Backend** | `app/modules/tenant/presentation/endpoints_conexiones.py`, `schemas.py` (`ConexionCreate`/`ConexionRead`), `conexion_service.py` |

---

## Anexo — Resultado de auditoría READ-ONLY

### Endpoint oficial confirmado

`POST /api/v1/conexiones/clientes/{cliente_id}/`

Montado en `app/api/v1/api.py` con prefijo `/conexiones`.

### Inconsistencias detectadas (sin corrección aplicada)

| ID | Capas | Descripción |
|----|-------|-------------|
| A1 | Router ↔ Service | `cliente_id` en path se declara pero **no se usa**; persiste `conexion_data.cliente_id` del body |
| A2 | Service ↔ Hybrid | `crear_conexion` **no invoca** `invalidate_client_connection_cache()` tras insertar |
| A3 | Service ↔ BD | Sin pre-check de existencia de `cliente_id`; FK fallida → `DatabaseError` 500 |
| A4 | BD ↔ Service | Constraint `UNIQUE (cliente_id, es_conexion_principal)` puede provocar 500 en segundo registro con mismo valor de `es_conexion_principal` sin mapeo a 409 |
| A5 | Service ↔ Hybrid | No se valida `es_conexion_principal=true` para clientes Dedicated |
| A6 | Router ↔ OpenAPI | Docstrings del router listan 403/409/500; OpenAPI generado solo incluye 201/422 |
| A7 | Exceptions | 403 por `HTTPException` (LBAC/RBAC) vs `CustomException` — formatos de error distintos |
| A8 | Service | `connection_string_encriptado` permanece `null`; comentario en código indica generación "después del test" pero crear no ejecuta test |

### Alineamiento OpenAPI ↔ Backend

| Componente | Alineado |
|------------|----------|
| `ConexionCreate` campos/tipos/defaults/required | Sí |
| `ConexionRead` respuesta 201 | Sí |
| Códigos de error documentados en OpenAPI | Parcial (gap O1) |
| Reglas Hybrid Shared/Dedicated | No modeladas en schema (por diseño); documentadas en este contrato |

---

*Documento generado por auditoría READ-ONLY. No modifica código productivo ni OpenAPI.*
