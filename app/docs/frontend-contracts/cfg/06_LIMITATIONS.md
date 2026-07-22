# CFG — Limitaciones del MVP

**Versión:** 1.0  
**Alcance:** solo limitaciones actuales del contrato certificado.

---

## 1. Operaciones no disponibles

El Frontend **no** encontrará (y no debe inventar) en este MVP:

- Crear secuencia por API.
- Eliminación física del registro.
- Endpoints de alineación de contador.
- Endpoints de diagnóstico.
- Validación manual / validar-config dedicados.
- Administración de series fiscales.
- Paths legacy `…/activar` o `…/desactivar` (usar `DELETE` + `POST …/reactivar`).

---

## 2. Campos no editables

No se pueden modificar vía API admin:

- Identidad y scope (`sequence_key`, `scope_type`, empresa/almacén/PV, fingerprint).
- `ultimo_numero` (contador operativo).
- `generation_policy`.
- `es_activo` vía PATCH (solo DELETE / reactivar).

---

## 3. Reglas de producto restringidas

| Limitación | Efecto en UI |
|------------|--------------|
| Secuencia `org_empresa` bloqueada | Sin edición ni soft-delete |
| Sin validación de colisión de formato entre secuencias | El usuario puede configurar formatos similares; no habrá error de colisión |
| Preview es estimación | No garantiza el código que se asignará en producción |
| Preview no consume contador | No “reserva” el número |
| Soft-desactivar | La secuencia sigue existiendo; solo cambia `es_activo` |

---

## 4. Listado

- `limit` solo aplica si se envía `page`.
- Filtro `modulo_codigo` es parte del contrato; el total paginado refleja el resultado ya filtrado.
- `sort_by` fuera de whitelist → 422.

---

## 5. Permisos

Solo existen dos permisos de negocio para este recurso. No hay permisos granulares por campo ni por `sequence_key` en el MVP.

---

## 6. Multi-tenant

- El Frontend opera siempre en el tenant de la sesión.
- Recursos de otro tenant responden **404** (no un listado cruzado).

---

## 7. OpenAPI y contrato

- El contrato MVP v1.0 está **congelado**.
- Cambios de producto Backend están fuera de alcance de este handoff.
