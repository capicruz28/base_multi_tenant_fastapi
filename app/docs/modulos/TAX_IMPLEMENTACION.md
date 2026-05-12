# TAX — Implementación y verificación final (Gestión tributaria)

Módulo: **Gestión tributaria** (`TAX`) — libros electrónicos / PLE  
Alcance: cierre **Fase 3–4** según `docs/prompts/PROMPT_MODULO_MAESTRO.md`, `docs/bd/TAX_TABLAS.sql` y `app/docs/modulos/AUDITORIA_TAX.md`.

Prefijo API: **`/tax`**. Subrecurso: **`/tax/libros-electronicos`**.

---

## 1) Archivos creados o modificados

### Creados

- `app/docs/modulos/AUDITORIA_TAX.md` — auditoría Fase 2 (referencia histórica).
- `app/docs/modulos/TAX_IMPLEMENTACION.md` — este documento (Fase 4).
- `app/docs/database/SEED_PERMISOS_TAX.sql` — seeds idempotentes (`MERGE`) de permisos `tax.libro.*`.
- `app/modules/tax/application/libro_estados.py` — constantes de estado y conjunto de estados anulables.

### Modificados

- `app/modules/tax/presentation/schemas.py` — creación con `estado` ignorado en servidor; `LibroElectronicoUpdate` sin `estado` + `generado_por_usuario_id`; `LibroElectronicoRegistrarEnvio`.
- `app/modules/tax/presentation/endpoints_libro_electronico.py` — endpoints de transición (`marcar-generado`, `registrar-envio`, `anular`).
- `app/modules/tax/application/services/libro_electronico_service.py` — validación de empresa en creación; máquina de estados; conflictos de negocio (`ConflictError`).
- `app/modules/tax/application/services/__init__.py` — export de funciones de servicio adicionales.
- `app/infrastructure/database/queries/tax/libro_electronico_queries.py` — `UPDATE` solo en `estado = 'borrador'`; `transition_libro_electronico_estado`.
- `app/infrastructure/database/queries/tax/__init__.py` — export de `transition_libro_electronico_estado`.

---

## 2) Endpoints — `cliente_id`, `empresa_id` y RBAC

Convención: en todos los handlers se usa `current_user.cliente_id` como tenant; permisos con `require_permission("tax.libro.<accion>")`. Las queries filtran por **`cliente_id`**; en listado y creación se usa **`empresa_id`** según tabla y reglas de negocio.

| Ruta (prefijo `/tax/libros-electronicos`) | Método | RBAC | `cliente_id` | `empresa_id` |
|---|---|---|---|---|
| `""` (lista) | GET | `tax.libro.leer` | Sí (servicio → queries) | Query opcional; si viene, filtra en listado |
| `/{libro_id}` | GET | `tax.libro.leer` | Sí | Persistido en fila; sin query de refuerzo en detalle |
| `""` (crear) | POST | `tax.libro.crear` | Sí (inyectado en insert) | Validado con `get_empresa_servicio(cliente_id, empresa_id)` del body |
| `/{libro_id}` | PUT | `tax.libro.actualizar` | Sí | No editable en `PUT` (solo en borrador) |
| `/{libro_id}/marcar-generado` | POST | `tax.libro.actualizar` | Sí | No cambia en esta acción |
| `/{libro_id}/registrar-envio` | POST | `tax.libro.actualizar` | Sí | No cambia en esta acción |
| `/{libro_id}/anular` | POST | `tax.libro.actualizar` | Sí | No cambia en esta acción |

---

## 3) Verificación de contratos (OpenAPI / clientes)

- **Rutas y métodos conservados:** `GET ""`, `GET /{libro_id}`, `POST ""`, `PUT /{libro_id}` — mismos paths y verbos; **`response_model`** sigue siendo `LibroElectronicoRead` (o lista del mismo esquema).
- **Cambios intencionados de contrato en request:**
  - **POST crear:** el campo opcional **`estado`** del body, si se envía, **se ignora**; el servidor persiste siempre **`borrador`**.
  - **PUT actualizar:** ya **no** se acepta **`estado`** en el JSON; las transiciones se hacen por los `POST` de acción. Sigue permitido actualizar metadatos (archivos, totales, observaciones, etc.) **solo** mientras el registro esté en **`borrador`**.
- **Respuestas:** altas nuevas devuelven **`estado: "borrador"`** en lugar del valor por defecto histórico del script SQL (`generado` en comentarios de BD); los clientes deben adaptar flujo: **borrador** → **`POST …/marcar-generado`** → **generado** → **`POST …/registrar-envio`** → **enviado**; **`POST …/anular`** desde estados permitidos.
- **Errores de negocio:** actualización o transición inválida responde **409** vía `ConflictError` (manejador global de `CustomException`).

---

## 4) RBAC — permisos y despliegue

Códigos usados por el backend:

- `tax.libro.leer`
- `tax.libro.crear`
- `tax.libro.actualizar` (también cubre `marcar-generado`, `registrar-envio` y `anular`)

Ejecutar en la **BD central de RBAC** el script `app/docs/database/SEED_PERMISOS_TAX.sql` (tras existir el módulo TAX con `modulo_id` **`E1000012-0000-4000-8000-000000000012`**, alineado a `SEED_MODULO_MENU.SQL`).

---

## 5) Modelo de datos y estados (`tax_libro_electronico`)

- Tabla de referencia: `docs/bd/TAX_TABLAS.sql`. Sin cambios de DDL desde la aplicación.
- Estados manejados en código: **`borrador`**, **`generado`**, **`enviado`**, **`aceptado`**, **`rechazado`**, **`anulado`** (definiciones en `libro_estados.py`).
- **Anular:** permitido desde `borrador`, `generado`, `enviado`, `rechazado`; no desde **`aceptado`** ni **`anulado`**.

---

## 6) Cierre del módulo (estado)

- **TAX queda cerrado** para el alcance acordado: una entidad activa (`tax_libro_electronico`), multi-tenant por `cliente_id`, validación de **`empresa_id`** en creación, flujo de estados con acciones dedicadas, `PUT` acotado a borrador, seeds de permisos documentados y trazabilidad en `AUDITORIA_TAX.md` + este archivo.
- **Fuera de alcance actual:** tablas tributarias adicionales que no existan en `TAX_TABLAS.sql`; integración real con SUNAT (solo campos y transiciones de negocio en API).

Si en el futuro se exige **query opcional `empresa_id`** en `GET /{libro_id}` u obligatoriedad de empresa en listados, debe tratarse como cambio de contrato explícito y revisión de clientes.
