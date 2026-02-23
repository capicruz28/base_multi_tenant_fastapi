# Documentación Frontend — Módulo BDG (Presupuestos)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** BDG - Presupuestos

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
/api/v1/bdg
```

### Dependencias

- **Módulo ORG:** Empresa y Centros de Costo (obligatorio para detalle por centro).
- **Módulo FIN:** Plan de Cuentas (obligatorio para detalle por cuenta contable).
- **Orden recomendado:** Configurar ORG (empresa, centros de costo) y FIN (plan de cuentas); luego crear presupuestos y su detalle por cuenta/centro de costo/mes.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Presupuestos (cabecera)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/bdg/presupuestos | Listar (empresa_id, anio, tipo_presupuesto, estado, buscar) |
| GET | /api/v1/bdg/presupuestos/{presupuesto_id} | Detalle |
| POST | /api/v1/bdg/presupuestos | Crear presupuesto |
| PUT | /api/v1/bdg/presupuestos/{presupuesto_id} | Actualizar |

**Campos principales en creación:** empresa_id, codigo_presupuesto, nombre, **anio** (número, ej. 2025), tipo_presupuesto (anual, mensual, trimestral), monto_total_presupuestado, monto_total_ejecutado, estado (borrador, aprobado, vigente, cerrado), fecha_aprobacion, observaciones, usuario_creacion_id.

**En la respuesta (Read):** La API devuelve además **porcentaje_ejecucion** (monto_total_ejecutado / monto_total_presupuestado * 100), calculado en backend.

### 2. Presupuesto Detalle (por cuenta y centro de costo)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/bdg/presupuesto-detalle | Listar (presupuesto_id, cuenta_id, centro_costo_id, mes) |
| GET | /api/v1/bdg/presupuesto-detalle/{presupuesto_detalle_id} | Detalle |
| POST | /api/v1/bdg/presupuesto-detalle | Crear línea de detalle |
| PUT | /api/v1/bdg/presupuesto-detalle/{presupuesto_detalle_id} | Actualizar |

**Campos principales en creación:** presupuesto_id, cuenta_id (UUID de plan de cuentas FIN), centro_costo_id (UUID de ORG, opcional), mes (1-12, opcional; null si es anual consolidado), monto_presupuestado, monto_ejecutado, observaciones.

**En la respuesta (Read):** La API devuelve **monto_disponible** (monto_presupuestado - monto_ejecutado), calculado en backend.

### 3. Ejecución Presupuestal (UI)

No hay endpoint específico; el menú incluye "Ejecución Presupuestal" como pantalla que compara real vs presupuestado y alertas de sobregiro. Consumir **presupuestos** y **presupuesto-detalle** (por presupuesto_id) y usar porcentaje_ejecucion y monto_disponible; alertar cuando monto_disponible < 0 o porcentaje_ejecucion > 100.

---

## Schemas TypeScript

### Presupuesto (cabecera)

```typescript
interface PresupuestoCreate {
  empresa_id: string;
  codigo_presupuesto: string;
  nombre: string;
  anio: number;   // En API se usa "anio" (sin ñ), ej. 2025
  tipo_presupuesto?: 'anual' | 'mensual' | 'trimestral';
  monto_total_presupuestado?: number;
  monto_total_ejecutado?: number;
  estado?: 'borrador' | 'aprobado' | 'vigente' | 'cerrado';
  fecha_aprobacion?: string;
  observaciones?: string;
  usuario_creacion_id?: string;
}

interface PresupuestoUpdate {
  codigo_presupuesto?: string;
  nombre?: string;
  tipo_presupuesto?: string;
  monto_total_presupuestado?: number;
  monto_total_ejecutado?: number;
  estado?: string;
  fecha_aprobacion?: string;
  observaciones?: string;
}

interface PresupuestoRead extends PresupuestoCreate {
  presupuesto_id: string;
  cliente_id: string;
  porcentaje_ejecucion?: number;  // Calculado: ejecutado/presupuestado*100
  fecha_creacion: string;
}
```

### Presupuesto Detalle

```typescript
interface PresupuestoDetalleCreate {
  presupuesto_id: string;
  cuenta_id: string;        // FIN plan de cuentas
  centro_costo_id?: string; // ORG centro de costo
  mes?: number;             // 1-12, null si anual consolidado
  monto_presupuestado: number;
  monto_ejecutado?: number;
  observaciones?: string;
}

interface PresupuestoDetalleUpdate {
  cuenta_id?: string;
  centro_costo_id?: string;
  mes?: number;
  monto_presupuestado?: number;
  monto_ejecutado?: number;
  observaciones?: string;
}

interface PresupuestoDetalleRead extends PresupuestoDetalleCreate {
  presupuesto_detalle_id: string;
  cliente_id: string;
  monto_disponible?: number;  // Calculado: presupuestado - ejecutado
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (presupuesto o detalle) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/bdg
  /presupuestos
    /list
    /create
    /:presupuesto_id/edit
    /:presupuesto_id/detalle   # Lista presupuesto-detalle?presupuesto_id=...
  /presupuesto-detalle
    /list
    /create
    /:presupuesto_detalle_id/edit
  /ejecucion-presupuestal
    # Pantalla comparativa real vs presupuestado; alertas sobregiro
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa, centros de costo) y FIN (plan de cuentas) disponibles.

### 2. Presupuestos (cabecera)

- Crear presupuesto: POST /bdg/presupuestos (empresa_id, codigo_presupuesto, nombre, anio, tipo_presupuesto, estado: "borrador").
- Listar por empresa_id, anio, estado para dashboards y filtros.
- Usar **porcentaje_ejecucion** en listado/detalle para indicadores.

### 3. Presupuesto Detalle

- Por cada presupuesto: POST /bdg/presupuesto-detalle (presupuesto_id, cuenta_id, centro_costo_id, mes, monto_presupuestado).
- Listar por presupuesto_id para la grilla de detalle del presupuesto.
- Usar **monto_disponible** para alertas de sobregiro (monto_disponible < 0).

### 4. Ejecución Presupuestal

- Consumir GET /bdg/presupuestos y GET /bdg/presupuesto-detalle?presupuesto_id=... para comparar real vs presupuestado.
- Mostrar alertas cuando porcentaje_ejecucion > 100 o monto_disponible < 0.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año en Presupuesto:** En la API se usa **anio** (sin ñ) en JSON. Enviar y leer como número (ej. 2025). En base de datos la columna es `año`; el backend realiza la conversión.

3. **Valores calculados:**
   - **PresupuestoRead.porcentaje_ejecucion:** monto_total_ejecutado / monto_total_presupuestado * 100 (0 si presupuestado es 0).
   - **PresupuestoDetalleRead.monto_disponible:** monto_presupuestado - monto_ejecutado. No recalcular en frontend.

4. **cuenta_id y centro_costo_id:** Obtener listas desde FIN (plan de cuentas) y ORG (centros de costo) para combos al crear/editar detalle.

5. **mes en detalle:** Opcional; null indica consolidado anual. Si tipo_presupuesto es mensual, usar mes 1-12.

6. **Estados del presupuesto:** borrador → aprobado → vigente → cerrado. Ajustar flujo en frontend según reglas de negocio.

7. **IDs en URLs:** presupuesto_id y presupuesto_detalle_id son UUID.

---

**Fin de la documentación del módulo BDG**
