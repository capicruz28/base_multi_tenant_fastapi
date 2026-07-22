# Aggregate Roots oficiales del Core

**Documento:** Etapa 0.5 · 03  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado a nivel conceptual)  
**Alcance:** Entidades de dominio — **sin tablas ni SQL**

---

## 1. Propósito

Definir los **Aggregate Roots (AR)** oficiales del Core: unidades de consistencia transaccional y de invariantes de negocio.

Reglas:

- Un AR tiene identidad global en su Bounded Context.
- Las entidades internas solo se modifican a través del AR.
- Otros contextos referencian el AR por identidad; no mutan su interior.
- Este documento **no** diseña persistencia.

---

## 2. Clasificación de Aggregates

| Categoría | Aggregates |
|-----------|------------|
| Organización | Empresa, Sucursal, CentroCosto |
| Producto e inventario | Producto, VarianteProducto, Lote, Serie, Almacen, MovimientoInventario, InventarioFisico |
| Almacén | Ubicacion, Oleada, TareaAlmacen |
| Calidad | PlanInspeccion, Inspeccion, NoConformidad |
| Compras | Proveedor, OrdenCompra, Recepcion |
| Ventas | Cliente, PedidoVenta, CotizacionVenta |
| Precios | ListaPrecio |
| Logística | GuiaRemision, Despacho |
| Manufactura | ListaMateriales, RutaFabricacion, OrdenProduccion |
| Ejecución | EjecucionOperacion |
| Capacidad | CalendarioCapacidad |
| Planificación | PlanMRP, PlanMPS |
| Mantenimiento | Activo, OrdenTrabajoMantenimiento |
| Personas | Empleado, Planilla |
| Facturación | Comprobante |
| POS | VentaPOS |
| Finanzas | AsientoContable, PeriodoContable |
| Gobernanza | VerticalEmpresa, SecuenciaCodigo |
| Alertas | ReglaAlerta |

Los stubs (Proyecto, Ticket, …) no se elevan a AR oficiales hasta su fase.

---

## 3. Catálogo de Aggregate Roots

### 3.1 Empresa (`ORG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Unidad legal/operativa MultiEmpresa del tenant |
| Ciclo de vida | Creada → activa → (desactivada/soft) |
| Quién modifica | ORG (administradores de tenant/empresa según RBAC) |
| Dependen de él | Casi todos los aggregates operativos (scope `empresa`) |

### 3.2 Sucursal / CentroCosto (`ORG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Subdivisiones operativas y de costo |
| Ciclo de vida | Activo/inactivo |
| Quién modifica | ORG |
| Dependen | Almacen, Pedido, empleados, documentos según política |

---

### 3.3 Producto (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Maestro stockeable/comprable/fabricable/vendible; identidad comercial y logística del ítem |
| Ciclo de vida | Borrador/activo/descontinuado/inactivo |
| Quién modifica | INV (maestros); otros solo leen |
| Dependen | Variante, Lote, Serie, Stock, líneas de documentos, BOM |

**Invariantes clave:** flags `maneja_lotes` / `maneja_series` / `maneja_vencimiento` gobiernan obligatoriedad de Lote/Serie en movimientos.

### 3.4 VarianteProducto (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Especialización genérica multi-eje de un Producto (SKU diferenciado) |
| Ciclo de vida | Activa / inactiva / descontinuada |
| Quién modifica | INV |
| Dependen | Stock y documentos que venden/compran el SKU concreto |

**Invariante:** toda Variante se integra al maestro stockeable; no existe “variante huérfana” sin política de Producto. Sin FKs a catálogos de Vertical.

### 3.5 Lote (`INV`) — Aggregate Root canónico V2

| Campo | Definición |
|-------|------------|
| Responsabilidad | Identidad y estado de una partida/lote de un Producto; trazabilidad y cantidades lógicas |
| Ciclo de vida | Creado → (cuarentena) → disponible → (bloqueado) → agotado / vencido / rechazado |
| Quién modifica | INV (cantidades/estado logístico); QMS influye vía resultado de inspección (política); WMS no redefine el AR |
| Dependen | Movimientos, stock lotificado, inspecciones, recepciones, consumos, facturas, tareas WMS |

**Invariantes:**  
- Identidad única por empresa+producto+código de lote.  
- Cantidades: inicial ≥ disponible+reservada+bloqueada (regla conceptual).  
- Origen tipado (compra, producción, devolución, apertura, ajuste).

### 3.6 Serie (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Identidad unitaria serializada de un ítem |
| Ciclo de vida | Creada → en stock → despachada / instalada / baja |
| Quién modifica | INV |
| Dependen | Movimientos y documentos cuando `maneja_series` |

*(Capacidad Core; detalle físico faseable tras Lote si se prioriza.)*

### 3.7 Almacen (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Contenedor lógico/físico de stock a nivel almacén; estrategia de salida por defecto |
| Ciclo de vida | Activo/inactivo |
| Quién modifica | INV |
| Dependen | Stock, Ubicaciones WMS, movimientos |

### 3.8 MovimientoInventario (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Documento transaccional que cambia stock (entrada/salida/transferencia/ajuste) |
| Ciclo de vida | Borrador → procesado → (anulado/estornado según política) |
| Quién modifica | INV (servicios de inventario); orquestadores llaman a INV, no escriben stock directo |
| Dependen | Detalles de movimiento; impacto en Stock/Lote |

### 3.9 InventarioFisico (`INV`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Conteo y ajuste de existencia real vs sistema |
| Ciclo de vida | Abierto → contado → ajustado/cerrado |
| Quién modifica | INV |
| Dependen | Detalles de conteo; posibles movimientos de ajuste |

---

### 3.10 Ubicacion (`WMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Posición pickeable/almacenable dentro de un almacén |
| Ciclo de vida | Activa / bloqueada / inactiva |
| Quién modifica | WMS |
| Dependen | Stock por ubicación, tareas |

### 3.11 Oleada (`WMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Agrupador de trabajo de almacén (wave) |
| Ciclo de vida | Pendiente → liberada → en progreso → completada / cancelada |
| Quién modifica | WMS |
| Dependen | Tareas de almacén |

### 3.12 TareaAlmacen (`WMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Unidad de trabajo (picking, putaway, reposición, etc.) |
| Ciclo de vida | Pendiente → asignada → en curso → completada / cancelada |
| Quién modifica | WMS |
| Dependen | Ejecución operativa; puede referenciar Pedido/Lote/Ubicacion |

---

### 3.13 PlanInspeccion (`QMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Definición de qué y cómo inspeccionar |
| Ciclo de vida | Activo/inactivo / versionado conceptualmente |
| Quién modifica | QMS |
| Dependen | Inspecciones ejecutadas |

### 3.14 Inspeccion (`QMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Ejecución de control de calidad sobre producto/lote/documento |
| Ciclo de vida | Planificada → en curso → aprobada / rechazada / cancelada |
| Quién modifica | QMS |
| Dependen | Detalles; efecto de estado sobre Lote (vía política INV) |

### 3.15 NoConformidad (`QMS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Registro y seguimiento de desviaciones de calidad |
| Ciclo de vida | Abierta → en tratamiento → cerrada / anulada |
| Quién modifica | QMS |
| Dependen | Acciones correctivas (evolución CAPA) |

---

### 3.16 Proveedor (`PUR`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Maestro de proveedor |
| Ciclo de vida | Activo/inactivo |
| Quién modifica | PUR |
| Dependen | OC, recepciones, lotes de origen compra |

### 3.17 OrdenCompra (`PUR`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Compromiso de compra con proveedor |
| Ciclo de vida | Borrador → emitida → parcial/recibida → cerrada / anulada |
| Quién modifica | PUR |
| Dependen | Detalles; Recepcion |

### 3.18 Recepcion (`PUR`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Ingreso físico/documental de mercancía comprada |
| Ciclo de vida | Borrador → registrada → (inspección) → cerrada |
| Quién modifica | PUR (documento); INV crea/actualiza Lote/Stock; QMS puede inspeccionar |
| Dependen | Detalles de recepción |

---

### 3.19 Cliente (`SLS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Maestro de cliente comercial |
| Ciclo de vida | Activo/inactivo |
| Quién modifica | SLS |
| Dependen | Pedidos, cotizaciones, facturas |

### 3.20 CotizacionVenta (`SLS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Oferta comercial pre-pedido |
| Ciclo de vida | Borrador → enviada → aceptada/rechazada/vencida |
| Quién modifica | SLS |
| Dependen | Posible conversión a Pedido |

### 3.21 PedidoVenta (`SLS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Demanda firme del cliente |
| Ciclo de vida | Borrador → confirmado → (reservado/picking/despachado/facturado) → cerrado / anulado |
| Quién modifica | SLS (estado comercial); WMS/LOG/BILL avanzan fulfillment vía orquestación/eventos |
| Dependen | Detalles; reservas; oleadas; despachos; facturas |

### 3.22 ListaPrecio (`PRC`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Condiciones de precio aplicables |
| Ciclo de vida | Activa en vigencia / vencida / inactiva |
| Quién modifica | PRC |
| Dependen | Cotizaciones, pedidos, POS (lectura) |

---

### 3.23 GuiaRemision / Despacho (`LOG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Documentos de salida logística hacia destino |
| Ciclo de vida | Borrador → emitida/confirmada → en tránsito → entregada / anulada |
| Quién modifica | LOG |
| Dependen | Detalles; vínculo a Pedido; impacto stock vía INV |

---

### 3.24 ListaMateriales (BOM) (`MFG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Qué componentes componen un producto fabricable |
| Ciclo de vida | Versionada: activa / obsoleta |
| Quién modifica | MFG |
| Dependen | OP, MRP |

### 3.25 RutaFabricacion (`MFG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Secuencia de operaciones y centros para fabricar |
| Ciclo de vida | Versionada: activa / obsoleta |
| Quién modifica | MFG |
| Dependen | OP, MES, PLN (lectura de CT) |

### 3.26 OrdenProduccion (`MFG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Orden para fabricar una cantidad de producto |
| Ciclo de vida | Planificada → liberada → en proceso → terminada / cerrada / anulada |
| Quién modifica | MFG |
| Dependen | Operaciones de OP; Ejecuciones MES; consumos; lotes de salida |

---

### 3.27 EjecucionOperacion (`MES`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Registro real de ejecución de una operación de OP en el piso |
| Ciclo de vida | En curso → pausada → completada / cancelada |
| Quién modifica | MES |
| Dependen | Paradas; feedback OEE; tiempos reales |

---

### 3.28 CalendarioCapacidad (`PLN`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Capacidad disponible de un centro de trabajo en una fecha/turno |
| Ciclo de vida | Vigente / excepcional (feriado, mantenimiento) |
| Quién modifica | PLN |
| Dependen | Planificación MFG/MRP/MPS; futuro APS |

---

### 3.29 PlanMRP / PlanMPS (`MRP` / `MPS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Corridas de planificación de materiales / plan maestro |
| Ciclo de vida | Borrador → calculado → (publicado) → archivado |
| Quién modifica | MRP / MPS respectivamente |
| Dependen | Sugerencias; no liberan solos OC/OP |

---

### 3.30 Activo / OrdenTrabajoMantenimiento (`MNT`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Activo mantenible y su OT |
| Ciclo de vida | OT: abierta → en curso → cerrada |
| Quién modifica | MNT |
| Dependen | Señalización de indisponibilidad a PLN/MES |

---

### 3.31 Empleado / Planilla (`HCM`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Persona laboral y liquidación |
| Ciclo de vida | Empleado activo/baja; Planilla abierta→cerrada |
| Quién modifica | HCM |
| Dependen | Operario en MES; costos laborales (futuro CST) |

---

### 3.32 Comprobante (`BILL`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Documento fiscal de venta |
| Ciclo de vida | Borrador → emitido → (anulado/nota crédito según política) |
| Quién modifica | BILL |
| Dependen | Detalles; referencia Pedido/Lote; asientos futuros |

### 3.33 VentaPOS (`POS`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Venta de mostrador en un turno |
| Ciclo de vida | Abierta → cobrada/cerrada / anulada |
| Quién modifica | POS |
| Dependen | Impacto stock/factura según política |

---

### 3.34 PeriodoContable / AsientoContable (`FIN`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Cierre temporal contable y registración |
| Ciclo de vida | Periodo abierto/cerrado; Asiento borrador→contabilizado→anulado |
| Quién modifica | FIN |
| Dependen | Reportes financieros; integraciones desde BILL/otros |

---

### 3.35 VerticalEmpresa (`CFG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Declarar qué verticales industriales están habilitadas para una empresa |
| Ciclo de vida | Activa → desactivada |
| Quién modifica | CFG / gobernanza plataforma |
| Dependen | Visibilidad de módulos verticales en aplicación |

### 3.36 SecuenciaCodigo (`CFG`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Política de numeración/códigos por scope |
| Ciclo de vida | Activa |
| Quién modifica | CFG |
| Dependen | Generación de códigos de documentos/maestros |

### 3.37 ReglaAlerta (`ALR`)

| Campo | Definición |
|-------|------------|
| Responsabilidad | Definición de cuándo generar una alerta |
| Ciclo de vida | Activa/inactiva |
| Quién modifica | ALR |
| Dependen | Instancias de alerta generadas |

---

## 4. Entidades internas notables (no son AR)

Estas viven **dentro** de un AR y no se exponen como raíz de consistencia independiente para escritura desde fuera:

| Entidad interna | AR dueño |
|-----------------|----------|
| Línea de movimiento | MovimientoInventario |
| Línea de pedido | PedidoVenta |
| Línea de OC / recepción | OrdenCompra / Recepcion |
| Detalle BOM / ruta | ListaMateriales / RutaFabricacion |
| Operación de OP | OrdenProduccion |
| Parada de máquina | EjecucionOperacion |
| Detalle de inspección | Inspeccion |
| Detalle de comprobante | Comprobante |
| Stock (saldo) | Proyección/entidad de INV gobernada por Movimiento/Lote — no documento raíz |

**Stock** no es un documento AR: es el **saldo derivado** cuya verdad se actualiza por Movimientos (y políticas de Lote/Reserva). Se trata como entidad de inventario bajo control de INV, no como documento editable libremente.

---

## 5. Reglas de modificación cruzada

1. Solo el BC dueño muta el AR.
2. Un BC externo puede **solicitar** un cambio vía servicio de aplicación del dueño o reaccionar a eventos.
3. Ejemplo: QMS no “escribe cuarentena” en tablas ajenas; publica/solicita transición de estado de Lote a INV.
4. MES no crea Movimientos arbitrarios; reporta producción/consumo según política MFG→INV.

---

## 6. Criterio de cierre

Los Aggregate Roots quedan cerrados cuando:

1. Cada AR tiene un único BC dueño.
2. Lote y Producto/Variante están definidos como raíces canónicas V2.
3. MFG (OP) y MES (Ejecución) están separados.
4. Stock queda explícitamente como saldo, no como documento raíz.

**Estado:** cerrado.
