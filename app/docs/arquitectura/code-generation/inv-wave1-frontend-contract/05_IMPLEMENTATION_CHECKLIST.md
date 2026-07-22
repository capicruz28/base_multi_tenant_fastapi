# 05 — Checklist de implementación y certificación Frontend

Un Frontend INV se considera certificado respecto al Motor de Códigos únicamente
cuando todos los gates de este documento están completos.

---

## 1. Preparación

- [ ] Equipo leyó este paquete completo.
- [ ] Baseline V1 y contrato ORG fueron identificados como referencias.
- [ ] `app/docs/openapi_snapshot.json` vigente fue fijado como fuente.
- [ ] Cliente/tipos TypeScript fueron regenerados o comparados con el snapshot.
- [ ] Se inventariaron los siete campos Motor.
- [ ] Se inventariaron validaciones, defaults, serializers y mutations.
- [ ] Se confirmó ambiente con Backend INV certificado y cfg de secuencias.
- [ ] Se definió cómo observar requests/responses en QA.

---

## 2. Tipos y API client

- [ ] `CategoriaCreate.codigo` es opcional/nullable.
- [ ] `UnidadMedidaCreate.codigo` es opcional/nullable.
- [ ] `TipoMovimientoCreate.codigo` es opcional/nullable.
- [ ] `AlmacenCreate.codigo` es opcional/nullable.
- [ ] `ProductoCreate.codigo_sku` es opcional/nullable.
- [ ] `MovimientoCreate` no contiene `numero_movimiento`.
- [ ] `MovimientoConDetalleCreate` no contiene `numero_movimiento`.
- [ ] `InventarioFisicoCreate` no contiene `numero_inventario`.
- [ ] `InventarioFisicoConDetalleCreate` no contiene `numero_inventario`.
- [ ] Ningún Update contiene su campo Motor.
- [ ] Todos los Read mantienen el campo Motor como `string` requerido.
- [ ] Producto Update conserva códigos alternativos editables.

---

## 3. Formularios CREATE

### Maestros AUTO_DEFAULT

- [ ] Submit no se bloquea por código vacío.
- [ ] Input opcional usa el copy oficial o se oculta.
- [ ] String vacío se omite o convierte a `null`.
- [ ] Código manual, si se ofrece, respeta `maxLength`.
- [ ] No se genera correlativo en React.
- [ ] Response 201 reemplaza el estado/caché local.
- [ ] Se muestra el código definitivo retornado.

### Documentos AUTO_REQUIRED

- [ ] Movimiento no muestra input de número.
- [ ] Inventario físico no muestra input de número.
- [ ] Formularios simples no guardan el número en estado.
- [ ] Formularios con detalle tampoco lo guardan.
- [ ] Request no contiene número, ni siquiera `null` o `""`.
- [ ] Response 201 se usa como fuente del número.

---

## 4. Formularios UPDATE / BR-IMM

- [ ] Código/número se muestra readonly o como texto.
- [ ] Campo readonly está fuera del objeto editable.
- [ ] Mapper/serializer PUT elimina el campo Motor.
- [ ] Ningún botón permite renumerar.
- [ ] Cambio local/manipulación de DOM no introduce el campo en request.
- [ ] Soft-delete/reactivar preserva el identificador.
- [ ] Producto solo protege `codigo_sku`.
- [ ] Movimiento/Inventario con detalle tampoco envían número.

---

## 5. Listados y detalle

- [ ] Categoría muestra `codigo`.
- [ ] Unidad de medida muestra `codigo`.
- [ ] Tipo de movimiento muestra `codigo`.
- [ ] Almacén muestra `codigo`.
- [ ] Producto muestra `codigo_sku`.
- [ ] Movimiento muestra `numero_movimiento`.
- [ ] Inventario físico muestra `numero_inventario`.
- [ ] Filtros/orden existentes no presentan regresión.
- [ ] No se muestra badge manual/automático sin dato de Backend.
- [ ] Badges funcionales de estado permanecen.

---

## 6. Errores y mensajes

- [ ] 409 de código/SKU manual se muestra junto al campo.
- [ ] Se conserva el `detail` útil del Backend.
- [ ] 403 por empresa/sesión se diferencia de validación de formulario.
- [ ] 404 de configuración se presenta como error técnico.
- [ ] Ante 404 no se genera código local.
- [ ] Errores 422 se asignan a campos cuando corresponda.
- [ ] Un submit fallido no muestra código provisional como definitivo.

---

## 7. Pruebas unitarias Frontend

- [ ] Schema/validator AUTO_DEFAULT acepta código ausente.
- [ ] Serializer AUTO_DEFAULT omite string vacío.
- [ ] Serializer Update omite campo Motor.
- [ ] Serializer documental nunca incluye número.
- [ ] `onSuccess` consume código/número del response.
- [ ] Error 409 se mapea al campo manual.
- [ ] Producto conserva edición de códigos alternativos.
- [ ] Cambio de empresa invalida formulario sensible al scope.

---

## 8. Pruebas de integración / E2E

### Cada maestro

- [ ] CREATE sin código ⇒ 201 + identificador.
- [ ] CREATE manual válido ⇒ 201 + identificador manual normalizado.
- [ ] CREATE manual duplicado ⇒ 409.
- [ ] UPDATE no envía código.
- [ ] Refresh confirma código inmutable.
- [ ] Desactivar/reactivar preserva código.

### Movimiento

- [ ] CREATE simple ⇒ request sin número; 201 con número.
- [ ] CREATE con detalle ⇒ request sin número; 201 con número.
- [ ] UPDATE simple/con-detalle ⇒ request sin número.
- [ ] Procesar/autorizar/anular preserva número.
- [ ] Estorno no envía número y conserva en el response el número del original.
- [ ] La UI no supone que la acción de estorno retorna directamente el
  movimiento compensatorio.

### Inventario físico

- [ ] CREATE simple ⇒ request sin número; 201 con número.
- [ ] CREATE con detalle ⇒ request sin número; 201 con número.
- [ ] UPDATE simple/con-detalle ⇒ request sin número.
- [ ] Finalizar/anular/aprobar preserva número de inventario.
- [ ] Aprobación no recibe un número de movimiento generado por React.

### Multiempresa

- [ ] Formularios usan empresa activa.
- [ ] Cambio de empresa no reutiliza caché/form state incorrecto.
- [ ] No se asume correlativo global entre empresas.

---

## 9. Validación contractual

- [ ] Requests capturados coinciden con schemas OpenAPI.
- [ ] Responses 201/200 coinciden con Read schemas.
- [ ] No hay campos Motor extra en PUT.
- [ ] No hay números AUTO_REQUIRED extra en POST.
- [ ] Rutas y permisos permanecen sin cambios.
- [ ] No se implementó acceso directo a cfg/Motor.
- [ ] No se implementó preview local.
- [ ] No se depende de que Backend ignore extras.

---

## 10. Definition of Done Frontend

| Gate | Criterio |
|------|----------|
| FE-D1 | Los cinco maestros crean sin código y muestran el retornado. |
| FE-D2 | El camino manual de maestros funciona y maneja 409. |
| FE-D3 | Movimiento e Inventario físico nunca envían número. |
| FE-D4 | Todos los Updates cumplen BR-IMM. |
| FE-D5 | Read/List muestran siempre el identificador. |
| FE-D6 | Soft-delete y procesos preservan identificadores. |
| FE-T1 | Tipos compilados coinciden con snapshot vigente. |
| FE-T2 | Unit tests de serializers/forms están verdes. |
| FE-T3 | E2E auto/manual/readonly están verdes. |
| FE-T4 | Evidencia Network confirma requests limpios. |
| FE-T5 | No hay generación local ni acceso a cfg. |
| FE-C1 | QA aprobó los siete recursos. |
| FE-C2 | Sin regresiones en empresa, RBAC, listas o detalles. |
| FE-C3 | Este paquete queda referenciado en la entrega Frontend. |

Gate final:

```text
[ ] FE-D1–FE-D6 completos
[ ] FE-T1–FE-T5 completos
[ ] FE-C1–FE-C3 completos
[ ] Revisión conjunta Frontend + QA
[ ] Certificación: “INV Frontend alineado con Backend Code Generation Baseline V1”
```

Si un ítem falla, el Frontend INV no está certificado aunque los CREATE
automáticos funcionen.
