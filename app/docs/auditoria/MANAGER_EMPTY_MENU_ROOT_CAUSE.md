# MANAGER `/auth/menu` devuelve `modulos=[]` — Root cause (runtime)

## Resumen ejecutivo

En el tenant de prueba **`t1base4de824d1`** (`cliente_id` **`04519c7c-8dac-456a-a5bb-b0664b1a1e8b`**), el usuario **MANAGER** tiene los permisos RBAC mínimos de T1 (**`rol_permiso` OK**), pero **no tiene ningún grant UI en `rol_menu_permiso`** (**0 filas**).  

El endpoint **`GET /auth/menu`** construye el menú **exclusivamente** a partir de:

- **Estructura de menús** (BD central): `modulo_menu` filtrado por `cliente_modulo` activo.
- **Visibilidad UI** (BD del tenant): `rol_menu_permiso` (solo filas con `puede_ver=1`) agregadas por `menu_id`.

Si **`rol_menu_permiso` está vacío**, el servicio no puede “habilitar” ningún `menu_id`, por lo que el resultado combinado queda vacío y se retorna:

```json
{ "modulos": [] }
```

**Conclusión:** esto no es un problema de T1 ni del Permission Resolver; es un **gap de provisioning de `rol_menu_permiso` para MANAGER/USER** (onboarding solo sincroniza `rol_menu_permiso` para `ADMIN_TENANT`).

---

## 1) Evidencia runtime (tenant de prueba)

- **Tenant**:
  - `subdominio`: `t1base4de824d1`
  - `cliente_id`: `04519c7c-8dac-456a-a5bb-b0664b1a1e8b`
- **Manager**:
  - `usuario_id`: `245a24b1-a354-4178-b12e-8d7517681156`

### 1.1 `rol_permiso` efectivo de `MANAGER_TENANT` (permisos API)

SQL ejecutado (tenant DB):

```sql
SELECT r.rol_id, r.codigo_rol, p.codigo
FROM rol r
INNER JOIN rol_permiso rp ON rp.rol_id=r.rol_id AND rp.cliente_id=r.cliente_id
INNER JOIN permiso p ON p.permiso_id=rp.permiso_id AND p.es_activo=1
WHERE r.cliente_id = ? AND r.codigo_rol = ?
ORDER BY p.codigo;
-- params: (cliente_id, 'MANAGER_TENANT')
```

Resultado (muestra completa):

- `core.app.acceder`
- `tenant.branding.leer`
- `org.empresa.leer`

Esto confirma que **T1 BASE_OPERATIVE sí se aplicó** en RBAC (`rol_permiso`).

### 1.2 `rol_menu_permiso` efectivo del manager (visibilidad UI)

SQL ejecutado (tenant DB):

```sql
SELECT COUNT(*) AS c_total,
       SUM(CASE WHEN p.puede_ver=1 THEN 1 ELSE 0 END) AS c_ver
FROM rol_menu_permiso p
INNER JOIN usuario_rol ur ON p.rol_id=ur.rol_id AND p.cliente_id=ur.cliente_id
WHERE ur.cliente_id = ? AND ur.usuario_id = ?;
-- params: (cliente_id, manager_usuario_id)
```

Resultado:

- `c_total = 0`
- `c_ver = NULL` (equivale a 0)

Muestra (20 filas) de `puede_ver=1`:

```sql
SELECT TOP 20
       p.menu_id, p.puede_ver, p.puede_crear, p.puede_editar, p.puede_eliminar,
       p.puede_exportar, p.puede_imprimir, p.puede_aprobar
FROM rol_menu_permiso p
INNER JOIN usuario_rol ur ON p.rol_id=ur.rol_id AND p.cliente_id=ur.cliente_id
WHERE ur.cliente_id = ? AND ur.usuario_id = ? AND p.puede_ver = 1
ORDER BY p.menu_id;
```

Resultado: **0 filas**.

**Interpretación:** para el manager, la capa UI (`rol_menu_permiso`) está totalmente vacía → no hay menús “visibles”.

---

## 2) Qué consulta usa `/auth/menu` (MenuResolver → ModuloMenuService)

### 2.1 Endpoint

`GET /auth/menu` llama a `MenuResolverService.get_menu_for_user()` y luego a `ModuloMenuService.obtener_menu_usuario()`.

### 2.2 Query 1 (BD central): estructura de módulos/secciones/menús del tenant

En `ModuloMenuService.obtener_menu_usuario`, el primer paso consulta `modulo_menu` (central) y filtra por `cliente_modulo` activo del tenant:

- fuente: `app/modules/modulos/application/services/modulo_menu_service.py` (QUERY 1)
- devuelve **todos los `menu_id`** posibles para el tenant (contratados + visibles).

### 2.3 Query 2 (BD del tenant): permisos de menú por usuario (rol_menu_permiso)

Después, `ModuloMenuService` ejecuta esta query RAW (tal como está en código) para traer permisos agregados por `menu_id`:

```sql
SELECT p.menu_id,
       MAX(CAST(p.puede_ver AS INT)) AS puede_ver,
       MAX(CAST(p.puede_crear AS INT)) AS puede_crear,
       MAX(CAST(p.puede_editar AS INT)) AS puede_editar,
       MAX(CAST(p.puede_eliminar AS INT)) AS puede_eliminar,
       MAX(CAST(p.puede_exportar AS INT)) AS puede_exportar,
       MAX(CAST(p.puede_imprimir AS INT)) AS puede_imprimir,
       MAX(CAST(p.puede_aprobar AS INT)) AS puede_aprobar
FROM rol_menu_permiso p
INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id
WHERE ur.usuario_id = ?
  AND ur.cliente_id = ?
  AND ur.es_activo = 1
  AND (ur.fecha_expiracion IS NULL OR ur.fecha_expiracion > GETDATE())
  AND p.cliente_id = ?
  AND p.menu_id IN (?,?,... N menu_ids ...)
  AND p.puede_ver = 1
GROUP BY p.menu_id;
```

**Punto crítico:** la query filtra por `p.puede_ver = 1`.  
Si no existen filas en `rol_menu_permiso` para los roles del usuario, el resultado es **0** menús.

### 2.4 Regla final (por qué queda vacío)

El servicio combina Query 1 + Query 2, pero **solo incluye** menús cuyo `menu_id` aparece en `permisos_por_menu` y `puede_ver=True`.  
Si Query 2 trae 0 filas, `resultado_combinado` queda vacío y retorna:

```json
{ "modulos": [] }
```

---

## 3) ¿T1 BASE_OPERATIVE toca `rol_permiso` o también `rol_menu_permiso`?

T1 BASE_OPERATIVE **solo inserta `rol_permiso`** (RBAC / permisos API). No inserta `rol_menu_permiso`.

Evidencia (código): `BaseOperativeService` es explícito: “Provisiona bundle BASE_OPERATIVE … INSERT rol_permiso…”.

**Implicación:** aunque el manager tenga RBAC para endpoints (ej. branding), el menú UI puede seguir vacío si no existe provisioning de `rol_menu_permiso`.

---

## 4) Root cause

### 4.1 Causa directa

**`rol_menu_permiso` vacío para MANAGER (0 filas)** → Query 2 retorna 0 → no hay `menu_id` visibles → `/auth/menu` retorna `modulos=[]`.

### 4.2 Causa sistémica (provisioning)

El bootstrap de `rol_menu_permiso` en onboarding (OwnerSync) está implementado para **`ADMIN_TENANT`**, pero **no** para `MANAGER_TENANT` / `USER_TENANT`.

Por diseño actual del Menu Resolver:

- `rol_permiso` controla **API RBAC** (Permission Resolver).
- `rol_menu_permiso` controla **visibilidad/acciones UI** del menú.

Si el tenant no tiene grants UI para MANAGER/USER, **el menú será vacío aunque RBAC esté correcto**.

---

## 5) Qué falta para que MANAGER vea ORG/INV (diagnóstico, no implementación)

Para que un MANAGER tenga módulos/menús visibles en `/auth/menu`, debe existir provisioning en `rol_menu_permiso` (y/o un proceso que lo derive) para:

- el rol asignado al usuario (`usuario_rol.rol_id`)
- el `cliente_id` del tenant
- los `menu_id` que correspondan a ORG/INV (y a los módulos contratados del tenant)
- con `puede_ver = 1` (mínimo)

Hoy, en el tenant de prueba, ese set es **vacío** para MANAGER.

