# Evolución del Permission Resolver hacia Authorization Layer central

**Rol:** Principal SaaS Architect — sistemas multi-tenant enterprise  
**Contexto:** Sistema en producción; evolución incremental sin reescrituras ni ruptura de compatibilidad.  
**Referencias:** `ANALISIS_ARQUITECTONICO_PERMISSION_RESOLVER.md`, `PERMISSION_RESOLVER_API_DESIGN.md`.

---

## 1. Responsabilidades del Permission Resolver

### 1.1 Estado actual (hoy)

Hoy **no existe** un componente llamado “Permission Resolver”. La lógica equivalente está repartida:

| Responsabilidad | Dónde vive hoy |
|-----------------|----------------|
| Calcular códigos de permiso de negocio para un usuario en un tenant | `permisos_usuario_service.obtener_codigos_permiso_usuario()` |
| Punto de uso de esa lista | `build_user_with_roles()` → `UsuarioReadWithRoles(permisos=...)` |
| Validación en endpoint | `require_permission(perm)` → `has_permission(user, perm)` sobre `user.permisos` |
| Decidir qué ítems de menú ve el usuario | `ModuloMenuService.get_menu_usuario()` (cliente_modulo + rol_menu_permiso) |
| Decidir qué módulos tiene el tenant | Consultas ad hoc a `cliente_modulo` en ModuloMenuService y otros |

No hay cache de permisos ni un único punto que devuelva “effective permissions” con metadatos. El “estado actual” del resolver es, por tanto, la **posición objetivo de la Fase 1** una vez implementado según `PERMISSION_RESOLVER_API_DESIGN.md`:

- **Resolver (Fase 1):** dado (usuario_id, cliente_id, contexto), devolver **EffectivePermissions** (códigos + metadatos), con cache e invalidación, sin cambiar contrato de `user.permisos` ni de `has_permission`.

### 1.2 Estado objetivo (futuro — Authorization Layer)

El Permission Resolver debe evolucionar para ser el **único productor de verdad** de:

1. **Permisos efectivos de negocio** para un usuario en un tenant: `effective_permissions = (subscription_modules) ∩ (role_permissions)`, con opción de incluir o no el filtro por suscripción.
2. **Una interfaz estable** que el resto del sistema consuma (capa de presentación, servicios, menú) sin duplicar consultas a `rol_permiso` / `usuario_rol` / `permiso`.
3. **Cache e invalidación** centralizados para evitar N+1 y consultas repetidas en el mismo request o entre requests.

Responsabilidades que **sí** debe tener en estado objetivo:

- Calcular y cachear **EffectivePermissions** (códigos + is_super_admin + metadata).
- Exponer **invalidación** por usuario y por tenant para que los escritores (rol_permiso, usuario_rol, cliente_modulo) mantengan coherencia sin conocer la implementación del cache.
- Opcionalmente, en etapas posteriores: exponer **módulos activos del tenant** (o un predicado “tiene módulo X”) para que menú y billing no repitan lógica de cliente_modulo.
- Mantener **compatibilidad** con el contrato actual: `user.permisos = effective.codes` y `has_permission(user, perm)` sin cambios de firma.

Responsabilidades que **no** debe tener (límites claros):

- **Autenticación:** no valida credenciales ni tokens; recibe usuario_id y cliente_id ya resueltos por el flujo actual (deps + build_user_with_roles).
- **Construcción del menú jerárquico:** no arma el árbol de módulos/secciones/menús; solo puede convertirse en **fuente de datos** para “quién puede ver qué” (permisos por ítem o por código). La construcción del árbol sigue en ModuloMenuService o en un servicio de menú que consuma el resolver.
- **Billing ni facturación:** no decide precios ni límites de plan; puede exponer “módulos activos” o “tiene permiso P” para que billing/feature-flags consuman, pero no calcula vencimientos ni cobros.
- **Lógica de UI:** no conoce rutas frontend ni componentes; no decide qué botón mostrar. Solo datos de autorización.
- **Persistencia directa:** no escribe en rol_permiso, usuario_rol ni cliente_modulo; solo lee (o delega en servicios existentes) e invalida cache cuando otros servicios escriben.
- **Políticas de negocio complejas** (ej. “puede editar solo si es el propietario”): en Stage 1–2 no; en Stage 3 (Policy Engine) se puede evaluar si el resolver orquesta políticas que deleguen en reglas más ricas, sin que el resolver implemente esas reglas él mismo.

---

## 2. Orden exacto de migración incremental

La regla es: **primero un único consumidor que ya necesita la lista de permisos; después servicios que hoy duplican consultas o lógica; por último menú y billing cuando el resolver sea la fuente de verdad de permisos y (opcional) de módulos activos.**

### 2.1 Orden recomendado

| Orden | Componente | Qué hace hoy | Cambio incremental | Riesgo |
|-------|------------|--------------|--------------------|--------|
| **1** | **build_user_with_roles** (user_builder) | Llama a `obtener_codigos_permiso_usuario` y asigna `permisos` al usuario. | Bajo feature flag, llamar al resolver; asignar `effective.codes` a `permisos`. Fallback a `obtener_codigos_permiso_usuario` si resolver falla o flag desactivado. | Bajo: contrato idéntico. |
| **2** | **Servicios que escriben rol_permiso / usuario_rol** | permisos_negocio_service (set permisos por rol), user_service (asignar roles). | Tras escribir, llamar `invalidate_for_user` o `invalidate_for_tenant` según alcance. No cambian firmas públicas. | Bajo. |
| **3** | **require_permission / has_permission** | Usan `user.permisos` (ya poblado por build_user_with_roles). | Ninguno en Stage 1: siguen leyendo `user.permisos`. En Stage 2 se puede hacer que `require_permission` opcionalmente reciba un “authorization context” que incluya EffectivePermissions para no depender del user object en todos los casos (opcional). | Bajo si no se toca; medio si se introduce contexto nuevo. |
| **4** | **ModuloMenuService.get_menu_usuario** | Lee cliente_modulo + modulo_menu (central) y rol_menu_permiso (tenant); para super_admin/tenant_admin no consulta rol_menu_permiso. | En Stage 1: sin cambios. En Stage 2: opcionalmente recibir EffectivePermissions del request (o resolver) para decidir “elevado” o para filtrar ítems por permiso requerido si modulo_menu tiene permiso_requerido_id. No sustituir de golpe la lógica actual de rol_menu_permiso. | Medio: solo después de que el resolver sea estable. |
| **5** | **Middleware / tenant** | Resuelve tenant (cliente_id) y contexto. | No debe “depender del resolver” en Stage 1. En Stage 2 se puede inyectar en request.state un “authorization_context” (EffectivePermissions) si ya se calculó en un middleware posterior a auth, para evitar recalcular en build_user_with_roles; eso es opcional y solo si se unifica el punto de cálculo. | Bajo si no se toca; medio si se añade inyección. |
| **6** | **Billing / feature access (cliente_modulo)** | Consultas directas a cliente_modulo para “¿tenant tiene módulo X?”. | En Stage 2–3: consumir del resolver (o de un servicio que use el resolver) “módulos activos” o “effective_permissions” filtradas por suscripción, en lugar de consultar cliente_modulo en cada flujo. Migración gradual por flujo. | Medio: depende de cuántos sitios lean cliente_modulo. |

Resumen del orden:

1. **User builder** (único consumidor inicial del resolver).  
2. **Invalidación** desde servicios que escriben.  
3. **require_permission/has_permission** sin cambio, o con extensión opcional en Stage 2.  
4. **ModuloMenuService** solo después de resolver estable; integración opcional y gradual.  
5. **Middleware** solo si se decide unificar el punto de cálculo en un “authorization context”.  
6. **Billing/cliente_modulo** cuando el resolver (o un servicio que lo use) exponga módulos activos y se migre flujo a flujo.

No se debe invertir el orden: menú y billing no deben depender del resolver antes de que build_user_with_roles y la invalidación estén en producción y estables.

---

## 3. Integración del resolver con los demás componentes

### 3.1 require_permission()

- **Hoy:** `require_permission(perm)` depende de `get_current_active_user`; obtiene `user` con `user.permisos` ya poblado y llama `has_permission(user, perm)` → `permission in user.permisos` (y super_admin bypass).
- **Stage 1:** Sin cambios. El resolver solo alimenta `user.permisos` vía build_user_with_roles; require_permission y has_permission siguen igual.
- **Stage 2 (opcional):** Si se introduce un “AuthorizationContext” en request.state (EffectivePermissions + user_id, cliente_id), require_permission podría aceptar ese contexto como alternativa a leer del user, para desacoplar de la forma del objeto user. Contrato actual debe seguir funcionando: si se pasa user, se usa user.permisos.
- **Regla:** No duplicar la comprobación: un solo lugar (has_permission) que lee una sola fuente (user.permisos o contexto inyectado). El resolver es productor; require_permission es consumidor.

### 3.2 ModuloMenuService

- **Hoy:** get_menu_usuario combina (1) módulos activos + menús desde central, (2) permisos por ítem desde rol_menu_permiso en tenant; super_admin/tenant_admin reciben todo sin consultar rol_menu_permiso.
- **Integración deseada sin romper:**
  - El menú puede seguir construyéndose como hoy (cliente_modulo + rol_menu_permiso). No es obligatorio que el menú “dependa del resolver” en Stage 1.
  - Cuando el resolver sea la fuente de permisos de negocio y opcionalmente de “módulos activos”, ModuloMenuService puede:
    - Recibir opcionalmente EffectivePermissions (o solo `active_module_codes`) para no repetir la consulta de cliente_modulo si ya está en el contexto.
    - Si modulo_menu tiene un campo “permiso_requerido_id” (o equivalente), filtrar ítems por “usuario tiene ese permiso” usando effective.codes en lugar de (o además de) rol_menu_permiso por ítem.
  - La transición debe ser por feature flag o parámetro opcional: “usar effective_permissions para filtrar ítems por permiso” vs “usar solo rol_menu_permiso como hoy”.
- **Riesgo:** Cambiar de golpe la lógica del menú puede alterar lo que ve cada rol. Por eso la integración con el menú es posterior y opcional.

### 3.3 cliente_modulo (billing / feature access)

- **Hoy:** Varios flujos consultan cliente_modulo para saber si el tenant tiene un módulo activo (y a veces fecha_vencimiento, límites).
- **Integración:**
  - El resolver (con `filter_by_subscription=True`) ya puede devolver effective_permissions restringidas a módulos activos; opcionalmente expone `active_module_codes` en EffectivePermissions.
  - Billing y feature-flags pueden, de forma gradual, usar “¿código de módulo en effective_permissions.active_module_codes?” o un método del tipo “tiene_módulo(cliente_id, modulo_codigo)” que internamente use el resolver o un servicio que cachee módulos activos por tenant, en lugar de consultar cliente_modulo en cada flujo.
  - No mover toda la lógica de billing (precios, límites, vencimientos) al resolver; solo la parte “¿está activo el módulo?” puede centralizarse para evitar consultas repetidas y duplicación.

---

## 4. Anti-patrones a evitar durante la migración

- **Duplicación de autorización:** No mantener dos caminos que calculen “permisos del usuario” en paralelo sin que uno sea el oficial. Una vez el resolver está activo tras build_user_with_roles, no seguir llamando también a `obtener_codigos_permiso_usuario` en el mismo request. Invalidación y fallback están bien; dos fuentes de verdad en paralelo no.

- **Lógica distribuida:** No añadir nuevas comprobaciones de “¿tiene permiso X?” en servicios que recreen la lógica (ej. volver a leer rol_permiso). Esas comprobaciones deben usar `user.permisos` (o el contexto que venga del resolver) o un método único del resolver (ej. “has_permission(usuario_id, cliente_id, perm)” que lea cache/resolver), no queries propias en cada servicio.

- **Consultas repetidas:** No llamar al resolver varias veces en el mismo request para el mismo (usuario_id, cliente_id). build_user_with_roles llama una vez; si más adelante el menú o otro componente necesitan permisos, deben reutilizar el EffectivePermissions ya calculado (p. ej. en request.state) en lugar de invocar de nuevo get_effective_permissions.

- **Acoplamiento con UI:** El resolver no debe conocer rutas frontend, nombres de pantallas ni componentes. Solo códigos de permiso y, si aplica, códigos de módulo. La decisión “mostrar u ocultar botón” sigue en frontend usando los datos que el backend ya envía (menú, user.permisos).

- **Reescribir de golpe:** No sustituir en un solo release toda la lógica de menú o de billing por el resolver. Flags y migración por flujo reducen riesgo.

- **Resolver como escritor:** El resolver no debe escribir en rol_permiso, usuario_rol ni cliente_modulo; solo leer (o delegar en servicios existentes) e invalidar cache cuando otros escriben.

---

## 5. Roadmap de madurez en 3 etapas

### Stage 1: Resolver interno (centralización)

- **Objetivo:** Un único punto de cálculo y cache de permisos efectivos de negocio, con contrato idéntico al actual (`user.permisos = List[str]`), sin cambiar comportamiento funcional ni firmas públicas de require_permission/has_permission.
- **Cambios mínimos necesarios:**
  - Implementar Permission Resolver según `PERMISSION_RESOLVER_API_DESIGN.md` (get_effective_permissions, EffectivePermissions, cache, invalidación, super_admin).
  - En build_user_with_roles: bajo feature flag, llamar al resolver y asignar `effective.codes` a `permisos`; en error o flag off, mantener `obtener_codigos_permiso_usuario`.
  - En permisos_negocio_service y user_service (y cualquier escritor de usuario_rol/rol_permiso): llamar invalidate_for_user o invalidate_for_tenant tras escribir.
  - Config: flags USE_PERMISSION_RESOLVER, PERMISSION_RESOLVER_CACHE_ENABLED, PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION (opcional).
- **Riesgos:** Fallos del resolver o del cache que obliguen a fallback; diferencias sutiles (orden, duplicados) entre resolver y servicio actual. Mitigación: tests de equivalencia y fallback automático.
- **Criterio de éxito:** Con el flag activado, todos los endpoints protegidos por require_permission se comportan igual que sin flag; no hay regresiones; métricas de latencia iguales o mejores por cache; invalidación verificada al cambiar roles/permisos.

---

### Stage 2: Authorization Service (capa independiente)

- **Objetivo:** El resolver es la única fuente de verdad de permisos efectivos; opcionalmente se expone un “authorization context” por request (EffectivePermissions + tal vez módulos activos) para que servicios y menú no repitan consultas ni lógica.
- **Cambios mínimos necesarios:**
  - Resolver estable en producción como fuente única en build_user_with_roles (flag por defecto True; se puede deprecar el camino antiguo).
  - Opcional: middleware o dependencia que ponga en request.state un AuthorizationContext (EffectivePermissions ya calculado) para que ModuloMenuService u otros consuman sin segunda llamada al resolver.
  - Opcional: ModuloMenuService recibe EffectivePermissions o active_module_codes para filtrar ítems por permiso o para reutilizar módulos activos sin consultar cliente_modulo de nuevo.
  - Opcional: servicio o helper “módulos activos por tenant” que use cliente_modulo y se cachee/invalide alineado con el resolver, para que billing/feature-flags empiecen a consumirlo.
- **Riesgos:** Introducir request.state o contexto nuevo puede afectar tests y middlewares; la integración con el menú debe ser conservadora (parámetro opcional, flag).
- **Criterio de éxito:** Un solo cálculo de EffectivePermissions por request cuando se use el contexto; menú y permisos de API coherentes; ningún flujo crítico consulta rol_permiso/usuario_rol/permiso directamente para “listar permisos del usuario”; billing puede usar módulos activos desde un punto único si se implementa.

---

### Stage 3: Policy Engine SaaS (nivel enterprise)

- **Objetivo:** Soporte a políticas más ricas (condiciones sobre recurso, atributos, contexto) sin reescribir el RBAC actual; el “resolver” o una capa que lo use puede evaluar políticas además de la lista de códigos.
- **Cambios mínimos necesarios:**
  - Modelo de políticas: definiciones (ej. “puede editar si es propietario o tiene permiso X”) evaluadas en un motor que reciba usuario, tenant, acción, recurso opcional.
  - El resolver actual sigue siendo la fuente de “effective codes”; el policy engine puede consumir EffectivePermissions y añadir reglas adicionales (ABAC-style) para casos concretos, sin sustituir require_permission en la mayoría de endpoints.
  - Integración con menú y feature-flags puede usar “¿policy X pasa?” para ítems o flags avanzados.
- **Riesgos:** Complejidad y posible duplicación si no se delimita bien “qué resuelve el resolver” vs “qué resuelve el policy engine”. Mantener RBAC por códigos como base y políticas como extensión.
- **Criterio de éxito:** Casos de negocio que requieran “permiso + condición” resueltos por policy engine; permisos actuales por código siguen funcionando; documentación clara de cuándo usar código vs política.

---

## 6. Resumen: plan evolutivo realista

- **Compatibilidad:** En todo momento `user.permisos` sigue siendo una lista de strings; `has_permission(user, perm)` y `require_permission(perm)` no cambian de contrato en Stage 1 y pueden extenderse de forma opcional en Stage 2.
- **Orden de migración:** (1) build_user_with_roles + invalidación, (2) require_permission sin cambio o con contexto opcional, (3) ModuloMenuService de forma opcional y gradual, (4) middleware/contexto si se desea unificar cálculo, (5) billing/cliente_modulo cuando exista abstracción de “módulos activos” y se migre flujo a flujo.
- **Anti-patrones:** Evitar doble fuente de verdad, lógica de autorización repartida, consultas repetidas al resolver o a BD, y que el resolver conozca UI o escriba en tablas de permisos/roles.
- **Etapas:** Stage 1 = centralización y cache; Stage 2 = capa de autorización única y reutilización en menú/billing; Stage 3 = policy engine como extensión sin reemplazar el RBAC actual.

Este plan permite evolucionar el diseño actual hacia un Authorization Layer central mediante migración incremental y segura, sin reescrituras completas ni ruptura de permisos existentes.
