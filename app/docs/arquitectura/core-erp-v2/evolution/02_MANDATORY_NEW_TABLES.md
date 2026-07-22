# Tablas nuevas obligatorias — justificación C1–C4

**Documento:** Fase D1 · 02  
**Serie:** CORE ERP V2 — Auditoría de evolución  
**Restricción:** Sin columnas. Solo justificación de *existencia*.

---

## Regla

Toda fila de este documento debe citar al menos un criterio:

- **C1** Nuevo Aggregate Root  
- **C2** Nuevo Bounded Context  
- **C3** Capacidad Enterprise imposible por extensión  
- **C4** Relación compleja con entidad propia  

Si no cumple → **no se crea tabla**; se extiende V1.

---

## 1. Obligatorias (ola industrial)

### 1.1 `inv_lote`

| Campo | Valor |
|-------|-------|
| Criterio | **C1** (AR Lote) + **C3** (trazabilidad/FEFO/cuarentena) |
| ¿Por qué no extender? | `lote NVARCHAR` en N tablas no tiene identidad, estado ni cantidades; no puede ser AR |
| Alternativa rechazada | Tabla por módulo (`qms_lote`, `pur_lote`) → duplicación |
| Prioridad | P0 |
| Impacto código | Alto en INV; medio en consumidores |

### 1.2 `wms_oleada`

| Campo | Valor |
|-------|-------|
| Criterio | **C1** (AR Oleada) |
| ¿Por qué no extender? | Un campo `oleada_codigo` en `wms_tarea` no modela ciclo de vida ni avance del wave |
| Prioridad | P1 |
| Impacto código | Medio (WMS tarea + endpoints nuevos) |

### 1.3 `cfg_vertical_empresa`

| Campo | Valor |
|-------|-------|
| Criterio | **C1** (AR VerticalEmpresa) + **C4** (N verticales por empresa) |
| ¿Por qué no extender? | `org_empresa.rubro` es un string; no soporta multi-vertical ni activación temporal |
| Alternativa rechazada | JSON en `org_parametro_sistema` → viola ADR-10 / spillover |
| Prioridad | P1 |
| Impacto código | Bajo (CFG nuevo endpoint; menú ya orientado a módulos) |

### 1.4 Núcleo MES

| Tabla | Criterio | ¿Por qué no extender MFG? |
|-------|----------|---------------------------|
| `mes_ejecucion_operacion` | **C2** BC MES + **C1** AR Ejecucion | MFG no debe absorber OEE/tiempos reales (ADR-02) |
| `mes_parada_maquina` | **C4** hijos de ejecución | Paradas no son campos de OP |
| `mes_motivo_parada` | **C4** catálogo OEE del BC | Motivos no son `mfg_operacion` |

Prioridad: **P1**. Impacto: código nuevo; MFG V1 se preserva.

### 1.5 `pln_calendario_capacidad` (nombre final en D1.1)

| Campo | Valor |
|-------|-------|
| Criterio | **C2** BC PLN + **C3** capacidad temporal |
| ¿Por qué no extender? | `mfg_centro_trabajo` solo tiene capacidad estática; calendario es serie temporal |
| Alternativa rechazada | Filas JSON de calendario en CT → ADR-10 |
| Prioridad | P1 |
| Nota | Prefijo `pln_` preferible; si por preservación de convención se usa `mfg_calendario_capacidad`, el **BC dueño sigue siendo PLN** |

### 1.6 Núcleo EVT (mínimo)

| Tabla (concepto) | Criterio | Notas |
|------------------|----------|-------|
| Outbox / evento persistido | **C2** BC EVT | Una o dos tablas máximo en D1.1; no bus enterprise completo |
| ¿Por qué no `aud_log_auditoria`? | AUD es auditoría técnica; no es contrato de Domain Events | |

Prioridad: **P1**.

### 1.7 Núcleo ALR

| Tabla | Criterio | ¿Por qué no extender? |
|-------|----------|----------------------|
| `alr_regla_alerta` | **C2** BC ALR | No es parámetro ORG ni AUD |
| `alr_alerta_generada` | **C1/C4** instancias | Ciclo de vida propio |

Prioridad: **P1**. ALR **no** absorbe el bus.

---

## 2. Condicionales (decidir en D1.1)

### 2.1 `inv_producto_variante`

| Campo | Valor |
|-------|-------|
| Criterio potencial | C1 AR Variante |
| Preferencia evolución | **No crear**: extender `inv_producto` con `producto_padre_id` + ejes genéricos |
| Crear solo si | Extensión rompe unicidad de SKU, precios PRC, o stock ya acoplado a `producto_id` de forma irrecuperable |
| Prioridad | P0 (capacidad); tabla **condicional** |

Esto **no** reabre ADR-05 (capacidad de variantes). Solo elige materialización mínima.

---

## 3. Explícitamente rechazadas / diferidas (no crear)

| Candidata | Motivo de rechazo ahora |
|-----------|-------------------------|
| `aps_*` | Diferido por ADR-09; no C3 urgente |
| `rpt_metrica` / `rpt_dimension` | Diferido ADR-08; riesgo SQL |
| `inv_serie` | Capacidad Core; no P0 si lote desbloquea la ola; faseable |
| `inv_stock_lote` separada | Preferir extender `inv_stock` (anti-duplicación) |
| `inv_reserva` | Evaluar extensión de stock/movimientos primero; solo C4 si D1.1 lo exige |
| Tablas CAPA/SPC | Evolución QMS P2+ |
| Tablas slotting/yard | WMS P2+ |
| Duplicar maestros por “limpieza” | Prohibido |

---

## 4. Conteo objetivo

| Categoría | Cantidad orientativa |
|-----------|----------------------|
| Nuevas obligatorias | ~10–12 conceptos de tabla |
| Condicionales | 0–1 (`inv_producto_variante`) |
| Rechazadas en ola | APS/RPT/slotting/CAPA/… |

Objetivo de disciplina: **≪** las ~15 tablas que proponían A/B sin filtro de evolución.
