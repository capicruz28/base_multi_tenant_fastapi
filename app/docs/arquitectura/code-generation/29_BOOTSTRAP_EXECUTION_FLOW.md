# F17B — Flujo de ejecución del Bootstrap con el Motor de Códigos

**Fase:** F17B (documentación). Complementa `28`.
**Objetivo:** dejar explícito el orden, transacciones, rollback, dependencias y puntos de extensión del onboarding, mostrando **dónde se inserta el Motor**.

---

## 1. Shared — flujo transaccional único

`ClienteOnboardingService.crear_cliente_con_onboarding(cliente_data)`
Conexión: `DatabaseConnection.ADMIN` (BD única en single-DB). Transacción: `async with session.begin()`.

```
BEGIN TX (ADMIN)
 ├─ 1. _insertar_cliente ................. cliente_id
 ├─ 2. _insertar_roles_base ............. admin_rol_id (ADMIN/MANAGER/USER)
 ├─ 3. ensure_empresa_inicial ........... empresa_id (EMP001, idempotente)
 ├─ 4. _insertar_usuario_admin .......... usuario_id  (empresa_default_id=empresa_id)
 ├─ 5. vincular_admin_empresa ........... usuario_rol ADMIN empresa_id=NULL (tenant-wide)
 ├─ 6. bootstrap_cliente_rbac ........... permisos + activación módulos
 ├─ 7. _insertar_auth_config_si_no_existe  cliente_auth_config
 └─ 8. _insertar_secuencias_codigo ...... [MOTOR] 57 filas cfg_codigo_secuencia (derivado catálogo, F17D)
COMMIT  (cualquier excepción ⇒ ROLLBACK total, incluidas las secuencias)

POST-COMMIT (no bloqueante):
 └─ permission_resolver.invalidate_for_tenant(cliente_id)
```

### 1.1 Detalle del paso 8 (Motor)

`_insertar_secuencias_codigo(session, cliente_id, empresa_id)` itera `ONBOARDING_SEQUENCE_SEEDS` (57 entradas: todas las CFG con scope TENANT/EMPRESA, **derivadas** del `SequenceCatalog`; las ALMACEN/PUNTO_VENTA quedan lazy):

```
for seed in ONBOARDING_SEQUENCE_SEEDS:
    eff_empresa = None if seed.scope_type == TENANT else empresa_id
    repo.insert_secuencia(
        cliente_id, sequence_key=seed.sequence_key,
        scope_type=seed.scope_type, prefijo=seed.prefijo,
        longitud_numero=seed.longitud_numero, separador=seed.separador,
        empresa_id=eff_empresa, session=session,           # ← misma TX
        ultimo_numero=seed.ultimo_numero, numero_inicial=seed.numero_inicial)
        # org_empresa TENANT: seed.ultimo_numero = 1 (BR-BOOT-04; post EMP001)
```

- `session=session` ⇒ escribe en la **misma BD/TX** del onboarding.
- `scope_type=TENANT` ⇒ `empresa_id=NULL` (corrige INC-01); única secuencia TENANT = `org_empresa` con **`ultimo_numero=1`** tras bootstrap sede.
- `insert_secuencia` computa `scope_fingerprint` y respeta `UQ_cfg_scope`.

### 1.2 Rollback Shared

Atómico. Si el paso 8 falla, se revierten los pasos 1–7. **No** quedan tenants a medias con secuencias huérfanas.

---

## 2. Dedicated — flujo por pasos con markers

`DedicatedTenantSeedService.run_tenant_seed(request)`
Conexión: `provisioning_dedicated_session(database_name)` (BD del tenant). Precondición: BD bootstrappeada + catálogos S6.

```
open dedicated_session(database_name)
 ├─ verify_tenant_seed_prerequisites  (permiso core.app.acceder ≥1, modulo ≥1)
 │
 ├─ FOR step IN profile.steps (orden 1..6):
 │    ├─ if _is_step_applied(marker) ⇒ hydrate_state + skip
 │    │     (rehidrata admin_rol_id / empresa_id / admin_usuario_id según step)
 │    └─ else:
 │         ├─ execute_tenant_seed_step(step)
 │         └─ _record_step_applied(marker en bootstrap_applied)
 │
 ├─ assert state.admin_rol_id & admin_usuario_id & empresa_id  (PROVISIONING_SEED_INCOMPLETE)
 └─ _verify_row_expectations:
        rol≥3, org_empresa≥1, usuario≥1, cfg_codigo_secuencia ≥ len(EAGER_SEQUENCE_KEYS)=57
```

Pasos (`_TENANT_SEED_STEPS`):

```
1 seed_base_roles ............ _insertar_roles_base
2 seed_org_empresa ........... ensure_empresa_inicial → state.empresa_id
3 seed_admin_user ............ _insertar_usuario_admin (requiere admin_rol_id)
4 seed_admin_empresa_link .... vincular_admin_empresa
5 seed_tenant_rbac ........... bootstrap_cliente_rbac
6 seed_codigo_secuencias ..... [MOTOR] _insertar_secuencias_codigo
      └─ prereq: state.empresa_id (TENANT_SEED_SECUENCIAS_PREREQ)
```

### 2.1 Sincronización y operation store

- Cada paso se marca en `bootstrap_applied` (`marker_code = tenant_<step>_v1`, `checksum_sha256`).
- Marker divergente ⇒ `TENANT_SEED_MARKER_CHECKSUM_MISMATCH` (protección anti-drift).
- Al re-ejecutar, los pasos aplicados se **saltan** pero `hydrate_tenant_seed_state` recupera `empresa_id` para que el paso 6 tenga contexto aunque el paso 2 se haya saltado.

### 2.2 Rollback / resumibilidad Dedicated

- No es una única TX atómica: es **resumible** por markers (idempotente por paso).
- Un fallo en el paso 6 no revierte los pasos 1–5; una nueva ejecución los salta y reintenta 6.
- `_verify_row_expectations` actúa como **gate de verificación final**: si `cfg_codigo_secuencia` no alcanza `len(EAGER_SEQUENCE_KEYS)` (57) filas, `TENANT_SEED_ROW_COUNT_FAILED`. El umbral se **deriva** del catálogo, no es un número fijo.

---

## 3. Runtime — lazy creation (fuera del onboarding)

Cuando un servicio ERP pide un código para un `sequence_key` sin fila cfg (p.ej. secuencia no incluida en el eager, o nueva empresa/almacén):

```
Servicio ERP (UoW, DatabaseConnection.DEFAULT + client_id)
  → CodigoGeneracionGateway.allocate(sequence_key, ctx, session)
     → AllocationCoordinator.allocate_next
        → CfgSequenceStore.ensure_row(session, scope_key, defn)   # crea si falta
        → CfgSequenceStore.increment_and_get                       # UPDLOCK/ROWLOCK
        → CodeFormatter.format
```

- `ensure_row` usa **defaults del `SequenceCatalog`** (no del onboarding_seed) — misma fuente de verdad.
- Usa **la sesión del UoW ERP** ⇒ escribe en la misma BD donde luego se leerá (Shared: BD única; Dedicated: BD del tenant).

---

## 4. Puntos de extensión (para ORG/INV)

| Punto | Dónde | Uso previsto |
|-------|-------|--------------|
| Paso de seed | Shared paso 8 / Dedicated paso 6 | Ampliar subconjunto eager si un módulo lo requiere |
| `ensure_row` lazy | `CfgSequenceStore` | Alta on-demand de secuencias EMPRESA/ALMACEN/PV |
| `row_expectations` | `tenant_seed_profiles` | Verificación de conteo Dedicated si cambia el eager |
| Gateway | `CodigoGeneracionGateway` | Único punto de consumo desde services ERP |

**Regla de oro:** ORG/INV **no** insertan filas cfg directamente ni conocen prefijos; consumen el Gateway. El bootstrap sigue siendo el único que hace el seed inicial.

---

## 5. Diferencias Shared vs Dedicated (resumen)

| Aspecto | Shared | Dedicated |
|---------|--------|-----------|
| Conexión | `ADMIN` (BD única) | `provisioning_dedicated_session` (BD tenant) |
| Transacción | TX única atómica | Pasos + markers (resumible) |
| Rollback | Total | Por reintento idempotente |
| Verificación | Implícita (TX) | `row_expectations` explícito |
| auth_config | Paso 7 explícito | Fuera del perfil de seed (verificar paridad) |
| Paso Motor | 8 (último) | 6 (último) |
| Fuente de código del seed | `_insertar_secuencias_codigo` (compartida) | idéntica |

---

*Matriz de responsabilidades en `30`. Ajustes recomendados en `31`.*
