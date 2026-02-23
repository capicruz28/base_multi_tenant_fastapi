# Coherencia auditorías vs prompt de implementación — Respuesta al cliente

**Objetivo:** Responder si las auditorías y el último prompt son coherentes, si el proyecto puede dañarse, qué recomendar y si el prompt logra el objetivo. **Sin implementar nada.**

---

## 1. ¿Las auditorías y el prompt son coherentes para mejorar el proyecto?

**Sí, con un matiz importante de alcance.**

- **En qué coinciden:**
  - Objetivo: Permission Resolver como fuente única de verdad de autorización.
  - No romper funcionalidad; mantener compatibilidad; migración progresiva.
  - Cache (in-memory o Redis con fallback), invalidación, logging de decisiones.
  - No eliminar código antiguo hasta estar migrado; no cambiar interfaces públicas de API.
  - Resolver integrado con el flujo actual (build_user_with_roles → user.permisos → require_permission/has_permission).

- **Diferencia de alcance:**
  - **Auditorías (EVOLUCION_PERMISSION_RESOLVER_AUTHORIZATION_LAYER):** Orden explícito: **Stage 1** = solo resolver + cache + build_user_with_roles + invalidación. **ModuloMenuService y billing/cliente_modulo en Stage 2**, “solo después de que el resolver sea estable” y de forma opcional/gradual.
  - **Tu prompt:** Pide “integrar el resolver con require_permission(), ModuloMenuService y cliente_modulo (billing)” en el mismo enunciado.

Si se interpreta “integrar” como “hacer que todo dependa del resolver en la primera entrega”, **no es coherente** con las auditorías: aumentaría riesgo y concentraría muchos cambios a la vez.  
Si se interpreta “integrar” como: (a) **require_permission:** que siga leyendo `user.permisos` alimentado por el resolver vía build_user_with_roles (sin tocar la firma de require_permission); (b) **ModuloMenuService y billing:** preparar puntos de integración opcionales (parámetros, helpers) pero **sin sustituir aún** la lógica actual de rol_menu_permiso/cliente_modulo, entonces **sí es coherente** y alineado con las auditorías.

**Conclusión:** Las auditorías y el prompt son coherentes para mejorar el proyecto **si la implementación se hace en fases**: primero Stage 1 (resolver + build_user_with_roles + invalidación + cache), y en una segunda fase la integración real con menú y billing.

---

## 2. ¿Puedes asegurarte de que no tendrás problemas y que el proyecto no se dañará ni romperá nada?

**No al 100%** — ningún cambio de esta envergadura puede garantizarse sin pruebas—, pero **sí se puede reducir el riesgo a un nivel aceptable** si se cumplen las condiciones que ya marcan las auditorías y el GO/NO-GO:

- **Fallback obligatorio:** Si el resolver falla (excepción, timeout), se usa `obtener_codigos_permiso_usuario` y se asigna su resultado a `user.permisos`. Así, un fallo del resolver no rompe el flujo de auth ni genera 5xx.
- **Feature flag:** El resolver se activa con `USE_PERMISSION_RESOLVER=True`. Con el flag en False, el comportamiento es idéntico al actual. Puedes rollback sin redeploy.
- **Sin tocar menú ni billing en Stage 1:** ModuloMenuService y cliente_modulo siguen como hoy. No se sustituye rol_menu_permiso ni las consultas a cliente_modulo en la primera entrega. Eso evita regresiones en menú o en feature access.
- **Invalidación en escritores:** Llamar a invalidación en set_permisos_negocio_rol y en los flujos de user_service que modifican usuario_rol. Sin esto, el cache podría servir datos viejos; con esto, el riesgo de permisos desactualizados se controla.
- **Test de equivalencia y métricas:** Antes de dar por cerrada la migración (y antes de activar en producción si aplica), tener al menos un test que compare el conjunto de códigos del servicio actual vs el resolver, y un baseline de 403/latencia para comparar después.

Con eso, **el proyecto no debería “romperse”** en el sentido de dejar de funcionar: el fallback y el flag protegen. Lo que sí puede pasar son **diferencias sutiles** (p. ej. orden o duplicados en la lista de códigos); las auditorías ya indican que `has_permission` usa `in`, así que el orden no importa y los duplicados no rompen. Para estar más tranquilo, el test de equivalencia debe comparar conjuntos (set).

**Resumen:** No hay garantía absoluta, pero si implementas Stage 1 con fallback, flag, invalidación y sin tocar menú/billing, y luego validas con test de equivalencia y métricas, el riesgo de dañar el proyecto es bajo y manejable.

---

## 3. ¿Qué recomendarías como lo mejor?

Recomendación en tres puntos:

1. **Implementar en dos fases claras**
   - **Fase A (Stage 1):** Permission Resolver + cache in-memory (o capa desacoplada que luego pueda usar Redis), EffectivePermissions, integración **solo** en build_user_with_roles (bajo flag) con fallback, invalidación en permisos_negocio_service y user_service. **No** cambiar ModuloMenuService ni flujos de billing/cliente_modulo; require_permission no se toca (solo recibe user.permisos ya llenado por el resolver).
   - **Fase B (Stage 2):** Una vez estable el resolver y validado con tests/métricas, añadir integración opcional con ModuloMenuService (p. ej. recibir EffectivePermissions o active_module_codes para no repetir consultas o para filtrar ítems por permiso si modulo_menu tiene permiso_requerido_id) y con billing/cliente_modulo (consumir “módulos activos” desde el resolver o un servicio que use el resolver), de forma gradual y con flags si hace falta.

2. **Respetar el checklist del GO/NO-GO**
   - Flags en config, fallback, invalidación, test de equivalencia (aunque sea uno por escenario representativo), y baseline de métricas si vas a activar en un entorno tipo producción. No eliminar código antiguo hasta que el resolver esté activado y estable.

3. **No hacer en la primera entrega**
   - Sustituir de golpe la lógica del menú (rol_menu_permiso) por el resolver.
   - Hacer que billing dependa obligatoriamente del resolver desde el primer release.
   - Cambiar la firma o el comportamiento de require_permission/has_permission (salvo que en el futuro decidas un “authorization context” opcional en Stage 2).

Con eso se alinea el trabajo con las auditorías y se minimiza el riesgo de romper algo.

---

## 4. ¿Con el prompt entregado se logrará el objetivo?

**Sí**, siempre que el prompt se ejecute **con el alcance en fases** que indican las auditorías:

- **Objetivo:** “Convertir el Permission Resolver en la fuente única de verdad de autorización.”
  - Se logra en Stage 1 para **permisos de negocio**: el único productor de la lista de códigos será el resolver (vía build_user_with_roles). require_permission/has_permission siguen siendo el único punto de evaluación, pero la **fuente de datos** de esa evaluación pasa a ser el resolver.
  - Para **menú y billing**, la “fuente única” se logra en Stage 2 cuando esos flujos consuman EffectivePermissions o módulos activos desde el resolver en lugar de repetir consultas; el prompt puede cumplirse haciendo esa integración en la segunda fase.

- **Interpretación recomendada del prompt:**
  - “Integra el resolver con require_permission()” → que require_permission siga usando `user.permisos` y que esa lista la llene el resolver en build_user_with_roles (sin cambiar la interfaz de require_permission).
  - “Integra con ModuloMenuService” → en Stage 1: no cambiar la lógica actual del menú; opcionalmente añadir parámetros o helpers para que en Stage 2 ModuloMenuService pueda recibir EffectivePermissions. En Stage 2: usar esos parámetros y, si se desea, filtrar ítems por permiso cuando esté definido.
  - “Integra con cliente_modulo (billing)” → en Stage 1: no cambiar los flujos que hoy leen cliente_modulo. En Stage 2: exponer “módulos activos” (o un helper) desde el resolver o un servicio que lo use, y migrar gradualmente los flujos de billing a consumir eso.

Si quien implemente hace **todo** en un solo paso (resolver + cambio de menú + cambio de billing), el objetivo también se logra pero con **mayor riesgo** y en desacuerdo con el orden que marcan las auditorías. Si se hace en **dos fases** como arriba, el objetivo se logra y se mantiene la coherencia con las auditorías y con un riesgo controlado.

---

## 5. Resumen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Auditorías y prompt son coherentes? | Sí, si la implementación se hace en fases: Stage 1 (resolver + build_user_with_roles + invalidación) y Stage 2 (menú y billing opcional/gradual). |
| ¿El proyecto se puede dañar o romper? | Riesgo bajo si hay fallback, feature flag, invalidación y no se toca menú/billing en Stage 1. Sin esas condiciones, el riesgo sube. |
| ¿Qué recomiendas? | Fase A = solo Stage 1; Fase B = integración con ModuloMenuService y cliente_modulo. Respetar checklist GO/NO-GO y no sustituir menú/billing en la primera entrega. |
| ¿El prompt logra el objetivo? | Sí: el resolver como fuente única de verdad se logra para permisos de negocio en Stage 1, y para menú/billing en Stage 2 si se integra entonces. |

Cuando decidas proceder, conviene indicar explícitamente si quieres **solo Stage 1** en la primera implementación o **Stage 1 + puntos de integración preparados (sin sustituir lógica) para menú y billing**. Con eso se puede bajar a un plan de cambios paso a paso y a la implementación concreta sin ambigüedades.
