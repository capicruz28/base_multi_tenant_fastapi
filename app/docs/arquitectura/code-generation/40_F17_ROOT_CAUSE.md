# 40 — F17 Root Cause (Causa raíz)

> Fase **F17G**. Solo lectura. Conclusión con evidencia. Sin soluciones (ver `41`).

---

## 1. Causa raíz (formato solicitado)

### Cambio responsable (nexo causal primario)

- **Archivo:** `app/bootstrap_v2/01_schema/V010__tablas_bd_erp_completo.sql`
  (reshape de `cfg_codigo_secuencia`, ≈ línea 6809) **+**
  `app/infrastructure/provisioning/script_manifest.py`
  (constante `_V010_ERP_SHA256`).
- **Método / símbolo:** DDL `CREATE TABLE cfg_codigo_secuencia`; constante
  `_V010_ERP_SHA256`; validada por `validate_manifest_integrity` en el paso S4.
- **Línea:** V010 ≈ 6809; `script_manifest.py` línea de `_V010_ERP_SHA256`.
- **Fase F17:** reshape en **OLA‑0**; realineo de checksum en **F17F**.
- **Qué cambió:** el contenido de V010 cambió (`SHA‑256 78733886… → 5f81e8c3…`);
  F17F actualizó el checksum congelado a `5f81e8c3…`, **reabriendo S4**.
- **Por qué rompe el onboarding:** durante toda la fase F17 Dedicated abortaba en
  S4, dejando **S6/S7 sin ejecutar**. Al reabrir S4, la saga alcanza S6/S7 **por
  primera vez desde el inicio de F17** y quedan expuestos fallos preexistentes de
  ese tramo. F17F es correcto y necesario (cerró la regresión F17E); su efecto
  colateral es *destapar* S6→S7.

### Fallo #1 observado — `FK_permiso_menu` (en el tramo destapado)

- **Archivo:** `app/modules/tenant/application/services/onboarding_rbac_service.py`
  (sub‑paso S7 `seed_tenant_rbac`), a través de
  `OwnerSyncService` / `BaseOperativeService`.
- **Método:** `OnboardingRbacService.bootstrap_cliente_rbac` →
  `sync_modules_for_owner` (`:137`) / `apply_to_operative_roles` (`:163`).
- **Constraint violada:** `FK_permiso_menu`
  (`rol_menu_permiso.menu_id → modulo_menu(menu_id)`,
  `app/bootstrap_v2/05_dedicated/V020__tenant_identity_rbac_store.sql:356`).
- **Fase F17:** **ninguna** — este archivo/ruta **no** fue modificado por F17
  (git: `469af23`; ausente del diff).
- **Qué cambió (en F17):** nada en esta ruta.
- **Por qué rompe el onboarding:** algún `menu_id` referenciado por los bundles no
  está presente en `modulo_menu` cuando corre S7. La verificación de S6
  (`catalog_profiles._row_expectations_for_plan:321‑335`) **no comprueba
  `modulo_menu`**, así que un déficit pasa S6 y revienta en S7. Es una laguna de
  **acoplamiento catálogo(S6)↔bundle(S7)** preexistente, hecha alcanzable por F17F.

### Fallo #2 observado — "run no está en provisioning" (cascada)

- **Archivo:** `app/modules/tenant/application/services/tenant_provisioning_state_service.py`.
- **Método:** `_transition_step` (línea 457), guard en **línea 485**;
  `internal_code = PROVISIONING_RUN_NOT_ACTIVE` (línea 490); mensaje línea 488.
- **Disparadores:** `mark_step_*` desde
  `dedicated_provisioning_orchestrator.py` (`:284`, `:299`, `:477`, `:532‑569`,
  `:678‑685`) o retry `compensation:326`.
- **Fase F17:** **ninguna** — código no modificado por F17 (git: `72ebaa1`).
- **Qué cambió (en F17):** nada en esta ruta.
- **Por qué rompe el onboarding:** es **secundario**. Requiere que el run ya haya
  salido de `PROVISIONING` (a `FAILED`/`READY`) y que otra ruta o entrega
  concurrente intente mutar steps. Se materializa por (a) la cascada tras el fallo
  primario de S7, y/o (b) los ciclos de retry/redispatch sobre runs dejados
  inconsistentes durante la ventana F17E (donde la reconciliación reventaba
  **antes** de `_fail_step_and_run`: `orchestrator:504` vs `:512`).

---

## 2. Cadena causal (5 Whys)

1. **¿Por qué aparece `FK_permiso_menu` ahora?**
   Porque la saga por fin ejecuta S7 (`seed_tenant_rbac`) contra una BD dedicada real.
2. **¿Por qué recién ahora ejecuta S7?**
   Porque **F17F** realineó `_V010_ERP_SHA256` y **S4 dejó de abortar**.
3. **¿Por qué S4 abortaba?**
   Porque F17 (OLA‑0) reescribió V010 y su `SHA‑256` dejó de coincidir con el
   checksum congelado (regresión F17E).
4. **¿Por qué la FK falla en S7 y no se detectó en S6?**
   Porque S6 aplica `modulo_menu` (S010) pero su verificación **no** cuenta filas
   de `modulo_menu` (`catalog_profiles.py:321‑335`); el déficit solo se manifiesta
   al insertar `rol_menu_permiso`.
5. **¿Por qué el déficit no se veía "antes de F17"?**
   Porque el "antes de F17" Dedicated está validado con **tests mockeados**
   (`test_f4_08_*`, `test_hybrid_provisioning_e2e`), que no ejercen el FK real; y
   porque durante F17 el tramo S6→S7 estuvo bloqueado por S4. La primera ejecución
   real de S6→S7 desde el inicio de F17 ocurre tras F17F.

---

## 3. Qué NO es la causa (descartado con evidencia)

- **No** son las FKs nuevas de `cfg_codigo_secuencia` (`FK_cfg_empresa/almacen/
  punto_venta`): las tablas referenciadas existen antes en V010
  (`org_empresa:156`, `inv_almacen:746`, `pos_punto_venta:5154` vs `cfg:6809`) →
  V010 se aplica sin fallo por esas FKs, y además esas FKs no son `FK_permiso_menu`.
- **No** es un cambio de orden de la saga (`SAGA_STEP_ORDER` sin cambios).
- **No** es un cambio de catálogo (`S010/S020/S030`, `catalog_profiles.py` sin
  cambios F17).
- **No** es un cambio de RBAC (`onboarding_rbac_service`, `manager_standard`,
  `user_standard`, `owner_sync`, `base_operative` sin cambios F17).
- **No** es el sub‑paso `seed_codigo_secuencias` (única rama F17 en el seed):
  ocurre **después** de `seed_tenant_rbac`; un fallo suyo sería
  `TENANT_SEED_ROW_COUNT_FAILED`/`cfg`‑FK, no `FK_permiso_menu`.
- **No** es un ImportError por el nuevo acoplamiento a `app.core.codigo.*`
  (107 tests verdes).

---

## 4. Veredicto

- **Nexo causal F17 (demostrado):** reshape de V010 + checksum (OLA‑0 → F17F).
  Es lo que cambia la **alcanzabilidad** de S6→S7.
- **Fallos que se observan en el tramo destapado:** `FK_permiso_menu` (defecto de
  acoplamiento catálogo↔bundle en S7, **código previo a F17**) y
  `PROVISIONING_RUN_NOT_ACTIVE` (cascada/retry, **código previo a F17**).
- **Afirmación central:** F17 **no** introdujo código que rompa RBAC/estado; F17
  (vía F17F, corrección legítima) **hizo alcanzable** un tramo S6→S7 con defectos
  y estado residual preexistentes.

> Para confirmar cuál de los dos sub‑orígenes del Fallo #1 aplica en la instalación
> concreta (déficit real de `modulo_menu` en BD limpia **vs.** estado sucio de runs
> fallidos), se requiere evidencia de runtime: el `COUNT(*)` de `modulo_menu` tras
> S6 y el `menu_id` exacto de la fila `rol_menu_permiso` que dispara la FK. Esa
> captura es de ejecución, fuera del alcance de solo‑lectura de F17G; las opciones
> para obtenerla y remediar están en `41_F17_REMEDIATION_OPTIONS.md`.
