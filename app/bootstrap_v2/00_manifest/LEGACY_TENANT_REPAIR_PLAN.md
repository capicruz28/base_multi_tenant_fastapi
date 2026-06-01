# Legacy Tenant Repair Plan — Post runtime RBAC bootstrap

**Fecha:** 2026-05-21 (actualizado con implementación runtime)  
**Contexto:** Tras validación E2E (`E2E_RUNTIME_VALIDATION.md`).

## Implementación (Opción 1 — activa)

| Componente | Ruta |
|------------|------|
| Servicio | `app/modules/tenant/application/services/legacy_tenant_rbac_repair_service.py` |
| CLI | `scripts/repair_legacy_tenant_rbac.py` |
| Tests | `tests/unit/test_legacy_tenant_rbac_repair.py` |

### Comandos

```bash
# Auditoría (reporte JSON: todos los tenants + candidatos)
python scripts/repair_legacy_tenant_rbac.py --audit-only

# Dry-run (candidatos: status dry_run, sin commit)
python scripts/repair_legacy_tenant_rbac.py --dry-run

# Aplicar (commit por tenant candidato)
python scripts/repair_legacy_tenant_rbac.py --apply

# Un tenant
python scripts/repair_legacy_tenant_rbac.py --dry-run --cliente-id <UUID>
```

### Criterios de candidato (`needs_repair`)

- Sin `cliente_modulo` activo, o faltan módulos `ORG` / `SYS_ADMIN`
- Sin `rol_permiso` en `ADMIN_TENANT`, o sin `core.app.acceder`, o conteo ADMIN &lt; 5

### Exclusiones (no se modifica)

- Cliente plataforma (`SUPERADMIN_CLIENTE_ID` / `00000000-0000-0000-0000-000000000001`)
- Tenants ya sanos (ORG+SYS_ADMIN + bundle ADMIN suficiente)
- Sin rol `ADMIN_TENANT` → `skipped`, requiere intervención manual (roles base)

### Idempotencia

Usa `OnboardingRbacService.bootstrap_cliente_rbac` (misma lógica que onboarding). Re-ejecutar en tenant sano → `ALREADY_HEALTHY`, sin inserts.

### Fallback SQL (no eliminados)

R010/R020/S030/S040–S066 siguen disponibles para recovery manual si el job Python no puede ejecutarse.

---

## 1. Inventario BD observado (`bd_sistema`)

| Subdominio | `cliente_id` | `cliente_modulo` activos | `rol_permiso` | `ADMIN_TENANT` | Diagnóstico |
|------------|--------------|--------------------------|---------------|----------------|-------------|
| `platform` | `00000000-...0001` | 6 | 416 | No (roles platform) | Sistema; fuera de alcance tenant ERP |
| `acme` | `11111111-...1111` | 3 | 450 | Sí | Legacy **completo**; permisos extra (`tenant.cliente.crear`) |
| `innova` | `22222222-...2222` | 2 | 416 | Sí | Legacy **completo**; permisos extra |
| `techcorp` | `33333333-...3333` | 1 (SYS_ADMIN) | **0** | No | **Incompleto** — sin RBAC API |
| `global` | `44444444-...4444` | 1 (SYS_ADMIN) | **0** | No | **Incompleto** |
| `prueba` | `EB067FE5-...` | **0** | **0** | Sí | **Incompleto** — onboarding sin bootstrap RBAC |
| `e2evalid01` | `db40cccc-...` | 2 (ORG,SYS_ADMIN) | **44** | Sí | **Referencia runtime** (sin R010/R020) |

### Queries de detección (ejecutar en PROD pre-migración)

```sql
-- Tenants activos con resumen
SELECT c.subdominio, c.codigo_cliente,
  (SELECT COUNT(*) FROM cliente_modulo cm WHERE cm.cliente_id = c.cliente_id AND cm.esta_activo = 1) AS cm,
  (SELECT COUNT(*) FROM rol_permiso rp WHERE rp.cliente_id = c.cliente_id) AS rp,
  (SELECT COUNT(*) FROM rol r WHERE r.cliente_id = c.cliente_id AND r.codigo_rol = 'ADMIN_TENANT') AS admin_rol
FROM cliente c
WHERE c.es_activo = 1
ORDER BY c.fecha_creacion;
```

Usar Anexo A de `E2E_RUNTIME_VALIDATION.md` (queries A4–A7) para listas de exclusión.

---

## 2. Clasificación de tenants

### Tipo A — Referencia (no reparar)

- Tenants creados **después** del despliegue con `OnboardingRbacService`.
- Criterio: `cliente_modulo` incluye `ORG`+`SYS_ADMIN` y `rol_permiso` ADMIN ≥ 40 (según tamaño catálogo actual).

### Tipo B — Legacy funcional con deuda

- **acme**, **innova**: operativos; menú y API OK.
- Deuda: `tenant.cliente.crear` en ADMIN (seed S040/R010 histórico).
- Opcional: limpiar permiso no deseado sin romper operación.

### Tipo C — Legacy incompleto (reparación obligatoria)

- **prueba**, **techcorp**, **global**
- Síntomas: login puede funcionar pero **403** masivos en API/menú reducido.
- Causa: sin `cliente_modulo` ORG y/o sin `rol_permiso`.

### Tipo D — Incompatibles con onboarding nuevo

| Caso | Descripción | Acción |
|------|-------------|--------|
| Sin rol `ADMIN_TENANT` | techcorp, global | Crear roles vía script o re-onboarding parcial |
| Onboarding a medias | prueba (roles+user sí, RBAC no) | Ejecutar repair idempotente (§3) |
| Metadata tenant | warning routing en tenants nuevos | Registrar metadata explícita (fuera RBAC) |

---

## 3. Estrategias de reparación (orden recomendado)

### Opción 1 — Job Python idempotente (recomendado PROD)

Reutilizar la misma lógica que onboarding (sin duplicar R010/R020):

```
OnboardingRbacService.bootstrap_cliente_rbac(session, cliente_id, admin_rol_id, activado_por_usuario_id?)
```

**Pseudoflujo:**

1. Por cada `cliente_id` en Tipo C (y opcional B):
2. Abrir `AsyncSession` ADMIN + transacción.
3. Resolver `admin_rol_id` = `rol` WHERE `codigo_rol='ADMIN_TENANT'`.
4. Si no existe ADMIN_TENANT → abortar tenant (log + ticket manual).
5. `bootstrap_cliente_rbac` (idempotente).
6. Commit.
7. Log: módulos activados, filas `rol_permiso` insertadas.

**Ventajas:** Paridad exacta con tenant nuevo; no UUID hardcodeados; respeta exclusion `tenant.cliente.crear`.

### Opción 2 — SQL batch (R010 + R020) una sola vez

Para emergencia si el backend no está disponible:

| Script | Cuándo |
|--------|--------|
| `R020__relacion_sys_admin_cliente_modulo.sql` | Solo SYS_ADMIN global; **no** activa ORG por tenant |
| `R010__asignar_core_app_a_roles.sql` | Solo `core.app.acceder`; **no** bundle admin/org/modulos |

**Limitación:** No replica grants por prefijos del runtime (44 permisos). Tras R010/R020 haría falta script adicional o Opción 1.

### Opción 3 — Re-ejecutar S040–S066 (no recomendado)

- Duplica fuente deprecada.
- Puede reintroducir `tenant.cliente.crear` y códigos obsoletos.
- **Evitar** salvo entornos de laboratorio.

---

## 4. Plan por tenant (observado en dev)

| Tenant | Acción recomendada | Prioridad |
|--------|-------------------|-----------|
| `prueba` | Opción 1 completa | P0 |
| `techcorp` | Opción 1 + verificar rol ADMIN existe | P0 |
| `global` | Opción 1 + verificar rol ADMIN existe | P0 |
| `acme` | Opcional: DELETE `rol_permiso` donde `permiso.codigo='tenant.cliente.crear'` y rol ADMIN | P2 |
| `innova` | Idem acme | P2 |
| `e2evalid01` | Ninguna (referencia) | — |

---

## 5. Validación post-reparación

Por cada tenant reparado, ejecutar:

```sql
DECLARE @cid UNIQUEIDENTIFIER = '<cliente_id>';

-- Debe devolver ORG y SYS_ADMIN
SELECT m.codigo FROM cliente_modulo cm
JOIN modulo m ON m.modulo_id = cm.modulo_id
WHERE cm.cliente_id = @cid AND cm.esta_activo = 1;

-- Debe ser > 0 (≈40+ según catálogo)
SELECT COUNT(*) FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
WHERE rp.cliente_id = @cid;

-- Debe incluir core, org.crear, modulos.menu.leer; NO tenant.cliente.crear
SELECT p.codigo FROM rol_permiso rp
JOIN rol r ON r.rol_id = rp.rol_id AND r.codigo_rol = 'ADMIN_TENANT'
JOIN permiso p ON p.permiso_id = rp.permiso_id
WHERE rp.cliente_id = @cid
  AND p.codigo IN ('core.app.acceder','org.empresa.crear','modulos.menu.leer','tenant.cliente.crear');
```

**Smoke API:**

1. Login admin tenant (`Origin` con subdominio).
2. `GET /auth/permissions/me` — códigos esperados.
3. `GET /auth/menu` — ORG + SYS_ADMIN.
4. `GET /api/v1/org/empresa` — 200.

---

## 6. R010 / R020 en legacy vs nuevos

| Escenario | R010 | R020 |
|-----------|------|------|
| Tenant **nuevo** vía API (runtime) | **No ejecutar** | **No ejecutar** |
| Tenant legacy Tipo C | Insuficiente solo R010+R020 | Insuficiente |
| Reparación completa | Usar **Opción 1** (runtime) | Incluido en Opción 1 (`ORG`+`SYS_ADMIN`) |
| Emergencia mínima | R010 temporal | R020 temporal |

---

## 7. Riesgos de la reparación

| Riesgo | Mitigación |
|--------|------------|
| Doble INSERT si no idempotente | Usar solo `OnboardingRbacService` (ya idempotente) |
| Revocar permisos legacy necesarios | No DELETE masivo; solo quitar `tenant.cliente.crear` si se desea |
| Downtime | Job por tenant; ventana de mantenimiento |
| Catálogo vacío | Verificar startup `permission_sync` antes del job |
| techcorp/global sin ADMIN_TENANT | Script manual de roles base antes del bootstrap |

---

## 8. Checklist operativo (cuando se autorice implementar)

- [ ] Exportar listas A4–A7 de PROD
- [ ] Backup `rol_permiso` + `cliente_modulo`
- [ ] Implementar comando/CLI `repair-tenant-rbac --cliente-id=...` (wrapper Opción 1)
- [ ] Dry-run en staging
- [ ] Ejecutar Tipo C en PROD
- [ ] Smoke login + menu + org por tenant
- [ ] Documentar en runbook que R010/R020 quedan solo archivo histórico
- [ ] (Opcional P2) Limpiar `tenant.cliente.crear` en acme/innova

---

## 9. Issues fuera de RBAC (registrar en backlog)

1. **Login 500** — `apellido` desde `razon_social` en onboarding (`e2evalid01`).
2. **Metadata routing** — tenant nuevo sin fila metadata.
3. **Menú SYS_ADMIN** — permisos plataforma no en catálogo sync.

Estos no se resuelven con R010/R020 ni con repair RBAC estándar.
