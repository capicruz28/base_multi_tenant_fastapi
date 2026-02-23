# Auditoría técnica: Sistema de autorización y roles (IAM/RBAC)

**Alcance:** Backend FastAPI, SaaS multi-tenant híbrido (shared DB + dedicated DB).  
**Objetivo:** Evaluar si el modelo actual cumple buenas prácticas enterprise para seguridad backend, RBAC, prevención de escalamiento de privilegios, separación permisos UI vs negocio, escalabilidad ERP, aislamiento multi-tenant e IAM moderno.

---

## 1. Diagnóstico del modelo actual

### 1.1 Esquema de datos (resumen)

| Tabla | Ubicación | Función |
|-------|-----------|--------|
| `usuario` | Central (shared) / Dedicada | Usuarios por cliente_id |
| `rol` | Central / Dedicada | Roles por cliente (cliente_id NULL = rol global) |
| `usuario_rol` | Central / Dedicada | Asignación usuario ↔ rol |
| `modulo`, `modulo_seccion`, `modulo_menu` | **Solo central** | Catálogo de módulos y menús (UI) |
| `rol_menu_permiso` | Central / Dedicada | Permisos **por menú**: puede_ver, puede_crear, puede_editar, puede_eliminar, puede_exportar, puede_imprimir, puede_aprobar |

**Hallazgos:**

- **No existe un catálogo global de permisos de negocio** (ej. `orders.create`, `inventory.edit`, `users.manage`). Los únicos “permisos” persistidos son los de `rol_menu_permiso`, ligados a `menu_id` (opciones de menú).
- **Permisos = visibilidad de menú.** El backend usa `rol_menu_permiso` solo para construir el menú del usuario (`GET /modulos-menus/me/`). No hay uso de esos flags (puede_crear, puede_editar, etc.) para proteger endpoints de API.
- **RBAC en código:** En `app/core/authorization/rbac.py` existe `PERMISOS_SISTEMA` (hardcoded) y `has_permission(user, "modulo.accion")`, que consulta `user.permisos`. Pero la dependencia principal `get_current_active_user` devuelve `UsuarioReadWithRoles`, que **no incluye el campo `permisos`** (solo `roles`). Por tanto, la lista `user.permisos` en la práctica está vacía o no existe; la comprobación de permisos granulares solo “funciona” para super_admin y tenant_admin por lógica implícita, no por datos en BD.
- **Protección real de endpoints:**  
  - **Solo autenticación + tenant:** La mayoría de los endpoints ERP (manufactura, reportes BI, flujos de trabajo, documentos, etc.) solo usan `Depends(get_current_active_user)` y pasan `current_user.cliente_id` a los servicios. No hay `require_permission(...)` ni equivalente por recurso/acción.  
  - **Restricción por rol/nivel:** Algunos módulos (usuarios, roles, menús, áreas) usan `RoleChecker(["Administrador"])` (LBAC por nivel mínimo) o `require_super_admin()`. No hay comprobación por permiso fino (ej. `usuarios.crear` vs `usuarios.leer`).
- **Aislamiento multi-tenant:** El tenant se resuelve en middleware por subdominio y se valida en `get_current_active_user` (`validate_tenant_access`). Los servicios reciben `cliente_id` y lo usan en queries. Existe `apply_tenant_filter` en `query_helpers` y validación en `execute_query` (con opción de skip), pero la aplicación del filtro depende de que cada capa pase `client_id` y de que no se use `skip_tenant_validation` de forma incorrecta. En BD dedicada, `rol_menu_permiso.menu_id` referencia `modulo_menu` en BD central (cross-DB, sin FK); la integridad depende de la aplicación.

**Conclusión del diagnóstico:** El modelo actual es **orientado a UI (menú)** y **nivel de acceso (LBAC)** más que a **permisos de negocio por recurso/acción**. La protección real del API se basa en “usuario autenticado del tenant” y, en algunos routers, en “rol Administrador” o “SuperAdmin”, no en un modelo RBAC con permisos explícitos en BD.

---

## 2. Riesgos críticos encontrados

| # | Riesgo | Severidad | Descripción |
|---|--------|-----------|-------------|
| 1 | **Sin control de acceso por acción en la mayoría del API** | **Crítica** | Cualquier usuario autenticado del tenant puede llamar a endpoints de creación/edición/eliminación de órdenes de producción, reportes, documentos, etc., si conoce la ruta. No se comprueba si su rol “permite” esa acción. |
| 2 | **Permisos de menú no se reflejan en el backend** | **Alta** | `rol_menu_permiso` (puede_crear, puede_editar, etc.) solo alimenta el menú. Un usuario sin “puede_crear” en un menú puede igualmente llamar al POST correspondiente si el endpoint no comprueba un permiso de negocio. |
| 3 | **Escalación de privilegios dentro del tenant** | **Alta** | Sin un catálogo de permisos y sin comprobación en cada endpoint, un usuario con un rol limitado puede realizar acciones reservadas a “Administrador” (ej. crear/editar usuarios) si esos endpoints no están protegidos por `RoleChecker` o equivalente. Hoy usuarios/roles/menús sí están protegidos por rol; el resto del ERP, no. |
| 4 | **Desconexión entre RBAC en código y datos** | **Alta** | `require_permission(permiso)` y `has_permission()` existen pero dependen de `user.permisos`, que no se rellena desde la BD actual (solo menú). El sistema de permisos granulares está “desconectado” del modelo de datos. |
| 5 | **BD dedicada: menu_id sin FK** | **Media** | En BD dedicada, `rol_menu_permiso.menu_id` apunta a `modulo_menu` en otra BD. No hay FK; hay que validar en aplicación. Riesgo de IDs inválidos o desincronización. |
| 6 | **Filtro de tenant no universal** | **Media** | El filtro de tenant se aplica cuando se usa `execute_query` con `client_id` y sin `skip_tenant_validation`. Cualquier query que no pase por este flujo o que use raw SQL sin filtro puede fugarse entre tenants si hay un error. |
| 7 | **Sin estándar de permisos (ej. nombres)** | **Media** | No hay tabla ni convención de códigos de permiso (ej. `ventas.orden.crear`). Dificulta auditoría, políticas consistentes y futura integración con IAM/OAuth2 scopes. |

---

## 3. Qué está mal conceptualmente

1. **Confusión entre “qué veo en el menú” y “qué puedo hacer en el API”.**  
   El modelo actual resuelve solo lo primero. En un ERP enterprise, la autorización debe definirse sobre **recursos y acciones** (ej. “crear orden de venta”), y el menú debe ser una **vista derivada** de esos permisos, no la única fuente de verdad.

2. **RBAC sin catálogo de permisos.**  
   Un RBAC profesional requiere: **recursos** (o recursos + acciones) definidos en el sistema, **roles** que agrupan permisos, y **asignación usuario → rol**. Aquí los “permisos” son filas por (rol, menú) con flags CRUD. No hay entidad “permiso” reutilizable (ej. “orders.create”) que se asigne a roles y se consulte en el API.

3. **Autorización basada solo en nivel (LBAC) para parte del sistema.**  
   Donde sí hay restricción (usuarios, roles, menús), se usa nivel mínimo (p. ej. “Administrador” → nivel 4). Eso evita que un usuario sin rol admin acceda a esos endpoints, pero no permite políticas granulares (ej. “solo lectura de usuarios” o “solo aprobar órdenes”).

4. **Permisos “implícitos” para tenant_admin.**  
   En `rbac.has_permission()` el tenant_admin tiene “casi todos” los permisos por lógica en código. Eso es útil como atajo, pero refuerza que no hay un modelo explícito en BD y dificulta auditoría y cambios de política.

5. **Sin separación clara UI vs negocio.**  
   Lo correcto sería: **capa de negocio/API** protegida por permisos (ej. `ventas.orden.crear`), y **capa de presentación** que oculte o deshabilite botones según esos mismos permisos. Hoy la capa de presentación se basa en menú/permisos de menú y la capa API en “autenticado + tenant” (y en algunos casos nivel de rol).

---

## 4. Arquitectura recomendada (RBAC + opción ABAC ligera)

### 4.1 Enfoque recomendado: RBAC con catálogo de permisos

- **Recursos/acciones como primera clase:** Definir un catálogo de permisos de **negocio** (no solo menú), por ejemplo:
  - `modulo.recurso.accion`: `ventas.orden.crear`, `inventario.ajuste.editar`, `admin.usuario.eliminar`, `reportes.bi.exportar`.
- **Roles** siguen siendo por tenant (y opcionalmente globales). Cada rol tiene una **lista de permisos** (tabla rol_permiso o rol_recurso_accion).
- **Menú:** Sigue existiendo `modulo_menu` y `rol_menu_permiso` para **visualización** (qué ítems de menú ver y con qué acciones mostrar). Se recomienda que la visibilidad/acción de menú se **mapee desde** el mismo catálogo de permisos (ej. “ver menú Órdenes de venta” ↔ permiso `ventas.orden.leer`), para no duplicar lógica.
- **API:** Cada endpoint que modifique estado o exponga datos sensibles debe comprobar un **permiso concreto** (p. ej. `Depends(require_permission("ventas.orden.crear"))`), obtenido desde BD (permisos del usuario vía sus roles), no solo “autenticado” o “nivel ≥ X”.
- **SuperAdmin / TenantAdmin:** Se pueden seguir tratando como bypass en código (tienen todos los permisos) siempre que quede documentado y auditado; a largo plazo puede preferirse asignarles explícitamente un rol “SuperAdmin” con todos los permisos en BD.

Opcionalmente, para casos “este usuario puede ver solo sus propias órdenes”, se puede añadir **ABAC ligero** (atributos: usuario_id, rol, tal vez departamento) en la capa de servicio, sin sustituir el RBAC en la puerta del API.

### 4.2 Compatibilidad con IAM moderno

- **Tokens:** JWT con `sub`, `client_id` (tenant), y opcionalmente `scope` o `permissions` (lista de códigos de permiso) para evitar hits a BD en cada request. Si se usa solo `sub` + tenant, el backend debe resolver permisos desde BD/caché.
- **Estándares:** OAuth2 scopes pueden mapearse a permisos (ej. `scope: ventas.orden.crear`). Para OIDC, los claims pueden incluir `roles` y/o `permission`; el backend debe validar contra el catálogo y no confiar solo en el token sin verificar en BD cuando la política lo exija.

---

## 5. Tablas nuevas necesarias (recomendación)

Las siguientes tablas permiten un RBAC con catálogo de permisos sin tirar el modelo actual; se integran con lo existente.

### 5.1 Catálogo de permisos (global, en BD central)

```sql
-- Permiso de negocio (recurso + acción). Global, no por tenant.
CREATE TABLE permiso (
    permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    codigo NVARCHAR(100) NOT NULL UNIQUE,   -- ej. 'ventas.orden.crear', 'admin.usuario.leer'
    nombre NVARCHAR(150) NOT NULL,
    descripcion NVARCHAR(500) NULL,
    modulo_id UNIQUEIDENTIFIER NULL,        -- FK a modulo (opcional, para agrupar)
    recurso NVARCHAR(80) NOT NULL,          -- ej. 'orden', 'usuario'
    accion NVARCHAR(30) NOT NULL,           -- ej. 'crear', 'leer', 'actualizar', 'eliminar'
    es_activo BIT DEFAULT 1 NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NULL,
    CONSTRAINT FK_permiso_modulo FOREIGN KEY (modulo_id) REFERENCES modulo(modulo_id)
);
CREATE INDEX IDX_permiso_codigo ON permiso(codigo);
CREATE INDEX IDX_permiso_modulo ON permiso(modulo_id);
```

### 5.2 Asignación rol → permiso (por tenant)

En **BD central** (para clientes shared) y en **BD dedicada** (para clientes dedicated), añadir:

```sql
-- Qué permisos tiene cada rol (por tenant).
CREATE TABLE rol_permiso (
    rol_permiso_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    cliente_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    permiso_id UNIQUEIDENTIFIER NOT NULL,
    fecha_creacion DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_rol_permiso_rol FOREIGN KEY (rol_id) REFERENCES rol(rol_id) ON DELETE CASCADE,
    CONSTRAINT FK_rol_permiso_cliente FOREIGN KEY (cliente_id) REFERENCES cliente(cliente_id) ON DELETE CASCADE,
    CONSTRAINT UQ_rol_permiso UNIQUE (cliente_id, rol_id, permiso_id)
);
-- permiso_id referencia permiso en BD central; en BD dedicada podría ser solo el UUID sin FK.
CREATE INDEX IDX_rol_permiso_rol ON rol_permiso(rol_id);
CREATE INDEX IDX_rol_permiso_permiso ON rol_permiso(permiso_id);
```

En BD dedicada no puede haber FK a `permiso` (está en central); se debe validar en aplicación que `permiso_id` exista en central o replicar solo la tabla `permiso` en dedicada si se desea FK local.

### 5.3 Opcional: enlace menú ↔ permiso

Para que “ver este ítem de menú” y “tener permiso X” sean lo mismo, en BD central:

```sql
-- En modulo_menu (añadir columna) o tabla nueva:
ALTER TABLE modulo_menu ADD permiso_requerido_id UNIQUEIDENTIFIER NULL;
-- CONSTRAINT FK_menu_permiso FOREIGN KEY (permiso_requerido_id) REFERENCES permiso(permiso_id);
```

Así, el backend puede seguir construyendo el menú según “usuario tiene permiso X” en lugar de solo `rol_menu_permiso` (o combinar ambos durante la transición).

---

## 6. Flujo ideal de autorización en FastAPI

1. **Middleware / contexto**  
   Resolver tenant (subdominio, etc.) y establecer `cliente_id` en contexto. Sin cambios mayores respecto a lo actual.

2. **Autenticación**  
   `get_current_active_user`: validar JWT, cargar usuario, validar tenant (`validate_tenant_access`), construir objeto usuario **con permisos resueltos** (lista de `codigo` de permisos que tiene por sus roles, desde `rol_permiso` + `permiso`). Ese objeto debe exponer algo como `user.permisos: List[str]` (códigos) para que `has_permission(user, "ventas.orden.crear")` sea comprobable.

3. **Protección de endpoints**  
   - Endpoints que solo requieren “estar autenticado en el tenant”: `Depends(get_current_active_user)`.  
   - Endpoints que requieren una acción concreta: `Depends(require_permission("ventas.orden.crear"))` (o `require_any_permission([...])`).  
   - Endpoints solo para administrador del tenant: `Depends(require_tenant_admin)`.  
   - Endpoints solo para super admin: `Depends(require_super_admin)`.

4. **Implementación de `require_permission`**  
   - Asegurar que el usuario inyectado tenga la lista de permisos cargada (desde BD o caché).  
   - `require_permission("ventas.orden.crear")` debe comprobar que `"ventas.orden.crear"` esté en `user.permisos` (o que el usuario sea super_admin/tenant_admin según política).  
   - Si el token incluye `permissions` o `scope`, se puede usar en primera instancia y contrastar con BD en operaciones sensibles.

5. **Servicios**  
   Siguen recibiendo `cliente_id` (y opcionalmente `current_user`) y aplicando filtro de tenant en todas las queries. No confiar en que “el usuario ya fue autorizado” para omitir el filtro por `cliente_id`.

6. **Menú**  
   Opción A: seguir construyendo el menú desde `rol_menu_permiso` (solo UI). Opción B: construir el menú desde “permisos del usuario” y `modulo_menu.permiso_requerido_id`, de modo que solo se muestren ítems cuyos permisos tenga el usuario. Ambas pueden coexistir en una fase de transición.

---

## 7. Nivel de madurez del sistema

| Dimensión | Estado actual | Comentario |
|-----------|----------------|------------|
| Autenticación | **Intermedio** | JWT + refresh, tenant en contexto, validación de acceso al tenant. Falta revocación/rotación clara y posible 2FA. |
| Aislamiento multi-tenant | **Intermedio** | Tenant por subdominio, cliente_id en servicios y en helpers de query. Riesgo en queries que no usen el flujo estándar o que usen skip_tenant_validation. |
| RBAC (permisos de negocio) | **Básico** | Roles y asignación usuario-rol existen; no hay catálogo de permisos ni comprobación por permiso en la mayoría del API. |
| Permisos de menú (UI) | **Intermedio** | Modelo de menú y rol_menu_permiso está bien para “qué ve el usuario”; no se usa para proteger el API. |
| Prevención de escalamiento de privilegios | **Básico** | Parcial: usuarios/roles/menús protegidos por nivel; el resto del ERP no. |
| Separación UI vs negocio | **Básico** | No hay capa de permisos de negocio; solo menú y nivel. |
| Escalabilidad (nuevos módulos) | **Intermedio** | Añadir módulos/menús es fácil; añadir permisos de API granulares requiere tocar código y no hay estándar en BD. |
| IAM / estándares | **Básico** | No hay scopes ni catálogo de permisos alineado con OAuth2/OIDC. |

**Veredicto global:** **Nivel básico–intermedio**. Adecuado para un MVP o entornos controlados; **no suficiente** para un ERP SaaS enterprise en producción global sin endurecer autorización (catálogo de permisos + comprobación en endpoints).

---

## 8. ¿Está listo para crecer como ERP SaaS enterprise?

**Respuesta corta: no**, tal como está, si “enterprise” implica:

- Múltiples roles por cliente con permisos granulares (no solo “todo o nada” por nivel).
- Auditoría clara de “quién puede hacer qué” desde datos, no solo desde código.
- Onboarding de nuevos módulos/recursos con permisos sin tocar código duro.
- Cumplimiento y estándares IAM (OAuth2 scopes, OIDC, posible integración con IdP).

**Qué sí está listo:**

- Base multi-tenant (shared + dedicated) y flujo de autenticación por tenant.
- Modelo de menú y de roles por cliente.
- Infraestructura de filtro de tenant y de niveles (LBAC) reutilizable.

**Pasos recomendados para acercarse a “listo para producción enterprise”:**

1. Introducir catálogo de permisos (`permiso`) y asignación rol–permiso (`rol_permiso`).  
2. Cargar permisos del usuario en `get_current_active_user` (o en un paso posterior inmediato) y exponerlos en el objeto usuario.  
3. Proteger todos los endpoints sensibles con `require_permission(...)` (o `require_any_permission`) según recurso/acción.  
4. Opcional: enlazar menú con permisos (`modulo_menu.permiso_requerido_id`) y derivar visibilidad de menú de los mismos permisos.  
5. Revisar y reducir el uso de `skip_tenant_validation` y asegurar que todas las queries operativas pasen `client_id`.  
6. Documentar y, si aplica, reflejar permisos en JWT (scopes/claims) para rendimiento y alineación con IAM.

Con esto, el sistema pasaría a un modelo RBAC con permisos de negocio explícitos y estaría en mejor posición para escalar como ERP SaaS enterprise y alinearse con estándares IAM modernos.

---

## Plan de implementación por fases

Para implementar estas mejoras **sin romper el funcionamiento actual** y con mejoras óptimas (catálogo, carga de permisos, protección gradual, caché/JWT opcional), se ha definido un plan ejecutable por fases:

→ **[PLAN_IMPLEMENTACION_RBAC_FASES.md](./PLAN_IMPLEMENTACION_RBAC_FASES.md)**

Resumen de fases:

- **Fase 1:** BD (tablas `permiso`, `rol_permiso`) + seed de permisos. Sin cambios en la app.
- **Fase 2:** Cargar permisos del usuario y exponer `user.permisos` en `get_current_active_user`; `has_permission()` usa datos reales.
- **Fase 3:** Proteger endpoints con `require_permission(...)` de forma gradual (empezando por usuarios/roles).
- **Fase 4 (opcional):** Menú derivado de permisos, caché de permisos, permisos en JWT.

Para proceder, indica la fase a implementar (ej. *"Implementa Fase 1"* o *"Implementa Fase 2"*).
