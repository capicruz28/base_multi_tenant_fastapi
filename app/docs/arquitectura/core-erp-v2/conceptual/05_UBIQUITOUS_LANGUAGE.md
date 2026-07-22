# Lenguaje Ubicuo del Core ERP

**Documento:** Etapa 0.5 · 05  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado)  
**Alcance:** Definiciones oficiales — **una definición por término**

---

## 1. Propósito

Este glosario es la **única fuente de significado** de los términos del Core.

Reglas:

1. Un término = una definición.
2. Sinónimos de industria se traducen en el Vertical; no renombran el Core.
3. Si un término aparece en código, UI Core o eventos, debe respetar esta definición.
4. Ambigüedades se resuelven aquí, no en conversaciones ad hoc.

---

## 2. Plataforma y organización

| Término | Definición oficial |
|---------|-------------------|
| **Tenant / Cliente** | Unidad de aislamiento SaaS dueña de los datos (`cliente_id`). En despliegue dedicado coincide con la BD del cliente. |
| **Empresa** | Unidad legal/operativa MultiEmpresa dentro del tenant. Todo dato operativo ERP se scopea por empresa cuando aplica. |
| **Sucursal** | Subdivisión geográfica/operativa de una Empresa. |
| **Centro de Costo** | Unidad de acumulación de costos dentro de la Empresa. |
| **Vertical** | Paquete de conocimiento y capacidades de una industria (TXT, FOD, …), habilitado por Empresa vía CFG. No es un módulo Core de negocio tipado. |
| **Capacidad Core** | Función agnóstica de industria disponible en la plataforma. |
| **Sesión ERP** | Contexto operativo (tenant/empresa/usuario/permisos) usado por módulos ERP; distinto de la sola identidad IAM. |
| **Impersonación** | Modo en que un operador de plataforma actúa sobre un tenant; el `cliente_id` de datos es el del tenant impersonado, no el de la fila SYSTEM del operador. |

---

## 3. Producto e inventario

| Término | Definición oficial |
|---------|-------------------|
| **Producto** | Ítem maestro del inventario/comercial/manufactura. Puede comprarse, venderse, fabricarse y/o almacenarse según flags. Es Aggregate Root. |
| **Variante** | Especialización genérica de un Producto mediante ejes de atributo (ej. color, talla, voltaje, envase) que define un SKU diferenciado. No implica semántica de un rubro. |
| **SKU** | Código de unidad stockeable/vendible. En el Core, el SKU concreto es el Producto stockeable asociado a la Variante (política de integración Producto↔Variante). |
| **Lote** | Partida identificable de un Producto con trazabilidad, fechas relevantes, origen y cantidades lógicas (disponible/reservada/bloqueada) y estado. Aggregate Root. |
| **Serie** | Identificador unitario de una pieza/unidad individual de un Producto que maneja series. |
| **Vencimiento** | Fecha límite de uso/consumo/venta asociada típicamente a un Lote (cuando el Producto maneja vencimiento). |
| **Almacén** | Contenedor de stock a nivel de instalación/lógico de la Empresa. Define estrategia de salida por defecto. |
| **Stock** | Saldo de cantidad de un Producto (y Lote cuando aplica) en un Almacén. Es **cantidad derivada**, no un documento editable libre. |
| **Movimiento** | Documento transaccional de inventario que causa cambios de Stock (entrada, salida, transferencia, ajuste, producción, consumo). |
| **Reserva** | Compromiso de cantidad de Stock para un documento origen (p. ej. Pedido) que reduce lo disponible sin ser aún salida definitiva. |
| **Disponible** | Cantidad de Stock/Lote libre para asignar (no reservada ni bloqueada). |
| **Bloqueado** | Cantidad o Lote impedido de uso operativo (calidad, daño, retención). |
| **Cuarentena** | Estado de Lote pendiente de disposición de calidad; no disponible para uso normal. |
| **Estrategia de salida** | Política de selección de Lote/ubicaciones al despachar: FIFO, FEFO, LEFO o MANUAL. |
| **FIFO** | Primero en entrar, primero en salir (por fecha de ingreso). |
| **FEFO** | Primero en vencer, primero en salir (por fecha de vencimiento). |
| **LEFO** | Último en entrar, primero en salir. |
| **MANUAL** | Selección explícita por el operario/usuario. |
| **Inventario físico** | Proceso de conteo de existencias reales y reconciliación con el sistema. |

**Prohibido:** usar “lote” como string sin identidad; usar “variante” para recetas de industria; llamar “stock” a una ubicación WMS.

---

## 4. Almacén (WMS)

| Término | Definición oficial |
|---------|-------------------|
| **Zona** | Agrupación lógica de ubicaciones dentro de un Almacén. |
| **Ubicación** | Posición específica donde puede residir stock dentro del Almacén. |
| **Stock por ubicación** | Saldo de Producto/Lote en una Ubicación concreta. |
| **Tarea de almacén** | Unidad de trabajo WMS (picking, putaway, reposición, conteo, etc.). |
| **Oleada (Wave)** | Agrupación de Tareas de almacén liberadas/ejecutadas como conjunto. |
| **Picking** | Extracción de mercadería desde ubicaciones para un pedido/ola. |
| **Putaway** | Ubicación de mercadería ingresada en posiciones de almacén. |

---

## 5. Calidad

| Término | Definición oficial |
|---------|-------------------|
| **Parámetro de calidad** | Característica medible/evaluable genérica (no tipada por industria). |
| **Plan de inspección** | Definición de qué parámetros y muestreo aplican a un contexto. |
| **Inspección** | Ejecución de un control de calidad con resultado (aprobado/rechazado/condicional). |
| **No Conformidad (NC)** | Registro de desviación respecto a un requisito de calidad. |
| **Disposición** | Decisión sobre el material no conforme (liberar, reprocesar, rechazar, destruir, etc.) a nivel genérico. |

**Nota:** checklists HACCP, NDC, galgas, etc. son términos de Vertical, no del Core.

---

## 6. Compras, ventas y logística

| Término | Definición oficial |
|---------|-------------------|
| **Proveedor** | Parte de la que la Empresa adquiere bienes/servicios. |
| **Orden de Compra (OC)** | Compromiso de compra emitido al Proveedor. |
| **Recepción** | Documento de ingreso de mercadería proveniente de una compra (u origen de ingreso asociado). |
| **Cliente** | Parte a la que la Empresa vende (maestro comercial SLS). |
| **Cotización de venta** | Oferta comercial previa al Pedido. |
| **Pedido (Pedido de venta)** | Demanda firme del Cliente. |
| **Lista de precio** | Conjunto de precios vigentes aplicables a Productos/Variantes. |
| **Despacho** | Proceso/documento de salida logística hacia destino. |
| **Guía de remisión** | Documento de transporte/remisión asociado al Despacho (localización documental). |
| **Factura / Comprobante** | Documento fiscal de venta emitido por BILL. |
| **Reserva de pedido** | Reserva de inventario originada por un Pedido confirmado. |

---

## 7. Manufactura, ejecución y capacidad

| Término | Definición oficial |
|---------|-------------------|
| **Centro de Trabajo (CT)** | Recurso productivo donde se ejecutan operaciones (máquina, línea, celda, puesto). |
| **Operación** | Paso estándar de fabricación (definición). |
| **Lista de Materiales (BOM)** | Estructura de componentes requeridos para fabricar un Producto. |
| **Ruta de fabricación** | Secuencia de Operaciones/CT para fabricar un Producto. |
| **Orden de Producción (OP)** | Orden para fabricar una cantidad de Producto según BOM/Ruta. |
| **Liberación de OP** | Transición que hace la OP ejecutable en piso. |
| **Consumo de materiales** | Registro de materiales usados por una OP (verdad de consumo en MFG). |
| **Producción reportada** | Declaración de cantidad fabricada (buena/merma según política) hacia inventario. |
| **Ejecución** | Registro real en MES de la realización de una operación de OP en el tiempo. |
| **Parada** | Interrupción registrada durante una Ejecución, clasificada por motivo OEE genérico. |
| **OEE** | Marco genérico de disponibilidad/rendimiento/calidad para análisis de performance de piso. |
| **Capacidad** | Horas (u otra unidad) disponibles de un CT en un intervalo (fecha/turno), administradas por PLN. |
| **Calendario de capacidad** | Serie temporal de Capacidad y excepciones (feriado, mantenimiento, parada programada). |
| **MRP** | Cálculo de necesidades de materiales y sugerencias de compra/fabricación. |
| **MPS** | Plan maestro agregado de producción / demanda planificada. |
| **APS** | Programación avanzada / scheduling finito (dominio futuro; no capacidad física actual). |

**Separación obligatoria:**  
- **MFG** define y ordena.  
- **MES** ejecuta y mide.  
- **PLN** declara capacidad.  
- **APS** (futuro) secuencia.

---

## 8. Personas, finanzas y alertas

| Término | Definición oficial |
|---------|-------------------|
| **Empleado** | Persona en relación laboral administrada por HCM. |
| **Operario** | Rol de Empleado cuando ejecuta trabajo de piso (MES) o almacén (WMS). |
| **Planilla** | Proceso de liquidación salarial de un periodo. |
| **Asiento contable** | Registro contable en el libro diario. |
| **Periodo contable** | Intervalo temporal de contabilización abierto/cerrado. |
| **Costo** | Valor económico asignado a producto/actividad (CST); no es precio de venta. |
| **Precio** | Valor comercial de venta (PRC); no es costo. |
| **Alerta** | Aviso generado por ALR a partir de una regla y/o evento. |
| **Regla de alerta** | Definición de condición/suscripción que puede generar Alertas. |
| **Evento de dominio** | Hecho de negocio inmutable ya ocurrido, publicado para consumidores. |

---

## 9. Términos explícitamente prohibidos / desambiguados

| Uso incorrecto | Corrección |
|----------------|------------|
| “Lote” = texto libre en línea | Usar **Lote** (AR) + identidad |
| “Partida” / “Batch” / “Colada” como renombre Core | Son sinónimos de Vertical; el Core dice **Lote** |
| “SAL” como módulo de ventas | El código oficial es **SLS** |
| “ALR = Event Bus” | **EVT** es el bus; **ALR** es consumidor |
| “MES = MFG” | Contextos distintos |
| “Capacidad = scheduling” | Capacidad es PLN; scheduling es APS futuro |
| “Stock = ubicación” | Stock es saldo INV; ubicación es WMS |
| “Variante textil” en Core | Variante es genérica; tipado textil en TXT |
| “JSON de configuración de rubro en CFG” | Prohibido en Core |

---

## 10. Criterio de cierre

El lenguaje ubicuo queda cerrado cuando todo documento conceptual Etapa 0.5 usa estos términos sin sinónimos conflictivos.

**Estado:** cerrado. Toda ambigüedad nueva se resuelve por enmienda versionada de este glosario.
