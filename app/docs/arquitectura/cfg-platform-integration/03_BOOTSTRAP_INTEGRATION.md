# Bootstrap — integración CFG

---

## 1. Catálogo bootstrap (`02_catalog`)

| Script | ¿Modificar para CFG? | Qué hacer (futuro) |
|--------|----------------------|---------------------|
| **`S010__seed_modulo_menu_completo.sql`** | **Sí** | Insertar `modulo` CFG + sección + `modulo_menu` ruta → `/app/cfg/secuencias` |
| **`S021__menu_routes_saas_alignment.sql`** | **Sí** | Añadir `OR ruta LIKE '/cfg/%'` al whitelist de rewrite |
| **`S020__seed_admin_menu.sql`** | **No** | IAM / SYS_ADMIN solamente |
| **`S030__seed_permisos_core.sql`** | **No** | Core transversal |
| **`S068__permisos_rbac_cfg.sql`** | **No** (contenido permisos) | Ya define RP; asegurar ejecución en Shared **y** Dedicated |
| `S040`–`S066` | **No** | Permisos por módulo comercial distinto |

### Manifest / orden

| Doc / artefacto | Acción futura |
|-----------------|---------------|
| `BOOTSTRAP_MANIFEST.md` | Documentar fila CFG en S010; S068 sigue vigente |
| `BOOTSTRAP_ORDER` / pipelines | Confirmar S010 antes de onboarding; S068 en línea de permisos |
| Checksums Dedicated | Recalcular SHA256 de S010 tras edición (`catalog_profiles._CATALOG_CHECKSUMS`) |

---

## 2. Runtime bootstrap (`03_runtime`)

| Script | Rol AS-IS | ¿CFG? |
|--------|-----------|-------|
| **`R020__relacion_sys_admin_cliente_modulo.sql`** | Activa `SYS_ADMIN` para todos los clientes activos | **No modificar.** CFG no va por R020. |
| **`R010__asignar_core_app_a_roles.sql`** | `core.app.acceder` | **No** |

**Decisión de pipeline:** CFG llega a `cliente_modulo` por **onboarding Python** (`TRIAL_MODULES`), igual que ORG/INV — no por script R0xx.

---

## 3. QA / demo (`04_qa`) — opcional

| Script | Nota |
|--------|------|
| `D030__cliente_modulo_activar_org.sql` | Opcional: activar CFG en tenants demo existentes |
| `D010__seed_bd_central.sql` | Solo si demos deben mostrar CFG sin re-onboarding |

No bloquean el pipeline productivo trial.

---

## 4. Resumen de archivos bootstrap a tocar

```text
OBLIGATORIO (implementación):
  S010  — catálogo módulo/menú CFG
  S021  — whitelist /cfg/%

CONFIRMAR EJECUCIÓN (sin cambiar lógica de permisos):
  S068  — ya existe; Dedicated registry debe incluirlo

NO TOCAR:
  S020, R020, R010, OpenAPI, contratos FE
```
