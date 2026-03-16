## Convención de permisos RBAC

### Formato estándar

- **Patrón base**: `{modulo}.{entidad}.{accion}` (todo en minúsculas).
- **Módulo**: código corto alineado con el módulo funcional (`org`, `inv`, `wms`, `crm`, `pos`, `tax`, `bdg`, etc.).
- **Entidad**: nombre funcional de la entidad o agregado expuesto por el router (`empresa`, `sucursal`, `venta`, `proyecto`, `libro`, `presupuesto`, `plan_maestro`, etc.).
- **Acción**: verbo de negocio (`leer`, `crear`, `actualizar`, `eliminar`, y otros específicos como `exportar`, `asignar`, `administrar` cuando sea necesario).

Ejemplos correctos:

- `org.empresa.leer`, `org.empresa.crear`, `org.empresa.actualizar`, `org.empresa.eliminar`
- `inv.producto.leer`, `inv.producto.crear`, `inv.producto.actualizar`, `inv.producto.eliminar`
- `crm.oportunidad.leer`, `crm.oportunidad.crear`, `crm.oportunidad.actualizar`, `crm.oportunidad.eliminar`
- `admin.usuario.leer`, `admin.rol.asignar`

### Patrón A con MODULE_CODE / RESOURCE_CODE

Para nuevos módulos o routers, usar **Patrón A**:

- **Import**:
  - `from app.core.authorization.rbac import require_permission`
- **Constantes por archivo de endpoints**:
  - `MODULE_CODE = "<modulo>"`
  - `RESOURCE_CODE = "<entidad>"`
- **Decoración por handler**:
  - GET: `_: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer"))`
  - POST: `_: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear"))`
  - PUT/PATCH: `_: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar"))`
  - DELETE: `_: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar"))`

Ejemplo para ORG – Empresa:

```python
MODULE_CODE = "org"
RESOURCE_CODE = "empresa"

@router.get("", ...)
async def listar_empresas(
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    ...
```

### Auto-registro de permisos

- El startup recorre todos los endpoints y recoge cualquier dependencia `require_permission("modulo.entidad.accion")` o `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.accion")`.
- Cada cadena **estática** encontrada se registra en el **PermissionRegistry** y luego se sincroniza con la tabla `permiso`.
- No se deben construir permisos dinámicos con concatenaciones no detectables por introspección.

### Reglas para nuevos endpoints

- **No reutilizar** el mismo `entidad` para recursos de negocio distintos en la UI.
  - Incorrecto: usar `org.area.*` para empresa, sucursal, departamento, cargo, centro_costo, parametro.
  - Correcto: `org.empresa.*`, `org.sucursal.*`, `org.departamento.*`, `org.cargo.*`, `org.centro_costo.*`, `org.parametro.*`.
- Mantener la correspondencia:
  - **1 archivo de endpoints** ≈ **1 entidad funcional** ≈ **1 `RESOURCE_CODE`**.
- Acciones extra (no CRUD básico) deben ser verbos claros de negocio:
  - Ejemplos: `exportar`, `asignar`, `administrar`, `aprobar`, `reversar`.

### Checklist obligatorio para nuevos módulos

- **Nombre del módulo**:
  - Definir `MODULE_CODE` coherente con el código ERP (`inv`, `wms`, `crm`, `org`, etc.).
- **Diseño de entidades**:
  - Lista de entidades de negocio que se expondrán (una por archivo de endpoints).
  - Definir `RESOURCE_CODE` único por entidad.
- **Decoración de endpoints**:
  - Todos los endpoints con cambio de estado o lectura de datos sensibles deben tener `Depends(require_permission(...))`.
  - Revisar que cada método use la acción adecuada (`leer`, `crear`, `actualizar`, `eliminar`).
- **Seed de permisos**:
  - Añadir entradas a `SEED_PERMISOS_RBAC.sql` siguiendo el patrón `{modulo}.{entidad}.{accion}`.
  - Asegurar que el `modulo_id` corresponde al módulo correcto en la tabla `modulo`.
- **Revisión rápida**:
  - Grep de `require_permission` en el módulo para confirmar que no se usa un recurso genérico compartido por varias entidades.
  - Arrancar el backend y verificar que el auto-registro no reporta warnings para rutas sin permiso.

### Nota sobre permisos obsoletos

- El antiguo patrón `org.area.*` se considera **obsoleto** y ha sido reemplazado por permisos granulares:
  - `org.empresa.*`, `org.sucursal.*`, `org.departamento.*`, `org.cargo.*`, `org.centro_costo.*`, `org.parametro.*`.
- No deben crearse nuevos permisos siguiendo el patrón `org.area.*` ni reutilizarse en endpoints nuevos.

