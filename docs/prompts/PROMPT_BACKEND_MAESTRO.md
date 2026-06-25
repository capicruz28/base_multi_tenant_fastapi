# CAXIS ERP — Prompt Maestro (operativo)

**Estándar oficial:** Backend V4 — 2026-06-03 (rev. 2026-06-24 patch gobernanza documental post auditoría V2; rev. previa 2026-06-16 post ORG+INV session scope e impersonación consolidados)

---

## Documento canónico de refactorización

Ejecutar **íntegramente**:

→ [`app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md)

Sustituir en ese documento:

- `[MODULO]` → nombre del módulo (ej. Compras)
- `[CODIGO]` → código del módulo (ej. PUR)

---

## Documentación de soporte V4

| Documento | Uso |
|-----------|-----|
| [`ERP_BACKEND_STANDARDS_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md) | Estándar técnico detallado |
| [`ERP_BACKEND_RULES_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_RULES_V4.md) | Reglas operativas R01–R112 |
| [`.cursorrules`](../../.cursorrules) | Resumen operativo Cursor (reglas críticas V4) |
| [`ERP_BACKEND_MASTER_PROMPT_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md) | Fases 0–4: análisis, auditoría, implementación, verificación |
| [`ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`](../../app/docs/arquitectura/ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md) | Auditoría arquitectónica origen |

**Nota:** Este documento es el **punto de entrada operativo** para refactorización de módulos ERP. La **norma técnica** reside en `ERP_BACKEND_STANDARDS_V4.md`; las reglas ejecutables en `ERP_BACKEND_RULES_V4.md`. La ejecución del proceso delega íntegramente en `ERP_BACKEND_MASTER_PROMPT_V4.md` (§ Documento canónico de refactorización).

---

## Referencias de código obligatorias

| Módulo | Usar para |
|--------|-----------|
| **ORG + INV (session scope)** | `get_{codigo}_session_client_id`, `require_session_cliente_id`, `{codigo}_deps.py` — ver `ERP_BACKEND_STANDARDS_V4.md` §3.7, §5.5 |
| **ORG** | `OrgScopePolicy`, gates `require_org_*_erp_session`, maestros tenant-wide, **listados escalables** |
| **INV** | `require_erp_session`, `inv_deps.py`, transaccionales, cabecera-detalle embebido, tablas derivadas, **listados escalables** |
| **INV (post Fase 0)** | Workflow enforcement, write policy derivadas, permisos lifecycle, rutas proceso canónicas, reversión compensatoria, gate RC |
| **ORG + INV (listados)** | Contrato PERF backend: `page`, `limit`, `buscar`, `sort_by`, `sort_dir` — `app/shared/pagination/` |

Normas completas de sesión e impersonación: **no redefinir aquí** — consultar `ERP_BACKEND_STANDARDS_V4.md` y reglas R19–R25, R110–R112 en `ERP_BACKEND_RULES_V4.md`.

---

## Módulo objetivo

**Módulo:** [MODULO]  
**Código:** [CODIGO]

---

## Instrucción de inicio

1. Leer `.cursorrules` y `ERP_BACKEND_RULES_V4.md`.
2. Abrir `ERP_BACKEND_MASTER_PROMPT_V4.md`.
3. Comenzar por **Fase 0 completa** (Pasos 0.1 → 0.2 → 0.3) sin detenerse entre pasos.
4. Detenerse **solo** al final del Paso 0.3 y esperar confirmación antes de Fase 1.

El alcance lo define la **BD real**, no el mapa funcional ideal.

---

## Versión anterior

El contenido v3 fue archivado en `docs/prompts/PROMPT_BACKEND_MAESTRO_ANT.md` (solo referencia histórica).
