# ORG — Implementación cerrada (Organización)

**Código de módulo:** ORG  
**Alcance:** Fases 1–4 según `docs/prompts/PROMPT_MODULO_MAESTRO.md` y `docs/bd/ORG_TABLAS.sql` (tablas `org_*`).  
**Fecha de cierre:** documento de verificación final del módulo.

---

## 1. Archivos tocados en la implementación

| Archivo | Rol |
|---------|-----|
| `app/modules/org/presentation/schemas.py` | Campos de auditoría y negocio alineados a BD en Create/Update/Read |
| `app/infrastructure/database/queries/org/sucursal_queries.py` | Filtro opcional `empresa_id` en `get` / `update` |
| `app/infrastructure/database/queries/org/centro_costo_queries.py` | Idem |
| `app/infrastructure/database/queries/org/departamento_queries.py` | Idem |
| `app/infrastructure/database/queries/org/cargo_queries.py` | Idem |
| `app/infrastructure/database/queries/org/parametro_queries.py` | Idem + condición `(empresa_id IS NULL OR empresa_id = :scope)` |
| `app/modules/org/application/services/sucursal_service.py` | `empresa_id` en operaciones por ID + `reactivar_sucursal_servicio` |
| `app/modules/org/application/services/centro_costo_service.py` | Idem + reactivar |
| `app/modules/org/application/services/departamento_service.py` | Idem + reactivar |
| `app/modules/org/application/services/cargo_service.py` | Idem + reactivar |
| `app/modules/org/application/services/parametro_service.py` | Idem + reactivar |
| `app/modules/org/presentation/endpoints_sucursales.py` | Query `empresa_id` opcional en detalle/PUT/DELETE + `POST .../reactivar` |
| `app/modules/org/presentation/endpoints_centros_costo.py` | Idem |
| `app/modules/org/presentation/endpoints_departamentos.py` | Idem |
| `app/modules/org/presentation/endpoints_cargos.py` | Idem |
| `app/modules/org/presentation/endpoints_parametros.py` | Idem |
| `app/docs/modulos/AUDITORIA_ORG.md` | Auditoría Fase 2 (referencia; no es código ejecutable) |

**No modificados en esta iteración:** `endpoints_empresa.py`, `empresa_service.py`, `empresa_queries.py` (ya tenían reactivar y modelo sin `empresa_id` de fila hija). **Seeds RBAC:** no se añadieron permisos nuevos; reactivar reutiliza `org.<recurso>.actualizar`.

---

## 2. Endpoints nuevos — checklist de seguridad

Prefijo API: `/org` (más el prefijo global de la API v1, p. ej. `/api/v1` según despliegue).

| Ruta (relativa a `/org`) | Método | `cliente_id` (tenant) | `empresa_id` (si aplica) | RBAC |
|--------------------------|--------|------------------------|---------------------------|------|
| `/sucursales/{id}/reactivar` | POST | Sí (`current_user.cliente_id` → servicio) | Opcional vía query (misma regla que detalle/PUT/DELETE) | `org.sucursal.actualizar` |
| `/centros-costo/{id}/reactivar` | POST | Sí | Query opcional | `org.centro_costo.actualizar` |
| `/departamentos/{id}/reactivar` | POST | Sí | Query opcional | `org.departamento.actualizar` |
| `/cargos/{id}/reactivar` | POST | Sí | Query opcional | `org.cargo.actualizar` |
| `/parametros/{id}/reactivar` | POST | Sí | Query opcional (ámbito global + empresa) | `org.parametro.actualizar` |

**Notas:**

- **`cliente_id`:** todas las rutas ORG siguen obteniendo el tenant desde el usuario autenticado (`require_permission` → usuario con `cliente_id`).
- **`empresa_id`:** para entidades con columna `empresa_id`, ahora se exige **`empresa_id` obligatorio en runtime** en operaciones por ID (detalle/actualizar/eliminar/reactivar). Esto cierra la brecha de “acceso por `cliente_id + PK`” dentro de un mismo cliente multi-empresa. En parámetros del sistema: con `empresa_id` informado se admiten filas globales (`empresa_id` NULL en BD) o de esa empresa.

---

## 3. Compatibilidad con endpoints existentes

| Verificación | Estado |
|--------------|--------|
| Rutas y métodos de listados, alta, detalle, actualización y baja lógica **existentes** | Sin cambio de path ni método |
| Estructura de **response** de los mismos | Sin cambios obligatorios: los schemas Read solo **añaden** campos opcionales (auditoría); clientes que ignoren claves extra siguen siendo compatibles |
| **PUT** con body JSON | Mismo contrato de cuerpo; en algunos handlers se usa `Body(...)` explícito solo por orden de parámetros con el query opcional |
| Query **`empresa_id`** en GET/PUT/DELETE por ID | **Mantenida sin cambio de contrato**; ahora es **requerida** para operaciones por ID en entidades con `empresa_id` (si no se envía, responde 400) |

**Empresa** (`/org/empresa/...`): sin cambios en esta iteración.

---

## 4. Resumen funcional entregado

1. **Schemas:** campos alineados a BD (usuarios de auditoría, `jefe_departamento_usuario_id` en alta de departamento, validación en alta de parámetro, `ruta_jerarquica` en centro de costo / departamento en escritura donde correspondía).
2. **Multi-empresa (brecha cerrada):** validación estricta de `empresa_id` en operaciones por ID para entidades que lo tienen. Implementado en capa de servicio con `ValidationError` (HTTP 400) cuando falta `empresa_id`.
3. **Reactivar:** cinco rutas `POST .../reactivar` alineadas al patrón de `org_empresa`, con el mismo permiso de actualización.
4. **RBAC:** sin nuevos códigos de permiso; sync code-first existente sigue aplicando.

---

## 5. Referencias

- Auditoría previa: `app/docs/modulos/AUDITORIA_ORG.md`
- Modelo de datos: `docs/bd/ORG_TABLAS.sql`
- Prompt maestro: `docs/prompts/PROMPT_MODULO_MAESTRO.md`

---

**Estado del módulo ORG (esta entrega):** implementación cerrada según el alcance acordado (Fase 3 en bloques + verificación Fase 4). Cualquier ampliación futura (p. ej. obligatoriedad de `empresa_id` en contexto multi-empresa, seeds adicionales o tests automatizados) queda fuera de este cierre.

---

## 6. Cierre de brecha adicional (post-verificación)

### Brecha cerrada

- **Validación estricta de `empresa_id` en operaciones por ID** (entidades con columna `empresa_id`): ya no se permite operar por `cliente_id + PK` sin scope de empresa.

### Archivos modificados

- `app/modules/org/application/services/sucursal_service.py`
- `app/modules/org/application/services/centro_costo_service.py`
- `app/modules/org/application/services/departamento_service.py`
- `app/modules/org/application/services/cargo_service.py`
- `app/modules/org/application/services/parametro_service.py`

### Validaciones nuevas

- En `get/update/delete/reactivar` por ID: si `empresa_id` no viene informado, se lanza `ValidationError` con `internal_code="MISSING_REQUIRED_FIELDS"` (HTTP 400).

### Limitaciones / compatibilidad mantenida

- **No se cambian rutas, métodos ni bodies.** `empresa_id` ya existía como query opcional; el contrato HTTP se mantiene.
- **Cambio de comportamiento intencional:** llamadas antiguas que omitían `empresa_id` en operaciones por ID ahora reciben 400 para evitar acceso cross-empresa dentro del mismo `cliente_id`.
