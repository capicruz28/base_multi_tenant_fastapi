# Patrones y convenciones RBAC del proyecto

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Estado:** Oficial — obligatorio para todos los endpoints actuales y futuros.

Este documento declara el estándar arquitectónico RBAC del proyecto. Cualquier endpoint nuevo **debe** cumplir Patrón A o Patrón B y la convención de permisos descrita.

---

## 1. Patrón A — Dominio de negocio (CANÓNICO)

**Uso obligatorio en:** módulos de negocio (HCM, LOG, INV, FIN, PUR, SLS, WMS, QMS, CRM, POS, MFG, MRP, MPS, MNT, CST, TAX, BDG, PM, SVC, TKT, DMS, WFL, BI, AUD y cualquier recurso funcional equivalente).

### 1.1 Estructura

- El permiso se declara como **dependencia del handler**, no en el decorador.
- Se usan dos dependencias:
  1. `get_current_active_user` (auth).
  2. `require_permission("<modulo>.<recurso>.<accion>")` (autorización).

El permiso puede inyectarse como parámetro “silencioso” (`_`) para no alterar la firma lógica del handler.

### 1.2 Forma oficial

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

# Opcional: metadata para auto-registro y consistencia
MODULE_CODE = "hcm"
RESOURCE_CODE = "empleado"

router = APIRouter()


@router.get("", response_model=...)
async def listar_recurso(
    # ... parámetros de query/path/body ...
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")
    ),
):
    ...
```

### 1.3 Reglas

- **Orden de dependencias:** primero `current_user`, después el permiso (parámetro `_`).
- No cambiar paths, nombres de funciones, schemas ni lógica; solo añadir la dependencia de permiso.
- El código de permiso debe seguir la convención `<modulo>.<recurso>.<accion>` (ver sección 3).
- Acción según método HTTP: GET → `leer`, POST → `crear`, PUT/PATCH → `actualizar`, DELETE → `eliminar`.

---

## 2. Patrón B — Admin / System

**Uso obligatorio en:** gestión de usuarios, roles, permisos, módulos (catálogo/activación), menús/plantillas/secciones y cualquier endpoint administrativo global (tenant, superadmin).

### 2.1 Estructura

- El permiso se declara en el **decorador** del endpoint, en `dependencies`.
- Se combina con `require_admin` (RoleChecker) cuando el endpoint es solo para administradores del tenant.

### 2.2 Forma oficial

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user, RoleChecker
from app.core.authorization.rbac import require_permission

require_admin = RoleChecker(["Administrador"])
router = APIRouter()


@router.get(
    "/",
    dependencies=[
        Depends(require_admin),
        Depends(require_permission("admin.usuario.leer")),
    ],
)
async def listar_usuarios(
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    ...
):
    ...
```

### 2.3 Reglas

- Mantener **orden:** `require_admin` y luego `require_permission`.
- Códigos de permiso del espacio `admin.<recurso>.<accion>` o `modulos.menu.leer|administrar` según el módulo (ver excepciones).
- No eliminar ni reordenar dependencias existentes; solo añadir si falta el permiso.

---

## 3. Convención oficial de permisos

### 3.1 Formato

```
<modulo>.<recurso>.<accion>
```

- **modulo:** identificador del módulo (minúsculas, coherente con el prefijo API cuando aplique): `hcm`, `log`, `inv`, `fin`, `org`, `admin`, `modulos`, etc.
- **recurso:** nombre lógico del recurso (snake_case, singular): `empleado`, `planilla`, `orden_servicio`, `documento`, `rol`, `usuario`.
- **accion:** una de las acciones estándar (minúsculas, español).

### 3.2 Acciones estándar

| Acción        | Uso típico                          |
|---------------|-------------------------------------|
| `leer`        | GET list, GET detail                |
| `crear`       | POST (alta de entidad)              |
| `actualizar`  | PUT, PATCH                          |
| `eliminar`    | DELETE                              |
| `administrar` | Operaciones estructurales (activar, desactivar, reordenar, duplicar, etc.) |
| `asignar`     | Asignar roles/permisos a usuarios   |
| `exportar`    | Exportación (cuando exista en seed) |

### 3.3 Derivación desde HTTP

| Método HTTP | Acción (CRUD estándar) |
|-------------|------------------------|
| GET (list o detail) | `leer`   |
| POST        | `crear`  |
| PUT / PATCH | `actualizar` |
| DELETE      | `eliminar`   |

Para rutas no CRUD (ej. `/activar/`, `/reordenar/`), usar la acción definida en el seed o convención del módulo (habitualmente `administrar`).

---

## 4. Excepciones existentes (no modificar convención)

Estas convenciones **ya están en uso** y deben respetarse; no sustituirlas por inferencia genérica desde el path.

### 4.1 ORG (Organización)

- **Permiso en uso:** `org.area.<accion>` (`leer`, `crear`, `actualizar`, `eliminar`).
- **Alcance:** Todos los recursos del módulo ORG (empresa, departamentos, parametros, centros_costo, cargos, sucursales) comparten el mismo recurso lógico `area`.
- **No usar** `org.empresa.leer`, `org.departamento.leer`, etc.

### 4.2 MODULOS (Menús, plantillas, secciones, catálogo)

- **Permisos en uso:** `modulos.menu.leer` y `modulos.menu.administrar`.
- **Alcance:** Menús de módulos, plantillas de roles, secciones, cliente_modulo, catálogo de módulos. Las operaciones de escritura/estructura usan `administrar`.
- **No usar** `modulos.plantilla.crear`, `modulos.seccion.actualizar`, etc.; mantener `modulos.menu.*`.

### 4.3 ADMIN (Usuarios y roles)

- **Permisos en uso:** `admin.usuario.leer|crear|actualizar|eliminar`, `admin.rol.leer|crear|actualizar|eliminar|asignar`.
- **Alcance:** Endpoints bajo `/usuarios`, `/roles`, y asignación de permisos a roles.
- Rutas de administración global (superadmin, tenant) pueden seguir usando solo rol o combinación rol + permiso según diseño actual.

---

## 5. Regla para endpoints nuevos

A partir de esta versión, **todo endpoint nuevo** debe:

1. **Definir** `MODULE_CODE` y `RESOURCE_CODE` en el archivo del router (o equivalente documentado).
2. **Incluir** la dependencia `require_permission("<modulo>.<recurso>.<accion>")` (Patrón A o B).
3. **Cumplir** Patrón A (negocio) o Patrón B (admin/system).
4. **Ser compatible** con el auto-registro de permisos en la tabla `permiso` (codigo = `<modulo>.<recurso>.<accion>`).

Los endpoints que no cumplan estos puntos no se consideran alineados al estándar RBAC del proyecto.

---

## 6. Referencia rápida — Catálogo de permisos (seed)

Los códigos de permiso deben existir en la tabla `permiso` (seed en `app/docs/database/SEED_PERMISOS_RBAC.sql`). Módulos y recursos incluidos en el seed (entre otros):

- **admin:** usuario, rol.
- **modulos:** menu.
- **org:** area.
- **inv:** producto.
- **wms:** almacen.
- **qms:** inspeccion.
- **pur:** orden_compra.
- **log:** ruta.
- **mfg:** orden_produccion.
- **mrp:** plan_materiales.
- **mps:** plan_maestro.
- **mnt:** activo, orden_trabajo.
- **sls:** venta.
- **crm:** oportunidad.
- **prc:** precio.
- **inv_bill:** comprobante.
- **pos:** venta.
- **hcm:** empleado, planilla.
- **fin:** asiento.
- **tax:** libro.
- **bdg:** presupuesto.
- **cst:** costo.
- **pm:** proyecto.
- **svc:** orden_servicio.
- **tkt:** ticket.
- **bi:** reporte.
- **dms:** documento.
- **wfl:** flujo.
- **aud:** log.

Para recursos no presentes en el seed (ej. `hcm.contrato`, `log.transportista`), usar la convención `<modulo>.<recurso>.<accion>` y dar de alta el permiso en `permiso` cuando se implemente el auto-registro o el seed se amplíe.
