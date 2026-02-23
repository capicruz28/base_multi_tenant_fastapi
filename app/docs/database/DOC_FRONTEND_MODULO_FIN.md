# Documentación Frontend — Módulo FIN (Finanzas y Contabilidad)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** FIN - Finanzas y Contabilidad ERP

---

## 📋 Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas](#schemas)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)

---

## 🔑 Información General

### Base URL
```
/api/v1/fin
```

### Dependencias
- **Módulo ORG:** Requiere tener empresas y centros de costo configurados.
- **Orden recomendado:** Configurar primero ORG, luego FIN.

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT token en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene automáticamente del token, **nunca debe enviarse en el body**.

---

## 📡 Endpoints

### 1. Plan de Cuentas

#### Listar Plan de Cuentas
```http
GET /api/v1/fin/plan-cuentas
```

**Query Parameters:**
- `empresa_id` (UUID, opcional): Filtrar por empresa
- `cuenta_padre_id` (UUID, opcional): Filtrar por cuenta padre (para ver subcuentas)
- `tipo_cuenta` (string, opcional): Filtrar por tipo ('activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto')
- `nivel` (int, opcional): Filtrar por nivel jerárquico
- `solo_activos` (boolean, default: true): Solo cuentas activas
- `buscar` (string, opcional): Búsqueda por nombre o código

**Response:** `200 OK`
```json
[
  {
    "cuenta_id": "uuid",
    "cliente_id": "uuid",
    "empresa_id": "uuid",
    "codigo_cuenta": "101",
    "nombre_cuenta": "Caja",
    "descripcion": "Caja y bancos",
    "cuenta_padre_id": null,
    "nivel": 1,
    "tipo_cuenta": "activo",
    "categoria": "corriente",
    "naturaleza": "deudora",
    "acepta_movimientos": true,
    "requiere_centro_costo": false,
    "aparece_balance": true,
    "es_activo": true
  }
]
```

#### Crear Cuenta
```http
POST /api/v1/fin/plan-cuentas
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "codigo_cuenta": "101",
  "nombre_cuenta": "Caja",
  "tipo_cuenta": "activo",
  "naturaleza": "deudora",
  "nivel": 1
}
```

---

### 2. Periodos Contables

#### Listar Periodos Contables
```http
GET /api/v1/fin/periodos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional)
- `año` (int, opcional)
- `mes` (int, opcional, 1-12)
- `estado` (string, opcional): 'abierto', 'cerrado', 'bloqueado'

**Response:** `200 OK`
```json
[
  {
    "periodo_id": "uuid",
    "empresa_id": "uuid",
    "año": 2025,
    "mes": 2,
    "fecha_inicio": "2025-02-01",
    "fecha_fin": "2025-02-28",
    "estado": "abierto",
    "fecha_cierre": null
  }
]
```

#### Crear Periodo Contable
```http
POST /api/v1/fin/periodos
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "año": 2025,
  "mes": 2,
  "fecha_inicio": "2025-02-01",
  "fecha_fin": "2025-02-28",
  "estado": "abierto"
}
```

---

### 3. Asientos Contables

#### Listar Asientos Contables
```http
GET /api/v1/fin/asientos
```

**Query Parameters:**
- `empresa_id` (UUID, opcional)
- `periodo_id` (UUID, opcional)
- `tipo_asiento` (string, opcional): 'apertura', 'diario', 'ajuste', 'cierre', 'provision'
- `estado` (string, opcional): 'borrador', 'registrado', 'aprobado', 'anulado'
- `modulo_origen` (string, opcional): 'PUR', 'SLS', 'INV', 'FIN', etc.
- `fecha_desde` (date, opcional)
- `fecha_hasta` (date, opcional)
- `buscar` (string, opcional): Búsqueda por número o glosa

**Response:** `200 OK`
```json
[
  {
    "asiento_id": "uuid",
    "numero_asiento": "AS-001",
    "fecha_asiento": "2025-02-18",
    "periodo_id": "uuid",
    "tipo_asiento": "diario",
    "modulo_origen": "SLS",
    "documento_origen_tipo": "pedido",
    "documento_origen_numero": "PED-001",
    "glosa": "Venta de productos",
    "moneda": "PEN",
    "total_debe": 1180.00,
    "total_haber": 1180.00,
    "estado": "registrado"
  }
]
```

#### Crear Asiento Contable
```http
POST /api/v1/fin/asientos
```

**Request Body:**
```json
{
  "empresa_id": "uuid",
  "numero_asiento": "AS-001",
  "fecha_asiento": "2025-02-18",
  "periodo_id": "uuid",
  "tipo_asiento": "diario",
  "glosa": "Venta de productos",
  "total_debe": 1180.00,
  "total_haber": 1180.00,
  "estado": "borrador"
}
```

#### Detalles de Asiento
```http
GET /api/v1/fin/asientos/{asiento_id}/detalles
POST /api/v1/fin/asientos/{asiento_id}/detalles
```

**Request Body (POST detalle):**
```json
{
  "item": 1,
  "cuenta_id": "uuid",
  "debe": 1180.00,
  "haber": 0.00,
  "glosa": "Cuentas por cobrar",
  "centro_costo_id": "uuid",
  "tercero_tipo": "cliente",
  "tercero_id": "uuid"
}
```

---

## 📝 Schemas TypeScript

### PlanCuenta
```typescript
interface PlanCuenta {
  cuenta_id: string;
  codigo_cuenta: string;
  nombre_cuenta: string;
  cuenta_padre_id?: string;
  nivel: number;
  tipo_cuenta: 'activo' | 'pasivo' | 'patrimonio' | 'ingreso' | 'gasto';
  naturaleza: 'deudora' | 'acreedora';
  acepta_movimientos: boolean;
  requiere_centro_costo: boolean;
  aparece_balance: boolean;
  es_activo: boolean;
}
```

### PeriodoContable
```typescript
interface PeriodoContable {
  periodo_id: string;
  año: number;
  mes: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado: 'abierto' | 'cerrado' | 'bloqueado';
  fecha_cierre?: string;
}
```

### AsientoContable
```typescript
interface AsientoContable {
  asiento_id: string;
  numero_asiento: string;
  fecha_asiento: string;
  periodo_id: string;
  tipo_asiento: 'apertura' | 'diario' | 'ajuste' | 'cierre' | 'provision';
  modulo_origen?: string;
  glosa: string;
  total_debe: number;
  total_haber: number;
  estado: 'borrador' | 'registrado' | 'aprobado' | 'anulado';
}
```

### AsientoDetalle
```typescript
interface AsientoDetalle {
  asiento_detalle_id: string;
  asiento_id: string;
  item: number;
  cuenta_id: string;
  debe: number;
  haber: number;
  glosa?: string;
  centro_costo_id?: string;
  tercero_tipo?: 'cliente' | 'proveedor' | 'empleado';
  tercero_id?: string;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| `400` | Bad Request - Datos inválidos |
| `401` | Unauthorized - Token inválido |
| `404` | Not Found - Recurso no encontrado |
| `422` | Unprocessable Entity - Error de validación |
| `500` | Internal Server Error |

---

## 🗺️ Rutas SPA Recomendadas

```
/fin
  /plan-cuentas
    /listado
    /nuevo
    /:id
    /:id/editar
  /periodos
    /listado
    /nuevo
    /:id
    /:id/cerrar
  /asientos
    /listado
    /nuevo
    /:id
    /:id/editar
    /:id/detalles
    /:id/aprobar
```

---

## 🚀 Flujo de Implementación Recomendado

### Fase 1: Configuración Base
1. **Crear Plan de Cuentas**
   - Importar o crear plan contable estándar
   - Configurar jerarquía de cuentas (padre-hijo)
   - Definir tipos y naturalezas de cuentas

2. **Crear Periodos Contables**
   - Crear periodos mensuales para el año fiscal
   - Mantener periodos abiertos para contabilizar
   - Cerrar periodos al finalizar el mes

### Fase 2: Operaciones Contables
1. **Asientos Automáticos**
   - Los módulos operativos (PUR, SLS, INV) generan asientos automáticos
   - Revisar y aprobar asientos generados automáticamente

2. **Asientos Manuales**
   - Crear asientos manuales desde el módulo FIN
   - Agregar detalles (debe/haber) por cuenta
   - Validar que el asiento esté cuadrado (debe = haber)
   - Registrar y aprobar asientos

### Fase 3: Control y Reportes
1. **Validación de Asientos**
   - Verificar cuadre de asientos (debe = haber)
   - Validar que periodos estén abiertos
   - Aprobar asientos antes de cerrar periodo

2. **Cierre de Periodos**
   - Verificar que todos los asientos estén aprobados
   - Cerrar periodo contable
   - Generar reportes financieros (Balance, P&G)

---

## 📌 Notas Importantes

1. **Multi-tenancy:** Todos los endpoints filtran automáticamente por `cliente_id` del token.

2. **Plan de Cuentas:**
   - Estructura jerárquica con cuenta padre-hijo
   - Niveles: 1=Clase, 2=Grupo, 3=Subcuenta, etc.
   - Tipos: 'activo', 'pasivo', 'patrimonio', 'ingreso', 'gasto'
   - Naturaleza: 'deudora' (aumenta con débitos) o 'acreedora' (aumenta con créditos)

3. **Periodos Contables:**
   - Controlan qué periodos están abiertos para contabilizar
   - Estados: 'abierto' (permite contabilizar), 'cerrado' (no permite), 'bloqueado'
   - Solo se puede contabilizar en periodos abiertos

4. **Asientos Contables:**
   - Deben estar cuadrados (total_debe = total_haber)
   - Tipos: 'apertura' (inicio de ejercicio), 'diario' (operaciones normales), 'ajuste' (correcciones), 'cierre' (cierre de ejercicio), 'provision' (provisiones)
   - Estados: 'borrador' (en creación), 'registrado' (guardado), 'aprobado' (aprobado), 'anulado' (anulado)

5. **Asientos Detalle:**
   - Cada línea tiene debe o haber (no ambos)
   - Puede incluir centro de costo para análisis
   - Puede vincular tercero (cliente/proveedor/empleado)
   - Puede tener fecha de vencimiento (para cuentas por cobrar/pagar)

6. **Integración con Otros Módulos:**
   - PUR: Genera asientos de compras y cuentas por pagar
   - SLS: Genera asientos de ventas y cuentas por cobrar
   - INV: Genera asientos de movimientos de inventario
   - HCM: Genera asientos de planilla y beneficios

7. **Validaciones Importantes:**
   - Asientos deben estar cuadrados antes de registrar
   - Solo se puede contabilizar en periodos abiertos
   - Cuentas deben estar activas para usar en asientos
   - Validar que cuenta acepte movimientos (no solo agrupación)

---

**Fin de la documentación**
