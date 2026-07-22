# Metodología y fuentes de la auditoría

**Documento:** 01  
**Serie:** CORE ERP V2 — Auditoría arquitectónica oficial

---

## 1. Objetivo

Construir la base oficial de diseño del **Core ERP V2** como plataforma industrial SaaS multi-tenant/multiempresa, agnóstica al rubro, capaz de soportar verticales durante 10–15 años.

Esta auditoría **no** genera tablas nuevas automáticamente ni scripts SQL.

---

## 2. Fuentes

| ID | Archivo | Naturaleza |
|----|---------|------------|
| S0 | `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql` | Baseline productivo del Core |
| SA | `script_core_v2_claudeA.sql` | Propuesta independiente de fortalecimiento |
| SB | `script_core_v2_claudeB.sql` | Propuesta independiente de fortalecimiento |

**Principio:** ninguna propuesta Claude se considera correcta por defecto. Toda decisión se justifica técnicamente contra la regla Core vs Vertical y los principios de diseño.

---

## 3. Restricciones de análisis

- No pensar en migraciones ni compatibilidad de datos históricos.
- No diseñar `ALTER` ni scripts de transición.
- Se asume que la BD puede recrearse desde cero.
- Prioridad absoluta: **mejor diseño posible**.
- Conservar MultiTenant, MultiEmpresa, auditoría, soft delete, consistencia con el resto del ERP.
- No eliminar tablas Core sin justificación arquitectónica fuerte.
- Preferir extender tablas existentes antes que reemplazarlas.
- Evitar duplicación de responsabilidades; alta cohesión / bajo acoplamiento.

---

## 4. Método de evaluación por capacidad

Para cada capacidad detectada en S0/SA/SB:

1. **Clasificar** Core vs Vertical vs Prematura vs Deuda diferible.
2. **Calificar** estado en V010 (ausente / embrionario / básico / maduro / enterprise).
3. **Comparar** A vs B (si aplica).
4. **Decidir** Adoptar / Mejorar / Descartar / Diferir.
5. **Documentar** prioridad, impacto, riesgos.

Plantilla de módulo (`modules/*`):

- Estado actual
- Fortalezas
- Debilidades
- Cambios recomendados
- Justificación
- Prioridad
- Impacto
- Riesgos

---

## 5. Criterios de aceptación de una capacidad en Core

Una capacidad entra al Core físico V2 solo si cumple **todas**:

1. Es utilizada (o razonablemente requerida) por la mayoría de industrias manufactureras / de distribución industrial.
2. No embebe semántica de un rubro concreto.
3. Tiene al menos un consumidor claro en el mapa de módulos Core.
4. Puede modelarse con integridad relacional (FKs, CHECKs) sin polimorfismo abusivo ni SQL libre.
5. No depende de un motor avanzado aún inexistente (p. ej. APS scheduler) para tener sentido.

Si falla (5) pero es estratégicamente necesaria → se deja **ADR + puntos de extensión**, sin tablas físicas.

---

## 6. Criterios de rechazo / diferimiento

| Señal | Acción |
|-------|--------|
| Ejemplo o campo específico TXT/FOD/MET en CFG Core | Rechazar / mover a Vertical |
| Tabla de resultado sin productor (APS impacto sin motor) | Diferir |
| JSON que esconde estados, reglas o grafos de negocio | Rechazar; modelar relacional |
| Polimorfismo `recurso_id` sin FK tipada | Rechazar o rediseñar |
| SQL dinámico en metadatos de reporte | Diferir / rechazar diseño |

---

## 7. Producto de esta serie documental

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Veredicto y priorización |
| `01_METHODOLOGY_AND_SOURCES.md` | Este documento |
| `02_CORE_VS_VERTICAL_CLASSIFICATION.md` | Matriz de clasificación |
| `03_PRELIMINARY_ADR_DECISIONS.md` | Las 10 decisiones preliminares |
| `04_V010_BASELINE.md` | Estado actual del Core |
| `05_PROPOSAL_A_VS_B.md` | Comparación A/B y fusión |
| `modules/*.md` | Auditoría por módulo |
| `90_CORE_V2_DEFINITION.md` | Definición oficial CORE V2 |
| `91_DESIGN_ROADMAP.md` | Orden de diseño de tablas (sin SQL) |

---

## 8. Fuera de alcance de esta auditoría

- Implementación de código FastAPI / RBAC / menús.
- Scripts bootstrap SQL definitivos.
- Diseño detallado de cada Vertical (TXT, FOD, …).
- Estrategia de migración de datos existentes.
