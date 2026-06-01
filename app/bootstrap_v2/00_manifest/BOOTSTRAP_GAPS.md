# BOOTSTRAP_GAPS — Known issues (document only, not fixed in v2)

Este documento registra problemas conocidos en los scripts legacy copiados a `bootstrap_v2`.
**No se corrigen en esta fase.** Sirve para planificar migraciones y runtime.

---

## 1. Orden DDL vs dependencias FK

| ID | Gap | Impacto |
|----|-----|---------|
| G-001 | `V020__tablas_bd_central.sql` define `usuario`, `rol`, `usuario_rol`, `rol_menu_permiso`, `refresh_tokens` con FK a `org_empresa`, pero `org_empresa` está en `V010__tablas_bd_erp_completo.sql` | **Orden oficial v2:** ejecutar `V010` antes de `V020` (no el orden numérico 1→3 del naming legacy) |
| G-002 | Documentación legacy sugería “central primero”; contradice FK reales | Confusión operativa; resuelto en `BOOTSTRAP_ORDER.md` |

---

## 2. Errores de sintaxis SQL (DDL central)

| ID | Ubicación (legacy) | Detalle |
|----|-------------------|---------|
| G-010 | `1.- TABLAS_BD_CENTRAL.sql` → `usuario_rol` | Falta coma después de `es_empresa_default BIT ... NOT NULL` antes de `fecha_asignacion` |
| G-011 | `1.- TABLAS_BD_CENTRAL.sql` → `rol_menu_permiso` | `empresa_id UNIQUEIDENTIFIER NULL;` usa `;` en lugar de `,` |
| G-012 | `1.- TABLAS_BD_CENTRAL.sql` → `refresh_tokens` | Mismo problema `;` en `empresa_id` |

---

## 3. Esquema vs onboarding / JWT

| ID | Gap | Impacto |
|----|-----|---------|
| G-020 | `usuario.empresa_default_id NOT NULL` + FK a `org_empresa` en DDL | `ClienteOnboardingService` inserta `NULL` — falla si DDL estricto |
| G-021 | Seeds activos en `D010` no insertan `org_empresa` ni `usuario_rol.empresa_id` | Login multiempresa requiere SQL QA adicional |
| G-022 | Tabla `cfg_codigo_secuencia` usada en onboarding Python (`tables.py`) **sin DDL** en scripts auditados | Onboarding falla si tabla no existe |
| G-023 | Columna `modulo_menu.permiso_codigo_requerido` (binder RBAC) no creada en scripts auditados | MenuPermissionBinder no persiste vínculos |

---

## 4. Seeds y catálogo

| ID | Gap | Impacto |
|----|-----|---------|
| G-030 | `SEED_PERMISOS_RBAC.sql` legacy = **archivo vacío** (0 bytes) | `S067__` es stub; `FASE4_CANDIDATOS` referencia dependencia inexistente |
| G-031 | `SEED_PERMISOS_RBAC_PRC.sql` no existe en repo | Módulo PRC en menú (`4.-`) sin seed de permisos dedicado |
| G-032 | Doble fuente `permiso`: seeds `S040–S066` MERGE vs `permission_sync_service` startup | Riesgo de drift código/SQL |
| G-033 | `D010__seed_bd_central.sql` contiene bloques **comentados** masivos (módulos ALMACEN/LOGISTICA, `rol_menu_permiso`) | Parece bootstrap incompleto si se lee el archivo entero |
| G-034 | `D020__rol_permiso_administrador.sql` asigna **todos** los permisos a rol "Administrador" | Incompatible con RBAC explícito en producción |

---

## 5. Multiempresa / menú

| ID | Gap | Impacto |
|----|-----|---------|
| G-040 | Autorización API usa `rol_permiso`; menú UI usa `rol_menu_permiso` | Seeds v2 no poblan `rol_menu_permiso` en camino prod (solo QA comentado en D010) |
| G-041 | `cliente_modulo` vacío tras solo prod bootstrap | Sin menú ERP hasta `D030` o API |
| G-042 | Dedicated: `SEED_BD_DEDICADA_*` **excluidos** de v2 pero existen en legacy con `menu_id` AA11/BB11 | Desalineados con menús `E301…` de `S010` |

---

## 6. Runtime / calidad scripts

| ID | Gap | Impacto |
|----|-----|---------|
| G-050 | `R020__relacion_sys_admin_cliente_modulo.sql` termina con `SELECT * FROM cliente_modulo` | No apto como script automatizado limpio |
| G-051 | Mayoría de seeds `S*` y `D010` no idempotentes (INSERT sin MERGE) | Re-ejecución falla por PK/unique |
| G-052 | `V010` monolítico (~100 tablas ERP) en shared | BD pesada aunque tenant no use módulos |

---

## 7. Backend ya automatiza (gaps de reemplazo futuro)

| Concern | Estado backend | Gap SQL |
|---------|----------------|---------|
| Catálogo `permiso` endpoints | `permission_sync_service` @ startup | Redundante con `S040–S066` |
| Crear tenant + admin | `ClienteOnboardingService` | Parcial vs `D010` |
| Activar módulo | `ClienteModuloService` | vs `D030`, `R020` |
| Menú ↔ permiso `.leer` | `MenuPermissionBinder` **no invocado** en startup | Sin equivalente SQL en v2 prod |

---

## 8. Próximas fases (fuera de alcance v2 reorganización)

1. Migraciones versionadas (Flyway/Alembic) generadas desde `01_schema/`
2. Corregir G-010–G-012 en fuente legacy + refresh copies
3. Split `V010` por módulo o baseline + módulos opcionales
4. Idempotencia MERGE en catálogo `S010`, `S020`
5. Mover `D010`, `D020`, `D030` a pipeline QA aislado
6. Deprecar `S040–S067` cuando sync code-first sea completo
