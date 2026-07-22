# Modelo de Dominio del Core ERP

**Documento:** Etapa 0.5 · 01  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado a nivel conceptual)  
**Alcance:** Dominios, responsabilidades y límites — **sin tablas ni SQL**

---

## 1. Propósito

Definir el **mapa de dominios** de la Plataforma ERP Industrial SaaS MultiTenant y MultiEmpresa.

Este documento responde:

- ¿Cuáles son los dominios principales del Core?
- ¿Qué responsabilidad tiene cada uno?
- ¿Cómo se relacionan?
- ¿Qué pertenece al Core y qué nunca debe pertenecer?

Las decisiones Core vs Vertical, PLN, MES, Event Bus, Lote, Variantes, APS, JSON y ALR están **aprobadas y fuera de discusión**. Aquí se materializan como mapa de dominio estable.

---

## 2. Premisas congeladas

1. El producto es una **plataforma industrial multi-vertical**, no un ERP de un solo rubro.
2. El Core contiene **capacidades**; los Verticales contienen **conocimiento de industria**.
3. MultiTenant y MultiEmpresa son transversales a todo dominio operativo.
4. La identidad autenticada (IAM) no es el contexto operativo ERP (sesión empresa/cliente).
5. La integración asíncrona entre dominios se prepara mediante **eventos de dominio** (contrato de negocio); el bus es infraestructura posterior.
6. APS y capa semántica RPT existen como **dominios futuros / diferidos**, no como capacidad física inmediata.

---

## 3. Capas del sistema

```
┌──────────────────────────────────────────────────────────┐
│  PLATAFORMA (Control Plane / Cross-cutting)              │
│  IAM · CFG · CAT · EVT · ALR · WFL · AUD · DMS · BI*     │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  CORE OPERATIVO (Capabilities)                           │
│  ORG · Comercial · Abastecimiento · Inventario/WMS/LOG   │
│  Calidad · Planificación · Manufactura · Ejecución       │
│  Mantenimiento · Personas · Finanzas · Facturación/POS   │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  VERTICALES (Industry Knowledge)                         │
│  TXT · FOD · MET · MED · AGR · DIS · SRV · CON · …       │
└──────────────────────────────────────────────────────────┘
```

\* BI/RPT semántica: dominio conceptual diferido; no capacidad física de ola 1.

---

## 4. Dominios principales del Core

### 4.1 Plataforma y gobernanza

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Identidad y acceso | **IAM** | Autenticación, autorización RBAC, impersonación, identidad de usuario |
| Organización | **ORG** | Empresa, sucursal, estructura organizacional, centros de costo, parámetros de empresa |
| Configuración de plataforma ERP | **CFG** | Secuencias de código, verticales habilitadas por empresa, feature flags de capacidad Core |
| Catálogos de referencia | **CAT** | Datos de referencia transversales (geografía, monedas, tipos documentales genéricos) |
| Eventos de dominio (infra) | **EVT** | Transporte/contrato de publicación de eventos (no lógica de negocio) |
| Alertas | **ALR** | Evaluación de reglas y bandeja de alertas como **consumidor** de eventos |
| Auditoría | **AUD** | Registro de cambios y trazabilidad técnica de acciones |
| Workflow | **WFL** | Definición y (futuro) runtime de flujos transversales |
| Documentos | **DMS** | Repositorio documental genérico |
| Inteligencia / reportes | **BI / RPT** | Catálogo de reportes; capa semántica **diferida** |

### 4.2 Comercial y relación con clientes

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Relación comercial | **CRM** | Leads, oportunidades, campañas, actividades |
| Ventas | **SLS** | Clientes comerciales, cotizaciones, pedidos |
| Precios | **PRC** | Listas de precio, promociones |
| Punto de venta | **POS** | Ventas de mostrador / caja |
| Facturación | **BILL** (`INV_BILL`) | Comprobantes fiscales / electrónicos de venta |

### 4.3 Abastecimiento y logística externa

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Compras | **PUR** | Proveedores, solicitudes, cotizaciones, órdenes de compra, recepciones |
| Logística de distribución | **LOG** | Transportistas, rutas, guías, despachos hacia cliente |

### 4.4 Inventario y almacén

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Inventario | **INV** | Producto, variante, lote, serie, almacén, stock, movimientos, inventario físico |
| Almacén operativo | **WMS** | Ubicaciones, stock por ubicación, tareas, oleadas, estrategia de salida operativa |

### 4.5 Calidad

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Calidad | **QMS** | Planes de inspección, inspecciones, no conformidades; efecto sobre estado de lote |

### 4.6 Planificación y manufactura

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Capacidad / planeación de recursos | **PLN** | Calendarios de capacidad, disponibilidad de centros de trabajo, excepciones |
| Plan de materiales | **MRP** | Explosión de necesidades y órdenes sugeridas de material |
| Plan maestro | **MPS** | Pronóstico y plan agregado de producción |
| Manufactura (definición y órdenes) | **MFG** | Centros de trabajo, operaciones, BOM, rutas, órdenes de producción, consumo de materiales |
| Ejecución de piso | **MES** | Ejecuciones reales, paradas, motivos OEE, tiempos reales |
| Programación avanzada | **APS** | Scheduling finito / escenarios — **dominio futuro**, sin capacidad física ahora |
| Mantenimiento de activos | **MNT** | Activos, planes, órdenes de trabajo de mantenimiento |

### 4.7 Personas, finanzas y control

| Dominio | Código | Responsabilidad |
|---------|--------|-----------------|
| Capital humano | **HCM** | Empleados, contratos, planilla, asistencia, vacaciones |
| Finanzas | **FIN** | Plan de cuentas, periodos, asientos |
| Tributario | **TAX** | Obligaciones y libros tributarios |
| Presupuestos | **BDG** | Presupuesto vs cuenta/centro de costo |
| Costos | **CST** | Costeo de producto / centros (evolución faseada) |

### 4.8 Dominios stub (reserva de capacidad)

| Dominio | Código | Responsabilidad actual |
|---------|--------|------------------------|
| Proyectos | **PM** | Reserva de capacidad de gestión de proyectos |
| Servicios | **SVC** | Reserva de órdenes de servicio |
| Ticketing | **TKT** | Reserva de mesa de ayuda |

Estos stubs **pertenecen al mapa Core** como namespaces, pero no se expanden conceptualmente en esta etapa más allá de su rol de reserva.

---

## 5. Relaciones entre dominios (conceptuales)

### 5.1 Eje maestro → operativo

```
ORG ──provee contexto empresa──► todos los dominios operativos
CFG ──habilita verticales/capacidades──► UI y módulos
CAT ──referencia──► ORG / INV / BILL / LOG
```

### 5.2 Ciclo procure-to-stock

```
PUR (OC / Recepción) ──crea/actualiza──► INV (Lote, Stock, Movimiento)
                                    └──► QMS (Inspección de ingreso)
WMS ──ubica/picking──► INV (verdad de cantidad) + LOG (despacho)
```

### 5.3 Ciclo order-to-cash

```
CRM ──► SLS (Pedido) ──► WMS (oleada/picking) ──► LOG (Despacho)
                         └──► BILL (Factura) ──► FIN (asiento, futuro)
PRC ──precio──► SLS / POS / BILL
```

### 5.4 Ciclo plan-to-produce

```
MPS / MRP ──planifican──► MFG (Orden de Producción)
PLN ──capacidad──► MFG / (futuro APS)
MFG ──libera OP──► MES (Ejecución)
MES ──tiempos/paradas──► PLN (feedback de uso) / ALR
MFG/MES ──consumo/producción──► INV (Lote, Movimiento, Stock)
QMS ──inspecciona──► INV (estado de Lote)
```

### 5.5 Integración asíncrona

```
Cualquier dominio productor ──emite Domain Event──► EVT
EVT ──distribuye──► ALR · WFL · Verticales · proyecciones futuras
```

---

## 6. Límites de responsabilidad (anti-mezcla)

| Frontera | Regla |
|----------|-------|
| **IAM ↔ ORG/ERP** | IAM autentica y autoriza; no es dueño del `cliente_id`/`empresa_id` operativo de datos |
| **INV ↔ WMS** | INV es dueño de producto, lote, stock lógico y movimientos; WMS es dueño de ubicación, tarea y oleada |
| **MFG ↔ MES** | MFG define y ordena; MES ejecuta y mide piso; una sola verdad de consumo de materiales |
| **PLN ↔ APS** | PLN es capacidad/calendario; APS (futuro) es scheduling; APS no vive dentro de PLN ni MFG |
| **QMS ↔ INV** | QMS decide resultado de inspección; INV (Lote) materializa estado cuarentena/disponible/rechazado |
| **ALR ↔ EVT** | ALR no es el bus; solo consume eventos y umbrales |
| **SLS ↔ BILL** | SLS vende (pedido); BILL fiscaliza (comprobante) |
| **Core ↔ Vertical** | Core no emite semántica de rubro; Vertical no redefine aggregates Core |

---

## 7. Qué pertenece al Core

Capacidades **agnósticas de industria** usadas por la mayoría de verticales manufactureras / distribución industrial, incluyendo (no exhaustivo):

- Organización multiempresa y gobernanza de verticales habilitadas
- Producto, variante genérica, lote, serie, stock, movimiento
- Almacén, ubicación, oleada, estrategia de salida
- Compra, recepción, venta, despacho, facturación
- Calidad genérica (inspección / NC) ligada a lote
- BOM, ruta, orden de producción, ejecución de piso, OEE genérico
- Capacidad por centro de trabajo / calendario
- MRP/MPS genéricos
- Personas, finanzas básicas, costos/presupuestos (evolución)
- Eventos de dominio + alertas como consumidor
- Auditoría, documentos, workflow transversal

---

## 8. Qué nunca debe pertenecer al Core

| Prohibido en Core | Destino |
|-------------------|---------|
| Galgas, rollos, partidas textiles tipadas | Vertical TXT |
| HACCP / cadena de frío tipada | Vertical FOD |
| Coladas, aleaciones, tratamientos tipados | Vertical MET |
| NDC / registros sanitarios tipados | Vertical MED |
| Recetas de proceso específicas de industria | Vertical correspondiente |
| Matrices de tallaje fashion como catálogo rígido | Vertical TXT / retail fashion |
| JSON de configuración con claves de rubro en CFG | Vertical |
| Referencias FK desde Core hacia catálogos de Vertical | Prohibido |
| Semántica APS completa como dependencia de ola 1 | Diferido (APS futuro) |
| Lógica de negocio escondida en JSON | Prohibido (norma ADR-10) |

---

## 9. Dominios diferidos (existen en el mapa, no en la ola física)

| Dominio | Rol conceptual ahora |
|---------|----------------------|
| **APS** | Extensión futura de scheduling; consume PLN + MFG + MES |
| **RPT semántica** | Extensión futura de métricas/dimensiones gobernadas |
| Subledgers FIN avanzados | Deuda Core faseable (CxC/CxP/bancos) |
| CAPA/SPC QMS enterprise | Evolución de QMS |
| WMS slotting/yard | Evolución de WMS |

Estos dominios **no se borran del mapa**; se congelan como *no implementados físicamente* hasta su fase.

---

## 10. Criterio de cierre de este documento

El modelo de dominio queda cerrado cuando:

1. Todo módulo del mapa Core tiene un dominio dueño.
2. Las fronteras INV/WMS, MFG/MES, PLN/APS, QMS/INV, EVT/ALR están explícitas.
3. La lista de “nunca en Core” es operativa para Verticales.
4. No se requieren tablas para entender el mapa.

**Estado:** cerrado.
