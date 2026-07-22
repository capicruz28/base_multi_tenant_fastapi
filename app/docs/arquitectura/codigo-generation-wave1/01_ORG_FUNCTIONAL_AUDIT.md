# Ola 1 — Auditoría funcional ORG (migración al Motor de Códigos)

**Estado:** Solo auditoría — motor congelado  
**Fecha:** 2026-07-10

---

## 1. Inventario de entidades ORG con campo «código»

### 1.1 Entidades de negocio (motor-eligible)

| Entidad | Tabla | Columna código | Create schema | Update schema | Read schema |
|---------|-------|------------------|---------------|---------------|-------------|
| Empresa | `org_empresa` | `codigo_empresa` | **Obligatorio** | Opcional | Siempre presente |
| Sucursal | `org_sucursal` | `codigo` | **Obligatorio** | Opcional | Siempre presente |
| Centro de costo | `org_centro_costo` | `codigo` | **Obligatorio** | Opcional | Siempre presente |
| Departamento | `org_departamento` | `codigo` | **Obligatorio** | Opcional | Siempre presente |
| Cargo | `org_cargo` | `codigo` | **Obligatorio** | Opcional | Siempre presente |

**Archivos schemas:** `app/modules/org/presentation/schemas.py`  
**Normalización Create/Update:** `normalize_upper` vía mixins `_EmpresaWriteMixin`, `_SucursalWriteMixin`, etc.

### 1.2 Entidades con campo «codigo» fuera del motor

| Entidad / campo | Tipo | Motivo exclusión |
|-----------------|------|------------------|
| `org_parametro_sistema.codigo_parametro` | Clave de configuración | No existe en `SequenceCatalog`; semántica clave-valor, no correlativo |
| `org_parametro_sistema.modulo_codigo` | Identificador de módulo | Catálogo RBAC/módulos, no secuencia ERP |
| `org_empresa.codigo_ciiu` | Referencia SUNAT | Código externo normativo |
| `org_empresa.codigo_postal` | Referencia postal | Dato geográfico |
| `org_sucursal.codigo_postal`, `ubigeo` | Referencia geo | Dato geográfico |
| `org_centro_costo.ruta_jerarquica` | Path derivado | Puede contener segmentos de código padre; no es PK de negocio |

---

## 2. ¿Cuáles solicitan el código al usuario?

| Entidad | Solicitud API | Campo OpenAPI Create |
|---------|---------------|----------------------|
| Empresa | **Sí — obligatorio** | `codigo_empresa: str` (required) |
| Sucursal | **Sí — obligatorio** | `codigo: str` (required) |
| Centro de costo | **Sí — obligatorio** | `codigo: str` (required) |
| Departamento | **Sí — obligatorio** | `codigo: str` (required) |
| Cargo | **Sí — obligatorio** | `codigo: str` (required) |
| Parámetro sistema | **Sí — obligatorio** | `codigo_parametro: str` (required) — **fuera motor** |

**Endpoints POST:**

| Ruta | Servicio |
|------|----------|
| `POST /api/v1/org/empresa` | `create_empresa_servicio` |
| `POST /api/v1/org/sucursales` | `create_sucursal_servicio` |
| `POST /api/v1/org/centros-costo` | `create_centro_costo_servicio` |
| `POST /api/v1/org/departamentos` | `create_departamento_servicio` |
| `POST /api/v1/org/cargos` | `create_cargo_servicio` |
| `POST /api/v1/org/parametros` | `create_parametro_servicio` |

**Conclusión:** el contrato OpenAPI actual **exige** código en body para las 5 entidades motor-eligible. La migración requiere evolución de schemas (ver §9).

---

## 3. ¿Dónde se valida el código?

### 3.1 Capa presentation (schemas)

| Validación | Dónde |
|------------|-------|
| Presencia / tipo | Pydantic `Field(...)` en Create |
| Longitud máxima | `max_length=20` (empresa, maestros company) |
| Normalización | `@field_validator` → `normalize_upper` |

**No hay** validación de formato de prefijo+número en schemas (ej. `SUC001` vs texto libre).

### 3.2 Capa application (services)

Patrón uniforme en los 5 servicios:

| Operación | Validación |
|-----------|------------|
| **CREATE** | `get_*_by_codigo(...)` → si existe → `ConflictError` 409 |
| **UPDATE** | Si payload incluye código → mismo pre-check con `exclude_id` |

**Archivos:**

- `empresa_service.py` — `get_empresa_by_codigo`
- `sucursal_service.py` — `get_sucursal_by_codigo`
- `centro_costo_service.py` — `get_centro_costo_by_codigo`
- `departamento_service.py` — `get_departamento_by_codigo`
- `cargo_service.py` — `get_cargo_by_codigo`
- `parametro_service.py` — `get_parametro_by_clave_natural` (clave compuesta)

### 3.3 Capa infrastructure (BD)

| Restricción | Tabla |
|------------|-------|
| `UQ_org_empresa_cliente (cliente_id, codigo_empresa)` | `org_empresa` |
| `UQ_org_empresa_ruc (cliente_id, ruc)` | `org_empresa` (no es código motor) |
| `UQ_cc_codigo (cliente_id, empresa_id, codigo)` | `org_centro_costo` |
| `UQ_sucursal_codigo (cliente_id, empresa_id, codigo)` | `org_sucursal` |
| `UQ_dpto_codigo (cliente_id, empresa_id, codigo)` | `org_departamento` |
| `UQ_cargo_codigo (cliente_id, empresa_id, codigo)` | `org_cargo` |
| `UQ_parametro (cliente_id, empresa_id, modulo_codigo, codigo_parametro)` | `org_parametro_sistema` |

**Fuente DDL:** `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql`

### 3.4 Motor (AS-IS — no integrado)

| Capacidad | Componente | Estado en ORG |
|-----------|------------|---------------|
| Validación formato maestro | `CodeValidator` vía gateway | **No invocado** |
| Unicidad lógica | Pre-check service + UNIQUE BD | Duplicado con motor en transición |
| Alineación contador | `CounterAlignmentService` | **No invocado** |

---

## 4. Consultas que buscan por código

| Query | Archivo | Uso |
|-------|---------|-----|
| `get_empresa_by_codigo` | `empresa_queries.py` | Pre-check create/update |
| `get_sucursal_by_codigo` | `sucursal_queries.py` | Pre-check create/update |
| `get_centro_costo_by_codigo` | `centro_costo_queries.py` | Pre-check create/update |
| `get_departamento_by_codigo` | `departamento_queries.py` | Pre-check create/update |
| `get_cargo_by_codigo` | `cargo_queries.py` | Pre-check create/update |
| `get_parametro_by_clave_natural` | `parametro_queries.py` | Pre-check create (modulo + codigo) |

### 4.1 Búsqueda en listados (`buscar`)

Filtro ILIKE sobre código + nombre (server-side):

| Listado | Columnas código en `buscar` |
|---------|----------------------------|
| Empresas | `codigo_empresa` |
| Sucursales | `codigo` |
| Centros costo | `codigo` |
| Departamentos | `codigo` |
| Cargos | `codigo` |
| Parámetros | `modulo_codigo`, `codigo_parametro` |

**Impacto migración:** los códigos generados por motor (`SUC001`, `CAR001`, …) siguen siendo buscables sin cambio en queries de listado.

---

## 5. Restricciones UNIQUE relacionadas

| ID | Constraint | Scope unicidad | Campo motor |
|----|------------|----------------|-------------|
| UQ-ORG-01 | `UQ_org_empresa_cliente` | Tenant | `codigo_empresa` |
| UQ-ORG-02 | `UQ_cc_codigo` | Tenant + empresa | `codigo` |
| UQ-ORG-03 | `UQ_sucursal_codigo` | Tenant + empresa | `codigo` |
| UQ-ORG-04 | `UQ_dpto_codigo` | Tenant + empresa | `codigo` |
| UQ-ORG-05 | `UQ_cargo_codigo` | Tenant + empresa | `codigo` |

**Red de seguridad post-migración:** mantener UNIQUE en BD; el motor consume contador en `cfg_codigo_secuencia` dentro de la misma TX que el INSERT.

---

## 6. sequence_key por entidad (SequenceCatalog — congelado)

| Entidad | `sequence_key` | `code_column` | Prefijo default | Padding |
|---------|----------------|---------------|-----------------|---------|
| Empresa | `org_empresa` | `codigo_empresa` | EMP | 3 |
| Sucursal | `org_sucursal` | `codigo` | SUC | 3 |
| Centro costo | `org_centro_costo` | `codigo` | CC | 3 |
| Departamento | `org_departamento` | `codigo` | DEP | 3 |
| Cargo | `org_cargo` | `codigo` | CAR | 3 |

**Fuente:** `app/core/codigo/sequence_catalog.py` líneas 114–118  
**Política:** `CodePolicy.AUTO_DEFAULT` — manual permitido si viene en contexto.

**Seed cfg:** filas precreadas en onboarding por `seed_cfg_tenant` (1× TENANT `org_empresa`) + `seed_cfg_empresa` (56 filas EMPRESA incluyendo las 4 company-scoped ORG).

---

## 7. ScopeType esperado por entidad

| Entidad | ScopeType catálogo | `GenerationContext` requerido |
|---------|-------------------|------------------------------|
| `org_empresa` | **TENANT** | `client_id`; `empresa_id=None` |
| `org_sucursal` | **EMPRESA** | `client_id` + `empresa_id` |
| `org_centro_costo` | **EMPRESA** | `client_id` + `empresa_id` |
| `org_departamento` | **EMPRESA** | `client_id` + `empresa_id` |
| `org_cargo` | **EMPRESA** | `client_id` + `empresa_id` |

**Resolución:** `ScopeResolver.resolve()` + fingerprint en `cfg_codigo_secuencia`.

**Nota TENANT vs EMPRESA en empresa:**

- La secuencia `org_empresa` es **TENANT-scoped** (una fila cfg por cliente).
- Los códigos `EMP002`, `EMP003` de empresas adicionales comparten contador TENANT con `EMP001`.
- El bootstrap cfg EMPRESA (56 filas) es independiente del allocate de código de empresa.

---

## 8. ¿Generación automática antes o durante el INSERT?

**Decisión normativa Ola 1 ORG:**

| Momento | Acción |
|---------|--------|
| **Antes del INSERT** | `CodigoGeneracionGateway.allocate(sequence_key, context, session)` |
| **Durante el INSERT** | Payload ya incluye `codigo` / `codigo_empresa` asignado |
| **Misma transacción** | `allocate` consume contador cfg + INSERT entidad en un solo `session.begin()` |

**Secuencia CREATE (patrón target):**

```
async with session.begin():
  1. [Opcional] si manual_code en payload → allocate con manual (ACCEPT_MANUAL + align)
     si omitido/vacío → allocate AUTO_GENERATE
  2. Inyectar código en payload
  3. INSERT entidad
  4. [Solo org_empresa] EmpresaBootstrapService.insertar_secuencias_codigo (existente)
```

**Prohibido:** generar código **después** del INSERT (race + UNIQUE + contador desincronizado).

**Estado AS-IS:**

| Entidad | TX | Momento código |
|---------|-----|----------------|
| `org_empresa` | UoW (`session.begin`) | Usuario envía antes del INSERT |
| Resto ORG | Auto-commit | Usuario envía antes del INSERT |

---

## 9. Impactos por capa

### 9.1 OpenAPI

| Cambio propuesto | Entidades | Breaking |
|------------------|-----------|----------|
| `codigo` / `codigo_empresa` **Optional** en Create | 5 maestros | **Sí** — de required a optional |
| Response Read **sin cambio** | Todas | No |
| Endpoint preview (futuro) | Por entidad | Aditivo — no breaking |

**Estrategia compatibilidad:** fase 1 acepta manual **y** omisión (AUTO_DEFAULT); fase 2 deprecar envío manual en UI.

### 9.2 Schemas (`schemas.py`)

| Schema | Cambio |
|--------|--------|
| `*Create` | Campo código optional; validator ignora None |
| `*Update` | Sin cambio funcional (manual sigue permitido vía gateway) |
| `*Read` | Sin cambio |

### 9.3 Services

| Cambio | Detalle |
|--------|---------|
| Nuevo helper interno | `_resolve_codigo_create(sequence_key, context, session, manual?)` |
| CREATE | Invocar gateway antes de INSERT; eliminar pre-check redundante si AUTO_GENERATE puro |
| CREATE manual | Mantener pre-check **o** delegar unicidad a UNIQUE + catch 409 |
| UPDATE con código | `gateway.validate_manual` + pre-check existente |
| `create_empresa_servicio` | Insertar allocate **antes** de `create_empresa`, dentro del `begin()` existente |

### 9.4 Queries

| Cambio | Detalle |
|--------|--------|
| Sin cambio estructural | INSERT recibe payload con código ya resuelto |
| UoW company-scoped | Extender patrón dual-path session (como empresa UoW-1) |
| Lookups by codigo | Permanecen para update y búsqueda |

### 9.5 Frontend (solo impacto documentado)

| Área | Impacto |
|------|---------|
| Formularios alta | Eliminar input obligatorio de código; mostrar preview opcional |
| Formularios edición | Mantener edición manual mientras `allow_manual=true` |
| Validación cliente | Dejar de exigir regex local; confiar en 422 motor |
| Listados / buscar | Sin cambio — códigos motor-compatibles |
| Empresa multi-tenant | Formulario alta empresa: quitar `codigo_empresa` manual |
| Importación masiva | Futuro: `GenerationOperation.IMPORT` — fuera Ola 1 ORG inicial |

---

## 10. Orden de migración (menor → mayor riesgo)

| Orden | Entidad | Riesgo | Justificación |
|-------|---------|--------|---------------|
| **1** | `org_cargo` | Bajo | Hoja del árbol ORG; sin FK entrantes críticas en create |
| **2** | `org_departamento` | Bajo | FK opcionales (sucursal, CC); volumen bajo |
| **3** | `org_centro_costo` | Medio | Jerarquía padre/hijo; sucursal referencia CC |
| **4** | `org_sucursal` | Medio-alto | FK opcional a centro_costo; operaciones INV/HCM downstream |
| **5** | `org_empresa` | **Alto** | TENANT scope; UoW + bootstrap cfg; EMP001 onboarding hardcodeado; multi-empresa |

---

## 11. Riesgos de compatibilidad hacia atrás

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R-CMP-01 | Clientes API envían código manual con formato distinto al motor | Media | AUTO_DEFAULT acepta manual; alinear contador |
| R-CMP-02 | Frontend exige campo código required | Alta | Coordinar release; optional en schema |
| R-CMP-03 | EMP001 hardcodeado vs contador TENANT | **Resuelto** | Seed cfg `ultimo_numero=1` (BR-BOOT-04); normativa `07` / `bootstrap/03` |
| R-CMP-04 | Empresa nueva sin filas cfg (pre-V1) | Media | Resuelto por Empresa Bootstrap V1; motor lazy no garantizado |
| R-CMP-05 | Pre-check + allocate doble costo | Baja | Eliminar pre-check en path AUTO puro |
| R-CMP-06 | Auto-commit vs allocate+INSERT atómico | **Alta** | UoW obligatorio por entidad antes de gateway |
| R-CMP-07 | UPDATE cambia código sin alinear contador | Media | Usar `align_counter` en update manual |
| R-CMP-08 | Formato legacy `SUC-LIMA-01` vs `SUC001` | Media | Manual permitido en transición; reporting gradual |
| R-CMP-09 | Dedicated sin cfg row | Baja | Bootstrap V1 + seed onboarding |

---

## 12. Estrategia incremental (Strangler) — resumen

Ver detalle en [`03_ORG_MIGRATION_STRATEGY.md`](03_ORG_MIGRATION_STRATEGY.md).

**Principios:**

1. **Una entidad por entrega** — gate tests por maestro.
2. **Motor congelado** — solo consumo de `CodigoGeneracionGateway`.
3. **AUTO_DEFAULT** — convivencia manual + auto sin breaking inmediato.
4. **UoW antes de gateway** — replicar patrón `create_empresa_servicio`.
5. **Sin tocar onboarding** en Ola 1 inicial — abordar `org_empresa` al final con plan EMP001.
6. **OpenAPI evolutivo** — optional codigo en Create; Read unchanged.

---

## Veredicto auditoría

**Auditoría funcional ORG Ola 1 — COMPLETA.**  
Lista para planificación de implementación por entidad, comenzando por **`org_cargo`**.
