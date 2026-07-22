# Empresa Bootstrap V1 — Auditoría de integración ORG

**Proyecto:** Empresa Bootstrap V1 (post Bootstrap V2)  
**Fecha:** 2026-07-10  
**Estado:** Solo auditoría — sin implementación  
**Base:** Bootstrap V2 completado (Fases 1–4)

---

## 1. Resumen ejecutivo

El módulo **ORG** ya expone `POST /api/v1/org/empresa` para crear empresas adicionales (`EMP002`, `EMP003`, …). Ese flujo **solo inserta** `org_empresa` y **no** ejecuta bootstrap de cfg (`cfg_codigo_secuencia` scope EMPRESA).

`EmpresaBootstrapService` (Bootstrap V2) hoy cubre onboarding inicial (`INITIAL`) vía `ensure_empresa_inicial`, `vincular_admin_empresa` e `insertar_secuencias_codigo` → `seed_cfg_empresa`. **Ningún método está conectado al flujo ORG.**

**Gap principal (G2/G3 AS-IS):** empresa adicional operativa en ORG sin 56 filas cfg EMPRESA → motor de códigos y documentos ERP pueden fallar o depender de lazy paths no garantizados en onboarding.

**Integración mínima V1:** tras crear `org_empresa` en ORG, invocar `seed_cfg_empresa` (vía `EmpresaBootstrapService`) en la **misma transacción** que el INSERT.

---

## 2. Flujo actual de creación de empresa (AS-IS)

### 2.1 Endpoint

| Atributo | Valor |
|----------|-------|
| **Ruta** | `POST /api/v1/org/empresa` |
| **Router** | `app/modules/org/presentation/endpoints_empresa.py` → `crear_empresa` |
| **Prefijo módulo** | `/org/empresa` (`endpoints.py`) |
| **RBAC** | `org.empresa.crear` |
| **Session gate** | `require_org_tenant_erp_session` (tenant-wide; **no** exige `empresa_id` en JWT) |
| **cliente_id** | `get_org_session_client_id` (impersonación-safe) |

### 2.2 Orquestador

| Capa | Componente |
|------|------------|
| **Orquestador** | `empresa_service.create_empresa_servicio` |
| **Queries** | `empresa_queries.create_empresa` |
| **No participan** | `TenantBootstrapOrchestrator`, `ClienteOnboardingService`, `MinimalErpTenantBootstrapService.ensure_empresa_inicial` |

### 2.3 Secuencia actual

```
POST /org/empresa
  → create_empresa_servicio(client_id, EmpresaCreate)
      → pre-check codigo_empresa único (SELECT)
      → pre-check ruc único (SELECT)
      → create_empresa(client_id, payload)   # INSERT org_empresa
      → log_org_empresa_scope(create_ok)
      → assert_row_tenant
      → return EmpresaRead
```

### 2.4 Métodos que crean `org_empresa`

| Método | Contexto | Código empresa | Idempotencia |
|--------|----------|----------------|--------------|
| `empresa_queries.create_empresa` | ORG runtime | Body (`codigo_empresa` libre, ej. EMP002) | No — ConflictError pre-check |
| `MinimalErpTenantBootstrapService.ensure_empresa_inicial` | Onboarding tenant | Fijo `EMP001` | Sí — retorna primera empresa existente |
| `EmpresaBootstrapService.ensure_empresa_inicial` | Facade onboarding | Delega EMP001 | Igual AS-IS |

**Conclusión:** ORG y onboarding usan **caminos distintos**. `ensure_empresa_inicial` **no debe** usarse para empresas adicionales ORG (hardcode EMP001, semántica idempotente de sede).

### 2.5 Validaciones existentes

| Validación | Dónde | HTTP |
|------------|-------|------|
| `codigo_empresa` único por tenant | `create_empresa_servicio` + SELECT | 409 ConflictError |
| `ruc` único por tenant | `create_empresa_servicio` + SELECT | 409 ConflictError |
| `cliente_id` forzado desde sesión | `create_empresa` query | — |
| RBAC `org.empresa.crear` | endpoint | 403 |
| Tenant scope post-insert | `_assert_empresa_row` | 404 cross-tenant |
| Schema Pydantic | `EmpresaCreate` (normalize mixins) | 422 |
| **No valida** | Existencia previa de EMP001 | — |
| **No valida** | cfg EMPRESA ya sembrada | — |

### 2.6 Transacción

| Aspecto | Comportamiento AS-IS |
|---------|---------------------|
| Patrón ORG | `execute_insert` en `queries_async.py` |
| Session | Abre contexto propio `_get_connection_context(client_id)` |
| Commit | **Automático** al final de cada `execute_insert` |
| UoW compartida | **No** — cada INSERT es TX independiente |
| Session propagable | **No** — `create_empresa_servicio` no recibe `AsyncSession` |

**Implicación V1:** integrar `seed_cfg_empresa` sin refactor TX deja empresa creada y cfg en riesgo si el seed falla (estado parcial), o requiere segunda conexión (no atómico).

### 2.7 Hooks post-INSERT

| Hook | Existe |
|------|--------|
| Logging `log_org_empresa_scope` | Sí |
| `assert_row_tenant` | Sí |
| Seed cfg EMPRESA | **No** |
| `vincular_admin_empresa` | **No** |
| RBAC por empresa | **No** |
| Eventos / cola | **No** |
| Invalidación cache | **No** |

### 2.8 Qué ocurre después de crear empresa (hoy)

1. API retorna `EmpresaRead` (201).
2. Empresa visible en `GET /org/empresa`.
3. Usuario puede seleccionar empresa en sesión (flujo auth separado).
4. Recursos company-scoped (sucursales, INV, etc.) pueden crearse **si** el usuario tiene `empresa_id` en JWT.
5. **No** se crean 56 filas `cfg_codigo_secuencia` scope EMPRESA para el nuevo `empresa_id`.

### 2.9 Qué NO ocurre y debería (V1)

| Debería ocurrir | Owner diseño V2 | Prioridad V1 |
|-----------------|-----------------|--------------|
| Seed 56 filas cfg EMPRESA | Empresa Bootstrap (E-CFG) | **P0** |
| Idempotencia por `empresa_id` | `insert_secuencia` repo | **P0** (ya existe) |
| Misma TX INSERT + seed | ORG orquestador + session | **P0** |
| Seed cfg TENANT (1 fila) | Tenant Bootstrap | **No** — ya existe por tenant |
| `vincular_admin_empresa` | Solo onboarding INITIAL | **No** en V1 |
| Sucursal sede / almacén default | Dominio ORG/INV futuro | Fuera V1 |
| RBAC grants por empresa | IAM futuro | Fuera V1 |

---

## 3. Grafo de dependencias actual

### 3.1 Onboarding inicial (referencia — no modificar en V1)

```
TenantBootstrapOrchestrator
  → EmpresaBootstrapService.ensure_empresa_inicial      (EMP001)
  → EmpresaBootstrapService.vincular_admin_empresa
  → seed_cfg_tenant + EmpresaBootstrapService.insertar_secuencias_codigo
        → seed_cfg_empresa (56 filas)
```

### 3.2 ORG empresa adicional (AS-IS — sin bootstrap)

```
POST /org/empresa
  → create_empresa_servicio
      → create_empresa (INSERT)
  ✗ sin EmpresaBootstrapService
```

### 3.3 Consumidores de `empresa_id` (post-creación)

| Dominio | Dependencia | Requiere cfg EMPRESA |
|---------|-------------|-------------------|
| Motor códigos | `cfg_codigo_secuencia` por fingerprint | **Sí** (eager 56) |
| INV / ORG company | `ensure_empresa_in_tenant` | Empresa existe (cfg indirecto) |
| Documentos F2 | secuencias MOV, OC, etc. | **Sí** |
| Maestros F1 | secuencias CAT, PROV, etc. | **Sí** |
| Lazy ALMACEN/PV | `AllocationCoordinator.ensure_row` | No en alta empresa |
| Auth sesión | selección empresa JWT | Solo fila `org_empresa` |
| Dedicated provisioning | N/A para ORG runtime | — |

---

## 4. EmpresaBootstrapService — estado y contrato ADDITIONAL

### 4.1 API actual (post Bootstrap V2 Fase 4)

| Método | Rol | Requiere `session` |
|--------|-----|-------------------|
| `ensure_empresa_inicial` | E-ORG onboarding EMP001 | Sí |
| `vincular_admin_empresa` | E-LNK admin | Sí |
| `insertar_secuencias_codigo` | E-CFG → `seed_cfg_empresa` (56) | Sí |

### 4.2 Modo ADDITIONAL (diseño `bootstrap-v2/design/04` §1.3)

| Operación V1 | Método existente | Notas |
|--------------|------------------|-------|
| E-ORG | **ORG** `create_empresa` | Ya implementado; no duplicar en bootstrap |
| E-CFG | `insertar_secuencias_codigo` / `seed_cfg_empresa` | **Única integración mínima V1** |
| E-LNK | Prohibido ADDITIONAL | Admin ya existe |

### 4.3 Integración mínima requerida

1. **Punto de invocación:** `create_empresa_servicio`, inmediatamente después de obtener `empresa_id`, **antes** de retornar `EmpresaRead`.
2. **Llamada:** `EmpresaBootstrapService.insertar_secuencias_codigo(session, client_id, empresa_id)` (o alias formal `bootstrap_cfg_empresa` modo ADDITIONAL).
3. **Prerequisito:** `session` SQL compartida entre INSERT y seed.
4. **Prohibido V1:** invocar `ensure_empresa_inicial` desde ORG (duplicaría/conflictuaría semántica EMP001).

---

## 5. Decisiones arquitectónicas (respuestas explícitas)

| Pregunta | Decisión V1 |
|----------|-------------|
| ¿Punto exacto de invocación? | `empresa_service.create_empresa_servicio`, post-INSERT, pre-return |
| ¿ORG sigue siendo orquestador? | **Sí** — ORG posee validaciones de negocio, RBAC, contrato API |
| ¿EmpresaBootstrap es subrutina? | **Sí** — componente interno E-CFG; no endpoint propio |
| ¿Una única transacción? | **Sí (objetivo normativo)** — requiere refactor queries ORG a session-driven UoW; AS-IS no lo cumple |
| ¿Reutilizar `ensure_empresa_inicial`? | **No** para ADDITIONAL |

---

## 6. Matriz de consumidores y riesgo

| Consumidor | Archivo | Método | Tipo | Auto-migra | Cambio Fase V1 | Riesgo |
|------------|---------|--------|------|------------|----------------|--------|
| ORG create | `empresa_service.py` | `create_empresa_servicio` | Orquestador | No | Invocar EBS + UoW session | **Alto** |
| ORG insert | `empresa_queries.py` | `create_empresa` | Directa SQL | Parcial | Aceptar `session` opcional | **Alto** |
| EBS cfg | `empresa_bootstrap_service.py` | `insertar_secuencias_codigo` | SSOT E-CFG | Sí | Sin cambio firma; caller nuevo | Bajo |
| SSOT seed | `cfg_codigo_onboarding_seed.py` | `seed_cfg_empresa` | Implementación | Sí | Sin cambio | Bajo |
| Onboarding INITIAL | `tenant_bootstrap_orchestrator.py` | `run_seed_*` | Indirecta | Sí | Sin cambio | Nulo |
| Dedicated S7 | `dedicated_tenant_seed_adapters.py` | `run_seed_codigo_secuencias` | Indirecta | Sí | Sin cambio | Nulo |
| `ensure_empresa_inicial` | `minimal_erp_tenant_bootstrap_service.py` | onboarding only | Legacy INITIAL | N/A | No usar en ORG | Medio si se reusa mal |
| Tests ORG scope | `test_org_empresa_tenant_scope.py` | scope helpers | Tests | N/A | Sin cambio | Nulo |
| Tests F17D | `test_codigo_engine_f17d_full_cfg_seed.py` | seed split | Tests | N/A | Añadir test ADDITIONAL opcional | Bajo |
| Repair legacy | `legacy_tenant_rbac_repair_service.py` | — | No consume | N/A | Futuro ENSURE | Nulo |
| Scripts | `scripts/*.py` | — | No consume | N/A | Ninguno | Nulo |
| Docs AS-IS | `bootstrap-v2/03` §3 | — | Documental | N/A | Actualizar post-V1 | Bajo |

---

## 7. Riesgos e impedimentos

| ID | Riesgo | Severidad | Mitigación V1 |
|----|--------|-----------|---------------|
| R-EBV1-01 | TX no atómica ORG (`execute_insert` commit inmediato) | **Alta** | UoW: `get_db_connection` + `session.begin()` en `create_empresa_servicio` |
| R-EBV1-02 | Empresa sin cfg si seed falla post-commit | Alta | Misma TX; rollback conjunto |
| R-EBV1-03 | Uso incorrecto de `ensure_empresa_inicial` en ORG | Media | Solo `insertar_secuencias_codigo`; documentar ADDITIONAL |
| R-EBV1-04 | Dedicated vs Shared DB path | Media | ORG usa `execute_query(client_id=)` — mismo patrón que cfg repo con session |
| R-EBV1-05 | Conteo cfg global 57 vs 56×N empresas | Baja | Row expectations Dedicated solo onboarding; ORG suma 56 por empresa nueva |
| R-EBV1-06 | Capa tenant importa tenant bootstrap desde org | Baja | ORG → `EmpresaBootstrapService` permitido (orquestador llama interno) |

### 7.1 Callers ocultos

**No detectados** en código Python productivo: grep `_insertar_secuencias_codigo`, `create_empresa_servicio`, `insertar_secuencias_codigo` confirma únicos caminos documentados.

### 7.2 Imports circulares potenciales

| Ruta propuesta | Ciclo |
|----------------|-------|
| `org.empresa_service` → `EmpresaBootstrapService` → `cfg_codigo_onboarding_seed` | **Sin ciclo** |
| `EmpresaBootstrapService` → `org.*` | **Prohibido** — no necesario |

### 7.3 Tests dependientes del monolito cfg

Post Fase 4: **ningún test** llama `_insertar_secuencias_codigo`. F17D usa `seed_cfg_tenant` + `seed_cfg_empresa` directamente.

### 7.4 Documentación inconsistente

| Documento | Inconsistencia |
|-----------|----------------|
| `bootstrap-v2/03_TENANT_VS_EMPRESA.md` §3 | Indica "no existe endpoint crear empresa" — **desactualizado**; existe `POST /org/empresa` |
| `code-generation/bootstrap/03_BOOTSTRAP_RULES.md` | Cita solo `_insertar_secuencias_codigo` monolítico — desactualizado post F4 |
| `bootstrap-v2/design/04` §ADDITIONAL | Correcto conceptualmente; pendiente implementación ORG |

---

## 8. Diseño objetivo V1 (sin implementar)

### 8.1 Flujo target

```
POST /org/empresa
  → create_empresa_servicio
      async with get_db_connection(DEFAULT, client_id) as session:
        async with session.begin():
          row = await create_empresa(..., session=session)
          await EmpresaBootstrapService.insertar_secuencias_codigo(
              session, client_id, row["empresa_id"]
          )
      return EmpresaRead
```

### 8.2 Contrato ADDITIONAL formal (extensión documental)

| Campo | Valor |
|-------|-------|
| Modo | `ADDITIONAL` |
| Trigger | `create_empresa_servicio` éxito |
| Input | `session`, `cliente_id`, `empresa_id` |
| Operaciones | E-CFG únicamente (`seed_cfg_empresa`) |
| Output | `empresa_id` (sin cambio API) |
| Idempotencia | Repo `insert_secuencia` skip si existe |
| Observable API | Sin cambio `EmpresaRead` |

### 8.3 Fuera de alcance V1

- Modo `ENSURE` / repair scripts
- `BootstrapExtensionRegistry`
- Sucursal/almacén sede automáticos
- Reasignación admin default
- Cambios OpenAPI / contrato `EmpresaCreate`

---

## 9. Checklist pre-implementación

- [ ] Confirmar patrón UoW session en ORG (alinear con onboarding Shared)
- [ ] Extender `create_empresa` query para `session` opcional (sin romper callers)
- [ ] Invocar `EmpresaBootstrapService.insertar_secuencias_codigo` en `create_empresa_servicio`
- [ ] **No** invocar `ensure_empresa_inicial` ni `vincular_admin_empresa` desde ORG
- [ ] Tests: empresa adicional tiene 56 cfg EMPRESA; TENANT sigue en 1 fila
- [ ] Tests: rollback si seed falla (empresa no persiste)
- [ ] Actualizar docs AS-IS §3 (endpoint existe)
- [ ] Gate: F17D + test integración ORG create

---

## 10. Veredicto auditoría

**Listo para diseño de implementación V1** con condición **R-EBV1-01** (transacción ORG) resuelta en el mismo entregable de implementación.

No hay blockers arquitectónicos en `EmpresaBootstrapService` ni en `seed_cfg_empresa`. El gap es **wiring ORG → E-CFG + UoW**.
