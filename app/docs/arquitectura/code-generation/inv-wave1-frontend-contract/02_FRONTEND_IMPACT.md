# 02 — Impacto en Frontend React

Este documento describe responsabilidades funcionales. Los nombres concretos de
componentes y hooks deben mapearse a la estructura real del proyecto React; el
Backend no prescribe nombres de archivos Frontend.

---

## 1. Cambios transversales obligatorios

| Área React | Cambio |
|------------|--------|
| Tipos/API client | Regenerar desde snapshot o aplicar el delta de `01_OPENAPI_CHANGES.md`. |
| Validación | Eliminar `required` de códigos AUTO_DEFAULT; eliminar números AUTO_REQUIRED. |
| Serialización | Omitir claves vacías/readonly; nunca construir correlativos. |
| Mutations CREATE | Usar el objeto retornado por el `201` como fuente del identificador. |
| Mutations UPDATE | Excluir explícitamente el campo Motor del payload. |
| Estado/cache | Reemplazar/insertar cache con response servidor, no con payload optimista sin código. |
| Errores | Mapear 409 al campo manual; 404 cfg a error técnico; 403 a sesión/RBAC. |

No se debe realizar alta optimista que invente temporalmente un código definitivo.

---

## 2. Categoría

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta, edición, detalle y listado de categorías |
| Componentes | Formulario categoría; campo código; columna código; confirmación de alta |
| Hooks | Mutation CREATE/UPDATE; adaptación de payload y cache post-201 |
| Formularios | CREATE `codigo` opcional; UPDATE código readonly y fuera del payload |
| Tablas | Sin cambio estructural; mantener columna `codigo` |
| Validaciones | Quitar required; conservar `maxLength=20` si se habilita manual |

---

## 3. Unidad de medida

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta, edición, detalle y listado de unidades |
| Componentes | Formulario unidad; campo código; columna código |
| Hooks | CREATE/UPDATE y cache |
| Formularios | CREATE opcional; UPDATE readonly |
| Tablas | Columna `codigo` sin cambio |
| Validaciones | Quitar required; conservar `maxLength=10` para manual |

---

## 4. Tipo de movimiento

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta, edición, detalle y listado de tipos |
| Componentes | Formulario tipo; campo/columna código |
| Hooks | CREATE/UPDATE y cache |
| Formularios | CREATE opcional; UPDATE readonly |
| Tablas | Columna `codigo` sin cambio |
| Validaciones | Quitar required; conservar `maxLength=20` para manual |

No confundir `TipoMovimiento.codigo` (maestro AUTO_DEFAULT) con
`Movimiento.numero_movimiento` (documento AUTO_REQUIRED).

---

## 5. Almacén

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta, edición, detalle y listado de almacenes |
| Componentes | Formulario almacén; campo/columna código |
| Hooks | CREATE/UPDATE y cache |
| Formularios | CREATE opcional; UPDATE readonly |
| Tablas | Columna `codigo` sin cambio |
| Validaciones | Quitar required; conservar `maxLength=20` para manual |

Selectores de sucursal y centro de costo no cambian.

---

## 6. Producto

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta, edición, detalle y listado de productos |
| Componentes | Campo SKU; códigos alternativos; columna SKU |
| Hooks | CREATE/UPDATE y cache |
| Formularios | `codigo_sku` opcional en CREATE y readonly en UPDATE |
| Tablas | Columna `codigo_sku` sin cambio |
| Validaciones | Quitar required de SKU; conservar `maxLength=50` para manual |

Sin cambios en:

- `codigo_barra`
- `codigo_interno`
- `codigo_fabricante`

Estos tres campos continúan editables. No aplicarles BR-IMM.

---

## 7. Movimiento

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta simple, alta cabecera-detalle, edición borrador, detalle, listado, estorno |
| Componentes | Formulario cabecera; formulario embebido; encabezado del documento; columna número |
| Hooks | CREATE simple y `con-detalle`; UPDATE; estorno; cache |
| Formularios | Eliminar `numero_movimiento` de CREATE y UPDATE |
| Tablas | Mantener columna `numero_movimiento` |
| Validaciones | Eliminar validación required/formato del número |

El mutation hook debe tomar `numero_movimiento` del response. En estorno, el
Frontend tampoco construye el número del movimiento compensatorio.

---

## 8. Inventario físico

| Elemento | Impacto |
|----------|---------|
| Pantallas | Alta simple, alta con conteos, edición, detalle, listado, aprobación |
| Componentes | Formulario cabecera; formulario embebido; encabezado; columna número |
| Hooks | CREATE simple y `con-detalle`; UPDATE; aprobar; cache |
| Formularios | Eliminar `numero_inventario` de CREATE y UPDATE |
| Tablas | Mantener columna `numero_inventario` |
| Validaciones | Eliminar validación required/formato del número |

La aprobación puede generar un movimiento de ajuste en Backend. No agregar un
campo de número de movimiento al formulario de aprobación.

---

## 9. Clasificación de cambios

### Obligatorios

- Actualizar los siete tipos CREATE y UPDATE.
- Retirar código/número de todos los payloads UPDATE.
- Retirar números AUTO_REQUIRED de los payloads CREATE.
- Permitir omitir código/SKU en los cinco CREATE AUTO_DEFAULT.
- Consumir y mostrar el identificador de la respuesta.
- Corregir tests que todavía esperen generación Frontend.

### Opcionales

- Ocultar el input AUTO_DEFAULT en alta estándar.
- Sección colapsada «Código manual» para implantación.
- Texto informativo «Se asignará al guardar».
- Toast con el código/número retornado.

Estas opciones no aplican a Movimiento ni Inventario físico: sus números no son
entrada manual.

### Sin cambios

- Rutas REST y permisos RBAC.
- Selección de empresa operativa y `empresa_id`.
- Listados, filtros y columnas de identificador.
- Soft-delete/reactivar de maestros.
- Flujo de estados y acciones de proceso.
- Detalles embebidos de Movimiento e Inventario físico.
- Códigos alternativos de Producto.
