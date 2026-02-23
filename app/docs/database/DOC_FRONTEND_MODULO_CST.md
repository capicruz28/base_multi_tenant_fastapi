# Documentación Frontend — Módulo CST (Costeo de Productos)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** CST - Costeo de Productos

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)
8. [Notas Importantes](#notas-importantes)

---

## Información General

### Base URL

```
/api/v1/cst
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Módulo INV:** Producto (obligatorio para Costo de Productos).
- **Módulo MFG:** Orden de producción (opcional; para vincular costo a una orden).
- **Orden recomendado:** Configurar ORG e INV; luego Tipos de Centro de Costo y Costo de Productos.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Tipos de Centro de Costo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/cst/tipos-centro-costo | Listar (empresa_id, tipo_clasificacion, es_activo, buscar) |
| GET | /api/v1/cst/tipos-centro-costo/{cc_tipo_id} | Detalle |
| POST | /api/v1/cst/tipos-centro-costo | Crear tipo |
| PUT | /api/v1/cst/tipos-centro-costo/{cc_tipo_id} | Actualizar |

**Campos principales en creación:** empresa_id, codigo, nombre, tipo_clasificacion (productivo, servicio, administrativo), base_distribucion (horas_hombre, unidades_producidas, ventas, area_m2), es_activo.

### 2. Costo de Productos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/cst/producto-costo | Listar (empresa_id, producto_id, anio, mes, metodo_costeo) |
| GET | /api/v1/cst/producto-costo/{producto_costo_id} | Detalle |
| POST | /api/v1/cst/producto-costo | Crear registro de costo |
| PUT | /api/v1/cst/producto-costo/{producto_costo_id} | Actualizar |

**Campos principales en creación:** empresa_id, producto_id, **anio** (número, ej. 2025), mes (1-12), costo_material_directo, costo_mano_obra_directa, costo_indirecto_fabricacion, cantidad_producida, orden_produccion_id (opcional), metodo_costeo (real, estandar, promedio), observaciones.

**En la respuesta (Read):** La API devuelve además **costo_total** (suma de material + mano de obra + CIF) y **costo_unitario** (costo_total / cantidad_producida cuando cantidad_producida > 0), calculados en backend.

### 3. Análisis de Variaciones (UI)

No hay endpoint específico; el menú incluye "Análisis de Variaciones" como pantalla que puede consumir los datos de **producto-costo** filtrando por producto y comparando registros con metodo_costeo `real` vs `estandar` (o por periodo). Implementar en frontend con los mismos endpoints de producto-costo.

---

## Schemas TypeScript

### Centro de Costo Tipo

```typescript
interface CentroCostoTipoCreate {
  empresa_id: string;
  codigo: string;
  nombre: string;
  tipo_clasificacion: 'productivo' | 'servicio' | 'administrativo';
  base_distribucion?: 'horas_hombre' | 'unidades_producidas' | 'ventas' | 'area_m2';
  es_activo?: boolean;
}

interface CentroCostoTipoUpdate {
  codigo?: string;
  nombre?: string;
  tipo_clasificacion?: string;
  base_distribucion?: string;
  es_activo?: boolean;
}

interface CentroCostoTipoRead extends CentroCostoTipoCreate {
  cc_tipo_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Producto Costo

```typescript
interface ProductoCostoCreate {
  empresa_id: string;
  producto_id: string;
  anio: number;   // En API se usa "anio" (sin ñ), ej. 2025
  mes: number;    // 1-12
  costo_material_directo?: number;
  costo_mano_obra_directa?: number;
  costo_indirecto_fabricacion?: number;
  cantidad_producida?: number;
  orden_produccion_id?: string;
  metodo_costeo?: 'real' | 'estandar' | 'promedio';
  observaciones?: string;
}

interface ProductoCostoUpdate {
  costo_material_directo?: number;
  costo_mano_obra_directa?: number;
  costo_indirecto_fabricacion?: number;
  cantidad_producida?: number;
  orden_produccion_id?: string;
  metodo_costeo?: string;
  observaciones?: string;
}

interface ProductoCostoRead extends ProductoCostoCreate {
  producto_costo_id: string;
  cliente_id: string;
  costo_total?: number;    // Calculado: material + mano_obra + CIF
  costo_unitario?: number; // Calculado: costo_total / cantidad_producida
  fecha_creacion: string;
  fecha_calculo?: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (tipo centro costo, producto costo) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/cst
  /tipos-centro-costo
    /list
    /create
    /:cc_tipo_id/edit
  /producto-costo
    /list
    /create
    /:producto_costo_id/edit
  /analisis-variaciones
    # Pantalla que consume GET /producto-costo con filtros (producto_id, anio, mes, metodo_costeo)
    # para comparar real vs estándar o por periodo
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) e INV (productos) disponibles.

### 2. Tipos de Centro de Costo

- Crear tipos: POST /cst/tipos-centro-costo (empresa_id, codigo, nombre, tipo_clasificacion, base_distribucion, es_activo).
- Listar por empresa_id, tipo_clasificacion o es_activo para combos y reportes.

### 3. Costo de Productos

- Crear registro: POST /cst/producto-costo (empresa_id, producto_id, anio, mes, costos, cantidad_producida, metodo_costeo).
- Listar por producto_id, anio, mes o metodo_costeo para reportes y análisis.
- Usar en respuesta **costo_total** y **costo_unitario** para tablas y gráficos sin recalcular en frontend.

### 4. Análisis de Variaciones

- Consumir GET /cst/producto-costo con filtros (producto_id, anio, mes, metodo_costeo) y presentar comparativas real vs estándar o evolución por periodo en la pantalla "Análisis de Variaciones".

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año en Producto Costo:** En la API se usa **anio** (sin ñ) en JSON. Enviar y leer como número (ej. 2025). En base de datos la columna es `año`; el backend realiza la conversión.

3. **Costos calculados:** En **ProductoCostoRead** el backend devuelve:
   - **costo_total:** suma de costo_material_directo + costo_mano_obra_directa + costo_indirecto_fabricacion.
   - **costo_unitario:** costo_total / cantidad_producida cuando cantidad_producida > 0; si no, null.
   No es necesario recalcularlos en frontend.

4. **IDs en URLs:** cc_tipo_id y producto_costo_id son UUID.

5. **Vínculo con MFG:** orden_produccion_id en producto_costo es opcional; usar si el costo se asocia a una orden de producción específica (listar órdenes desde módulo MFG para el combo).

6. **Análisis de Variaciones:** Es una pantalla de solo lectura/consulta que usa los mismos endpoints de producto-costo; no hay CRUD adicional.

---

**Fin de la documentación del módulo CST**
