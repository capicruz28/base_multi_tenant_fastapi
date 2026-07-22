# 03 — Auditoría de pruebas (Categoría)

**Alcance:** pruebas nuevas de Fase A + impacto sobre la suite INV preexistente.
**Modo:** auditoría; sin modificar tests.

---

## 1. Pruebas nuevas de Fase A (verdes)

| Archivo | Casos | Resultado |
|---------|-------|-----------|
| `tests/unit/test_inv_codigo_generation_service.py` | 14 | ✅ 14 passed |
| `tests/unit/test_inv_categoria_motor_integration.py` | 7 | ✅ 7 passed |
| `tests/unit/test_inv_categoria_br_imm_update.py` | 3 | ✅ 3 passed |
| **Total** | **24** | ✅ **24 passed** |

### 1.1 Cobertura vs casos del Plan Técnico

| ID Plan | Caso | Cubierto por |
|---------|------|--------------|
| INV-C01 | Create sin código → allocate → código en insert | `test_create_categoria_servicio_auto_generate_without_codigo` |
| INV-C02 | Create manual → accept | `test_create_categoria_servicio_manual_codigo_accepted` |
| INV-C03 | Manual duplicado → 409; allocate no llamado | `test_create_categoria_servicio_duplicate_manual_raises_conflict` |
| INV-C04 | cfg missing → NotFound; no insert | `test_create_categoria_servicio_cfg_missing_propagates` |
| INV-C05 | Un solo `session.begin` | `test_create_categoria_servicio_single_transaction_begin` + `_conflict_rolls_back_via_begin_context` |
| INV-U01 | Update solo nombre → código intacto; `"codigo" not in payload` | `test_update_categoria_servicio_does_not_pass_codigo_or_call_motor` |
| INV-U02 | Schema Update sin campo Motor | `test_categoria_update_schema_excludes_codigo_field` + `_ignores_extra_codigo_in_constructor` |
| INV-U03 | Motor / `get_*_by_codigo` no llamados en Update | `test_update_categoria_servicio_does_not_pass_codigo_or_call_motor` |

**Todos los casos del Plan están cubiertos.** El adapter añade además validación de
`GenerationContext`, propagación de `ValidationError` y prueba anti-acoplamiento
(`test_does_not_reference_entity_services`).

### 1.2 Calidad de los asserts

- Verifican `sequence_key`, argumentos exactos de `resolve_codigo_for_create`, identidad de la
  `session` propagada, y que `create_categoria` recibe `data["codigo"]` y `usuario_creacion_id`.
- BR-IMM: verifican ausencia de `codigo` en payload y que Motor/`get_by_codigo` **no** se llaman.
- **Buen nivel**: son pruebas de comportamiento (no de implementación trivial), espejo directo de
  la suite ORG Cargo.

---

## 2. Impacto sobre la suite INV preexistente (regresión)

### 2.1 Bloqueantes de certificación

| ID | Test | Causa raíz | Sev. |
|----|------|-----------|------|
| **C-01** | `test_inv_audit_usuario.py::test_a10_create_categoria_servicio_persiste_usuario_creacion_id` | El test parchea `ensure_empresa_in_tenant` y `create_categoria`, pero **no** `get_connection_for_tenant` ni el adapter/Gateway. Con el nuevo flujo UoW, se abre una **sesión real** y la consulta a `cfg_codigo_secuencia` falla. | Alta |
| **C-02** | `test_inv_audit_usuario.py::test_a17_create_categoria_servicio_sin_usuario_id_deja_usuario_creacion_none` | Misma causa que C-01. | Alta |

Estos tests validan **la misma entidad candidata** (`create_categoria_servicio`), por lo que su
estado rojo **impide** declarar Categoría como plantilla Golden con suite 100% verde.

Corrección esperada (fuera de esta auditoría): alinear los mocks al patrón UoW — parchear
`get_connection_for_tenant` (context manager de sesión) + `InvCodigoGenerationService.resolve_codigo_for_create`,
exactamente como se hizo en la suite de auditoría ORG tras integrar el Motor.

### 2.2 Fallos NO atribuibles a Fase A (ruido preexistente)

| Test | Causa | Relación con Fase A |
|------|-------|---------------------|
| `test_inv_company_isolation.py::test_list_categorias_uses_session_empresa_only` | Assert no contempla `sort_by`/`sort_dir` en la llamada a `list_categorias` | **Ninguna** — cambio de listados previo, no del Motor |
| `test_list_almacenes/productos/stocks/movimientos/inventarios_fisicos/kardex_*` | Mismo patrón de assert `sort_by`/`sort_dir` | **Ninguna** — otras entidades, fuera de alcance |

Estos fallos existen independientemente de la integración del Motor y corresponden a otras
entidades INV (no Categoría). No forman parte del gate de esta certificación, pero se registran
como deuda de suite.

---

## 3. Gaps de cobertura (mejora futura, no bloqueante)

| Gap | Descripción |
|-----|-------------|
| G-1 | No hay test unitario del **endpoint** POST que verifique el remapeo `ConflictError → 409` a nivel HTTP (solo a nivel service). |
| G-2 | No hay test directo del **dual-path** de `get_categoria_by_codigo`/`create_categoria` con `session` vs sin `session`. |
| G-3 | No hay test que verifique el orden pre-check→allocate cuando `manual_codigo` está presente y la fila NO existe (camino feliz manual con allocate ACCEPT_MANUAL) más allá del assert de `resolve`. |

---

## 4. Veredicto de pruebas

- **Pruebas nuevas de Categoría:** completas, de buena calidad, 100% verdes.
- **Suite específica de Categoría (incluyendo auditoría usuario):** **NO** 100% verde por C-01/C-02.
- **Conclusión:** el gate de test de Golden Reference **no** se cumple hasta reconciliar C-01/C-02.
