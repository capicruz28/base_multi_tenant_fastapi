# Diagnóstico de Auto-Decoración RBAC

**Fecha:** 2026-02-18  
**Contexto:** Análisis técnico de por qué los endpoints listados en `docs/rbac_endpoints_missing_permissions.md` no pueden ser decorados automáticamente con RBAC de forma segura, al mismo nivel que los ~51 endpoints que ya tienen `require_permission` / `RequirePermission`.

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|--------|--------|
| **Endpoints ya decorados con permiso RBAC** | ~51 (org, modulos-menus/plantillas/secciones/cliente_modulo/modulos, rbac roles/permisos-catalogo, aud, svc parcial, tkt, dms, wfl, mfg ordenes_produccion, bi, users) |
| **Endpoints sin decorador de permiso** | 350+ (HCM, LOG, INV, FIN, PUR, SLS, etc.) |
| **Porcentaje automatizable sin riesgo** | **~15–25%** (solo CRUD estándar con path y módulo inequívocos) |
| **Porcentaje automatizable con heurística** | **~40–50%** (CRUD con prefijos anidados resueltos) |
| **Requieren revisión humana** | **~35–45%** (acciones custom, permisos por diseño, recursos anidados/ambiguos) |

**Riesgos detectados si se automatiza al 100% sin criterios:**

1. **Permisos incorrectos por diseño:** En ORG todos los recursos (empresa, departamentos, cargos, sucursales, etc.) usan el mismo permiso `org.area.leer/crear/actualizar`. Un decorador que infiera por path generaría `org.empresa.leer`, `org.departamento.leer`, etc., rompiendo el modelo de permisos acordado.
2. **Acciones no CRUD:** Módulos usa `modulos.menu.administrar` para PUT, DELETE, activar, desactivar, reordenar, duplicar. No hay mapeo HTTP→accion 1:1.
3. **Path incompleto en tiempo de análisis:** El archivo que define la ruta (ej. `endpoints_empleados.py`) solo ve `""` o `"/{empleado_id}"`; el prefijo `/hcm` y el recurso `/empleados` vienen de `api.py` y del `include_router` del módulo. Sin grafo de routers no se puede inferir el permiso de forma fiable.
4. **Dependencias duales:** Varios endpoints usan `require_admin` + `require_permission`. Una herramienta que solo inyecte `require_permission` podría dejar comportamiento correcto, pero una que reemplace o reordene dependencias podría romper la semántica (ej. exigir permiso pero no rol Administrador donde sí se requiere).

---

## 2. Categorías de bloqueo

### 2.1 Problemas estructurales del router

#### 2.1.1 Prefixes anidados

La ruta final de un endpoint se construye en **varios niveles**:

1. **`app/main.py`** (o equivalente): monta `api_router` con un prefijo global (ej. `/api/v1`).
2. **`app/api/v1/api.py`**: hace `include_router(hcm_endpoints.router, prefix="/hcm", ...)`. El **módulo** (`hcm`) solo existe aquí.
3. **`app/modules/hcm/presentation/endpoints.py`**: hace `include_router(empleados_router, prefix="/empleados", ...)`. El **recurso** (`empleados`) solo existe aquí.
4. **`app/modules/hcm/presentation/endpoints_empleados.py`**: define `@router.get("")`, `@router.get("/{empleado_id}")`, etc. Este archivo **no** conoce ni `/hcm` ni `/empleados`.

Por tanto, un analizador que solo lea `endpoints_empleados.py` no puede saber que el permiso debe ser `hcm.empleado.*`: no tiene el prefijo del módulo ni el nombre del recurso. Esa información está en otros archivos. Una auto-decoración **por archivo** sin contexto del árbol de routers es insegura (riesgo de permisos genéricos o erróneos).

#### 2.1.2 Múltiples `include_router` por módulo

Cada módulo de negocio (HCM, LOG, INV, FIN, etc.) tiene un único `endpoints.py` que incluye **varios** sub-routers, cada uno con su propio `prefix`. Ejemplo (HCM):

```python
router.include_router(empleados_router, prefix="/empleados", ...)
router.include_router(planilla_detalle_router, prefix="/planilla-detalle", ...)
```

Para saber qué prefijo aplica a cada handler hay que:

- Resolver qué router está definido en qué archivo.
- Saber en qué `include_router` se usa ese archivo y con qué `prefix`.

Eso implica un **análisis de grafo de imports y de llamadas a `include_router`**, no solo del archivo del handler.

#### 2.1.3 Sin routers dinámicos

No se detectan routers creados en runtime (ej. por configuración). El bloqueo no viene de dinamismo, sino de la **dispersión de la información de path** entre varios módulos y archivos.

#### 2.1.4 Imports cruzados

Las dependencias RBAC viven en `app.core.authorization.rbac` y `app.api.deps`. Los endpoints importan desde ahí. No hay problema de imports circulares para decorar; el bloqueo es de **inferencia** (qué string de permiso poner), no de ubicación del código.

---

### 2.2 Problemas de inferencia de permisos

#### 2.2.1 Rutas no CRUD y acciones custom

En el proyecto, varios endpoints **no** siguen el mapeo estándar GET→leer, POST→crear, PUT→actualizar, DELETE→eliminar:

- **Modulos (menús):**  
  - Crear, actualizar, eliminar, activar, desactivar, reordenar, duplicar → todos usan **`modulos.menu.administrar`**.  
  - No hay permiso `modulos.menu.crear` ni `modulos.menu.actualizar` en uso.
- **Modulos (plantillas):**  
  - Validar JSON, preview de aplicación → `modulos.menu.leer` o `administrar` según el caso.
- **RBAC (roles):**  
  - Asignar permisos a un rol → `admin.rol.actualizar` (no `admin.rol.asignar` en el string en algunos puntos; en users sí existe `admin.rol.asignar`).
- **BI (reportes):**  
  - Crear y otro endpoint de creación comparten `bi.reporte.crear`; un heurístico puro por método HTTP podría duplicar o equivocar el permiso.

Un decorador automático que solo mapee método HTTP → acción generaría permisos que **no existen en el catálogo** (ej. `modulos.menu.actualizar`) o que no coinciden con la política real (todo bajo `administrar`).

#### 2.2.2 Recursos ambiguos

- **Un mismo router, varios recursos:**  
  En `endpoints_asientos.py` (FIN) conviven:
  - Rutas de **asiento:** `""`, `"/{asiento_id}"`.
  - Rutas de **detalle de asiento:** `"/{asiento_id}/detalles"`, `"/detalles/{asiento_detalle_id}"`.
  Un inferidor por “último segmento de path” podría mezclar recurso `asiento` y `asiento_detalle` o no distinguir correctamente cuál es el recurso “principal” del endpoint.
- **Path con parámetros:**  
  Rutas como `GET /stock/producto/{producto_id}/almacen/{almacen_id}` no tienen un único “recurso” en el path; el recurso lógico es “stock”, pero el path no es estándar CRUD.
- **Singular/plural:**  
  Algunos prefijos son plural (`empleados`, `planillas`), otros compuestos (`planilla-detalle`, `guias-remision`). Singularizar y convertir a snake_case para el permiso requiere reglas consistentes y excepciones (ej. `vacaciones` ya en plural en el path).

#### 2.2.3 Conflictos de naming y permisos por diseño

- **ORG:**  
  Empresa, departamentos, parametros, centros_costo, cargos, sucursales usan **el mismo permiso** `org.area.leer`, `org.area.crear`, `org.area.actualizar`. No se usa `org.empresa.leer` ni `org.departamento.leer`. Es una decisión de diseño: un solo “área” de permisos para toda la organización.  
  Cualquier auto-decoración que infiera recurso por path generaría permisos distintos y **rompería** el modelo actual (y probablemente el catálogo en BD).
- **Permisos en español:**  
  El catálogo usa acciones en español: `leer`, `crear`, `actualizar`, `eliminar`, `administrar`, `asignar`. Cualquier herramienta que genere códigos en inglés (`read`, `create`, …) sin alineación al catálogo dejaría permisos que no existen o no se asignan.

---

### 2.3 Problemas técnicos de FastAPI

#### 2.3.1 Dependencias existentes

Todos los endpoints protegidos tienen al menos:

- `current_user: ... = Depends(get_current_active_user)`  
  o  
- `dependencies=[Depends(...)]`

`require_permission(permiso)` devuelve un callable que **internamente** usa `Depends(get_current_active_user)`. Añadir `Depends(require_permission("x.y.z"))` es **aditivo** y compatible con la resolución de dependencias de FastAPI. No hay conflicto por “dependencia duplicada” de usuario: FastAPI resuelve una vez y reutiliza. Por tanto, **añadir** una dependencia de permiso no rompe por duplicado. El riesgo no es técnico aquí, sino de **qué string** poner.

#### 2.3.2 Orden de dependencias

En endpoints que ya tienen varias dependencias, el orden puede importar semánticamente:

- Ejemplo: `dependencies=[Depends(require_admin), Depends(require_permission("admin.rol.crear"))]`.  
  Ambas se ejecutan; si una herramienta **inserta** `require_permission` sin tocar `require_admin`, el orden se mantiene. Si **reemplaza** la lista de dependencias o la reordena, podría quitar `require_admin` y cambiar el comportamiento. Una auto-decoración segura debe **solo añadir** (o marcar para revisión) y no reemplazar dependencias existentes.

#### 2.3.3 Wrappers y decoradores indirectos

No se observan wrappers que alteren el path o el método HTTP después de definida la ruta. El único “extra” es el uso de `tags=[...]` en varios routers. No bloquea la inyección de una dependencia de permiso.

#### 2.3.4 Tres patrones de uso de permiso en el proyecto

1. **En firma del handler:**  
   `current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer"))`  
   (org: empresa, departamentos, parametros, etc.)
2. **En decorator:**  
   `dependencies=[Depends(require_permission("modulos.menu.leer"))]`  
   (modulos, rbac, users)
3. **Dependencia “silenciosa”:**  
   `_: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.leer"))`  
   (aud, svc, tkt, dms, wfl, mfg ordenes_produccion, bi)

Una automatización que inyecte solo uno de estos patrones (ej. siempre en `dependencies=`) cambiaría el estilo del resto del archivo o del módulo. No es un bloqueo funcional, pero sí de **consistencia** y mantenibilidad (y posible conflicto con herramientas que asumen un solo patrón).

---

### 2.4 Diferencias exactas: decorados vs no decorados

| Aspecto | Endpoints SÍ decorados | Endpoints NO decorados |
|--------|------------------------|-------------------------|
| **Ubicación** | org, modulos (menus, plantillas, secciones, cliente_modulo, modulos), rbac (roles, permisos_catalogo), aud, svc (parcial), tkt, dms, wfl, mfg (ordenes_produccion), bi, users | HCM, LOG, INV, FIN, PUR, SLS, INVBILL, PRC, WMS, QMS, CRM, POS, MFG (resto), MRP, MPS, MNT, CST, TAX, BDG, PM, permisos rol-menú, menus legacy, tenant/superadmin, areas |
| **Permiso** | String fijo elegido por desarrollador (ej. `org.area.leer`, `admin.rol.crear`) | No hay llamada a `require_permission` ni `RequirePermission` |
| **Auth** | Siempre hay auth (get_current_active_user implícito en require_permission o explícito) | Solo `Depends(get_current_active_user)` |
| **Rol adicional** | Algunos además tienen `require_admin` (users, rbac) | No |
| **Path en el archivo** | Igual: paths relativos `""`, `"/{id}"`, etc. | Igual |
| **Estructura de routers** | Misma: include_router en api.py y en endpoints.py del módulo | Misma |

Conclusión: la **única** diferencia es la presencia explícita de una dependencia de permiso con un string **elegido manualmente**. No hay middleware ni mecanismo central que “auto-decore”; la decoración fue manual y selectiva. Por eso los no decorados “no pudieron serlo” en el sentido de que **nunca se aplicó** una regla automática; aplicar una ahora exige resolver los problemas de inferencia y estructura descritos arriba.

---

## 3. Ejemplos reales del proyecto

### 3.1 Mismo patrón de ruta, permiso distinto por diseño (ORG)

**Archivo:** `app/modules/org/presentation/endpoints_empresa.py`

```python
@router.get("", response_model=list[EmpresaRead], summary="Listar empresas")
async def listar_empresas(
    solo_activos: bool = True,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
```

**Archivo:** `app/modules/org/presentation/endpoints_departamentos.py`

```python
@router.get("", ...)
async def listar_departamentos(
    ...
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
```

Un inferidor por path generaría `org.empresa.leer` y `org.departamento.leer`. En el proyecto se usa **solo** `org.area.leer`. Auto-decorar por path aquí sería **incorrecto** respecto al diseño actual.

---

### 3.2 Acción no CRUD: administrar (Modulos)

**Archivo:** `app/modules/modulos/presentation/endpoints_menus.py`

```python
@router.put("/{menu_id}/", ..., dependencies=[Depends(require_permission("modulos.menu.administrar"))])
async def actualizar_menu(...): ...

@router.post("/{menu_id}/reordenar/", ..., dependencies=[Depends(require_permission("modulos.menu.administrar"))])
async def reordenar_menus(...): ...

@router.post("/{menu_id}/duplicar/", ..., dependencies=[Depends(require_permission("modulos.menu.administrar"))])
async def duplicar_menu(...): ...
```

PUT y POST a rutas custom comparten el mismo permiso `administrar`. Un mapeo automático GET→leer, POST→crear, PUT→actualizar generaría `modulos.menu.actualizar` y `modulos.menu.crear`, que no coinciden con el catálogo usado en el código.

---

### 3.3 Path incompleto en el archivo del handler (HCM)

**Archivo:** `app/modules/hcm/presentation/endpoints_empleados.py`

```python
@router.get("", response_model=List[EmpleadoRead], tags=["HCM - Empleados"])
async def get_empleados(
    ...
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
```

En este archivo solo aparece el path `""`. El prefijo `/hcm` y el segmento `/empleados` vienen de:

- `api.py`: `include_router(hcm_endpoints.router, prefix="/hcm", ...)`
- `hcm/presentation/endpoints.py`: `include_router(empleados_router, prefix="/empleados", ...)`

Sin ejecutar el árbol de routers o sin analizar esos dos archivos, no se puede saber que el permiso debe ser `hcm.empleado.leer`. Un script que solo lea `endpoints_empleados.py` no tiene información suficiente.

---

### 3.4 Recurso anidado en el mismo router (FIN)

**Archivo:** `app/modules/fin/presentation/endpoints_asientos.py`

```python
@router.get("/{asiento_id}/detalles", ...)
async def get_asiento_detalles(...): ...

@router.get("/detalles/{asiento_detalle_id}", ...)
async def get_asiento_detalle(...): ...
```

Dos recursos en el mismo archivo: “asiento” y “detalle de asiento”. Un inferidor por “último segmento literal” podría usar `detalles` para ambos o confundir cuál es el recurso. Hace falta regla explícita (ej. subpath `/detalles` → recurso `asiento_detalle`) y posiblemente revisión humana.

---

### 3.5 Dependencias duales (Users / RBAC)

**Archivo:** `app/modules/users/presentation/endpoints.py`

```python
dependencies=[Depends(require_admin), Depends(require_permission("admin.usuario.leer"))]
```

**Archivo:** `app/modules/rbac/presentation/endpoints.py`

```python
dependencies=[Depends(require_admin), Depends(require_permission("admin.rol.crear"))]
```

Cualquier automatización que **solo** añada `require_permission` y deje intacto `require_admin` sería coherente. Si la herramienta “normalizara” dependencias y eliminara `require_admin` (p. ej. asumiendo que el permiso implica el rol), el comportamiento cambiaría y podría ser inseguro.

---

## 4. Qué necesitaría una herramienta para automatizar el 100%

Para poder decorar de forma segura **todos** los endpoints faltantes de forma automática, haría falta:

1. **Grafo de routers**
   - Recorrer `api.py` y cada `modules/<modulo>/presentation/endpoints.py`.
   - Por cada `include_router(router_x, prefix=...)`, asociar ese `prefix` al router importado y, si es posible, al archivo donde está definido (p. ej. `endpoints_empleados.py`).
   - Construir el path completo por ruta: `prefix_api + prefix_modulo + prefix_recurso + path_del_decorator`.

2. **Registro de rutas en tiempo de aplicación**
   - Tras montar la app, usar `app.routes` (o equivalente) para obtener la lista de rutas con path y método ya resueltos.
   - Asociar cada ruta al handler (función) que la sirve. FastAPI/Starlette exponen esta información.
   - Con path completo y método, un motor de reglas podría proponer `modulo.recurso.accion`.

3. **Catálogo de permisos y excepciones**
   - Cargar desde BD o desde código los permisos existentes (modulo.recurso.accion).
   - Mantener un mapa de excepciones: path o (módulo, recurso) → permiso real (ej. todo ORG → `org.area.*`).
   - Mapeo de acciones en español (leer, crear, actualizar, eliminar, administrar, asignar) y posiblemente acciones custom por path (ej. `/reordenar` → administrar).

4. **Reglas de inferencia de recurso**
   - Subpaths que indican recurso anidado (ej. `/{id}/detalles` → recurso secundario `asiento_detalle`).
   - Singularización y normalización (plural → singular, guiones → snake_case) con excepciones (vacaciones, etc.).
   - Recursos con path no estándar (ej. `stock/producto/{}/almacen/{}` → recurso `stock`).

5. **Inyección de dependencia sin tocar el resto**
   - Añadir `Depends(require_permission("..."))` sin eliminar ni reordenar otras dependencias.
   - Decidir un único patrón (firma vs `dependencies=` vs dependencia silenciosa) o configurarlo por módulo para mantener consistencia.

6. **Validación post-cambio**
   - Comprobar que cada string inyectado exista en el catálogo de permisos.
   - Tests de integración que llamen a cada endpoint con usuario con/sin permiso y verifiquen 200 vs 403.

En la práctica, (1)–(2) requieren ejecución de la app o un AST/importador que resuelva el árbol de routers; (3)–(4) exigen configuración y excepciones por dominio (ORG, modulos, etc.); (5)–(6) son viables con un script o un plugin de IDE. Sin (1)–(4) bien resueltos, automatizar el 100% sería inseguro o incoherente con el diseño actual.

---

## 5. Clasificación final

| Categoría | Descripción | Ejemplos (estimado) | Automatización recomendada |
|-----------|-------------|---------------------|-----------------------------|
| **Decorables automáticamente (seguros)** | CRUD estándar (GET/POST/PUT por path simple), path y módulo identificables de forma no ambigua, permiso que existe en catálogo y sigue convención modulo.recurso.accion (español). | HCM empleados, LOG transportistas, INV categorías, FIN plan-cuentas (rutas simples). | Script que resuelva prefijos (grafo de routers o rutas montadas), infiera modulo.recurso.leer/crear/actualizar y añada `Depends(require_permission(...))`. Validar contra catálogo antes de aplicar. |
| **Decorables con heurística** | CRUD estándar pero con prefijos anidados o recursos anidados (ej. asiento vs asiento_detalle). La inferencia es posible con reglas claras pero puede haber casos límite. | FIN asientos y detalles, LOG guías y detalles, INV stock por producto/almacén. | Misma herramienta que arriba + reglas para subpaths y recursos anidados; revisión humana en listado generado antes de commit. |
| **Requieren revisión humana** | Permisos por diseño (org.area.*), acciones custom (administrar, asignar), rutas no CRUD (reordenar, duplicar, activar, desactivar), o recursos ambiguos. | Todo ORG, modulos (menus/plantillas/secciones), users (require_admin + permiso), rbac (roles + permisos), endpoints con require_admin sin permiso (permisos rol-menú, menus legacy, areas). | No automatizar la cadena de permiso; usar la auditoría en `rbac_endpoints_missing_permissions.md` como lista de tareas y decorar manualmente con el string acordado. |

---

**Conclusión:** La decoración RBAC en este proyecto fue aplicada **manualmente** y de forma selectiva. Los endpoints no decorados no están en un formato distinto; simplemente no se les añadió la dependencia de permiso. Poder “auto-decorar” de forma segura a todos exige resolver la dispersión del path (prefijos anidados, múltiples include_router), alinear con el catálogo y con decisiones de diseño (org.area.*, modulos.menu.administrar), y manejar acciones y recursos no estándar. Hasta tener esa capacidad (grafo de routers, catálogo, excepciones y reglas), la parte automatizable es solo una fracción (CRUD claros); el resto debe seguir con revisión humana y cambios manuales.
