# Compatibilidad hacia atrás — Inmutabilidad del código

**Fecha:** 2026-07-13  
**Audiencia:** Arquitectura, Backend, Frontend, QA

---

## 1. Definición de “breaking”

Un cambio es **breaking** si un cliente que enviaba un payload **válido hoy** pasa a recibir error o a comportarse distinto de forma observable.

| Escenario actual | Post BR-IMM | ¿Breaking? |
|------------------|-------------|------------|
| POST Create sin código | 201 + código auto | No |
| POST Create con código manual | 201 | No |
| GET / list con campo código | Sin cambio | No |
| PUT Update **sin** campo código | 200 (resto de campos) | No |
| PUT Update con código **igual** al persistido | Hoy 200; mañana depende política | Condicional |
| PUT Update con código **distinto** | Hoy 200 si único; mañana **rechazo** | **Sí** |
| OpenAPI: Update schema deja de listar `codigo` | Codegen FE rompe tipos | **Sí (contrato)** |

---

## 2. Clientes conocidos / supuestos

| Cliente | Uso UPDATE código | Riesgo |
|---------|-------------------|--------|
| Frontend React ORG (AS-IS) | Formularios edición suelen incluir código | **Alto** si envían PATCH/PUT completo |
| Frontend post contrato Ola 1 Create | Create aligned; Update aún “editable” en docs | Medio — docs a corregir **antes** de FE Update |
| Scripts implantación / Postman | Pueden “corregir” códigos vía PUT | Medio |
| Integraciones externas | Poco probable en greenfield | Bajo |
| Motor / Gateway callers | No UPDATE | Nulo |

---

## 3. Estrategias de compatibilidad (ordenadas)

### Estrategia A — Hard cut (recomendada tras breve aviso)

1. Quitar campos del schema Update.
2. Con `extra=ignore` (default Pydantic v2): si FE envía `codigo`, **se ignora** → código **no cambia** (silent strip).
3. Con `extra=forbid`: 422 por campo extra.

**Nota CAXIS:** BaseModel suele **ignorar** extras → quitar el campo = **strip silencioso** salvo model_config forbid.

| Pros | Contras |
|------|---------|
| FE que reenvía form completo no rompe con error | Bug silencioso: usuario cree que cambió el código |
| Rolling deploy seguro | UX debe marcar campo disabled |

**Recomendación:** Estrategia A + UI disabled + toast si detecta envío (opcional log warning).

### Estrategia B — Strict reject

Service: si `"codigo" in payload` → `ValidationError` 422 `CODE_IMMUTABLE`.

| Pros | Contras |
|------|---------|
| Explícito; educa integraciones | Rompe FE que serializa form completo |

### Estrategia C — Dual phase

| Fase | Comportamiento |
|------|----------------|
| C1 (1–2 sprints) | Strip + log `CODE_IMMUTABLE_STRIPPED` |
| C2 | 422 si presente y distinto; o schema sin campo + FE alineado |

**Recomendación oficial de esta auditoría:** **C → A** (fase dual corta, luego schema limpio).

---

## 4. Compatibilidad con implementaciones actuales ORG

| Implementación | Compatible con BR-IMM |
|----------------|----------------------|
| Ola 1 CREATE motor | Sí — sin cambio |
| Bootstrap EMP001 | Sí — código nace en insert bootstrap; no UPDATE |
| Align en CREATE manual | Sí — sigue CREATE |
| Update servicio con rama UNIQUE código | **Incompatible** — debe eliminarse |
| Contrato FE “UPDATE editable” | **Incompatible** — doc a corregir |

---

## 5. Datos históricos

| Pregunta | Respuesta |
|----------|-----------|
| ¿Hay que reescribir códigos existentes? | **No** |
| ¿Códigos ya cambiados por UPDATE en el pasado? | Quedan como están; no hay migración |
| ¿Alinear contadores por UPDATEs previos? | Fuera de alcance; align admin solo si drift detectado |

---

## 6. Semántica HTTP recomendada

| Caso | Status | `internal_code` | Mensaje sugerido |
|------|--------|-----------------|------------------|
| Código en Update (strict) | 422 | `CODE_IMMUTABLE` | `El código no puede modificarse después de la creación.` |
| Código distinto intentado | 422 | `CODE_IMMUTABLE` | Idem |
| Código omitido | 200 | — | Actualización resto de campos |

**No usar 409** para “no permitido editar”: 409 se reserva a conflictos de estado/duplicados. 422 expresa violación de regla de negocio de contrato.

---

## 7. Versionado API

| Opción | Veredicto |
|--------|-----------|
| `/v2` solo por este cambio | **No** — overkill; mismo recurso |
| Header deprecación | Opcional si hay integradores externos |
| Changelog + contrato FE | **Obligatorio** |

---

## 8. Matriz de aceptación QA compatibilidad

| ID | Caso | Resultado esperado post-impl |
|----|------|------------------------------|
| BC-01 | PUT sin código | 200 |
| BC-02 | PUT solo `nombre` | 200; código intacto |
| BC-03 | PUT con código igual (fase strip) | 200; código intacto; opcional warning log |
| BC-04 | PUT con código distinto (fase strict) | 422 CODE_IMMUTABLE |
| BC-05 | POST Create manual | 201 invariante |
| BC-06 | OpenAPI Update sin propiedad código | Spec actualizada |

---

*OpenAPI / FE: [`05_OPENAPI_CONTRACT_IMPACT.md`](05_OPENAPI_CONTRACT_IMPACT.md)*
