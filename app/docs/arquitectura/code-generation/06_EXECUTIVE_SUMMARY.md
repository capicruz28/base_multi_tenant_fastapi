# F15 — Resumen ejecutivo: Motor de generación de códigos ERP

**Proyecto:** CAXIS ERP Backend V4  
**Fase:** F15 — Auditoría arquitectónica (solo documentación)  
**Fecha:** 2026-07-02  
**Fuente canónica:** `V010__tablas_bd_erp_completo.sql`

---

## 1. Contexto

El modelo de datos ERP define **113 campos de código/numeración** en **79 tablas**, con restricciones UNIQUE mayormente consistentes. Existe infraestructura (`cfg_codigo_secuencia`, repositorio, seed en onboarding) pero **ningún servicio ERP la utiliza** para generar códigos en runtime.

Hoy el comportamiento efectivo es:

- **Maestros:** código manual enviado por API (ORG valida duplicados; INV parcial).
- **Documentos:** manual (`numero_movimiento`) o **ad hoc** por timestamp (`INV-EST-…`, `INV-AJUS-…`).
- **Integraciones:** derivación por concatenación (`PUR-…`, `PED-…`).

---

## 2. Hallazgos clave

| # | Hallazgo | Severidad |
|---|----------|-----------|
| H1 | Motor de secuencias **dormido** — seed sin consumo | P0 |
| H2 | **Desalineación de scope**: 8/9 secuencias onboarding son tenant-level pero UNIQUE exige empresa | P0 |
| H3 | **Sin estándar de formato** entre módulos | P1 |
| H4 | Fiscal (`invbill_*`) requiere motor **por serie**, distinto al cfg genérico | P0 legal |
| H5 | WMS y POS requieren dimensiones **almacén** y **punto de venta** no modeladas en cfg actual | P1 |
| H6 | Infraestructura repository **lista** para UoW transaccional (patrón correcto) | Oportunidad |

---

## 3. Decisiones arquitectónicas F15 (estándar oficial)

### 3.1 ¿Motor centralizado?

**Sí.** Un servicio transversal en `app/core/codigo/` (gateway + políticas + scope resolver), consumido por `*_servicio` de cada módulo ERP. Persistencia en `cfg_codigo_secuencia` (evolución Fase 2) y tablas especializadas para fiscal.

### 3.2 Alcance del motor

| Incluir | Excluir |
|---------|---------|
| Maestros ERP (grupo B): ~38 tablas | Catálogos globales `cat_*` |
| Documentos (grupo C): ~24 tablas | RUC/DNI, EAN, códigos SUNAT de catálogo |
| Series fiscales (submotor F3) | `codigo_hash`, `codigo_qr` |
| WMS/POS con scope extendido | `cliente.codigo_cliente` (SaaS) |
| | Parámetros técnicos (`org_parametro_sistema`) |

### 3.3 Scope de secuencia (regla de oro)

> **Derivar siempre del UNIQUE de V010.**

- **Tenant-global:** solo `org_empresa.codigo_empresa`.
- **Por empresa:** mayoría de maestros y documentos.
- **Por almacén:** WMS zona, ubicación, tarea.
- **Por punto de venta:** turnos de caja.
- **Por serie fiscal:** comprobantes y guías electrónicas.

### 3.4 Política API objetivo (post Fase 2)

- Documentos: `AUTO_REQUIRED` (cliente no envía correlativo).
- Maestros: `AUTO_DEFAULT` (autogenerar si omitido; compatibilidad migración).
- Terceros: `numero_documento` permanece identidad legal externa.

---

## 4. Comparación con buenas prácticas ERP modernos

Los ERP SaaS multi-tenant contemporáneos (SAP Business One, Odoo, NetSuite, Dynamics BC) convergen en:

| Práctica | Descripción | Aplicación CAXIS |
|----------|-------------|------------------|
| **Number Series / Document Sequences** | Tabla de series por entidad, empresa y periodo | `cfg_codigo_secuencia` + extensiones scope |
| **Separación maestro vs. transacción** | SKU/código artículo ≠ número de pedido | Familias F1 vs. F2 en gateway |
| **Numeración fiscal aislada** | Series legales con auditoría estricta | F3 sobre `invbill_serie_comprobante` |
| **Scope company** | Cada empresa legal tiene correlativos propios | Alineado a `empresa_id` en UNIQUE |
| **Gapless vs. performance** | Huecos aceptables en alta concurrencia; fiscal suele ser gapless | Decisión Fase 2; fiscal gapless |
| **No smart sequences en UI** | Usuario no inventa OC-001 manualmente | Eliminar required en schemas documentales |
| **Atomic increment** | `SELECT … UPDLOCK` o equivalente en misma TX | UoW + repository existente |

**Recomendación:** adoptar patrón **Number Series** con gateway central, sin copiar implementación de un ERP específico. Priorizar **INV + PUR + SLS + invbill** como primera ola por dependencias ya implementadas.

---

## 5. Compatibilidad futura

| Dimensión | ¿Escala? | Nota |
|-----------|----------|------|
| Shared DB | ✅ | `cliente_id` en cfg y entidades |
| Dedicated DB | ✅ | cfg en store dedicado (V010 + seed) |
| Multiempresa | ✅ | Con corrección de scope en secuencias |
| Multi-tenant | ✅ | Aislamiento por `cliente_id` |
| Alta concurrencia | ⚠️ | Requiere lock en incremento (Fase 2) |
| Integraciones API | ✅ | Formato predecible por política |

---

## 6. Riesgos si no se implementa Fase 2

1. Colisiones y duplicados en documentos INV/PUR al escalar usuarios.
2. Incumplimiento potencial en numeración fiscal electrónica.
3. Reporting e integraciones frágiles por formatos libres.
4. Multiempresa incorrecta si se activa el seed actual sin correcciones.

---

## 7. Entregables F15

| Documento | Contenido |
|-----------|-----------|
| `01_CODE_FIELDS_INVENTORY.md` | Inventario completo V010 (+ anexo V020) |
| `02_ENTITY_CLASSIFICATION.md` | Clasificación A/B/C/D con justificación |
| `03_SEQUENCE_SCOPE.md` | Scope tenant vs. empresa vs. almacén/serie/PV |
| `04_CURRENT_STATE_AND_RISKS.md` | Estado runtime, inconsistencias, riesgos P0–P2 |
| `05_PROPOSED_ARCHITECTURE.md` | Ubicación `core/codigo`, familias, flujos |
| `06_EXECUTIVE_SUMMARY.md` | Este documento |

---

## 8. Fuera de alcance (Fase 2+)

- Estructura DDL definitiva de `cfg_codigo_secuencia` extendida.
- Algoritmo de incremento y manejo de huecos.
- Implementación del gateway y wiring en servicios.
- Endpoints de administración de series.
- Cambios en frontend y OpenAPI.

---

## 9. Recomendación inmediata

Aprobar el estándar arquitectónico F15 y encargar **Fase 2** con:

1. Catálogo normativo de claves `entidad_logica` alineadas a tablas V010.
2. Corrección de scope en seeds (`empresa_id` por entidad).
3. Gateway transaccional en `app/core/codigo/`.
4. Primera integración: `inv_movimiento` (reemplazar manual + timestamp).
5. Submotor fiscal sobre `invbill_serie_comprobante`.

---

*Auditoría realizada sin modificar código, V010, ORM ni migraciones.*
