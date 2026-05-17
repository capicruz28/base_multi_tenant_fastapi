# Auditoría — Módulo ORG (Organización)

**Código:** ORG  
**Fuente de modelo de datos:** `docs/bd/ORG_TABLAS.sql` (solo tablas `org_*`).  
**Metodología:** `docs/prompts/PROMPT_MODULO_MAESTRO.md` — Fase 2.

**Inventario de código ORG**

| Capa | Ubicación |
|------|-----------|
| Routers (presentation) | `app/modules/org/presentation/endpoints.py` (agregador), `endpoints_empresa.py`, `endpoints_sucursales.py`, `endpoints_centros_costo.py`, `endpoints_departamentos.py`, `endpoints_cargos.py`, `endpoints_parametros.py` |
| Schemas | `app/modules/org/presentation/schemas.py` |
| Servicios (application) | `app/modules/org/application/services/*.py` |
| Consultas SQL (infraestructura) | `app/infrastructure/database/queries/org/*.py` |
| Repositories dedicados (módulo ORG) | No hay carpeta `repositories` en ORG; persistencia vía queries en infraestructura |

Prefijo API registrado: **`/org`** (`app/api/v1/api.py`).

---

## 1. Tablas detectadas y su tipo

| Tabla | Tipo (prompt) |
|-------|----------------|
| `org_empresa` | Maestro |
| `org_centro_costo` | Maestro |
| `org_sucursal` | Maestro |
| `org_departamento` | Maestro |
| `org_cargo` | Maestro |
| `org_parametro_sistema` | Maestro / configuración |

No hay tablas derivadas o analíticas en el alcance ORG de `ORG_TABLAS.sql`.

---

## 2. Endpoints existentes

Criterios: **tenant** = uso de `cliente_id` del usuario autenticado en servicio/query. **RBAC** = `require_permission(...)` en la ruta.

Patrón ORG: en la mayoría de rutas la dependencia principal es `Depends(require_permission("org.<recurso>.<accion>"))`, que internamente resuelve el usuario activo (no siempre se declara `get_current_active_user` por separado, a diferencia de algunos módulos como INV).

| Ruta (relativa al router del módulo) | Método | Entidad (tabla) | Tenant (`cliente_id`) | RBAC |
|--------------------------------------|--------|-----------------|------------------------|------|
| `/empresa` | GET | `org_empresa` | Sí | `org.empresa.leer` |
| `/empresa/{empresa_id}` | GET | `org_empresa` | Sí | `org.empresa.leer` |
| `/empresa` | POST | `org_empresa` | Sí | `org.empresa.crear` |
| `/empresa/{empresa_id}` | PUT | `org_empresa` | Sí | `org.empresa.actualizar` |
| `/empresa/{empresa_id}` | DELETE | `org_empresa` | Sí | `org.empresa.eliminar` |
| `/empresa/{empresa_id}/reactivar` | POST | `org_empresa` | Sí | `org.empresa.actualizar` |
| `/sucursales` | GET | `org_sucursal` | Sí | `org.sucursal.leer` |
| `/sucursales/{sucursal_id}` | GET | `org_sucursal` | Sí | `org.sucursal.leer` |
| `/sucursales` | POST | `org_sucursal` | Sí | `org.sucursal.crear` |
| `/sucursales/{sucursal_id}` | PUT | `org_sucursal` | Sí | `org.sucursal.actualizar` |
| `/sucursales/{sucursal_id}` | DELETE | `org_sucursal` | Sí | `org.sucursal.eliminar` |
| `/centros-costo` | GET | `org_centro_costo` | Sí | `org.centro_costo.leer` |
| `/centros-costo/{centro_costo_id}` | GET | `org_centro_costo` | Sí | `org.centro_costo.leer` |
| `/centros-costo` | POST | `org_centro_costo` | Sí | `org.centro_costo.crear` |
| `/centros-costo/{centro_costo_id}` | PUT | `org_centro_costo` | Sí | `org.centro_costo.actualizar` |
| `/centros-costo/{centro_costo_id}` | DELETE | `org_centro_costo` | Sí | `org.centro_costo.eliminar` |
| `/departamentos` | GET | `org_departamento` | Sí | `org.departamento.leer` |
| `/departamentos/{departamento_id}` | GET | `org_departamento` | Sí | `org.departamento.leer` |
| `/departamentos` | POST | `org_departamento` | Sí | `org.departamento.crear` |
| `/departamentos/{departamento_id}` | PUT | `org_departamento` | Sí | `org.departamento.actualizar` |
| `/departamentos/{departamento_id}` | DELETE | `org_departamento` | Sí | `org.departamento.eliminar` |
| `/cargos` | GET | `org_cargo` | Sí | `org.cargo.leer` |
| `/cargos/{cargo_id}` | GET | `org_cargo` | Sí | `org.cargo.leer` |
| `/cargos` | POST | `org_cargo` | Sí | `org.cargo.crear` |
| `/cargos/{cargo_id}` | PUT | `org_cargo` | Sí | `org.cargo.actualizar` |
| `/cargos/{cargo_id}` | DELETE | `org_cargo` | Sí | `org.cargo.eliminar` |
| `/parametros` | GET | `org_parametro_sistema` | Sí | `org.parametro.leer` |
| `/parametros/{parametro_id}` | GET | `org_parametro_sistema` | Sí | `org.parametro.leer` |
| `/parametros` | POST | `org_parametro_sistema` | Sí | `org.parametro.crear` |
| `/parametros/{parametro_id}` | PUT | `org_parametro_sistema` | Sí | `org.parametro.actualizar` |
| `/parametros/{parametro_id}` | DELETE | `org_parametro_sistema` | Sí | `org.parametro.eliminar` |

---

## 3. Brechas frente al estándar MAESTRO del prompt

Estándar: crear, listar, detalle, actualizar, **activar/desactivar**.

| Tabla | Crear | Listar | Detalle | Actualizar | Desactivar (lógico) | Reactivar (activar) |
|-------|-------|--------|---------|------------|---------------------|---------------------|
| `org_empresa` | Sí | Sí | Sí | Sí | Sí (`DELETE` → baja lógica) | Sí (`POST .../reactivar`) |
| `org_sucursal` | Sí | Sí | Sí | Sí | Sí (`DELETE`) | **No** (solo reactivación vía `PUT` con `es_activo`, si el cliente lo envía) |
| `org_centro_costo` | Sí | Sí | Sí | Sí | Sí (`DELETE`) | **No** (mismo comentario) |
| `org_departamento` | Sí | Sí | Sí | Sí | Sí (`DELETE`) | **No** |
| `org_cargo` | Sí | Sí | Sí | Sí | Sí (`DELETE`) | **No** |
| `org_parametro_sistema` | Sí | Sí | Sí | Sí | Sí (`DELETE`) | **No** |

**Conclusión:** Falta un simétrico explícito a empresa **reactivar** (o política documentada de “solo `PUT` + `es_activo`”) para sucursal, centro de costo, departamento, cargo y parámetro, si se quiere alinear al mismo patrón UX/API que `org_empresa`.

---

## 4. Endpoints faltantes sugeridos (opcional, Fase 3)

Si se desea paridad con `org_empresa` y permisos claros de “activar”:

| Ruta sugerida | Método | Notas |
|---------------|--------|--------|
| `/org/sucursales/{sucursal_id}/reactivar` | POST | Misma semántica que empresa; permiso sugerido: `org.sucursal.actualizar` (o `org.sucursal.activar` si se agrega a RBAC). |
| `/org/centros-costo/{centro_costo_id}/reactivar` | POST | Idem. |
| `/org/departamentos/{departamento_id}/reactivar` | POST | Idem. |
| `/org/cargos/{cargo_id}/reactivar` | POST | Idem. |
| `/org/parametros/{parametro_id}/reactivar` | POST | Idem. |

No se detectaron endpoints de escritura sobre vistas derivadas (no aplica).

---

## 5. Campos en BD no cubiertos (o parcialmente) en schemas

Comparación explícita contra columnas de `docs/bd/ORG_TABLAS.sql`. Los schemas **sí** alinean tipos UUID para `pais_id`, `moneda_base_id`, `moneda_salarial`, etc., con la definición actual del SQL de referencia.

### 5.1 `org_empresa` ↔ `EmpresaCreate` / `EmpresaUpdate` / `EmpresaRead`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_creacion_id` | En **Read** no está expuesto en el schema (puede venir en fila SQL y descartarse al mapear). |
| `usuario_actualizacion_id` | Igual: no está en **Read**. |

Create/Update cubren el resto de columnas de negocio relevantes según el SQL (incl. `pais_id`, `moneda_base_id`, `maneja_multimoneda`).

### 5.2 `org_centro_costo` ↔ `CentroCosto*`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_creacion_id` | No está en **Read**. |
| `ruta_jerarquica` | En **Read** sí; en **Create** / **Update** no (aceptable si se calcula en backend; si la BD debe recibirse desde cliente, falta en escritura). |

### 5.3 `org_sucursal` ↔ `Sucursal*`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_creacion_id` | No está en **Read**. |

### 5.4 `org_departamento` ↔ `Departamento*`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_creacion_id` | No está en **Read**. |
| `jefe_departamento_usuario_id` | En **Create** no está (sí en **Update** y **Read**). Si el alta debe fijar jefe por UUID, falta en Create. |

### 5.5 `org_cargo` ↔ `Cargo*`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_creacion_id` | No está en **Read**. |

`moneda_salarial` en BD es `UNIQUEIDENTIFIER NOT NULL`; el schema usa `UUID` — **coherente**.

### 5.6 `org_parametro_sistema` ↔ `Parametro*`

| Columna BD | Observación |
|--------------|-------------|
| `usuario_actualizacion_id` | No está en **Read**. |
| `expresion_validacion`, `mensaje_validacion` | En **Update** sí; en **Create** no (la BD los admite; útil para alta con validación desde el inicio). |

**Nota:** `ParametroUpdate` no permite cambiar `modulo_codigo`, `codigo_parametro` ni `empresa_id`; puede ser decisión de negocio (clave compuesta inmutable tras crear).

---

## 6. Problemas de tenant o RBAC

### 6.1 Tenant (`cliente_id`)

- Todas las operaciones ORG revisadas pasan `client_id` desde el usuario autenticado hacia servicios y queries.
- Las queries en `app/infrastructure/database/queries/org/*` filtran por `cliente_id` en listados y en `get_*_by_id`.

### 6.2 `empresa_id` cuando la tabla lo tiene

- **Listados:** filtro opcional por query `empresa_id` donde aplica (sucursal, centro de costo, departamento, cargo, parámetro).
- **Alta:** `empresa_id` viene en el body (excepto `org_empresa` y parámetros con `empresa_id` opcional).
- **Detalle / actualización / baja por ID:** los `get_*_by_id` usan **`cliente_id` + clave primaria**, pero **no** exigen `empresa_id` en el `WHERE`.

**Riesgo:** un `*_id` válido de otra empresa del mismo cliente sería accesible si se conociera el UUID (mismo `cliente_id`, distinta `empresa_id`). Para cumplir estrictamente “validar `empresa_id` cuando la tabla lo tenga”, habría que reforzar en servicio o query (p. ej. query param obligatorio `empresa_id` en GET/PUT/DELETE, o comprobar que la fila devuelta coincida con contexto de empresa activa).

### 6.3 RBAC

- Patrón `org.<recurso>.<accion>` aplicado de forma consistente en los endpoints ORG listados.
- La baja lógica usa permiso **`eliminar`**, no un permiso dedicado `desactivar`; coherente con el nombre de acción en código.

---

## 7. Código u observaciones (no eliminar en auditoría)

- **Patrón de dependencias:** ORG usa con frecuencia solo `Depends(require_permission(...))` como “usuario actual”, frente al patrón `get_current_active_user` + `require_permission` de otros módulos. No es código obsoleto por sí solo; es variante válida si el tipo devuelto expone `cliente_id`.
- **“Eliminar” = baja lógica:** implementación alineada con la regla de no borrar físicamente (`es_activo`).
- **Documento anterior:** versiones antiguas de esta auditoría citaban discrepancias de BD (p. ej. texto `pais` vs `pais_id`) que **no** corresponden a `docs/bd/ORG_TABLAS.sql` actual; esta revisión las corrige.

---

## 8. Checkpoint Fase 2 (para confirmación antes de Fase 3)

1. **Tablas ORG con cobertura API:** las 6 tablas maestras tienen flujo CRUD (vía REST) salvo la paridad de **reactivar** explícito (solo empresa hoy).  
2. **Mayor brecha de reglas:** validación explícita de **`empresa_id`** en operaciones por ID frente a tablas que la incluyen.  
3. **Mayor brecha de schemas:** campos de auditoría (`usuario_*`) y algunos opcionales en **Create** (departamento jefe, parámetros de validación).  
4. **Infraestructura:** no hay capa `repositories` en el módulo ORG; las queries viven en `app/infrastructure/database/queries/org/`.

⛔ **Detente aquí (Fase 2).** Tras tu confirmación, la Fase 3 debe implementar solo lo acordado a partir de este informe (schemas → queries/servicios → routers → seeds RBAC si aplica).