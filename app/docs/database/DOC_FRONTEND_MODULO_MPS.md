# Documentación Frontend — Módulo MPS (Plan Maestro de Producción)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** MPS - Master Production Schedule (Plan Maestro de Producción)

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
/api/v1/mps
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Módulo INV:** Producto, unidad de medida (obligatorio).
- **Orden recomendado:** Configurar ORG e INV antes de usar MPS. Los pronósticos y planes alimentan a **MRP** (necesidades brutas).

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Pronóstico de Demanda

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mps/pronostico-demanda | Listar (empresa_id, producto_id, anio, mes) |
| GET | /api/v1/mps/pronostico-demanda/{pronostico_id} | Detalle |
| POST | /api/v1/mps/pronostico-demanda | Crear pronóstico |
| PUT | /api/v1/mps/pronostico-demanda/{pronostico_id} | Actualizar |

Campos principales en creación: empresa_id, producto_id, **anio** (número, ej. 2026), mes (1-12), semana (opcional), fecha_inicio, fecha_fin, cantidad_pronosticada, unidad_medida_id, metodo_pronostico (historico, tendencia, estacional, manual), confiabilidad_porcentaje, cantidad_real (para análisis), observaciones.  
La respuesta incluye **desviacion** (cantidad_real - cantidad_pronosticada) cuando existe cantidad_real.

### 2. Plan de Producción

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mps/plan-produccion | Listar (empresa_id, estado, buscar) |
| GET | /api/v1/mps/plan-produccion/{plan_produccion_id} | Detalle |
| POST | /api/v1/mps/plan-produccion | Crear plan |
| PUT | /api/v1/mps/plan-produccion/{plan_produccion_id} | Actualizar |

Campos principales: empresa_id, codigo_plan, nombre, fecha_inicio, fecha_fin, estado (borrador, aprobado, ejecutado, cerrado), fecha_aprobacion, aprobado_por_usuario_id, observaciones.

### 3. Plan de Producción Detalle

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/mps/plan-produccion-detalle | Listar (plan_produccion_id, producto_id) |
| GET | /api/v1/mps/plan-produccion-detalle/{plan_detalle_id} | Detalle |
| POST | /api/v1/mps/plan-produccion-detalle | Crear línea (producto + periodo) |
| PUT | /api/v1/mps/plan-produccion-detalle/{plan_detalle_id} | Actualizar |

Campos principales: plan_produccion_id, producto_id, fecha_inicio, fecha_fin, pronostico_demanda, pedidos_firmes, stock_inicial, stock_seguridad, cantidad_planificada, cantidad_producida, unidad_medida_id, capacidad_disponible, observaciones.  
La respuesta incluye **porcentaje_uso_capacidad** calculado (cantidad_planificada / capacidad_disponible * 100 cuando capacidad_disponible > 0).

---

## Schemas TypeScript

### Pronóstico Demanda

```typescript
interface PronosticoDemandaCreate {
  empresa_id: string;
  producto_id: string;
  anio: number;  // 2000-2100, en API se usa "anio" (no "año")
  mes: number;  // 1-12
  semana?: number;
  fecha_inicio: string;
  fecha_fin: string;
  cantidad_pronosticada: number;
  unidad_medida_id: string;
  metodo_pronostico?: 'historico' | 'tendencia' | 'estacional' | 'manual';
  confiabilidad_porcentaje?: number;
  cantidad_real?: number;
  observaciones?: string;
}

interface PronosticoDemandaRead extends PronosticoDemandaCreate {
  pronostico_id: string;
  cliente_id: string;
  desviacion?: number;  // cantidad_real - cantidad_pronosticada (cuando hay cantidad_real)
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Plan Producción

```typescript
interface PlanProduccionCreate {
  empresa_id: string;
  codigo_plan: string;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado?: 'borrador' | 'aprobado' | 'ejecutado' | 'cerrado';
  observaciones?: string;
}

interface PlanProduccionRead extends PlanProduccionCreate {
  plan_produccion_id: string;
  cliente_id: string;
  fecha_aprobacion?: string;
  aprobado_por_usuario_id?: string;
  fecha_creacion: string;
  usuario_creacion_id?: string;
}
```

### Plan Producción Detalle

```typescript
interface PlanProduccionDetalleCreate {
  plan_produccion_id: string;
  producto_id: string;
  fecha_inicio: string;
  fecha_fin: string;
  pronostico_demanda?: number;
  pedidos_firmes?: number;
  stock_inicial?: number;
  stock_seguridad?: number;
  cantidad_planificada: number;
  cantidad_producida?: number;
  unidad_medida_id: string;
  capacidad_disponible?: number;
  observaciones?: string;
}

interface PlanProduccionDetalleRead extends PlanProduccionDetalleCreate {
  plan_detalle_id: string;
  cliente_id: string;
  porcentaje_uso_capacidad?: number;  // calculado
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (pronóstico, plan, detalle) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/mps
  /pronostico-demanda
    /list
    /create
    /:id/edit
  /plan-produccion
    /list
    /create
    /:id/edit
    /:id/detalle   # Líneas (plan-produccion-detalle?plan_produccion_id=)
  /plan-produccion-detalle
    /list
    /create
    /:id/edit
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) e INV (productos, unidades de medida) configurados.

### 2. Pronósticos de demanda

- Crear pronósticos por producto y periodo: POST /mps/pronostico-demanda (producto_id, anio, mes, fecha_inicio, fecha_fin, cantidad_pronosticada, unidad_medida_id, metodo_pronostico opcional).
- Listar por producto o por año/mes para pantallas de planificación.
- Opcional: actualizar cantidad_real y consultar desviacion para análisis.

### 3. Plan de producción

- Crear plan agregado: POST /mps/plan-produccion (codigo_plan, nombre, fecha_inicio, fecha_fin).
- Aprobar cuando corresponda: PUT con estado=aprobado, fecha_aprobacion, aprobado_por_usuario_id.

### 4. Detalle del plan

- Por cada plan, cargar líneas por producto y periodo: POST /mps/plan-produccion-detalle (plan_produccion_id, producto_id, fecha_inicio, fecha_fin, pronostico_demanda, pedidos_firmes, stock_inicial, stock_seguridad, cantidad_planificada, unidad_medida_id, capacidad_disponible opcional).
- Listar detalle por plan_produccion_id para la grilla del plan.
- Usar porcentaje_uso_capacidad para indicadores de carga.

### 5. Integración con MRP

- Las necesidades brutas en MRP pueden originarse en pronósticos (origen=pronostico) o en planes; el frontend puede ofrecer “importar desde pronósticos MPS” llamando a GET /mps/pronostico-demanda y luego creando necesidades en MRP.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año:** En la API se usa **anio** (sin ñ) en JSON para evitar problemas de encoding. Siempre enviar y leer `anio` (número, ej. 2026) en pronóstico de demanda.

3. **Desviación:** Se calcula en backend cuando existe cantidad_real (desviacion = cantidad_real - cantidad_pronosticada). Útil para análisis de precisión del pronóstico.

4. **Porcentaje uso capacidad:** En plan detalle se devuelve calculado (cantidad_planificada / capacidad_disponible * 100) cuando capacidad_disponible > 0.

5. **IDs en URLs:** Usar pronostico_id, plan_produccion_id, plan_detalle_id según el recurso; todos son UUID.

---

**Fin de la documentación del módulo MPS**
