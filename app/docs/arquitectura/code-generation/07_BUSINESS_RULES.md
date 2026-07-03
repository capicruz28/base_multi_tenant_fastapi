# F15A — Reglas de negocio del motor de generación de códigos

**Fase:** F15A — Política funcional (solo documentación)  
**Base normativa:** F15 (`01`–`06` en `app/docs/arquitectura/code-generation/`)  
**Fecha:** 2026-07-02  
**Alcance:** Comportamiento funcional que el motor **debe respetar** durante toda la vida del sistema. Sin diseño técnico ni implementación.

---

## 1. Propósito de este documento

Define las **reglas de negocio transversales** del motor de códigos CAXIS ERP. Las decisiones aquí contenidas son **vinculantes** para Fase 2 (DDL, gateway, servicios) y para cualquier módulo ERP aque cree o modifique entidades con código.

**Principio rector:** un código de negocio es un **identificador operativo humano** dentro de un scope de unicidad definido por el modelo (tenant, empresa, almacén, serie fiscal). No es la clave primaria técnica (UUID).

---

## 2. Definiciones de negocio

| Término | Definición |
|---------|------------|
| **Código maestro** | Identificador estable de una entidad de configuración (empresa, producto, proveedor). Persiste mientras la entidad exista. |
| **Correlativo documental** | Número secuencial de un documento de proceso (OC, movimiento, pedido). Adquiere significado legal u operativo al confirmarse/procesarse. |
| **Scope** | Ámbito de unicidad: tenant, empresa, almacén, punto de venta o serie fiscal (según F15 `03_SEQUENCE_SCOPE.md`). |
| **Consumo de secuencia** | Asignación irreversible de un número que incrementa el contador oficial del scope. |
| **Política de generación** | Regla que determina si el sistema, el usuario o un sistema externo origina el código (`08_CODE_POLICIES.md`). |

---

## 3. Reglas para maestros (grupo B — F15)

### 3.1 Generación automática

| Regla ID | Regla |
|----------|-------|
| **BR-M-01** | En operación normal (post go-live), los maestros operativos estándar se crean con política **AUTO_DEFAULT**: si el usuario no ingresa código, el sistema lo asigna. |
| **BR-M-02** | La primera empresa de un tenant (`org_empresa` con código `EMP001` en bootstrap) es excepción histórica; empresas adicionales siguen AUTO_DEFAULT con scope **tenant** (único por `cliente_id`). |
| **BR-M-03** | Maestros de **configuración deliberada** (`inv_tipo_movimiento`, `fin_plan_cuentas`, `hcm_concepto_planilla`) admiten AUTO_DEFAULT pero el implementador funcional puede exigir manual por gobernanza contable/nómina. |
| **BR-M-04** | Maestros WMS (`wms_zona_almacen`, `wms_ubicacion`) generan dentro del scope **almacén**, no empresa. |
| **BR-M-05** | `invbill_serie_comprobante.serie` es maestro fiscal: **MANUAL_ONLY** en alta (serie autorizada por SUNAT); el correlativo numérico es AUTO_REQUIRED en emisión. |

### 3.2 Ingreso manual

| Regla ID | Regla |
|----------|-------|
| **BR-M-10** | El usuario **puede** ingresar código manualmente en maestros AUTO_DEFAULT si cumple formato y unicidad en el scope. |
| **BR-M-11** | El ingreso manual es **obligatorio** cuando la política es MANUAL_ONLY (`codigo_barra`, `codigo_interno` opcional alias, campos grupo D). |
| **BR-M-12** | El usuario **no puede** sobrescribir un código ya asignado automáticamente en la misma petición de creación (una sola fuente de verdad por transacción). |
| **BR-M-13** | Códigos con significado semántico corporativo (ej. `CC-ADM`, `SUC-LIMA`) son decisión del usuario; el motor no impone significado, solo formato y unicidad. |

### 3.3 Validación de duplicados

| Regla ID | Regla |
|----------|-------|
| **BR-M-20** | Toda creación o cambio de código debe validar unicidad en el **scope del UNIQUE de V010** antes de persistir. |
| **BR-M-21** | El mensaje de negocio ante duplicado debe indicar entidad, campo y scope (empresa/almacén), conforme estándar V4 de conflictos. |
| **BR-M-22** | La comparación de códigos maestros es **case-insensitive** para búsqueda y unicidad (alineado a `normalize_upper` en schemas ORG/INV). |
| **BR-M-23** | `numero_documento` de terceros (RUC/DNI) no comparte reglas con códigos maestros internos; política EXTERNAL. |

### 3.4 Edición posterior

| Regla ID | Regla |
|----------|-------|
| **BR-M-30** | El código maestro es **inmutable** una vez que la entidad ha sido **referenciada** por cualquier documento procesado, movimiento de stock, asiento contable, comprobante fiscal o vínculo irreversible equivalente. |
| **BR-M-31** | Sin referencias, el código puede editarse solo por usuarios con permiso explícito de actualización del maestro; cada cambio queda en auditoría. |
| **BR-M-32** | No existe ventana temporal automática por días; la inmutabilidad la determina **el primer uso operativo**, no el calendario. |
| **BR-M-33** | Cambiar un código maestro referenciado exige proceso excepcional fuera del motor (re-maestro / migración asistida), no UPDATE estándar. |

### 3.5 Migraciones e implantación

| Regla ID | Regla |
|----------|-------|
| **BR-M-40** | En migración de datos legados, el proyecto de implantación opera en modo **importación con códigos preservados** (ver §8). |
| **BR-M-41** | Tras importar códigos históricos, el contador de secuencia del scope debe posicionarse en **max(código numérico existente)**, nunca por debajo, para no generar colisiones. |
| **BR-M-42** | Maestros sin código en archivo fuente reciben AUTO_DEFAULT en importación masiva. |
| **BR-M-43** | La coexistencia temporal de códigos libres legados y autogenerados en un mismo scope es aceptable solo durante la ventana de migración documentada; post cutover aplica política estándar. |

---

## 4. Reglas para documentos (grupo C — F15)

### 4.1 Principio general

| Regla ID | Regla |
|----------|-------|
| **BR-D-01** | Los correlativos documentales de proceso usan política **AUTO_REQUIRED** en operación normal: el usuario **nunca** envía el número en creación. |
| **BR-D-02** | El correlativo se asigna en el momento de **crear el documento en estado inicial** (`borrador` o equivalente), no en la transición a procesado, salvo excepción fiscal explícita. |
| **BR-D-03** | Un documento mantiene su correlativo de por vida; no se renumera al cambiar estado, anular o estornar. |
| **BR-D-04** | Documentos compensatorios (estorno, NC, reversión) reciben **nuevo** correlativo propio; referencian el original vía `documento_referencia_*`, no reutilizan su número. |

### 4.2 Por familia documental

| Familia | Entidades (ej.) | Usuario envía código | Notas de negocio |
|---------|-----------------|----------------------|------------------|
| **Inventario** | `inv_movimiento`, `inv_inventario_fisico` | **Nunca** | Correlativo visible en kardex e integraciones INV. |
| **Compras** | `pur_solicitud_compra`, `pur_cotizacion`, `pur_orden_compra`, `pur_recepcion` | **Nunca** | OC y recepción son trazabilidad con proveedor. |
| **Ventas** | `sls_cotizacion`, `sls_pedido` | **Nunca** | Pedido no hereda número de cotización como identidad. |
| **Logística** | `log_despacho`, `log_guia_remision` | **Nunca** en número; serie guía es maestro fiscal |
| **Manufactura** | `mfg_orden_produccion` | **Nunca** | |
| **Mantenimiento** | `mnt_orden_trabajo` | **Nunca** | |
| **Calidad** | `qms_inspeccion`, `qms_no_conformidad` | **Nunca** | |
| **Finanzas** | `fin_asiento_contable` | **Nunca** | |
| **RRHH** | `hcm_planilla`, `hcm_contrato`, `hcm_prestamo` | **Nunca** | |
| **POS** | `pos_venta`, `pos_turno_caja` | **Nunca** | Turno scoped por punto de venta. |
| **CRM** | `crm_oportunidad` | **Nunca** | |
| **Servicio** | `svc_orden_servicio`, `tkt_ticket` | **Nunca** | |

### 4.3 Documentos derivados e integración entre módulos

| Regla ID | Regla |
|----------|-------|
| **BR-D-10** | Un módulo que genera otro documento (ej. recepción → movimiento INV) **no concatena** el correlativo origen como identidad del destino; cada documento consume su propia secuencia. |
| **BR-D-11** | El vínculo entre documentos es por UUID y campos `documento_referencia_tipo` / `documento_referencia_numero` (snapshot legible), no por igualdad de correlativos. |
| **BR-D-12** | Listados y búsquedas usan el correlativo del documento propio, no cadenas derivadas (`PUR-…`, `PED-…` quedan prohibidas como estándar). |

---

## 5. Reglas para documentos fiscales (comportamiento esperado)

Sin diseñar el motor fiscal. Solo negocio.

| Regla ID | Regla |
|----------|-------|
| **BR-F-01** | La numeración de comprobantes electrónicos (`invbill_comprobante`) y guías (`log_guia_remision`) obedece a la **serie autorizada** y normativa SUNAT, no a la secuencia genérica de documentos internos. |
| **BR-F-02** | El usuario **no elige** el número correlativo fiscal en venta normal; el sistema asigna el siguiente de la serie activa. |
| **BR-F-03** | Una serie fiscal inactiva o agotada **bloquea** emisión; no se salta a otra serie sin configuración explícita. |
| **BR-F-04** | Anulación o baja fiscal **no reutiliza** el número emitido; el hueco es aceptable y auditable según normativa. |
| **BR-F-05** | `codigo_hash`, `codigo_qr`, `codigo_respuesta_sunat` son artefactos de respuesta OSE/SUNAT; política EXTERNAL / sistema fiscal; fuera del motor de códigos internos. |
| **BR-F-06** | El comprobante POS (`pos_venta.numero_comprobante`) es referencia legible al comprobante fiscal; no sustituye `serie`+`numero` de `invbill_comprobante`. |

---

## 6. Reglas para importaciones masivas

| Escenario | Comportamiento esperado |
|-----------|-------------------------|
| **Fila trae código válido y único en scope** | Se persiste tal cual. Secuencia del scope se actualiza a ≥ valor importado si el código es secuencial-parseable. |
| **Fila trae código duplicado en archivo o BD** | Rechazo de la fila con error de negocio; no se genera sustituto silencioso. |
| **Fila no trae código** | AUTO_DEFAULT (maestros) o rechazo configurable (documentos AUTO_REQUIRED: típicamente rechazo en documentos históricos sin número). |
| **Fila trae código con formato inválido** | Rechazo con detalle de formato esperado. |
| **Importación de terceros con RUC/DNI** | `numero_documento` EXTERNAL; `codigo_proveedor` / `codigo_cliente` interno puede venir en archivo o autogenerarse. |
| **Importación de productos con EAN** | `codigo_barra` MANUAL_ONLY/EXTERNAL; `codigo_sku` según columna presente. |
| **Modo migración inicial** | Permite lote con mezcla manual/autogenerado bajo supervisión de implantación; contador alineado al final del lote. |
| **Reimportación / upsert** | No consume nueva secuencia si el código no cambia; cambio de código sujeto a BR-M-30. |

---

## 7. Reglas de concurrencia (perspectiva funcional)

| Situación | Comportamiento esperado del negocio |
|-----------|-------------------------------------|
| Dos usuarios crean sucursal simultáneamente sin código | Ambos reciben códigos distintos consecutivos (`SUC001`, `SUC002`); ninguno ve error por “carrera” si la transacción es correcta. |
| Dos usuarios crean sucursal con el **mismo** código manual | Exactamente uno tiene éxito; el otro recibe error de duplicado claro. |
| Dos usuarios emiten factura en la misma serie al mismo tiempo | Uno recibe número N, el otro N+1; **nunca** el mismo `serie`+`numero`. |
| Reintento de red tras timeout en creación | El negocio no debe duplicar documento con distinto UUID y mismo correlativo; idempotencia operativa es requisito del diseño técnico futuro, pero la expectativa funcional es **un correlativo por intención de negocio**. |
| Usuario consulta “último código” en pantalla y otro crea antes | El primero puede recibir otro código al confirmar; la UI no debe prometer reserva sin función de preview formal (ver §8). |

---

## 8. Preview (“próximo código”)

| Aspecto | Decisión de negocio |
|---------|---------------------|
| **¿Es necesario?** | **Recomendado, no obligatorio** para maestros AUTO_DEFAULT. **No aplica** para documentos AUTO_REQUIRED en flujo estándar (el número aparece tras guardar). |
| **Comportamiento** | Muestra estimación del siguiente código **sin consumir** secuencia ni reservar. |
| **Ventajas** | Mejor UX en altas manuales asistidas; comunicación con proveedores/clientes internos. |
| **Riesgos** | Usuario asume compromiso del número mostrado; colisión si otro usuario crea antes; falsa expectativa en alta concurrencia. |
| **Mitigación funcional** | Etiquetar siempre como “estimado / no reservado”; no imprimir en documentos legales hasta confirmación. |
| **Documentos fiscales** | Preview **desaconsejado** salvo rol administrativo; riesgo de huecos si se malinterpreta como reserva. |

---

## 9. Reinicio de secuencias (solo negocio)

| Regla ID | Regla |
|----------|-------|
| **BR-S-01** | Por defecto las secuencias **no se reinician** por cambio de año fiscal o calendario; continuidad es el comportamiento estándar ERP. |
| **BR-S-02** | Reinicio explícito (volver a 1 o a un origen definido) es acción **administrativa excepcional**, auditada, con permiso elevado y solo cuando no existan colisiones con códigos ya emitidos. |
| **BR-S-03** | Series fiscales: el reinicio obedece a normativa y autorización SUNAT, no a preferencia operativa. |
| **BR-S-04** | Tras reinicio aprobado, los códigos ya emitidos conservan su valor histórico; no se renumeran. |
| **BR-S-05** | Multiempresa: reiniciar secuencia en empresa A **no afecta** empresa B del mismo tenant. |

---

## 10. Prefijos (reglas de negocio)

| Tipo | Ejemplos | Editable por tenant | Regla |
|------|----------|---------------------|-------|
| **Prefijo estándar de producto** | `EMP`, `SUC`, `MOV`, `OC` | Configurable con restricción | Longitud acotada; cambio no retroactivo. |
| **Prefijo de documento** | `MOV`, prefijos compras/ventas | Configurable por entidad y empresa | Afecta solo futuros correlativos. |
| **Serie fiscal** | `F001`, `B001` | MANUAL en alta de serie | Asignación legal; no es “prefijo” libre del motor genérico. |
| **Prefijos de módulo legacy** | `INV-EST-`, `PUR-` | **No estandarizar** | Quedan prohibidos en operación normal post F15A. |
| **Separador** | `-`, vacío | Configurable | Consistencia por entidad dentro del scope. |

**BR-P-01:** Cambiar prefijo no altera códigos históricos.  
**BR-P-02:** Prefijos reservados del sistema (bootstrap `EMP001`) no pueden reasignarse a otra entidad.  
**BR-P-03:** Recomendación ERP: prefijos cortos, mayúsculas, sin espacios; significado opcional, no secuencial semántico obligatorio.

---

## 11. Compatibilidad operativa (sin implementación)

| Dimensión | Impacto en políticas de negocio |
|-----------|----------------------------------|
| **Shared Database** | Mismas reglas; aislamiento por `cliente_id`; secuencias lógicamente independientes por tenant. |
| **Dedicated Database** | Mismas reglas funcionales; cada tenant dedicado posee contadores locales; migración entre modos exige alinear contadores con datos existentes (BR-M-41). |
| **Multiempresa** | AUTO_REQUIRED y AUTO_DEFAULT siempre respetan scope **empresa** salvo `org_empresa`; un usuario en empresa X no consume secuencia de empresa Y. |
| **Multi-tenant** | Ninguna política permite compartir o deducir códigos entre tenants; `codigo_cliente` SaaS permanece EXTERNAL a este motor. |

---

## 12. Riesgos funcionales por política incorrecta

| Política mal aplicada | Problema de negocio |
|-----------------------|---------------------|
| Documento como MANUAL_ONLY | Duplicados, saltos, fraude, imposibilidad de auditar correlatividad. |
| Maestro como AUTO_REQUIRED sin permitir migración | Bloqueo de implantación histórica. |
| Permitir edición libre de códigos referenciados | Rotura de trazabilidad kardex, fiscal, contable. |
| Preview interpretado como reserva | Colisiones y disputas entre usuarios/áreas. |
| Reinicio de secuencia sin gobernanza | Duplicados catastróficos post reinicio. |
| Concatenar correlativos entre módulos | Integraciones frágiles, overflow de longitud, búsquedas inconsistentes. |
| Secuencia tenant donde el UNIQUE es por empresa | Colisiones multiempresa o números “saltados” por empresa. |
| Fiscal en secuencia genérica | Riesgo legal SUNAT, series incorrectas. |

---

## 13. Jerarquía normativa

1. Normativa legal fiscal (SUNAT)  
2. Este documento y `08_CODE_POLICIES.md`  
3. F15 arquitectura (`05`, `03`, `02`)  
4. Estándar ERP Backend V4  
5. Configuración por tenant/empresa (prefijos, no políticas base)

---

## 14. Referencias

| Documento | Contenido relacionado |
|-----------|----------------------|
| `08_CODE_POLICIES.md` | Matriz política por entidad |
| `09_ERP_BEST_PRACTICES.md` | Benchmark ERP mercado |
| `10_FINAL_RECOMMENDATION.md` | Estándar oficial consolidado CAXIS |

---

*F15A — Sin implementación. Listo para diseño DDL/gateway sin reabrir reglas de negocio.*
