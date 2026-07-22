# CFG — Comportamiento de UI esperado

**Versión:** 1.0  
**Audiencia:** Frontend

Describe cómo debe comportarse la interfaz ante cada operación. No define look & feel; define **estados y reacciones**.

---

## 1. Pantallas del MVP

| Pantalla | Permiso mínimo | Contenido |
|----------|----------------|-----------|
| Listado de secuencias | `cfg.secuencias.consultar` | Tabla/lista + filtros |
| Detalle / edición | `cfg.secuencias.consultar` | Formulario lectura + acciones |
| Acciones de mutación | `cfg.secuencias.actualizar` | Guardar, desactivar, reactivar |

Sin `consultar`: no entrar al módulo (o mostrar acceso denegado).

---

## 2. Listado

### Loading

- Al montar y al cambiar filtros/página/sort: estado **loading**.
- No mostrar datos stale como “definitivos” mientras carga (o indicar claramente que se refresca).

### Datos

- Sin `page`: tratar la respuesta como array completo.
- Con `page`: usar `items` + metadatos (`total`, `pagina_actual`, `total_paginas`, `limit`).

### Filtros recomendados

- `modulo_codigo`, `es_activo`, `sequence_key`, `empresa_id`, `buscar`.
- Al cambiar filtros con paginación: volver a `page=1`.

### Indicadores por fila

| Campo | UI sugerida |
|-------|-------------|
| `es_activo=false` | Badge “Inactiva” |
| `config_locked=true` | Badge “Bloqueada” + sin botones editar/desactivar |
| `policy_drift=true` | Badge informativo (no bloquea edición por sí solo) |

### Cuándo refrescar el listado

- Tras **PATCH** exitoso (si el usuario vuelve al listado o el listado está visible).
- Tras **DELETE** (desactivar) o **reactivar** exitoso.
- Tras cambio de filtros / page / sort.
- **No** es obligatorio refrescar el listado solo por un Preview.

---

## 3. Detalle

### Loading

- Al abrir por `secuencia_id`: loading hasta `GET` detalle.
- Si 404: mensaje “Secuencia no encontrada” y volver al listado.

### Campos de solo lectura (siempre)

- `sequence_key`, scope (`scope_type`, empresa/almacén/PV si aplican).
- `ultimo_numero`, `generation_policy`.
- Metadatos enrich (`modulo_codigo`, defaults, etc.).
- Auditoría (`fecha_creacion`, `fecha_actualizacion`).

### Campos editables (si `config_locked=false` y permiso `actualizar`)

- `prefijo`, `separador`, `longitud_numero`, `numero_inicial`.

### Si `config_locked=true` (`org_empresa`)

- Formulario en **solo lectura**.
- Ocultar/deshabilitar Guardar y Desactivar.
- Permitir ver detalle y Preview (si aplica).
- Mensaje: “Esta secuencia está bloqueada y no se puede modificar.”

### Cuándo refrescar el detalle

- Tras **PATCH** exitoso → usar el body 200 o volver a `GET` detalle.
- Tras **DELETE** / **reactivar** exitoso → actualizar con el body 200.
- Tras Preview → **no** hace falta refrescar detalle por consumo de contador (no hay consumo); opcional solo si se quiere revalidar estado.

---

## 4. Guardar (PATCH)

### Flujo UI

1. Usuario edita campos B.
2. Validación local recomendada (ver `03_ERROR_HANDLING` / reglas de envío).
3. Botón Guardar → loading en el botón / formulario disabled.
4. **200** → toast éxito (“Configuración actualizada”) + actualizar estado local con response.
5. **422** → mostrar mensaje de negocio junto al campo o banner.
6. **403/404** → ver manejo de errores.

### Mensajes esperados

| Caso | Mensaje sugerido |
|------|------------------|
| Éxito | “Configuración actualizada.” |
| Body vacío | Evitar envío; “Indique al menos un campo a modificar.” |
| Locked | “No se puede modificar esta secuencia.” |

### Refresh

- Actualizar detalle con response.
- Invalidar cache del listado (ver guía de integración).

---

## 5. Desactivar (DELETE) y Reactivar

### Desactivar

- Mostrar confirmación: “¿Desactivar esta secuencia? No se eliminará; podrá reactivarla después.”
- Loading en la acción.
- **200** → toast “Secuencia desactivada.” + UI en estado inactivo.
- Si ya inactiva: 200 → no mostrar error; opcional toast suave o silencio.

### Reactivar

- Visible cuando `es_activo=false` (y no locked).
- **200** → toast “Secuencia reactivada.”
- Si ya activa: 200 idempotente.

### Regla de botones

| Estado | Desactivar | Reactivar |
|--------|:----------:|:---------:|
| Activa + no locked | visible | oculto |
| Inactiva + no locked | oculto | visible |
| `config_locked` | oculto/disabled | oculto/disabled (o no aplica) |

### Refresh

- Actualizar detalle y listado tras éxito.

**Importante:** no implementar toggles “activar/desactivar” vía PATCH. Solo `DELETE` y `POST …/reactivar`.

---

## 6. Preview

### Cuándo mostrar el botón

- Permiso `consultar`.
- Preferible si `supports_preview !== false`.
- Permitido también con secuencia **inactiva**.

### Comportamiento

1. Click Preview → loading breve.
2. Body vacío en el POST.
3. Mostrar `codigo_estimado` de forma destacada.
4. Mostrar siempre el `disclaimer` (texto del Backend).
5. Indicar que **no consume** correlativo (`consume_contador === false`).

### Mensajes

| Caso | Mensaje sugerido |
|------|------------------|
| Éxito | Título: “Código estimado”; subtítulo: disclaimer del API |
| Inactiva + 200 | Mostrar estimación + aviso “La secuencia está inactiva.” |
| 422 no permitido | “La previsualización no está disponible para esta secuencia.” |

### Refresh

- No invalidar listado por Preview.
- No asumir que `ultimo_numero` cambió.

---

## 7. Estados globales de UI (resumen)

| Estado | Significado |
|--------|-------------|
| `idle` | Sin operación en curso |
| `loading_list` | Cargando listado |
| `loading_detail` | Cargando detalle |
| `saving` | PATCH en curso |
| `toggling_active` | DELETE o reactivar en curso |
| `previewing` | Preview en curso |
| `error` | Error recuperable mostrado al usuario |

Evitar mutaciones concurrentes sobre la misma secuencia (deshabilitar botones mientras `saving` / `toggling_active`).
