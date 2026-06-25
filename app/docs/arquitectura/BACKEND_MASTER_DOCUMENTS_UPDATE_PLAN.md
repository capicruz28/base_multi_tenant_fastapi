# Plan Oficial de Actualización — Backend Master Documents V4

**Versión del plan:** 1.0.0  
**Fecha:** 2026-06-24  
**Estado:** Aprobado para ejecución — **única fuente de verdad** del patch documental  
**Modo actual:** READ ONLY (este documento); la ejecución de etapas modificará solo los cinco oficiales según §6  

**Documentos base (aprobados):**

| Documento | Rol |
|-----------|-----|
| `app/docs/arquitectura/BACKEND_MASTER_DOCUMENTS_V2_AUDIT.md` | Auditoría origen |
| `app/docs/arquitectura/BACKEND_MASTER_DOCUMENTS_V2_REVIEW_FINAL.md` | Revisión final certificada |

---

## 1. Propósito

Definir el **plan oficial de actualización documental** de los cinco documentos maestros Backend V4, equivalente al proceso de certificación/actualización utilizado en Frontend.

Este plan es la **única fuente de verdad** para ejecutar el patch. Cualquier cambio fuera del alcance aquí definido **requiere nueva auditoría** antes de aplicarse.

---

## 2. Confirmaciones de alcance (obligatorias)

### 2.1 Alcance reducido — solo hallazgos B aprobados

El patch incorpora **únicamente** los cuatro hallazgos B certificados en la revisión final:

| ID | Hallazgo | Documento(s) afectado(s) |
|----|----------|--------------------------|
| **H-01** | Corregir orden de prioridad resolución `cliente_id` (alinear con `session_scope.py`) | STANDARDS §3.4; Master Prompt matriz L662 |
| **H-02** | Clarificar relación RULES ↔ `.cursorrules` (complemento, no reemplazo) | RULES encabezado L6 |
| **H-03 / O-04** | Clarificar relación Master Prompt ↔ PROMPT (proceso vs entrada) | Master Prompt encabezado L6 |
| **F-01** | Frontera módulos ERP operativos vs auth/IAM/platform | STANDARDS §21; `.cursorrules` (1 línea) |

**Además (derivado de jerarquía confirmada):** documentar la cadena normativa STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt en STANDARDS §22, RULES «Documentos relacionados», `.cursorrules`, PROMPT — **sin** añadir reglas nuevas.

**Total:** 11 ediciones puntuales (~35–55 líneas). **Cero** hallazgos C. **Cero** hallazgos descartados reintroducidos (F-04, F-05, F-06, F-08, D-05).

### 2.2 Confirmación explícita — NO IAM Session Management V2

Durante la ejecución de **ninguna etapa** se incorporará contenido propio de IAM Session Management V2 ni de dominio auth/sesiones:

| Prohibido incorporar | Ejemplos |
|----------------------|----------|
| Persistencia sesión | `refresh_tokens`, `token_family`, `user_session`, V031 |
| Algoritmos sesión | session rotation, RTR, replay detection |
| Producto / API | Active Sessions, admin sessions, session probe |
| Contratos | `ERP-IAM-SESSIONS-API-CONTRACT-*` |
| Servicios | `session_rotation_service`, `session_redis_bridge`, etc. |
| Parámetros auth legacy | `sort_order`, envelopes dual admin |

**Excepción vigente (no expandir):** STANDARDS §3.6 «Sesión padre → Redis» en impersonación permanece **sin modificación** salvo edición colateral inevitable — no ampliar redacción.

### 2.3 Confirmación — ORG + INV como referencia ERP

El patch **no modifica** las referencias de código ORG + INV. Permanece normativo:

- **ORG:** session scope, `OrgScopePolicy`, maestros, listados escalables, `{codigo}_deps.py`
- **INV:** transaccional, cabecera-detalle, derivadas, workflow, rutas proceso, RC1.1

Ninguna etapa sustituye ORG/INV por auth, IAM o módulos legacy (PUR sin refactorizar).

### 2.4 Fuera de alcance — procesos independientes

**NO forman parte de este plan** (no editar, no referenciar como entregables del patch):

| Exclusión | Motivo |
|-----------|--------|
| `docs/prompts/RULES_CURSOR_BACKEND.md` | Track «Convergencia Gobernanza Cursor Activa» |
| `reglas.md` | Idem |
| Documentación `docs/arquitectura/IAM-*` | Dominio IAM |
| Active Sessions, contratos Auth | Dominio IAM |
| `bootstrap_v2/` | Ámbito SQL/seeds |
| README futuros, `PROMPT_PLATFORM_V4.md` | Backlog auxiliar (hallazgos C pospuestos) |
| Reescritura Fases 0–4 Master Prompt | Permanece A — vigente |
| Duplicar R27, R104, `tables_erp/` en `.cursorrules` | Descartado en revisión final |

---

## 3. Jerarquía documental y orden obligatorio de ejecución

### 3.1 Cadena normativa (mayor → menor autoridad)

```
ERP_BACKEND_STANDARDS_V4.md
         ↓
ERP_BACKEND_RULES_V4.md
         ↓
.cursorrules
         ↓
docs/prompts/PROMPT_BACKEND_MAESTRO.md
         ↓
app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md
```

### 3.2 Regla de ejecución

Las etapas **E1 → E5** deben ejecutarse **en secuencia estricta**. Cada etapa **depende** de la anterior cerrada con criterio de aceptación cumplido.

La etapa **E0** (preparación) precede a E1. La etapa **E6** (verificación y cierre) sigue a E5.

```
E0 Preparación
 → E1 STANDARDS
 → E2 RULES
 → E3 .cursorrules
 → E4 PROMPT_BACKEND_MAESTRO
 → E5 ERP_BACKEND_MASTER_PROMPT_V4
 → E6 Verificación y cierre
```

**Prohibido:** editar documentos de etapa inferior antes de cerrar la etapa superior correspondiente (ej. no tocar `.cursorrules` antes de cerrar E2 RULES).

---

## 4. Inventario de cambios autorizados (especificación)

### 4.1 `ERP_BACKEND_STANDARDS_V4.md` — Etapa E1

| Patch | Ubicación | Acción |
|-------|-----------|--------|
| **S-01** | §3.4 L124–127 | Reordenar ítems 2 y 3: (2) `request.state.cliente_id` → (3) ContextVar tenant |
| **S-02** | §21 | Añadir fila en tabla o párrafo: módulos **auth/IAM** (`modules/auth/`) no siguen checklist ERP operativo completo; documentación en `docs/arquitectura/IAM-*` |
| **S-03** | §22 | Añadir subsección «Jerarquía documental oficial» con los 5 niveles |

**Texto canónico §3.4 (post-patch):**

```
1. JWT `cliente_id` si `is_impersonation` (tenant impersonado)
2. `request.state.cliente_id` (si el middleware lo poblara explícitamente)
3. ContextVar tenant (`TenantMiddleware` → `get_current_client_id()`)
4. `current_user.cliente_id` (legacy — prohibido en presentation…)
```

**Evidencia código:** `app/core/tenant/session_scope.py` docstring L7–11.

### 4.2 `ERP_BACKEND_RULES_V4.md` — Etapa E2

| Patch | Ubicación | Acción |
|-------|-----------|--------|
| **R-01** | Encabezado L6 | «reemplazo definitivo de `.cursorrules`» → «complemento ejecutable de `.cursorrules` (detalle normativo vs resumen operativo)» |
| **R-02** | § Documentos relacionados | Añadir filas + bloque jerarquía: STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt |

### 4.3 `.cursorrules` — Etapa E3

| Patch | Ubicación | Acción |
|-------|-----------|--------|
| **C-01** | Bloque «Documentación canónica» L13–17 | Reordenar y numerar según jerarquía normativa |
| **C-02** | Tras referencia ORG+INV L19 | Una línea: módulos auth/IAM/platform → STANDARDS §21; no aplicar checklist ERP completo |

### 4.4 `docs/prompts/PROMPT_BACKEND_MAESTRO.md` — Etapa E4

| Patch | Ubicación | Acción |
|-------|-----------|--------|
| **P-01** | § Documentación de soporte V4 L22–28 | Reordenar tabla: STANDARDS → RULES → `.cursorrules` → Master Prompt → Alignment Audit |
| **P-02** | Tras § Documentación de soporte | Nota: punto de entrada operativo; norma técnica en STANDARDS |

### 4.5 `ERP_BACKEND_MASTER_PROMPT_V4.md` — Etapa E5

| Patch | Ubicación | Acción |
|-------|-----------|--------|
| **M-01** | Encabezado L6 | «reemplazo completo de PROMPT_BACKEND_MAESTRO v3» → «proceso canónico de refactorización por módulo; PROMPT_BACKEND_MAESTRO es punto de entrada operativo» |
| **M-02** | Matriz V3→V4, fila «Resolución impersonación» L662 | Orden: `JWT impersonation → request.state → ContextVar → user legacy` |

---

## 5. Política de versionado (aplicar en ejecución, no en este plan)

| Campo | Regla |
|-------|-------|
| **Versión mayor** (`4.0`) | **NO cambiar** |
| **Fecha base** (`2026-06-03`) | **NO cambiar** |
| **Línea Revisión** | **SÍ actualizar** al cerrar E6 con texto: `2026-06-XX — patch gobernanza documental post auditoría V2 (H-01, H-02, H-03, F-01, jerarquía)` |
| **Renombrar archivos** | **Prohibido** |
| **Crear documentos nuevos** | **Prohibido** (excepto evidencia de cierre opcional en §8) |

---

## 6. Etapas de ejecución

### Etapa E0 — Preparación

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Asegurar baseline limpio y alcance acotado antes del primer edit |
| **Documentos afectados** | Ninguno (solo lectura) |
| **Cambios permitidos** | Ninguno en oficiales |
| **Cambios prohibidos** | Cualquier edit en los cinco oficiales |
| **Dependencias** | Auditoría y revisión final aprobadas |
| **Criterio de aceptación** | (1) Working tree identificado. (2) Diff baseline de los 5 archivos capturado o `git status` limpio de edits previos en esos paths. (3) Checklist §2 leído y confirmado por ejecutor |

**Checklist E0:**

- [ ] Leer este plan completo
- [ ] Confirmar que no se incluyen hallazgos C, F-04, F-05, F-06, F-08, D-05
- [ ] Confirmar exclusión IAM §2.2
- [ ] Abrir `session_scope.py` como evidencia para S-01 / M-02

---

### Etapa E1 — STANDARDS (norma técnica)

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Corregir §3.4; ampliar §21 frontera auth/IAM; registrar jerarquía en §22 |
| **Documento afectado** | `app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md` |
| **Patches autorizados** | S-01, S-02, S-03 |
| **Cambios permitidos** | Solo §3.4, §21, §22; línea Revisión al final si se adelanta (preferible en E6) |
| **Cambios prohibidos** | Cualquier otra sección; IAM V2; nuevas reglas R*; alterar referencias ORG/INV; expandir §3.6 Redis |
| **Dependencias** | E0 cerrada |
| **Criterio de aceptación** | (1) §3.4 orden = código `session_scope.py`. (2) §21 menciona auth/IAM sin contratos auth. (3) §22 incluye jerarquía 5 niveles. (4) Cero menciones a refresh_tokens, token_family, session_rotation, Active Sessions |

---

### Etapa E2 — RULES (reglas ejecutables)

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Alinear encabezado con jerarquía; documentar cadena normativa en «Documentos relacionados» |
| **Documento afectado** | `app/docs/arquitectura/ERP_BACKEND_RULES_V4.md` |
| **Patches autorizados** | R-01, R-02 |
| **Cambios permitidos** | Encabezado L6; tabla § Documentos relacionados |
| **Cambios prohibidos** | Modificar R01–R112; añadir reglas IAM; cambiar numeración; alterar mapeo excepciones |
| **Dependencias** | E1 cerrada (jerarquía definida en STANDARDS §22) |
| **Criterio de aceptación** | (1) L6 dice «complemento» no «reemplazo». (2) Jerarquía en documentos relacionados coincide con §3.1. (3) Referencia a STANDARDS §22 jerarquía si aplica |

---

### Etapa E3 — `.cursorrules` (resumen Cursor)

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Ordenar punteros canónicos; añadir línea frontera auth/IAM/platform |
| **Documento afectado** | `.cursorrules` |
| **Patches autorizados** | C-01, C-02 |
| **Cambios permitidos** | Bloque documentación canónica; una línea bajo referencia ORG+INV |
| **Cambios prohibidos** | Duplicar RULES (R27, R104); añadir reglas IAM; expandir listados/tablas; cambiar reglas críticas existentes salvo orden de punteros |
| **Dependencias** | E2 cerrada |
| **Criterio de aceptación** | (1) Orden punteros = jerarquía §3.1. (2) Línea §21 presente. (3) Conteo líneas delta ≤ ~8. (4) ORG+INV referencia intacta |

---

### Etapa E4 — PROMPT_BACKEND_MAESTRO (entrada operativa)

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Reordenar tabla soporte; declarar rol de punto de entrada |
| **Documento afectado** | `docs/prompts/PROMPT_BACKEND_MAESTRO.md` |
| **Patches autorizados** | P-01, P-02 |
| **Cambios permitidos** | § Documentación de soporte V4; nota entrada operativa |
| **Cambios prohibidos** | Alterar instrucción de inicio Fase 0; añadir IAM; duplicar contenido Master Prompt |
| **Dependencias** | E3 cerrada |
| **Criterio de aceptación** | (1) Tabla ordenada STANDARDS primero. (2) Nota «norma técnica en STANDARDS» presente. (3) Delegación a Master Prompt intacta |

---

### Etapa E5 — MASTER_PROMPT (proceso por módulo)

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Corregir encabezado; alinear matriz V3→V4 con §3.4 STANDARDS |
| **Documento afectado** | `app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md` |
| **Patches autorizados** | M-01, M-02 |
| **Cambios prohibidos** | Reescribir Fases 0–4; Anexo C ORG/INV; añadir IAM; modificar checklists salvo L662 |
| **Dependencias** | E1 cerrada (S-01 es fuente de verdad para M-02); E4 cerrada |
| **Criterio de aceptación** | (1) L6 clarifica PROMPT = entrada. (2) L662 orden = §3.4 post-patch. (3) Fases 0–4 byte-identical salvo L6 y L662 |

---

### Etapa E6 — Verificación y cierre

| Campo | Detalle |
|-------|---------|
| **Objetivo** | Validar coherencia cruzada; actualizar líneas Revisión; certificar patch |
| **Documentos afectados** | Los cinco oficiales (solo línea Revisión si no se hizo antes) |
| **Cambios permitidos** | Línea `Revisión:` en encabezado/pie de cada oficial; opcional: `BACKEND_MASTER_DOCUMENTS_V2_PATCH_EVIDENCE.md` (evidencia, no normativo) |
| **Cambios prohibidos** | Cualquier edit sustantivo adicional no listado en §4 |
| **Dependencias** | E1–E5 cerradas |
| **Criterio de aceptación** | Ver §7 checklist global PASS |

---

## 7. Checklist de verificación global (E6)

Ejecutor debe confirmar **PASS** en todos:

| # | Verificación |
|---|--------------|
| V-01 | §3.4 STANDARDS = docstring `session_scope.py` = fila L662 Master Prompt |
| V-02 | Jerarquía idéntica en STANDARDS §22, RULES, `.cursorrules`, PROMPT |
| V-03 | RULES L6: «complemento», no «reemplazo» |
| V-04 | Master Prompt L6: PROMPT = entrada operativa |
| V-05 | §21 STANDARDS + `.cursorrules`: frontera auth/IAM sin contratos auth |
| V-06 | Cero ocurrencias nuevas: `refresh_tokens`, `token_family`, `session_rotation`, `user_session`, `IAM_SESSION`, Active Sessions |
| V-07 | Referencias ORG + INV sin alteración semántica |
| V-08 | Fases 0–4 Master Prompt sin reescritura |
| V-09 | Solo 5 archivos oficiales modificados en el patch |
| V-10 | Líneas Revisión actualizadas en los cinco oficiales |

---

## 8. Criterios de cierre del plan

El patch documental se considera **cerrado** cuando:

1. Etapas E0–E6 completadas con checklist PASS.
2. Diff total acotado a ~35–55 líneas netas en cinco archivos.
3. Ningún ítem §2.4 (fuera de alcance) modificado.
4. Dictamen registrado: **Backend Master Documents V4 — patch gobernanza 2026-06 aplicado**.

**Artefacto opcional post-cierre:** `BACKEND_MASTER_DOCUMENTS_V2_PATCH_EVIDENCE.md` con diff summary y checklist V-01–V-10 — **no** forma parte de la gobernanza normativa.

---

## 9. Matriz hallazgos → etapa

| Hallazgo | Etapa | Patch(s) |
|----------|-------|----------|
| H-01 | E1, E5 | S-01, M-02 |
| H-02 | E2 | R-01 |
| H-03 / O-04 | E5 | M-01 |
| F-01 | E1, E3 | S-02, C-02 |
| Jerarquía | E1, E2, E3, E4 | S-03, R-02, C-01, P-01, P-02 |

---

## 10. Prohibiciones globales del patch

Durante **todas** las etapas E1–E5:

1. **NO** incorporar IAM Session Management V2 (§2.2).
2. **NO** modificar `RULES_CURSOR_BACKEND.md`, `reglas.md`, docs IAM, bootstrap_v2.
3. **NO** crear README, PROMPT_PLATFORM, ni documentos auxiliares normativos.
4. **NO** cambiar versión `4.0` ni renombrar archivos.
5. **NO** añadir reglas R113+ ni alterar R01–R112.
6. **NO** reescribir Master Prompt Fases 0–4.
7. **NO** sustituir referencia ORG/INV.
8. **NO** expandir `.cursorrules` a copia de RULES.
9. **NO** documentar contratos auth (`sort_order`, envelopes admin, etc.).
10. **NO** aplicar cambios fuera de §4 aunque parezcan «mejoras obvias».

---

## 11. Resumen ejecutivo para ejecutores

| Aspecto | Decisión |
|---------|----------|
| **Qué se actualiza** | 5 documentos oficiales, 11 patches, 4 hallazgos B |
| **Orden** | STANDARDS → RULES → `.cursorrules` → PROMPT → Master Prompt |
| **Qué NO se toca** | IAM, Cursor v3 legacy, bootstrap, README, Platform prompt |
| **Referencia ERP** | ORG + INV permanecen |
| **IAM V2** | Explícitamente excluido |
| **Fuente de verdad ejecución** | **Este documento** |

---

## 12. Trazabilidad

| Artefacto | ID |
|-----------|-----|
| Auditoría | `BACKEND_MASTER_DOCUMENTS_V2_AUDIT.md` v1.0.0 |
| Revisión final | `BACKEND_MASTER_DOCUMENTS_V2_REVIEW_FINAL.md` v1.0.0 |
| Plan de actualización | **Este documento** v1.0.0 |

---

*Plan oficial de actualización — Backend Master Documents V4 — CAXIS ERP — 2026-06-24*
