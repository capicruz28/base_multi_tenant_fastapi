# Documentación Frontend — Módulo HCM (Planillas y RRHH)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** HCM - Human Capital Management (Planillas y Recursos Humanos)

---

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## 🔑 Información General

### Base URL
```
/api/v1/hcm
```

### Dependencias
- **Módulo ORG:** Empresa, departamentos, cargos, sucursales, centros de costo (obligatorio).
- **Orden recomendado:** Configurar ORG antes de usar HCM.

---

## 🔐 Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## 📡 Endpoints

### 1. Empleados

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/empleados | Listar (empresa_id, estado_empleado, es_activo, departamento_id, cargo_id, buscar) |
| GET | /api/v1/hcm/empleados/{empleado_id} | Detalle |
| POST | /api/v1/hcm/empleados | Crear empleado |
| PUT | /api/v1/hcm/empleados/{empleado_id} | Actualizar |

Campos principales en creación: empresa_id, codigo_empleado, tipo_documento, numero_documento, apellido_paterno, apellido_materno, nombres, fecha_nacimiento, sexo, fecha_ingreso, sistema_pensionario (AFP/ONP), departamento_id, cargo_id, sucursal_id, centro_costo_id, banco, numero_cuenta, etc.

### 2. Contratos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/contratos | Listar (empresa_id, empleado_id, estado_contrato, es_contrato_vigente) |
| GET | /api/v1/hcm/contratos/{contrato_id} | Detalle |
| POST | /api/v1/hcm/contratos | Crear contrato |
| PUT | /api/v1/hcm/contratos/{contrato_id} | Actualizar |

Campos principales: empresa_id, empleado_id, numero_contrato, tipo_contrato (plazo_indeterminado, plazo_fijo, part_time, etc.), fecha_inicio, fecha_fin, cargo_id, remuneracion_basica, moneda, tipo_remuneracion, tiene_periodo_prueba, tiene_cts, tiene_gratificacion, estado_contrato.

### 3. Conceptos de Planilla

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/conceptos-planilla | Listar (empresa_id, tipo_concepto, es_activo, buscar) |
| GET | /api/v1/hcm/conceptos-planilla/{concepto_id} | Detalle |
| POST | /api/v1/hcm/conceptos-planilla | Crear concepto |
| PUT | /api/v1/hcm/conceptos-planilla/{concepto_id} | Actualizar |

tipo_concepto: 'ingreso' | 'descuento' | 'aporte_empleador'. Campos: codigo_concepto, nombre, es_fijo, monto_fijo, es_porcentaje, porcentaje_base, base_calculo, afecto_renta_quinta, afecto_essalud, afecto_cts, afecto_gratificacion, afecto_vacaciones, codigo_plame, cuenta_contable.

### 4. Planillas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/planillas | Listar (empresa_id, tipo_planilla, estado, año, mes) |
| GET | /api/v1/hcm/planillas/{planilla_id} | Detalle |
| POST | /api/v1/hcm/planillas | Crear planilla |
| PUT | /api/v1/hcm/planillas/{planilla_id} | Actualizar |

Campos: numero_planilla, año, mes, periodo_descripcion, tipo_planilla (mensual, quincenal, gratificacion, cts, utilidades), fecha_inicio_periodo, fecha_fin_periodo, fecha_pago, estado (borrador, calculada, aprobada, pagada, cerrada). Nota: en JSON el campo año se envía como "año" (con n con tilde).

### 5. Planilla Empleados (boletas por empleado)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/planilla-empleados | Listar (planilla_id, empleado_id) |
| GET | /api/v1/hcm/planilla-empleados/{planilla_empleado_id} | Detalle |
| POST | /api/v1/hcm/planilla-empleados | Crear (incluir empleado en planilla) |
| PUT | /api/v1/hcm/planilla-empleados/{planilla_empleado_id} | Actualizar |

Campos: planilla_id, empleado_id, dias_laborados, dias_faltas, horas_ordinarias, horas_extras_25/35/100, remuneracion_basica, total_ingresos, total_descuentos, total_neto, pagado, metodo_pago, numero_operacion.

### 6. Planilla Detalle (conceptos por empleado)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/planilla-detalle | Listar (planilla_empleado_id, tipo_concepto) |
| GET | /api/v1/hcm/planilla-detalle/{planilla_detalle_id} | Detalle |
| POST | /api/v1/hcm/planilla-detalle | Crear línea de concepto |
| PUT | /api/v1/hcm/planilla-detalle/{planilla_detalle_id} | Actualizar |

Campos: planilla_empleado_id, concepto_id, tipo_concepto, base_calculo, cantidad, tasa_porcentaje, monto.

### 7. Asistencia

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/asistencia | Listar (empresa_id, empleado_id, fecha_desde, fecha_hasta, tipo_asistencia) |
| GET | /api/v1/hcm/asistencia/{asistencia_id} | Detalle |
| POST | /api/v1/hcm/asistencia | Registrar marcación/día |
| PUT | /api/v1/hcm/asistencia/{asistencia_id} | Actualizar |

Campos: empresa_id, empleado_id, fecha, hora_entrada, hora_salida, horas_trabajadas, horas_extras, tipo_asistencia (presente, falta, tardanza, licencia, vacaciones, descanso_medico), minutos_tardanza, justificacion.

### 8. Vacaciones

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/vacaciones | Listar (empresa_id, empleado_id, estado, año_periodo) |
| GET | /api/v1/hcm/vacaciones/{vacaciones_id} | Detalle |
| POST | /api/v1/hcm/vacaciones | Crear periodo vacaciones |
| PUT | /api/v1/hcm/vacaciones/{vacaciones_id} | Actualizar (programar, aprobar, registrar tomados) |

Campos: empresa_id, empleado_id, año_periodo, fecha_inicio_periodo, fecha_fin_periodo, dias_ganados, dias_tomados, fecha_inicio_programada, fecha_fin_programada, estado (pendiente, programada, aprobada, en_curso, completada, vencida).

### 9. Préstamos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/hcm/prestamos | Listar (empresa_id, empleado_id, estado) |
| GET | /api/v1/hcm/prestamos/{prestamo_id} | Detalle |
| POST | /api/v1/hcm/prestamos | Crear préstamo |
| PUT | /api/v1/hcm/prestamos/{prestamo_id} | Actualizar (cuotas pagadas, estado) |

Campos: empresa_id, empleado_id, numero_prestamo, tipo_prestamo (adelanto_sueldo, prestamo, adelanto_gratificacion), monto_prestamo, numero_cuotas, monto_cuota, cuotas_pagadas, saldo_pendiente, estado (activo, pagado, cancelado).

---

## 📝 Schemas TypeScript

### Empleado (resumen)
```typescript
interface EmpleadoCreate {
  empresa_id: string;
  codigo_empleado: string;
  tipo_documento?: string;  // 'DNI' | 'CE' | 'PASAPORTE'
  numero_documento: string;
  apellido_paterno: string;
  apellido_materno: string;
  nombres: string;
  fecha_nacimiento: string;  // date
  sexo: 'M' | 'F';
  fecha_ingreso: string;
  sistema_pensionario: 'AFP' | 'ONP';
  departamento_id?: string;
  cargo_id?: string;
  sucursal_id?: string;
  centro_costo_id?: string;
  banco?: string;
  numero_cuenta?: string;
  estado_empleado?: 'activo' | 'inactivo' | 'cesado';
  // ... más campos opcionales
}

interface EmpleadoRead extends EmpleadoCreate {
  empleado_id: string;
  cliente_id: string;
  fecha_creacion: string;
  fecha_actualizacion?: string;
}
```

### Contrato (resumen)
```typescript
interface ContratoCreate {
  empresa_id: string;
  empleado_id: string;
  numero_contrato: string;
  tipo_contrato: string;  // plazo_indeterminado | plazo_fijo | part_time | etc
  fecha_inicio: string;
  fecha_fin?: string;
  remuneracion_basica: number;
  moneda?: string;
  tipo_remuneracion?: string;  // mensual | quincenal | etc
  tiene_cts?: boolean;
  tiene_gratificacion?: boolean;
  estado_contrato?: 'vigente' | 'vencido' | 'rescindido';
  // ...
}

interface ContratoRead extends ContratoCreate {
  contrato_id: string;
  cliente_id: string;
  fecha_creacion: string;
}
```

### Concepto Planilla
```typescript
interface ConceptoPlanillaCreate {
  empresa_id: string;
  codigo_concepto: string;
  nombre: string;
  tipo_concepto: 'ingreso' | 'descuento' | 'aporte_empleador';
  categoria?: string;
  es_fijo?: boolean;
  monto_fijo?: number;
  es_porcentaje?: boolean;
  porcentaje_base?: number;
  base_calculo?: string;
  afecto_renta_quinta?: boolean;
  afecto_essalud?: boolean;
  afecto_cts?: boolean;
  afecto_gratificacion?: boolean;
  afecto_vacaciones?: boolean;
  es_activo?: boolean;
}
```

### Planilla
```typescript
interface PlanillaCreate {
  empresa_id: string;
  numero_planilla: string;
  año: number;  // En JSON enviar como "año"
  mes: number;
  periodo_descripcion?: string;
  tipo_planilla?: 'mensual' | 'quincenal' | 'gratificacion' | 'cts' | 'utilidades';
  fecha_inicio_periodo: string;
  fecha_fin_periodo: string;
  fecha_pago?: string;
  estado?: 'borrador' | 'calculada' | 'aprobada' | 'pagada' | 'cerrada';
}

interface PlanillaRead extends PlanillaCreate {
  planilla_id: string;
  cliente_id: string;
  total_empleados?: number;
  total_ingresos?: number;
  total_descuentos?: number;
  total_neto?: number;
  total_aportes_empleador?: number;
  fecha_creacion: string;
}
```

### Planilla Empleado
```typescript
interface PlanillaEmpleadoCreate {
  planilla_id: string;
  empleado_id: string;
  dias_laborados?: number;
  dias_faltas?: number;
  horas_ordinarias?: number;
  horas_extras_25?: number;
  horas_extras_35?: number;
  horas_extras_100?: number;
  remuneracion_basica: number;
  total_ingresos?: number;
  total_descuentos?: number;
  total_neto?: number;
}
```

### Planilla Detalle
```typescript
interface PlanillaDetalleCreate {
  planilla_empleado_id: string;
  concepto_id: string;
  tipo_concepto: string;
  base_calculo?: number;
  cantidad?: number;
  tasa_porcentaje?: number;
  monto: number;
}
```

### Asistencia
```typescript
interface AsistenciaCreate {
  empresa_id: string;
  empleado_id: string;
  fecha: string;  // YYYY-MM-DD
  hora_entrada?: string;  // HH:mm
  hora_salida?: string;
  horas_trabajadas?: number;
  horas_extras?: number;
  tipo_asistencia?: 'presente' | 'falta' | 'tardanza' | 'licencia' | 'vacaciones' | 'descanso_medico';
  minutos_tardanza?: number;
  justificacion?: string;
}
```

### Vacaciones
```typescript
interface VacacionesCreate {
  empresa_id: string;
  empleado_id: string;
  año_periodo: number;
  fecha_inicio_periodo: string;
  fecha_fin_periodo: string;
  dias_ganados?: number;
  dias_tomados?: number;
  estado?: 'pendiente' | 'programada' | 'aprobada' | 'en_curso' | 'completada' | 'vencida';
}
```

### Préstamo
```typescript
interface PrestamoCreate {
  empresa_id: string;
  empleado_id: string;
  numero_prestamo: string;
  tipo_prestamo: 'adelanto_sueldo' | 'prestamo' | 'adelanto_gratificacion';
  monto_prestamo: number;
  numero_cuotas: number;
  monto_cuota: number;
  moneda?: string;
  estado?: 'activo' | 'pagado' | 'cancelado';
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Recurso no encontrado (empleado, contrato, planilla, etc.) |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## 🗺️ Rutas SPA Recomendadas

```
/hcm
  /empleados
    /list
    /create
    /:id/edit
    /:id/contratos
  /contratos
    /list
    /create
    /:id/edit
  /conceptos-planilla
    /list
    /create
    /:id/edit
  /planillas
    /list
    /create
    /:id/edit
    /:id/empleados        # Planilla empleados (boletas)
    /:id/empleados/:peid  # Detalle + conceptos (planilla-detalle)
  /asistencia
    /list
    /marcar
    /:id/edit
  /vacaciones
    /list
    /solicitar
    /:id/edit
  /prestamos
    /list
    /solicitar
    /:id/edit
```

---

## 🔄 Flujo de Implementación Recomendado

### 1. Configuración ORG
- Tener empresas, departamentos, cargos, sucursales y centros de costo (ORG) antes de usar HCM.

### 2. Maestro de Empleados
- Crear empleados (POST /hcm/empleados) con datos personales, documento, AFP/ONP, banco, cargo, departamento.
- Opcional: vincular usuario del sistema (usuario_id) para acceso al portal.

### 3. Contratos
- Por cada empleado, crear contrato vigente (tipo, fechas, remuneración, CTS, gratificación, periodo de prueba).
- Renovaciones: nuevo contrato con contrato_renovado_desde_id opcional.

### 4. Conceptos de Planilla
- Definir conceptos de tipo ingreso (sueldo, bonos, horas extras), descuento (AFP, ONP, adelantos, préstamos) y aporte_empleador (ESSALUD, etc.).
- Configurar afectaciones (renta 5ta, ESSALUD, CTS, gratificación, vacaciones) y código PLAME si aplica.

### 5. Planillas
- Crear planilla por periodo (mensual, gratificación, CTS): POST /hcm/planillas.
- Agregar empleados a la planilla: POST /hcm/planilla-empleados (días, horas, remuneración base).
- Cargar detalle de conceptos por empleado: POST /hcm/planilla-detalle (concepto_id, monto o cálculo).
- Aprobar y marcar como pagada; opcional: integrar con FIN (asiento_contable_id) y PLAME.

### 6. Asistencia
- Registrar marcaciones (entrada/salida) por empleado y fecha: POST /hcm/asistencia.
- Consultar por empleado y rango de fechas para calcular faltas, tardanzas y horas extras.

### 7. Vacaciones
- Por empleado y año: crear registro de vacaciones (días ganados, periodo).
- Programar y aprobar salidas; actualizar dias_tomados y fecha_inicio_real/fin_real.

### 8. Préstamos
- Registrar préstamos/adelantos; descontar en planilla vía concepto de descuento vinculado al préstamo.
- Actualizar cuotas_pagadas y saldo_pendiente; marcar estado "pagado" al terminar.

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año:** En planilla, el campo de año se llama `año` (con ñ). En JSON se envía como `"año": 2026`. En TypeScript puede definirse como `año: number` (nombre de propiedad válido).

3. **Empleado – jefe:** `jefe_inmediato_empleado_id` es auto-referencia a otro empleado (hcm_empleado).

4. **Contrato vigente:** Un empleado puede tener varios contratos; usar `es_contrato_vigente` y `estado_contrato` para saber cuál usar en la planilla actual.

5. **Planilla – estado:** Borrador → calculada → aprobada → pagada → cerrada. Hasta no estar aprobada/pagada no debería bloquearse para edición según reglas de negocio.

6. **Asistencia – único por día:** Un solo registro por (empleado_id, fecha). Para modificar el mismo día usar PUT del registro existente.

7. **Vacaciones – único por año:** Un registro por (empleado_id, año_periodo). dias_pendientes = dias_ganados - dias_tomados (puede calcularse en frontend si no viene en API).

8. **Préstamos – descuento en planilla:** El descuento por cuota suele implementarse como un concepto de planilla que referencia al préstamo (por ejemplo por número) y se actualiza cuotas_pagadas vía PUT al préstamo.

---

**Fin de la documentación del módulo HCM**
