# Documentación Frontend — Módulo MFG (Manufactura y Producción)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** MFG - Manufactura y Producción

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
/api/v1/mfg
```

### Dependencias

- **Módulo ORG:** Empresa, sucursal, centro de costo (obligatorio para centros de trabajo y costos).
- **Módulo INV:** Producto, unidad de medida, almacén (obligatorio para BOM, rutas y órdenes de producción).
- **Orden recomendado:** Configurar ORG e INV antes de usar MFG.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Centros de Trabajo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/centros-trabajo | Listar (empresa_id, estado_centro, es_activo, buscar) |
| GET | /api/v1/mfg/centros-trabajo/{centro_trabajo_id} | Detalle |
| POST | /api/v1/mfg/centros-trabajo | Crear centro de trabajo |
| PUT | /api/v1/mfg/centros-trabajo/{centro_trabajo_id} | Actualizar |

Campos principales en creación: empresa_id, codigo, nombre, descripcion, sucursal_id, ubicacion_fisica, tipo_centro, capacidad_horas_dia, capacidad_unidades_hora, eficiencia_promedio, costo_hora_maquina, costo_setup, centro_costo_id, requiere_mantenimiento, frecuencia_mantenimiento_dias, ultima_fecha_mantenimiento, estado_centro (disponible, mantenimiento, ocupado), es_activo.

### 2. Operaciones

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/operaciones | Listar (empresa_id, centro_trabajo_id, es_activo, buscar) |
| GET | /api/v1/mfg/operaciones/{operacion_id} | Detalle |
| POST | /api/v1/mfg/operaciones | Crear operación |
| PUT | /api/v1/mfg/operaciones/{operacion_id} | Actualizar |

Campos principales: empresa_id, codigo, nombre, descripcion, centro_trabajo_id, tiempo_setup_minutos, tiempo_operacion_minutos, requiere_herramientas, requiere_habilidad, requiere_inspeccion, plan_inspeccion_id, es_activo.

### 3. Listas de Materiales (BOM)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/listas-materiales | Listar (empresa_id, producto_id, es_bom_activa, estado, buscar) |
| GET | /api/v1/mfg/listas-materiales/{bom_id} | Detalle |
| POST | /api/v1/mfg/listas-materiales | Crear BOM |
| PUT | /api/v1/mfg/listas-materiales/{bom_id} | Actualizar |

Campos principales: empresa_id, codigo_bom, producto_id, version, fecha_vigencia_desde, fecha_vigencia_hasta, cantidad_base, unidad_medida_id, tipo_bom (produccion, ingenieria), porcentaje_desperdicio, es_bom_activa, estado (borrador, aprobado), aprobado_por_usuario_id, fecha_aprobacion, observaciones.

### 4. Lista de Materiales Detalle (BOM Detalle)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/lista-materiales-detalle | Listar (bom_id) |
| GET | /api/v1/mfg/lista-materiales-detalle/{bom_detalle_id} | Detalle |
| POST | /api/v1/mfg/lista-materiales-detalle | Crear línea BOM |
| PUT | /api/v1/mfg/lista-materiales-detalle/{bom_detalle_id} | Actualizar |

Campos principales: bom_id, producto_componente_id, cantidad, unidad_medida_id, tipo_componente (material, semielaborado), es_critico, porcentaje_desperdicio, tiene_sustitutos, productos_sustitutos, secuencia, observaciones.

### 5. Rutas de Fabricación

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/rutas-fabricacion | Listar (empresa_id, producto_id, es_ruta_activa, estado, buscar) |
| GET | /api/v1/mfg/rutas-fabricacion/{ruta_id} | Detalle |
| POST | /api/v1/mfg/rutas-fabricacion | Crear ruta |
| PUT | /api/v1/mfg/rutas-fabricacion/{ruta_id} | Actualizar |

Campos principales: empresa_id, codigo_ruta, producto_id, bom_id, nombre, descripcion, version, tiempo_total_setup_minutos, tiempo_total_operacion_minutos, es_ruta_activa, estado (borrador, aprobado).

### 6. Ruta de Fabricación Detalle

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/ruta-fabricacion-detalle | Listar (ruta_id) |
| GET | /api/v1/mfg/ruta-fabricacion-detalle/{ruta_detalle_id} | Detalle |
| POST | /api/v1/mfg/ruta-fabricacion-detalle | Crear paso de ruta |
| PUT | /api/v1/mfg/ruta-fabricacion-detalle/{ruta_detalle_id} | Actualizar |

Campos principales: ruta_id, secuencia, operacion_id, centro_trabajo_id, tiempo_setup_minutos, tiempo_operacion_minutos, es_operacion_critica, permite_operaciones_paralelas, instrucciones.

### 7. Órdenes de Producción

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/ordenes-produccion | Listar (empresa_id, producto_id, estado, fecha_desde, fecha_hasta) |
| GET | /api/v1/mfg/ordenes-produccion/{orden_produccion_id} | Detalle |
| POST | /api/v1/mfg/ordenes-produccion | Crear orden de producción |
| PUT | /api/v1/mfg/ordenes-produccion/{orden_produccion_id} | Actualizar |

Campos principales: empresa_id, numero_op, fecha_emision, fecha_inicio_programada, fecha_fin_programada, producto_id, bom_id, ruta_fabricacion_id, cantidad_planeada, cantidad_producida, cantidad_defectuosa, unidad_medida_id, almacen_destino_id, prioridad (1-4), tipo_orden (normal, urgente), costo_materiales, costo_mano_obra, costo_cif, moneda, centro_costo_id, estado (borrador, liberada, en_proceso, terminada), responsable_usuario_id, responsable_nombre, observaciones.

### 8. Orden de Producción Operaciones

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/orden-produccion-operaciones | Listar (orden_produccion_id, centro_trabajo_id, estado) |
| GET | /api/v1/mfg/orden-produccion-operaciones/{op_operacion_id} | Detalle |
| POST | /api/v1/mfg/orden-produccion-operaciones | Crear operación en OP |
| PUT | /api/v1/mfg/orden-produccion-operaciones/{op_operacion_id} | Actualizar (avance, tiempos reales) |

Campos principales: orden_produccion_id, ruta_detalle_id, operacion_id, centro_trabajo_id, secuencia, tiempo_setup_planificado_minutos, tiempo_operacion_planificado_minutos, tiempo_setup_real_minutos, tiempo_operacion_real_minutos, fecha_inicio_programada, fecha_fin_programada, fecha_inicio_real, fecha_fin_real, cantidad_procesada, cantidad_aprobada, cantidad_rechazada, operario_usuario_id, operario_nombre, estado (pendiente, en_proceso, terminada), observaciones.

### 9. Consumo de Materiales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mfg/consumo-materiales | Listar (orden_produccion_id, producto_id) |
| GET | /api/v1/mfg/consumo-materiales/{consumo_id} | Detalle |
| POST | /api/v1/mfg/consumo-materiales | Registrar consumo |
| PUT | /api/v1/mfg/consumo-materiales/{consumo_id} | Actualizar |

Campos principales: orden_produccion_id, producto_id, cantidad_planificada, cantidad_consumida, unidad_medida_id, lote, almacen_origen_id, costo_unitario, movimiento_inventario_id, observaciones.

---

## Schemas TypeScript

### Centro de Trabajo

```typescript
interface CentroTrabajoCreate {
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  sucursal_id?: string;
  ubicacion_fisica?: string;
  tipo_centro: string;
  capacidad_horas_dia?: number;
  capacidad_unidades_hora?: number;
  eficiencia_promedio?: number;
  costo_hora_maquina?: number;
  costo_setup?: number;
  centro_costo_id?: string;
  requiere_mantenimiento?: boolean;
  frecuencia_mantenimiento_dias?: number;
  ultima_fecha_mantenimiento?: string;
  estado_centro?: string;
  es_activo?: boolean;
}

interface CentroTrabajoRead extends CentroTrabajoCreate {
  centro_trabajo_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Operación

```typescript
interface OperacionCreate {
  empresa_id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  centro_trabajo_id?: string;
  tiempo_setup_minutos?: number;
  tiempo_operacion_minutos?: number;
  requiere_herramientas?: string;
  requiere_habilidad?: string;
  requiere_inspeccion?: boolean;
  plan_inspeccion_id?: string;
  es_activo?: boolean;
}

interface OperacionRead extends OperacionCreate {
  operacion_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Lista de Materiales (BOM)

```typescript
interface ListaMaterialesCreate {
  empresa_id: string;
  codigo_bom: string;
  producto_id: string;
  version?: string;
  fecha_vigencia_desde: string;
  fecha_vigencia_hasta?: string;
  cantidad_base?: number;
  unidad_medida_id: string;
  tipo_bom?: string;
  porcentaje_desperdicio?: number;
  es_bom_activa?: boolean;
  estado?: string;
  aprobado_por_usuario_id?: string;
  fecha_aprobacion?: string;
  observaciones?: string;
}

interface ListaMaterialesRead extends ListaMaterialesCreate {
  bom_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Lista Materiales Detalle

```typescript
interface ListaMaterialesDetalleCreate {
  bom_id: string;
  producto_componente_id: string;
  cantidad: number;
  unidad_medida_id: string;
  tipo_componente?: string;
  es_critico?: boolean;
  porcentaje_desperdicio?: number;
  tiene_sustitutos?: boolean;
  productos_sustitutos?: string;
  secuencia?: number;
  observaciones?: string;
}

interface ListaMaterialesDetalleRead extends ListaMaterialesDetalleCreate {
  bom_detalle_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Ruta de Fabricación

```typescript
interface RutaFabricacionCreate {
  empresa_id: string;
  codigo_ruta: string;
  producto_id: string;
  bom_id?: string;
  nombre: string;
  descripcion?: string;
  version?: string;
  tiempo_total_setup_minutos?: number;
  tiempo_total_operacion_minutos?: number;
  es_ruta_activa?: boolean;
  estado?: string;
}

interface RutaFabricacionRead extends RutaFabricacionCreate {
  ruta_id: string;
  cliente_id: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Ruta Fabricación Detalle

```typescript
interface RutaFabricacionDetalleCreate {
  ruta_id: string;
  secuencia: number;
  operacion_id: string;
  centro_trabajo_id: string;
  tiempo_setup_minutos?: number;
  tiempo_operacion_minutos?: number;
  es_operacion_critica?: boolean;
  permite_operaciones_paralelas?: boolean;
  instrucciones?: string;
}

interface RutaFabricacionDetalleRead extends RutaFabricacionDetalleCreate {
  ruta_detalle_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Orden de Producción

```typescript
interface OrdenProduccionCreate {
  empresa_id: string;
  numero_op: string;
  fecha_emision?: string;
  fecha_inicio_programada: string;
  fecha_fin_programada: string;
  producto_id: string;
  bom_id: string;
  ruta_fabricacion_id?: string;
  cantidad_planeada: number;
  cantidad_producida?: number;
  cantidad_defectuosa?: number;
  unidad_medida_id: string;
  almacen_destino_id?: string;
  prioridad?: number;
  tipo_orden?: string;
  documento_origen_tipo?: string;
  documento_origen_id?: string;
  costo_materiales?: number;
  costo_mano_obra?: number;
  costo_cif?: number;
  moneda?: string;
  centro_costo_id?: string;
  estado?: string;
  responsable_usuario_id?: string;
  responsable_nombre?: string;
  observaciones?: string;
}

interface OrdenProduccionRead extends OrdenProduccionCreate {
  orden_produccion_id: string;
  cliente_id: string;
  fecha_inicio_real?: string;
  fecha_fin_real?: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
  usuario_creacion_id?: string;
}
```

### Orden Producción Operación

```typescript
interface OrdenProduccionOperacionCreate {
  orden_produccion_id: string;
  ruta_detalle_id?: string;
  operacion_id: string;
  centro_trabajo_id: string;
  secuencia: number;
  tiempo_setup_planificado_minutos?: number;
  tiempo_operacion_planificado_minutos?: number;
  tiempo_setup_real_minutos?: number;
  tiempo_operacion_real_minutos?: number;
  fecha_inicio_programada?: string;
  fecha_fin_programada?: string;
  fecha_inicio_real?: string;
  fecha_fin_real?: string;
  cantidad_procesada?: number;
  cantidad_aprobada?: number;
  cantidad_rechazada?: number;
  operario_usuario_id?: string;
  operario_nombre?: string;
  estado?: string;
  observaciones?: string;
}

interface OrdenProduccionOperacionRead extends OrdenProduccionOperacionCreate {
  op_operacion_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Consumo Materiales

```typescript
interface ConsumoMaterialesCreate {
  orden_produccion_id: string;
  producto_id: string;
  cantidad_planificada: number;
  cantidad_consumida: number;
  unidad_medida_id: string;
  lote?: string;
  almacen_origen_id?: string;
  costo_unitario?: number;
  movimiento_inventario_id?: string;
  observaciones?: string;
}

interface ConsumoMaterialesRead extends ConsumoMaterialesCreate {
  consumo_id: string;
  cliente_id: string;
  fecha_consumo: string;
  usuario_registro_id?: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (centro, operación, BOM, ruta, OP, etc.) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/mfg
  /centros-trabajo
    /list
    /create
    /:id/edit
  /operaciones
    /list
    /create
    /:id/edit
  /listas-materiales
    /list
    /create
    /:id/edit
    /:id/detalle          # Líneas BOM (lista-materiales-detalle?bom_id=)
  /rutas-fabricacion
    /list
    /create
    /:id/edit
    /:id/detalle          # Pasos de ruta (ruta-fabricacion-detalle?ruta_id=)
  /ordenes-produccion
    /list
    /create
    /:id/edit
    /:id/operaciones      # Operaciones de OP (orden-produccion-operaciones?orden_produccion_id=)
    /:id/consumo          # Consumo materiales (consumo-materiales?orden_produccion_id=)
  /consumo-materiales
    /list
```

---

## Flujo de Implementación Recomendado

### 1. Configuración ORG e INV

- Tener empresas, sucursales, centros de costo (ORG) y productos, unidades de medida, almacenes (INV) antes de usar MFG.

### 2. Centros de Trabajo y Operaciones

- Crear centros de trabajo (máquinas/estaciones): POST /mfg/centros-trabajo.
- Crear operaciones (corte, armado, empaque, etc.) vinculadas a centro: POST /mfg/operaciones.

### 3. Lista de Materiales (BOM)

- Crear BOM por producto terminado: POST /mfg/listas-materiales (producto_id, cantidad_base, unidad_medida_id, vigencia).
- Agregar componentes: POST /mfg/lista-materiales-detalle (bom_id, producto_componente_id, cantidad, tipo_componente).

### 4. Rutas de Fabricación

- Crear ruta por producto: POST /mfg/rutas-fabricacion (producto_id, bom_id opcional).
- Agregar pasos en secuencia: POST /mfg/ruta-fabricacion-detalle (ruta_id, secuencia, operacion_id, centro_trabajo_id, tiempos).

### 5. Órdenes de Producción

- Crear OP: POST /mfg/ordenes-produccion (numero_op, producto_id, bom_id, ruta_fabricacion_id, cantidad_planeada, fechas, almacen_destino_id).
- Liberar: PUT con estado "liberada".
- Registrar operaciones de la OP: POST /mfg/orden-produccion-operaciones (orden_produccion_id, operacion_id, centro_trabajo_id, secuencia); actualizar con tiempos reales y cantidad procesada/aprobada/rechazada.
- Registrar consumo: POST /mfg/consumo-materiales (orden_produccion_id, producto_id, cantidad_planificada, cantidad_consumida). Opcional: integrar con INV para generar movimiento de salida.

### 6. Cierre de OP

- Actualizar OP: cantidad_producida, cantidad_defectuosa, fecha_fin_real, estado "terminada", costos (materiales, MO, CIF).

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **BOM – producto:** El `producto_id` en lista_materiales es el producto terminado; en detalle, `producto_componente_id` es el componente (material o semielaborado). Soporta BOM multinivel si el componente a su vez tiene BOM.

3. **Ruta – BOM:** La ruta puede vincularse a un `bom_id` opcional; la OP requiere tanto `bom_id` como `ruta_fabricacion_id` para materiales y secuencia de operaciones.

4. **Estados OP:** borrador → liberada → en_proceso → terminada. Solo en estado apropiado se deben registrar operaciones y consumo.

5. **Consumo e inventario:** El campo `movimiento_inventario_id` en consumo_materiales permite vincular a un movimiento de salida de INV; la generación del movimiento puede hacerse en backend o frontend según reglas de negocio.

6. **IDs en URLs:** Los identificadores son UUID; usar centro_trabajo_id, operacion_id, bom_id, bom_detalle_id, ruta_id, ruta_detalle_id, orden_produccion_id, op_operacion_id, consumo_id según el recurso.

---

**Fin de la documentación del módulo MFG**
