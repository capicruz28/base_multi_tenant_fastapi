# Checklists — módulo genérico e INV — Baseline V1

---

## 1. Checklist obligatorio — cualquier nuevo módulo Motor

Usar antes de declarar el módulo “integrado al Motor”. Marcar solo con evidencia.

### 1.1 Catálogo y scope

- [ ] `sequence_key`(s) existen en `SequenceCatalog` (sin inventar keys ad hoc)
- [ ] `ScopeType` y dimensiones de context documentadas
- [ ] Policy correcta (`AUTO_*` / `MANUAL_ONLY`) según F15A / `08_CODE_POLICIES`
- [ ] Prefijo / padding defaults entendidos; override solo vía cfg, no hardcode en service

### 1.2 Schemas

- [ ] `*Create`: campo código según policy (AUTO_DEFAULT → Optional)
- [ ] `*Update`: **sin** campo código Motor (BR-IMM)
- [ ] `*Read`: código `str` requerido
- [ ] Normalización UPPER/strip solo en Create (y campos no-código en Update)

### 1.3 Services CREATE

- [ ] Adapter → `Gateway.allocate` (no lógica local de correlativo)
- [ ] Misma `session` / `begin()` que el INSERT
- [ ] Pre-check UNIQUE solo si manual
- [ ] Payload fuerza código resuelto por Motor
- [ ] Dedicated: `get_connection_for_tenant` + session

### 1.4 Services UPDATE

- [ ] Cero ramas `if "codigo" in payload`
- [ ] Cero llamadas Gateway / adapter
- [ ] Cero `get_*_by_codigo` en update

### 1.5 Queries / OpenAPI / Tests

- [ ] `get_*_by_codigo` disponible para CREATE
- [ ] OpenAPI vivo: Update sin código; Create/Read correctos
- [ ] Regenerar snapshot si el módulo cierra contrato público
- [ ] Tests: CREATE auto + manual + dup 409 + cfg missing
- [ ] Tests: UPDATE no pasa código; Motor no invocado (patrón `test_org_br_imm_*`)

### 1.6 Seguridad y sesión

- [ ] `cliente_id` de session deps (no body para authz)
- [ ] `empresa_id` de sesión cuando scope COMPANY
- [ ] Cross-scope → 404

---

## 2. Checklist específico — INV

INV hereda **todo** el §1. Además:

### 2.1 Entidades candidatas (ola típica)

| Entidad / campo | Notas Baseline |
|-----------------|----------------|
| `inv_producto.codigo_sku` | AUTO_DEFAULT; BR-IMM en Update (hoy aún mutable → debe alinearse al migrar) |
| Almacenes / ubicaciones (si en catálogo) | Respetar ScopeType ALMACEN |
| Documentos (`numero_movimiento`, …) | AUTO_REQUIRED; sin override usuario en Create |
| Series fiscales | Store FISCAL; no mezclar con CFG genérico |

### 2.2 Obligatorios INV

- [ ] **No** modificar `app/core/codigo` ni Gateway
- [ ] Reutilizar patrón UoW ORG (allocate + insert misma TX)
- [ ] Producto/maestros: quitar `codigo_sku` (u homólogo Motor) de `*Update` al integrar
- [ ] Documentos: nunca aceptar número en Create estándar
- [ ] Workflow INV (`procesar`, estorno) **no** renumera (BR-D-03 / BR-D-04)
- [ ] Stock / tablas derivadas: escritura solo por proceso — no vía “código”
- [ ] Tests espejo ORG: motor create + IMM update por entidad migrada
- [ ] OpenAPI INV regenerado al cerrar cada entidad
- [ ] Documentar `sequence_key` ↔ campo en matriz del módulo

### 2.3 Prohibido en INV (además de §05)

- [ ] No “generar SKU en el frontend”
- [ ] No UPDATE de `codigo_sku` “mientras no haya movimientos”
- [ ] No segundo motor paralelo en `inv_*_service`
- [ ] No alinear contador en UPDATE

### 2.4 Orden recomendado INV

1. Auditoría entidad ↔ catálogo (matriz)  
2. Schemas Create/Update/Read  
3. Service CREATE + tests  
4. Service UPDATE BR-IMM + tests  
5. OpenAPI / snapshot  
6. Siguiente entidad — **sin** tocar Motor  

---

## 3. Evidencia Golden Reference (ORG)

| Artefacto | Ubicación tipica |
|-----------|------------------|
| Adapter | `app/modules/org/.../org_codigo_generation_service.py` |
| CREATE | `*_service.py` → `resolve_codigo_for_create` |
| UPDATE IMM | schemas sin código + services sin ramas |
| Tests | `test_org_*_motor_integration.py`, `test_org_br_imm_update_immutability.py` |
| OpenAPI | `app/docs/openapi_snapshot.json` |

---

*Reglas y prohibiciones: [`05_RULES_AND_PROHIBITIONS.md`](05_RULES_AND_PROHIBITIONS.md)*
