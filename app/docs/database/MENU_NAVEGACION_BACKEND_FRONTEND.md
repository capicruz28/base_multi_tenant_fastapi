# Menú de navegación (modulo_menu): consumo en frontend y rendimiento

Este documento aclara cómo se exponen los datos de **modulo_menu** en el backend, qué endpoint debe usar el frontend para el sidebar, y qué puede estar causando lentitud.

---

## 1. Estructura de datos (modulo_menu en BD)

En **TABLAS_BD_CENTRAL.sql** la tabla relevante es:

- **modulo_menu**: menús de navegación por módulo/sección (modulo_id, seccion_id, cliente_id, menu_padre_id, nombre, ruta, icono, orden, nivel, etc.).
- Jerarquía: **Módulo → Sección → Menú → Submenús** (menu_padre_id).
- Los permisos del usuario sobre cada menú están en **rol_menu_permiso** (en BD central o en BD dedicada según el cliente).

---

## 2. Endpoints que devuelven menú (árbol / lista)

Hay **dos sistemas de menú** en el backend; para el sidebar basado en **modulo_menu** solo aplica uno.

### 2.1 Sistema correcto para sidebar (modulo_menu)

| Método | Ruta | Descripción |
|--------|------|-------------|
| **GET** | **`/api/v1/modulos-menus/me/`** | **Recomendado.** Menú del usuario actual (token). Sin parámetros en URL. Diferenciación automática: usuario normal, admin tenant, SuperAdmin. |
| **GET** | **`/api/v1/modulos-menus/usuario/{usuario_id}/`** | Menú de un usuario por ID (mismo tenant). Útil para admin/soporte. SuperAdmin ve todo solo cuando pide su propio menú. |

- **Prefijo en API:** `prefix="/modulos-menus"` (ver `app/api/v1/api.py`).
- **Recomendación frontend:** Usar **`GET /api/v1/modulos-menus/me/`** para el sidebar (una sola petición, no requiere enviar `usuario_id` ni `cliente_id`).
- **Respuesta (ambos):** `MenuUsuarioResponse`:
  - `modulos`: array de módulos.
  - Cada módulo tiene `secciones`; cada sección tiene `menus`.
  - Cada ítem de menú tiene: `menu_id`, `nombre`, `ruta`, `icono`, `permisos` (ver, crear, editar, eliminar, exportar, imprimir, aprobar), `submenus` (recursivo).

Documentación detallada para el frontend: **DOC_FRONTEND_MENU_NAVEGACION.md**.

### 2.2 Otros endpoints de modulos-menus (no para cargar el árbol del sidebar)

- `GET /api/v1/modulos-menus/modulo/{modulo_id}/` → Lista **plana** de menús de un módulo (para admin, no árbol completo de navegación).
- `GET /api/v1/modulos-menus/{menu_id}/` → Detalle de un menú.
- El resto son CRUD (crear, actualizar, eliminar, etc.).

Si el frontend usa **varios** `GET .../modulo/{modulo_id}/` (uno por módulo) para construir el sidebar, eso implica **N peticiones** y explica que tarde mucho. Debe usar **una sola** llamada a `GET .../usuario/{usuario_id}/`.

### 2.3 Sistema legacy (no modulo_menu)

- **GET /api/v1/menus/getmenu/** → Usa `sp_GetMenuForUser` y tablas antiguas (menu/area), **no** la tabla `modulo_menu`.
- **GET /api/v1/menus/all-structured/** → Árbol completo para admin, también sobre el modelo antiguo.

Para el sidebar basado en **modulo_menu** (catálogo de módulos ERP), no uses estos; usa solo `/api/v1/modulos-menus/usuario/{usuario_id}/`.

---

## 3. Cómo se consumen los datos en el backend (por qué puede ir lento)

El endpoint `GET /api/v1/modulos-menus/usuario/{usuario_id}/` está implementado en:

- **Servicio:** `ModuloMenuService.obtener_menu_usuario(usuario_id, cliente_id)`.
- **Flujo actual:**
  1. **Query 1 (BD central – ADMIN):** módulos activos del cliente + secciones + todos los ítems de **modulo_menu** (JOIN modulo, modulo_seccion, modulo_menu, cliente_modulo).
  2. **Query 2 (BD del cliente – DEFAULT):** permisos del usuario sobre esos menús (rol_menu_permiso + usuario_rol), filtrando por `menu_id IN (...)`.
  3. **En Python:** se combinan ambos resultados, se filtran solo los menús con `puede_ver`, y se arma la jerarquía (módulo → sección → menú → submenús) con `transformar_sp_menu_usuario`.

No se usa el stored procedure **sp_obtener_menu_usuario** en este flujo (en arquitectura híbrida, módulos/menús están en central y permisos en BD del cliente, por eso se hacen 2 consultas).

Posibles causas de lentitud:

- Muchos ítems en **modulo_menu** y muchos `menu_id` en el `IN` de la segunda query.
- Varios JOINs en la primera query sin índices adecuados.
- El frontend hace **varias** peticiones (por módulo o por sección) en lugar de **una** a `/usuario/{usuario_id}/`.

---

## 4. Resumen para el frontend

- **¿Existe un endpoint que devuelva todo el árbol completo de menú de navegación?**  
  **Sí:** `GET /api/v1/modulos-menus/me/` (recomendado) o `GET /api/v1/modulos-menus/usuario/{usuario_id}/`.
- **Uso recomendado:**  
  - Una sola llamada a **`GET /api/v1/modulos-menus/me/`** (no hace falta pasar `usuario_id` ni `cliente_id`).  
  - No llamar en bucle a `/modulos-menus/modulo/{modulo_id}/` para construir el sidebar.
- **Formato de respuesta:**  
  Jerarquía: `modulos[] → secciones[] → menus[]` (cada menú con `submenus[]` y `permisos`).
- **Documentación para frontend:** Ver **DOC_FRONTEND_MENU_NAVEGACION.md**.

---

## 5. Recomendaciones (qué hacer si sigue lento)

### 5.1 Frontend

1. **Una sola petición para el sidebar**  
   Usar únicamente `GET /api/v1/modulos-menus/usuario/{usuario_id}/` con el usuario actual. Evitar N peticiones por módulo o por sección.
2. **Cachear la respuesta**  
   El menú suele cambiar poco; cachear en memoria o en almacenamiento local (por sesión) y refrescar solo al hacer logout o cada X minutos.
3. **No bloquear la UI**  
   Mostrar el layout/skeleton del sidebar de inmediato y rellenar los ítems cuando llegue la respuesta del menú.

### 5.2 Backend (opcional, para mejorar tiempos)

1. **Endpoint “me” para menú**  
   Añadir algo como `GET /api/v1/modulos-menus/me/` que use el `usuario_id` (y `cliente_id`) del token. Así el frontend no necesita pasar `usuario_id` y se evitan errores de uso.
2. **Cache con TTL corto**  
   Cachear la respuesta de `obtener_menu_usuario` por `(usuario_id, cliente_id)` con TTL de 1–5 minutos e invalidar al cambiar permisos/roles.
3. **Índices en BD**  
   Revisar índices en:
   - `modulo_menu` (modulo_id, seccion_id, menu_padre_id, es_activo, orden).
   - `rol_menu_permiso` (cliente_id, rol_id, menu_id).
   - `usuario_rol` (usuario_id, cliente_id, es_activo).
4. **Usar SP en Single-DB**  
   Si el cliente usa solo BD central (single-DB), se podría usar el SP `sp_obtener_menu_usuario` en una sola llamada para reducir trabajo en Python y round-trips. En híbrido (central + BD dedicada) el flujo actual de 2 queries es coherente con la arquitectura.

---

## 6. Checklist rápido

| Pregunta | Respuesta |
|----------|-----------|
| ¿Endpoint recomendado para el sidebar? | **`GET /api/v1/modulos-menus/me/`** (sin parámetros; usa token). |
| ¿Endpoint alternativo por usuario_id? | **`GET /api/v1/modulos-menus/usuario/{usuario_id}/`** |
| ¿Una sola llamada suficiente para el sidebar? | **Sí.** Una llamada a `/me/`. |
| ¿SuperAdmin ve todo el menú? | **Sí.** Cuando llama a `/me/` o a `/usuario/{su_id}/`, recibe todos los menús del tenant con permisos completos. |
| ¿Dónde está la tabla? | **modulo_menu** en BD central (TABLAS_BD_CENTRAL.sql). |
| Documentación para frontend | **DOC_FRONTEND_MENU_NAVEGACION.md** |
