# CFG — Checklist de implementación Frontend

**Versión:** 1.0  
**Uso:** validar punto por punto que el Frontend implementó el módulo correctamente.

Marcar cada ítem solo cuando sea **verificable** en la app.

---

## A. Acceso y RBAC

- [ ] El menú/ruta CFG exige `cfg.secuencias.consultar`.
- [ ] Sin `consultar`, el módulo no es usable.
- [ ] Con solo `consultar`: listado, detalle y preview disponibles.
- [ ] Con solo `consultar`: Guardar, Desactivar y Reactivar **no** visibles (o disabled).
- [ ] Con `actualizar`: mutaciones visibles según estado y lock.
- [ ] Un 403 de API muestra mensaje de permiso, sin crash.

---

## B. Listado

- [ ] `GET /api/v1/cfg/secuencias` (`list_cfg_codigo_secuencias`).
- [ ] Filtros cableados: al menos `es_activo`, `modulo_codigo`, `buscar` (o subset documentado en UI).
- [ ] Modo sin `page` → array; con `page` → envelope paginado.
- [ ] `limit` no se asume efectivo sin `page`.
- [ ] Sort solo con columnas whitelist; inválido manejado (422).
- [ ] Badges/estados para inactiva, `config_locked`, opcional `policy_drift`.
- [ ] Loading state en carga inicial y refetch.

---

## C. Detalle

- [ ] `GET …/{secuencia_id}` (`get_cfg_codigo_secuencia`).
- [ ] 404 → mensaje + vuelta a listado.
- [ ] Campos de contador/política/identidad en solo lectura.
- [ ] Si `config_locked`: formulario no editable + mensaje claro.

---

## D. Edición (PATCH)

- [ ] `PATCH` con `update_cfg_codigo_secuencia`.
- [ ] Solo envía `prefijo` / `separador` / `longitud_numero` / `numero_inicial`.
- [ ] No envía `es_activo` ni `ultimo_numero` ni campos extra.
- [ ] Validación local básica antes del submit.
- [ ] Éxito 200 → toast + UI actualizada.
- [ ] 422 de prefijo/separador/padding/número inicial → mensaje recuperable en campo.
- [ ] Locked → no permite guardar.

---

## E. Desactivar / Reactivar

- [ ] Desactivar = `DELETE` (`desactivar_cfg_codigo_secuencia`), no otro path.
- [ ] Reactivar = `POST …/reactivar` (`reactivar_cfg_codigo_secuencia`).
- [ ] Confirmación antes de desactivar.
- [ ] Idempotencia: repetir acción no muestra error falso.
- [ ] Botones correctos según `es_activo` y lock.
- [ ] Tras éxito: detalle y listado reflejan el nuevo estado.

---

## F. Preview

- [ ] `POST …/preview` (`preview_cfg_codigo_secuencia`) sin body.
- [ ] Muestra `codigo_estimado`.
- [ ] Muestra `disclaimer` siempre.
- [ ] Comunica que no consume contador (`consume_contador === false`).
- [ ] Funciona con secuencia inactiva (200).
- [ ] Si `PREVIEW_NOT_ALLOWED` / `supports_preview=false`: botón oculto o mensaje claro.
- [ ] Preview no dispara invalidación innecesaria del contador.

---

## G. Errores y sesión

- [ ] Mapa de errores de `03_ERROR_HANDLING.md` aplicado.
- [ ] 401 redirige a login / refresh de sesión.
- [ ] Reintento solo en red/5xx, no en 422/403/404.
- [ ] No se envía `cliente_id` en body/query para autorizar.

---

## H. Cache / refresh

- [ ] Tras PATCH / DELETE / reactivar: se invalida o refresca listado y detalle.
- [ ] Tras Preview: no se asume cambio de `ultimo_numero`.
- [ ] Cambio de sesión limpia cache CFG.

---

## I. Fuera de alcance (no implementado)

- [ ] No hay UI de “crear secuencia”.
- [ ] No hay UI de align / diagnóstico / series fiscales.
- [ ] No hay botones activar/desactivar legacy distintos de DELETE/reactivar.
- [ ] No se promete en copy que el preview “reserva” el código.

---

## J. OpenAPI / client

- [ ] Client generado o tipado contra `app/docs/openapi_snapshot.json` (o equivalente publicado).
- [ ] Los 6 operationIds están referenciados correctamente.

| operationId | Usado en UI |
|-------------|:-----------:|
| `list_cfg_codigo_secuencias` | [ ] |
| `get_cfg_codigo_secuencia` | [ ] |
| `update_cfg_codigo_secuencia` | [ ] |
| `desactivar_cfg_codigo_secuencia` | [ ] |
| `reactivar_cfg_codigo_secuencia` | [ ] |
| `preview_cfg_codigo_secuencia` | [ ] |

---

## Criterio de cierre Frontend

El módulo CFG Frontend se considera alineado al contrato MVP v1.0 cuando **todas** las secciones A–J están marcadas y verificadas en ambiente de integración.
