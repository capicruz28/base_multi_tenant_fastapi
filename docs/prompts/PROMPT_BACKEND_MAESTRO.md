# CAXIS ERP — Prompt Maestro (operativo)

**Estándar oficial:** Backend V4 — 2026-06-03

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
| [`ERP_BACKEND_MASTER_PROMPT_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_MASTER_PROMPT_V4.md) | Fases 0–4: análisis, auditoría, implementación, verificación |
| [`ERP_BACKEND_RULES_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_RULES_V4.md) | Reglas operativas R01–R81 |
| [`ERP_BACKEND_STANDARDS_V4.md`](../../app/docs/arquitectura/ERP_BACKEND_STANDARDS_V4.md) | Estándar técnico detallado |
| [`ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md`](../../app/docs/arquitectura/ERP_BACKEND_ARCHITECTURE_ALIGNMENT_AUDIT.md) | Auditoría arquitectónica origen |
| [`.cursorrules`](../../.cursorrules) | Reglas Cursor activas (resumen V4) |

---

## Referencias de código obligatorias

| Módulo | Usar para |
|--------|-----------|
| **ORG** | Session scope, `OrgScopePolicy`, `{codigo}_deps.py`, maestros tenant-wide |
| **INV** | `require_erp_session`, transaccionales, cabecera-detalle embebido, tablas derivadas |

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
