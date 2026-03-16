## 1. Resumen del módulo ORG

El módulo **ORG — Organización** es el **módulo base obligatorio** del ERP multi-tenant.  
Su objetivo, según `CATALOGO_MODULOS.md`, `MENU_NAVEGACION.md` y la sección 2.1 del `MANUAL_USUARIO.md`, es:

- **Definir la estructura organizacional** y la **configuración global (incluyendo multi-moneda)** de cada tenant:
  - **Empresa** (razón social, RUC/NIT, moneda base, parámetros globales, política de multi-moneda).
  - **Sucursales** (sedes físicas y virtuales).
  - **Departamentos** (estructura jerárquica por áreas).
  - **Cargos** (puestos de trabajo).
  - **Centros de costo** (unidades para imputar gastos).
  - **Parámetros del sistema** (por módulo y, opcionalmente, por empresa).
- Proveer la base para que otros módulos (INV, PUR, SLS, FIN, HCM, etc.) referencien:
  - `empresa_id`, `sucursal_id`, `departamento_id`, `cargo_id`, `centro_costo_id`.
- Mantener **aislamiento multi-tenant**:
  - Todas las tablas ORG tienen `cliente_id`.
  - La mayoría de entidades se escopan por `(cliente_id, empresa_id)`.

A nivel backend, ORG se implementa con:

- **Modelos SQLAlchemy Core** en `tables_org.py` (`OrgEmpresaTable`, `OrgCentroCostoTable`, `OrgSucursalTable`, `OrgDepartamentoTable`, `OrgCargoTable`, `OrgParametroSistemaTable`).
- **Queries asíncronas** en `app/infrastructure/database/queries/org/*.py` (filtro estricto por `cliente_id`).
- **Servicios de aplicación** en `app/modules/org/application/services/*.py`.
- **Endpoints FastAPI** en `app/modules/org/presentation/endpoints_*.py`, montados bajo `/api/v1/org` vía `app/api/v1/api.py`.
- **RBAC** basado en permisos del catálogo `org.<recurso>.<acción>` definidos en `SEED_PERMISOS_RBAC.sql`.

Conclusión de alto nivel: la implementación backend de ORG **está fuertemente alineada** con la documentación funcional y con el diseño multi-tenant, con oportunidades de mejora principalmente en endpoints semánticos (eliminar / reactivar), búsqueda y operaciones jerárquicas.

---

## 2. Funcionalidades definidas en documentación

### 2.1 `CATALOGO_MODULOS.md`

- **ORG — Configuración Empresarial**
  - **Estructura organizacional completa**.
  - **Sucursales, departamentos, cargos**.
  - **Centros de costo**.
  - Se asume una empresa puede operar múltiples sucursales y centros de costo.

### 2.2 `MENU_NAVEGACION.md`

Opciones de menú para ORG:

- **Mi Empresa**
  - Ver y editar datos de empresa (RUC, razón social, logo, moneda).
- **Sucursales**
  - Gestionar sucursales con dirección, teléfono, responsable y flags de uso (casa matriz, punto de venta, almacén).
- **Departamentos**
  - Crear estructura organizacional jerárquica por áreas (padre/hijo).
- **Cargos**
  - Definir puestos de trabajo (gerente, operario, vendedor, etc.).
- **Centros de Costo**
  - Configurar centros para control de gastos por área, con jerarquía y responsable.
- **Parámetros del Sistema**
  - Configuración global:
    - Parámetros por módulo (`modulo_codigo`, p.ej. `INV`, `FIN`, `MFG`).
    - Parámetros globales o por empresa (`empresa_id` opcional).

### 2.3 `MANUAL_USUARIO.md` — 2.1 Módulo ORG

Flujo funcional descrito:

- **Paso 1: Configurar Mi Empresa**
  - Navegar a: `ORG > Mi Empresa`.
  - Completar RUC/NIT, razón social, nombre comercial, tipo de empresa, moneda base, país, dirección fiscal.
  - El RUC **no se puede cambiar** después (dato crítico).
  - Activar **“Multi-moneda”** solo si realmente opera en USD/EUR (implica manejar más de una moneda por empresa).
- **Paso 2: Crear Sucursales**
  - Navegar a: `ORG > Sucursales > [+ Nueva Sucursal]`.
  - Definir código, nombre, dirección, teléfono, responsable.
  - Marcar una sucursal como **principal** (casa matriz).
  - Se sugiere crear sucursales **virtuales** para e‑commerce.
- **Paso 3: Definir Departamentos**
  - Navegar a: `ORG > Departamentos`.
  - Crear estructura jerárquica (Dirección General → Administración/Operaciones/Comercial, etc.).
  - Definir códigos (`DIR-GRAL`, `ADMIN-FIN`, etc.).
  - Notas: los departamentos se usan intensivamente en RRHH/HCM.
- **Paso 4: Crear Cargos**
  - Navegar a: `ORG > Cargos`.
  - Crear cargos por área (producción, administración, ventas) con códigos descriptivos.
- **Paso 5: Configurar Centros de Costo**
  - Navegar a: `ORG > Centros de Costo`.
  - Crear centros productivos y no productivos, con pocos elementos bien definidos.
  - Los centros de costo se usan en:
    - Asientos contables (FIN).
    - Presupuestos (BDG).
    - Costeo (CST, MFG).
- **Paso 6: Parámetros del Sistema**
  - Navegar a: `ORG > Parámetros del Sistema`.
  - Configurar parámetros de Inventarios, Facturación, Producción, etc.
  - Algunos parámetros son globales al tenant, otros específicos de una empresa.

La documentación no detalla explícitamente operaciones de **eliminación física**, pero sí utiliza el concepto de **activación / vigencia** (a través de `es_activo` y fechas), lo que apunta a un modelo de **baja lógica**.

---

## 3. Implementación actual detectada (backend ORG)

- **Routing principal**
  - `app/api/v1/api.py` incluye:
    - `api_router.include_router(org_endpoints.router, prefix="/org", tags=["ORG - Organización"])`.
  - `app/modules/org/presentation/endpoints.py`:
    - Incluye sub-routers con prefijos:
      - `/empresa`, `/sucursales`, `/centros-costo`, `/departamentos`, `/cargos`, `/parametros`.
    - Prefijo completo efectivo: `/api/v1/org/<recurso>`.

- **Capas principales**
  - **Presentación (FastAPI)**
    - `endpoints_empresa.py`, `endpoints_sucursales.py`, `endpoints_centros_costo.py`, `endpoints_departamentos.py`, `endpoints_cargos.py`, `endpoints_parametros.py`.
    - Todas las rutas usan:
      - `UsuarioReadWithRoles` como usuario autenticado.
      - `require_permission("org.<recurso>.<accion>")`.
      - `client_id = current_user.cliente_id` (nunca desde el body).
  - **Servicios de aplicación**
    - `empresa_service.py`, `sucursal_service.py`, `centro_costo_service.py`, `departamento_service.py`, `cargo_service.py`, `parametro_service.py`.
    - Reciben `client_id` y delegan a queries del módulo ORG.
  - **Queries SQL**
    - `empresa_queries.py`, `sucursal_queries.py`, `centro_costo_queries.py`, `departamento_queries.py`, `cargo_queries.py`, `parametro_queries.py`.
    - Todas las operaciones filtran por `cliente_id` y, donde aplica, por `empresa_id`.
  - **Modelos de BD**
    - `tables_org.py` define actualmente:
      - `OrgEmpresaTable`, `OrgCentroCostoTable`, `OrgSucursalTable`, `OrgDepartamentoTable`, `OrgCargoTable`, `OrgParametroSistemaTable`, todas con `cliente_id` y (salvo parámetros) `empresa_id` obligatorio.
      - Campos relacionados con moneda como:
        - `OrgEmpresaTable.moneda_base` (código de 3 letras, por defecto `PEN`).
        - `OrgCargoTable.moneda_salarial` (código de 3 letras, por defecto `PEN`).
      - Constraints únicos por `(cliente_id, empresa_id, codigo)` o equivalentes.
    - El archivo de diseño de BD `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql` introduce una **nueva tabla `org_moneda`** y campos adicionales en `org_empresa`:
      - `org_empresa.maneja_multimoneda` (BIT) y `org_empresa.moneda_base_id` (FK a `org_moneda.moneda_id`).
      - Tabla `org_moneda` (por empresa) con `codigo`, `nombre`, `simbolo`, `es_moneda_base`, `es_activo`.
      - Múltiples tablas de FIN, PUR, SLS, HCM, etc. referenciando `org_moneda.moneda_id`.
    - A fecha de esta auditoría, **`tables_org.py` aún no modela `org_moneda` ni los nuevos campos `moneda_base_id` / `maneja_multimoneda`**, por lo que la capa ORM/servicios/endpoints todavía no soporta el diseño multi-moneda completo definido en la BD.

- **RBAC y permisos**
  - `app/core/authorization/rbac.py` (importado como `require_permission`) valida permisos contra la lista de permisos del usuario.
  - `SEED_PERMISOS_RBAC.sql` define explícitamente permisos:
    - `org.empresa.leer/crear/actualizar/eliminar`.
    - `org.sucursal.leer/crear/actualizar/eliminar`.
    - `org.departamento.leer/crear/actualizar/eliminar`.
    - `org.cargo.leer/crear/actualizar/eliminar`.
    - `org.centro_costo.leer/crear/actualizar/eliminar`.
    - `org.parametro.leer/crear/actualizar/eliminar`.
  - Los endpoints ORG usan actualmente solo las variantes `leer`, `crear`, `actualizar`.

---

## 4. Entidades del módulo ORG

- **Empresa (`org_empresa`)**
  - Clave: `empresa_id`.
  - Scope: `cliente_id` (tenant) + `empresa_id`.
  - Campos clave: `codigo_empresa`, `razon_social`, `ruc`, datos fiscales, configuración de formatos, logos, fechas de constitución/inicio, `es_activo`.
  - Campos relacionados con moneda:
    - En diseño de BD (Fase 4): `moneda_base_id` (FK a `org_moneda`), `maneja_multimoneda` (BIT), `decimales_moneda`.
    - En implementación actual (`tables_org.py` y schemas): `moneda_base: str` (código de 3 letras) y `decimales_moneda` como entero; **no existen aún `moneda_base_id` ni `maneja_multimoneda` en el modelo ORM ni en los endpoints**.
  - Constraints:
    - `UNIQUE (cliente_id, codigo_empresa)`.
    - `UNIQUE (cliente_id, ruc)`.

- **Sucursal (`org_sucursal`)**
  - Clave: `sucursal_id`.
  - Scope: `cliente_id` + `empresa_id`.
  - Campos: `codigo`, `nombre`, dirección completa, `es_casa_matriz`, `es_punto_venta`, `es_almacen`, `es_planta_produccion`, `centro_costo_id`, `es_activo`, etc.

- **Centro de Costo (`org_centro_costo`)**
  - Clave: `centro_costo_id`.
  - Scope: `cliente_id` + `empresa_id`.
  - Campos: `codigo`, `nombre`, jerarquía (`centro_costo_padre_id`, `nivel`, `ruta_jerarquica`), `tipo_centro_costo`, `categoria`, flags de presupuesto/imputación, responsable, `es_activo`, vigencia.

- **Departamento (`org_departamento`)**
  - Clave: `departamento_id`.
  - Scope: `cliente_id` + `empresa_id`.
  - Campos: `codigo`, `nombre`, jerarquía (`departamento_padre_id`, `nivel`, `ruta_jerarquica`), `tipo_departamento`, `jefe_departamento_usuario_id`, `jefe_nombre`, `centro_costo_id`, `sucursal_id`, `es_activo`.

- **Cargo (`org_cargo`)**
  - Clave: `cargo_id`.
  - Scope: `cliente_id` + `empresa_id`.
  - Campos: `codigo`, `nombre`, descripción, `nivel_jerarquico`, `categoria`, `area_funcional`, `departamento_id`, `cargo_jefe_id`, rango salarial, requisitos, `es_activo`.

- **Parámetro del Sistema (`org_parametro_sistema`)**
  - Clave: `parametro_id`.
  - Scope: `cliente_id` + `empresa_id` opcional + `modulo_codigo` + `codigo_parametro`.
  - Campos: `modulo_codigo`, `codigo_parametro`, `nombre_parametro`, `tipo_dato`, distintas columnas `valor_*`, `es_editable`, `es_obligatorio`, `es_activo`, `opciones_validas`, `expresion_validacion`, `mensaje_validacion`.

- **Moneda (`org_moneda`) — solo en diseño de BD Fase 4**
  - Clave: `moneda_id`.
  - Scope: `cliente_id` + `empresa_id`.
  - Campos: `codigo` (ej. `PEN`, `USD`, `EUR`), `nombre`, `simbolo`, `es_moneda_base`, `decimales`, `es_activo`, más campos de auditoría.
  - Relaciones:
    - `org_empresa.moneda_base_id` → `org_moneda.moneda_id`.
    - Referencias desde tablas de FIN, PUR, SLS, HCM, MFG, etc. para indicar la moneda de documentos financieros.
  - Implementación actual:
    - **No existe una tabla `OrgMonedaTable` en `tables_org.py`, ni schemas Pydantic, ni servicios, ni endpoints para gestionar monedas**.

Dependencias con otros módulos:

- Múltiples tablas de otros módulos (`tables_inv.py`, `tables_pur.py`, `tables_sls.py`, `tables_hcm.py`, `tables_fin.py`, etc.) referencian:
  - `org_empresa.empresa_id`.
  - `org_sucursal.sucursal_id`.
  - `org_departamento.departamento_id`.
  - `org_cargo.cargo_id`.
  - `org_centro_costo.centro_costo_id`.
- Esto confirma que ORG es la **fuente única** de entidades organizacionales para el ERP completo.

---

## 5. Endpoints detectados (detalle por endpoint)

Todos los endpoints ORG:

- Están bajo prefijo `/api/v1/org`.
- Requieren autenticación y un usuario (`UsuarioReadWithRoles`) con permisos RBAC.
- Obtienen `client_id` únicamente desde `current_user.cliente_id`.

### 5.1 Empresa

- **Listar empresas**
  - **Método / ruta**: `GET /api/v1/org/empresa`
  - **Archivo / función**: `endpoints_empresa.py` → `listar_empresas`
  - **Servicio**: `empresa_service.list_empresas_servicio`
  - **Entidad**: `OrgEmpresaTable`
  - **Permiso**: `org.empresa.leer`
  - **Multi-tenant**:
    - `client_id = current_user.cliente_id`.
    - Query: `WHERE cliente_id == client_id` (+ `es_activo == True` si `solo_activos`).
  - **Moneda / multi-moneda**:
    - Los endpoints exponen y consumen el campo `moneda_base` como string (código de 3 letras).
    - No exponen ningún campo equivalente a `moneda_base_id` ni a `maneja_multimoneda` definidos en el diseño de BD Fase 4.

- **Detalle de empresa**
  - **Método / ruta**: `GET /api/v1/org/empresa/{empresa_id}`
  - **Función**: `detalle_empresa`
  - **Servicio**: `empresa_service.get_empresa_servicio`
  - **Permiso**: `org.empresa.leer`
  - **Multi-tenant**: `get_empresa_by_id` filtra por `cliente_id` y `empresa_id`.

- **Crear empresa**
  - **Método / ruta**: `POST /api/v1/org/empresa`
  - **Función**: `crear_empresa`
  - **Body**: `EmpresaCreate` (sin `cliente_id` ni `empresa_id`).
  - **Servicio**: `empresa_service.create_empresa_servicio`
  - **Permiso**: `org.empresa.crear`
  - **Multi-tenant**: `create_empresa` fuerza `payload["cliente_id"] = client_id` y genera `empresa_id`.

- **Actualizar empresa**
  - **Método / ruta**: `PUT /api/v1/org/empresa/{empresa_id}`
  - **Función**: `actualizar_empresa`
  - **Body**: `EmpresaUpdate` (parcial).
  - **Servicio**: `empresa_service.update_empresa_servicio`
  - **Permiso**: `org.empresa.actualizar`
  - **Multi-tenant**: `update_empresa` usa `WHERE cliente_id == client_id AND empresa_id == empresa_id`.

### 5.2 Sucursales

- **Listar sucursales**
  - **Método / ruta**: `GET /api/v1/org/sucursales?empresa_id&solo_activos`
  - **Función**: `listar_sucursales`
  - **Servicio**: `sucursal_service.list_sucursales_servicio`
  - **Entidad**: `OrgSucursalTable`
  - **Permiso**: `org.sucursal.leer`
  - **Multi-tenant**: filtro por `cliente_id` y opcionalmente `empresa_id`.

- **Detalle sucursal**
  - **Método / ruta**: `GET /api/v1/org/sucursales/{sucursal_id}`
  - **Función**: `detalle_sucursal`
  - **Servicio**: `sucursal_service.get_sucursal_servicio`
  - **Permiso**: `org.sucursal.leer`
  - **Multi-tenant**: `get_sucursal_by_id` filtra por `cliente_id` + `sucursal_id`.

- **Crear sucursal**
  - **Método / ruta**: `POST /api/v1/org/sucursales`
  - **Función**: `crear_sucursal`
  - **Body**: `SucursalCreate` (incluye `empresa_id`).
  - **Servicio**: `sucursal_service.create_sucursal_servicio`
  - **Permiso**: `org.sucursal.crear`
  - **Multi-tenant**: `create_sucursal` fuerza `cliente_id` y genera `sucursal_id`.

- **Actualizar sucursal**
  - **Método / ruta**: `PUT /api/v1/org/sucursales/{sucursal_id}`
  - **Función**: `actualizar_sucursal`
  - **Servicio**: `sucursal_service.update_sucursal_servicio`
  - **Permiso**: `org.sucursal.actualizar`
  - **Multi-tenant**: `update_sucursal` restringe por `cliente_id` + `sucursal_id`.

### 5.3 Centros de Costo

- **Listar centros de costo**
  - **Método / ruta**: `GET /api/v1/org/centros-costo?empresa_id&solo_activos`
  - **Función**: `listar_centros_costo`
  - **Servicio**: `centro_costo_service.list_centros_costo_servicio`
  - **Entidad**: `OrgCentroCostoTable`
  - **Permiso**: `org.centro_costo.leer`
  - **Multi-tenant**: filtro por `cliente_id` y opcionalmente `empresa_id`.

- **Detalle centro de costo**
  - **Método / ruta**: `GET /api/v1/org/centros-costo/{centro_costo_id}`
  - **Función**: `detalle_centro_costo`
  - **Servicio**: `centro_costo_service.get_centro_costo_servicio`
  - **Permiso**: `org.centro_costo.leer`
  - **Multi-tenant**: `get_centro_costo_by_id` filtra por `cliente_id` + `centro_costo_id`.

- **Crear centro de costo**
  - **Método / ruta**: `POST /api/v1/org/centros-costo`
  - **Función**: `crear_centro_costo`
  - **Body**: `CentroCostoCreate` (incluye `empresa_id`).
  - **Servicio**: `centro_costo_service.create_centro_costo_servicio`
  - **Permiso**: `org.centro_costo.crear`

- **Actualizar centro de costo**
  - **Método / ruta**: `PUT /api/v1/org/centros-costo/{centro_costo_id}`
  - **Función**: `actualizar_centro_costo`
  - **Servicio**: `centro_costo_service.update_centro_costo_servicio`
  - **Permiso**: `org.centro_costo.actualizar`

### 5.4 Departamentos

- **Listar departamentos**
  - **Método / ruta**: `GET /api/v1/org/departamentos?empresa_id&solo_activos`
  - **Función**: `listar_departamentos`
  - **Servicio**: `departamento_service.list_departamentos_servicio`
  - **Entidad**: `OrgDepartamentoTable`
  - **Permiso**: `org.departamento.leer`

- **Detalle departamento**
  - **Método / ruta**: `GET /api/v1/org/departamentos/{departamento_id}`
  - **Función**: `detalle_departamento`
  - **Servicio**: `departamento_service.get_departamento_servicio`
  - **Permiso**: `org.departamento.leer`

- **Crear departamento**
  - **Método / ruta**: `POST /api/v1/org/departamentos`
  - **Función**: `crear_departamento`
  - **Body**: `DepartamentoCreate` (incluye `empresa_id`).
  - **Servicio**: `departamento_service.create_departamento_servicio`
  - **Permiso**: `org.departamento.crear`

- **Actualizar departamento**
  - **Método / ruta**: `PUT /api/v1/org/departamentos/{departamento_id}`
  - **Función**: `actualizar_departamento`
  - **Servicio**: `departamento_service.update_departamento_servicio`
  - **Permiso**: `org.departamento.actualizar`

### 5.5 Cargos

- **Listar cargos**
  - **Método / ruta**: `GET /api/v1/org/cargos?empresa_id&solo_activos`
  - **Función**: `listar_cargos`
  - **Servicio**: `cargo_service.list_cargos_servicio`
  - **Entidad**: `OrgCargoTable`
  - **Permiso**: `org.cargo.leer`

- **Detalle cargo**
  - **Método / ruta**: `GET /api/v1/org/cargos/{cargo_id}`
  - **Función**: `detalle_cargo`
  - **Servicio**: `cargo_service.get_cargo_servicio`
  - **Permiso**: `org.cargo.leer`

- **Crear cargo**
  - **Método / ruta**: `POST /api/v1/org/cargos`
  - **Función**: `crear_cargo`
  - **Body**: `CargoCreate` (incluye `empresa_id`).
  - **Servicio**: `cargo_service.create_cargo_servicio`
  - **Permiso**: `org.cargo.crear`

- **Actualizar cargo**
  - **Método / ruta**: `PUT /api/v1/org/cargos/{cargo_id}`
  - **Función**: `actualizar_cargo`
  - **Servicio**: `cargo_service.update_cargo_servicio`
  - **Permiso**: `org.cargo.actualizar`

### 5.6 Parámetros del Sistema

- **Listar parámetros**
  - **Método / ruta**: `GET /api/v1/org/parametros?empresa_id&modulo_codigo&solo_activos`
  - **Función**: `listar_parametros`
  - **Servicio**: `parametro_service.list_parametros_servicio`
  - **Entidad**: `OrgParametroSistemaTable`
  - **Permiso**: `org.parametro.leer`

- **Detalle parámetro**
  - **Método / ruta**: `GET /api/v1/org/parametros/{parametro_id}`
  - **Función**: `detalle_parametro`
  - **Servicio**: `parametro_service.get_parametro_servicio`
  - **Permiso**: `org.parametro.leer`

- **Crear parámetro**
  - **Método / ruta**: `POST /api/v1/org/parametros`
  - **Función**: `crear_parametro`
  - **Body**: `ParametroCreate`.
  - **Servicio**: `parametro_service.create_parametro_servicio`
  - **Permiso**: `org.parametro.crear`

- **Actualizar parámetro**
  - **Método / ruta**: `PUT /api/v1/org/parametros/{parametro_id}`
  - **Función**: `actualizar_parametro`
  - **Servicio**: `parametro_service.update_parametro_servicio`
  - **Permiso**: `org.parametro.actualizar`

Actualmente **no existen endpoints ORG para gestionar el catálogo de monedas (`org_moneda`)** ni para activar/desactivar multi-moneda a nivel de empresa más allá de exponer `moneda_base` como campo de texto.

---

## 6. Matriz funcionalidad vs implementación

**Leyenda**:

- **✔ Implementado completamente**.
- **⚠ Implementado parcialmente**.
- **✖ No implementado**.

| Funcionalidad (documentación)                                             | Endpoint / backend                                   | Estado | Comentario |
|---------------------------------------------------------------------------|------------------------------------------------------|--------|-----------|
| Mi Empresa: crear / ver / editar empresa del tenant                      | `GET/POST/PUT /api/v1/org/empresa`                   | ✔      | CRUD completo para los campos actualmente modelados (incluyendo `moneda_base` como string). |
| Mi Empresa: eliminar / desactivar empresa                                | No hay DELETE; `es_activo` manejable por PUT        | ⚠      | Baja lógica posible vía `es_activo`, pero sin endpoint semántico dedicado. |
| Multi-moneda: configurar moneda base de la empresa                        | Campo `moneda_base` en `org_empresa` y schemas       | ⚠      | Implementado como código de 3 letras; el diseño Fase 4 espera `moneda_base_id` → `org_moneda`, aún no implementado en ORM/endpoints. |
| Multi-moneda: habilitar/deshabilitar operación en varias monedas          | Campo `maneja_multimoneda` en diseño BD Fase 4       | ✖      | Campo solo existe en script SQL; no está modelado en `tables_org.py` ni expuesto en endpoints/schemas. |
| Multi-moneda: catálogo de monedas por empresa (`org_moneda`)             | Tabla `org_moneda` en diseño BD Fase 4               | ✖      | No hay `OrgMonedaTable`, ni services, ni endpoints (`/api/v1/org/monedas`), pese a que otros módulos ya referencian `moneda_id`. |
| Sucursales: listar (con filtro por empresa), ver detalle, crear, editar  | `GET/GET by id/POST/PUT /api/v1/org/sucursales`     | ✔      | Cobertura total según docs, con `empresa_id` y `solo_activos`. |
| Sucursales: eliminar / desactivar                                        | Sin DELETE dedicado; `es_activo` vía PUT            | ⚠      | Misma situación que empresa. |
| Departamentos: listar, detalle, crear, editar                            | CRUD vía `/api/v1/org/departamentos`                | ✔      | Soporta jerarquía y asociación a sucursal/centro de costo. |
| Departamentos: eliminar / desactivar                                     | Sin DELETE; `es_activo` actualizable                | ⚠      | Recomendable modelar baja lógica explícita por impacto en HCM. |
| Cargos: listar, detalle, crear, editar                                   | CRUD vía `/api/v1/org/cargos`                       | ✔      | Alineado con uso intensivo en RRHH. |
| Cargos: eliminar / desactivar                                            | Sin DELETE; `es_activo` vía PUT                     | ⚠      | Importante para gestión de históricos de empleados. |
| Centros de costo: listar, detalle, crear, editar                         | CRUD vía `/api/v1/org/centros-costo`                | ✔      | Filtros `empresa_id` y `solo_activos` según DOC frontend. |
| Centros de costo: eliminar / desactivar                                  | Sin DELETE; `es_activo` vía PUT                     | ⚠      | Debe coordinarse con FIN/BDG para no romper referencias. |
| Parámetros del Sistema: listar (por empresa/módulo), detalle, crear, editar | CRUD vía `/api/v1/org/parametros`                 | ✔      | Campos de valor y flags cubiertos. |
| Parámetros del Sistema: eliminar / desactivar                            | Sin DELETE; `es_activo` modificable                 | ⚠      | Coherente con soft delete, falta endpoint semántico. |
| Búsqueda / filtrado textual (por nombre/código)                          | No implementado (`buscar` ausente)                  | ⚠      | No exigido explícitamente, pero recomendado para UX (listas largas). |
| Visualizar árbol jerárquico departamentos / centros de costo             | Listas planas con campos de jerarquía               | ⚠      | Implementable en frontend; falta endpoint de árbol dedicado. |

En resumen, las funcionalidades principales están **implementadas**; las marcas ⚠ corresponden a aspectos **mejorables** más que a brechas críticas.

---

## 7. CRUD funcional por entidad

### 7.1 Tabla resumen

| Entidad          | Crear | Listar | Detalle | Actualizar | Eliminar (DELETE) | Desactivar / Reactivar (vía `es_activo`) |
|------------------|:-----:|:------:|:-------:|:----------:|:-----------------:|:-----------------------------------------:|
| Empresa          |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |
| Sucursal         |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |
| Centro de costo  |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |
| Departamento     |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |
| Cargo            |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |
| Parámetro        |  ✔    |   ✔    |   ✔     |     ✔      |        ✖          |                  ⚠ (PUT)                 |

Notas:

- **Eliminar (DELETE)**: no hay endpoints HTTP `DELETE`; la baja se modela implícitamente a través del campo `es_activo` (actualizable vía `PUT`).
- **Desactivar / Reactivar**: funcionalmente posible usando `PUT` con `es_activo = false/true`, pero **sin endpoints ni documentación semántica específica**.

---

## 8. Endpoints faltantes (según checklist funcional)

Aunque la documentación de usuario no exige explícitamente operaciones DELETE, el checklist de auditoría pide validar **eliminar** y **activar/desactivar**. Bajo ese criterio, se consideran **faltantes recomendados**:

- **Empresa**
  - **Endpoint sugerido**: `DELETE /api/v1/org/empresa/{empresa_id}`.
  - **Operación**: baja lógica (`es_activo = false`), sin borrado físico.
  - **Entidad afectada**: `org_empresa`.

- **Sucursales**
  - **Endpoint sugerido**: `DELETE /api/v1/org/sucursales/{sucursal_id}`.
  - **Entidad afectada**: `org_sucursal`.

- **Centros de costo**
  - **Endpoint sugerido**: `DELETE /api/v1/org/centros-costo/{centro_costo_id}`.
  - **Entidad afectada**: `org_centro_costo`.

- **Departamentos**
  - **Endpoint sugerido**: `DELETE /api/v1/org/departamentos/{departamento_id}`.
  - **Entidad afectada**: `org_departamento`.

- **Cargos**
  - **Endpoint sugerido**: `DELETE /api/v1/org/cargos/{cargo_id}`.
  - **Entidad afectada**: `org_cargo`.

- **Parámetros**
  - **Endpoint sugerido**: `DELETE /api/v1/org/parametros/{parametro_id}`.
  - **Entidad afectada**: `org_parametro_sistema`.

Motivo funcional común:

- Permitir modelar explícitamente la acción de “dar de baja” una entidad organizacional, alineado con los permisos `.eliminar` ya existentes en el catálogo RBAC, manteniendo internamente una **baja lógica**.

Adicionalmente, considerando los documentos oficiales y el diseño Fase 4 de la BD:

- **Moneda (multi-moneda)**
  - **Funcionalidad documentada**:
    - CATALOGO y MANUAL mencionan soporte **“Multi-moneda y multi-idioma”**.
    - En el paso de “Mi Empresa” se indica explícitamente activar “Multi-moneda” si se opera en USD/EUR.
    - El script `3.- TABLAS_BD_ERP_COMPLETO_FASE4.sql` define `org_moneda` y múltiples FKs `moneda_id` en FIN, PUR, SLS, HCM, etc.
  - **Faltantes detectados en backend ORG**:
    - Falta modelar `OrgMonedaTable` en `tables_org.py` alineada con `org_moneda`.
    - Falta una capa de queries (`moneda_queries.py`) y servicios para listar/crear/actualizar/desactivar monedas por empresa.
    - No existen endpoints bajo `/api/v1/org/monedas` para gestionar el catálogo de monedas (ni sus permisos RBAC asociados, p.ej. `org.moneda.leer/crear/actualizar/eliminar`).
    - `org_empresa` en código sigue usando `moneda_base` como string; no expone `moneda_base_id` ni `maneja_multimoneda` como en el diseño Fase 4.
  - **Endpoints sugeridos**:
    - `GET /api/v1/org/monedas?empresa_id&solo_activos` — Listar monedas de una empresa.
    - `GET /api/v1/org/monedas/{moneda_id}` — Detalle de moneda.
    - `POST /api/v1/org/monedas` — Crear moneda (empresa, código, nombre, símbolo, es_moneda_base, decimales).
    - `PUT /api/v1/org/monedas/{moneda_id}` — Actualizar moneda.
    - `DELETE /api/v1/org/monedas/{moneda_id}` — Baja lógica de moneda (`es_activo = false`).
  - **Ajustes adicionales recomendados**:
    - Ampliar `EmpresaCreate/Read/Update` para manejar `moneda_base_id` y `maneja_multimoneda` (además o en lugar de `moneda_base` string), manteniendo compatibilidad hacia atrás.

---

## 9. Endpoints incompletos o mejorables

- **Falta de endpoints de reactivación explícita**
  - Actualmente, la reactivación se hace vía `PUT` estableciendo `es_activo = true`.
  - Podrían definirse endpoints semánticos como:
    - `POST /api/v1/org/empresa/{id}/reactivar`.
    - `POST /api/v1/org/centros-costo/{id}/reactivar`, etc.
  - Estado: **mejora UX/API**, no brecha funcional crítica.

- **Búsqueda textual**
  - No existen parámetros tipo `?buscar=` o similares para filtrar por nombre/código en:
    - Empresas, sucursales, departamentos, cargos, centros de costo, parámetros.
  - A nivel de usabilidad, esto puede ser limitante en tenants con muchas entidades ORG.

- **Recuperación de árboles jerárquicos**
  - El manual presenta estructuras de árbol (departamentos, centros de costo).
  - El backend expone listas planas con relaciones padre/hijo.
  - Podría añadirse:
    - `GET /api/v1/org/departamentos/arbol?empresa_id=...`.
    - `GET /api/v1/org/centros-costo/arbol?empresa_id=...`.

- **Uso parcial del catálogo de permisos**
  - Los permisos `.eliminar` existen en `SEED_PERMISOS_RBAC.sql` para todas las entidades ORG, pero **no hay endpoints que los utilicen**.
  - Esto genera una ligera inconsistencia entre catálogo de permisos y superficie de API.

---

## 10. Validación multi-tenant

- **Filtrado por `cliente_id`**
  - Todas las queries ORG (`list_*`, `get_*_by_id`, `create_*`, `update_*`) filtran explícita y consistentemente por:
    - `WHERE <tabla>.cliente_id == client_id`.
  - `client_id`:
    - Proviene siempre de `current_user.cliente_id` en los endpoints.
    - Se pasa tal cual a servicios y queries.
  - No hay forma de manipular `client_id` desde el body ni query params.

- **Filtrado / asociación por `empresa_id`**
  - En entidades dependientes de empresa (sucursales, centros de costo, departamentos, cargos):
    - `empresa_id` es obligatorio en BD.
    - Las queries de listado permiten un filtro opcional `empresa_id` (param de query), acorde a la documentación.
  - En parámetros:
    - `empresa_id` puede ser `NULL` para parámetros globales al tenant.

- **Cross-tenant**
  - Las consultas de detalle siempre usan combinación `cliente_id + id_primario`.
  - No hay queries ORG que operen solo por `id_primario` sin `cliente_id`.
  - Esto mitiga riesgos de fuga de datos entre tenants incluso si se adivina un UUID.

Conclusión: el módulo ORG implementa un **aislamiento multi-tenant robusto**, acorde al diseño descrito en la documentación.

---

## 11. Validación de permisos (RBAC)

- **Patrón de permisos**
  - Los endpoints ORG usan `require_permission("org.<recurso>.<accion>")` con:
    - `org.empresa.leer/crear/actualizar`.
    - `org.sucursal.leer/crear/actualizar`.
    - `org.departamento.leer/crear/actualizar`.
    - `org.cargo.leer/crear/actualizar`.
    - `org.centro_costo.leer/crear/actualizar`.
    - `org.parametro.leer/crear/actualizar`.

- **Catálogo de permisos**
  - `SEED_PERMISOS_RBAC.sql` declara además las variantes `*.eliminar` para todos estos recursos, con descripciones coherentes (“Dar de baja …”).

- **Mecanismo de verificación**
  - `require_permission`:
    - Obtiene el usuario vía `get_current_active_user`.
    - Verifica el permiso contra `user.permisos` (o equivalente).
    - Considera super admin como bypass total.
  - Todos los endpoints ORG que exponen datos de negocio están protegidos por al menos un permiso.

Hallazgos:

- No se detectan endpoints ORG sin control de permisos.
- Existe una **inconsistencia menor**: el catálogo contempla permisos `.eliminar` que hoy no están asociados a ningún endpoint ORG.

---

## 12. Riesgos detectados

- **Ambigüedad sobre “eliminar” vs “desactivar”**
  - El manual habla de “gestionar” entidades, pero no diferencia claramente entre borrar y desactivar.
  - La BD y los schemas utilizan `es_activo` para todas las entidades ORG.
  - Sin endpoints `DELETE` ni documentación explícita:
    - Frontend puede implementar “eliminar” como `es_activo = false` sin una semántica única.
    - Integradores externos podrían asumir que no se soporta eliminación alguna.

- **Catálogo de permisos más amplio que la API**
  - Permisos `.eliminar` existen pero no se usan aún.
  - Puede generar confusión en administración de roles y auditoría de acceso.

- **Usabilidad con grandes volúmenes de datos**
  - La ausencia de parámetros de búsqueda textual puede dificultar:
    - Seleccionar departamentos, cargos, centros de costo en combos listados.
    - Encontrar sucursales en tenants grandes.

- **Jerarquías únicamente del lado frontend**
  - La construcción de árboles (departamentos, centros de costo) queda completamente a cargo del frontend.
  - Para módulos como HCM, BDG y FIN, esto puede duplicar lógica en varios clientes.

- **Soporte de multi-moneda incompleto respecto al diseño Fase 4**
  - El diseño de BD define `org_moneda`, `moneda_base_id` y `maneja_multimoneda` en `org_empresa`, además de múltiples FKs `moneda_id` en tablas de FIN, PUR, SLS, HCM, etc.
  - El backend ORG actual:
    - Solo expone `moneda_base` como string en empresa (y `moneda_salarial` en cargos).
    - No tiene modelos/queries/endpoints para `org_moneda`.
    - No expone ni gestiona `maneja_multimoneda`.
  - Riesgos:
    - Módulos financieros pueden depender de `org_moneda` sin que exista una forma estándar (API) de mantener ese catálogo.
    - Posibles inconsistencias si se cargan monedas directamente en BD sin pasar por una capa de negocio ORG (falta de validaciones, auditoría funcional, RBAC).

---

## 13. Propuesta de mejoras (sin escribir código)

- **Mejoras de endpoints**
  - Añadir endpoints `DELETE` por entidad ORG que realicen baja lógica (actualizar `es_activo = false`), consumiendo los permisos `*.eliminar` ya presentes en el catálogo.
  - Añadir endpoints de **reactivación** (por ejemplo, `POST /.../{id}/reactivar`) que dejen clara la intención funcional.
  - Incorporar un parámetro opcional `buscar` en los listados ORG para filtrar por `codigo` y/o `nombre` (y `razon_social` en empresa).
  - Definir endpoints específicos para recuperar la **estructura jerárquica completa** de departamentos y centros de costo en un solo árbol.
  - Diseñar y exponer un **submódulo ORG - Monedas**:
    - CRUD multi-tenant por empresa sobre `org_moneda`.
    - Endpoints sugeridos bajo `/api/v1/org/monedas`.
    - Filtros por `empresa_id`, `solo_activos`, `es_moneda_base`, `buscar` (por código/nombre).

- **Mejoras en validaciones**
  - En las operaciones de baja lógica:
    - Verificar que no existan registros activos dependientes críticos (por ejemplo, empleados activos con ese cargo o departamento).
  - En parámetros:
    - Ofrecer mecanismos (endpoints o lógica de servicio) para validar valores según `expresion_validacion` y `opciones_validas`.
  - En multi-moneda:
    - Garantizar que solo exista una moneda base activa por empresa (`es_moneda_base = 1`).
    - Validar que `moneda_base_id` en `org_empresa` siempre apunte a una moneda activa de esa empresa.

- **Mejoras en permisos**
  - Alinear la API con el catálogo RBAC:
    - Usar los permisos `org.<recurso>.eliminar` en los nuevos endpoints de baja lógica.
    - Definir permisos específicos para moneda (`org.moneda.leer/crear/actualizar/eliminar`) y asociarlos a roles adecuados.
  - Documentar qué roles deben tener acceso a operaciones de eliminación/reactivación y a la administración de monedas (normalmente administradores financieros o de configuración).

- **Mejoras en filtros multi-tenant**
  - Para las nuevas operaciones (DELETE, reactivar, árbol, búsqueda, monedas), asegurar:
    - Filtros por `cliente_id` y `empresa_id` consistentes con lo ya existente.
    - Mensajes de error claros cuando se intenta acceder a recursos de otro tenant.

- **Mejoras en consistencia de API**
  - Mantener nomenclatura consistente de rutas (`/empresa`, `/sucursales`, `/centros-costo`, `/monedas`, etc.) y de parámetros (`empresa_id`, `solo_activos`, `buscar`).
  - Documentar en `DOC_FRONTEND_MODULO_ORG.md` tanto:
    - El comportamiento de baja lógica y de búsqueda en todas las entidades ORG.
    - El flujo recomendado para configurar **multi-moneda**: creación de monedas, definición de moneda base y activación de `maneja_multimoneda`.

---

## 14. Plan de implementación (priorizado)

### 14.1 Prioridad Alta

- **Implementar baja lógica explícita con DELETE**
  - **Qué**: endpoints `DELETE` para empresa, sucursal, centro de costo, departamento, cargo, parámetro.
  - **Endpoints afectados**: todos los recursos ORG (`/empresa`, `/sucursales`, `/centros-costo`, `/departamentos`, `/cargos`, `/parametros`).
  - **Entidades**: `org_empresa`, `org_sucursal`, `org_centro_costo`, `org_departamento`, `org_cargo`, `org_parametro_sistema`.
  - **Impacto**:
    - Clarifica la semántica de “eliminar” manteniendo soft delete.
    - Permite utilizar los permisos `*.eliminar` ya definidos en RBAC.

- **Implementar soporte completo de multi-moneda en ORG**
  - **Qué**:
    - Modelar `org_moneda` en el ORM (`OrgMonedaTable`) y crear queries/servicios correspondientes.
    - Exponer endpoints `/api/v1/org/monedas` con CRUD multi-tenant por empresa.
    - Extender `org_empresa` (modelos y endpoints) para usar `moneda_base_id` y `maneja_multimoneda` según el diseño Fase 4, manteniendo compatibilidad con `moneda_base` cuando sea necesario.
  - **Entidades**: `org_moneda`, `org_empresa` (campos de multi-moneda).
  - **Impacto**:
    - Alinea completamente el backend con la funcionalidad de multi-moneda prometida en los documentos oficiales.
    - Provee una fuente única de verdad para monedas que ya son referenciadas por otros módulos (FIN, PUR, SLS, HCM, etc.).

- **Documentar política de eliminación/desactivación y multi-moneda**
  - **Qué**: actualizar documentación (principalmente `DOC_FRONTEND_MODULO_ORG.md` y `MANUAL_USUARIO.md` sección ORG) explicando:
    - Que las entidades ORG no se borran físicamente.
    - Que la baja se realiza vía `es_activo = false` usando endpoints dedicados.
    - Cómo configurar multi-moneda correctamente (creación de monedas, definición de moneda base, activación de `maneja_multimoneda`).
  - **Impacto**: reduce ambigüedad y alinea expectativas de usuarios e integradores tanto para eliminación como para configuración monetaria.

### 14.2 Prioridad Media

- **Añadir endpoints de reactivación**
  - **Qué**: endpoints tipo `POST /api/v1/org/<recurso>/{id}/reactivar`.
  - **Entidades**: mismas entidades ORG.
  - **Impacto**:
    - Mejora la trazabilidad funcional (baja vs reactivación).
    - Facilita flujos de negocio donde se reactivan estructuras organizacionales.

- **Soporte de búsqueda textual en listados ORG**
  - **Qué**: parámetro `buscar` opcional en `GET` de empresa, sucursales, departamentos, cargos, centros de costo y parámetros.
  - **Impacto**:
    - Mejora significativa de UX para tenants con muchos registros.

- **Endpoints de árbol jerárquico**
  - **Qué**: endpoints para devolver árboles de departamentos y centros de costo.
  - **Impacto**:
    - Centraliza la lógica de armado de jerarquías en el backend.
    - Simplifica implementaciones en frontend y otros módulos (HCM, BDG, FIN).

### 14.3 Prioridad Baja

- **Validaciones avanzadas de parámetros**
  - **Qué**: opcionalmente, endpoints o servicios para:
    - Probar valores contra `expresion_validacion`.
    - Resolver parámetros efectivos combinando defaults y valores por empresa.
  - **Impacto**:
    - Mayor robustez en configuración, pero no es un requerimiento funcional explícito actual.

- **Refinar documentación de dependencias con otros módulos**
  - **Qué**: documentar en manuales de INV, PUR, SLS, FIN, HCM que:
    - Dependen de ORG para `empresa_id`, `sucursal_id`, `centro_costo_id`, etc.
  - **Impacto**:
    - Mejora la comprensión global del ERP, sin cambios funcionales inmediatos.

---

¿Deseas que proceda con la implementación de las mejoras recomendadas para el módulo ORG?

## 1. Resumen del módulo ORG

El módulo **ORG — Organización** es el **módulo base obligatorio** del ERP.  
Su objetivo, según `CATALOGO_MODULOS.md`, `MENU_NAVEGACION.md` y el `MANUAL_USUARIO.md`, es:

- **Definir la estructura organizacional** de un tenant:
  - **Empresa** (razón social, RUC, moneda base, parámetros globales).
  - **Sucursales** (sedes físicas y virtuales).
  - **Departamentos** (estructura jerárquica por áreas).
  - **Cargos** (puestos de trabajo).
  - **Centros de costo** (unidades para imputar gastos).
  - **Parámetros del sistema** (por módulo y, opcionalmente, por empresa).
- Servir como **fundamento para todos los demás módulos** (RRHH, FIN, MFG, LOG, etc.), que dependen de empresa, sucursal, departamento, cargo y centro de costo para operar.
- Mantener **aislamiento multi-tenant**:
  - Cada registro pertenece a un `cliente_id` (tenant).
  - Muchas entidades se escopan por `(cliente_id, empresa_id)`.

A nivel de backend, ORG está implementado como:

- **Tablas SQLAlchemy Core**: `OrgEmpresaTable`, `OrgCentroCostoTable`, `OrgSucursalTable`, `OrgDepartamentoTable`, `OrgCargoTable`, `OrgParametroSistemaTable` en `tables_org.py`, todas con `cliente_id` y (salvo parámetros) `empresa_id` obligatorio.
- **Queries SQLAlchemy Core**: en `app/infrastructure/database/queries/org/*.py`, con filtro **estricto por `cliente_id`** y filtros opcionales por `empresa_id`.
- **Servicios de aplicación**: en `app/modules/org/application/services/*.py`, que transforman filas en schemas Pydantic (Read) y encapsulan reglas como “no aceptar `cliente_id` desde el body”.
- **Endpoints FastAPI**: en `app/modules/org/presentation/endpoints_*.py`, montados bajo `/api/v1/org/...` (ver `DOC_FRONTEND_MODULO_ORG.md`), con:
  - Autenticación obligatoria.
  - RBAC por permisos (`require_permission("org.<recurso>.<accion>")`).
  - `client_id` siempre derivado de `current_user.cliente_id`.

En conjunto, la implementación backend de ORG está **fuertemente alineada** con la documentación funcional y con el diseño multi-tenant del sistema.

---

## 2. Funcionalidades definidas en documentación

### 2.1 Según `MENU_NAVEGACION.md` (Módulo ORG)

Opciones de menú para ORG:

- **Mi Empresa**
  - Ver y editar datos de la empresa:
    - RUC/NIT, razón social, nombre comercial.
    - Logo, moneda, país, dirección fiscal, contactos.
- **Sucursales**
  - Gestionar sucursales con:
    - Dirección, teléfono, responsable.
    - Marcar sucursales como casa matriz / punto de venta / almacén.
- **Departamentos**
  - Crear estructura organizacional jerárquica por áreas:
    - Departamentos padre/hijo.
    - Asociación a sucursales y centros de costo (para HCM).
- **Cargos**
  - Definir puestos de trabajo:
    - Nombre y código de cargo.
    - Nivel jerárquico, área funcional, rango salarial y requisitos.
- **Centros de costo**
  - Configurar centros de costo para control de gastos:
    - Jerarquía (centro padre/hijo, nivel, ruta jerárquica).
    - Asociación con responsables y departamentos/sucursales.
- **Parámetros del sistema**
  - Configuración global:
    - Parámetros por módulo (`modulo_codigo`) y, opcionalmente, por empresa.
    - Soporte de distintos tipos de dato (texto, numérico, booleano, fecha, JSON).

### 2.2 Según `MANUAL_USUARIO.md` — 2.1 Módulo ORG

Flujo funcional descrito:

1. **Paso 1: Configurar Mi Empresa**
   - Navegar a: `ORG > Mi Empresa`.
   - Completar campos obligatorios: RUC/NIT, razón social, nombre comercial, tipo de empresa, moneda base, país.
   - Notas:
     - El RUC **no se puede cambiar** después (campo crítico).
     - Configurar logo, multimoneda, zona horaria, formato de fecha, idioma.
2. **Paso 2: Crear Sucursales**
   - Navegar a: `ORG > Sucursales > [+ Nueva Sucursal]`.
   - Definir código, nombre, dirección, teléfono, responsable.
   - Marcar una sucursal como **principal**.
   - Se sugiere crear sucursales “VIRTUALES” para e‑commerce.
3. **Paso 3: Definir Departamentos**
   - Navegar a: `ORG > Departamentos`.
   - Crear estructura jerárquica (Dirección General, Administración, Operaciones, Comercial, etc.).
   - Definir **códigos** de departamento (p.ej. `DIR-GRAL`, `ADMIN-FIN`).
   - Notas: departamentos se usan intensivamente en RRHH/HCM.
4. **Paso 4: Crear Cargos**
   - Navegar a: `ORG > Cargos`.
   - Crear cargos por área (Producción, Administración, Ventas).
   - Definir códigos de cargo (p.ej. `OPERARIO-CORTE`, `JEFE-VENTAS`).
5. **Paso 5: Configurar Centros de Costo**
   - Navegar a: `ORG > Centros de costo`.
   - Configurar centros de costo y su jerarquía:
     - Ejemplos: `CC-PRODUCCION`, `CC-ADMINISTRACION`, `CC-VENTAS`.
   - Asociar centros de costo con sucursales y departamentos donde aplique.
6. **Paso 6 (implícito): Configurar Parámetros del Sistema**
   - Configurar parámetros por módulo:
     - Métodos de costeo, afectación de IGV, número de decimales, etc.
   - Algunos parámetros son por empresa, otros globales al tenant.

### 2.3 Según `DOC_FRONTEND_MODULO_ORG.md`

El documento describe explícitamente la **API backend esperada**:

- **Base URL y autenticación**
  - Prefijo: `/api/v1/org/`.
  - Todas las rutas requieren **Bearer token**.
  - El backend obtiene el tenant desde el token y (en login) desde el Host.

- **Endpoints esperados por entidad**

  - **Empresa**
    - `GET /api/v1/org/empresa` — Listar empresas del tenant, con `solo_activos` (bool).
    - `GET /api/v1/org/empresa/{empresa_id}` — Detalle.
    - `POST /api/v1/org/empresa` — Crear (sin enviar `cliente_id` ni `empresa_id`).
    - `PUT /api/v1/org/empresa/{empresa_id}` — Actualizar.

  - **Sucursales**
    - `GET /api/v1/org/sucursales?empresa_id&solo_activos`.
    - `GET /api/v1/org/sucursales/{sucursal_id}`.
    - `POST /api/v1/org/sucursales`.
    - `PUT /api/v1/org/sucursales/{sucursal_id}`.

  - **Centros de costo**
    - `GET /api/v1/org/centros-costo?empresa_id&solo_activos`.
    - `GET /api/v1/org/centros-costo/{centro_costo_id}`.
    - `POST /api/v1/org/centros-costo`.
    - `PUT /api/v1/org/centros-costo/{centro_costo_id}`.

  - **Departamentos**
    - `GET /api/v1/org/departamentos?empresa_id&solo_activos`.
    - `GET /api/v1/org/departamentos/{departamento_id}`.
    - `POST /api/v1/org/departamentos`.
    - `PUT /api/v1/org/departamentos/{departamento_id}`.

  - **Cargos**
    - `GET /api/v1/org/cargos?empresa_id&solo_activos`.
    - `GET /api/v1/org/cargos/{cargo_id}`.
    - `POST /api/v1/org/cargos`.
    - `PUT /api/v1/org/cargos/{cargo_id}`.

  - **Parámetros del sistema**
    - `GET /api/v1/org/parametros?empresa_id&modulo_codigo&solo_activos`.
    - `GET /api/v1/org/parametros/{parametro_id}`.
    - `POST /api/v1/org/parametros`.
    - `PUT /api/v1/org/parametros/{parametro_id}`.

- **Schemas funcionales**:
  - Confirman campos obligatorios y opcionales por entidad (Empresa, Sucursal, Centro de costo, Departamento, Cargo, Parámetro).

**Conclusión funcional:**  
El módulo ORG debe proporcionar **CRUD completo** para las seis entidades mencionadas, filtrado por tenant (`cliente_id`) y, cuando aplica, por `empresa_id`, con parámetros de filtro adicionales (`solo_activos`, `modulo_codigo`).

---

## 3. Implementación actual detectada en backend (ORG)

### 3.1 Rutas y endpoints

Router principal ORG:

- Archivo: `app/modules/org/presentation/endpoints.py`
- Prefijo (vía `api_router` general): `/api/v1/org`.
- Sub‑routers incluidos:
  - `/org/empresa` → `endpoints_empresa.py`.
  - `/org/sucursales` → `endpoints_sucursales.py`.
  - `/org/centros-costo` → `endpoints_centros_costo.py`.
  - `/org/departamentos` → `endpoints_departamentos.py`.
  - `/org/cargos` → `endpoints_cargos.py`.
  - `/org/parametros` → `endpoints_parametros.py`.

#### Empresa

- Archivo: `app/modules/org/presentation/endpoints_empresa.py`
- Endpoints:
  - `GET ""` → `listar_empresas`
    - Ruta real: `GET /api/v1/org/empresa`.
    - Permisos: `require_permission("org.empresa.leer")`.
    - Tenancy:
      - `current_user: UsuarioReadWithRoles = Depends(require_permission(...))`.
      - `client_id = current_user.cliente_id`.
      - Llama a `empresa_service.list_empresas_servicio(client_id, solo_activos)`.
  - `GET "/{empresa_id}"` → `detalle_empresa`
    - `GET /api/v1/org/empresa/{empresa_id}`.
    - Permiso: `org.empresa.leer`.
    - Tenancy:
      - `client_id` desde `current_user.cliente_id`.
      - Llama a `empresa_service.get_empresa_servicio(client_id, empresa_id)`.
      - Convierte `NotFoundError` a `404`.
  - `POST ""` → `crear_empresa`
    - `POST /api/v1/org/empresa`.
    - Permiso: `org.empresa.crear`.
    - Body: `EmpresaCreate` (sin `cliente_id` ni `empresa_id`).
    - Tenancy:
      - `client_id = current_user.cliente_id`.
      - `empresa_service.create_empresa_servicio(client_id, data)`.
  - `PUT "/{empresa_id}"` → `actualizar_empresa`
    - `PUT /api/v1/org/empresa/{empresa_id}`.
    - Permiso: `org.empresa.actualizar`.
    - Body: `EmpresaUpdate` (parcial).
    - Tenancy:
      - `client_id = current_user.cliente_id`.
      - `empresa_service.update_empresa_servicio(client_id, empresa_id, data)`.

#### Sucursales

- Archivo: `app/modules/org/presentation/endpoints_sucursales.py`
- Endpoints:
  - `GET ""` → `listar_sucursales`
    - Ruta: `GET /api/v1/org/sucursales?empresa_id&solo_activos`.
    - Permiso: `org.sucursal.leer`.
    - Tenancy:
      - `client_id = current_user.cliente_id`.
      - `sucursal_service.list_sucursales_servicio(client_id, empresa_id, solo_activos)`.
  - `GET "/{sucursal_id}"` → `detalle_sucursal`
    - `GET /api/v1/org/sucursales/{sucursal_id}`.
    - Permiso: `org.sucursal.leer`.
    - Tenancy: `client_id` + `NotFoundError` → `404`.
  - `POST ""` → `crear_sucursal`
    - `POST /api/v1/org/sucursales`.
    - Permiso: `org.sucursal.crear`.
    - Body: `SucursalCreate` (incluye `empresa_id`).
  - `PUT "/{sucursal_id}"` → `actualizar_sucursal`
    - `PUT /api/v1/org/sucursales/{sucursal_id}`.
    - Permiso: `org.sucursal.actualizar`.

#### Centros de costo

- Archivo: `app/modules/org/presentation/endpoints_centros_costo.py`
- Endpoints:
  - `GET ""` → `listar_centros_costo`
    - `GET /api/v1/org/centros-costo?empresa_id&solo_activos`.
    - Permiso: `org.centro_costo.leer`.
    - Tenancy: `client_id = current_user.cliente_id`.
  - `GET "/{centro_costo_id}"` → `detalle_centro_costo`.
  - `POST ""` → `crear_centro_costo`.
    - Permiso: `org.centro_costo.crear`.
    - Body: `CentroCostoCreate` (incluye `empresa_id`).
  - `PUT "/{centro_costo_id}"` → `actualizar_centro_costo`.
    - Permiso: `org.centro_costo.actualizar`.

#### Departamentos

- Archivo: `app/modules/org/presentation/endpoints_departamentos.py`
- Endpoints:
  - `GET ""` → `listar_departamentos`
    - `GET /api/v1/org/departamentos?empresa_id&solo_activos`.
    - Permiso: `org.departamento.leer`.
  - `GET "/{departamento_id}"` → `detalle_departamento`.
  - `POST ""` → `crear_departamento`.
    - Permiso: `org.departamento.crear`.
    - Body: `DepartamentoCreate` (incluye `empresa_id`).
  - `PUT "/{departamento_id}"` → `actualizar_departamento`.
    - Permiso: `org.departamento.actualizar`.

#### Cargos

- Archivo: `app/modules/org/presentation/endpoints_cargos.py`
- Endpoints:
  - `GET ""` → `listar_cargos`
    - `GET /api/v1/org/cargos?empresa_id&solo_activos`.
    - Permiso: `org.cargo.leer`.
  - `GET "/{cargo_id}"` → `detalle_cargo`.
  - `POST ""` → `crear_cargo`.
    - Permiso: `org.cargo.crear`.
  - `PUT "/{cargo_id}"` → `actualizar_cargo`.
    - Permiso: `org.cargo.actualizar`.

#### Parámetros del sistema

- Archivo: `app/modules/org/presentation/endpoints_parametros.py`
- Endpoints:
  - `GET ""` → `listar_parametros`
    - `GET /api/v1/org/parametros?empresa_id&modulo_codigo&solo_activos`.
    - Permiso: `org.parametro.leer`.
  - `GET "/{parametro_id}"` → `detalle_parametro`.
  - `POST ""` → `crear_parametro`.
    - Permiso: `org.parametro.crear`.
  - `PUT "/{parametro_id}"` → `actualizar_parametro`.
    - Permiso: `org.parametro.actualizar`.

### 3.2 Servicios de aplicación (ORG)

Para cada entidad existe un servicio en `app/modules/org/application/services/`:

- `empresa_service.py` → `list_empresas_servicio`, `get_empresa_servicio`, `create_empresa_servicio`, `update_empresa_servicio`.
- `sucursal_service.py` → análogo para sucursales.
- `centro_costo_service.py` → para centros de costo.
- `departamento_service.py` → para departamentos.
- `cargo_service.py` → para cargos.
- `parametro_service.py` → para parámetros.

Patrón común:

- Reciben **explícitamente** `client_id: UUID`.
- Llaman a las queries del módulo ORG (ver siguiente sección).
- Transforman dicts en schemas Read Pydantic.
- Lanza `NotFoundError` cuando corresponde.

### 3.3 Queries SQL (ORG)

Ubicación: `app/infrastructure/database/queries/org/*.py`.

Para cada entidad:

- **Empresa** (`empresa_queries.py`)
  - `list_empresas(client_id, solo_activos)`:
    - `WHERE OrgEmpresaTable.c.cliente_id == client_id`.
    - `solo_activos` → `es_activo == True`.
  - `get_empresa_by_id(client_id, empresa_id)`:
    - `WHERE cliente_id == client_id AND empresa_id == empresa_id`.
  - `create_empresa(client_id, data)`:
    - Fuerza `payload["cliente_id"] = client_id`.
    - Genera `empresa_id` (UUID) si no viene.
  - `update_empresa(...)`:
    - `WHERE cliente_id == client_id AND empresa_id == empresa_id`.

- **Sucursales** (`sucursal_queries.py`), **Centros de costo** (`centro_costo_queries.py`),  
  **Departamentos** (`departamento_queries.py`), **Cargos** (`cargo_queries.py`),  
  **Parámetros** (`parametro_queries.py`):
  - Todas las funciones de lista:
    - Filtran por `OrgXxxTable.c.cliente_id == client_id`.
    - Permiten **filtro opcional** por `empresa_id` (salvo parámetros, donde `empresa_id` puede ser `NULL`).
    - Filtran por `es_activo == True` cuando `solo_activos` es `True`.
  - Funciones de detalle:
    - `WHERE cliente_id == client_id AND <id> == <id>`.
  - Funciones de creación:
    - Forzan `cliente_id` desde parámetro de función, **ignorando cualquier valor que viniera en el body**.
  - Funciones de actualización:
    - `WHERE cliente_id == client_id` y el `id` correspondiente.
    - Actualizan `fecha_actualizacion`.

### 3.4 Modelos de base de datos (ORG)

Ubicación: `app/infrastructure/database/tables_erp/tables_org.py`.

Todas las tablas ORG comparten:

- `cliente_id` obligatorio (sin FK, para soportar BD dedicada).
- `empresa_id` obligatorio para sucursales, centros de costo, departamentos, cargos.
- **Constraints multi-tenant**:
  - Únicos por `(cliente_id, empresa_id, codigo)` para sucursal, centro_costo, departamento, cargo.
  - Únicos por `(cliente_id, ruc)` y `(cliente_id, codigo_empresa)` para empresa.
  - Parámetros: Unique por `(cliente_id, empresa_id, modulo_codigo, codigo_parametro)`.
- Índices por `empresa_id` y flag de estado (`es_activo`), facilitando filtros por empresa.

---

## 4. Matriz funcionalidad vs implementación

### 4.1 Leyenda

- **✔ Implementada completamente**: Existe CRUD funcional según docs, con multi-tenant y RBAC correctos.
- **⚠ Implementada parcialmente**: Operaciones principales existen pero falta alguna operación/documentación / endpoint auxiliar (p.ej. DELETE explícito).
- **✖ No implementada**: No hay endpoint ni lógica que la cubra.

### 4.2 Matriz por entidad / funcionalidad

| Entidad / Funcionalidad                                    | Documentación (MENU / MANUAL / DOC_FRONTEND)                                | Implementación backend detectada                             | Estado | Comentarios clave |
|------------------------------------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------|--------|-------------------|
| Empresa – Listar empresas del tenant                       | `GET /api/v1/org/empresa` con `solo_activos`                              | `listar_empresas` + `list_empresas` (filtro `cliente_id`)    | ✔      | Alineado con docs, filtro `solo_activos` y tenant estricto. |
| Empresa – Detalle de empresa                               | `GET /api/v1/org/empresa/{empresa_id}`                                    | `detalle_empresa` + `get_empresa_by_id`                     | ✔      | `NotFoundError` → 404, siempre confinado por `cliente_id`. |
| Empresa – Crear empresa                                    | `POST /api/v1/org/empresa` (sin enviar `cliente_id`/`empresa_id`)         | `crear_empresa` + `create_empresa`                          | ✔      | `cliente_id` se forza desde contexto; `empresa_id` UUID generado. |
| Empresa – Actualizar empresa                               | `PUT /api/v1/org/empresa/{empresa_id}`                                    | `actualizar_empresa` + `update_empresa`                     | ✔      | No hay PATCH explícito; PUT parcial vía `exclude_unset`. |
| Empresa – Eliminar empresa                                 | No se explicita DELETE; se habla de “es_activo”                           | **No hay DELETE** en endpoints                               | ⚠      | Eliminación lógica se puede hacer vía `es_activo` en PUT, pero no hay endpoint dedicado ni doc explícita de “eliminar/desactivar empresa”. |
| Sucursal – Listar (con filtro por empresa)                 | `GET /api/v1/org/sucursales?empresa_id&solo_activos`                      | `listar_sucursales` + `list_sucursales`                     | ✔      | Coincide exactamente con DOC_FRONTEND; ordenado por código. |
| Sucursal – Detalle                                         | `GET /api/v1/org/sucursales/{sucursal_id}`                                | `detalle_sucursal` + `get_sucursal_by_id`                   | ✔      | Tenant estricto vía `cliente_id`. |
| Sucursal – Crear                                           | `POST /api/v1/org/sucursales`                                             | `crear_sucursal` + `create_sucursal`                        | ✔      | `empresa_id` obligatorio en schema; `cliente_id` forzado. |
| Sucursal – Actualizar                                      | `PUT /api/v1/org/sucursales/{sucursal_id}`                                | `actualizar_sucursal` + `update_sucursal`                   | ✔      | Soporta actualización de flags (casa matriz, activa, etc.). |
| Sucursal – Eliminar / Desactivar                           | Manual habla de “Es principal” y `es_activo`, no de eliminar definitiva   | Sin DELETE; `es_activo` actualizable vía PUT                | ⚠      | Desactivación posible (PUT `es_activo=False`), pero no hay endpoint específico ni doc de “borrar sucursal”. |
| Centro de costo – Listar                                   | `GET /api/v1/org/centros-costo?empresa_id&solo_activos`                   | `listar_centros_costo` + `list_centros_costo`               | ✔      | Filtro multi-tenant/empresa correcto. |
| Centro de costo – Detalle                                  | `GET /api/v1/org/centros-costo/{centro_costo_id}`                         | `detalle_centro_costo` + `get_centro_costo_by_id`           | ✔      | Tenant estricto. |
| Centro de costo – Crear                                    | `POST /api/v1/org/centros-costo`                                          | `crear_centro_costo` + `create_centro_costo`                | ✔      | Campos coinciden con schema funcional. |
| Centro de costo – Actualizar                               | `PUT /api/v1/org/centros-costo/{centro_costo_id}`                         | `actualizar_centro_costo` + `update_centro_costo`           | ✔      | Actualiza jerarquía, responsable, vigencia. |
| Centro de costo – Eliminar / Desactivar                    | Manual recomienda centros estables; no documento explícito de delete      | Sin DELETE; `es_activo` actualizable                         | ⚠      | Se asume baja lógica via `es_activo`; falta endpoint/documento específico. |
| Departamento – Listar                                      | `GET /api/v1/org/departamentos?empresa_id&solo_activos`                   | `listar_departamentos` + `list_departamentos`               | ✔      | Ordenado por código; soporte jerarquía. |
| Departamento – Detalle                                     | `GET /api/v1/org/departamentos/{departamento_id}`                         | `detalle_departamento` + `get_departamento_by_id`           | ✔      | Multi-tenant correcto. |
| Departamento – Crear                                       | `POST /api/v1/org/departamentos`                                          | `crear_departamento` + `create_departamento`                | ✔      | Soporta padre, nivel, tipo, centro costo, sucursal. |
| Departamento – Actualizar                                  | `PUT /api/v1/org/departamentos/{departamento_id}`                         | `actualizar_departamento` + `update_departamento`           | ✔      | Adecuado para mantenimiento de estructura organizacional. |
| Departamento – Eliminar / Desactivar                       | Manual no detalla delete, sí relevancia de departamentos                  | Via `es_activo` en update, sin DELETE                       | ⚠      | Misma situación que centros y sucursales. |
| Cargo – Listar                                             | `GET /api/v1/org/cargos?empresa_id&solo_activos`                          | `listar_cargos` + `list_cargos`                             | ✔      | Multi-tenant correcto. |
| Cargo – Detalle                                            | `GET /api/v1/org/cargos/{cargo_id}`                                       | `detalle_cargo` + `get_cargo_by_id`                         | ✔      | Tenant estricto. |
| Cargo – Crear                                              | `POST /api/v1/org/cargos`                                                 | `crear_cargo` + `create_cargo`                              | ✔      | Campos alineados a doc (código, nombre, categoría, etc.). |
| Cargo – Actualizar                                         | `PUT /api/v1/org/cargos/{cargo_id}`                                       | `actualizar_cargo` + `update_cargo`                         | ✔      | Permite cambios en jerarquía y estado. |
| Cargo – Eliminar / Desactivar                              | No hay mención de borrar cargos, sí de uso intensivo en RRHH              | `es_activo` vía PUT, sin DELETE explícito                   | ⚠      | Soft delete implícito; faltan semántica y doc explícita. |
| Parámetro – Listar (por empresa y módulo)                  | `GET /api/v1/org/parametros?empresa_id&modulo_codigo&solo_activos`        | `listar_parametros` + `list_parametros`                     | ✔      | Filtro por `empresa_id` y `modulo_codigo`, exactamente como docs. |
| Parámetro – Detalle                                        | `GET /api/v1/org/parametros/{parametro_id}`                               | `detalle_parametro` + `get_parametro_by_id`                 | ✔      | Tenant estricto. |
| Parámetro – Crear                                          | `POST /api/v1/org/parametros`                                             | `crear_parametro` + `create_parametro`                      | ✔      | Soporta todos los tipos de valor y flags (`es_editable`, etc.). |
| Parámetro – Actualizar                                     | `PUT /api/v1/org/parametros/{parametro_id}`                               | `actualizar_parametro` + `update_parametro`                 | ✔      | Permite mantenimiento completo del parámetro. |
| Parámetro – Eliminar / Desactivar                          | No se listan operaciones de borrado en docs                               | `es_activo` modificable, sin DELETE explícito               | ⚠      | De nuevo, baja lógica sin endpoint dedicado. |

**Resumen de la matriz:**  
- Todas las **operaciones CRUD básicas** (listar, detalle, crear, actualizar) están **implementadas y alineadas** con la documentación para las seis entidades.  
- Las operaciones de **eliminación** se gestionan indirectamente mediante el campo `es_activo` (soft delete), pero **no existen endpoints DELETE** ni la documentación de usuario lo menciona explícitamente, por lo que se marca como **implementación parcial**.

---

## 5. Endpoints faltantes (según documentación)

La documentación no exige explícitamente endpoints DELETE, pero sí pide en términos generales “gestionar” las entidades y, en el checklist de auditoría, se solicita verificar **crear / listar / detalle / actualizar / eliminar / activar o desactivar**.

Desde esa perspectiva, y respetando el diseño actual de soft delete (`es_activo`), se pueden considerar **faltantes funcionales opcionales**:

- **Empresa**
  - Endpoint sugerido: `DELETE /api/v1/org/empresa/{empresa_id}`.
  - Operación: marcar `es_activo = false` (sin borrar físicamente).
  - Entidad: `org_empresa`.
- **Sucursales**
  - Endpoint sugerido: `DELETE /api/v1/org/sucursales/{sucursal_id}`.
  - Operación: baja lógica (`es_activo = false`).
  - Entidad: `org_sucursal`.
- **Centros de costo**
  - Endpoint sugerido: `DELETE /api/v1/org/centros-costo/{centro_costo_id}`.
  - Operación: baja lógica respetando integridad con FIN/BDG.
  - Entidad: `org_centro_costo`.
- **Departamentos**
  - Endpoint sugerido: `DELETE /api/v1/org/departamentos/{departamento_id}`.
  - Operación: baja lógica, validando que no existan contratos/empleados activos vinculados.
  - Entidad: `org_departamento`.
- **Cargos**
  - Endpoint sugerido: `DELETE /api/v1/org/cargos/{cargo_id}`.
  - Operación: baja lógica, garantizando que no haya empleados activos con ese cargo.
  - Entidad: `org_cargo`.
- **Parámetros del sistema**
  - Endpoint sugerido: `DELETE /api/v1/org/parametros/{parametro_id}`.

En todos los casos, la implementación recomendada sería:

- Un **DELETE** que internamente haga `UPDATE ... SET es_activo = 0` y registre `fecha_actualizacion`.
- Mismo patrón de permisos ya usado: `org.<recurso>.eliminar`.
- Mismo filtrado multi-tenant (`cliente_id`) que los endpoints ya existentes.

---

## 6. Endpoints incompletos o mejorables

Aun cuando la funcionalidad core está cubierta, se identifican algunos puntos de mejora:

- **Falta de endpoints específicos de reactivación**
  - Actualmente, la reactivación se puede hacer vía `PUT` enviando `es_activo = true`, pero no hay endpoints semánticamente claros como:
    - `POST /api/v1/org/empresa/{id}/reactivar`.
    - `POST /api/v1/org/centros-costo/{id}/reactivar`.
  - **Impacto:** Bajo; funcionalmente se puede hacer con `PUT`, pero la API no expone explícitamente la operación de “reactivar”.

- **Búsqueda textual (buscar por nombre/código)**
  - Los listados se ordenan por código o razón social, pero **no exponen un parámetro de búsqueda** (`buscar` o similar) en ORG, a diferencia de otros módulos (por ejemplo, algunos módulos usan `buscar` en sus queries).
  - Manual y menú no lo exigen explícitamente para ORG, pero a nivel de UX sería coherente tener:
    - `?buscar=...` para empresas, sucursales, departamentos, cargos, centros de costo.
  - **Estado:** No es un incumplimiento de la documentación, pero sí una **omisión funcional razonable** para UX futura.

- **Operaciones de reporte/resumen**
  - No existen endpoints ORG específicos para:
    - Contar número de sucursales por empresa.
    - Obtener el árbol completo de departamentos o centros de costo en una sola llamada.
  - El manual muestra estructuras jerárquicas, pero no detalla cómo deben recuperarse (varias llamadas vs. árbol).

En resumen, los endpoints actuales **cumplen** la funcionalidad esencial, pero hay espacio para enriquecer la API con **operaciones semánticas** (eliminar, reactivar, búsqueda, árboles jerárquicos).

---

## 7. Validación multi-tenant (seguridad)

### 7.1 Filtrado por `cliente_id`

En todas las queries ORG se observa el patrón:

- `WHERE <tabla>.cliente_id == client_id`.
- `client_id` siempre proviene de:
  - `current_user.cliente_id` (en endpoints), y
  - se pasa explícitamente a servicios y queries.
- Funciones de detalle (`get_*_by_id`) siempre incluyen `cliente_id` en el `WHERE`, evitando leer registros de otros tenants.

### 7.2 Filtrado por `empresa_id`

- En listados (`list_sucursales`, `list_centros_costo`, `list_departamentos`, `list_cargos`, `list_parametros`) el filtro `empresa_id` es **opcional**, justo como dictan los docs:
  - Si `empresa_id` se proporciona, se restringe a esa empresa.
  - Si no se proporciona, se listan entidades de todas las empresas del tenant.
- A nivel de modelo, `empresa_id` es **NOT NULL** para todas las entidades que son por empresa (sucursal, centro_costo, departamento, cargo).  
  Esto asegura que:
  - No existan centros de costo “huérfanos” (sin empresa).
  - La pertenencia a empresa es inequívoca.

### 7.3 RBAC y permisos

- Cada endpoint ORG está protegido por **permisos de negocio**:
  - `org.empresa.leer/crear/actualizar`.
  - `org.sucursal.leer/crear/actualizar`.
  - `org.centro_costo.leer/crear/actualizar`.
  - `org.departamento.leer/crear/actualizar`.
  - `org.cargo.leer/crear/actualizar`.
  - `org.parametro.leer/crear/actualizar`.
- `UsuarioReadWithRoles` incluye la lista de `permisos: List[str]` y `require_permission` verifica que el usuario tenga el permiso requerido.
- No se observan endpoints ORG públicos ni accesibles sin permisos.

### 7.4 Riesgos multi-tenant específicos

- **Cruces indirectos con otros módulos:**  
  ORG se usa como referencia en muchas otras tablas (HCM, FIN, MFG, etc.), pero esto se audita en otros módulos; en ORG específicamente:
  - Todas las operaciones se circunscriben a `(cliente_id, empresa_id)` y al ID primario correspondiente.
  - No se permite filtrar por `cliente_id` desde el frontend; siempre va desde el token.
- **Conclusión de seguridad multi-tenant (módulo ORG):**  
  La implementación es **sólida y coherente** con el diseño multi-tenant del sistema, sin hallazgos de fuga de datos entre tenants dentro del módulo ORG.

---

## 8. Riesgos e inconsistencias funcionales detectadas (módulo ORG)

- **Eliminación lógica vs. falta de endpoints DELETE**
  - Riesgo: ambigüedad funcional. El manual habla de gestión de entidades, pero no de borrados; la base de datos tiene `es_activo` para todas las entidades ORG.
  - Consecuencia:
    - Frontend podría implementar “eliminación” cambiando `es_activo` vía PUT, pero esto no está documentado explícitamente.
    - Sin endpoints DELETE, integradores externos pueden asumir que no se pueden borrar entidades.

- **Ausencia de búsqueda textual (`buscar`) en ORG**
  - No es un incumplimiento estricto de documentación, pero sí un **gap de UX**:
    - Listas largas de departamentos, cargos o centros de costo serían difíciles de navegar sin filtro textual.

- **No hay endpoints de lectura de árbol completo (jerarquías)**
  - El manual muestra árboles de departamentos y sugiere jerarquías de centros de costo.
  - Actualmente, el backend expone sólo listados planos (con `departamento_padre_id`, `centro_costo_padre_id`), dejando al frontend la responsabilidad de armar árboles.
  - No es incorrecto, pero podría considerarse una **funcionalidad documentada implícita** (ver la estructura jerárquica) no directamente soportada por un endpoint específico.

- **Parámetros sin endpoint de “evaluación”**
  - ORG expone CRUD de parámetros, pero no endpoints para:
    - Validar valores contra `expresion_validacion`.
    - Resolver parámetros efectivos (ej. combinación de defaults + valores por empresa).
  - Esto, sin embargo, no está explicitado en la documentación como funcionalidad esperada del módulo ORG.

**En síntesis:**  
No se han encontrado inconsistencias graves entre la documentación funcional y la implementación backend del módulo ORG. Las diferencias detectadas son, en su mayoría, **oportunidades de mejora** y no brechas críticas.

---

## 9. Plan de implementación recomendado (sin escribir código)

A la luz de la auditoría, se recomienda el siguiente plan incremental:

### 9.1 Endpoints para baja lógica (eliminar / desactivar)

Para cada entidad ORG:

- **Diseñar endpoints DELETE semánticamente claros**:
  - `DELETE /api/v1/org/empresa/{empresa_id}`.
  - `DELETE /api/v1/org/sucursales/{sucursal_id}`.
  - `DELETE /api/v1/org/centros-costo/{centro_costo_id}`.
  - `DELETE /api/v1/org/departamentos/{departamento_id}`.
  - `DELETE /api/v1/org/cargos/{cargo_id}`.
  - `DELETE /api/v1/org/parametros/{parametro_id}`.
- Implementación conceptual:
  - Validar existencia con `get_*_by_id(client_id, id)`.
  - Setear `es_activo = False` y `fecha_actualizacion = now()`.
  - Mantener logs/auditoría a través del módulo AUD.
- RBAC:
  - Usar permisos `org.<recurso>.eliminar` y mapearlos en RBAC/seed de permisos.

### 9.2 Opciones de búsqueda textual

Agregar parámetro opcional `buscar` en los listados ORG:

- `GET /api/v1/org/empresa?buscar=...`.
- `GET /api/v1/org/sucursales?empresa_id&buscar=...`.
- `GET /api/v1/org/departamentos?empresa_id&buscar=...`.
- `GET /api/v1/org/cargos?empresa_id&buscar=...`.
- `GET /api/v1/org/centros-costo?empresa_id&buscar=...`.
- `GET /api/v1/org/parametros?empresa_id&modulo_codigo&buscar=...`.

Lógica sugerida:

- Filtrar por campos clave (`codigo`, `nombre`, `razon_social`, etc.) con `ILIKE`.
- Mantener siempre `cliente_id` como filtro principal.

### 9.3 Endpoints de árbol jerárquico

Para mejorar la UX descrita en el manual (estructuras jerárquicas), se recomienda:

- Añadir endpoints tipo:
  - `GET /api/v1/org/departamentos/arbol?empresa_id=...`.
  - `GET /api/v1/org/centros-costo/arbol?empresa_id=...`.
- Respuesta:
  - Estructuras anidadas (padre→hijos) construidas en backend usando los campos `*_padre_id` y `nivel`.
- Beneficio:
  - Simplifica la lógica en frontend.
  - Permite reutilizar la misma estructura en otros módulos (HCM, FIN, BDG).

### 9.4 Documentar explícitamente la política de eliminación

Actualizar la documentación funcional (DOC_FRONTEND_MODULO_ORG y MANUAL_USUARIO) para que:

- Aclare que:
  - **No se hace delete físico** de empresas, sucursales, centros de costo, departamentos, cargos, parámetros.
  - La baja se gestiona mediante `es_activo = false`.
- Describa:
  - Cómo reactivar registros (`es_activo = true` vía PUT).
  - Qué implicancias tiene desactivar una empresa/sucursal/centro de costo en otros módulos.

### 9.5 Confirmar alineación RBAC para operaciones nuevas

Si se agregan endpoints DELETE y/o REACTIVAR:

- Actualizar:
  - Seed de permisos (`SEED_PERMISOS_RBAC.sql`).
  - Documentación de RBAC (por ejemplo, `rbac_patterns_and_conventions.md`).
- Verificar:
  - Que el rol Administrador del cliente tenga los nuevos permisos asignados por defecto (o vía script de seed), manteniendo la experiencia actual.

---

**Conclusión final de la auditoría (módulo ORG):**

- La implementación backend del módulo ORG **cubre completamente las funcionalidades declaradas** en `MENU_NAVEGACION.md`, `CATALOGO_MODULOS.md`, `MANUAL_USUARIO.md` (sección ORG) y `DOC_FRONTEND_MODULO_ORG.md`, en lo relativo a:
  - CRUD de Empresa, Sucursales, Departamentos, Cargos, Centros de Costo y Parámetros.
  - Seguridad multi-tenant (`cliente_id`, `empresa_id`).
  - Protección con RBAC de negocio.
- Las diferencias encontradas son **menores y mejorables** (endpoints semánticos de baja/reactivación, búsqueda textual, árboles jerárquicos), y no representan una brecha crítica frente a los requerimientos funcionales actuales.

