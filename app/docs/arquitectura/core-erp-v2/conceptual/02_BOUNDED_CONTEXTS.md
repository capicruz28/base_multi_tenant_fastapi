# Bounded Contexts del Core ERP

**Documento:** Etapa 0.5 · 02  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado a nivel conceptual)  
**Alcance:** Contextos delimitados — **sin tablas ni SQL**

---

## 1. Propósito

Un **Bounded Context (BC)** es el límite dentro del cual un modelo de lenguaje y reglas es coherente y dueño de su verdad.

Este documento fija los BC oficiales del Core. El código de módulo (`INV`, `SLS`, …) coincide con el BC salvo donde se indica alias (`BILL` = `INV_BILL`).

**Nota de nomenclatura:** el contexto de ventas oficiales es **SLS** (no `SAL`). `SAL` no es código oficial.

---

## 2. Mapa de Bounded Contexts

### 2.1 Plataforma

| BC | Madurez conceptual |
|----|--------------------|
| IAM | Activo |
| ORG | Activo |
| CFG | Activo (incluye verticales habilitadas) |
| CAT | Activo |
| EVT | Activo (infra de eventos) |
| ALR | Activo |
| AUD | Activo |
| WFL | Stub / evolución |
| DMS | Stub / evolución |
| BI/RPT | Stub; semántica diferida |

### 2.2 Operativos Core

| BC | Madurez conceptual |
|----|--------------------|
| CRM | Activo |
| SLS | Activo |
| PRC | Activo |
| POS | Activo |
| BILL | Activo |
| PUR | Activo |
| LOG | Activo |
| INV | Activo (elevado V2: Lote, Variante) |
| WMS | Activo (elevado V2: Oleada, estrategia) |
| QMS | Activo (elevado V2: vínculo Lote) |
| PLN | Activo (nuevo V2) |
| MRP | Activo |
| MPS | Activo |
| MFG | Activo |
| MES | Activo (nuevo V2) |
| MNT | Activo |
| HCM | Activo |
| FIN | Activo (evolución subledgers diferida) |
| TAX | Activo (básico) |
| BDG | Activo |
| CST | Activo (evolución) |

### 2.3 Reserva / futuro

| BC | Estado |
|----|--------|
| PM, SVC, TKT | Stub de namespace |
| APS | Futuro (sin capacidad física ola 1) |
| Verticales (TXT, FOD, …) | Fuera del Core; BC propios |

---

## 3. Especificación por Bounded Context

Para cada BC:

- **Responsabilidad**
- **Qué administra** (verdad propia)
- **Qué no administra**
- **Qué comparte** (contratos / lecturas / eventos)
- **Qué nunca debe compartir** (fuga de modelo)

---

### IAM — Identidad y acceso

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Autenticar usuarios, emitir tokens, aplicar RBAC, soportar impersonación |
| Administra | Identidad, credenciales, roles/permisos, sesiones de autenticación |
| No administra | Empresa operativa, stock, documentos ERP, menú de vertical |
| Comparte | Identidad de usuario (`usuario_id`), claims de permisos, flag de impersonación |
| Nunca comparte | Secretos, hashes, tokens crudos hacia dominios ERP; no impone `cliente_id` de datos ERP desde fila SYSTEM del operador |

---

### ORG — Organización

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Definir el contexto organizacional MultiEmpresa del tenant |
| Administra | Empresa, sucursal, departamentos org., cargos, centros de costo, parámetros de empresa |
| No administra | Productos, stock, pedidos, permisos IAM, semántica de vertical |
| Comparte | Identificadores de empresa/sucursal/CC; datos maestros org. de solo lectura |
| Nunca comparte | Reglas de inventario, precios, ni configuración JSON de industria |

---

### CFG — Configuración de plataforma ERP

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Gobernar capacidades Core y verticales habilitadas por empresa |
| Administra | Secuencias de código; flags de vertical activa; políticas de generación de códigos |
| No administra | Contenido de negocio de un vertical; menú hardcodeado por rubro en código |
| Comparte | Código de vertical habilitada; scope de secuencia |
| Nunca comparte | `configuracion_json` con claves de industria; catálogos TXT/FOD |

---

### CAT — Catálogos de referencia

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Datos de referencia transversales y estables |
| Administra | Geografía, monedas, y catálogos genéricos no industriales |
| No administra | Categorías de producto de negocio (eso es INV); catálogos de vertical |
| Comparte | Códigos y nombres de referencia |
| Nunca comparte | Atributos de industria (galgas, NDC, aleaciones) |

---

### EVT — Eventos (infraestructura)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Publicar y entregar eventos de dominio entre contextos |
| Administra | Contrato de transporte, ordenamiento/idempotencia a nivel infra, suscripciones técnicas |
| No administra | Reglas de alerta, workflows de negocio, semántica de aggregates |
| Comparte | Envelopes de evento versionados |
| Nunca comparte | Lógica de negocio dentro del transporte; no sustituye transacciones del productor |

---

### ALR — Alertas

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Evaluar reglas y generar alertas accionables |
| Administra | Definición de reglas de alerta; instancias de alerta; estado de lectura/atención |
| No administra | El bus de eventos; stock; órdenes |
| Comparte | Alertas generadas hacia UI/notificaciones |
| Nunca comparte | No impone cambios de estado en aggregates ajenos sin política explícita |

---

### AUD — Auditoría

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Registrar quién cambió qué y cuándo (trazabilidad técnica) |
| Administra | Log de auditoría append-oriented |
| No administra | Estados de negocio ni workflows |
| Comparte | Consultas de auditoría |
| Nunca comparte | No es fuente de verdad de stock ni documentos |

---

### CRM — Relación con clientes (pre-venta)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Gestionar pipeline comercial previo al pedido firme |
| Administra | Campañas, leads, oportunidades, actividades CRM |
| No administra | Pedidos firmes (SLS), precios oficiales (PRC), facturas |
| Comparte | Identificadores de oportunidad/lead; conversión hacia cliente SLS |
| Nunca comparte | Stock ni reservas de inventario |

---

### SLS — Ventas

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Convertir demanda en pedidos y administrar el ciclo comercial de venta |
| Administra | Cliente comercial, contactos/direcciones de cliente, cotizaciones, pedidos |
| No administra | Stock físico, picking, factura fiscal, precios maestros (lee PRC) |
| Comparte | Pedido confirmado (evento); líneas con producto/cantidad/fechas |
| Nunca comparte | Movimientos de inventario ni estados de lote |

---

### PRC — Precios

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Definir precios y promociones aplicables |
| Administra | Listas de precio, detalle por producto/variante, promociones |
| No administra | Pedidos, facturas, costos industriales (CST) |
| Comparte | Precio aplicable resuelto |
| Nunca comparte | Stock ni reglas de vertical de descuento tipadas en Core |

---

### POS — Punto de venta

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Ventas de mostrador con turno de caja |
| Administra | Punto de venta, turnos, ventas POS |
| No administra | Pedidos B2B (SLS), WMS completo |
| Comparte | Venta cerrada; impacto a stock/factura según política |
| Nunca comparte | Semántica de vertical retail fashion como modelo Core |

---

### BILL — Facturación (`INV_BILL`)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Emitir y administrar comprobantes fiscales/electrónicos de venta |
| Administra | Series, comprobantes, detalle fiscal |
| No administra | Pedido comercial (SLS), stock (INV) — solo referencia e impacto vía eventos/servicios |
| Comparte | Factura emitida; montos; referencias a pedido/cliente/producto/lote |
| Nunca comparte | Lógica SUNAT como “vertical industrial”; es localización fiscal, no conocimiento de rubro |

---

### PUR — Compras

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Abastecer materiales/servicios desde proveedores |
| Administra | Proveedor, solicitudes, cotizaciones de compra, OC, recepciones |
| No administra | Stock final (INV es dueño); calidad (QMS); pagos (FIN futuro) |
| Comparte | Recepción registrada; intención de crear lote; cantidades recibidas |
| Nunca comparte | Estados de cuarentena (son de Lote vía QMS/INV) |

---

### LOG — Logística de distribución

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Mover mercancía hacia el cliente / puntos de entrega |
| Administra | Transportista, vehículo, ruta, guía de remisión, despacho |
| No administra | Picking interno (WMS); factura; stock maestro (INV) |
| Comparte | Despacho confirmado; guías; referencias a pedido |
| Nunca comparte | Oleadas WMS ni reglas FEFO |

---

### INV — Inventario

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Ser la verdad de **qué producto/lote/serie existe, en qué cantidad y estado logístico** |
| Administra | Categoría, UoM, Producto, Variante, Lote, Serie (capacidad), Almacén, Stock, Tipo de movimiento, Movimiento, Inventario físico |
| No administra | Ubicación slotting/tareas (WMS); inspección (QMS); precio (PRC) |
| Comparte | Identidad de Producto/Lote/Almacén; saldos; eventos de stock/lote |
| Nunca comparte | Atributos tipados de industria; no permite que Vertical redefina Lote |

---

### WMS — Warehouse Management

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Operar el almacén a nivel ubicación y trabajo |
| Administra | Zona, Ubicación, Stock por ubicación, Tarea, Oleada, estrategia de salida operativa |
| No administra | Maestro de producto/lote (INV); factura; capacidad de planta (PLN) |
| Comparte | Tareas/oleadas completadas; ubicaciones; sugerencias FEFO operativas |
| Nunca comparte | No es dueño del saldo contable/lógico global si diverge — debe reconciliar con INV |

---

### QMS — Calidad

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Evaluar conformidad y registrar no conformidades |
| Administra | Parámetros de calidad, planes de inspección, inspecciones, no conformidades |
| No administra | Cantidades de stock; ejecución de piso (MES); CAPA/SPC enterprise (evolución) |
| Comparte | Resultado de inspección; NC abierta/cerrada; recomendación de estado de lote |
| Nunca comparte | Checklists HACCP tipados / NDC / galgas — eso es Vertical |

---

### PLN — Capacidad y calendarios

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Declarar **capacidad disponible** de recursos productivos en el tiempo |
| Administra | Calendarios de capacidad por centro de trabajo/fecha/turno; excepciones (feriado, parada programada) |
| No administra | Scheduling de operaciones (APS futuro); BOM; ejecuciones reales (MES) |
| Comparte | Horas disponibles / carga planificada; señales de sobrecarga |
| Nunca comparte | Secuencias Gantt ni restricciones polimórficas de APS |

---

### MRP — Plan de materiales

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Calcular necesidades netas de material y sugerir órdenes |
| Administra | Plan MRP, necesidades, explosión, órdenes sugeridas |
| No administra | Liberación firme de OP (MFG); compras firmes (PUR) — solo sugiere |
| Comparte | Sugerencias de compra/fabricación |
| Nunca comparte | Capacidad finita detallada (PLN) ni scheduling (APS) |

---

### MPS — Plan maestro de producción

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Planificar producción a nivel agregado / familia |
| Administra | Pronósticos, plan maestro y su detalle agregado |
| No administra | OP detallada; MES; APS |
| Comparte | Plan agregado; demanda planificada |
| Nunca comparte | Ejecución de piso |

---

### MFG — Manufactura (definición y órdenes)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Definir cómo se fabrica y gestionar órdenes de producción |
| Administra | Centro de trabajo, Operación, BOM, Ruta, Orden de Producción, operaciones de OP, consumo de materiales (verdad de consumo) |
| No administra | Tiempos reales OEE (MES); calendarios de capacidad (PLN); scheduling APS |
| Comparte | OP liberada/cerrada; consumo; producción reportada hacia INV |
| Nunca comparte | Motivos OEE tipados de industria; recetas verticales como reemplazo de BOM Core |

---

### MES — Ejecución de manufactura

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Registrar la realidad del piso de producción |
| Administra | Ejecución de operación, paradas, motivos OEE genéricos, tiempos reales |
| No administra | Definición BOM/ruta; liberación de OP; capacidad calendario (lee PLN/MFG) |
| Comparte | Ejecución iniciada/completada; paradas; feedback de performance |
| Nunca comparte | No redefine OP; no inventa stock sin pasar por política INV/MFG |

---

### MNT — Mantenimiento

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Mantener activos productivos |
| Administra | Activo, plan de mantenimiento, OT de mantenimiento, historial |
| No administra | OP de fabricación; stock de repuestos formales (evolución); OEE (MES) |
| Comparte | OT abierta/cerrada; indisponibilidad de activo (señal a PLN/MES vía eventos) |
| Nunca comparte | No es dueño de capacidad (PLN) aunque la afecte |

---

### HCM — Personas

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Administrar el capital humano y planilla |
| Administra | Empleado, contrato, conceptos, planilla, asistencia, vacaciones, préstamos |
| No administra | Asignación fina de scheduling APS; costos de producto (CST) |
| Comparte | Identidad de empleado/operario hacia MES |
| Nunca comparte | Datos salariales sensibles hacia dominios no autorizados |

---

### FIN / TAX / BDG / CST — Control económico

| BC | Responsabilidad resumida | No administra |
|----|--------------------------|---------------|
| **FIN** | Contabilidad general (cuentas, periodos, asientos) | Factura fiscal (BILL); stock |
| **TAX** | Obligaciones tributarias / libros | Diseño de Lote |
| **BDG** | Presupuesto | Ejecución de piso |
| **CST** | Costeo de producto/centros | Precio de venta (PRC) |

**Comparten:** asientos, saldos contables, costos unitarios publicados.  
**Nunca comparten:** semántica de vertical; no redefinen Movimiento de INV.

---

### APS — Programación avanzada (futuro)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad futura | Secuenciar y simular carga finita de operaciones |
| Administra (futuro) | Escenarios, tareas programadas, restricciones tipadas |
| No administra ahora | Nada físico en ola 1 |
| Comparte (futuro) | Plan secuenciado; impacto simulado |
| Nunca | Vivir dentro de MFG/PLN como tablas disfrazadas antes de tiempo |

---

### Verticales (TXT, FOD, MET, MED, AGR, DIS, SRV, …)

| Aspecto | Definición |
|---------|------------|
| Responsabilidad | Conocimiento y procesos específicos de industria |
| Administra | Entidades y reglas propias del vertical |
| No administra | Aggregates Core (Producto, Lote, OP, Pedido, …) como dueño |
| Comparte | Extensiones y eventos propios; consume eventos Core |
| Nunca | Contaminar CFG Core con JSON de rubro; ni forzar FK Core→Vertical |

Detalle normativo: `06_EXTENSION_POINTS.md`.

---

## 4. Matriz de dependencia (lectura permitida)

| Consumidor ↓ / Dueño → | ORG | INV | WMS | QMS | PUR | SLS | MFG | MES | PLN | BILL |
|------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| WMS | L | L | — | | | L | | | | |
| QMS | L | L | | — | L | | L | | | |
| MES | L | L | | | | | L | — | L | |
| LOG | L | L | L | | | L | | | | |
| BILL | L | L | | | | L | | | | — |
| ALR | L | E | E | E | E | E | E | E | E | E |

Leyenda: **L** = lectura de identidad/datos maestros; **E** = consumo de eventos; vacío = no dependencia directa típica.

Las **escrituras** solo las hace el dueño del aggregate, salvo políticas explícitas de servicio de aplicación orquestado.

---

## 5. Anti-corrupción entre contextos

1. Un BC no escribe el modelo interno de otro BC.
2. La integración preferente entre BC desacoplados es **evento de dominio** o **API/servicio anti-corrupción**.
3. IDs compartidos (Producto, Lote, Empresa, Pedido) son contratos de identidad, no licencia para mutar.
4. Traducciones de lenguaje (ej. “partida” textil ≠ renombrar Lote Core) viven en el Vertical.

---

## 6. Criterio de cierre

Los Bounded Contexts quedan cerrados cuando cada capacidad del mapa Core tiene un único dueño y las fronteras INV/WMS, MFG/MES, PLN/APS, EVT/ALR, Core/Vertical están definidas sin ambigüedad.

**Estado:** cerrado.
