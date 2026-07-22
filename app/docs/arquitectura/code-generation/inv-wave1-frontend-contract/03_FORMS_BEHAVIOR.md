# 03 — Guía funcional de formularios y UX

---

## 1. Reglas UX transversales

### AUTO_DEFAULT (cinco maestros)

- Alta estándar: el código puede estar oculto o visible como opcional.
- Si está visible, placeholder oficial:
  **«Dejar vacío para generar automáticamente»**.
- Ayuda:
  **«El código se asignará al guardar. Puede indicar uno manual si el proceso de implantación lo requiere.»**
- Input vacío: preferir omitir la propiedad del JSON.
- Éxito: usar el código del response, nunca el valor local.

### AUTO_REQUIRED (dos documentos)

- No renderizar input editable ni oculto para el número.
- No incluir el campo en estado de formulario, validación ni payload.
- Texto previo al guardado:
  **«El número se asignará automáticamente al guardar.»**

### UPDATE / BR-IMM

El identificador puede mostrarse como texto o control disabled/readonly, pero
debe vivir fuera del objeto enviado por PUT. No existe operación estándar para
renumerar.

### Badges

El response no informa si un código AUTO_DEFAULT fue generado o ingresado
manualmente. Por tanto:

- no mostrar badge «Automático»/«Manual» en listados;
- sí se puede mostrar un badge temporal «Asignado» tras el `201`;
- badges de estado (`activo`, `borrador`, etc.) no cambian.

---

## 2. Categoría

### CREATE

| Elemento | Comportamiento |
|----------|----------------|
| Automático | `codigo` omitido/`null`/vacío ⇒ Backend genera `CATnnn` |
| Visible | `nombre` y campos funcionales existentes |
| Opcional | Input `codigo` solo si se mantiene modo manual |
| Oculto | Ningún valor pre-generado por React |
| Placeholder | «Dejar vacío para generar automáticamente» |
| 409 | Mostrar `detail` junto al campo código manual |
| Éxito | «Categoría creada con código {codigo}» |

### UPDATE

- `codigo`: readonly; no enviarlo.
- Resto de campos de `CategoriaUpdate`: editables según permisos existentes.
- Intentar cambiar el valor local no debe alterar el payload.

### LIST

- Mantener columna `codigo`.
- Mantener búsqueda/orden existentes.
- No inferir origen manual/automático.

---

## 3. Unidad de medida

### CREATE

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Sin `codigo` ⇒ `UMnnn` |
| Visibles requeridos | `nombre`, `tipo_unidad` y empresa de contexto |
| Código manual | Opcional; máximo 10 caracteres |
| Placeholder | «Dejar vacío para generar automáticamente» |
| Éxito | «Unidad de medida creada con código {codigo}» |

### UPDATE

- `codigo` readonly y excluido del PUT.
- `nombre`, `simbolo`, `tipo_unidad`, conversiones y estado permanecen editables
  conforme al schema.

### LIST

- Mantener `codigo`, nombre, símbolo y estado.
- Sin badge de origen del código.

---

## 4. Tipo de movimiento

### CREATE

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Sin `codigo` ⇒ `TMnnn` |
| Visibles requeridos | `nombre`, `clase_movimiento` |
| Código manual | Opcional; máximo 20 caracteres |
| Placeholder | «Dejar vacío para generar automáticamente» |
| Éxito | «Tipo de movimiento creado con código {codigo}» |

### UPDATE

- `codigo` readonly y excluido.
- No confundir con el número de un documento Movimiento.

### LIST

- Mantener columna `codigo`.
- Badges funcionales de clase/sistema/activo sin cambios.

---

## 5. Almacén

### CREATE

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Sin `codigo` ⇒ `ALMnnn` |
| Visibles requeridos | `nombre`, `tipo_almacen` |
| Código manual | Opcional; máximo 20 caracteres |
| Placeholder | «Dejar vacío para generar automáticamente» |
| Éxito | «Almacén creado con código {codigo}» |

### UPDATE

- `codigo` readonly y excluido.
- Sucursal, centro de costo, capacidades y flags siguen su comportamiento actual.

### LIST

- Mantener columna `codigo`.
- Badges de almacén principal/permisos/activo sin cambios.

---

## 6. Producto

### CREATE

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Sin `codigo_sku` ⇒ `P` + 5 dígitos |
| SKU manual | Opcional; máximo 50 caracteres |
| Placeholder SKU | «Dejar vacío para generar automáticamente» |
| Otros códigos | `codigo_barra`, `codigo_interno`, `codigo_fabricante` siguen visibles/editables |
| Éxito | «Producto creado con SKU {codigo_sku}» |

La automatización solo afecta `codigo_sku`.

### UPDATE

- `codigo_sku`: readonly y fuera del PUT.
- Código de barras, interno y fabricante: editables.
- No deshabilitar todos los campos cuyo nombre empieza por `codigo`.

### LIST

- Mantener columna SKU.
- Otros códigos pueden conservar sus columnas/filtros actuales.
- Sin badge de origen del SKU.

---

## 7. Movimiento

### CREATE simple y CREATE con detalle

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Backend siempre asigna `numero_movimiento` |
| Visible antes de guardar | Texto «El número se asignará automáticamente al guardar» |
| Oculto/eliminado | Input, validation y payload de `numero_movimiento` |
| Detalles | En `/con-detalle`, mínimo una línea; sin cambio |
| Éxito | «Movimiento creado: {numero_movimiento}» |

No existe override manual en UI.

### UPDATE simple y con detalle

- Mostrar `numero_movimiento` en encabezado readonly.
- No enviarlo.
- BR-IMM aplica aunque el movimiento esté en borrador.
- Las reglas de edición por estado y reemplazo de detalles no cambian.

### LIST / DETALLE / PROCESOS

- Mantener columna/encabezado `numero_movimiento`.
- Mantener badges de estado.
- Procesar, autorizar y anular preservan el número.
- Estornar: el response corresponde al movimiento original en estado
  `estornado`; el compensatorio se numera internamente y no se calcula ni se
  presenta como dato retornado directo de esta acción.

---

## 8. Inventario físico

### CREATE simple y CREATE con detalle

| Elemento | Comportamiento |
|----------|----------------|
| Automático | Backend siempre asigna `numero_inventario` |
| Visible antes de guardar | Texto «El número se asignará automáticamente al guardar» |
| Oculto/eliminado | Input, validation y payload de `numero_inventario` |
| Detalles | Opcionales al crear; sin cambio |
| Éxito | «Inventario físico creado: {numero_inventario}» |

No existe override manual en UI.

### UPDATE simple y con detalle

- Mostrar `numero_inventario` readonly.
- No enviarlo.
- Detalles opcionales y reglas de conteo permanecen.

### LIST / DETALLE / PROCESOS

- Mantener columna/encabezado `numero_inventario`.
- Mantener badges de estado.
- Anular, finalizar y aprobar preservan el número.
- La aprobación puede devolver `movimiento_ajuste_id`; el número del movimiento
  asociado se consulta al Backend, no se calcula localmente.

---

## 9. Manejo de mensajes

| Evento | Mensaje UX |
|--------|------------|
| 201 maestro | Usar «{Entidad} creada con código {response.codigo/SKU}» |
| 201 documento | Usar «{Documento} creado: {response.numero_*}» |
| 409 manual duplicado | Mostrar el `detail` exacto del Backend junto al campo |
| 404 `CFG_SEQUENCE_NOT_FOUND` | «No se pudo asignar el código. Contacte a soporte.» |
| 403 empresa mismatch | «La empresa del formulario no coincide con la sesión activa.» |
| 422 | Mostrar errores por campo; no sustituirlos por un mensaje genérico |

No reintentar un 404/409 inventando un correlativo en Frontend.
