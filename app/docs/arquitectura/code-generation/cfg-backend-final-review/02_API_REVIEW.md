# Revisión de API / OpenAPI / schemas

**Paquete:** `cfg-backend-final-review`  
**Fecha:** 2026-07-17

---

## 1. Diseño REST completo

### Endpoints que deben permanecer

| Endpoint | Veredicto |
|----------|-----------|
| GET list | **Necesario** |
| GET detail | **Necesario** |
| PATCH config B | **Necesario** |
| POST preview | **Necesario** |

### Endpoints a sustituir (G-01)

| Blueprint actual | Sustituto V4 | Notas |
|------------------|--------------|-------|
| `POST .../activar` | `POST .../reactivar` | Mismo permiso `actualizar` |
| `POST .../desactivar` | `DELETE .../{id}` | Soft `es_activo=0`; **no** borra fila |

**No** son endpoints “de más” en capacidad; son la **forma incorrecta** de exponer la misma capacidad. Tras G-01 el conteo MVP sigue en **6** operaciones HTTP (list, detail, patch, delete soft, reactivar, preview).

### Endpoints correctamente excluidos

Align, diagnóstico, create, validate-manual, PATCH contador/policy — **no reabrir**.

---

## 2. OpenAPI

| Hallazgo | Severidad | Acción |
|----------|-----------|--------|
| operationIds claros | OK | — |
| Union list/paginated | OK | Tras G-04 documentar semántica de page |
| `IMMUTABLE_FIELD` vs `extra='forbid'` | Baja | O-02: documentar que forbid cubre A/C/D; IMMUTABLE solo defensa interna si aplica |
| `SEQUENCE_INACTIVE` en tabla errores preview | Ambiguo | **G-05** eliminar de contrato admin preview |
| `CFG_FORMAT_COLLISION` en contrato MVP | Sobreingeniería | **G-02** quitar del OpenAPI MVP |
| `CFG_NUMERO_INICIAL_CONFLICT` | Ambiguo | **G-03** quitar |
| Activar/desactivar operationIds | Divergencia V4 | **G-01** renombrar a delete/reactivar |

---

## 3. Schemas

### `CodigoSecuenciaRead`

| Campo | Veredicto |
|-------|-----------|
| Campos B + contador + policy | OK |
| Enrich Catalog | OK (útil FE) |
| `config_locked` / `policy_drift` | OK |
| `scope_fingerprint` | Opcional O-03 — ruido FE; puede quedar (admin técnico) |
| Omitir `cliente_id` | OK |

### `CodigoSecuenciaUpdate`

| Aspecto | Veredicto |
|---------|-----------|
| Solo B; sin `es_activo` | **Correcto** (activo vía soft-delete endpoints) |
| `extra='forbid'` | **Correcto** |
| `numero_inicial` editable | OK con **G-03** (solo `>= 1`) |

### Preview response

| Aspecto | Veredicto |
|---------|-----------|
| `consume_contador: false` | OK (explícito para FE) |
| `disclaimer` desde Gateway | OK |
| `es_activo` en response | Útil — FE puede avisar sin bloquear |

---

## 4. PATCH

| Regla | Veredicto |
|-------|-----------|
| Solo B | OK |
| org_empresa locked | OK |
| Colisión formato | **Sacar MVP (G-02)** |
| Auditoría en update | OK |

---

## 5. Preview

| Regla diseño funcional | Motor AS-IS | Blueprint | Gate |
|------------------------|------------|-----------|------|
| Preview no reserva | Sí | Sí | OK |
| Preview en inactiva permitido | PreviewReader no bloquea activo | Texto ambiguo 409 | **G-05** |
| Scope desde fila | — | Sí | OK |
| `supports_preview=false` | ValidationError `PREVIEW_NOT_ALLOWED` | No listado en errores OpenAPI | Añadir a errores documentados (menor; incluir en G-05 doc) |

---

## 6. Activar / Desactivar → soft-delete V4

**Problema:** inventar vocabulario paralelo al estándar del proyecto.

**Solución obligatoria G-01:**

```text
DELETE /cfg/secuencias/{secuencia_id}     → es_activo=false (lock org_empresa)
POST   /cfg/secuencias/{secuencia_id}/reactivar → es_activo=true
```

Impacto en diseño funcional: misma UX (modal al desactivar); solo cambian verbos HTTP. Actualizar mental model FE a patrón ORG.

RBAC: ambos con `cfg.secuencias.actualizar` (como `reactivar` en ORG).

---

## 7. `numero_inicial`

Motor: el piso solo adelanta el próximo número si `numero_inicial - 1 > ultimo_numero`.

| Regla propuesta blueprint | Problema |
|---------------------------|----------|
| `CFG_NUMERO_INICIAL_CONFLICT` “piso absurdo” | No hay definición operativa |

**G-03:** validar únicamente entero `>= 1` (y techo razonable opcional). No rechazar `numero_inicial <= ultimo_numero` (es no-op funcional, no error).

---

## 8. Colisiones de formato

Bloquear mismo `prefijo+separador+longitud_numero` entre distinct `sequence_key` es:

- Fácil de implementar mal (false positives entre módulos)
- No exigido por el Motor
- Complejidad de producto sin evidencia de incidente

**G-02:** diferir a v1.3 / diagnóstico.

---

## 9. RBAC

| Aspecto | Veredicto |
|---------|-----------|
| consultar vs actualizar | OK |
| preview con consultar | OK |
| No sembrar mantener/diagnosticar en MVP | OK |
| Tras G-01: DELETE/reactivar con actualizar | OK |

Sin cambio de modelo de permisos.
