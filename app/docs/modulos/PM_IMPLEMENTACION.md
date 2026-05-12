# PM — Implementación cerrada (Gestión de Proyectos)

**Código de módulo:** PM  
**Alcance:** tablas `pm_*` según `docs/bd/PM_TABLAS.sql` (en la práctica una sola tabla: `pm_proyecto`). Ciclo completo Fases 1–4 respecto a `docs/prompts/PROMPT_MODULO_MAESTRO.md`.  
**Estado:** módulo cerrado en la entrega actual; la ampliación funcional futura queda fuera de este documento.

---

## 1. Archivos del módulo (inventario relevante)

### Código ejecutable

| Archivo | Rol |
|---------|-----|
| `app/modules/pm/presentation/endpoints.py` | Agregador: monta proyectos bajo prefijo `/proyectos`. |
| `app/modules/pm/presentation/endpoints_proyecto.py` | Endpoints REST de `pm_proyecto`; RBAC y parámetro opcional `empresa_id` en detalle y actualización por ID. |
| `app/modules/pm/presentation/schemas.py` | `ProyectoCreate`, `ProyectoUpdate`, `ProyectoRead`. |
| `app/modules/pm/application/services/proyecto_service.py` | Orquestación: lista, detalle, alta, actualización. |
| `app/modules/pm/application/services/__init__.py` | Exporta funciones del servicio. |
| `app/infrastructure/database/tables_erp/tables_pm.py` | Definición SQLAlchemy Core de `pm_proyecto`. |
| `app/infrastructure/database/queries/pm/proyecto_queries.py` | Consultas e inserciones/actualizaciones con filtro `cliente_id` y `empresa_id` opcional donde aplica. |
| `app/infrastructure/database/queries/pm/__init__.py` | Reexporta funciones de queries. |
| `app/api/v1/api.py` | Inclusión del router PM con prefijo `/pm`. |

### Documentación y seeds

| Archivo | Rol |
|---------|-----|
| `app/docs/modulos/AUDITORIA_PM.md` | Auditoría Fase 2 (referencia histórica). |
| `app/docs/database/SEED_PERMISOS_RBAC_PM.sql` | Permisos `pm.proyecto.*` (idempotente por `MERGE`). |

**Capa repository:** el servicio llama directamente a `proyecto_queries`; no hay clase `*repository*` dedicada (patrón ya usado en otras partes del monolito).

---

## 2. Verificación Fase 4 — endpoints y seguridad

Prefijo de API: `/pm` respecto a la raíz v1 (p. ej. `/api/v1/pm` según `settings.API_V1_STR`). Recurso proyectos: `/proyectos`.

| Ruta (relativa a `/pm/proyectos`) | Método | `cliente_id` (tenant) | `empresa_id` | RBAC |
|-----------------------------------|--------|------------------------|--------------|------|
| `""` (lista) | GET | Sí (`current_user.cliente_id` en todas las queries) | Filtro opcional en query | `pm.proyecto.leer` |
| `/{proyecto_id}` | GET | Sí | Query **opcional**: si se envía, la fila debe pertenecer a esa empresa además del cliente | `pm.proyecto.leer` |
| `""` (alta) | POST | Sí (forzado en insert) | Obligatorio en body (`ProyectoCreate.empresa_id`) | `pm.proyecto.crear` |
| `/{proyecto_id}` | PUT | Sí | Query **opcional** (misma regla que GET por ID) | `pm.proyecto.actualizar` |

**Notas de contrato:**

- No se eliminaron rutas ni se cambiaron método ni path de las operaciones existentes.
- En GET y PUT por ID solo se **añadió** un query opcional `empresa_id`; los clientes que no lo envían conservan el comportamiento anterior (ámbito solo por `cliente_id` + `proyecto_id`).
- **POST** alta: sin cambios de body respecto al cierre acordado; `empresa_id` sigue viniendo en el cuerpo de creación.

---

## 3. RBAC — permisos sembrados

Script: `app/docs/database/SEED_PERMISOS_RBAC_PM.sql`  

Códigos (alta idempotente, `modulo_id` PM `E1000015-0000-4000-8000-000000000015`):

- `pm.proyecto.leer`
- `pm.proyecto.crear`
- `pm.proyecto.actualizar`

Conviene ejecutar el script después de la base RBAC principal y del seed de módulos/menú que define el PM.

---

## 4. Compatibilidad

| Verificación | Estado |
|--------------|--------|
| Rutas existentes lista / detalle / POST / PUT | Sin cambio de método ni path |
| Response `ProyectoRead` | Igual alcance contractual acordado (schemas no modificados en Fase 3 final) |
| Body `ProyectoCreate` / `ProyectoUpdate` | Sin cambios en el cierre acordado |
| Clientes legacy que omiten `empresa_id` en GET/PUT por ID | Siguen funcionando igual que antes del refuerzo multi-empresa opcional |

---

## 5. Limitaciones conscientes del modelo de datos (`PM_TABLAS.sql`)

- La tabla `pm_proyecto` **no** define `es_activo`; no hay en esta entrega endpoints dedicados tipo activar/desactivar por soft flag. Una evolución funcional podría apoyarse en el campo **`estado`** sin tocar DDL, si negocio lo define.
- `ProyectoUpdate` **no** expone `empresa_id`; cambiar empresa vía API requeriría decisión funcional futura y extensión de schema coordinada.

---

## 6. Referencias

- Auditoría Fase 2: `app/docs/modulos/AUDITORIA_PM.md`
- DDL de referencia por módulo: `docs/bd/PM_TABLAS.sql`
- Prompt maestro: `docs/prompts/PROMPT_MODULO_MAESTRO.md`

---

**Cierre:** el módulo PM queda cerrado conforme al alcance de las fases ejecutadas con el usuario: auditoría → ajustes de services/queries/routers (scope opcional por empresa en GET y PUT por ID) → seed RBAC PM → esta verificación final.
