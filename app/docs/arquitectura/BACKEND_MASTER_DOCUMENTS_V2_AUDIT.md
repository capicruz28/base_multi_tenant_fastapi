# Auditoría de Gobernanza Documental — Backend Master Documents V2

**Versión:** 1.0.0  
**Fecha:** 2026-06-24  
**Modo:** READ ONLY — ningún documento oficial fue modificado  
**Alcance:** Cinco documentos oficiales de gobernanza Backend ERP  
**Metodología:** Mismo criterio de certificación documental aplicado al Frontend (coherencia, contradicciones, obsolescencia, lagunas, duplicación, separación dominio transversal vs IAM, validación contra código referencia ORG/INV, jerarquía, clasificación A/B/C/D, dictamen final)  
**Validación de código:** ORG, INV, `session_scope.py`, auth/IAM Session Management V2 (solo lectura, para delimitar frontera)

---

## Documentos auditados

| # | Documento | Rol declarado | Revisión documentada |
|---|-----------|---------------|----------------------|
| 1 | `.cursorrules` | Resumen operativo Cursor + punteros canónicos | 2026-06-16 post ORG+INV session scope |
| 2 | `docs/prompts/PROMPT_BACKEND_MAESTRO.md` | Prompt operativo de entrada | 2026-06-16 |
| 3 | `app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md` | Estándar técnico detallado | 2026-06-16 |
| 4 | `app/docs/arquitectura/ERP_BACKEND_RULES_V4.md` | Reglas operativas R01–R112 | 2026-06-16 |
| 5 | `app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md` | Flujo de refactorización por módulo (Fases 0–4) | 2026-06-16 |

**Fuera de alcance oficial (pero evaluados como riesgo perimetral):** `reglas.md`, `docs/prompts/RULES_CURSOR_BACKEND.md` (v3 activo), documentación IAM Session Management V2 en `docs/arquitectura/IAM-*`.

---

## 1. Resumen ejecutivo

Los cinco documentos oficiales Backend **siguen siendo válidos como estándar reutilizable** para el desarrollo de futuros módulos ERP (ORG, INV, CRM, Compras, Producción, RRHH, Contabilidad, Costos, Comercial y cualquier módulo operativo nuevo). La arquitectura V4 — capas `presentation → application/services → queries`, session scope unificado, listados escalables, transaccional INV, evaluación de contratos y proceso Master Prompt — está **alineada con el código de referencia ORG e INV** y **no ha sido sustituida** por IAM Session Management V2.

IAM Session Management V2 afecta persistencia y servicios de **auth/sesiones refresh**; el análisis de impacto del proyecto confirma que **ERP session scope** (`session_scope.py`, `{codigo}_deps.py`, JWT operativo) **no depende del modelo de tres tablas** IAM. Por tanto, los documentos oficiales **no deben convertirse** en documentación de sesiones V2.

**Hallazgos globales:**

| Clasificación | Cantidad | Interpretación |
|---------------|----------|----------------|
| **A — Vigente** | 38 | Núcleo normativo correcto y usable hoy |
| **B — Actualización menor** | 11 | Correcciones puntuales sin replantear V4 |
| **C — Actualización mayor** | 4 | Gaps estructurales o cobertura Platform; no bloquean PUR/CRM |
| **D — Exclusivo IAM** | 14 | No incorporar a documentos oficiales ERP |

**Contradicciones críticas entre los cinco documentos:** 2 (prioridad `cliente_id` §3.4; meta-texto “reemplazo” de `.cursorrules`).

**Dictamen:** **Procede iniciar un ciclo de actualización menor (B)**, no una reescritura mayor. Los documentos pueden seguir gobernando refactorizaciones ERP **desde ya**, aplicando las correcciones B en paralelo al primer módulo nuevo. Las actualizaciones C son deseables pero **no prerequisito** para ORG/INV-style modules.

---

## 2. Jerarquía documental

### 2.1 Jerarquía declarada (coherente en los cinco)

```
                    ┌─────────────────────────────┐
                    │  PROMPT_BACKEND_MAESTRO.md  │  ← Entrada operativa
                    └──────────────┬──────────────┘
                                   │ delega
                    ┌──────────────▼──────────────┐
                    │ ERP_BACKEND_MASTER_PROMPT_V4 │  ← Proceso por módulo
                    └──────────────┬──────────────┘
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
┌──────────▼──────────┐ ┌─────────▼─────────┐ ┌──────────▼──────────┐
│ ERP_BACKEND_RULES_V4 │ │ ERP_BACKEND_       │ │ .cursorrules        │
│ (reglas R01–R112)    │ │ STANDARDS_V4       │ │ (resumen Cursor)    │
└──────────┬──────────┘ │ (estándar técnico) │ └──────────┬──────────┘
           │            └─────────┬─────────┘            │
           └──────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ ERP_BACKEND_ARCHITECTURE_  │  ← Fuente histórica
                    │ ALIGNMENT_AUDIT.md         │     (no auditado aquí)
                    └───────────────────────────┘
```

### 2.2 Evaluación de jerarquía

| Aspecto | Estado | Clasificación |
|---------|--------|---------------|
| STANDARDS como fuente técnica normativa | Correcto; RULES y Master Prompt referencian §3.7, §5.5, §10, §13–§17 | **A** |
| Master Prompt como proceso obligatorio pre-código | Coherente en los 5 documentos | **A** |
| `.cursorrules` como capa resumida | Válido; duplica reglas críticas intencionalmente | **A** |
| RULES declara “reemplazo definitivo de `.cursorrules`” | Contradice el hecho de que `.cursorrules` sigue siendo documento oficial listado | **B** |
| Master Prompt declara “reemplazo completo de PROMPT_BACKEND_MAESTRO v3” | PROMPT actual es puntero delgado; meta-texto desactualizado | **B** |
| Índice único `app/docs/arquitectura/README.md` | Propuesto en Adoption Plan; no existe entre los 5 oficiales | **C** |
| `PROMPT_PLATFORM_V4.md` | Anexo B Master Prompt: pendiente; Platform sin prompt dedicado | **C** |

---

## 3. Validación contra código referencia (ORG + INV)

| Tema normativo | Evidencia código | ¿Docs oficiales vigentes? |
|----------------|------------------|---------------------------|
| `{codigo}_deps.py` + `get_{codigo}_session_client_id` | `org_deps.py`, `inv_deps.py` → `require_session_cliente_id` | **A** — coincide |
| `require_erp_session` en router padre | `modules/inv/presentation/endpoints.py` | **A** |
| OrgScopePolicy TENANT/COMPANY/HYBRID | `session_scope.py`, `org_deps.py` | **A** |
| Listados `page`, `limit`, `buscar`, `sort_by`, `sort_dir` | `app/shared/pagination/`, services ORG/INV | **A** |
| Cabecera-detalle embebido | `MovimientoConDetalleCreate`, endpoints INV | **A** |
| Workflow / write policy / rutas proceso | `inv_workflow_enforcement.py`, `inv_stock_write_policy.py`, RC1.1 | **A** |
| Queries en `infrastructure/database/queries/{cod}/` | `queries/org/`, `queries/inv/` | **A** |
| Prioridad impersonación `cliente_id` | `resolve_session_cliente_id` en `session_scope.py` | **B** — STANDARDS §3.4 orden incorrecto (ver H-02) |
| IAM Session V2 (tablas, rotación, RTR) | `session_v2_feature.py`, servicios auth | **D** — no aplica a módulos ERP |

**Conclusión ORG/INV:** Siguen siendo la referencia correcta y suficiente para nuevos módulos. IAM V2 no invalida ese patrón.

---

## 4. IAM Session Management V2 — frontera transversal vs exclusivo

### 4.1 Elementos exclusivos IAM — **NO incorporar** (clasificación D)

| Elemento | Motivo |
|----------|--------|
| Modelo `user_session` + `token_family` + `refresh_tokens` | Persistencia auth; irrelevante para PUR/CRM/FIN |
| Rotación RTR, `is_used`, `is_compromised`, replay por familia | Algoritmo OAuth refresh |
| `IAM_SESSION_MANAGEMENT_V2_ENABLED`, tenant allowlist | Feature flag de cutover IAM |
| Servicios `session_rotation_service`, `session_revocation_service`, `session_redis_bridge`, etc. | Dominio auth |
| Endpoints `/auth/sessions/*`, admin sessions, session probe | Contrato IAM, no ERP operativo |
| Parámetro `sort_order` en listados auth (vs `sort_dir` ERP) | Legacy contrato IAM admin |
| Throttle `last_business_activity_at` en middleware | Optimización sesión IAM |
| DDL `V031__iam_session_management_v3.sql` | Migración auth central |
| Contratos `ERP-IAM-SESSIONS-API-CONTRACT-V2.md` | Documentación IAM propia |

### 4.2 Elementos evaluados como transversales — decisión

| Elemento | ¿Incorporar al estándar ERP? | Clasificación |
|----------|------------------------------|---------------|
| Separación identidad vs contexto operativo (`§3.7`) | Ya documentado; validado con impersonación | **A** |
| `require_session_cliente_id` centralizado | Ya documentado | **A** |
| Auth audit `AuditService.registrar_auth_event` | Ya en RULES R65–R68 | **A** |
| Redis genérico (blacklist JWT) | Infra transversal; no detallar modelo sesión V2 | **A** (sin expandir) |
| Feature flags por tenant para rollout | Patrón útil Platform; no norma ERP módulo | **C** (opcional futuro Platform prompt) |
| Nota “módulos auth/IAM pueden usar nombres legacy en query params” | Evitar confundir con `sort_dir` ERP | **B** |
| Session probe / validación refresh en cada request ERP | No aplica; ERP usa access JWT + deps existentes | **D** |

**Conclusión IAM:** Ningún cambio sustancial de Session V2 debe entrar a los cinco documentos oficiales. Solo una **nota de frontera** (auth vs ERP operativo) sería actualización menor útil.

---

## 5. Matriz de hallazgos

**Leyenda:** ID | Hallazgo | Documento(s) | Clasificación

### 5.1 Coherencia inter-documental

| ID | Hallazgo | Doc(s) | Clas. |
|----|----------|--------|-------|
| C-01 | Los cinco documentos comparten fecha/revisión 2026-06-16 y referencia ORG+INV | Todos | **A** |
| C-02 | Stack, arquitectura modular, prohibición domain/repositories ERP alineados | Todos | **A** |
| C-03 | Session scope: `require_erp_session`, `{codigo}_deps.py`, §3.7 identidad vs operativo coherente entre .cursorrules, RULES R17–R25/R110–R112, STANDARDS §3.7/§5.5, Master Prompt Fase 1–2 | Todos | **A** |
| C-04 | Listados escalables (opt-in `page`, envelope, `sort_by`/`sort_dir`, PERF) alineados | Todos | **A** |
| C-05 | Transaccional INV (cabecera-detalle, workflow, derivadas, rutas proceso, estorno) alineado | Todos | **A** |
| C-06 | Manejo errores HTTP (`ConflictError` 409 duplicados, anti-patrón `except Exception→500`) alineado | Todos | **A** |
| C-07 | Proceso Fase 0→4 con checkpoints; PROMPT delega íntegramente en Master Prompt | PROMPT, Master Prompt | **A** |
| C-08 | PROMPT_BACKEND_MAESTRO lista `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` como soporte; coherente con STANDARDS fuente | PROMPT, STANDARDS | **A** |

### 5.2 Contradicciones

| ID | Hallazgo | Doc(s) | Clas. |
|----|----------|--------|-------|
| H-01 | **Prioridad resolución `cliente_id`:** STANDARDS §3.4 ordena (2) ContextVar → (3) `request.state`. Código `session_scope.resolve_session_cliente_id` y `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` ordenan (2) `request.state` → (3) ContextVar. Documentos oficiales internamente inconsistentes | STANDARDS §3.4 vs realidad código | **B** |
| H-02 | RULES encabezado: “reemplazo definitivo de `.cursorrules`” pero `.cursorrules` permanece documento oficial activo con contenido propio | RULES, .cursorrules | **B** |
| H-03 | Master Prompt: “reemplazo completo de PROMPT_BACKEND_MAESTRO v3” mientras PROMPT actual es wrapper de 67 líneas | Master Prompt, PROMPT | **B** |
| H-04 | RULES R56 / STANDARDS §12.3: estado transaccional inválido → 422; misma regla indica terminales/doble op → 409. No es contradicción lógica pero requiere lectura cuidadosa; Master Prompt Fase 3 resume bien | RULES, STANDARDS | **A** |

### 5.3 Reglas obsoletas (dentro de los cinco oficiales)

| ID | Hallazgo | Doc(s) | Clas. |
|----|----------|--------|-------|
| O-01 | Referencias a repositories como capa ERP: **ausentes** en los cinco (correctamente eliminadas vs v3) | Todos | **A** |
| O-02 | Fallback 422 para duplicados: **eliminado** en los cinco; alineado con `ConflictError` | Todos | **A** |
| O-03 | `DatabaseConnection.ERP`: correctamente marcado inexistente | Todos | **A** |
| O-04 | Meta-texto “reemplazo” de PROMPT v3 / .cursorrules: obsoleto semánticamente | Master Prompt, RULES | **B** |
| O-05 | STANDARDS §21 “Dashboard BFF pendiente”: sigue siendo deuda real; no obsoleto pero incompleto | STANDARDS | **C** |
| O-06 | STANDARDS §7.4 deuda D03 dual `require_super_admin`: sigue vigente como deuda documentada | STANDARDS | **A** |

### 5.4 Reglas faltantes

| ID | Hallazgo | Doc(s) | Clas. |
|----|----------|--------|-------|
| F-01 | Frontera explícita **módulos ERP operativos vs módulos Platform/Auth/IAM** (qué reglas no aplican) | .cursorrules (gap); STANDARDS §21 parcial | **B** |
| F-02 | Prompt dedicado Platform (`PROMPT_PLATFORM_V4.md`) referenciado pero no existe | Master Prompt Anexo B | **C** |
| F-03 | Índice documental único de gobernanza V4 | Ninguno de los 5 | **C** |
| F-04 | Regla explícita: **parámetros legacy auth** (`sort_order`, envelopes dual admin) no definen contrato ERP | STANDARDS §10 | **B** |
| F-05 | Seeds RBAC obligatorios (R27): presente en RULES; ausente en resumen .cursorrules | .cursorrules | **B** |
| F-06 | Gate CI/regresión acumulada (R104): en RULES/Master Prompt §4.7; ausente en .cursorrules | .cursorrules | **B** |
| F-07 | Documentación bootstrap_v2 como ámbito SQL/seeds separado de arquitectura Python ERP | Ninguno de los 5 | **C** |
| F-08 | Convención `tables.py` central + `tables_erp/` por módulo: STANDARDS §2.1 lo describe; .cursorrules no | .cursorrules | **B** |

### 5.5 Reglas duplicadas

| ID | Hallazgo | Doc(s) | Clas. |
|----|----------|--------|-------|
| D-01 | Reglas absolutas R01–R08 duplicadas casi literal entre .cursorrules y RULES Cat. A | .cursorrules, RULES | **A** (intencional; riesgo deriva) |
| D-02 | Listados escalables duplicados (.cursorrules sección PERF + RULES R105–R109 + STANDARDS §10) | 3 docs | **A** (intencional) |
| D-03 | Cabecera-detalle / derivadas / workflow / rutas proceso triplicados (.cursorrules, RULES, STANDARDS) | 3 docs | **A** (intencional) |
| D-04 | Matriz transición V3→V4 en Master Prompt duplica contenido de RULES “Reglas eliminadas v3” | Master Prompt, RULES | **A** (complementario) |
| D-05 | Riesgo mantenimiento: duplicación sin mecanismo “single source” automatizado | Ecosistema | **B** |

### 5.6 Referencia ORG + INV

| ID | Hallazgo | Clas. |
|----|----------|-------|
| R-01 | ORG referenciado para scope mixto, maestros Tier A, listados, `org_deps.py` | **A** |
| R-02 | INV referenciado para transaccional, company scope, workflow, derivadas, RC1.1 | **A** |
| R-03 | Master Prompt Fase 1.1/1.2 desglosa archivos concretos ORG/INV — usable por agentes | **A** |
| R-04 | Anexo C Master Prompt checklist INV Fase 0 mapeado a reglas R82–R104 | **A** |
| R-05 | STANDARDS §10.7 perfiles Tier A/B/C con recursos ORG/INV nombrados | **A** |
| R-06 | Nota PUR legacy (`order` vs `sort_dir`): correctamente acotada; no contamina estándar | **A** |

### 5.7 IAM — elementos que NO deben migrar a oficiales

| ID | Elemento IAM V2 | Clas. |
|----|-----------------|-------|
| I-01 | Tres entidades sesión + migración V031 | **D** |
| I-02 | Feature flag `IAM_SESSION_MANAGEMENT_V2_ENABLED` | **D** |
| I-03 | Servicios session_* en `modules/auth/application/services/` | **D** |
| I-04 | Queries `session/*_queries_core.py` | **D** |
| I-05 | Contrato API sessions admin / self-revoke V2 | **D** |
| I-06 | `sort_order` en endpoints auth | **D** |
| I-07 | Envelope dual `sessions`/`items` en admin sessions | **D** |
| I-08 | Redis bridge sesión V2 | **D** |
| I-09 | Session audit emitter específico IAM | **D** |
| I-10 | Tests `test_iam_sessions_v2_*` como norma ERP | **D** |
| I-11 | Throttle actividad negocio en deps auth | **D** |
| I-12 | Token family replay / `ReplayDetectionResult` | **D** |
| I-13 | Specs `IAM-SESSION-MANAGEMENT-V2-*.md` | **D** |
| I-14 | Impersonation trace diag (`impersonation_trace_diag.py`) | **D** |

---

## 6. Riesgos

### 6.1 Riesgos altos (ecosistema, fuera de los cinco oficiales)

| Riesgo | Impacto | Mitigación recomendada |
|--------|---------|------------------------|
| `docs/prompts/RULES_CURSOR_BACKEND.md` con `alwaysApply: true` sigue en **v3** (repositories, PROMPT_MODULO_MAESTRO_v3, fallback 422) | Agentes Cursor pueden contradecir V4 aunque `.cursorrules` sea correcto | Converger o deprecar RULES_CURSOR; no forma parte de los 5 oficiales pero compite con ellos |
| `reglas.md` duplicado v3 sin converger | Misma deriva para desarrolladores humanos | Deprecar o redirigir a RULES V4 |
| Prioridad §3.4 incorrecta en STANDARDS | Implementadores nuevos podrían documentar orden erróneo (impacto bajo en runtime: código ya es canónico) | Corrección B en STANDARDS + .cursorrules |

### 6.2 Riesgos medios

| Riesgo | Impacto |
|--------|---------|
| Duplicación triplicada de reglas críticas sin SSOT | Deriva silenciosa entre .cursorrules, RULES y STANDARDS en futuras revisiones |
| Platform Administration sin prompt V4 dedicado | Refactors tenant/superadmin sin proceso equivalente al Master Prompt ERP |
| Ausencia de índice README arquitectura | Onboarding lento; confusión sobre cuál documento leer primero |

### 6.3 Riesgos bajos

| Riesgo | Impacto |
|--------|---------|
| Meta-textos “reemplazo” obsoletos | Confusión semántica, no funcional |
| Dashboard BFF pendiente (§21) | Deuda ya declarada |
| Confundir contrato listados auth (`sort_order`) con ERP (`sort_dir`) | Errores de integración FE en pantallas IAM, no en módulos ERP |

---

## 7. Recomendaciones

### 7.1 Prioridad inmediata (ciclo B — actualización menor)

1. **Corregir STANDARDS §3.4** (y espejo en Master Prompt matriz V3→V4 si aplica) para reflejar orden canónico del código:  
   `JWT impersonation → request.state → ContextVar → current_user.cliente_id`.
2. **Ajustar meta-textos:** RULES no “reemplaza” `.cursorrules` sino que lo **complementa** (detalle vs resumen). Master Prompt: PROMPT es **entrada**, no documento reemplazado.
3. **Añadir nota de frontera** en STANDARDS (§3 o §21) y resumen en .cursorrules: módulos **auth/IAM/platform** no siguen el checklist ERP completo; Session V2 vive en docs `IAM-*`.
4. **Añadir nota** en STANDARDS §10: contrato listados ERP usa `sort_dir`; excepciones legacy solo en auth/admin documentadas aparte.
5. **Completar .cursorrules** con bullets faltantes de bajo costo: R27 seeds RBAC, R104 gate RC, §21 Platform caso especial (1 párrafo).

### 7.2 Prioridad planificada (ciclo C — actualización mayor, no bloqueante ERP)

1. Crear **`PROMPT_PLATFORM_V4.md`** (Anexo B ya lo exige).
2. Crear **`app/docs/arquitectura/README.md`** como índice de gobernanza.
3. Documentar relación **bootstrap_v2 vs arquitectura Python** (seeds/SQL ≠ capas ERP).
4. Cerrar o actualizar deuda **Dashboard BFF** en §21 cuando exista implementación.

### 7.3 Acciones explícitamente NO recomendadas

- Incorporar modelo Session V2, tablas, servicios o contratos IAM a los cinco documentos oficiales.
- Reemplazar referencia ORG/INV por auth o por módulos legacy (PUR sin refactorizar).
- Unificar `sort_order` (auth) con `sort_dir` (ERP) en el estándar global — mantener frontera.
- Reescribir Master Prompt Fases 0–4: el proceso sigue siendo válido.

### 7.4 Gobernanza perimetral (fuera del entregable oficial pero crítica)

- Converger **`RULES_CURSOR_BACKEND.md`** y **`reglas.md`** a V4 o marcarlos DEPRECATED con redirección a `ERP_BACKEND_RULES_V4.md`.
- Verificar en Cursor que **`alwaysApply`** no active reglas v3 por encima de `.cursorrules` V4.

---

## 8. Clasificación consolidada A / B / C / D

| Clasificación | Total | Criterio aplicado |
|---------------|-------|-------------------|
| **A — Vigente** | 38 | Correcto hoy; referencia ORG/INV válida; usable sin cambio |
| **B — Actualización menor** | 11 | Corrección puntual, nota de frontera, meta-texto, completar resumen |
| **C — Actualización mayor** | 4 | Nuevo artefacto o sección estructural (Platform prompt, README, bootstrap note, BFF) |
| **D — Exclusivo IAM** | 14 | Session Management V2 y contratos auth; permanecer en docs IAM |

---

## 9. Dictamen final

### ¿Los documentos oficiales siguen siendo válidos como estándar para futuros módulos ERP?

**Sí.** El núcleo V4 está implementado, referenciado y coherente entre los cinco documentos para arquitectura modular ERP, multi-tenant, multiempresa, RBAC, listados, transaccional y proceso de refactorización. IAM Session Management V2 **no invalida** ni **no debe absorber** este estándar.

### ¿Procede iniciar la actualización de los documentos oficiales?

**Sí, en modalidad de actualización menor (B)**, no como reescritura V5.

| Decisión | Veredicto |
|----------|-----------|
| Usar los 5 documentos para iniciar refactor PUR, CRM, FIN, etc. | **APROBADO** — con conciencia de corregir H-01 y gobernanza perimetral v3 |
| Incorporar Session Management V2 a oficiales | **RECHAZADO** |
| Mantener ORG + INV como referencia de código | **CONFIRMADO** |
| Ciclo de actualización mayor (C) antes de cualquier módulo | **NO REQUERIDO** |
| Ciclo B en paralelo al primer módulo post-auditoría | **RECOMENDADO** |

### Estado de certificación documental

| Criterio (certificación tipo Frontend) | Resultado |
|----------------------------------------|-----------|
| Coherencia entre documentos oficiales | **PASS con 2 excepciones menores (H-01, H-02)** |
| Sin contaminación IAM en estándar ERP | **PASS** |
| Referencia ORG/INV vigente | **PASS** |
| Jerarquía clara | **PASS con gap de índice (C)** |
| Listo para gobernar desarrollo futuro | **PASS condicionado** a convergencia perimetral v3 |

**Certificación:** Los Backend Master Documents V4 **permanecen certificados como estándar operativo** para módulos ERP, sujetos a un **patch documental B** (estimado: 1 sesión de edición) antes o en paralelo al siguiente módulo. No se requiere congelar desarrollo ERP esperando Session V2 ni una revisión mayor V5.

---

## 10. Anexo — documentos relacionados (no auditados como oficiales)

| Documento | Relación con los cinco oficiales |
|-----------|----------------------------------|
| `ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md` | Fuente origen; prioridad `cliente_id` alineada con código, no con STANDARDS §3.4 |
| `ERP_BACKEND_V4_ADOPTION_PLAN.md` | Plan histórico convergencia; P0 largamente avanzado en `.cursorrules`/PROMPT |
| `docs/arquitectura/IAM-SESSION-MANAGEMENT-V2-*.md` | Dominio IAM; frontera explícita |
| `docs/prompts/RULES_CURSOR_BACKEND.md` | **Conflicto v3 activo** — riesgo perimetral |
| `reglas.md` | **Conflicto v3** — riesgo perimetral |

---

*Auditoría READ ONLY — Backend Master Documents V2 — CAXIS ERP — 2026-06-24*
