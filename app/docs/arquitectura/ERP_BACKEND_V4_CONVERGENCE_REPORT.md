# Reporte de Convergencia V4 — Sprint 0 Reducido

**Fecha:** 2026-06-03  
**Alcance:** Gobernanza activa únicamente — sin código, sin módulos, sin bootstrap

---

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `.cursorrules` | Actualizado a V4 — alineado con `ERP_BACKEND_RULES_V4.md` |
| `docs/prompts/PROMPT_BACKEND_MAESTRO.md` | Reemplazado por punto de entrada V4 → `ERP_BACKEND_MASTER_PROMPT_V4.md` |

## Archivos no modificados (fuera de flujo activo)

- `reglas.md`
- `docs/prompts/RULES_CURSOR_BACKEND.md`
- `docs/prompts/PROMPT_MODULO_MAESTRO.md`
- `docs/prompts/PROMPT_MAESTRO.md`
- Documentación histórica en `app/docs/modulos/`

---

## Cambios aplicados en `.cursorrules`

| v3 eliminado | v4 aplicado |
|--------------|-------------|
| `schemas → repositories → services → routers` | `schemas → queries → services → routers` |
| Fallback 422 para duplicados | `ConflictError` (409) obligatorio |
| `PROMPT_MODULO_MAESTRO_v3.md` | `ERP_BACKEND_MASTER_PROMPT_V4.md` |
| "Confirma antes de continuar" | Checkpoints por fase (Master Prompt) |
| Referencia genérica a módulos existentes | ORG + INV explícitos |

| v4 añadido |
|------------|
| Bloque ESTÁNDAR ERP V4: `require_erp_session`, scope TENANT/COMPANY/HYBRID, `{codigo}_deps.py` |
| Prohibido `except Exception → 500` |
| `cliente_id` / `empresa_id` desde sesión |
| `DatabaseConnection.DEFAULT` / `ADMIN` — no existe ERP |
| Enlaces a documentación canónica V4 |

---

## Cambios aplicados en `PROMPT_BACKEND_MAESTRO.md`

- Eliminado contenido v3 (383 líneas de fases obsoletas).
- Sustituido por punto de entrada operativo que delega en `ERP_BACKEND_MASTER_PROMPT_V4.md`.
- Referencias cruzadas a RULES, STANDARDS y `.cursorrules`.
- v3 preservado históricamente en `PROMPT_BACKEND_MAESTRO_ANT.md`.

---

## Verificación post-convergencia

Búsqueda en artefactos activos:

| Patrón | `.cursorrules` | `PROMPT_BACKEND_MAESTRO.md` |
|--------|----------------|------------------------------|
| `repositories → services` (orden ERP) | ❌ ausente | ❌ ausente |
| `PROMPT_MODULO_MAESTRO` | ❌ ausente | ❌ ausente (solo nota histórica ANT) |
| Fallback 422 duplicados | ❌ ausente | ❌ ausente |
| Referencia V4 canónica | ✅ presente | ✅ presente |

---

## Declaración oficial

**El backend queda oficialmente en estándar V4** para gobernanza de desarrollo:

- Reglas Cursor: `.cursorrules` → V4
- Prompt operativo módulos: `PROMPT_BACKEND_MAESTRO.md` → V4
- Estándar técnico: `ERP_BACKEND_STANDARDS_V4.md`
- Reglas completas: `ERP_BACKEND_RULES_V4.md`
- Flujo refactorización: `ERP_BACKEND_MASTER_PROMPT_V4.md`

---

## ¿Listo para iniciar PUR Fase 0?

## **SÍ**

**Condición:** usar exclusivamente el estándar V4 (`ERP_BACKEND_MASTER_PROMPT_V4.md` vía `PROMPT_BACKEND_MAESTRO.md`).

**Siguiente paso:** Fase 0 PUR — mapa funcional + contraste BD (`docs/bd/PUR_TABLAS.sql`), sin código, detener post Paso 0.3.

---

*Sprint 0 reducido completado — 2026-06-03*
