# Definición oficial — CORE ERP V2

**Documento:** 90  
**Estado:** Definición arquitectónica cerrada (pre-diseño físico de tablas)  
**Fecha:** 2026-07-22

---

## 1. Qué es el CORE V2

El **CORE ERP V2** es la plataforma ERP Industrial SaaS **multi-tenant** y **multiempresa**, **agnóstica al rubro**, que concentra las capacidades utilizadas por la mayoría de industrias manufactureras y de distribución industrial.

Los conocimientos específicos de industria viven en **Verticales** (`txt_*`, `fod_*`, `met_*`, …) que se activan por empresa vía control-plane, sin contaminar el Core.

---

## 2. Principios inquebrantables

1. MultiTenant + MultiEmpresa + auditoría + soft delete.
2. Regla Core vs Vertical (doc 02).
3. Preferir extensión de V010 a reemplazo.
4. Alta cohesión / bajo acoplamiento entre módulos.
5. JSON solo para atributos altamente variables (ADR-10).
6. Integridad relacional para estados, cantidades, FKs y reglas transaccionales.
7. No implementar APS/RPT semántica física hasta tener consumidores y contratos seguros.

---

## 3. Mapa modular CORE V2

### 3.1 Conservados desde V010 (extensión puntual)

ORG, CAT, INV, WMS, QMS, PUR, LOG, MFG, MRP, MPS, MNT, SLS, CRM, PRC, INV_BILL, POS, HCM, FIN, TAX, BDG, CST, PM, SVC, TKT, BI, DMS, WFL, AUD, CFG (secuencias).

### 3.2 Nuevos / elevados en V2

| Módulo | Rol |
|--------|-----|
| **PLN** | Capacidad y calendarios de recursos (CRP básico) |
| **MES** | Ejecución de piso, paradas, OEE |
| **EVT** | Event Bus interno (infraestructura) |
| **ALR** | Motor de alertas — consumidor de EVT |

### 3.3 Diferidos (arquitectura sí, esquema físico no en ola 1)

| Módulo | Estado |
|--------|--------|
| **APS** | ADR + puntos de extensión vía PLN/MES/MFG |
| **RPT** | Capa semántica conceptual; sin tablas aún |

---

## 4. Capacidades canónicas nuevas del Core

### 4.1 Aggregate `inv_lote`
Identidad, origen, fechas, cantidades (disponible/reservada/bloqueada), estados QC/logísticos, FKs desde movimiento/WMS/QMS/PUR/MFG/factura.

### 4.2 Variantes genéricas
Ejes tipados multi-industria + integración a `inv_producto` stockeable. Sin FKs a catálogos verticales.

### 4.3 WMS V2.0
Estrategia de salida + oleadas + stock ubicación lotificado.

### 4.4 QMS V2.0
Inspección/NC → `lote_id`; cuarentena vía estado del lote.

### 4.5 MES
Ejecución de operación + paradas + catálogo motivos OEE.

### 4.6 PLN
Calendario de capacidad por CT/fecha/turno.

### 4.7 CFG vertical
`cfg_vertical_empresa` limpio (códigos tipados, activación). Sin JSON de industria.

### 4.8 EVT + ALR
Bus de eventos de dominio; alertas como consumidor.

---

## 5. Qué queda explícitamente fuera del Core físico (ola 1)

- Tablas `aps_*`
- Tablas `rpt_*` de capa semántica
- Semántica textil/alimentos/metal/farma tipada
- `configuracion_json` de vertical en CFG
- SQL libre en metadatos de reportes
- WMS slotting/yard (fase posterior)
- CAPA/SPC completo (fase posterior)
- Subledgers FIN completos (deuda faseable, no descartada)

---

## 6. Relación Core ↔ Vertical

```
┌─────────────────────────────────────────────┐
│                 CORE V2                     │
│  ORG INV WMS QMS PUR MFG MES PLN SLS …     │
│  EVT ──► ALR / WFL / proyecciones           │
│  cfg_vertical_empresa (flags)               │
└──────────────────┬──────────────────────────┘
                   │ habilita
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    TXT_*       FOD_*       MET_*   … (Verticales)
```

Regla: el Vertical **extiende**; no redefine aggregates Core (lote, producto, OP).

---

## 7. Criterio de éxito del diseño (Definition of Done arquitectónico)

El diseño CORE V2 se considera cerrado cuando:

1. Cada módulo tiene auditoría documentada (esta serie).
2. Las 10 decisiones preliminares tienen ADR con veredicto.
3. Existe matriz Adoptar/Descartar/Mejorar/Diferir A vs B.
4. Está definida la frontera Core vs Vertical.
5. Está listado el backlog de diseño de tablas **sin** haber generado SQL aún.

**Estado:** cumplido con esta serie documental.

---

## 8. Próximo artefacto (fuera de este documento)

`91_DESIGN_ROADMAP.md` → orden para diseñar el modelo físico definitivo.  
Después: especificación de tablas (aún no scripts bootstrap).
