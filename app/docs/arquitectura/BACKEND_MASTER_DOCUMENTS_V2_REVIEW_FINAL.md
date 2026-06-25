# Revisión Final — Auditoría Backend Master Documents V2

**Versión:** 1.0.0  
**Fecha:** 2026-06-24  
**Modo:** READ ONLY — ningún documento oficial modificado  
**Documento revisado:** `app/docs/arquitectura/BACKEND_MASTER_DOCUMENTS_V2_AUDIT.md`  
**Metodología:** Mismo criterio de certificación documental Frontend — reevaluación crítica hallazgo por hallazgo, validación contra código ORG/INV y frontera IAM Session V2

---

## 1. Resumen ejecutivo de la revisión

La auditoría original **es sustancialmente correcta** en su dictamen central: los cinco documentos oficiales siguen siendo válidos para módulos ERP futuros; IAM Session V2 **no debe incorporarse**; ORG + INV siguen siendo la referencia de código.

Tras esta revisión final se **ajustan clasificaciones**, se **descartan hallazgos** que no deben entrar al plan de actualización de los cinco oficiales, y se **corrige la jerarquía documental** (la auditoría original la representaba invertida).

| Métrica | Auditoría original | Revisión final |
|---------|-------------------|----------------|
| **A — Vigente** | 38 | **40** (+2 reclasificados) |
| **B — Actualización menor** | 11 | **5** (6 descartados o absorbidos) |
| **C — Actualización mayor** | 4 | **0 en plan oficial** (4 pospuestos/auxiliares) |
| **D — Exclusivo IAM** | 14 | **15** (+1: F-04 reclasificado) |

**Cambios clave respecto a la auditoría:**

1. La jerarquía canónica correcta es la indicada por gobernanza (STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt), no PROMPT en la cima normativa.
2. Varios hallazgos **B** (F-04, F-05, F-06, F-08, D-05) **no deben implementarse** en los oficiales — o son redundantes o violarían la frontera auth/IAM.
3. Todos los hallazgos **C** quedan **fuera del plan de actualización de los cinco oficiales** — track auxiliar o backlog separado.
4. `RULES_CURSOR_BACKEND.md` y `reglas.md` requieren **proceso independiente** de convergencia Cursor, no mezclado con el patch V4.

**Dictamen:** **Sí puede iniciarse el plan oficial de actualización documental**, con alcance **estrecho** (5 cambios concretos en 4 de los 5 documentos). El track Cursor v3 debe ejecutarse **en paralelo**, no como prerequisito bloqueante del patch normativo.

---

## 2. Jerarquía documental — confirmación y corrección

### 2.1 Jerarquía canónica (confirmada)

La auditoría original colocaba `PROMPT_BACKEND_MAESTRO` en la cima del diagrama. **Eso era incorrecto** como jerarquía normativa. La jerarquía correcta, de mayor a menor autoridad normativa, es:

```
ERP_BACKEND_STANDARDS_V4.md          ← Norma técnica (fuente de verdad)
         ↓
ERP_BACKEND_RULES_V4.md              ← Reglas ejecutables R01–R112 (derivan de STANDARDS)
         ↓
.cursorrules                         ← Resumen operativo Cursor (apunta a STANDARDS + RULES)
         ↓
PROMPT_BACKEND_MAESTRO.md            ← Punto de entrada operativo (delega ejecución)
         ↓
ERP_BACKEND_MASTER_PROMPT_V4.md      ← Proceso por módulo (Fases 0–4)
```

**Documentos de soporte (fuera de la cadena normativa, no sustituyen a STANDARDS):**

- `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` — evidencia origen
- Documentación IAM en `docs/arquitectura/IAM-*` — dominio auth/sesiones

### 2.2 Implicaciones para la actualización

| Documento | Rol en jerarquía | ¿Qué debe contener? |
|-----------|------------------|---------------------|
| **STANDARDS** | Norma | Definiciones técnicas, patrones, §3.7, §5.5, §10, §13–§17, §21 |
| **RULES** | Reglas | R01–R112 numeradas; referencias a STANDARDS; no duplicar narrativa larga |
| **.cursorrules** | Resumen | Reglas críticas + punteros; **no** expandir a copia de RULES |
| **PROMPT** | Entrada | Tabla de documentos + instrucción de inicio; delega a Master Prompt |
| **Master Prompt** | Proceso | Fases 0–4, checklists, referencias ORG/INV |

**Hallazgo de auditoría §2.1:** **DESCARTADO** como representación válida. Reemplazado por jerarquía confirmada arriba.

---

## 3. Validación frontera IAM Session V2

### 3.1 Confirmación: los oficiales NO deben documentar

| Elemento | ¿Presente hoy en los 5 oficiales? | ¿Debe añadirse? | Clasificación |
|----------|-----------------------------------|-----------------|---------------|
| `refresh_tokens` | No | **No** | **D** |
| `token_family` | No | **No** | **D** |
| `session_rotation` / RTR | No | **No** | **D** |
| Replay detection | No | **No** | **D** |
| Active Sessions (admin/self) | No | **No** | **D** |
| Contratos auth (`ERP-IAM-SESSIONS-*`) | No | **No** | **D** |
| Servicios Session V2 | No | **No** | **D** |
| Tablas IAM (`user_session`, V031) | No | **No** | **D** |

**Excepción acotada ya vigente (permanece A):** STANDARDS §3.6 menciona «Sesión padre → Redis» en **impersonación** (restauración `/impersonate/end/`). Es comportamiento transversal de impersonación **preexistente**, no documentación del modelo Session V2. **No expandir** más allá de esa línea.

### 3.2 Reevaluación: ¿IAM mal clasificado como transversal?

| Elemento (auditoría §4.2) | Clas. original | Clas. revisada | Motivo |
|---------------------------|----------------|----------------|--------|
| Separación identidad vs operativo §3.7 | A | **A** | Transversal ERP; ya documentado |
| `require_session_cliente_id` | A | **A** | Transversal ERP |
| Auth audit `AuditService` | A | **A** | Transversal; RULES R65–R68 |
| Redis genérico | A | **A** | Infra; no detallar bridge V2 |
| Feature flags por tenant | C | **DESCARTADO** | Patrón Platform/IAM; no norma ERP módulo |
| Nota `sort_order` auth vs `sort_dir` ERP | B (F-04) | **D** | Es contrato auth; mencionarlo en STANDARDS violaría frontera |
| Session probe en requests ERP | D | **D** | Correcto |

**Conclusión IAM:** Ningún elemento Session V2 fue clasificado incorrectamente como transversal en la auditoría. Un hallazgo **B (F-04)** debe **reclasificarse a D** y **descartarse** del plan de actualización oficial.

### 3.3 Reevaluación: ¿ERP transversal mal clasificado como IAM?

Revisión de los 14 ítems **I-01 a I-14:** todos permanecen **D**. Ningún patrón reutilizable para módulos ERP quedó erróneamente en exclusivo IAM.

Los patrones ERP transversales relevantes (`{codigo}_deps.py`, listados, workflow INV, etc.) están correctamente en **A** (C-03 a C-06, R-01 a R-06).

---

## 4. Confirmación ORG + INV como referencia

| ID | Hallazgo | Revisión | Clas. final |
|----|----------|----------|-------------|
| R-01 | ORG: scope, maestros, listados | Confirmado contra `org_deps.py`, services, pagination | **A** |
| R-02 | INV: transaccional, workflow, RC1.1 | Confirmado contra `inv_deps.py`, movimientos, policies | **A** |
| R-03 | Master Prompt Fase 1.1/1.2 | Usable; referencias de archivo correctas | **A** |
| R-04 | Anexo C checklist INV | Mapeo R82–R104 válido | **A** |
| R-05 | STANDARDS §10.7 Tier A/B/C | Alineado con implementación ORG/INV | **A** |
| R-06 | Nota PUR legacy `order` | Acotación correcta; no contamina estándar | **A** |

**Veredicto:** ORG e INV **siguen siendo la única referencia arquitectónica** para módulos ERP nuevos. IAM Session V2 **no sustituye** ni **compite** con esa referencia.

---

## 5. Matriz de hallazgos — permanecen / cambian / descartan

### 5.1 Coherencia (C-01 a C-08)

| ID | Clas. audit. | Clas. final | Acción |
|----|--------------|-------------|--------|
| C-01 | A | **A** | Permanece |
| C-02 | A | **A** | Permanece |
| C-03 | A | **A** | Permanece |
| C-04 | A | **A** | Permanece |
| C-05 | A | **A** | Permanece |
| C-06 | A | **A** | Permanece |
| C-07 | A | **A** | Permanece |
| C-08 | A | **A** | Permanece |

### 5.2 Contradicciones (H-01 a H-04)

| ID | Clas. audit. | Clas. final | Acción |
|----|--------------|-------------|--------|
| H-01 | B | **B** | **Permanece** — error real en STANDARDS §3.4; extender corrección a Master Prompt matriz L662 |
| H-02 | B | **B** | **Permanece** — RULES encabezado L6 |
| H-03 | B | **B** | **Permanece** (fusionado con O-04) — Master Prompt encabezado L6 |
| H-04 | A | **A** | Permanece — no es contradicción |

### 5.3 Obsolescencia (O-01 a O-06)

| ID | Clas. audit. | Clas. final | Acción |
|----|--------------|-------------|--------|
| O-01 | A | **A** | Permanece |
| O-02 | A | **A** | Permanece |
| O-03 | A | **A** | Permanece |
| O-04 | B | **B** | Absorbido en H-03 — mismo fix |
| O-05 | C | **A** | **Reclasificado** — deuda ya declarada en §21; no requiere actualización |
| O-06 | A | **A** | Permanece |

### 5.4 Reglas faltantes (F-01 a F-08)

| ID | Clas. audit. | Clas. final | Acción |
|----|--------------|-------------|--------|
| F-01 | B | **B** | **Permanece** — ampliar §21 (auth/IAM fuera de checklist ERP); **sin** detallar contratos auth |
| F-02 | C | **Pospuesto** | Fuera del plan oficial — backlog `PROMPT_PLATFORM_V4.md` |
| F-03 | C | **Pospuesto** | Fuera del plan oficial — índice auxiliar `README.md` |
| F-04 | B | **D** | **DESCARTADO** del plan oficial — contrato auth; no entra a STANDARDS |
| F-05 | B | **DESCARTADO** | R27 ya en RULES; `.cursorrules` debe puntero, no duplicar |
| F-06 | B | **DESCARTADO** | R104 ya en RULES/Master Prompt §4.7; no duplicar en `.cursorrules` |
| F-07 | C | **Pospuesto** | Fuera del plan oficial — nota en `bootstrap_v2/README` |
| F-08 | B | **DESCARTADO** | STANDARDS §2.1 ya cubre `tables_erp/`; `.cursorrules` apunta a STANDARDS |

### 5.5 Duplicación (D-01 a D-05)

| ID | Clas. audit. | Clas. final | Acción |
|----|--------------|-------------|--------|
| D-01 | A | **A** | Permanece — duplicación intencional |
| D-02 | A | **A** | Permanece |
| D-03 | A | **A** | Permanece |
| D-04 | A | **A** | Permanece |
| D-05 | B | **Pospuesto** | Riesgo de mantenimiento — track auxiliar post-patch; no bloquea plan oficial |

### 5.6 Referencia ORG/INV (R-01 a R-06)

Todos **A** — permanecen sin cambio.

### 5.7 IAM exclusivo (I-01 a I-14)

Todos **D** — permanecen. Se añade **F-04** como **D-15** (contratos listado auth).

---

## 6. Reevaluación hallazgos B — oficial vs auxiliar

| ID | ¿Incorporar a oficiales? | Documento(s) | Justificación |
|----|--------------------------|--------------|---------------|
| **H-01** | **Sí** | STANDARDS §3.4; Master Prompt matriz L662 | Error factual vs `session_scope.py`; impacto en implementadores |
| **H-02** | **Sí** | RULES encabezado L6 | Clarificar: RULES **detalla**, `.cursorrules` **resume** |
| **H-03 / O-04** | **Sí** | Master Prompt encabezado L6 | PROMPT es entrada; Master Prompt es proceso canónico |
| **F-01** | **Sí** | STANDARDS §21 (+ 1 línea `.cursorrules`) | Frontera ERP vs auth/platform; **sin** listar contratos IAM |
| F-04 | **No** | — | Reclasificado D |
| F-05, F-06, F-08 | **No** | — | Duplicación innecesaria; jerarquía exige punteros |
| D-05 | **No** | — | Track auxiliar post-certificación |

**Alcance B final:** **4 hallazgos**, **4 documentos** afectados (STANDARDS, RULES, Master Prompt, `.cursorrules`).

---

## 7. Reevaluación hallazgos C — necesidad y posposición

| ID | ¿Necesario ahora? | Decisión |
|----|-------------------|----------|
| F-02 `PROMPT_PLATFORM_V4` | No para módulos ERP | **Pospuesto** — sprint Platform futuro |
| F-03 README arquitectura | No bloqueante | **Pospuesto** — artefacto auxiliar |
| F-07 bootstrap vs Python ERP | No bloqueante | **Pospuesto** — `bootstrap_v2/README` |
| O-05 Dashboard BFF | Ya documentado como pendiente | **No acción** — reclasificado A |

**Conclusión C:** **Ningún hallazgo C entra al plan de actualización de los cinco oficiales.**

---

## 8. Riesgo `RULES_CURSOR_BACKEND.md` y `reglas.md`

### 8.1 Diagnóstico

| Archivo | Estado | Conflicto con V4 |
|---------|--------|------------------|
| `docs/prompts/RULES_CURSOR_BACKEND.md` | v3 activo; `alwaysApply: true` | repositories, PROMPT_MODULO_MAESTRO_v3, fallback 422, bloques incrementales |
| `reglas.md` | v3; `alwaysApply: false` | Mismo contenido legacy |

**No forman parte de los cinco documentos oficiales** auditados.

### 8.2 ¿Dentro o fuera de esta gobernanza?

| Opción | Decisión |
|--------|----------|
| Incluir en patch de los 5 oficiales | **Rechazado** — no son documentos oficiales V4 |
| Proceso independiente | **Aprobado** |

**Track recomendado (independiente):** «Convergencia Gobernanza Cursor Activa»

1. Deprecar `RULES_CURSOR_BACKEND.md` v3 **o** reemplazar por puntero a `.cursorrules` + RULES V4.
2. Ajustar `alwaysApply: true` → solo tras convergencia V4 verificada.
3. Deprecar `reglas.md` con redirección a `ERP_BACKEND_RULES_V4.md`.
4. Verificar en Cursor que no compitan reglas v3 con `.cursorrules` V4.

**Prioridad:** **Alta para agentes Cursor**; **paralela** al patch B de oficiales. No bloquea edición de STANDARDS/RULES, pero **sí condiciona** la certificación operativa en Cursor hasta completarse.

---

## 9. Cambios concretos por documento oficial (plan post-revisión)

### 9.1 `ERP_BACKEND_STANDARDS_V4.md`

| # | Cambio | Origen hallazgo |
|---|--------|-----------------|
| 1 | **Corregir §3.4** orden de prioridad `cliente_id`: (1) JWT impersonation → (2) `request.state.cliente_id` → (3) ContextVar tenant → (4) `current_user.cliente_id` legacy | H-01 |
| 2 | **Ampliar §21** con fila o párrafo: módulos **auth/IAM** (`modules/auth/`) no siguen checklist ERP operativo completo; documentación propia en `docs/arquitectura/IAM-*` | F-01 |
| 3 | **Añadir §22 (o bloque en §22 existente)** jerarquía documental canónica (5 niveles) | Jerarquía confirmada |
| 4 | **No añadir:** refresh_tokens, token_family, session_rotation, contratos auth, sort_order, servicios Session V2 | Frontera IAM |

### 9.2 `ERP_BACKEND_RULES_V4.md`

| # | Cambio | Origen hallazgo |
|---|--------|-----------------|
| 1 | **L6:** cambiar «reemplazo definitivo de `.cursorrules`» → «complemento ejecutable de `.cursorrules` (detalle vs resumen)» | H-02 |
| 2 | **Tabla «Documentos relacionados»:** añadir jerarquía STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt | Jerarquía |
| 3 | **No añadir** reglas IAM Session V2 | Frontera IAM |

### 9.3 `.cursorrules`

| # | Cambio | Origen hallazgo |
|---|--------|-----------------|
| 1 | **Bloque «Documentación canónica»:** ordenar explícitamente según jerarquía normativa (STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt) | Jerarquía |
| 2 | **Una línea** bajo referencia ORG+INV: «Módulos auth/IAM/platform: ver STANDARDS §21; no aplicar checklist ERP completo» | F-01 |
| 3 | **No expandir** con R27, R104, `tables_erp/`, detalle sort auth | F-05, F-06, F-08 descartados |

### 9.4 `docs/prompts/PROMPT_BACKEND_MAESTRO.md`

| # | Cambio | Origen hallazgo |
|---|--------|-----------------|
| 1 | **Sección «Documentación de soporte V4»:** reordenar tabla según jerarquía normativa | Jerarquía |
| 2 | **Nota explícita:** este documento es **punto de entrada**; la norma técnica está en STANDARDS, no aquí | Jerarquía |
| 3 | **No añadir** contenido IAM | Frontera IAM |

### 9.5 `ERP_BACKEND_MASTER_PROMPT_V4.md`

| # | Cambio | Origen hallazgo |
|---|--------|-----------------|
| 1 | **L6:** cambiar «reemplazo completo de PROMPT_BACKEND_MAESTRO v3» → «proceso canónico de refactorización; PROMPT_BACKEND_MAESTRO es punto de entrada operativo» | H-03 |
| 2 | **Matriz V3→V4 L662:** corregir orden a `JWT impersonation → request.state → ContextVar → user legacy` | H-01 |
| 3 | **No reescribir** Fases 0–4 | C-07 permanece A |

### 9.6 Resumen de alcance

| Documento | Cambios | Líneas estimadas |
|-----------|---------|------------------|
| STANDARDS | 3 | ~15–25 |
| RULES | 2 | ~5–10 |
| `.cursorrules` | 2 | ~5–8 |
| PROMPT | 2 | ~5–8 |
| Master Prompt | 2 | ~3–5 |
| **Total** | **11 ediciones puntuales** | **~35–55 líneas** |

---

## 10. Dictamen final

### 10.1 ¿La auditoría original es aprobable?

**Sí, con reservas menores.** El dictamen central, la frontera IAM y la referencia ORG/INV **permanecen válidos**. Se corrigen: jerarquía invertida, sobre-inclusión de hallazgos B/C, y F-04 mal ubicado como actualización oficial.

### 10.2 ¿Puede iniciarse el plan oficial de actualización documental?

**Sí.**

| Condición | Estado |
|-----------|--------|
| Estándar V4 vigente para módulos ERP | **Confirmado** |
| IAM Session V2 fuera de oficiales | **Confirmado** |
| ORG + INV como referencia | **Confirmado** |
| Alcance de actualización definido | **Confirmado** — patch B estrecho (§9) |
| Track Cursor v3 | **Paralelo obligatorio** — proceso independiente (§8) |
| Hallazgos C | **Pospuestos** — no incluidos en plan oficial |

### 10.3 Orden de ejecución recomendado

```
Fase 1 (paralelo)
├── Patch B: STANDARDS → RULES → .cursorrules → PROMPT → Master Prompt
└── Track independiente: convergencia RULES_CURSOR_BACKEND + reglas.md

Fase 2 (post-patch, opcional)
├── README arquitectura (auxiliar)
├── PROMPT_PLATFORM_V4 (backlog Platform)
└── Nota bootstrap_v2 (auxiliar)
```

### 10.4 Certificación final

| Criterio | Resultado |
|----------|-----------|
| Coherencia entre oficiales | **PASS** tras H-01, H-02, H-03 |
| Sin contaminación IAM | **PASS** — F-04 descartado del plan |
| ORG/INV referencia | **PASS** |
| Jerarquía documental | **PASS** tras corrección diagrama + punteros |
| Listo para patch oficial | **APROBADO** |
| Listo para agentes Cursor | **CONDICIONADO** al track §8 |

---

## 11. Anexo — registro de cambios de categoría

| ID | Audit. | Final | Motivo |
|----|--------|-------|--------|
| O-05 | C | **A** | Deuda ya documentada; no es laguna |
| F-04 | B | **D** | Contrato auth; no en oficiales ERP |
| F-05 | B | **Descartado** | Duplicación; RULES es fuente |
| F-06 | B | **Descartado** | Duplicación; Master Prompt §4.7 |
| F-08 | B | **Descartado** | STANDARDS §2.1 suficiente |
| D-05 | B | **Pospuesto** | Auxiliar post-patch |
| F-02, F-03, F-07 | C | **Pospuesto** | Fuera de los 5 oficiales |
| Feature flags §4.2 | C | **Descartado** | No norma ERP |
| Diagrama §2.1 audit. | A implícito | **Corregido** | Jerarquía invertida |

---

*Revisión final READ ONLY — Backend Master Documents V2 — CAXIS ERP — 2026-06-24*
