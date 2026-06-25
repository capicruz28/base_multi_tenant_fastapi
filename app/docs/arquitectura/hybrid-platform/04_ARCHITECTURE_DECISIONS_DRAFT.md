# 04 — Architecture Decision Records (Borrador)

> **SUPERSEDED — BL-1.0 (2026-06-25)**  
> Este documento es **histórico** (Etapa 1). Las decisiones oficiales están en:  
> **`architecture-baseline/02_ADR_STATUS.md`**  
> No usar para implementación. Ver `architecture-baseline/07_CHANGELOG_BASELINE_FREEZE.md`.

**Etapa:** 1 — Diseño conceptual  
**Fecha:** 2026-06-25  
**Estado:** ~~Borrador~~ **SUPERSEDED**  
**Restricción:** Sin implementación; recomendaciones conceptuales únicamente

---

## 1. Propósito

Documentar las **decisiones arquitectónicas** que deben tomarse para la plataforma híbrida. Cada ADR presenta el problema, alternativas, trade-offs y una **recomendación preliminar** sujeta a aprobación.

**Ningún ADR de este documento es definitivo** hasta revisión formal.

---

## ADR-001: Separación Control Plane / Data Plane

### Problema

Hoy Platform y datos operativos ERP coexisten en el mismo almacén lógico. Dedicated Database requiere frontera física clara.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Control plane centralizado, data plane por tenant | Platform siempre en almacén central; ERP en almacén resuelto |
| B | Todo replicado por tenant | Cada dedicated incluye copia de catálogo Platform |
| C | Control plane distribuido | Metadata de tenant en cada almacén dedicated |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Frontera clara; catálogo único; operación simple | Dependencia de central para routing |
| B | Autonomía total del tenant | Drift de catálogo; actualizaciones N veces |
| C | Menor latencia local | Pérdida de autoridad única; complejidad de sync |

### Riesgos

- A: Central como SPOF para resolución
- B: Inconsistencia de producto entre tenants
- C: Gobernanza fragmentada

### Recomendación preliminar

**Alternativa A.** Platform permanece como control plane centralizado. Data plane ERP vive en almacén del tenant (shared o dedicated). Alineado con principios P5, P6 y fronteras definidas en `02_PLATFORM_BOUNDARIES.md`.

### Estado

**Pendiente de aprobación.**

---

## ADR-002: Ubicación de sesiones IAM

### Problema

Sesiones V2 (refresh tokens, familias, user_session) hoy persisten en almacén central. En Dedicated, ¿dónde deben vivir?

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Sesiones siempre en control plane | Central para todos los modos |
| B | Sesiones en almacén del tenant | Co-localizadas con datos del tenant |
| C | Híbrido: metadata central, tokens en tenant | Split de responsabilidades |
| D | Sesiones solo en Redis/cache | Sin persistencia relacional |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Un solo punto de revocación; refresh sin resolver almacén ERP | Acoplamiento central; latencia cross-DB en probe |
| B | Localidad; menor dependencia central en runtime | Revocación cross-tenant más compleja; migración de sesiones |
| C | Balance | Mayor complejidad; dos fuentes de verdad |
| D | Simplicidad | Pérdida de durabilidad; recovery difícil |

### Riesgos

- A: Inconsistencia si almacén tenant cae pero sesión central válida
- B: Superadmin e impersonación requieren lógica especial
- D: No apto para enterprise (durabilidad)

### Recomendación preliminar

**Alternativa A** para fase inicial, con Redis como acelerador (estado actual evolucionado). Minimiza cambio respecto a IAM V2 existente. Reevaluar en fase 2 si latencia o compliance exigen B.

### Estado

**Pendiente de aprobación.** Impacto crítico en Dedicated.

---

## ADR-003: Catálogo de permisos (RBAC de producto)

### Problema

El catálogo de permisos es global y se sincroniza en startup. Los grants (`rol_permiso`) son por tenant. ¿Cómo escala en Dedicated?

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Catálogo central; grants en almacén tenant | Platform define; tenant asigna |
| B | Catálogo y grants centralizados | Todo en control plane |
| C | Catálogo replicado en cada almacén dedicated | Copia local en provisioning |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Producto consistente; grants locales | Resolución de permiso_id cross-plane en runtime |
| B | Simple hoy | Grants lejanos de datos ERP; queries cross-DB |
| C | Autonomía en runtime | Sync al actualizar producto |

### Riesgos

- A: Referencias cross-plane si no se abstraen
- B: No escala a dedicated físico
- C: Versionado de catálogo complejo

### Recomendación preliminar

**Alternativa A.** Catálogo en Platform; grants y roles en almacén del tenant. IAM resuelve permisos vía servicio, no vía join cross-almacén en lógica ERP.

### Estado

**Pendiente de aprobación.**

---

## ADR-004: Onboarding como saga vs transacción única

### Problema

Onboarding actual es una transacción atómica que mezcla Platform e ERP. Dedicated requiere pasos en almacenes distintos sin transacción distribuida única.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Saga orquestada con compensación | Pasos idempotentes; rollback semántico |
| B | Transacción única (solo Shared) | Mantener para shared; otro flujo para dedicated |
| C | Provisioning asíncrono | Cola de trabajos; tenant en estado Provisioning |
| D | Dos APIs separadas | Alta Platform + seed manual |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Unificado para todos los modos | Complejidad de compensación |
| B | Sin cambio para shared | Dos caminos = riesgo de divergencia (viola P5) |
| C | Resiliente; escalable | UX de espera; estados intermedios |
| D | Simple | Operación manual; errores humanos |

### Riesgos

- A: Pasos mal compensados dejan tenant huérfano
- B: Duplicación de lógica
- C: Percepción de lentitud en onboarding

### Recomendación preliminar

**Alternativa A + C.** Saga orquestada con estados de ciclo de vida (`Provisioning`) y pasos idempotentes. Un solo flujo conceptual para Shared y Dedicated. Evita bifurcación de negocio.

### Estado

**Pendiente de aprobación.**

---

## ADR-005: Encapsulación del modo de instalación

### Problema

Código actual tiene ramas `database_type == "multi"` en algunos servicios. Viola principio P5.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Modo solo en capa de persistencia | Negocio recibe Tenant Context; infra resuelve |
| B | Strategy pattern explícito en servicios | Interfaz InstallationStrategy inyectada |
| C | Mantener ramas en servicios | Status quo evolucionado |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Negocio limpio; extensible | Requiere refactor de infraestructura |
| B | Testeable | Riesgo de filtrar modo a negocio |
| C | Menor cambio inmediato | Deuda; cada módulo nuevo puede bifurcar |

### Riesgos

- A: Esfuerzo de migración de `apply_tenant_filter` y similares
- C: Proliferación de `if multi` (ya observado en AS-IS)

### Recomendación preliminar

**Alternativa A.** El modo de instalación es metadata de Platform consumida exclusivamente por la capa de resolución de persistencia. Los servicios de aplicación no reciben ni consultan el modo.

### Estado

**Pendiente de aprobación.** Principio ya consolidado conceptualmente (P4, P5).

---

## ADR-006: Aislamiento de datos en Shared vs Dedicated

### Problema

Shared usa aislamiento lógico (identificador de tenant). Dedicated podría eliminar redundancia de identificador de tenant en almacén exclusivo.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Mismo modelo lógico en ambos modos | `cliente_id` (o equivalente) siempre presente |
| B | Dedicated sin identificador de tenant en datos | Almacén ya es el aislamiento |
| C | Vista lógica unificada; schema físico puede variar | Abstracción en infraestructura |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Un solo schema; migración shared↔dedicated simple | Redundancia en dedicated |
| B | Schema más limpio en dedicated | Dos modelos; lógica bifurcada (riesgo P5) |
| C | Flexibilidad | Complejidad de abstracción |

### Riesgos

- B: Viola principio de código único si queries difieren
- A: Ninguno crítico; redundancia aceptable

### Recomendación preliminar

**Alternativa A o C.** Preferir modelo lógico unificado; si dedicated omite columna física, la infraestructura la inyecta o ignora transparentemente. **Nunca** que el servicio ERP sepa cuál caso aplica.

### Estado

**Pendiente de aprobación técnica.**

---

## ADR-007: Provisioning de almacén Dedicated

### Problema

Dedicated requiere crear almacén físico, aplicar schema, registrar metadata. ¿Quién ejecuta y cuándo?

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Provisioning síncrono en onboarding | Tenant espera hasta listo |
| B | Provisioning asíncrono | Tenant en Provisioning; notificación al completar |
| C | Pre-provisioned pool | Almacenes vacíos pre-creados; asignación rápida |
| D | Cliente aporta almacén (on-premise) | Platform solo registra metadata |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | UX simple | Timeout; fallos bloquean request |
| B | Resiliente | Complejidad de estados |
| C | Alta rápida | Costo de pool ocioso |
| D | Enterprise | Validación de conectividad; seguridad |

### Riesgos

- A: SLA de onboarding difícil en dedicated
- C: Almacenes huérfanos en pool

### Recomendación preliminar

**B + C combinados.** Pool para velocidad; fallback a creación async. D como extensión futura (on-premise).

### Estado

**Pendiente de aprobación.**

---

## ADR-008: Migración Shared → Dedicated

### Problema

Clientes existentes pueden requerir migración de modo. Proceso de alto riesgo.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Migración online con doble escritura temporal | Sin downtime |
| B | Migración offline | Tenant en estado Migrando; downtime |
| C | Solo nuevos tenants en dedicated | Sin migración |
| D | Export/import manual | Operación asistida |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Sin downtime | Máxima complejidad |
| B | Más simple | Ventana de indisponibilidad |
| C | Sin riesgo migración | Limita adopción |
| D | Control total | No escala |

### Riesgos

- A: Inconsistencia en ventana de doble escritura
- B: SLA comprometido

### Recomendación preliminar

**Fase 1: C** (solo nuevos tenants). **Fase 2: B** (migración offline orquestada). **Fase 3: evaluar A** si demanda enterprise lo exige.

### Estado

**Pendiente de aprobación comercial y técnica.**

---

## ADR-009: Impersonación bajo Dedicated

### Problema

Superadmin impersona tenant accediendo a datos operativos. En dedicated, datos están en almacén separado.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Impersonación resuelve almacén del tenant target | Mismo flujo; infra resuelve |
| B | Bloquear impersonación en dedicated | Restricción de modo |
| C | Proxy de lectura centralizada | Copia de datos para soporte |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Paridad funcional | Superadmin accede a almacén dedicado |
| B | Simple | Funcionalidad reducida |
| C | Soporte sin acceso directo | Duplicación; compliance |

### Riesgos

- A: Auditoría y acceso a almacén cliente
- B: Soporte enterprise degradado

### Recomendación preliminar

**Alternativa A** con auditoría reforzada. Impersonación es capacidad de Platform/IAM; la resolución de almacén es infraestructura.

### Estado

**Pendiente de aprobación.**

---

## ADR-010: Extensibilidad On-Premise / Cloud privada

### Problema

Principio P7 exige soportar modos futuros sin cambiar negocio.

### Alternativas

| ID | Alternativa | Descripción |
|----|-------------|-------------|
| A | Modo como enum extensible en Platform | Nuevos modos = nueva metadata + conector infra |
| B | Plugin system para conectores | Registro dinámico de estrategias de almacén |
| C | Solo shared + dedicated por diseño | Sin extensión formal |

### Ventajas / Desventajas

| Alt | Ventajas | Desventajas |
|-----|----------|-------------|
| A | Simple; suficiente para 3-4 modos | Enum puede crecer |
| B | Máxima flexibilidad | Over-engineering temprano |
| C | Enfoque | Requiere rediseño para on-premise |

### Riesgos

- B: Complejidad prematura
- C: Incumple P7

### Recomendación preliminar

**Alternativa A** con contrato de infraestructura documentado. Evolucionar a B solo si modos custom lo exigen.

### Estado

**Pendiente de aprobación.**

---

## 2. Resumen de ADRs

| ADR | Tema | Recomendación preliminar | Prioridad |
|-----|------|--------------------------|-----------|
| 001 | Control / Data plane | Separación central / tenant almacén | Crítica |
| 002 | Sesiones IAM | Centralizadas (fase 1) | Crítica |
| 003 | Catálogo permisos | Central catálogo; grants en tenant | Alta |
| 004 | Onboarding | Saga + estados async | Crítica |
| 005 | Encapsulación modo | Solo en infraestructura | Crítica |
| 006 | Aislamiento datos | Modelo lógico unificado | Alta |
| 007 | Provisioning dedicated | Async + pool | Alta |
| 008 | Migración modo | Nuevos primero; offline después | Media |
| 009 | Impersonación | Resolver almacén target | Media |
| 010 | Extensibilidad | Enum de modos extensible | Media |

---

## 3. ADRs derivados de auditoría AS-IS

| Riesgo AS-IS | ADR relacionado |
|--------------|---------------|
| R-C01 Onboarding cross-boundary | ADR-004 |
| R-C04 Permisos globales | ADR-003 |
| R-C05 Sesiones centralizadas | ADR-002 |
| R-I01 Filtro cliente_id | ADR-005, ADR-006 |
| R-I02 database_type parcial | ADR-005 |
| R-C03 Sin metadata en onboarding | ADR-004, ADR-007 |

---

## 4. Proceso de aprobación sugerido

1. Revisión de modelo conceptual (`01`, `02`, `03`)
2. Discusión de ADRs críticos (001, 002, 004, 005)
3. Aprobación formal por arquitecto principal
4. Solo entonces: etapa técnica (connection resolver, schema, etc.)

**Ninguna implementación debe iniciarse con ADRs en estado borrador.**
