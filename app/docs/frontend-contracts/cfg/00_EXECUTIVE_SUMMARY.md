# CFG — Contrato Frontend (handoff oficial)

**Versión del contrato:** 1.0  
**Fecha:** 2026-07-17  
**Audiencia:** equipo Frontend  
**Estado Backend:** **CERTIFICADO y CERRADO**

---

## 1. Estado del Backend

El MVP Backend del módulo `cfg` (Administrador de secuencias de código) está **certificado**.

A partir de la certificación:

- No se modificará el código Backend de este MVP.
- No se modificará el contrato OpenAPI de este MVP.
- Este paquete es la **única documentación oficial** para integrar el módulo en Frontend.

---

## 2. Versión

| Concepto | Valor |
|----------|-------|
| Contrato API Frontend | **1.0** |
| Base path | `/api/v1/cfg` |
| Recurso | `/secuencias` |
| Snapshot OpenAPI | `app/docs/openapi_snapshot.json` |

---

## 3. Alcance MVP (qué puede hacer el Frontend)

El Frontend puede:

1. Listar secuencias de código del tenant.
2. Ver el detalle de una secuencia.
3. Actualizar configuración de formato (`prefijo`, `separador`, `longitud_numero`, `numero_inicial`).
4. Desactivar (soft) y reactivar una secuencia.
5. Previsualizar el próximo código estimado (sin consumir contador).

El Frontend **no** debe implementar en este MVP: crear secuencias, borrar físico, alinear contadores, diagnóstico, editar política/contador/identidad, ni series fiscales.

---

## 4. Recursos disponibles

| Método | Ruta | operationId | Permiso |
|--------|------|-------------|---------|
| `GET` | `/api/v1/cfg/secuencias` | `list_cfg_codigo_secuencias` | `cfg.secuencias.consultar` |
| `GET` | `/api/v1/cfg/secuencias/{secuencia_id}` | `get_cfg_codigo_secuencia` | `cfg.secuencias.consultar` |
| `PATCH` | `/api/v1/cfg/secuencias/{secuencia_id}` | `update_cfg_codigo_secuencia` | `cfg.secuencias.actualizar` |
| `DELETE` | `/api/v1/cfg/secuencias/{secuencia_id}` | `desactivar_cfg_codigo_secuencia` | `cfg.secuencias.actualizar` |
| `POST` | `/api/v1/cfg/secuencias/{secuencia_id}/reactivar` | `reactivar_cfg_codigo_secuencia` | `cfg.secuencias.actualizar` |
| `POST` | `/api/v1/cfg/secuencias/{secuencia_id}/preview` | `preview_cfg_codigo_secuencia` | `cfg.secuencias.consultar` |

**Total:** 6 operationIds.

---

## 5. OpenAPI utilizada

Fuente canónica de tipos y paths:

- Archivo: `app/docs/openapi_snapshot.json`
- Prefijo de rutas en snapshot: `/api/v1/cfg/secuencias…`

Este paquete explica **cómo consumir** la API. Para campos exactos y schemas, usar OpenAPI; no duplicarlos aquí.

---

## 6. Índice del paquete

| Documento | Uso |
|-----------|-----|
| `00_EXECUTIVE_SUMMARY.md` | Este resumen |
| `01_API_CONTRACT.md` | Endpoints, params, HTTP, operationIds |
| `02_UI_BEHAVIOR.md` | Comportamiento de UI esperado |
| `03_ERROR_HANDLING.md` | Errores y reacción del Frontend |
| `04_RBAC.md` | Permisos y visibilidad de acciones |
| `05_FRONTEND_INTEGRATION_GUIDE.md` | Flujo de consumo y cache |
| `06_LIMITATIONS.md` | Límites del MVP |
| `07_IMPLEMENTATION_CHECKLIST.md` | Checklist verificable Frontend |

---

## 7. Declaración de handoff

> El Backend del módulo `cfg` MVP v1.0 queda **oficialmente cerrado**.  
> El paquete `app/docs/frontend-contracts/cfg/` constituye la **documentación oficial de integración** para el proyecto Frontend.
