# Documentación Frontend — Módulo MRP (Planeamiento de Materiales)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** MRP - Material Requirements Planning (Planeamiento de Materiales)

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## Información General

### Base URL

```
/api/v1/mrp
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio para plan maestro).
- **Módulo INV:** Producto, unidad de medida (obligatorio para necesidades, explosión y órdenes sugeridas).
- **Módulo MFG:** Listas de materiales / BOM (necesario para calcular la explosión de materiales).
- **Módulo PUR:** Proveedor (opcional; para sugerir proveedor en órdenes de compra).
- **Orden recomendado:** Configurar ORG, INV y MFG (BOM) antes de usar MRP.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Plan Maestro MRP

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mrp/plan-maestro | Listar (empresa_id, estado, buscar) |
| GET | /api/v1/mrp/plan-maestro/{plan_maestro_id} | Detalle |
| POST | /api/v1/mrp/plan-maestro | Crear plan maestro |
| PUT | /api/v1/mrp/plan-maestro/{plan_maestro_id} | Actualizar |

Campos principales en creación: empresa_id, codigo_plan, nombre, descripcion, fecha_inicio, fecha_fin, tipo_periodo (diario, semanal, mensual), horizonte_planificacion_dias, punto_reorden_dias, estado (borrador, calculado, aprobado, ejecutado, cerrado), observaciones.

### 2. Necesidades Brutas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mrp/necesidades-brutas | Listar (plan_maestro_id, producto_id, origen) |
| GET | /api/v1/mrp/necesidades-brutas/{necesidad_id} | Detalle |
| POST | /api/v1/mrp/necesidades-brutas | Crear necesidad bruta |
| PUT | /api/v1/mrp/necesidades-brutas/{necesidad_id} | Actualizar |

Campos principales: plan_maestro_id, producto_id, fecha_requerida, cantidad_requerida, unidad_medida_id, origen (pedido_venta, pronostico, stock_seguridad, orden_produccion), documento_origen_id, documento_origen_numero, prioridad.

### 3. Explosión de Materiales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mrp/explosion-materiales | Listar (plan_maestro_id, producto_componente_id, nivel_bom) |
| GET | /api/v1/mrp/explosion-materiales/{explosion_id} | Detalle |
| POST | /api/v1/mrp/explosion-materiales | Crear línea de explosión (manual o resultado de proceso) |
| PUT | /api/v1/mrp/explosion-materiales/{explosion_id} | Actualizar (p. ej. stocks) |

Campos principales: plan_maestro_id, producto_padre_id, necesidad_padre_id, producto_componente_id, bom_detalle_id, nivel_bom, cantidad_necesaria, unidad_medida_id, fecha_requerida, stock_actual, stock_reservado, stock_transito. La respuesta incluye **stock_disponible** y **cantidad_a_ordenar** calculados (stock_disponible = stock_actual - stock_reservado + stock_transito; cantidad_a_ordenar = max(0, cantidad_necesaria - stock_disponible)).

### 4. Órdenes Sugeridas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mrp/ordenes-sugeridas | Listar (plan_maestro_id, producto_id, estado, tipo_orden) |
| GET | /api/v1/mrp/ordenes-sugeridas/{orden_sugerida_id} | Detalle |
| POST | /api/v1/mrp/ordenes-sugeridas | Crear orden sugerida |
| PUT | /api/v1/mrp/ordenes-sugeridas/{orden_sugerida_id} | Actualizar (estado, documento generado al convertir) |

Campos principales: plan_maestro_id, producto_id, tipo_orden (compra, produccion, transferencia), cantidad_sugerida, unidad_medida_id, fecha_requerida, fecha_orden_sugerida, explosion_materiales_id, proveedor_sugerido_id, lead_time_dias, estado (sugerida, aprobada, convertida, rechazada), documento_generado_tipo (orden_compra, orden_produccion), documento_generado_id, fecha_conversion, observaciones.

---

## Schemas TypeScript

### Plan Maestro MRP

```typescript
interface PlanMaestroCreate {
  empresa_id: string;
  codigo_plan: string;
  nombre: string;
  descripcion?: string;
  fecha_inicio: string;  // YYYY-MM-DD
  fecha_fin: string;
  tipo_periodo?: 'diario' | 'semanal' | 'mensual';
  horizonte_planificacion_dias?: number;
  punto_reorden_dias?: number;
  estado?: string;
  observaciones?: string;
}

interface PlanMaestroRead extends PlanMaestroCreate {
  plan_maestro_id: string;
  cliente_id: string;
  fecha_calculo?: string;
  fecha_aprobacion?: string;
  total_productos_planificados?: number;
  total_requisiciones_generadas?: number;
  total_ordenes_sugeridas?: number;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Necesidad Bruta

```typescript
interface NecesidadBrutaCreate {
  plan_maestro_id: string;
  producto_id: string;
  fecha_requerida: string;
  cantidad_requerida: number;
  unidad_medida_id: string;
  origen: 'pedido_venta' | 'pronostico' | 'stock_seguridad' | 'orden_produccion';
  documento_origen_id?: string;
  documento_origen_numero?: string;
  prioridad?: number;
}

interface NecesidadBrutaRead extends NecesidadBrutaCreate {
  necesidad_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Explosión Materiales

```typescript
interface ExplosionMaterialesCreate {
  plan_maestro_id: string;
  producto_padre_id: string;
  necesidad_padre_id?: string;
  producto_componente_id: string;
  bom_detalle_id?: string;
  nivel_bom?: number;
  cantidad_necesaria: number;
  unidad_medida_id: string;
  fecha_requerida: string;
  stock_actual?: number;
  stock_reservado?: number;
  stock_transito?: number;
}

interface ExplosionMaterialesRead extends ExplosionMaterialesCreate {
  explosion_id: string;
  cliente_id: string;
  stock_disponible?: number;   // calculado: actual - reservado + transito
  cantidad_a_ordenar?: number; // calculado: max(0, necesaria - stock_disponible)
  fecha_calculo: string;
}
```

### Orden Sugerida

```typescript
interface OrdenSugeridaCreate {
  plan_maestro_id: string;
  producto_id: string;
  tipo_orden: 'compra' | 'produccion' | 'transferencia';
  cantidad_sugerida: number;
  unidad_medida_id: string;
  fecha_requerida: string;
  fecha_orden_sugerida: string;
  explosion_materiales_id?: string;
  proveedor_sugerido_id?: string;
  lead_time_dias?: number;
  estado?: string;
  observaciones?: string;
}

interface OrdenSugeridaRead extends OrdenSugeridaCreate {
  orden_sugerida_id: string;
  cliente_id: string;
  documento_generado_tipo?: string;
  documento_generado_id?: string;
  fecha_conversion?: string;
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (plan maestro, necesidad, explosión, orden sugerida) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/mrp
  /plan-maestro
    /list
    /create
    /:id/edit
    /:id/necesidades    # Necesidades brutas (necesidades-brutas?plan_maestro_id=)
    /:id/explosion      # Explosión (explosion-materiales?plan_maestro_id=)
    /:id/ordenes-sugeridas  # Órdenes sugeridas (ordenes-sugeridas?plan_maestro_id=)
  /necesidades-brutas
    /list
    /create
    /:id/edit
  /explosion-materiales
    /list
    /:id
  /ordenes-sugeridas
    /list
    /:id/edit
    /:id/convertir      # Flujo: abrir modal y crear OC o OP desde sugerida
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa), INV (productos, unidades de medida) y MFG (BOM por producto) configurados.

### 2. Plan Maestro

- Crear plan maestro: POST /mrp/plan-maestro (codigo_plan, nombre, fecha_inicio, fecha_fin, tipo_periodo, horizonte_planificacion_dias).
- Estados típicos: borrador → (al ejecutar cálculo) calculado → aprobado → ejecutado → cerrado.

### 3. Necesidades Brutas

- Cargar necesidades por plan: POST /mrp/necesidades-brutas (plan_maestro_id, producto_id, fecha_requerida, cantidad_requerida, unidad_medida_id, origen).
- Origen: pedido_venta (documento_origen_id puede ser pedido_id), pronostico (desde MPS), stock_seguridad, orden_produccion.
- El frontend puede ofrecer “importar desde pedidos” o “desde pronóstico MPS” llamando a otros módulos y luego creando necesidades brutas.

### 4. Explosión de Materiales

- La explosión suele ser un **proceso batch en backend** (no solo CRUD): a partir del plan y las necesidades brutas, el sistema recorre las BOM y genera líneas en mrp_explosion_materiales. Este módulo expone GET/POST/PUT para consultar, crear o ajustar líneas.
- Listar explosión por plan: GET /mrp/explosion-materiales?plan_maestro_id=...
- Cada línea devuelve stock_disponible y cantidad_a_ordenar; usar cantidad_a_ordenar para generar órdenes sugeridas.

### 5. Órdenes Sugeridas

- Listar sugeridas por plan: GET /mrp/ordenes-sugeridas?plan_maestro_id=...&estado=sugerida.
- El usuario puede aprobar (PUT con estado=aprobada) o convertir: crear en PUR una orden de compra o en MFG una orden de producción y luego PUT orden_sugerida con documento_generado_tipo, documento_generado_id, fecha_conversion y estado=convertida.

### 6. Cierre del plan

- Actualizar plan maestro con totales y estado (calculado, aprobado, ejecutado, cerrado) según reglas de negocio.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Explosión:** El cálculo real de explosión (recorrer BOM multinivel y rellenar mrp_explosion_materiales) normalmente se implementa como un **job o endpoint de proceso** en el backend; los endpoints CRUD permiten consultar y mantener los resultados. Si el backend ofrece un endpoint tipo POST /mrp/plan-maestro/{id}/ejecutar-explosion, el frontend lo invoca después de cargar necesidades brutas.

3. **Órdenes sugeridas:** Pueden generarse automáticamente desde la explosión (cantidad_a_ordenar) en backend; el frontend lista, filtra y permite convertir en OC (PUR) o OP (MFG).

4. **IDs en URLs:** Usar plan_maestro_id, necesidad_id, explosion_id, orden_sugerida_id según el recurso; todos son UUID.

5. **Origen de necesidad:** Mantener documento_origen_id y documento_origen_numero para trazabilidad (p. ej. enlace al pedido de venta o al pronóstico MPS).

---

**Fin de la documentación del módulo MRP**
