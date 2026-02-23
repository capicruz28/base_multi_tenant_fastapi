# Plan de implementación RBAC por fases

**Criterio:** Implementación **sin romper ni dañar** el funcionamiento actual. Todo es **aditivo**: el menú actual (`rol_menu_permiso`), el login, los endpoints y el `RoleChecker`/`require_super_admin` siguen funcionando igual hasta que se decida usar los nuevos permisos.

**Incluye:** Catálogo de permisos, asignación rol→permiso, carga de permisos en el usuario, protección opcional por permiso en endpoints, y mejoras opcionales (caché, JWT claims).

---

## Principios de no ruptura

| Principio | Cómo se cumple |
|-----------|-----------------|
| **No eliminar ni deprecar** | `rol_menu_permiso` y `modulo_menu` no se tocan. El menú se sigue construyendo como hoy. |
| **No cambiar contratos** | `get_current_active_user` sigue devolviendo un tipo compatible; se **añade** el campo `permisos` (lista de códigos) sin quitar nada. |
| **Compatibilidad de tipos** | `UsuarioReadWithRoles` se extiende con `permisos: List[str]` opcional (default `[]`); quien no use permisos sigue igual. |
| **Protección opt-in** | Los endpoints **no** se cambian hasta una fase explícita; entonces se añade `require_permission(...)` solo donde se decida. |
| **BD dedicada** | Tabla `permiso` solo en central; `rol_permiso` en central y en dedicada (sin FK a `permiso` en dedicada); consulta de permisos del usuario puede leer `permiso` en central cuando haga falta. |
| **Rollback** | Cada fase se puede desactivar (ej. no cargar permisos, no usar `require_permission`) sin tocar BD; las tablas nuevas simplemente no se usan. |

---

## Resumen de fases

| Fase | Objetivo | Rompe algo | Qué ganas |
|------|----------|------------|-----------|
| **Fase 1** | BD: tablas `permiso` y `rol_permiso` + seed inicial | No | Catálogo listo para usar y asignar a roles. |
| **Fase 2** | Cargar permisos del usuario y exponerlos en `current_user` | No | `user.permisos` disponible; `has_permission()` funciona con datos reales. |
| **Fase 3** | Proteger endpoints críticos con `require_permission` (gradual) | No* | API alineada con permisos de negocio. (*Se elige qué endpoints.) |
| **Fase 4** | (Opcional) Menú derivado de permisos y/o caché/JWT | No | Menú y API con una sola fuente de verdad; menos hits a BD. |

---

## Fase 1: Modelo de datos y catálogo de permisos

**Objetivo:** Tener en BD las tablas `permiso` y `rol_permiso` y un conjunto inicial de permisos (seed) sin cambiar ningún comportamiento de la app.

### 1.1 Entregables

1. **Script SQL (BD central)**  
   - Crear tabla `permiso` (codigo, nombre, descripcion, modulo_id, recurso, accion, es_activo, ...).  
   - Crear tabla `rol_permiso` (cliente_id, rol_id, permiso_id, UQ por rol+permiso).  
   - Índices: `permiso(codigo)`, `permiso(modulo_id)`, `rol_permiso(rol_id)`, `rol_permiso(permiso_id)`.

2. **Script SQL (BD dedicada)**  
   - Crear solo `rol_permiso` (misma estructura; **sin** FK a `permiso`; `permiso_id` es UUID que referencia central).  
   - Opcional: si prefieres FK local, copiar solo la tabla `permiso` (solo lectura/catálogo) en cada dedicada.

3. **Seed de permisos**  
   - Inserción inicial de permisos por módulo existente, por ejemplo:  
     - `admin.usuario.leer`, `admin.usuario.crear`, `admin.usuario.actualizar`, `admin.usuario.eliminar`  
     - `admin.rol.leer`, `admin.rol.crear`, …  
     - `modulos.menu.leer`, `modulos.menu.administrar`  
     - Para cada módulo ERP (mfg, bi, wfl, dms, tkt, …): `modulo.recurso.leer`, `.crear`, `.actualizar`, `.eliminar` según los recursos expuestos en API.  
   - Convención de códigos: `modulo.recurso.accion` (ej. `mfg.orden_produccion.crear`).

4. **Modelos/schemas en código (opcional en Fase 1)**  
   - Definir modelos Pydantic o SQLAlchemy para `permiso` y `rol_permiso` para uso desde servicios en fases siguientes. No es obligatorio usarlos ya en ningún endpoint.

### 1.2 Cómo proceder

- Ejecutar scripts en entorno de desarrollo/staging primero.  
- No hay cambios en auth ni en endpoints; solo BD y, si quieres, modelos.  
- **Criterio de éxito:** Tablas creadas, seed insertado, aplicación sigue funcionando igual (login, menú, todos los endpoints).

### 1.3 Mejora óptima incluida

- **Nomenclatura estándar** desde el inicio (`modulo.recurso.accion`) para auditoría y futuros scopes OAuth2.  
- **Relación opcional con `modulo`** para agrupar permisos por módulo ERP y facilitar UIs de asignación.

---

## Fase 2: Cargar permisos del usuario y exponerlos en `current_user`

**Objetivo:** Que el objeto usuario que devuelve `get_current_active_user` incluya una lista de códigos de permiso (`user.permisos`), obtenida desde `rol_permiso` + `permiso`, sin cambiar el comportamiento de ningún endpoint.

### 2.1 Entregables

1. **Servicio o función de permisos**  
   - `obtener_permisos_usuario(usuario_id, cliente_id)` (o por lista de `rol_id`) que:  
     - Lee desde `rol_permiso` (y `permiso` para el codigo) en la BD del tenant (central o dedicada).  
     - Para BD dedicada: si `permiso` no está en dedicada, obtener códigos desde central por `permiso_id` (lista de UUIDs).  
     - Devuelve `List[str]` de códigos (ej. `["admin.usuario.leer", "mfg.orden_produccion.crear"]`).

2. **Integración en `get_current_active_user` (o en `build_user_with_roles`)**  
   - Después de construir el usuario con roles, llamar a `obtener_permisos_usuario(...)` y **añadir** al objeto usuario el atributo `permisos: List[str]`.  
   - Si el tipo actual es `UsuarioReadWithRoles`, extender el schema para incluir `permisos: List[str] = Field(default_factory=list)`.  
   - SuperAdmin / TenantAdmin: se puede seguir dando “todos los permisos” por lógica (ej. no consultar BD y asignar lista con wildcard o lista completa), para no romper `has_permission()` actual.

3. **Compatibilidad con `has_permission()` (rbac.py)**  
   - Asegurar que `has_permission(user, "modulo.recurso.accion")` use `user.permisos` cuando exista.  
   - Si `user.permisos` está vacío o no existe, mantener el comportamiento actual (solo super_admin / tenant_admin por lógica). Así no se rompe nada.

### 2.2 Cómo proceder

- Implementar servicio de permisos y llamada desde el builder de usuario.  
- Extender schema de usuario con `permisos`.  
- Probar login y un endpoint que use `current_user`; comprobar que `current_user.permisos` tiene códigos cuando el usuario tiene roles con `rol_permiso` asignados.  
- **Criterio de éxito:** Mismo comportamiento que antes; además, `user.permisos` poblado cuando hay datos en `rol_permiso`. Si no hay filas en `rol_permiso`, `user.permisos` puede estar vacío y el resto del sistema sigue igual.

### 2.3 Mejora óptima incluida

- **Caché opcional (Redis/memoria):** clave `permisos:usuario_id:cliente_id` con TTL corto (ej. 1–5 min) para no golpear BD en cada request. Si no hay Redis, solo BD.  
- **Un solo query** para obtener todos los permisos del usuario (JOIN rol_permiso + permiso por sus roles activos).

---

## Fase 3: Proteger endpoints con `require_permission` (gradual)

**Objetivo:** Que los endpoints sensibles exijan un permiso concreto además de “usuario autenticado del tenant”, usando la lista ya cargada en `user.permisos`, sin quitar la protección actual donde ya exista (RoleChecker / require_super_admin).

### 3.1 Entregables

1. **Regla de uso**  
   - Donde hoy solo está `Depends(get_current_active_user)`, se puede **añadir** `Depends(require_permission("modulo.recurso.accion"))`.  
   - Donde ya hay `RoleChecker(["Administrador"])` o `require_super_admin()`, se puede:  
     - Mantenerlos y además exigir un permiso concreto, o  
     - Sustituir por `require_permission(...)` cuando el permiso correspondiente esté asignado al rol Administrador en `rol_permiso`.  
   - SuperAdmin (y opcionalmente TenantAdmin) siguen teniendo acceso total en `has_permission()`.

2. **Mapa de endpoints → permisos**  
   - Documentar (o definir en código) qué permiso requiere cada ruta, por ejemplo:  
     - `POST /api/v1/usuarios/` → `admin.usuario.crear`  
     - `GET /api/v1/usuarios/` → `admin.usuario.leer`  
     - `PUT /api/v1/usuarios/{id}` → `admin.usuario.actualizar`  
     - `DELETE /api/v1/usuarios/{id}` → `admin.usuario.eliminar`  
     - Endpoints de manufactura, BI, WFL, DMS, TKT, etc. → permisos del tipo `mfg.orden_produccion.crear`, `bi.reporte.exportar`, etc.

3. **Aplicación gradual**  
   - Empezar por un subconjunto (ej. módulo usuarios y roles).  
   - Añadir `require_permission(...)` en esos endpoints y comprobar que usuarios con rol que tiene ese permiso pasan y los que no, reciben 403.  
   - Luego ir extendiendo al resto de módulos.

### 3.2 Cómo proceder

- Elegir el primer grupo de endpoints (recomendado: usuarios y roles).  
- Añadir `Depends(require_permission("..."))` según el mapa.  
- Asegurar que el rol “Administrador” (o el que corresponda) tenga en `rol_permiso` los permisos necesarios para no romper a los admins actuales.  
- **Criterio de éxito:** Mismo acceso que antes para quienes ya tenían rol admin; usuarios sin ese permiso reciben 403 en endpoints protegidos. El resto del API sin `require_permission` sigue igual.

### 3.3 Mejora óptima incluida

- **`require_any_permission([...])`** para rutas que puedan permitir varios permisos (ej. “leer reporte” o “exportar reporte”).  
- Documentar en OpenAPI el permiso requerido (summary/description o extensión custom) para que el frontend y la auditoría sepan qué permiso pide cada ruta.

---

## Fase 4 (Opcional): Menú desde permisos y/o caché/JWT

**Objetivo:** Unificar menú con permisos (opcional) y reducir carga en BD (caché o JWT).

### 4.1 Menú derivado de permisos (opcional)

- Añadir en BD central `modulo_menu.permiso_requerido_id` (FK a `permiso`).  
- En el servicio que construye el menú: además de (o en lugar de) `rol_menu_permiso`, filtrar ítems por “usuario tiene el permiso indicado en `permiso_requerido_id`”.  
- Se puede hacer en modo híbrido: si el ítem tiene `permiso_requerido_id`, exigir ese permiso; si no, seguir con lógica actual por `rol_menu_permiso`. Así no se rompe nada.

### 4.2 Caché de permisos (si no se hizo en Fase 2)

- Cachear `permisos:usuario_id:cliente_id` con TTL corto. Invalidar al cambiar asignaciones de roles o `rol_permiso`.

### 4.3 Permisos en JWT (opcional)

- En el login, incluir en el payload del JWT una claim `permissions: string[]` (lista de códigos).  
- En `get_current_active_user`, si el token trae `permissions`, usarlos y opcionalmente no llamar a BD (o usarlos como caché y refrescar en segundo plano).  
- Considerar tamaño del token; si hay muchos permisos, seguir usando BD/caché y no poner todos en el token.

---

## Orden recomendado y dependencias

```
Fase 1 (BD + seed)
    ↓
Fase 2 (cargar permisos en usuario)
    ↓
Fase 3 (proteger endpoints, gradual)
    ↓
Fase 4 (opcional: menú/permisos, caché, JWT)
```

- **Fase 1** no depende de código de aplicación (solo scripts SQL y opcionalmente modelos).  
- **Fase 2** depende de Fase 1 (tablas y seed).  
- **Fase 3** depende de Fase 2 (user.permisos disponible).  
- **Fase 4** puede hacerse en cualquier momento después de Fase 2 (y Fase 3 si se quiere menú alineado con permisos protegidos).

---

## Cómo indicar cómo proceder

Puedes decir, por ejemplo:

- *"Implementa Fase 1"* → scripts SQL (central + dedicada) + seed de permisos + modelos/schemas si se incluyen.  
- *"Implementa Fase 2"* → servicio de permisos, extensión del usuario con `permisos`, integración en `get_current_active_user` / `build_user_with_roles`, y ajuste de `has_permission()`.  
- *"Implementa Fase 3 para el módulo de usuarios"* → mapa de permisos para usuarios/roles y añadir `require_permission` en esos endpoints.  
- *"Implementa Fase 4.1"* → columna `permiso_requerido_id` y lógica híbrida en el servicio de menú.

Cada fase se puede implementar y probar por separado; el sistema actual sigue funcionando en todo momento.

---

## Estado de implementación

| Fase | Estado | Archivos / notas |
|------|--------|-------------------|
| **Fase 1** | Implementada | `SCRIPT_RBAC_TABLAS_CENTRAL.sql`, `SCRIPT_RBAC_TABLAS_DEDICADA.sql`, `SEED_PERMISOS_RBAC.sql`. Ejecutar en BD central (y en cada BD dedicada) para crear tablas y catálogo. |
| **Fase 2** | Implementada | `permisos_usuario_service.py` (obtener_codigos_permiso_usuario), `user_builder.py` (carga permisos en usuario), `UsuarioReadWithRoles.permisos`, `query_helpers.GLOBAL_TABLES` (+ permiso), `rbac.has_permission` (acepta lista de códigos). Si las tablas no existen, se devuelve `permisos=[]` y no se rompe nada. |
| **Fase 3** | Implementada | Seed `SEED_ROL_PERMISO_ADMINISTRADOR.sql`. `require_permission` en usuarios, roles, BI, MFG, WFL, DMS, TKT, SVC, AUD. Se mantiene `require_admin`/`RoleChecker` donde ya existía. |
| **Fase 4** | Pendiente | Opcional. |

**Importante Fase 3:** Ejecutar `SEED_ROL_PERMISO_ADMINISTRADOR.sql` en BD central **después** de tener roles "Administrador" creados por cliente, para que ese rol reciba todos los permisos y no se rompa el acceso actual.
