# F16B — Análisis de gaps e inconsistencias

**Fase:** F16B — Auditoría final de validación  
**Fecha:** 2026-07-03  
**Metodología:** Búsqueda de contradicciones entre F15, F15A, F16, F16A, V010 y coherencia interna del diseño. **No** propuestas de rediseño.

**Clasificación:**

| Nivel | Criterio |
|-------|----------|
| **P0** | Bloquea implementación fundacional o produce comportamiento incorrecto inevitable |
| **P1** | Bloquea olas específicas o requiere decisión antes de esa ola |
| **P2** | Documentación, UX o deuda ya reconocida; no bloquea Ola 0 |

---

## 1. Resumen ejecutivo de gaps

| Nivel | Cantidad | Bloquea F17 Ola 0 |
|-------|----------|-------------------|
| P0 | 0 (diseño) / 3 (AS-IS impl) | No — son trabajo de Ola 0 |
| P1 | 3 | No — olas posteriores |
| P2 | 6 | No |

**No se detectaron contradicciones que obliguen a replantear arquitectura F15–F16A.**

---

## 2. Gaps P0 — Implementación AS-IS (ya en F16 `16`)

Estos gaps **no son fallos del diseño**; son deuda conocida que Ola 0 debe resolver.

| ID | Descripción | Fuente | Estado diseño |
|----|-------------|--------|---------------|
| **GAP-P0-01** | UNIQUE cfg `(cliente_id, empresa_id, entidad)` no soporta ALMACEN/PUNTO_VENTA | V010 vs F16 `14` | ✅ Resuelto en diseño: `scope_fingerprint` (INC-04) |
| **GAP-P0-02** | Seed onboarding `empresa_id=NULL` para entidades empresa-scoped | F15 `04`, INC-01 | ✅ Plan migración Ola 0 |
| **GAP-P0-03** | `CfgCodigoSecuenciaRepository` sin `update_ultimo_numero` en runtime | F15 `04`, INC-05 | ✅ AllocationCoordinator Ola 0 |

**Veredicto P0:** El diseño contempla estos gaps; la implementación **debe** comenzar por Ola 0 para cerrarlos. No hay P0 de diseño sin mitigación.

---

## 3. Gaps P1 — Decisiones o alineaciones antes de olas específicas

### GAP-P1-01 — Store fiscal guía de remisión (EX-08)

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | `log_guia_remision` en catálogo como F3/FISCAL/SERIE_FISCAL; V010 no tiene tabla serie guía equivalente a `invbill_serie_comprobante` |
| **Impacto** | Bloquea Ola 4.3 (`log_guia_remision` emisión) |
| **Referencias** | INC-10, F16 `13` §5.3, `25` EX-08 |
| **Mitigación existente** | Roadmap Ola 4; evaluación explícita en `16` |
| **¿Replanteo arquitectura?** | No — extensión de FiscalSeriesStore o DDL serie guía en Ola 4 |

---

### GAP-P1-02 — `CodeParser` omitido en inventario F16 `11`

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | F16 `11` §4 no lista `CodeParser`; F16A `20` y flujos manual/align lo requieren |
| **Impacto** | Riesgo de omisión en implementación si solo se lee F16 `11` |
| **Mitigación** | F16A `20` es autoritativo; incluir Parser en Ola 0 junto a Formatter/Validator |
| **¿Replanteo?** | No — omisión documental |

---

### GAP-P1-03 — Dedicated: FK `cliente_id` cfg vs store local

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | INC-09: ORM apunta central; dedicated usa tenant store |
| **Impacto** | Wiring CfgSequenceStore en modo dedicated |
| **Mitigación** | TA-06 operation store resolver; patrón existente en plataforma híbrida |
| **¿Replanteo?** | No — implementación infra |

---

## 4. Gaps P2 — Observaciones no bloqueantes

### GAP-P2-01 — `dms_documento` en F16 `13` pero excluida del catálogo

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | F16 `13` §5.1 lista `dms_documento` scope EMPRESA; F16A `21` la excluye (MANUAL_ONLY) |
| **Impacto** | Ninguno en runtime; catálogo prevalece |
| **Acción** | Ninguna en F17 (no modificar docs congelados) |

---

### GAP-P2-02 — `pos_venta` scope EMPRESA vs UNIQUE V010 con `punto_venta_id`

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | F16 `13` §8.3 afirma «UNIQUE solo empresa»; V010 `UQ_posvta_numero` incluye `punto_venta_id` |
| **Impacto** | El diseño EMPRESA-scope **sigue siendo válido** (contador compartido por empresa); la nota factual en F16 es imprecisa |
| **Alternativa no adoptada** | PUNTO_VENTA scope permitiría `VTA000001` repetido en cada PV |
| **¿Error de clasificación?** | No — decisión consciente F16; compatible con V010 |

---

### GAP-P2-03 — Colisiones de prefijo entre entidades distintas

| Prefijo | Entidades | Scope | Riesgo |
|---------|-----------|-------|--------|
| OP | `mfg_operacion`, `mfg_orden_produccion` | EMPRESA | Confusión UX; UNIQUE por tabla |
| EMP | `org_empresa`, `hcm_empleado` | TENANT vs EMPRESA | Bajo |
| CC | `org_centro_costo`, `pur_cotizacion` | EMPRESA | Bajo |
| PRE | `bdg_presupuesto`, `hcm_prestamo` | EMPRESA | Bajo |

**Impacto:** Ninguno en unicidad técnica; aceptable en V1.

---

### GAP-P2-04 — Conteo módulo LOG en `21` §9

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | Tabla indica LOG=3; entradas reales: transportista, ruta, despacho, guía = 4 |
| **Impacto** | Solo documentación auxiliar |

---

### GAP-P2-05 — `prefijo` NVARCHAR(5) AS-IS

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | INC-03; prefijos actuales caben pero sin margen |
| **Impacto** | Migración Ola 0 a NVARCHAR(10) ya diseñada |

---

### GAP-P2-06 — Idempotencia API no especificada en contrato OpenAPI

| Aspecto | Detalle |
|---------|---------|
| **Síntoma** | F16 `15` §2.4 deja ventana dedup a implementación |
| **Impacto** | Olas API; no bloquea core motor |

---

## 5. Validaciones sin gap detectado

| Área auditada | Resultado |
|---------------|-----------|
| **Clasificación grupo B/C** | 63 entradas; exclusiones A/D correctas |
| **Políticas AUTO_* / EXTERNAL / MANUAL** | Sin asignación incorrecta en catálogo |
| **Familias F1–F5** | Coherentes con policy (`19` §7) |
| **Duplicados sequence_key** | Ninguno en `21` |
| **Dependencias circulares Gateway** | DAG limpio: Catalog → Resolvers → Coordinator → Stores |
| **cfg modelo físico F16 `14`** | Soporta 5 scopes con `scope_fingerprint` |
| **Shared vs Dedicated** | Misma semántica; routing por operation store (TA-06) |
| **Multiempresa** | TENANT `org_empresa`; resto EMPRESA/ALMACEN/PV independientes |
| **TX rollback / manual / preview** | Sin contradicción en `15` |
| **Concurrencia allocate** | Comportamiento definido; lock = detalle impl |
| **Roadmap dependencias** | Ola 0 bloqueante; sin fase olvidada |

---

## 6. Parser / Formatter / Validator — coherencia

| Componente | ¿Implementable sin circularidad? | Nota |
|------------|----------------------------------|------|
| PolicyResolver | ✅ | Solo catálogo |
| ScopeResolver | ✅ | Solo catálogo + context |
| CodeFormatter | ✅ | Stateless; perfiles `20` |
| CodeParser | ✅ | Invocado por Align y manual path |
| CodeValidator | ✅ | Stateless |
| PreviewReader | ✅ | Read-only cfg |
| CounterAlignmentService | ✅ | Parser + cfg write |
| AllocationCoordinator | ✅ | Formatter + stores |

---

## 7. Tabla consolidada

| ID | Severidad | Bloquea F17 inicio | Mitigación |
|----|-----------|-------------------|------------|
| GAP-P0-01..03 | P0 impl | No | Ola 0 |
| GAP-P1-01 | P1 | No (sí Ola 4.3) | FiscalSeriesStore guía |
| GAP-P1-02 | P1 | No | Incluir Parser Ola 0 |
| GAP-P1-03 | P1 | No | Operation store |
| GAP-P2-01..06 | P2 | No | Documentado / aceptado |

---

## 8. Conclusión

**Existen gaps documentados; ninguno invalida el contrato maestro F16A.** Los P0 son deuda AS-IS con plan en Ola 0. Los P1 acotan olas 4 e infra dedicated. No se requiere nueva fase de diseño.

---

*Validación módulo en `24`. Veredicto en `27`.*
