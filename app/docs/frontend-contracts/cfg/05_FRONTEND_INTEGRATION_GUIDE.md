# CFG — Guía de integración Frontend

**Versión:** 1.0

Flujo correcto de consumo del API y recomendaciones de cache/invalidación.

---

## 1. Flujo canónico

```text
GET listado
    ↓
GET detalle
    ↓
PATCH (opcional)
    ↓
DELETE soft  ó  POST reactivar  (opcional)
    ↓
POST preview  (opcional, en cualquier momento de lectura)
    ↓
Refresh (listado y/o detalle según mutación)
```

### Orden recomendado al abrir el módulo

1. Verificar permisos (`consultar` mínimo).
2. `GET /cfg/secuencias` (con filtros iniciales).
3. Al seleccionar fila → `GET /cfg/secuencias/{id}`.
4. Edición solo si `actualizar` y no `config_locked`.
5. Preview bajo demanda (no obligatorio al abrir).

---

## 2. Consumo por operación

### Listado

- Llamar con los query params activos.
- Decidir modo legacy (sin `page`) vs paginado (con `page`) de forma consistente en toda la app.
- No mezclar: si la UI es paginada, **siempre** enviar `page`.

### Detalle

- Usar `secuencia_id` del listado.
- Preferir detalle fresco antes de editar (evitar PATCH sobre datos stale).

### PATCH

- Enviar **solo** campos modificados.
- Tras 200: reemplazar estado local con el response (o re-GET).

### DELETE / Reactivar

- No usar PATCH para `es_activo`.
- Tras 200: actualizar estado local; invalidar listado.

### Preview

- POST sin body.
- Mostrar `codigo_estimado` + `disclaimer`.
- No encadenar allocate ni asumir persistencia.

---

## 3. Invalidación de cache (recomendada)

Asumiendo un cache/query client (React Query, SWR, etc.):

| Query key sugerida | Contenido |
|--------------------|-----------|
| `['cfg','secuencias', filters]` | Listado |
| `['cfg','secuencia', secuenciaId]` | Detalle |
| `['cfg','preview', secuenciaId]` | Preview (opcional, TTL corto) |

| Evento | Invalidar |
|--------|-----------|
| PATCH 200 | Detalle + listado |
| DELETE 200 | Detalle + listado |
| Reactivar 200 | Detalle + listado |
| Preview 200 | **Nada** obligatorio (preview no muta) |
| Cambio de filtros | Refetch listado (nueva key) |
| 404 en detalle | Remover detalle de cache; refetch listado |

### TTL sugerido

| Recurso | Sugerencia |
|---------|------------|
| Listado | Stale corto (p. ej. 30–60 s) o refetch on focus |
| Detalle | Stale corto; refetch antes de editar |
| Preview | No cachear, o TTL muy corto (segundos); siempre mostrar disclaimer |

---

## 4. Cuándo volver a consultar

| Situación | Acción |
|-----------|--------|
| Usuario vuelve al listado tras editar | Refetch o usar cache invalidado |
| Usuario cambia empresa / filtros de sesión ERP | Refetch listado completo |
| Tras error 404 en mutación | Refetch listado; salir del detalle |
| Tras `ORG_EMPRESA_CFG_LOCKED` | Refetch detalle (confirmar `config_locked`) |
| Tab focus después de mucho tiempo | Refetch listado (opcional) |
| Solo hizo Preview | No refetch de contador |

---

## 5. Sesión y tenant

- Todas las rutas viven bajo sesión ERP del tenant.
- No enviar `cliente_id` en body/query para “elegir tenant”.
- Si la sesión cambia (logout, cambio de contexto): limpiar todo el cache `cfg`.

---

## 6. Cliente HTTP (orientación)

- Usar los **operationIds** al generar el client OpenAPI.
- Base URL: la misma del resto del ERP (`/api/v1`).
- Headers de autenticación: iguales al resto de módulos ERP.
- Content-Type `application/json` en PATCH.

---

## 7. Anti-patrones

- Llamar “activar” / “desactivar” por paths inventados.
- PATCH con `es_activo` o `ultimo_numero`.
- Tratar Preview como commit del siguiente código.
- Cachear Preview como dato maestro sin disclaimer.
- Crear UI de “nueva secuencia” en este MVP.
