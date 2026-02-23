# Documentación Frontend — Módulo PM (Gestión de Proyectos)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** PM - Gestión de Proyectos

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
/api/v1/pm
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Módulo SLS:** Cliente de venta (opcional; para vincular proyecto a un cliente).
- **Orden recomendado:** Configurar ORG; opcionalmente SLS si se asocian proyectos a clientes.

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Proyectos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/pm/proyectos | Listar (empresa_id, estado, cliente_venta_id, buscar) |
| GET | /api/v1/pm/proyectos/{proyecto_id} | Detalle |
| POST | /api/v1/pm/proyectos | Crear proyecto |
| PUT | /api/v1/pm/proyectos/{proyecto_id} | Actualizar |

**Campos principales en creación:** empresa_id, codigo_proyecto, nombre, descripcion, cliente_venta_id (opcional), fecha_inicio, fecha_fin_estimada, fecha_fin_real (opcional), presupuesto, costo_real (default 0), responsable_usuario_id, estado (planificado, en_curso, pausado, completado, cancelado).

**En actualización:** Se puede actualizar costo_real al imputar gastos reales desde otros módulos o manualmente; estado, fecha_fin_real, etc.

### 2. Seguimiento (UI)

No hay endpoint específico; el menú incluye "Seguimiento" como pantalla que compara presupuesto vs costo real y % de avance. Consumir GET /pm/proyectos (o por proyecto_id) y calcular en frontend:
- **Porcentaje de ejecución (costo):** `presupuesto > 0 ? (costo_real / presupuesto) * 100 : 0`
- **Desviación:** costo_real - presupuesto (alertas si supera presupuesto).

---

## Schemas TypeScript

### Proyecto

```typescript
interface ProyectoCreate {
  empresa_id: string;
  codigo_proyecto: string;
  nombre: string;
  descripcion?: string;
  cliente_venta_id?: string;   // SLS cliente
  fecha_inicio: string;        // ISO date (YYYY-MM-DD)
  fecha_fin_estimada?: string;
  fecha_fin_real?: string;
  presupuesto?: number;
  costo_real?: number;
  responsable_usuario_id?: string;
  estado?: 'planificado' | 'en_curso' | 'pausado' | 'completado' | 'cancelado';
}

interface ProyectoUpdate {
  codigo_proyecto?: string;
  nombre?: string;
  descripcion?: string;
  cliente_venta_id?: string;
  fecha_inicio?: string;
  fecha_fin_estimada?: string;
  fecha_fin_real?: string;
  presupuesto?: number;
  costo_real?: number;
  responsable_usuario_id?: string;
  estado?: string;
}

interface ProyectoRead extends ProyectoCreate {
  proyecto_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Proyecto no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/pm
  /proyectos
    /list
    /create
    /:proyecto_id/edit
    /:proyecto_id          # Detalle y seguimiento (presupuesto vs real, % avance)
  /seguimiento
    # Pantalla comparativa presupuesto vs costo real por proyecto; % avance
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) configurado; opcionalmente SLS (clientes) para asociar proyecto a cliente de venta.

### 2. Proyectos

- Crear proyecto: POST /pm/proyectos (empresa_id, codigo_proyecto, nombre, fecha_inicio, presupuesto, estado: "planificado", cliente_venta_id si aplica).
- Listar por empresa_id, estado o cliente_venta_id para dashboards y filtros.
- Actualizar costo_real (PUT) al imputar gastos desde otros módulos o al cargar costos reales manualmente.
- Actualizar estado (planificado → en_curso → completado/cancelado) y fecha_fin_real al cerrar.

### 3. Seguimiento

- Consumir GET /pm/proyectos (o detalle por proyecto_id).
- Calcular % ejecución costo: (costo_real / presupuesto) * 100 cuando presupuesto > 0.
- Mostrar alertas cuando costo_real > presupuesto.

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Fechas:** Enviar y recibir en formato ISO date (YYYY-MM-DD) para fecha_inicio, fecha_fin_estimada, fecha_fin_real.

3. **Presupuesto vs real:** La API devuelve `presupuesto` y `costo_real`. El **porcentaje de avance (costo)** se calcula en frontend: `presupuesto > 0 ? (costo_real / presupuesto) * 100 : 0`. No existe campo calculado en la respuesta.

4. **cliente_venta_id:** Opcional; vincula el proyecto a un cliente (módulo SLS). Usar listado de clientes SLS para el combo.

5. **Estados:** planificado → en_curso → pausado | completado | cancelado. Ajustar flujo en frontend según reglas de negocio.

6. **IDs en URLs:** proyecto_id es UUID.

7. **Vincular gastos reales:** El costo_real se actualiza vía PUT; la imputación desde otros módulos (FIN, PUR, etc.) puede hacerse en backend en futuras integraciones o actualizando costo_real desde el frontend al registrar gastos.

---

**Fin de la documentación del módulo PM**
