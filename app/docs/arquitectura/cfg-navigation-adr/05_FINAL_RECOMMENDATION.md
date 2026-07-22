# Recomendación final — Plano de navegación CFG

---

## 1. Recomendación ejecutiva

**Adoptar Modelo B.**

| Mantener | Decidir ahora |
|----------|---------------|
| Dominio ERP `cfg` | Shell FE = **Tenant Administration** |
| API `/api/v1/cfg` | Rutas de menú bajo **`/admin/...`** |
| Módulo propio + `cliente_modulo` | **No** `/app/cfg` como plano canónico |
| Permisos `cfg.secuencias.*` | **No** `/super-admin` |

---

## 2. Justificación en una frase

CFG es **configuración gobernada del tenant** usada por Administradores/implantadores; el shell `/admin` expresa ese rol mejor que el ERP operativo `/app`, sin alterar el dominio ni la API.

---

## 3. Criterios de aceptación del ADR (documentales)

El ADR se considera aplicado en diseño cuando:

1. Toda especificación futura de menú CFG usa prefijo **`/admin/`** (no `/app/cfg`, no `/super-admin`).
2. Se mantiene explícito que el registro de catálogo es módulo **`CFG`** (no solo menú huérfano en `SYS_ADMIN` sin módulo).
3. El contrato API FE sigue apuntando a `/api/v1/cfg`.
4. Los gates de UI de negocio siguen siendo `cfg.secuencias.*`.
5. Se documenta (cuando se implemente FE) la relación opcional con `admin.tenant.access` como gate de plano.

---

## 4. Qué queda fuera de este ADR

- Crear seeds / SQL / migraciones
- Registrar CFG en menú
- Cambiar código Backend o Frontend
- Fijar el path exacto final (`/admin/configuracion/secuencias` vs otra taxonomía bajo `/admin`) — solo se exige el **plano** `/admin`
- Incluir CFG en `TRIAL_MODULES` / OwnerSync (decisión de onboarding posterior)

---

## 5. Matriz final de conceptos

| Concepto | Valor canónico post-ADR |
|----------|-------------------------|
| Dominio | ERP `cfg` |
| API | `/api/v1/cfg` |
| Catálogo módulo | `CFG` (propio) |
| Shell FE | `/admin` (Tenant Administration) |
| Shell operativo | `/app` (ORG/INV/WMS… — sin CFG como hogar canónico) |
| Platform | `/super-admin` — excluido |
| Tipo de decisión | **Navegación**, no dominio |

---

## 6. Mensaje para equipos

| Equipo | Lectura |
|--------|---------|
| Backend | No mover API ni dominio. Futuro `modulo_menu.ruta` bajo `/admin/...`. |
| Frontend | Montar pantallas CFG en shell Tenant Admin; PermissionGuard con `cfg.secuencias.*`; no asumir `ERP_MODULES` ⇒ `/app/cfg`. |
| Producto | CFG aparece junto a administración del tenant (configuración), no junto a operación diaria de almacén/organización. |

---

## 7. Firma de decisión

| Campo | Valor |
|-------|--------|
| Decisión | **Modelo B** |
| Fecha | 2026-07-18 |
| Estado | Recomendación arquitectónica formal (lista para aprobación de producto/FE/BE) |
| Próximo paso habilitado | Diseñar registro de menú CFG **con rutas `/admin`** (sin implementar aún) |
