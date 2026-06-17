# INV — Plan Oficial de Corrección

**Fecha:** 2026-06-12  
**Estado:** Roadmap de planificación — **no implementación**  
**Fuentes de verdad:**
- `app/docs/arquitectura/ERP_MAPA_DEPENDENCIAS.md`
- `app/docs/auditoria/INV_AUDITORIA_PERSISTENCIA.md`

**Objetivo:** Definir el orden y las condiciones de corrección del módulo INV **antes** de iniciar auditorías de contratos API o frontend.

**Restricciones de este documento:**
- No modifica código, BD, contratos ni genera parches/migraciones.
- No recomienda eliminar campos de BD salvo evidencia sólida de error de diseño.
- No recomienda eliminar contratos API; los candidatos se registran como *Pendiente de auditoría de contratos*.

---

## 1. Resumen ejecutivo

### 1.1 Diagnóstico consolidado

| Dimensión | Hallazgo |
|-----------|----------|
| **Modelo de datos** | Correcto e intencionalmente preparado para PUR/SLS/MFG/FIN/CST. Solo **1 candidato F** (`subcategoria_id`) y **2 inconsistencias leves** (precios duales, ubicación WMS). |
| **Persistencia** | Brechas reales en costeo de stock, auditoría de usuario, snapshot de inventario físico y asignaciones fantasma en servicios. |
| **Workflow** | Máquinas de estado operativas; **estado forgeable en CREATE** (P0-006); faltan totales automáticos, preservación de timestamps y estrategia de reversión post-proceso. |
| **Contratos API** | Coexisten patrones correctos (cabecera+detalle) con endpoints deprecated y exposición adelantada de campos E. |
| **Frontend** | No auditado aún; varios hallazgos de persistencia/contrato tienen impacto directo en consumo UI. |

### 1.2 Conteo de hallazgos por prioridad

| Prioridad | Cantidad | Significado |
|-----------|----------|-------------|
| **P0** | 6 | Obligatorio antes de implementar PUR, SLS, MFG, FIN o CST |
| **P1** | 12 | Consolidación INV — corregir en la fase actual del módulo |
| **P2** | 14 | Corregir cuando exista el módulo consumidor |
| **P3** | 10 | Documentar, monitorear o validar en auditoría transversal |

### 1.3 Fases del roadmap

```
FASE 0 — Pre-requisitos (antes de nuevos módulos)
  └─ P0: enforcement workflow, integridad stock+costo, política stock derivado, auditoría B, reversión documentada

FASE 1 — Consolidación INV (módulo standalone maduro)
  └─ P1: inventario físico, workflow timestamps, validaciones, alineación ORM/servicios

FASE 2 — Integración por módulo consumidor
  └─ P2: campos E poblados por PUR/SLS/MFG/FIN/CST/WMS/QMS

FASE 3 — Observabilidad y diseño
  └─ P3: decisiones de modelo, CFG, precedencia precios, subcategoria_id

FASE 4 — Auditoría de contratos API (siguiente hito formal)
  └─ Backlog al final de este documento
```

---

## 2. Leyenda

### 2.1 Prioridades

| Código | Definición |
|--------|------------|
| **P0** | Obligatorio corregir **antes** de implementar nuevos módulos que consuman INV |
| **P1** | Importante corregir **durante consolidación INV** (fase actual) |
| **P2** | Corregir **cuando exista el módulo consumidor** |
| **P3** | **Documentar y monitorear** — sin acción inmediata |

### 2.2 Naturaleza del hallazgo

| Categoría | Alcance |
|-----------|---------|
| **Modelo de datos** | Diseño de tablas/columnas en V010 |
| **Persistencia** | Quién llena qué, cuándo y con qué valor |
| **Workflow** | Transiciones de estado y campos de proceso |
| **Contrato API** | Endpoints, schemas, permisos, deprecated |
| **Frontend** | Impacto en UI/consumo (inferido, no auditado) |

### 2.3 Riesgos referenciados

Riesgos **R1–R7** definidos en `INV_AUDITORIA_PERSISTENCIA.md` §9.

---

## 3. Registro de hallazgos

### 3.1 P0 — Obligatorio antes de nuevos módulos

#### INV-P0-001 — Costo de stock ignorado al procesar movimiento

| Atributo | Valor |
|----------|-------|
| **Descripción** | `procesar_movimiento` solo actualiza `inv_stock.cantidad_actual`. Ignora `inv_tipo_movimiento.afecta_costo` y `inv_movimiento_detalle.costo_unitario`. `costo_promedio` queda en 0 en altas automáticas de stock. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P0** |
| **Riesgo** | **R1** — Valorización incorrecta; reportes y CST futuros inválidos |
| **Impacto** | Financiero alto; bloquea confianza en kardex valorizado y en integración CST/FIN |
| **Dependencias** | Definir regla mínima de costeo (promedio ponderado) antes de implementar; alineación futura con módulo CST |
| **Módulos afectados** | INV, CST (futuro), FIN (futuro), BI |
| **Momento de corrección** | **Fase 0** — inmediatamente, antes de PUR/SLS/MFG |

---

#### INV-P0-002 — Tabla derivada `inv_stock` mutable fuera del workflow transaccional

| Atributo | Valor |
|----------|-------|
| **Descripción** | `inv_stock` es derivada por diseño (actualizada vía `inv_movimiento` procesado). POST/PUT `/stock` están marcados `deprecated=True` pero siguen operativos y permiten alterar cantidades/costos directamente. |
| **Categoría** | Persistencia · Contrato API |
| **Prioridad** | **P0** |
| **Riesgo** | **R2** — Integridad de cantidades |
| **Impacto** | Stock inconsistente respecto al kardex; invalida cualquier módulo que confíe en saldos |
| **Dependencias** | Política operativa acordada; auditoría de contratos (ver backlog BC-01) |
| **Módulos afectados** | INV, PUR, SLS, MFG, CST |
| **Momento de corrección** | **Fase 0** — definir política; implementación de bloqueo en Fase 1 o vía contratos |

> **Nota:** No se recomienda eliminar el contrato aún. Clasificado como *Pendiente de auditoría de contratos* (BC-01).

---

#### INV-P0-003 — Sin estrategia de reversión para movimientos procesados

| Atributo | Valor |
|----------|-------|
| **Descripción** | `anular_movimiento` rechaza movimientos en estado `procesado` sin ofrecer reversión de stock. No existe movimiento compensatorio ni documento de estorno en el diseño implementado. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P0** |
| **Riesgo** | **R6** — Operaciones bloqueadas; correcciones manuales fuera del sistema |
| **Impacto** | Errores operativos no corregibles por API; riesgo de ajustes manuales en BD |
| **Dependencias** | Decisión de negocio: movimiento inverso vs. flag de estorno; impacto contable (FIN futuro) |
| **Módulos afectados** | INV, FIN (futuro), AUD |
| **Momento de corrección** | **Fase 0** — al menos documentar política y diseño objetivo; implementación puede ser P1/P3 según decisión |

---

#### INV-P0-004 — Auditoría de usuario no poblada en altas y ediciones

| Atributo | Valor |
|----------|-------|
| **Descripción** | `usuario_creacion_id` y `usuario_actualizacion_id` existen en maestros y documentos INV pero no se asignan desde sesión en CRUD estándar. Solo parcialmente en aprobación IF → movimiento y en procesar/autorizar. |
| **Categoría** | Persistencia |
| **Prioridad** | **P0** |
| **Riesgo** | **R4** — Compliance y trazabilidad empresarial |
| **Impacto** | Imposible auditar quién creó/modificó productos, almacenes, movimientos manuales |
| **Dependencias** | Patrón transversal de auditoría (validar en ORG primero); `current_user.usuario_id` disponible en endpoints |
| **Módulos afectados** | INV, AUD (futuro), todos los maestros INV |
| **Momento de corrección** | **Fase 0** — antes de escalar datos de producción |

---

#### INV-P0-005 — Flag `afecta_costo` del tipo de movimiento sin efecto en runtime

| Atributo | Valor |
|----------|-------|
| **Descripción** | `inv_tipo_movimiento.afecta_costo` está en el modelo como gate de recosteo pero `procesar_movimiento` no lo consulta. Relacionado con INV-P0-001 pero merece ítem propio por impacto en configuración de catálogo. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P0** |
| **Riesgo** | **R1** |
| **Impacto** | Configuración de tipos de movimiento engañosa; administradores asumen costeo activo |
| **Dependencias** | INV-P0-001 |
| **Módulos afectados** | INV, CST |
| **Momento de corrección** | **Fase 0** — junto con INV-P0-001 |

---

#### INV-P0-006 — Estado de workflow forgeable en altas/ediciones sin enforcement servidor

| Atributo | Valor |
|----------|-------|
| **Descripción** | Los servicios `create_movimiento*` e `create_inventario_fisico*` persisten el campo `estado` recibido en el body sin forzar el valor inicial de workflow (`borrador` / `en_proceso`). Un cliente puede crear un movimiento con `estado=procesado` **sin mutar stock**. `procesar_movimiento_servicio` hace early-return si `estado == "procesado"` (idempotencia ciega), blindando el error de forma permanente. Análogo en IF con estados terminales (`ajustado`, `finalizado`) editables en Create/Update. |
| **Categoría** | Persistencia · Workflow · Contrato API (BC-20) |
| **Prioridad** | **P0** |
| **Riesgo** | **R2 + R6** — Integridad stock silenciosa; operaciones bloqueadas o irreversibles sin evidencia en kardex |
| **Impacto** | Desincronización movimiento↔stock peor que escritura directa de stock: el sistema cree que el inventario ya fue impactado. Invalida confianza en saldos, kardex y cualquier integración PUR/SLS que consulte estado del movimiento |
| **Dependencias** | Ninguna externa; identificado en cierre formal Fase 0 (`INV_AUDITORIA_CONTRATOS_API.md` BC-20). **No requiere cambio de contrato API** — corrección en capa de servicio |
| **Módulos afectados** | INV, PUR (recepción vía `procesar_movimiento`), FIN (futuro), AUD |
| **Momento de corrección** | **Fase 0** — **antes** de P0-001; prerequisito de integridad transaccional |

> **Nota:** Relacionado con BC-20 (`estado` editable en `MovimientoCreate`/`InventarioFisicoCreate`). La corrección Fase 0 es **enforcement servidor** (forzar/validar estado en CREATE; rechazar estados terminales en UPDATE; ajustar idempotencia de `procesar`/`autorizar`). Los campos permanecen en schema hasta auditoría de contratos formal.

**Criterios de corrección mínima:**

1. CREATE movimiento → `estado` forzado a `borrador` (ignorar body).
2. CREATE inventario físico → `estado` forzado a `en_proceso`.
3. UPDATE → rechazar cambio de `estado` vía body; solo transiciones POST proceso.
4. `procesar_movimiento` → no aceptar `procesado` huérfano (sin `fecha_procesado`/`usuario_procesado_id` o sin evidencia de stock aplicado); retornar 409 con mensaje accionable.
5. `autorizar_movimiento` → misma regla para `autorizado` huérfano.

---

### 3.2 P1 — Consolidación INV (fase actual)

#### INV-P1-001 — `cantidad_sistema` manual en inventario físico

| Atributo | Valor |
|----------|-------|
| **Descripción** | Al crear líneas de IF, `cantidad_sistema` proviene del body del cliente. El modelo espera snapshot de `inv_stock.cantidad_actual` al momento del conteo. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | **R3** — Ajustes incorrectos por desfase sistema vs. realidad |
| **Impacto** | Diferencias falsas; movimientos de ajuste incorrectos al aprobar |
| **Dependencias** | Ninguna externa |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-002 — `valor_diferencias` en cabecera IF nunca calculado

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campo derivable (C) expuesto en schema y BD pero permanece en 0. Debería agregarse desde `valor_diferencia` del detalle al finalizar o aprobar. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — reportes de cierre de conteo incompletos |
| **Impacto** | Cabecera IF no refleja impacto económico del conteo |
| **Dependencias** | INV-P0-001 (costo unitario confiable en detalle) |
| **Módulos afectados** | INV, CST (futuro) |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-003 — `total_costo` incompleto en movimiento generado por aprobación IF

| Atributo | Valor |
|----------|-------|
| **Descripción** | `aprobar_inventario_fisico` calcula `total_items` y `total_cantidad` del movimiento de ajuste pero no `total_costo` (suma de `cantidad × costo_unitario`). |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — cabecera de movimiento inconsistente con detalle |
| **Impacto** | Reportes y kardex con totales parciales |
| **Dependencias** | INV-P0-001 |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-004 — `fecha_finalizacion` sobrescrita en aprobar

| Atributo | Valor |
|----------|-------|
| **Descripción** | `finalizar_inventario_fisico` establece `fecha_finalizacion`. `aprobar_inventario_fisico` la sobrescribe con `now`, perdiendo el timestamp real del cierre de conteo. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — auditoría de tiempos de conteo incorrecta |
| **Impacto** | SLA de conteo y reportes operativos distorsionados |
| **Dependencias** | Ninguna |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-005 — Responsables de conteo no derivados de sesión

| Atributo | Valor |
|----------|-------|
| **Descripción** | `supervisor_usuario_id`, `contador_usuario_id` y nombres asociados se aceptan manualmente en body. Deberían poblarse desde `current_user` en finalizar/aprobar/conteo según rol. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — trazabilidad de responsables débil |
| **Impacto** | Conteos sin responsable verificable |
| **Dependencias** | INV-P0-004 (patrón auditoría) |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-006 — Validación `subcategoria_id` ausente en producto

| Atributo | Valor |
|----------|-------|
| **Descripción** | `inv_producto.subcategoria_id` aceptado sin validar existencia ni coherencia con `categoria_id`. Arquitectónicamente es candidato F (DM-01) pero mientras exista en BD debe validarse o ignorarse explícitamente. |
| **Categoría** | Persistencia · Modelo de datos |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — referencias rotas en maestro producto |
| **Impacto** | Datos incoherentes en clasificación |
| **Dependencias** | Decisión DM-01 (INV-P3-001) |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** — validar mientras campo exista; no eliminar BD |

---

#### INV-P1-007 — Asignaciones a columnas inexistentes en servicios

| Atributo | Valor |
|----------|-------|
| **Descripción** | `inventario_fisico_service` intenta `fecha_actualizacion` en cabecera IF (columna no existe en tabla). `movimiento_service` asigna `moneda` y `fecha_actualizacion` en detalle (columnas no existen). Filtrado silencioso por `_COLUMNS`. |
| **Categoría** | Persistencia |
| **Prioridad** | **P1** |
| **Riesgo** | Bajo — confusión de mantenimiento; falsa sensación de persistencia |
| **Impacto** | Deuda técnica interna; posibles regresiones si se agregan columnas homónimas |
| **Dependencias** | Ninguna |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-008 — Columnas computadas PERSISTED ausentes en ORM (`tables_inv.py`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | BD define `cantidad_disponible`, `valor_total`, `costo_total`, `diferencia`, `valor_diferencia` como PERSISTED. ORM no las declara. Lectura funciona vía `select(Table)` pero alertas calculan disponible en Python. |
| **Categoría** | Persistencia · Modelo de datos |
| **Prioridad** | **P1** |
| **Riesgo** | **R7** — Bajo hoy; medio al cambiar driver o proyecciones |
| **Impacto** | Documentación de modelo incompleta; riesgo en evolución de queries |
| **Dependencias** | Ninguna |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-009 — Discrepancia nullable `moneda_id` ORM vs NOT NULL SQL

| Atributo | Valor |
|----------|-------|
| **Descripción** | `InvMovimientoTable.moneda_id` es `nullable=True` en SQLAlchemy; `INV_TABLAS.sql` define `NOT NULL`. Servicio resuelve PEN por defecto pero el contrato ORM no refleja la restricción canónica. |
| **Categoría** | Modelo de datos · Persistencia |
| **Prioridad** | **P1** |
| **Riesgo** | Medio — posible INSERT sin moneda si se omite resolución |
| **Impacto** | Integridad referencial inconsistente entre capas |
| **Dependencias** | Ninguna |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-010 — Totales de cabecera IF (`total_productos_contados`, `total_diferencias`) solo en aprobar

| Atributo | Valor |
|----------|-------|
| **Descripción** | Resúmenes de conteo se calculan únicamente en `aprobar_inventario_fisico`, no en `finalizar`. El estado `finalizado` no expone totales de cierre. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P1** |
| **Riesgo** | Bajo — UX y reportes pre-ajuste incompletos |
| **Impacto** | Usuario no ve resumen al finalizar conteo |
| **Dependencias** | INV-P1-002 |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-011 — `costo_unitario` en detalle IF no auto-poblado desde stock

| Atributo | Valor |
|----------|-------|
| **Descripción** | Al crear líneas IF, `costo_unitario` es opcional/manual. Debería tomarse de `inv_stock.costo_promedio` o `inv_producto.costo_promedio` al snapshot. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | **R3** — valor_diferencia y ajustes con costo 0 |
| **Impacto** | Ajustes sin valorización económica |
| **Dependencias** | INV-P0-001, INV-P1-001 |
| **Módulos afectados** | INV, CST (futuro) |
| **Momento de corrección** | **Fase 1** |

---

#### INV-P1-012 — `usuario_creacion_id` ausente en movimientos manuales

| Atributo | Valor |
|----------|-------|
| **Descripción** | Sub-hallazgo de INV-P0-004 específico de documentos transaccionales: `create_movimiento*` no asigna `usuario_creacion_id`; solo el flujo IF→ajuste lo hace parcialmente. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P1** |
| **Riesgo** | **R4** |
| **Impacto** | Movimientos manuales sin autor identificable |
| **Dependencias** | INV-P0-004 |
| **Módulos afectados** | INV |
| **Momento de corrección** | **Fase 1** — puede ejecutarse junto con P0-004 |

---

### 3.3 P2 — Corregir con módulo consumidor

#### INV-P2-001 — `cantidad_reservada` sin lógica de reserva

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campo E diseñado para pedidos/producción pendientes. `cantidad_disponible` en BD depende de este valor. Sin SLS/MFG no se actualiza. |
| **Categoría** | Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Medio cuando SLS active — disponible = actual |
| **Impacto** | Reservas inexistentes; riesgo de sobreventa futura |
| **Dependencias** | Módulo **SLS** y/o **MFG** |
| **Módulos afectados** | INV, SLS, MFG |
| **Momento de corrección** | Al implementar SLS (reserva pedido) / MFG (reserva materiales) |

---

#### INV-P2-002 — `cantidad_transito` sin lógica PUR

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campo E para OC en camino. Sin PUR permanece en 0. |
| **Categoría** | Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Bajo hasta PUR |
| **Impacto** | Pipeline de compras invisible en stock |
| **Dependencias** | Módulo **PUR** |
| **Módulos afectados** | INV, PUR |
| **Momento de corrección** | Al implementar PUR |

---

#### INV-P2-003 — `fecha_ultima_compra` / `fecha_ultima_venta` sin poblar

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campos E de analytics en `inv_stock`. Diseñados para actualizarse desde movimientos PUR/SLS. |
| **Categoría** | Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Bajo |
| **Impacto** | KPIs de rotación no disponibles |
| **Dependencias** | **PUR**, **SLS** |
| **Módulos afectados** | INV, PUR, SLS, BI |
| **Momento de corrección** | Con integración PUR/SLS |

---

#### INV-P2-004 — Puente contable `genera_asiento_contable` / `cuenta_contable_*`

| Atributo | Valor |
|----------|-------|
| **Descripción** | Tipos de movimiento y categorías tienen configuración FIN por código de cuenta. Sin módulo FIN no genera asientos. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P2** |
| **Riesgo** | Bajo hasta FIN |
| **Impacto** | Inventario sin reflejo contable automático |
| **Dependencias** | Módulo **FIN**; decisión DM-03 (cuenta NVARCHAR vs FK) |
| **Módulos afectados** | INV, FIN, CST |
| **Momento de corrección** | Al implementar FIN |

---

#### INV-P2-005 — Validación `documento_referencia_*` y `requiere_documento_referencia`

| Atributo | Valor |
|----------|-------|
| **Descripción** | Tipo de movimiento puede exigir documento origen. Sin PUR/SLS/MFG no hay validación de tipos ni existencia de documentos. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Medio — movimientos huérfanos sin trazabilidad |
| **Impacto** | Integración cross-módulo incompleta |
| **Dependencias** | **PUR**, **SLS**, **MFG** |
| **Módulos afectados** | INV + módulos origen |
| **Momento de corrección** | Por módulo integrador |

---

#### INV-P2-006 — Flags `maneja_lotes` / `maneja_series` / `maneja_vencimiento` sin enforcement

| Atributo | Valor |
|----------|-------|
| **Descripción** | Producto expone flags; movimiento e IF aceptan lote/serie/vencimiento opcionales sin exigirlos cuando el producto lo requiere. |
| **Categoría** | Workflow · Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | **R5** — industrias reguladas |
| **Impacto** | Trazabilidad incompleta |
| **Dependencias** | **QMS**, **WMS** (opcional); reglas de negocio por industria |
| **Módulos afectados** | INV, QMS, WMS |
| **Momento de corrección** | Al activar trazabilidad por industria o QMS |

---

#### INV-P2-007 — Flags `permite_ventas/compras/produccion` en almacén sin enforcement

| Atributo | Valor |
|----------|-------|
| **Descripción** | Almacén define routing operativo. Movimientos no validan compatibilidad almacén↔clase movimiento. |
| **Categoría** | Workflow |
| **Prioridad** | **P2** |
| **Riesgo** | Medio — operaciones en almacén incorrecto |
| **Impacto** | Entradas de compra en almacén no habilitado, etc. |
| **Dependencias** | **PUR**, **SLS**, **MFG** |
| **Módulos afectados** | INV + operativos |
| **Momento de corrección** | Al integrar cada flujo |

---

#### INV-P2-008 — `centro_costo_id` en movimiento/almacén sin consumo

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campos E para imputación FIN/CST. Persistidos si el cliente los envía; sin validación ni uso en asientos. |
| **Categoría** | Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Bajo hasta FIN/CST |
| **Impacto** | Costos no imputables |
| **Dependencias** | **FIN**, **CST**, ORG (`org_centro_costo`) |
| **Módulos afectados** | INV, FIN, CST, HCM |
| **Momento de corrección** | Con FIN/CST |

---

#### INV-P2-009 — Campos PUR en producto (`es_comprable`, lead time, múltiplos, `proveedor_habitual_id`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campos E confirmados por V010. No deben considerarse deuda; se activan con PUR/MRP. |
| **Categoría** | Modelo de datos · Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Ninguno en fase actual |
| **Impacto** | Reglas de reorden inactivas |
| **Dependencias** | **PUR**, **MRP** |
| **Módulos afectados** | INV, PUR |
| **Momento de corrección** | Al implementar PUR — **no eliminar campos** |

---

#### INV-P2-010 — Campos SLS en producto (`es_vendible`, `requiere_autorizacion_venta`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Reserva E para gate comercial. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P2** |
| **Riesgo** | Ninguno en fase actual |
| **Impacto** | Sin gate de venta por producto |
| **Dependencias** | **SLS** |
| **Módulos afectados** | INV, SLS |
| **Momento de corrección** | Al implementar SLS |

---

#### INV-P2-011 — Campos MFG en producto (`es_fabricable`, `tiene_lista_materiales`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Reserva E para BOM/OP. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P2** |
| **Riesgo** | Ninguno en fase actual |
| **Impacto** | Sin distinción fabricable en runtime |
| **Dependencias** | **MFG** |
| **Módulos afectados** | INV, MFG |
| **Momento de corrección** | Al implementar MFG |

---

#### INV-P2-012 — Campos tributarios (`codigo_sunat`, `tipo_afectacion_igv`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Reserva E para TAX/INVBILL. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P2** |
| **Riesgo** | Ninguno hasta facturación |
| **Impacto** | Facturación electrónica sin clasificación producto |
| **Dependencias** | **TAX**, **INVBILL** |
| **Módulos afectados** | INV, INVBILL, TAX |
| **Momento de corrección** | Al implementar facturación |

---

#### INV-P2-013 — `ubicacion_almacen` texto vs módulo WMS

| Atributo | Valor |
|----------|-------|
| **Descripción** | INV usa texto libre (WMS-lite). WMS define `wms_ubicacion` con FK. Coexistencia planificada (DM-05). |
| **Categoría** | Modelo de datos · Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Bajo hasta WMS |
| **Impacto** | Duplicidad de concepto ubicación |
| **Dependencias** | **WMS** |
| **Módulos afectados** | INV, WMS |
| **Momento de corrección** | Al implementar WMS — plan de transición, no eliminación prematura |

---

#### INV-P2-014 — Sincronización `inv_producto.costo_*` con `cst_producto_costo`

| Atributo | Valor |
|----------|-------|
| **Descripción** | Maestro producto tiene snapshot de costos; CST tendrá tabla analítica por periodo. Falta regla de fuente canónica. |
| **Categoría** | Modelo de datos · Persistencia |
| **Prioridad** | **P2** |
| **Riesgo** | Alto cuando CST active — dos fuentes de verdad |
| **Impacto** | Costos inconsistentes entre maestro y analítica |
| **Dependencias** | Módulo **CST**; INV-P0-001 |
| **Módulos afectados** | INV, CST |
| **Momento de corrección** | Diseño conjunto INV+CST antes de codificar CST |

---

### 3.4 P3 — Documentar y monitorear

#### INV-P3-001 — Candidato huérfano `subcategoria_id` (DM-01)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Redundante con jerarquía `inv_categoria_producto.categoria_padre_id`. Único campo F confirmado. **No recomendar eliminación de BD** hasta validación con negocio y datos existentes. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo si se valida en P1-006 |
| **Impacto** | Confusión de modelo; doble vía de clasificación |
| **Dependencias** | Inventario de datos en tenants; decisión arquitectónica formal |
| **Módulos afectados** | INV |
| **Momento de corrección** | Antes de seed masivo de productos; documentar decisión en arquitectura |

---

#### INV-P3-002 — Dualidad `precio_base_venta` vs `prc_lista_precio` (DM-02)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Precio en maestro producto coexiste con listas PRC. Sin regla de precedencia documentada. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P3** |
| **Riesgo** | Medio al activar PRC/SLS |
| **Impacto** | Precios contradictorios |
| **Dependencias** | Módulo **PRC** |
| **Módulos afectados** | INV, PRC, SLS |
| **Momento de corrección** | Auditoría INV+PRC conjunta |

---

#### INV-P3-003 — Cuentas contables NVARCHAR vs FK `fin_plan_cuentas` (DM-03)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Integración FIN por código de cuenta en INV; decisión de acoplamiento débil intencional. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo — cuentas inválidas detectables en FIN |
| **Impacto** | Sin integridad referencial estricta |
| **Dependencias** | **FIN** |
| **Módulos afectados** | INV, FIN |
| **Momento de corrección** | Documentar contrato en integración FIN |

---

#### INV-P3-004 — Jerarquía categoría: `nivel` y `ruta_jerarquica` manuales

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campos derivables (C) aceptados en body sin recálculo automático al asignar `categoria_padre_id`. |
| **Categoría** | Persistencia |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo |
| **Impacto** | Rutas jerárquicas incorrectas en reportes |
| **Dependencias** | Ninguna |
| **Módulos afectados** | INV |
| **Momento de corrección** | Mejora oportunista en consolidación |

---

#### INV-P3-005 — Correlativos manuales (`numero_movimiento`, `numero_inventario`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Cliente/API debe proveer correlativos; existe `cfg_codigo_secuencia` en V010 sin integración observable en INV. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P3** |
| **Riesgo** | Medio — duplicados si no hay validación UI |
| **Impacto** | UX y unicidad dependen del cliente |
| **Dependencias** | Auditoría **CFG** |
| **Módulos afectados** | INV, CFG |
| **Momento de corrección** | Auditoría CFG previa a escalar volumen |

---

#### INV-P3-006 — Capacidad WMS en almacén (`capacidad_m3/kg/unidades`)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Campos E/D sin validación; diseñados para planificación WMS. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P3** |
| **Riesgo** | Ninguno |
| **Impacto** | Sin control de capacidad |
| **Dependencias** | **WMS** |
| **Módulos afectados** | INV, WMS |
| **Momento de corrección** | Con WMS |

---

#### INV-P3-007 — Campos E expuestos como editables en schemas sin módulo consumidor (DI-01)

| Atributo | Valor |
|----------|-------|
| **Descripción** | `ProductoCreate/Update` incluye ~30 campos E (PUR/SLS/MFG/TAX) editables por API. No es error de BD; es contrato adelantado. |
| **Categoría** | Contrato API |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo — datos prematuros en maestro |
| **Impacto** | Cliente puede poblar campos sin semántica activa |
| **Dependencias** | Auditoría de contratos (backlog BC-02) |
| **Módulos afectados** | INV, futuros consumidores |
| **Momento de corrección** | Auditoría de contratos — no acción ahora |

---

#### INV-P3-008 — `estado_conteo` sin transiciones automáticas en IF detalle

| Atributo | Valor |
|----------|-------|
| **Descripción** | Permanece `pendiente` salvo que el cliente lo actualice. Workflow podría transicionar a `contado` al registrar `cantidad_contada`. |
| **Categoría** | Workflow |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo |
| **Impacto** | Estado de línea no refleja progreso real |
| **Dependencias** | INV-P1-001 |
| **Módulos afectados** | INV |
| **Momento de corrección** | Mejora oportunista Fase 1 |

---

#### INV-P3-009 — Soft FKs sin constraint en V010 (DM-04)

| Atributo | Valor |
|----------|-------|
| **Descripción** | Patrón arquitectónico deliberado (`proveedor_habitual_id`, `movimiento_ajuste_id`, etc.). Requiere validación en capa aplicación. |
| **Categoría** | Modelo de datos |
| **Prioridad** | **P3** |
| **Riesgo** | Bajo con validación app |
| **Impacto** | Referencias rotas posibles |
| **Dependencias** | Módulos referenciados |
| **Módulos afectados** | INV, PUR, SLS, MFG |
| **Momento de corrección** | Documentar en estándar de integración |

---

#### INV-P3-010 — Integridad transaccional: stock costo fuera de lógica unificada

| Atributo | Valor |
|----------|-------|
| **Descripción** | UoW existe en cabecera+detalle y aprobación IF, pero actualización de costo en stock no participa de la misma regla de negocio que cantidad. |
| **Categoría** | Persistencia · Workflow |
| **Prioridad** | **P3** (elevar a P0 vía INV-P0-001) |
| **Riesgo** | **R1** |
| **Impacto** | Ver INV-P0-001 |
| **Dependencias** | INV-P0-001 |
| **Módulos afectados** | INV |
| **Momento de corrección** | Cubierto por P0-001 — ítem de seguimiento |

---

## 4. Matriz de priorización consolidada

| ID | Título corto | P | Categoría | Riesgo |
|----|--------------|---|-----------|--------|
| INV-P0-001 | Costo stock al procesar | P0 | Persistencia | R1 |
| INV-P0-002 | Stock derivado escribible | P0 | Persistencia/API | R2 |
| INV-P0-003 | Sin reversión procesados | P0 | Workflow | R6 |
| INV-P0-004 | Auditoría usuario maestros | P0 | Persistencia | R4 |
| INV-P0-005 | `afecta_costo` ignorado | P0 | Workflow | R1 |
| INV-P0-006 | Estado workflow forgeable | P0 | Workflow/Persistencia | R2+R6 |
| INV-P1-001 | Snapshot `cantidad_sistema` IF | P1 | Persistencia | R3 |
| INV-P1-002 | `valor_diferencias` IF | P1 | Workflow | Medio |
| INV-P1-003 | `total_costo` movimiento IF | P1 | Persistencia | Medio |
| INV-P1-004 | `fecha_finalizacion` sobrescrita | P1 | Workflow | Medio |
| INV-P1-005 | Responsables conteo sesión | P1 | Persistencia | Medio |
| INV-P1-006 | Validar `subcategoria_id` | P1 | Persistencia | Medio |
| INV-P1-007 | Columnas fantasma en servicios | P1 | Persistencia | Bajo |
| INV-P1-008 | ORM sin computadas | P1 | Modelo | R7 |
| INV-P1-009 | Nullable `moneda_id` ORM | P1 | Modelo | Medio |
| INV-P1-010 | Totales IF solo en aprobar | P1 | Workflow | Bajo |
| INV-P1-011 | `costo_unitario` IF auto | P1 | Persistencia | R3 |
| INV-P1-012 | Auditoría usuario movimientos | P1 | Persistencia | R4 |
| INV-P2-001 … P2-014 | Campos E por módulo consumidor | P2 | Varios | — |
| INV-P3-001 … P3-010 | Documentar / monitorear | P3 | Varios | — |

---

## 5. Orden de ejecución recomendado (sin implementar)

### Fase 0 — Gate antes de PUR / SLS / MFG / FIN / CST

1. INV-P0-006 (enforcement estado workflow — **prerequisito de integridad**)
2. INV-P0-004 + INV-P1-012 (auditoría usuario)
3. INV-P0-001 + INV-P0-005 (costeo al procesar)
4. INV-P0-002 (política stock derivado — decisión + bloqueo runtime)
5. INV-P0-003 (política de reversión — diseño documentado; estorno opcional)

**Criterio de salida Fase 0:** Workflow no forgeable; stock valorizado correctamente; trazabilidad de usuario en writes; política explícita para stock directo y anulación de procesados.

### Fase 1 — Consolidación INV standalone

1. INV-P1-001 + INV-P1-011 (snapshot IF)
2. INV-P1-002 + INV-P1-003 + INV-P1-010 (totales IF y movimiento ajuste)
3. INV-P1-004 + INV-P1-005 (timestamps y responsables)
4. INV-P1-006 (subcategoria_id mientras exista)
5. INV-P1-007 + INV-P1-008 + INV-P1-009 (higiene técnica ORM/servicios)

**Criterio de salida Fase 1:** Flujo IF completo sin dependencias externas; inventario físico produce ajustes valorizados y auditables.

### Fase 2 — Por módulo consumidor

Ejecutar ítems P2 en el orden de implementación del roadmap ERP:

`PUR → SLS → MFG → CST → FIN → WMS → QMS → PRC/TAX/INVBILL`

### Fase 3 — Observabilidad

Ítems P3 en paralelo a auditorías ORG, CFG y decisiones de modelo (DM-01 a DM-05).

### Fase 4 — Auditoría de contratos API

Ver §6 — **no iniciar antes de cerrar Fase 0**.

---

## 6. Backlog para futura auditoría de contratos API

> Estado: **Pendiente de auditoría de contratos** — registrar candidatos sin proponer cambios.

### 6.1 Endpoints posiblemente redundantes

| ID | Endpoint | Motivo de redundancia | Riesgo eliminación | Consumidores conocidos |
|----|----------|----------------------|--------------------|------------------------|
| BC-01 | `POST /inv/movimientos` (solo cabecera) | Flujo canónico V4 es `POST /movimientos/con-detalle` con líneas obligatorias | Medio — clientes legacy podrían usar cabecera vacía | Desconocido — **auditar frontend** |
| BC-02 | `POST /inv/inventario-fisico` (solo cabecera) | Flujo canónico es `/con-detalle` | Bajo | Desconocido |
| BC-03 | `GET /inv/movimientos-detalle` (lista global) | Detalle debería consultarse bajo cabecera | Bajo | Desconocido |
| BC-04 | `GET /inv/inventario-fisico-detalle` (lista global) | Ídem | Bajo | Desconocido |

### 6.2 Endpoints deprecated ya existentes

| ID | Endpoint | `deprecated` | Motivo original | Candidato a | Riesgo eliminación |
|----|----------|--------------|-----------------|-------------|-------------------|
| BC-05 | `POST /inv/stock` | Sí | Tabla derivada — anti-patrón | Mantener deprecated → eventual 410 | **Alto** si frontend escribe stock |
| BC-06 | `PUT /inv/stock/{id}` | Sí | Ídem | Ídem | **Alto** |
| BC-07 | `POST /inv/movimientos-detalle` | Sí | Escritura standalone detalle vs cabecera+detalle V4 | Deprecated permanente | Medio |
| BC-08 | `PUT /inv/movimientos-detalle/{id}` | Sí | Ídem | Ídem | Medio |
| BC-09 | `POST /inv/inventario-fisico-detalle` | Sí | Ídem | Ídem | Medio |
| BC-10 | `PUT /inv/inventario-fisico-detalle/{id}` | Sí | Ídem | Ídem | Medio |

### 6.3 Schemas posiblemente sobreexpuestos

| ID | Schema | Observación | Candidato a | Riesgo |
|----|--------|-------------|-------------|--------|
| BC-11 | `ProductoCreate` / `ProductoUpdate` | ~30 campos E (PUR/SLS/MFG/TAX/PRC) editables sin consumidor activo | Dividir schema por dominio o marcar grupos readonly en contrato futuro | Medio — breaking change |
| BC-12 | `StockCreate` / `StockUpdate` | Exponen escritura sobre tabla derivada | Deprecated en endpoint; schemas podrían quedar solo Read | Alto si hay cliente |
| BC-13 | `InventarioFisicoCreate` | Expone `total_*`, `movimiento_ajuste_id`, `valor_diferencias` como editables en body | Readonly en Update; calculados en servidor | Bajo |
| BC-14 | `MovimientoCreate` | Expone `estado`, totales, campos de autorización como editables | Algunos deberían ser readonly o solo internos | Medio |
| BC-15 | `MovimientoDetalleCreate` (standalone) | Contrato legacy paralelo a embebido | Deprecated | Medio |

### 6.4 Campos que no deberían ser editables (candidatos readonly)

| ID | Campo | Schema actual | Motivo | Riesgo si se restringe |
|----|-------|---------------|--------|------------------------|
| BC-16 | `cliente_id` | No expuesto (correcto) | Siempre sesión | — |
| BC-17 | `total_items`, `total_cantidad`, `total_costo` | Editables en MovimientoCreate/Update | Derivados (C) | Bajo |
| BC-18 | `valor_diferencias`, `total_diferencias`, `total_productos_contados` | Editables en InventarioFisicoCreate/Update | Derivados (C) | Bajo |
| BC-19 | `movimiento_ajuste_id` | Editable en InventarioFisicoCreate/Update | Solo workflow aprobar | Medio |
| BC-20 | `estado` (movimiento, IF) | Editable en Create/Update | Solo transiciones POST proceso | **Alto** — clientes podrían forzar estados. **Hallazgo funcional:** INV-P0-006 |
| BC-21 | `fecha_finalizacion`, `fecha_ajuste` | Editable en InventarioFisicoUpdate | Solo workflow | Medio |
| BC-22 | `autorizado_por_usuario_id`, `fecha_autorizacion`, `usuario_procesado_id`, `fecha_procesado` | Editables en MovimientoCreate/Update | Solo endpoints proceso | **Alto** |
| BC-23 | `diferencia`, `valor_diferencia`, `cantidad_disponible`, `valor_total`, `costo_total` | En Read (correcto) | Computadas BD — nunca en Write | Bajo |

### 6.5 Campos que deberían ser readonly en respuesta pero completos

| ID | Campo | Gap actual | Impacto frontend |
|----|-------|------------|------------------|
| BC-24 | `usuario_creacion_id`, `usuario_actualizacion_id` | En Read pero vacíos | UI de auditoría vacía |
| BC-25 | `valor_total`, `cantidad_disponible` | En StockRead; depende de BD/ORM | Dashboards de valorización |
| BC-26 | `costo_total` (detalle movimiento) | En MovimientoDetalleRead | Línea sin total en UI si BD no proyecta |

### 6.6 Contratos candidatos a migrar a deprecated (futuro)

| ID | Contrato | Condición para deprecar | Prerequisito |
|----|----------|-------------------------|--------------|
| BC-27 | POST/PUT `/stock` | Confirmar cero consumidores activos | Auditoría frontend + BC-05/06 |
| BC-28 | POST/PUT detalle standalone (movimiento, IF) | Frontend migrado a cabecera+detalle | Auditoría frontend |
| BC-29 | POST `/movimientos` sin detalle | Eliminar flujo borrador sin líneas | Política: borrador siempre con ≥1 línea |
| BC-30 | Campo `moneda` legacy en schemas movimiento/detalle | Clientes migrados a `moneda_id` | Inventario consumo API |

### 6.7 Checklist para la auditoría de contratos (siguiente hito)

- [ ] Inventariar consumo real por endpoint (frontend, integraciones, tests)
- [ ] Validar que ningún cliente activo usa BC-05, BC-06 (stock write)
- [ ] Confirmar flujo UI: ¿cabecera+detalle o standalone?
- [ ] Mapear campos Write vs campos que el servidor sobrescribe
- [ ] Definir matriz readonly por estado de documento (borrador vs procesado)
- [ ] Evaluar breaking changes vs versionado de API
- [ ] Documentar contrato canónico por entidad (Producto, Movimiento, IF, Stock)
- [ ] Alinear permisos RBAC con operaciones de proceso vs CRUD

---

## 7. Campos INV "no usados" — decisión arquitectónica final

Referencia cruzada con `ERP_MAPA_DEPENDENCIAS.md` §5.

| Grupo de campos | Acción en este plan | Prioridad |
|-----------------|---------------------|-----------|
| Campos E (PUR/SLS/MFG/FIN/CST/TAX/PRC/WMS) | **Mantener BD y contrato**; activar con P2 | P2 / P3 |
| Campos B (auditoría usuario/fecha) | **Corregir persistencia** | P0 / P1 |
| Campos C (computadas/agregados) | **No escribir desde app**; calcular en workflow | P1 |
| Campos D (contextuales) | **Mantener**; enforcement opcional P2/P3 | P3 |
| `subcategoria_id` (F) | **No eliminar BD**; validar P1; decidir P3 | P1 + P3 |
| Stock POST/PUT | **No eliminar contrato aún**; backlog BC-05/06 | P0 política + Fase 4 |

---

## 8. Dependencias con otras auditorías

| Auditoría previa/requerida | Relación con este plan |
|----------------------------|------------------------|
| `ERP_MAPA_DEPENDENCIAS.md` | Clasificación E/B/C de campos — evita falsos positivos de deuda |
| `INV_AUDITORIA_PERSISTENCIA.md` | Evidencia de brechas P0/P1 |
| `INV_AUDITORIA_CONTRATOS_API.md` | BC-20 → INV-P0-006; contrato canónico |
| ORG (pendiente) | Patrón auditoría B, validación `centro_costo`, `sucursal` |
| CFG (pendiente) | Correlativos INV-P3-005 |
| CST (pendiente) | INV-P0-001, INV-P2-014 |
| Contratos API (pendiente) | §6 backlog completo |

---

## 9. Criterios de cierre del módulo INV (pre-contratos)

El módulo INV se considera **consolidado para abrir auditoría de contratos** cuando:

1. **P0 cerrado** — 6 ítems (001–006); P0-006 **sin excepción**; demás con excepción documentada si aplica (P0-003 mínimo).
2. **P1 de inventario físico y costeo** cerrado (ítems 001–004, 010–011 como mínimo).
3. **Política de stock derivado** definida (aunque el contrato siga deprecated).
4. **Política de reversión** de movimientos procesados documentada.
5. **Backlog §6** listo para ejecución formal con inventario de consumidores.

---

*Documento de planificación. No autoriza cambios de código, BD ni contratos. Próximo hito formal: **Auditoría de Contratos API INV** usando §6 como entrada.*
