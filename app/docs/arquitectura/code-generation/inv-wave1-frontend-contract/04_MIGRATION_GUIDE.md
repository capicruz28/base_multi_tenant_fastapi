# 04 — Guía de migración Frontend

---

## 1. Preparación

1. Fijar como fuente `app/docs/openapi_snapshot.json`.
2. Regenerar el cliente/tipos TypeScript en una rama dedicada o aplicar el delta
   manualmente.
3. Inventariar usos de:
   - `codigo` en los cuatro maestros;
   - `codigo_sku` en Producto;
   - `numero_movimiento`;
   - `numero_inventario`.
4. Clasificar cada uso como Create, Update, Read/List, filtro o presentación.
5. No cambiar rutas ni permisos.

Búsquedas recomendadas en el proyecto React:

```text
codigo:
codigo_sku
numero_movimiento
numero_inventario
required(...)
defaultValues
mutationFn
onSuccess
```

---

## 2. Orden recomendado

### Fase FE-0 — Tipos y utilidades

- Actualizar tipos Create/Update/Read.
- Añadir helper de serialización que omita strings vacíos para campos
  AUTO_DEFAULT.
- Asegurar que el manejador de `onSuccess` usa el response real.
- Preparar manejo común 403/404/409/422.

### Fase FE-1 — Maestros base

Implementar en este orden:

1. Categoría
2. Unidad de medida
3. Tipo de movimiento
4. Almacén

En cada uno:

- quitar `required` del código en CREATE;
- retirar código de UPDATE;
- conservar código en Read/List;
- validar auto + manual + duplicado.

### Fase FE-2 — Producto

Producto depende funcionalmente de Categoría y Unidad de Medida.

- hacer opcional solo `codigo_sku`;
- hacerlo readonly en edición;
- conservar editables `codigo_barra`, `codigo_interno`,
  `codigo_fabricante`;
- validar alta automática antes de continuar.

### Fase FE-3 — Movimiento

Depende de Tipo de movimiento, Almacén, Producto y Unidad de Medida.

- eliminar `numero_movimiento` de Create/Update simple;
- repetir para schemas/flujos `con-detalle`;
- adaptar encabezado/listado;
- validar proceso y estorno.

### Fase FE-4 — Inventario físico

Depende de Almacén, Categoría, Producto y Movimiento.

- eliminar `numero_inventario` de Create/Update simple y embebido;
- adaptar encabezado/listado;
- validar finalizar/aprobar y movimiento de ajuste.

### Fase FE-5 — Regresión integral

- listado y detalle de las siete entidades;
- soft-delete/reactivar de maestros;
- edición BR-IMM;
- cambios de empresa activa;
- flujo cabecera-detalle;
- procesos de Movimiento e Inventario físico.

---

## 3. Ejemplos de tipos

### Maestro AUTO_DEFAULT

```typescript
// Antes
type CategoriaCreate = {
  empresa_id: string;
  codigo: string;
  nombre: string;
};

// Vigente
type CategoriaCreate = {
  empresa_id: string;
  codigo?: string | null;
  nombre: string;
};

type CategoriaUpdate = {
  // codigo no existe
  nombre?: string | null;
};
```

### Documento AUTO_REQUIRED

```typescript
type MovimientoCreate = {
  // numero_movimiento no existe
  empresa_id: string;
  tipo_movimiento_id: string;
  fecha_contable: string;
};

type MovimientoRead = {
  numero_movimiento: string; // required, readonly
  // ...
};
```

### Serialización

```typescript
const payload = {
  ...values,
  codigo: values.codigo?.trim() || undefined,
};
```

Para Movimiento e Inventario físico no serializar el número en absoluto.

---

## 4. Dependencias

| Dependencia | Requisito |
|-------------|-----------|
| Backend INV certificado | Desplegado en ambiente de validación |
| Snapshot vigente | Tipos alineados con `openapi_snapshot.json` |
| Sesión ERP | Empresa activa válida; `empresa_id` coincidente |
| Configuración Motor | Filas cfg sembradas por empresa |
| Permisos | Mismos permisos `inv.*` existentes |
| Datos maestros | Categoría/UM/Tipo/Almacén disponibles antes de documentos |

No existe dependencia Frontend con el módulo administrativo de secuencias.

---

## 5. Validación por recurso

### Maestros AUTO_DEFAULT

1. Crear sin código ⇒ 201 y código no vacío.
2. Crear manual válido ⇒ 201 y response contiene el manual normalizado.
3. Crear manual duplicado ⇒ 409 y no se crea fila.
4. Editar ⇒ payload no contiene campo Motor.
5. Verificar que código no cambia.
6. Desactivar/reactivar ⇒ código se conserva.

### Documentos AUTO_REQUIRED

1. Crear sin número ⇒ 201 y número no vacío.
2. Inspeccionar Network ⇒ request no contiene número.
3. Editar borrador ⇒ PUT no contiene número.
4. Crear con detalles ⇒ mismo comportamiento.
5. Ejecutar procesos ⇒ número original se conserva.
6. Estorno/aprobación ⇒ números derivados vienen del Backend.

### Scope empresa

1. Crear en empresa A y empresa B.
2. Confirmar que la UI envía el `empresa_id` de la sesión activa.
3. No asumir continuidad global entre empresas.

---

## 6. Cómo detectar regresiones

| Señal | Regresión probable |
|-------|--------------------|
| Submit bloqueado por código vacío | Validación legacy required |
| Request contiene `numero_movimiento` | Tipo/form state legacy |
| PUT contiene código readonly | Mapper Update incorrecto |
| Toast muestra código vacío | Se usa payload en vez del response |
| SKU alternativos quedan disabled | BR-IMM aplicado demasiado ampliamente |
| UI muestra número calculado antes del 201 | Generación local prohibida |
| Cambio aparente de código tras PUT pero refresh revierte | Extra ignorado por Backend |
| 404 cfg provoca fallback local | Manejo de error peligroso |

Usar DevTools/Network como evidencia de request y response en los tests de
aceptación.

---

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Tipos generados desactualizados | Build o payload incorrecto | Regenerar desde snapshot vigente |
| Formularios comparten schema Create/Update | Código se filtra al PUT | Separar tipos/mappers |
| Estado optimista usa request | Código vacío en cache | Reemplazar con response 201 |
| Extras legacy se ignoran silenciosamente | Usuario cree que renumeró | Retirar input y payload Update |
| Producto deshabilita todos sus códigos | Pérdida funcional | BR-IMM solo en `codigo_sku` |
| Manual habilitado en documentos | Contrato inválido | No renderizar input |
| FE genera correlativo offline | Colisiones/inconsistencia | Backend como única autoridad |
| Cambio de empresa durante formulario | 403 mismatch | Invalidar/cerrar formulario al cambiar sesión |

---

## 8. Estrategia de despliegue

Los cinco maestros son backward-compatible en CREATE: un Frontend anterior que
envía código manual sigue funcionando. Sin embargo, UPDATE y los dos documentos
requieren migración:

- UPDATE legacy puede ser tolerado como extra, pero no cambia el identificador;
- números legacy en CREATE documental se ignoran.

Por ello, desplegar Frontend alineado inmediatamente después o junto al Backend
certificado. No mantener generación local como fallback.

Rollback Frontend:

- volver temporalmente a enviar código manual en CREATE de maestros es compatible;
- no reintroducir números manuales en Movimiento/Inventario;
- no reintroducir campos Motor en UPDATE.
