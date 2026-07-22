# Auditoría modular — CFG / EVT / ALR / RPT / APS

**Módulos:** CFG (extensión), EVT (nuevo), ALR (nuevo), RPT (diferido), APS (diferido)  
**Prioridad global:** P1 (CFG/EVT/ALR) · P3 (RPT/APS)

---

## CFG

### Estado actual
Solo `cfg_codigo_secuencia`. Sin verticales.

### Cambios recomendados
- Añadir `cfg_vertical_empresa` estilo **A**: códigos tipados, activación, sin JSON de rubro.
- Verticales habilitan menú/módulos en aplicación; **no** guardan semántica industrial.

### Prioridad
**P1**

---

## EVT — Event Bus (nuevo, ADR-03)

### Estado actual
Ausente. Integración implícita síncrona.

### Cambios recomendados
- Modelo outbox/event store interno Core (detalle en fase tablas).
- Contrato: tipo, aggregate, cliente/empresa, payload versionado, correlation id.
- Productores: módulos operativos. Consumidores: ALR, WFL, proyecciones, verticales.

### Prioridad
**P1**

### Riesgos
- Over-engineering de bus antes de 2–3 consumidores reales → mitigar con outbox mínimo.

---

## ALR

### Estado actual
Ausente. A/B proponen regla + alerta generada.

### Cambios recomendados
- Adoptar idea regla/instancia.
- Tipado de condiciones (A) + scheduling/anti-spam (B).
- Suscripción a **tipos de evento EVT**, no solo polling de tablas.
- ALR **no** es el bus.

### Prioridad
**P1**

---

## RPT (ADR-08)

### Estado actual
`bi_reporte` placeholder. A/B proponen métrica/dimensión.

### Decisión
**Diferir tablas.** Concepto semántico aprobado. Prohibir SQL libre en metadatos.

### Prioridad
**P3**

---

## APS (ADR-09)

### Estado actual
Ausente. A = resultados; B = motor/restricciones.

### Decisión
**Sin tablas `aps_*` ahora.** Preparar inputs vía PLN+MES+MFG. Documentar ADR futuro con restricciones tipadas y sin polimorfismo abusivo.

### Prioridad
**P3** (solo arquitectura)

---

## Justificación conjunta

CFG vertical limpio + Event Bus + ALR son infraestructura de plataforma. RPT/APS son enterprise avanzado prematuro si se materializan ahora.
