# Contratos por entidad — Frontend ↔ Backend

**Referencia única por recurso ORG Ola 1.**  
Cada sección responde los 13 puntos solicitados.

---

## A. org_empresa

### 1. Endpoint CREATE

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Ruta | `/org/empresa` |
| Permiso | `org.empresa.crear` |
| Sesión | ERP TENANT (`require_org_tenant_erp_session`) |
| Content-Type | `application/json` |
| Status éxito | `201 Created` |

### 2. Campo código

Identificador interno de empresa dentro del tenant. Distinto de RUC (identidad legal).

### 3. Nombre exacto del campo

| Operación | Nombre |
|-----------|--------|
| CREATE / UPDATE body | `codigo_empresa` |
| READ response | `codigo_empresa` |

### 4. ¿Opcional en CREATE?

**Sí.** `codigo_empresa: Optional[str] = null` — no es required en schema.

### 5. Cuándo genera automáticamente

| Condición | Acción |
|-----------|--------|
| Campo omitido, `null` o `""` | Motor `allocate("org_empresa")` scope TENANT |
| Post-bootstrap tenant | Primer alta usuario → típicamente **`EMP002`** (EMP001 reservado onboarding) |
| Siguientes altas | Correlativo tenant: EMP003, EMP004, … |

### 6. Cuándo acepta manual

| Condición | Acción |
|-----------|--------|
| Valor no vacío en body | Motor `ACCEPT_MANUAL` (AUTO_DEFAULT) |
| Formato válido según motor | Aceptado |
| No existe otra empresa con mismo código en tenant | Persistido |
| Alineación contador | Motor alinea `ultimo_numero` si manual > high-water |

**Casos típicos manual:** migración, implantación, convivencia EMP001 bootstrap.

### 7. Cuándo devuelve error

| HTTP | Causa | Mensaje típico |
|------|-------|----------------|
| 409 | Código manual duplicado en tenant | `Ya existe una empresa con el código '…' en este tenant.` |
| 409 | RUC duplicado | `Ya existe una empresa con el RUC '…' en este tenant.` |
| 404 | cfg secuencia ausente (anomalía) | `Configuración de secuencia no encontrada.` |
| 400/422 | Formato manual inválido (motor) | Detalle validación motor |
| 422 | Validación Pydantic (falta `razon_social`, `ruc`, etc.) | Errores campo |
| 403 | Sin permiso `org.empresa.crear` | Authorization |

### 8. Código en respuesta

```json
{
  "empresa_id": "uuid",
  "cliente_id": "uuid",
  "codigo_empresa": "EMP002",
  "razon_social": "...",
  "ruc": "...",
  ...
}
```

El código devuelto es el **definitivo** asignado (auto o manual). Siempre `string` no nulo en Read.

### 9. Impacto formularios React

| Elemento | Acción |
|----------|--------|
| Input `codigo_empresa` CREATE | **Quitar required**; ocultar o colapsar en UX estándar |
| Badge informativo | «El código se asignará al guardar» |
| Post-guardado | Mostrar `codigo_empresa` en detalle / toast éxito |
| RUC | **Sin cambio** — sigue obligatorio |
| Selector empresa activa | No aplica en alta empresa (scope tenant) |

### 10. Impacto tablas

| Elemento | Acción |
|----------|--------|
| Columna `codigo_empresa` | **Sin cambio** — sigue visible |
| Orden / sort | **Sin cambio** |
| Filtro `buscar` | **Sin cambio** — busca por código entre otros campos |

### 11. Impacto edición (UPDATE)

| Aspecto | Comportamiento |
|---------|----------------|
| PUT `/org/empresa/{empresa_id}` | **Normativa BR-IMM:** `codigo_empresa` **inmutable**. Objetivo: campo ausente del Update schema |
| Motor en UPDATE | **Nunca** (**BR-IMM-04**) |
| Runtime AS-IS (pre-Fase 2) | Aún puede aceptar mutación — **gap** hasta enforcement |
| UX objetivo | Solo lectura; no enviar en PUT |

> Fuente: `code-generation/07_BUSINESS_RULES.md` §3.4 · `code-immutability/`.

### 12. Compatibilidad Frontend anterior

| Escenario | Compatible |
|-----------|------------|
| FE envía `codigo_empresa` manual | ✅ |
| FE deja de enviar campo | ✅ Nuevo camino recomendado |
| FE espera código en 201 | ✅ |
| Tipos TS con `codigo_empresa: string` en Read | ✅ Sin cambio |

### 13. Casos de prueba funcionales

| ID | Caso | Request | Esperado |
|----|------|---------|----------|
| EMP-01 | Auto sin código | `{ razon_social, ruc }` sin `codigo_empresa` | 201, código EMP00N |
| EMP-02 | Manual válido | `{ codigo_empresa: "EMP999", ... }` | 201, `EMP999` |
| EMP-03 | Duplicado manual | Código ya existente | 409 |
| EMP-04 | RUC duplicado | RUC existente | 409 |
| EMP-05 | String vacío | `codigo_empresa: ""` | 201 auto (equivalente omitir) |
| EMP-06 | Normalización | `codigo_empresa: "emp999"` | 201, `EMP999` |
| EMP-07 | cfg ausente | Tenant sin seed (anomalía) | 404 |
| EMP-08 | Sin permiso | Usuario sin `crear` | 403 |

---

## B. org_sucursal

### 1. Endpoint CREATE

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Ruta | `/org/sucursales` |
| Permiso | `org.sucursal.crear` |
| Sesión | ERP COMPANY (`require_org_company_erp_session`) |
| Status éxito | `201 Created` |

### 2. Campo código

Identificador de sucursal dentro de la empresa activa.

### 3. Nombre exacto del campo

`codigo` (CREATE, UPDATE, READ).

### 4. ¿Opcional en CREATE?

**Sí.** `codigo: Optional[str] = null`.

### 5. Cuándo genera automáticamente

| Condición | Acción |
|-----------|--------|
| Campo omitido / null / "" | `allocate("org_sucursal")` scope EMPRESA |
| Por empresa | SUC001, SUC002, … independiente por empresa |

### 6. Cuándo acepta manual

Valor no vacío, formato motor válido, único en `(cliente_id, empresa_id, codigo)`.

### 7. Cuándo devuelve error

| HTTP | Causa |
|------|-------|
| 409 | Código duplicado en empresa |
| 403 | `empresa_id` body ≠ sesión JWT |
| 404 | cfg secuencia empresa ausente |
| 422 | Falta `empresa_id`, `nombre`, etc. |

### 8. Código en respuesta

`SucursalRead.codigo: string` — ej. `"SUC001"`.

### 9. Impacto formularios React

Quitar required en CREATE; `empresa_id` debe coincidir con empresa activa sesión; mostrar código post-201.

### 10. Impacto tablas

Columna `codigo` sin cambio; visible en listado empresa.

### 11. Impacto edición

**BR-IMM:** `codigo` inmutable post-CREATE; Motor nunca en UPDATE. Runtime AS-IS = gap hasta Fase 2. UX: solo lectura / omitir PUT.

### 12. Compatibilidad Frontend anterior

Compatible enviando manual; compatible omitiendo (nuevo).

### 13. Casos de prueba funcionales

| ID | Caso | Esperado |
|----|------|----------|
| SUC-01 | Auto sin código | 201 SUC00N |
| SUC-02 | Manual SUC999 | 201 SUC999 |
| SUC-03 | Duplicado | 409 |
| SUC-04 | empresa_id mismatch | 403 |
| SUC-05 | Normalización lower→upper | 201 upper |

---

## C. org_departamento

### 1. Endpoint CREATE

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Ruta | `/org/departamentos` |
| Permiso | `org.departamento.crear` |
| Sesión | ERP COMPANY |
| Status éxito | `201 Created` |

### 2. Campo código

Identificador de departamento organizacional en la empresa.

### 3. Nombre exacto del campo

`codigo`.

### 4. ¿Opcional en CREATE?

**Sí.**

### 5. Cuándo genera automáticamente

Omitido/null/"" → `allocate("org_departamento")` → DEP001, DEP002, …

### 6. Cuándo acepta manual

AUTO_DEFAULT: manual válido y único por empresa.

### 7. Cuándo devuelve error

409 duplicado; 403 empresa mismatch; 404 cfg; 422 validación schema.

### 8. Código en respuesta

`DepartamentoRead.codigo: string`.

### 9. Impacto formularios React

Igual patrón sucursal: optional CREATE, empresa_id sesión, badge auto.

### 10. Impacto tablas

Columna `codigo` visible; jerarquía sin cambio.

### 11. Impacto edición

**BR-IMM:** `codigo` inmutable; Motor nunca en UPDATE. Gap runtime hasta Fase 2. UX: solo lectura.

### 12. Compatibilidad Frontend anterior

✅ Compatible dual (manual u omitido).

### 13. Casos de prueba funcionales

| ID | Caso | Esperado |
|----|------|----------|
| DEP-01 | Auto | 201 DEP00N |
| DEP-02 | Manual DEP999 | 201 |
| DEP-03 | Duplicado | 409 |
| DEP-04 | empresa_id mismatch | 403 |

---

## D. org_centro_costo

### 1. Endpoint CREATE

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Ruta | `/org/centros-costo` |
| Permiso | `org.centro_costo.crear` |
| Sesión | ERP COMPANY |
| Status éxito | `201 Created` |

### 2. Campo código

Identificador contable / imputación en la empresa.

### 3. Nombre exacto del campo

`codigo`.

### 4. ¿Opcional en CREATE?

**Sí.**

### 5. Cuándo genera automáticamente

Omitido/null/"" → `allocate("org_centro_costo")` → CC001, CC002, …

### 6. Cuándo acepta manual

AUTO_DEFAULT: manual válido y único por empresa.

### 7. Cuándo devuelve error

409 duplicado; 403 mismatch; 404 cfg; 422 (falta `tipo_centro_costo`, `nombre`, `empresa_id`).

### 8. Código en respuesta

`CentroCostoRead.codigo: string`.

### 9. Impacto formularios React

Optional CREATE; campos contables sin cambio; código post-guardado.

### 10. Impacto tablas

Columna `codigo`; árbol jerárquico sin cambio.

### 11. Impacto edición

**BR-IMM:** `codigo` inmutable; Motor nunca en UPDATE. Gap runtime hasta Fase 2. UX: solo lectura.

### 12. Compatibilidad Frontend anterior

✅ Compatible.

### 13. Casos de prueba funcionales

| ID | Caso | Esperado |
|----|------|----------|
| CC-01 | Auto | 201 CC00N |
| CC-02 | Manual CC999 | 201 |
| CC-03 | Duplicado | 409 |
| CC-04 | Falta tipo_centro_costo | 422 |

---

## E. org_cargo

### 1. Endpoint CREATE

| Atributo | Valor |
|----------|-------|
| Método | `POST` |
| Ruta | `/org/cargos` |
| Permiso | `org.cargo.crear` |
| Sesión | ERP COMPANY |
| Status éxito | `201 Created` |

### 2. Campo código

Identificador de puesto / cargo RRHH en la empresa.

### 3. Nombre exacto del campo

`codigo`.

### 4. ¿Opcional en CREATE?

**Sí.**

### 5. Cuándo genera automáticamente

Omitido/null/"" → `allocate("org_cargo")` → CAR001, CAR002, …

### 6. Cuándo acepta manual

AUTO_DEFAULT: manual válido y único por empresa.

### 7. Cuándo devuelve error

409 duplicado; 403 mismatch; 404 cfg; 422 (falta `nombre`, `moneda_salarial`, `empresa_id`).

### 8. Código en respuesta

`CargoRead.codigo: string`.

### 9. Impacto formularios React

Optional CREATE; `moneda_salarial` sigue required; código post-201.

### 10. Impacto tablas

Columna `codigo` en grilla cargos.

### 11. Impacto edición

**BR-IMM:** `codigo` inmutable; Motor nunca en UPDATE. Gap runtime hasta Fase 2. UX: solo lectura.

### 12. Compatibilidad Frontend anterior

✅ Compatible.

### 13. Casos de prueba funcionales

| ID | Caso | Esperado |
|----|------|----------|
| CAR-01 | Auto | 201 CAR00N |
| CAR-02 | Manual CAR999 | 201 |
| CAR-03 | Duplicado | 409 |
| CAR-04 | Falta moneda_salarial | 422 |

---

## F. Payload CREATE de referencia

### Empresa — auto

```json
{
  "razon_social": "ACME SA",
  "ruc": "20123456789"
}
```

### Sucursal — auto

```json
{
  "empresa_id": "uuid-empresa-sesion",
  "nombre": "Sede Lima"
}
```

### Cargo — auto

```json
{
  "empresa_id": "uuid-empresa-sesion",
  "nombre": "Analista Senior",
  "moneda_salarial": "uuid-moneda"
}
```

### Manual (cualquier entidad company-scoped)

```json
{
  "empresa_id": "uuid-empresa-sesion",
  "codigo": "SUC-LIMA-01",
  "nombre": "..."
}
```

> El motor valida formato; códigos semánticos no estándar pueden ser aceptados si cumplen reglas PAR_PREFIX_NUM / validador maestro.

---

*Errores y flujo: [`03_HTTP_ERRORS_AND_RUNTIME_FLOW.md`](03_HTTP_ERRORS_AND_RUNTIME_FLOW.md)*
