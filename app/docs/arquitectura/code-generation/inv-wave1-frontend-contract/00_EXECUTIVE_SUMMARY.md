# INV Wave 1 — Contrato oficial Frontend

**Contrato:** INV Frontend Contract v1.0.0  
**Fecha:** 2026-07-17  
**Estado Backend:** **CERTIFICADO** respecto al Motor de Códigos  
**Audiencia:** proyecto Frontend React + QA  
**Autoridad:** paquete definitivo para iniciar la adaptación Frontend de INV Wave 1

---

## 1. Alcance

INV Wave 1 comprende siete recursos company-scoped:

| Recurso | `sequence_key` | Campo | Policy | Formato automático |
|---------|----------------|-------|--------|--------------------|
| Categoría | `inv_categoria_producto` | `codigo` | AUTO_DEFAULT | `CAT` + 3 dígitos |
| Unidad de medida | `inv_unidad_medida` | `codigo` | AUTO_DEFAULT | `UM` + 3 dígitos |
| Tipo de movimiento | `inv_tipo_movimiento` | `codigo` | AUTO_DEFAULT | `TM` + 3 dígitos |
| Almacén | `inv_almacen` | `codigo` | AUTO_DEFAULT | `ALM` + 3 dígitos |
| Producto | `inv_producto` | `codigo_sku` | AUTO_DEFAULT | `P` + 5 dígitos |
| Movimiento | `inv_movimiento` | `numero_movimiento` | AUTO_REQUIRED | `MOV` + 6 dígitos |
| Inventario físico | `inv_inventario_fisico` | `numero_inventario` | AUTO_REQUIRED | `IF` + 5 dígitos |

Todos los contadores son por empresa operativa. El Frontend debe conservar
`empresa_id` en los cuerpos que lo exigen y enviarlo igual a la empresa activa de
la sesión ERP.

---

## 2. Cambio contractual central

| Familia | CREATE | UPDATE | READ / LIST |
|---------|--------|--------|-------------|
| Cinco maestros AUTO_DEFAULT | Código opcional. Omitido/`null`/vacío ⇒ Backend genera. Manual válido y único ⇒ Backend acepta. | Campo Motor ausente; no enviarlo. | Código requerido, definitivo y siempre presente. |
| Movimiento e inventario físico AUTO_REQUIRED | Número ausente del request; Backend siempre genera. | Número ausente; BR-IMM. | Número requerido, definitivo y siempre presente. |

El Frontend no calcula correlativos, no reserva números, no consulta directamente
`cfg_codigo_secuencia` y no intenta modificar un identificador después del alta.

---

## 3. Estado de certificación y referencias

- Backend INV Wave 1: **cerrado y certificado**, según declaración de cierre del proyecto.
- Norma obligatoria:
  `app/docs/arquitectura/code-generation/baseline-v1/`.
- Golden Reference:
  `app/docs/arquitectura/codigo-generation-wave1/frontend-contract/` (ORG).
- Contrato máquina vigente:
  `app/docs/openapi_snapshot.json`.
- Snapshot vigente: OpenAPI **3.1.0**, API `Service API` versión **0.1.0**.

Ante una diferencia:

1. `openapi_snapshot.json` define la forma exacta de requests y responses.
2. Baseline V1 define la semántica CREATE y BR-IMM.
3. Este paquete define la adaptación oficial React para INV.

---

## 4. Consecuencias para React

Cambios obligatorios:

1. Regenerar o ajustar tipos TypeScript desde el snapshot vigente.
2. Hacer opcionales los códigos de los cinco maestros en los tipos CREATE.
3. Eliminar `numero_movimiento` y `numero_inventario` de los tipos CREATE.
4. Eliminar todos los campos Motor de los tipos UPDATE.
5. Consumir el identificador definitivo de la respuesta `201`.
6. No enviar campos readonly aunque permanezcan visibles en edición.

Cambios opcionales:

- Ocultar el código AUTO_DEFAULT en el alta estándar.
- Ofrecer entrada manual en una sección avanzada.
- Mostrar confirmación con el código/número retornado.

Sin cambios:

- Rutas, permisos RBAC, empresa de sesión, columnas de listado y tipos Read.
- Otros identificadores de Producto (`codigo_barra`, `codigo_interno`,
  `codigo_fabricante`) siguen siendo campos editables y no pertenecen al Motor.

---

## 5. Índice

| Documento | Propósito |
|-----------|-----------|
| `01_OPENAPI_CHANGES.md` | Delta contractual exacto por endpoint |
| `02_FRONTEND_IMPACT.md` | Impacto React por recurso |
| `03_FORMS_BEHAVIOR.md` | Guía funcional CREATE / UPDATE / LIST |
| `04_MIGRATION_GUIDE.md` | Secuencia de migración y validación |
| `05_IMPLEMENTATION_CHECKLIST.md` | Gate de certificación Frontend |

Este directorio es el único contexto funcional necesario para iniciar la
implementación Frontend de INV Wave 1.
