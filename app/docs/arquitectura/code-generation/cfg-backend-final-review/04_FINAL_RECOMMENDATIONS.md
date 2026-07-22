# Recomendaciones finales (Architecture Gate)

**Paquete:** `cfg-backend-final-review`  
**Fecha:** 2026-07-17

---

## 1. Ajustes obligatorios (deben aplicarse al blueprint antes de implementar)

### G-01 — Soft-disable alineado a STANDARDS V4 / ORG / INV

**Antes:**

- `POST /cfg/secuencias/{id}/activar`
- `POST /cfg/secuencias/{id}/desactivar`

**Después:**

- `DELETE /cfg/secuencias/{id}` → `es_activo = false` (soft; lock `org_empresa`)
- `POST /cfg/secuencias/{id}/reactivar` → `es_activo = true`

Permiso: `cfg.secuencias.actualizar` en ambos.  
PATCH **sigue sin** `es_activo`.  
Actualizar: OpenAPI, services, tests, y nota de alineación en diseño funcional (mismo CU, otros verbos).

---

### G-02 — Diferir colisión de formato

**Quitar del MVP:**

- Validación `CFG_FORMAT_COLLISION`
- Tests U-V07 asociados
- Mención 409 colisión en OpenAPI MVP

**Reubicar:** fase madurez / diagnóstico (v1.3).

---

### G-03 — Simplificar `numero_inicial`

**MVP:**

- Editable en PATCH
- Validar: entero `>= 1` (`CFG_NUMERO_INICIAL_INVALID` si falla)
- **No** emitir `CFG_NUMERO_INICIAL_CONFLICT`

Comportamiento Motor ya ignora piso cuando `<= ultimo_numero` (no-op). No convertir no-op en error.

---

### G-04 — Listado: corregir paginación vs `modulo_codigo`

**Problema:** SQL `page` → enrich → filtro `modulo_codigo` rompe `total` / páginas.

**Decisión obligatoria (elegir una; recomendada A):**

| Opción | Descripción |
|--------|-------------|
| **A (recomendada)** | Query SQL con filtros nativos (`cliente_id`, scope, empresa, activo, key, buscar) **sin** page SQL; enrich; filtro `modulo_codigo`; sort; **paginar en memoria** si `page` presente. Volumen eager+lazy cabe en MVP. |
| **B** | Eliminar query param `modulo_codigo` del MVP (filtrar solo en FE). Paginación SQL estándar. |

Documentar la opción elegida en `02_OPENAPI_DESIGN` / plan de implementación antes de code.

---

### G-05 — Preview sobre secuencia inactiva

**Regla definitiva:**

> Si la fila existe y `supports_preview`, el admin preview **debe responder 200** aunque `es_activo=false`, incluyendo `es_activo` en el response para que FE muestre aviso.

No documentar ni implementar mapeo a `SEQUENCE_INACTIVE` en este endpoint.  
Documentar `PREVIEW_NOT_ALLOWED` (Catalog) como 422 posible.

---

### G-06 — Una sola ruta de persistencia HTTP

**Reglas:**

1. List/get/update/activo **solo** vía `queries/cfg/`.  
2. **No** extender `CfgCodigoSecuenciaRepository` en el MVP del módulo admin.  
3. Onboarding sigue usando Repo como hoy (fuera de alcance HTTP).  
4. Actualizar diagrama: eliminar `SVC → REPO` del path admin.

---

## 2. Recomendaciones opcionales (no bloquean autorización)

| ID | Recomendación | Beneficio |
|----|---------------|-----------|
| **O-01** | Colapsar enricher/validator/context builder como funciones privadas en el service module (o un solo `cfg_secuencia_support.py`) | Menos archivos |
| **O-02** | No exponer `IMMUTABLE_FIELD` en OpenAPI si `extra='forbid'` basta | Menos ruido |
| **O-03** | Mover `scope_fingerprint` a campo “advanced” u omitir en listado (mantener en detail) | UI más limpia |

---

## 3. Explicitamente: sin mejora significativa adicional

Fuera de G-01..G-06 y O-01..O-03, **no** se identificaron otras mejoras arquitectónicas materiales. El resto del blueprint (sesión TENANT, Gateway preview, enrich Catalog, lock org_empresa, Motor frozen, exclusión align) debe **preservarse**.

---

## 4. Matriz endpoints MVP **post-gate**

| Método | Ruta | RBAC |
|--------|------|------|
| GET | `/cfg/secuencias` | consultar |
| GET | `/cfg/secuencias/{secuencia_id}` | consultar |
| PATCH | `/cfg/secuencias/{secuencia_id}` | actualizar |
| DELETE | `/cfg/secuencias/{secuencia_id}` | actualizar |
| POST | `/cfg/secuencias/{secuencia_id}/reactivar` | actualizar |
| POST | `/cfg/secuencias/{secuencia_id}/preview` | consultar |

---

## 5. Cómo aplicar los ajustes (documental)

Antes de autorizar código, el implementador debe tratar G-01..G-06 como **errata vinculante** del blueprint `cfg-backend-mvp-design/`.  

Opcional (no requerido por esta gate): parchear los markdown del blueprint para reflejar la errata.  
**Mínimo requerido:** cumplir G-01..G-06 en la implementación y en OpenAPI al generarlo.

Esta review **no** reescribe el blueprint completo; lo **condiciona**.
