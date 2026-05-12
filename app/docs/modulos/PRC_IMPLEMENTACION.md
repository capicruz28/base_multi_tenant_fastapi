# PRC — Implementación y verificación final (Gestión de precios)

Módulo: **Gestión de precios** (`PRC`)  
Alcance: cierre **Fase 3–4** según `docs/prompts/PROMPT_MODULO_MAESTRO.md`, `docs/bd/PRC_TABLAS.sql` y `app/docs/modulos/AUDITORIA_PRC.md`.

---

## 1) Archivos creados o modificados

### Creados

- `app/docs/modulos/AUDITORIA_PRC.md` — auditoría Fase 2 (referencia histórica).
- `app/docs/database/SEED_PERMISOS_PRC.sql` — seeds idempotentes (`MERGE`) de permisos `prc.lista_precio.*` y `prc.promocion.*`.

### Modificados

- `app/modules/prc/presentation/schemas.py` — `moneda_id` (UUID) en lista de precio; `empresa_id` en detalle (create/read).
- `app/infrastructure/database/tables_erp/tables_prc.py` — columna `moneda_id` + FK a `cat_moneda` en `prc_lista_precio`.
- `app/infrastructure/database/queries/prc/lista_precio_queries.py` — filtros por `cliente_id` y `empresa_id` opcional en get/update; detalle con `empresa_id` en listados.
- `app/infrastructure/database/queries/prc/promocion_queries.py` — `empresa_id` opcional en get/update.
- `app/modules/prc/application/services/lista_precio_service.py` — validación cabecera/detalle; baja/reactivación de lista.
- `app/modules/prc/application/services/promocion_service.py` — baja/reactivación de promoción; `empresa_id` en get/update.
- `app/modules/prc/application/services/__init__.py` — export de nuevos servicios.
- `app/modules/prc/presentation/endpoints_listas_precio.py` — RBAC en `POST` de detalle; `empresa_id` en queries; `DELETE` + `POST …/reactivar`; orden de rutas.
- `app/modules/prc/presentation/endpoints_promociones.py` — `empresa_id` en queries; `DELETE` + `POST …/reactivar`.

---

## 2) Endpoints nuevos — `cliente_id`, `empresa_id` y RBAC

Convención: `client_id = current_user.cliente_id` en todos los handlers; permisos con `require_permission("prc.<recurso>.<accion>")`.  
Las queries aplican **`empresa_id` en el `WHERE`** cuando el cliente envía el query opcional `empresa_id` (mismo criterio que ORG: acotar por empresa además del tenant).

| Ruta (prefijo `/prc`) | Método | RBAC | `cliente_id` | `empresa_id` |
|---|---|---|---|---|
| `/listas-precio/{lista_precio_id}/reactivar` | POST | `prc.lista_precio.actualizar` | Sí (servicios → queries) | Query opcional; si viene, filtra cabecera |
| `/listas-precio/{lista_precio_id}` | DELETE | `prc.lista_precio.eliminar` | Sí | Query opcional; idem |
| `/promociones/{promocion_id}/reactivar` | POST | `prc.promocion.actualizar` | Sí | Query opcional |
| `/promociones/{promocion_id}` | DELETE | `prc.promocion.eliminar` | Sí | Query opcional |

**Endpoint corregido (RBAC):**

| Ruta | Método | RBAC |
|---|---|---|
| `/listas-precio/{lista_precio_id}/detalles` | POST | `prc.lista_precio.crear` (antes solo autenticación) |

**Endpoints existentes reforzados (misma ruta y método):** `GET`/`PUT` de lista y detalle, `GET` de listados, `POST`/`PUT` de promoción — añaden **query opcional `empresa_id`** donde aplica; la lógica de negocio y las queries respetan ese filtro.

---

## 3) Verificación de contratos (OpenAPI / clientes)

- **Rutas y métodos** de los endpoints que ya existían se mantienen (mismos paths y verbos HTTP para listar, crear, actualizar, obtener por id y detalle).
- **Cambios intencionados de contrato** (alineación a BD y seguridad):
  - **Lista de precio:** el campo **`moneda` (string)** en request/response fue sustituido por **`moneda_id` (UUID)** en `ListaPrecioCreate`, `ListaPrecioUpdate` y `ListaPrecioRead`.
  - **Detalle de lista:** el body de creación exige **`empresa_id`**; la respuesta de lectura incluye **`empresa_id`**.
- **Responses nuevas:** `POST`/`DELETE` de reactivación y baja lógica devuelven el mismo `response_model` que el resto de escrituras (`ListaPrecioRead` / `PromocionRead`) o `204` en `DELETE`, sin romper el patrón REST del proyecto.

Ningún endpoint existente cambió **nombre de ruta ni método**; sí cambió el **shape** de algunos schemas como arriba (coordinar con frontend/consumidores).

---

## 4) RBAC — permisos y despliegue

Códigos usados por el backend:

- `prc.lista_precio.leer` | `crear` | `actualizar` | `eliminar`
- `prc.promocion.leer` | `crear` | `actualizar` | `eliminar`

Ejecutar en la **BD central de RBAC** el script `app/docs/database/SEED_PERMISOS_PRC.sql` (tras existir el módulo PRC con `modulo_id` `E100000D-0000-4000-8000-00000000000D`).

---

## 5) Cierre del módulo (estado)

- **PRC queda cerrado** para el alcance acordado: alineación a `moneda_id` y `empresa_id` en modelo y API de listas/detalles, validación tenant + empresa en queries, RBAC completo en creación de detalle, baja lógica y reactivación de listas y promociones, y seeds de permisos documentados.
- **Prerequisito de BD:** la tabla `prc_lista_precio` debe exponer la columna **`moneda_id`** (FK a `cat_moneda`), coherente con `docs/bd/PRC_TABLAS.sql`. El ORM `tables_prc.py` ya refleja ese contrato.

Si en el futuro se requiere endurecer reglas (por ejemplo: obligar `empresa_id` en query en todos los `GET` por id), debe tratarse como cambio de contrato explícito y revisión de clientes.
