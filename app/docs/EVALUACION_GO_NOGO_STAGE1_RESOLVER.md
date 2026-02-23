# Evaluación GO/NO-GO: Stage 1 — Resolver interno

**Rol:** Principal SaaS Architect  
**Objetivo:** Determinar si el proyecto está listo para iniciar la implementación de Stage 1 (Permission Resolver interno) según el plan de evolución.  
**Referencias:** `EVOLUCION_PERMISSION_RESOLVER_AUTHORIZATION_LAYER.md`, `PERMISSION_RESOLVER_API_DESIGN.md`, código actual.

---

## 1. Precondiciones técnicas ya cumplidas

| Precondición | Estado | Evidencia |
|--------------|--------|-----------|
| **Un único consumidor de la lista de permisos** | ✅ Cumplida | Solo `build_user_with_roles()` llama a `obtener_codigos_permiso_usuario()` y asigna `user.permisos`. No hay otros call sites que deban migrarse en Stage 1. |
| **Contrato estable** | ✅ Cumplida | `UsuarioReadWithRoles.permisos: List[str]` y `has_permission(user, perm)` con `permission in user.permisos`. El resolver solo debe exponer `.codes` equivalente. |
| **Servicio de origen reutilizable** | ✅ Cumplida | `permisos_usuario_service.obtener_codigos_permiso_usuario(usuario_id, cliente_id, database_type)` existe, soporta single y multi BD, y puede ser invocado por el resolver o su lógica replicada sin cambiar firmas públicas. |
| **Contexto de tenant y usuario disponible** | ✅ Cumplida | En `build_user_with_roles` ya se tienen `usuario_id`, `cliente_id`, `database_type` (vía `try_get_tenant_context()`), e `is_superadmin` (derivado de roles). El resolver recibe todo lo necesario sin nuevos middleware. |
| **Patrón de feature flags** | ✅ Cumplida | `config.py` usa flags tipo `ENABLE_*` con `os.getenv(..., "true").lower() == "true"`. Añadir `USE_PERMISSION_RESOLVER`, `PERMISSION_RESOLVER_CACHE_ENABLED`, `PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION` es consistente. |
| **Infraestructura de cache** | ✅ Cumplida | `ENABLE_REDIS_CACHE`, `REDIS_*`, `CACHE_DEFAULT_TTL`; `get_cached`/`set_cached` en `infrastructure/cache/redis_cache.py` con fallback en memoria. El resolver puede usar la misma capa. |
| **Invalidación en otros dominios** | ✅ Cumplida | Ya existe `invalidate_client_connection_cache` (tenant routing) y `connection_cache.invalidate(client_id)`. El patrón de invalidación está establecido; el resolver añade sus propias claves y métodos. |
| **Puntos de escritura identificados** | ✅ Cumplida | Escrituras en `rol_permiso`: `permisos_negocio_service.set_permisos_negocio_rol`. Escrituras en `usuario_rol`: `user_service` (asignar/desasignar roles). Son los únicos que deben llamar a invalidación en Stage 1. |
| **Sin dependencia del menú ni billing** | ✅ Cumplida | Stage 1 no toca ModuloMenuService ni cliente_modulo. El menú sigue usando rol_menu_permiso y cliente_modulo como hoy. |
| **Diseño y API definidos** | ✅ Cumplida | `PERMISSION_RESOLVER_API_DESIGN.md` y plan de evolución describen firma, EffectivePermissions, cache keys, invalidación y super_admin. |

---

## 2. Dependencias o acoplamientos que podrían bloquear Stage 1

| Dependencia / acoplamiento | ¿Bloquea? | Notas |
|----------------------------|-----------|--------|
| **Redis no disponible** | ❌ No bloquea | El diseño permite cache desactivado o fallback en memoria. Si Redis está caído, el resolver puede operar sin cache (igual que hoy, una query por request). |
| **Múltiples call sites de permisos** | ❌ No existe | Solo un consumidor; no hay que coordinar varios puntos de migración. |
| **require_permission / has_permission** | ❌ No bloquean | No cambian en Stage 1; siguen leyendo `user.permisos`. Ninguna firma depende del resolver. |
| **Tests de equivalencia de permisos** | ⚠️ GAP | No hay tests automatizados que comparen resultado de `obtener_codigos_permiso_usuario` vs un resolver. No bloquean implementar, pero son **precondición recomendada** para considerar la migración segura (ver checklist). |
| **Config sin flags del resolver** | ❌ No bloquea | Añadir tres variables en `config.py` es trabajo mínimo y forma parte de la implementación de Stage 1. |
| **Escritores sin llamada a invalidación** | ❌ No bloquea | Hoy no llaman a ningún resolver porque no existe. Al implementar Stage 1, se añaden las llamadas a `invalidate_for_user` / `invalidate_for_tenant` en `set_permisos_negocio_rol` y en los flujos de user_service que modifican usuario_rol. No es un acoplamiento previo que impida empezar. |
| **BD dedicada (multi)** | ❌ No bloquea | La lógica ya está en `permisos_usuario_service` (tenant + central). El resolver puede delegar en ese servicio o replicar las mismas dos consultas; no hay dependencia nueva de infra. |

**Conclusión:** No hay dependencias técnicas que impidan iniciar Stage 1. El único gap es la ausencia de tests de equivalencia, que debe cubrirse en el checklist antes de dar por cerrada la migración.

---

## 3. Riesgos reales al introducir el resolver

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Resolver lanza excepción o timeout** | Media | Alto si no hay fallback | Fallback obligatorio en `build_user_with_roles`: en caso de error, llamar a `obtener_codigos_permiso_usuario` y asignar su resultado a `permisos`. No propagar el error al usuario. |
| **Diferencias sutiles (orden, duplicados)** | Baja | Bajo | `has_permission` usa `permission in user.permisos`; el orden no importa. Duplicados no rompen `in`. Si se quiere equivalencia exacta, tests que comparen conjuntos (set) de códigos. |
| **Cache desactualizado tras cambiar roles/permisos** | Media si no se invalida | Alto | Invocar `invalidate_for_user` o `invalidate_for_tenant` en los puntos de escritura definidos. Incluir esta llamada en la implementación de Stage 1 y verificar en pruebas manuales o E2E. |
| **Super_admin con cache** | Baja | Bajo | Diseño: no cachear cuando `is_super_admin=True`. Implementar ese bypass desde el inicio. |
| **Redis caído en producción** | Depende del entorno | Medio | Resolver debe degradar a “sin cache” o usar fallback en memoria por proceso. La capa de cache existente ya tiene fallback; el resolver debe usarla y no asumir Redis siempre disponible. |
| **Regresión en permisos (403 donde antes no)** | Baja con fallback | Alto | Con fallback a `obtener_codigos_permiso_usuario`, el comportamiento debe ser idéntico si el resolver falla. Con resolver OK, la equivalencia se valida con tests y métricas de 403. |

Ningún riesgo es bloqueante si se implementan fallback, invalidación y criterios de éxito (métricas y checklist).

---

## 4. Métricas para validar que la migración fue segura

| Métrica | Qué medir | Criterio de éxito |
|---------|-----------|-------------------|
| **Tasa de 403 en endpoints protegidos** | Comparar antes/después por endpoint o global (con flag activado). | No aumento significativo (idealmente igual). Cualquier aumento debe investigarse (posible regresión). |
| **Latencia de flujo de autenticación** | Latencia de `get_current_active_user` o del primer request autenticado (p50, p95). | Con cache activo: igual o mejor. Sin cache: igual al baseline actual. |
| **Tasa de fallback** | Cuántas veces en un periodo se usó `obtener_codigos_permiso_usuario` porque el resolver falló o lanzó. | Estable y baja; si es alta, revisar salud del resolver y de Redis. |
| **Cache hit rate de permisos** | (Requests con hit) / (Requests que llamaron al resolver). | En tráfico estable, > 0 cuando cache está habilitado; valor concreto según TTL y patrones de uso. |
| **Errores 5xx en rutas que usan get_current_active_user** | Errores en login o en cualquier endpoint que dependa del usuario activo. | Sin aumento atribuible al resolver; si el resolver falla, el fallback debe evitar 5xx. |
| **Equivalencia funcional** | Test (manual o automatizado): mismo usuario/tenant, comparar lista de códigos del servicio actual vs resolver (conjunto igual). | 100% de coincidencia en muestras representativas (incl. super_admin, multi BD si aplica). |

Recomendación: tener un baseline de 403 y latencia antes de activar el flag en producción, y comparar durante un periodo de roll-out (ej. 24–48 h).

---

## 5. Checklist exacto de preparación antes de implementar

- [ ] **Docs de diseño disponibles y revisados:** `PERMISSION_RESOLVER_API_DESIGN.md`, `EVOLUCION_PERMISSION_RESOLVER_AUTHORIZATION_LAYER.md` (Stage 1). Equipo alineado en contrato y fallback.
- [ ] **Feature flags definidos en config:** Añadir `USE_PERMISSION_RESOLVER` (default False), `PERMISSION_RESOLVER_CACHE_ENABLED` (default False inicialmente), `PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION` (default False). Sin implementar aún el resolver, solo las variables.
- [ ] **Test de equivalencia de permisos:** Al menos un test (unit o integration) que, para un mismo (usuario_id, cliente_id, database_type), compare el conjunto de códigos devuelto por `obtener_codigos_permiso_usuario` y el que devolverá el resolver (misma entrada). Incluir caso sin permisos, con varios roles, y si aplica super_admin (resolver debe devolver is_super_admin=True y no depender de la lista para acceso). Este ítem puede cumplirse en paralelo a la implementación pero antes de activar el flag en producción.
- [ ] **Puntos de invalidación acordados:** Confirmar que se invocará invalidación en (1) `permisos_negocio_service.set_permisos_negocio_rol` (invalidate_for_tenant(cliente_id) o por rol si luego se implementa), (2) cada flujo de user_service que cree/actualice/desactive asignaciones en usuario_rol (invalidate_for_user(usuario_id, cliente_id)).
- [ ] **Estrategia de roll-out:** Decidir entorno (dev → staging → prod), activación por flag sin redeploy si es posible, y criterio para rollback (desactivar flag y, si hace falta, limpiar claves de cache del resolver).
- [ ] **Baseline de métricas:** Registrar tasa de 403 y latencia (p50/p95) del flujo auth o primeros requests autenticados antes de activar el resolver en cada entorno.
- [ ] **Redis/cache:** Confirmar que en producción Redis está disponible y que la capa de cache tiene fallback en memoria (ya existe). Si Redis no se usa, el resolver puede trabajar con cache desactivado.

No es obligatorio tener tests E2E de todos los endpoints protegidos; sí es obligatorio tener fallback y, antes de considerar Stage 1 “completo”, tests de equivalencia y métricas estables.

---

## 6. Veredicto GO / NO-GO

### GO — con condiciones

El proyecto **está listo para iniciar Stage 1** desde el punto de vista arquitectónico y de dependencias:

- Hay un único consumidor, contrato claro, servicio reutilizable, contexto disponible, feature flags y cache existentes, y puntos de escritura identificados.
- No hay acoplamientos que impidan la implementación; el único gap (tests de equivalencia) se cubre en el checklist antes de dar por segura la migración.
- Los riesgos son controlables con fallback, invalidación y métricas.

**Condiciones para considerar Stage 1 cerrado y seguro:**

1. Implementar **fallback** en `build_user_with_roles`: ante cualquier fallo del resolver (excepción, timeout), usar `obtener_codigos_permiso_usuario` y asignar su resultado a `permisos`.
2. Implementar **invalidación** en los escritores (set_permisos_negocio_rol y flujos de usuario_rol en user_service).
3. Cumplir el **checklist de preparación** (en particular test de equivalencia y baseline de métricas) antes de activar el flag en producción.
4. No activar `USE_PERMISSION_RESOLVER` en producción hasta tener métricas post-activación y confirmar que no hay aumento de 403 ni degradación de latencia.

**NO-GO** solo si, antes de empezar, se detectara algo no contemplado aquí (por ejemplo, otro consumidor directo de `obtener_codigos_permiso_usuario` que no sea build_user_with_roles, o un requisito de negocio que exija no tocar el flujo de auth en absoluto). Con el estado actual del código y del diseño, no hay evidencia de ello.

---

**Resumen:** GO para iniciar Stage 1. Implementación con feature flag y fallback; completar checklist (sobre todo equivalencia y métricas) antes de dar por segura la migración y activar el resolver en producción.
