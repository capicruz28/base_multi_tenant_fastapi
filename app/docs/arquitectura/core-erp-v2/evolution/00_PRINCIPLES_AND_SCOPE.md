# Principios de evolución CORE V1 → CORE V2

**Documento:** Fase D1 · 00  
**Serie:** CORE ERP V2 — Auditoría de evolución  
**Estado:** Vigente  
**Restricción:** No modifica D0 ni Etapa 0.5. No diseña columnas ni SQL.

---

## 1. Contexto real del proyecto

| Hecho | Implicación |
|-------|-------------|
| Core V1 existe y se está probando | V2 no es un greenfield conceptual ejecutado a ciegas |
| IAM / CFG / ORG / INV ~maduros | Preservar código y contratos de estos módulos es prioridad |
| BD puede recrearse desde cero | No hay deuda de migración de datos históricos |
| Resto de módulos en desarrollo | Mayor libertad de extensión, pero sin reescritura gratuita |

---

## 2. Principio arquitectónico obligatorio (nuevo)

> **CORE V2 debe construirse como una evolución mínima y controlada del CORE V1.**

### Reglas de diseño físico (aplican desde ahora)

1. **Primero** intentar extender tablas existentes.
2. **Solo** crear tablas nuevas cuando sea estrictamente necesario.

### Criterios para proponer tabla nueva

Una tabla nueva solo es admisible si cumple **al menos uno**:

| # | Criterio |
|---|----------|
| C1 | Representa un **nuevo Aggregate Root** |
| C2 | Representa un **nuevo Bounded Context** (o su núcleo persistente) |
| C3 | Representa una **capacidad Enterprise** imposible de modelar por extensión |
| C4 | Representa una **relación compleja** que justifica entidad propia |

### Prohibición

> Queda **prohibido** crear tablas nuevas únicamente por limpieza conceptual.

---

## 3. Qué permanece congelado (no se reabre)

- Auditoría D0 (`00`–`05`, `90`, `modules/*` de auditoría)
- Modelo conceptual Etapa 0.5 (`conceptual/*`)
- ADRs 01–10 (capacidades y fronteras)
- Lenguaje ubicuo, eventos, extension points

Esta fase traduce esas decisiones a un **mapa de evolución de esquema/código**, bajo el principio de minimalidad.

---

## 4. Qué hace y qué no hace esta fase

| Hace | No hace |
|------|---------|
| Clasificar cada módulo: conservar / extender / rediseñar / tabla nueva | Diseñar columnas |
| Justificar cada tabla nueva con C1–C4 | Generar SQL |
| Estimar impacto en código V1 | Implementar servicios/routers |
| Priorizar P0/P1/P2 | Migraciones de datos |

---

## 5. Clasificadores usados en la auditoría

| Etiqueta | Significado |
|----------|-------------|
| **Conservar** | Tabla/código se mantiene; sin cambio de contrato para V2 ola industrial |
| **Extender** | Se añaden campos/FKs/índices a tabla existente; código crece, no se reescribe |
| **Rediseñar** | Cambio estructural relevante en tabla existente (p. ej. clave de stock); alto impacto en código |
| **Nueva (obligatoria)** | Tabla nueva justificada por C1–C4 |
| **Diferir** | Capacidad conceptual aprobada; sin cambio físico en esta ola |

---

## 6. Prioridades

| Prioridad | Criterio |
|-----------|----------|
| **P0** | Desbloquea trazabilidad industrial / INV maduro en prueba |
| **P1** | Eleva WMS/MES/PLN/CFG vertical/EVT sin romper V1 |
| **P2** | Evoluciones importantes pero no bloqueantes del P0 industrial |
| **P3** | Deuda / diferidos (APS, RPT, stubs, subledgers) |

---

## 7. Relación con el diseño físico posterior

```
D0 + 0.5 (congelados)
        ↓
D1 Evolución V1→V2 (este documento / carpeta evolution/)
        ↓
D1.1 Diseño físico de tablas (columnas/FKs) — solo tras aprobar este mapa
        ↓
I0 Scripts bootstrap
```

**Gate de esta fase:** mapa completo de evolución aprobado.  
**No autorizado aún:** diseño de columnas ni SQL.
