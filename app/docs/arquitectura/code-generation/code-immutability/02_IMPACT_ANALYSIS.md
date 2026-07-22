# Análisis de impacto — Inmutabilidad del código

**Fecha:** 2026-07-13  
**Alcance:** Backend completo relevante al Motor + contrato FE ORG  
**Método:** Inventario AS-IS vs impacto TO-BE BR-IMM

Para cada ítem: **¿Modificar?** · **Por qué** · **Cambio** · **Impacto** · **Riesgo**

Niveles de impacto: **Nulo** | **Bajo** | **Medio** | **Alto**  
Niveles de riesgo: **Bajo** | **Medio** | **Alto**

---

## 1. Servicios CREATE

| Componente | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|------------|-------------|---------|--------|---------|--------|
| `create_empresa_servicio` | **No** (lógica) | Ya resuelve código solo en CREATE vía motor | Ninguno funcional; opcional comentario/docstring BR-IMM | Nulo | Bajo |
| `create_sucursal_servicio` | **No** | Idem | — | Nulo | Bajo |
| `create_departamento_servicio` | **No** | Idem | — | Nulo | Bajo |
| `create_centro_costo_servicio` | **No** | Idem | — | Nulo | Bajo |
| `create_cargo_servicio` | **No** | Idem | — | Nulo | Bajo |
| Futuros CREATE INV | **Plantilla** | Deben nacer con BR-IMM (Update sin código) | No mutar Update | Bajo | Bajo |

**Conclusión CREATE:** sin cambios de comportamiento.

---

## 2. Servicios UPDATE

| Componente | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|------------|-------------|---------|--------|---------|--------|
| `update_empresa_servicio` | **Sí** | Hoy muta `codigo_empresa` si viene en payload + dup check | Eliminar rama `if "codigo_empresa" in payload`; rechazar o strip del campo | **Alto** | Medio |
| `update_sucursal_servicio` | **Sí** | Mutación `codigo` | Idem | **Alto** | Medio |
| `update_departamento_servicio` | **Sí** | Idem | Idem | **Alto** | Medio |
| `update_centro_costo_servicio` | **Sí** | Idem | Idem | **Alto** | Medio |
| `update_cargo_servicio` | **Sí** | Idem | Idem | **Alto** | Medio |
| `update_producto_servicio` (INV) | **Sí (Ola INV)** | Ya permite cambio `codigo_sku` | Al integrar motor: mismo enforcement | Medio (preemptivo) | Medio |
| Updates parámetros ORG | **No** | Ya no permiten `codigo_parametro` en Update | — | Nulo | Bajo |

**Patrón de enforcement recomendado (fase impl):**

1. Preferido: campo **ausente** del schema Update → Pydantic lo ignora / 422 si `extra=forbid`.
2. Defensa en profundidad: si llega clave código → `ValidationError` 422 `CODE_IMMUTABLE` (o 409 `ConflictError` según estándar de estado).

---

## 3. Schemas Update

| Schema | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|--------|-------------|---------|--------|---------|--------|
| `EmpresaUpdate.codigo_empresa` | **Sí** | Campo presente = OpenAPI lo muestra editable | **Quitar** del Update (como `ParametroUpdate`) | **Alto** | Medio (breaking OpenAPI) |
| `SucursalUpdate.codigo` | **Sí** | Idem | Quitar | **Alto** | Medio |
| `DepartamentoUpdate.codigo` | **Sí** | Idem | Quitar | **Alto** | Medio |
| `CentroCostoUpdate.codigo` | **Sí** | Idem | Quitar | **Alto** | Medio |
| `CargoUpdate.codigo` | **Sí** | Idem | Quitar | **Alto** | Medio |
| Mixins `_*WriteMixin` upper en Update | **Revisar** | Validators de `codigo` en mixin Update | Si quitan campo, validator deja de aplicar | Bajo | Bajo |
| `ProductoUpdate.codigo_sku` | **Sí (INV)** | Preparar Ola 1 INV | Quitar al migrar a motor | Medio | Medio |

---

## 4. Schemas Read

| Schema | ¿Modificar? | Cambio | Impacto | Riesgo |
|--------|-------------|--------|---------|--------|
| `*Read.codigo` / `codigo_empresa` | **No** | Sigue `str` obligatorio en response | Nulo | Bajo |

---

## 5. DTOs / presentación

| Artefacto | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|-----------|-------------|---------|--------|---------|--------|
| Endpoints PUT ORG | **No** (ruta) | Misma ruta; body sin código | Response idéntica | Bajo | Bajo |
| Handlers de excepción | **Posible** | Si se elige 422 `CODE_IMMUTABLE` | Mapear `ValidationError` | Bajo | Bajo |
| DTOs internos no publishados | **No** | N/A ORG V4 | — | Nulo | Bajo |

---

## 6. OpenAPI

| Aspecto | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|---------|-------------|---------|--------|---------|--------|
| Spec Update bodies | **Sí (efecto)** | Campos eliminados de Pydantic | Regeneración automática al desplegar | **Alto** FE codegen | Medio |
| operationId / paths | **No** | Rutas estables | — | Nulo | Bajo |
| Create schemas | **No** | Código sigue optional CREATE | — | Nulo | Bajo |

Detalle FE: [`05_OPENAPI_CONTRACT_IMPACT.md`](05_OPENAPI_CONTRACT_IMPACT.md).

---

## 7. Gateway (`CodigoGeneracionGateway`)

| Dimensión | Valor |
|-----------|-------|
| ¿Modificar? | **No** (core) |
| Por qué | Sin `GenerationOperation.UPDATE`; `allocate`/`preview`/`validate_manual`/`align_counter` ya correctos |
| Cambio | Solo documentación / comentarios que mencionen BR-M-30 edición |
| Impacto | Nulo código · Bajo docs |
| Riesgo | Bajo |

---

## 8. OrgCodigoGenerationService

| Dimensión | Valor |
|-----------|-------|
| ¿Modificar? | **No** (firma) |
| Por qué | Solo CREATE / contexto; no usado en UPDATE |
| Cambio | Opcional: assert si alguien añade enum UPDATE; docstring BR-IMM |
| Impacto | Nulo / Bajo |
| Riesgo | Bajo |

---

## 9. SequenceCatalog

| Dimensión | Valor |
|-----------|-------|
| ¿Modificar? | **Documental / metadata** |
| Por qué | Modelo conceptual `editable_before_usage` / `editable_after_usage` (doc 18) queda obsoleto |
| Cambio | Fijar ambos a `false` en docs; **no** requiere código en `sequence_catalog.py` hoy (campos no runtime) |
| Impacto | Bajo |
| Riesgo | Bajo |

---

## 10. Validaciones

| Capa | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|------|-------------|---------|--------|---------|--------|
| Pre-check UNIQUE en UPDATE (código) | **Eliminar** | Obsoleto | Quitar bloques `get_*_by_codigo` en update | Medio | Bajo |
| `normalize_upper` Create | **Conservar** | Sigue aplicando a Create | — | Nulo | Bajo |
| Motor validate_manual | **Solo CREATE** | Ya es el caso | — | Nulo | Bajo |
| Nueva validación immutabilidad | **Sí** | Defensa en profundidad | 422 si código en Update body (si schema aún lo permite transitoriamente) | Medio | Bajo |

---

## 11. Repositorios

| Componente | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|------------|-------------|---------|--------|---------|--------|
| `CfgCodigoSecuenciaRepository` | **No** | Contador no es “código de entidad” | — | Nulo | Bajo |
| Update de filas cfg (admin futuro) | **Fuera** | Admin muta formato, no código maestro emitido | — | Nulo | Bajo |

---

## 12. Queries

| Componente | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|------------|-------------|---------|--------|---------|--------|
| `update_empresa` / `update_cargo` / … | **No obligatorio** | Reciben `data` dict; si service no pasa código, no actualiza | Opcional: strip whitelist sin columna código | Bajo | Bajo |
| `get_*_by_codigo` | **Conservar** | Sigue en CREATE dup-check y listados | — | Nulo | Bajo |
| UPDATE SQL columnas | **No schema BD** | Columna sigue existiendo | **No** alterar V010 | Nulo | Bajo |

---

## 13. Tests

| Suite | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|-------|-------------|---------|--------|---------|--------|
| `test_org_*_motor_integration.py` | **Extender** | Cubren CREATE; agregar UPDATE rechazo código | Casos nuevos | Medio | Bajo |
| Tests Update genéricos ORG | **Revisar** | Si algún test envía código en PUT | Adaptar | Medio | Medio |
| Tests motor core | **No** | Sin UPDATE | — | Nulo | Bajo |

Ver [`06_TESTING_STRATEGY.md`](06_TESTING_STRATEGY.md).

---

## 14. Documentación normativa

| Documento | ¿Modificar? | Cambio | Impacto | Riesgo |
|-----------|-------------|--------|---------|--------|
| `07_BUSINESS_RULES.md` | **Sí** | BR-M-30 → BR-IMM; deprecar BR-M-31 | Alto normativo | Bajo |
| `08_CODE_POLICIES.md` | **Sí** | Edición AUTO_DEFAULT | Medio | Bajo |
| `09_ERP_BEST_PRACTICES.md` | **Sí** | Tabla inmutabilidad | Bajo | Bajo |
| `10_FINAL_RECOMMENDATION.md` | **Sí** | STD-E-02 alinear | Bajo | Bajo |
| `12_GATEWAY_DESIGN.md` | **Sí** | Quitar responsabilidad edición entidad | Bajo | Bajo |
| `catalog/18_…` | **Sí** | editable_* = false | Bajo | Bajo |
| Wave1 FE contract | **Sí** | UPDATE solo lectura | **Alto** FE | Medio |
| `04_FUNCTIONAL_CONTRACT.md` | **Sí** | §2.4 / §4.3 | Medio | Bajo |
| Admin cfg docs | **No crítico** | No gobierna código de entidad | Bajo | Bajo |

---

## 15. Contrato Frontend

| Artefacto | ¿Modificar? | Por qué | Cambio | Impacto | Riesgo |
|-----------|-------------|---------|--------|---------|--------|
| `frontend-contract/00..04` | **Sí** | Hoy documentan código editable en UPDATE | Inmutabilidad; field disabled / omitido PUT | **Alto** | Medio |
| Forms React Update | **Sí (FE)** | UI | Solo lectura | Alto UX | Medio |
| Create FE | **No** | Ya optional | — | Nulo | Bajo |

---

## 16. Compatibilidad hacia atrás

Ver documento dedicado [`03_BACKWARD_COMPATIBILITY.md`](03_BACKWARD_COMPATIBILITY.md).

| Resumen | Valor |
|---------|-------|
| CREATE con/sin código | Compatible |
| GET / list | Compatible |
| PUT **sin** código | Compatible |
| PUT **con** código (mismo valor) | Depende estrategia (strip silencioso vs 422) |
| PUT **con** código distinto | **Breaking** — debe fallar |

---

## 17. Riesgos funcionales

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| RF-01 | FE legacy envía código en PUT → 422 masivo | Alta | Fase dual: strip+log → luego 422; comunicar contrato |
| RF-02 | Usuario corrige typo solo con recreate | Media | Soft-delete + create; UX clara |
| RF-03 | Integraciones batch UPDATE código | Media | Inventario consumidores; ventana migración |
| RF-04 | INV nace con Update mutable “por ahora” | Alta | Gate: plantilla INV incluye BR-IMM |
| RF-05 | Confusión BR-M-30 vs BR-IMM en docs | Media | Supersede explícito en 07 |

---

## 18. Riesgos de negocio

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| RN-01 | Operación pide “cambiar código ya impreso” | Media | Política: anular + crear; no reimpresiones con número viejo |
| RN-02 | Migración legacy con códigos incorrectos | Media | Import tool / BR-M-33 antes de cutover |
| RN-03 | Percepeión de pérdida de flexibilidad vs Odoo-like | Baja | Mensaje: estabilidad ERP SaaS |
| RN-04 | Códigos fiscales / legales (EXTERNAL) confundidos con Motor | Media | Delimitar alcance ADR a SequenceCatalog |

---

## 19. Matriz módulo × acción (resumen ejecutivo técnico)

| Módulo / capa | CREATE | UPDATE código | Motor | Docs |
|---------------|--------|---------------|-------|------|
| ORG 5 maestros | OK | **Cambiar** | No tocar | Actualizar |
| ORG parámetro | N/A Manual | Ya inmutable | — | — |
| INV (pre-ola) | Sin motor aún | **Planificar** | Futuro | Plantilla |
| Core `app/core/codigo` | OK | N/A | **No modificar** | Comentarios |
| Platform / RBAC | N/A | Códigos de permiso ≠ Motor | — | — |

---

## 20. Conclusión de impacto

| Pregunta | Respuesta |
|----------|-----------|
| ¿El Motor core requiere refactor? | **No** |
| ¿ORG requiere cambios? | **Sí** — Update schemas + services (principal) |
| ¿FE requiere cambios? | **Sí** — formularios edición + contrato |
| ¿BD / V010? | **No** |
| ¿Complejidad implementación? | **Baja–media** (localizada, repetible ×5) |
| ¿Riesgo de rollback? | **Bajo** si feature-flag / strip fase 1 |

---

*Compatibilidad: [`03_BACKWARD_COMPATIBILITY.md`](03_BACKWARD_COMPATIBILITY.md) · Estrategia: [`04_IMPLEMENTATION_STRATEGY.md`](04_IMPLEMENTATION_STRATEGY.md)*
