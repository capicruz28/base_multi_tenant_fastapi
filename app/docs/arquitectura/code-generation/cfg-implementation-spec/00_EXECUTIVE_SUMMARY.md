# CFG Backend MVP — Especificación consolidada oficial (v1.0)

**Versión:** 1.0  
**Fecha:** 2026-07-17  
**Estado:** **ESPECIFICACIÓN OFICIAL DEFINITIVA** — única referencia obligatoria de implementación  
**Alcance:** MVP Backend del módulo ERP transversal `cfg` (Administrador del Motor de Códigos)

---

## 1. Propósito de este paquete

Este paquete **reemplaza** la lectura obligatoria de:

- `cfg-admin-audit/`
- `cfg-platform-architecture/`
- `cfg-functional-design/`
- `cfg-backend-mvp-design/`
- `cfg-backend-final-review/`

Esos paquetes conservan valor histórico/auditoría. **Para implementar, solo aplica `cfg-implementation-spec/` v1.0.**

Incorpora de forma vinculante la Architecture Gate: **G-01 … G-06**.

---

## 2. Dictamen de producto/técnico (congelado)

| Decisión | Valor oficial |
|----------|---------------|
| Dominio | Módulo ERP operativo `cfg` (no Platform Administration) |
| Dato | `cfg_codigo_secuencia` (store CFG; fiscal fuera de alcance) |
| Usuario | ADMIN_TENANT / parametrización tenant |
| Conexión | `get_connection_for_tenant` + session UoW (Shared y Dedicated) |
| Motor | Congelado — solo consumo de `CodigoGeneracionGateway.preview` y `SequenceCatalog` read-only |
| ORG / INV | No modificar |
| MVP | Listar, detalle, PATCH formato, soft-delete V4, preview |

---

## 3. Endpoints oficiales MVP (post G-01)

| Método | Ruta | RBAC |
|--------|------|------|
| GET | `/cfg/secuencias` | `cfg.secuencias.consultar` |
| GET | `/cfg/secuencias/{secuencia_id}` | `cfg.secuencias.consultar` |
| PATCH | `/cfg/secuencias/{secuencia_id}` | `cfg.secuencias.actualizar` |
| DELETE | `/cfg/secuencias/{secuencia_id}` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/reactivar` | `cfg.secuencias.actualizar` |
| POST | `/cfg/secuencias/{secuencia_id}/preview` | `cfg.secuencias.consultar` |

**Fuera de MVP:** align, diagnóstico, create admin, validar-manual, series fiscales, Frontend.

---

## 4. Errata Architecture Gate (ya aplicada en esta spec)

| ID | Decisión consolidada |
|----|----------------------|
| **G-01** | Soft-disable = `DELETE` + `POST .../reactivar` (STANDARDS V4) |
| **G-02** | Sin validación de colisión de formato en MVP |
| **G-03** | `numero_inicial` solo `>= 1` |
| **G-04** | Listado: pipeline in-memory (opción A) — ver `02_API_SPEC` |
| **G-05** | Preview permitido con secuencia inactiva (HTTP 200) |
| **G-06** | Persistencia HTTP solo `queries/cfg/`; no extender Repo en MVP |

---

## 5. Índice

| Doc | Contenido |
|-----|-----------|
| `00_EXECUTIVE_SUMMARY.md` | Este documento |
| `01_ARCHITECTURE_SPEC.md` | Módulo, carpetas, deps, integraciones |
| `02_API_SPEC.md` | REST + schemas + OpenAPI contrato |
| `03_BUSINESS_RULES.md` | Reglas de negocio y validaciones |
| `04_IMPLEMENTATION_GUIDE.md` | Orden de implementación |
| `05_TESTING_GUIDE.md` | Pruebas obligatorias |
| `06_FINAL_CHECKLIST.md` | Checklist de certificación / DoD |

---

## 6. Autorización de código

Esta especificación es la guía de implementación. **Escribir código requiere autorización explícita adicional del usuario** (esta etapa documental no autoriza por sí sola la implementación).

---

*v1.0 — sin contradicciones respecto a G-01…G-06. No reabrir discusiones ni añadir funcionalidad.*
