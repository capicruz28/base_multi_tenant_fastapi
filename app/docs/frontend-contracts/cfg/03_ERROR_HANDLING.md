# CFG — Manejo de errores (Frontend)

**Versión:** 1.0

Documenta errores **funcionales** que el Frontend debe manejar. No incluye errores internos del Backend.

Prioridad de mensaje al usuario:

1. `detail` / mensaje del response HTTP (si es legible).
2. Mensaje sugerido de esta tabla según código / `internal_code` (si el cliente lo expone).
3. Mensaje genérico de la categoría HTTP.

---

## 1. Mapa de errores funcionales

| HTTP | Código / señal | Operaciones | Mensaje sugerido UI | Recuperable | Reintento |
|------|----------------|-------------|---------------------|:-----------:|:---------:|
| **403** | Sin permiso | Todas | “No tiene permiso para esta acción.” | Sí (pedir rol) | No automático |
| **404** | No encontrada | GET/PATCH/DELETE/reactivar/preview | “La secuencia no existe o no está disponible.” | Sí (volver al listado) | No |
| **422** | `ORG_EMPRESA_CFG_LOCKED` | PATCH, DELETE | “Esta secuencia está bloqueada y no se puede modificar ni desactivar.” | Sí (solo lectura) | No |
| **422** | `CFG_PREFIX_INVALID` | PATCH | “El prefijo no es válido. Use hasta 10 caracteres alfanuméricos.” | Sí (corregir campo) | No |
| **422** | `CFG_SEPARATOR_INVALID` | PATCH | “El separador solo puede estar vacío o ser ‘-’.” | Sí (corregir) | No |
| **422** | `CFG_PADDING_INVALID` | PATCH | “La longitud del número debe ser un entero mayor o igual a 1.” | Sí (corregir) | No |
| **422** | `CFG_NUMERO_INICIAL_INVALID` | PATCH | “El número inicial debe ser mayor o igual a 1.” | Sí (corregir) | No |
| **422** | `PREVIEW_NOT_ALLOWED` | Preview | “La previsualización no está disponible para esta secuencia.” | Sí (ocultar Preview) | No |
| **422** | `INVALID_SORT_COLUMN` | Listado | “Columna de orden no válida.” | Sí (quitar sort) | No |
| **422** | Schema / campos extra / body vacío | PATCH | “Revise los datos enviados. Solo se permiten prefijo, separador, longitud y número inicial.” | Sí | No |
| **401** | Sesión | Todas | “Sesión expirada. Vuelva a iniciar sesión.” | Sí (relogin) | Tras autenticar |
| **5xx** / red | Fallo transporte | Todas | “No se pudo completar la operación. Intente de nuevo.” | Sí | Sí (manual o 1 retry) |

---

## 2. Cómo debe reaccionar el Frontend

### 403

- No mostrar botones que el RBAC ya ocultó (prevención).
- Si llega 403: toast/banner; no corromper el formulario.
- No reintentar la misma acción automáticamente.

### 404

- En detalle: pantalla vacía + CTA “Volver al listado”.
- En mutación desde detalle: cerrar edición y refrescar listado.
- Tratar cross-tenant como “no encontrada” (mismo 404).

### 422 de negocio

- Mantener el formulario con los valores editados.
- Resaltar el campo implicado cuando el código lo permita.
- Si `ORG_EMPRESA_CFG_LOCKED`: forzar modo solo lectura y refrescar detalle (`config_locked`).

### Preview 422

- Deshabilitar botón Preview para esa secuencia en la sesión UI.
- No interpretar como fallo de red.

### Errores de red / 5xx

- Únicos candidatos a **reintento** (1 vez o botón “Reintentar”).
- No reintentar 4xx de validación.

---

## 3. Validación preventiva (antes de llamar API)

Reduce 422 y mejora UX:

| Campo | Validar en UI |
|-------|----------------|
| `prefijo` | No vacío si se envía; máx. 10; preferir alfanumérico; mayúsculas |
| `separador` | Solo `""` o `"-"` |
| `longitud_numero` | Entero ≥ 1 |
| `numero_inicial` | Entero ≥ 1 |
| PATCH | Al menos un campo modificado |

**Nota:** `numero_inicial` menor o igual que `ultimo_numero` **está permitido**; no bloquearlo en UI.

---

## 4. Qué no hacer

- No mapear errores SQL ni mensajes técnicos internos.
- No asumir códigos de error no listados en este contrato MVP.
- No tratar 404 como 403.
- No mostrar “conflicto de formato” (no existe en este MVP).
- No mostrar error si DELETE/reactivar idempotente devuelve 200.

---

## 5. Resumen: recuperable vs reintento

| Tipo | Recuperable | Reintento automático |
|------|:-----------:|:--------------------:|
| 403 / 404 / 422 negocio | Sí (cambiar UI o datos) | No |
| 401 | Sí (login) | Tras nuevo token |
| Red / 5xx | Sí | Sí (acotado) |
