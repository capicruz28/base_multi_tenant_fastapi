# Design Review Final — Architecture Gate (MVP Backend `cfg`)

**Etapa:** Revisión arquitectónica crítica previa a implementación  
**Fecha:** 2026-07-17  
**Objeto:** Blueprint `cfg-backend-mvp-design/`  
**Método:** Revisión independiente (no nueva arquitectura)

---

## 1. Dictamen

### **Blueprint aprobado con ajustes obligatorios antes de implementar.**

El blueprint es sólido en lo esencial (módulo ERP `cfg`, UoW Dedicated/Shared, Gateway.preview, Catalog enrich, lock `org_empresa`, Motor frozen). **No** requiere rediseño.

Sin embargo, la gate detectó **inconsistencias y sobreingeniería** que, si se implementan tal cual, generarían deuda inmediata o divergencia con STANDARDS V4 / ORG-INV.

| Resultado | Valor |
|-----------|--------|
| ¿Aprobado para implementar hoy? | **No** — primero aplicar ajustes §2 |
| ¿Rediseño completo? | **No** |
| ¿Cambios cosméticos? | Excluidos de esta review |
| Nº ajustes obligatorios | **6** |
| Nº recomendaciones opcionales | **3** |

---

## 2. Ajustes obligatorios (resumen)

| ID | Tema | Acción |
|----|------|--------|
| **G-01** | Soft-disable vs STANDARDS V4 | Sustituir `POST activar` + `POST desactivar` por `DELETE /{id}` + `POST /{id}/reactivar` |
| **G-02** | Colisión de formato | **Sacar del MVP** (`CFG_FORMAT_COLLISION` → post-MVP) |
| **G-03** | `numero_inicial` | Solo validar `>= 1`; eliminar regla vaga `CFG_NUMERO_INICIAL_CONFLICT` del MVP |
| **G-04** | Listado + `modulo_codigo` + paginación | Pipeline in-memory (cargar set filtrado SQL básico → enrich → filter módulo → sort/page) **o** quitar `modulo_codigo` del MVP |
| **G-05** | Preview + inactiva | Declarar: preview **siempre permitido** si existe fila; no mapear `SEQUENCE_INACTIVE` en admin preview |
| **G-06** | Repo en path HTTP | Path HTTP **solo** `queries/cfg`; no extender Repo en MVP; quitar ambigüedad diagrama/servicio |

Detalle en `04_FINAL_RECOMMENDATIONS.md`. Autorización formal en `05_IMPLEMENTATION_AUTHORIZATION.md`.

---

## 3. Lo que está bien (no tocar)

- Ubicación ERP `cfg` + `require_cfg_tenant_erp_session`
- `get_cfg_session_client_id` impersonación-safe
- `get_connection_for_tenant` en toda I/O
- Preview vía Gateway; sin allocate
- PATCH solo B + `extra='forbid'`
- Lock `org_empresa`
- RBAC consultar/actualizar (sin mantener/diagnóstico en MVP)
- Motor / ORG / INV frozen
- Endpoints fuera de MVP (align, diagnóstico) correctamente excluidos

---

## 4. Índice del paquete

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este dictamen |
| `01_ARCHITECTURE_REVIEW.md` | Módulo, deps, Shared/Dedicated, ORG/INV/V4/Motor |
| `02_API_REVIEW.md` | REST, OpenAPI, schemas, PATCH, preview, activo |
| `03_RISK_REVIEW.md` | Riesgos, mantenimiento, escalabilidad |
| `04_FINAL_RECOMMENDATIONS.md` | Obligatorios vs opcionales |
| `05_IMPLEMENTATION_AUTHORIZATION.md` | Condiciones para autorizar código |

---

*Sin cambios de código. El blueprint base permanece; los ajustes G-01..G-06 son condiciones de la Architecture Gate.*
