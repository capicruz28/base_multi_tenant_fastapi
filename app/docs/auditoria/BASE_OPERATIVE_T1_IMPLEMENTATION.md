# T1 — BASE_OPERATIVE Implementation

**Referencia:** [ROLE_BUNDLE_BASELINE_AUDIT.md](./ROLE_BUNDLE_BASELINE_AUDIT.md)  
**Fecha:** 2026-05-31  
**Fase:** T1 — bundle transversal operativo (sin MANAGER_STANDARD / USER_STANDARD completos)

---

## 1. Objetivo

Provisionar automáticamente **`BASE_OPERATIVE`** en `MANAGER_TENANT` y `USER_TENANT`:

| Código | Uso |
|--------|-----|
| `core.app.acceder` | Grant base ERP |
| `tenant.branding.leer` | `GET /clientes/tenant/branding` |
| `org.empresa.leer` | Contexto / selector empresa vía ORG |

**No modifica:** `ADMIN_TENANT` (OWNER_FULL), frontend, OwnerSync.

---

## 2. Componentes

| Archivo | Responsabilidad |
|---------|-----------------|
| `base_operative_constants.py` | Códigos bundle + roles operativos |
| `base_operative_service.py` | INSERT idempotente `rol_permiso` |
| `onboarding_rbac_service.py` | Hook post-OwnerSync onboarding |
| `user_service.py` | Hook en `asignar_rol_a_usuario` |
| `scripts/repair_base_operative.py` | Backfill tenants existentes |

---

## 3. Flujos

### 3.1 Onboarding tenant

```text
crear_cliente_con_onboarding
  → bootstrap_cliente_rbac (OwnerSync ADMIN)
  → BaseOperativeService.apply_to_operative_roles(MANAGER + USER)
```

### 3.2 Assign rol operativo

```text
POST /usuarios/{id}/roles/{rol_id}/
  → asignar_rol_a_usuario
  → ensure_for_operative_role si codigo_rol ∈ {MANAGER, USER}
```

### 3.3 Repair legacy

```bash
python scripts/repair_base_operative.py --all --dry-run
python scripts/repair_base_operative.py --subdominio <tenant> --apply
python scripts/repair_base_operative.py --all --apply \
  --output app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_REPAIR.json
```

---

## 4. Validación

```bash
pytest tests/unit/test_base_operative_t1.py -v
pytest tests/unit/test_onboarding_rbac_bootstrap.py tests/unit/test_assign_role_empresa_scope.py -v
```

Evidencia unitaria: `app/bootstrap_v2/00_manifest/evidence/T1_BASE_OPERATIVE_VALIDATION.json`

---

## 5. Criterios de aceptación T1

| Criterio | Mecanismo |
|----------|-----------|
| MANAGER/USER tienen 3 RP tras onboarding | `bootstrap_cliente_rbac.base_operative` |
| Assign MANAGER aplica BASE idempotente | `test_asignar_rol_triggers_base_operative_for_manager` |
| Repair idempotente | `repair_base_operative.py --all` |
| ADMIN sin cambios | No invoca BASE en ADMIN |
| Sin MANAGER_STANDARD | Solo 3 códigos BASE |

---

## 6. Próximos pasos (fuera T1)

- T2: `MANAGER_STANDARD` / `USER_STANDARD` (RoleGrantSync + RMP)
- FE: alinear guards con códigos backend
