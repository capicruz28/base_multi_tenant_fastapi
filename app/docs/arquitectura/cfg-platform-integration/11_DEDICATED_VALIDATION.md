# Micro-validación — Pipeline Dedicated para CFG

**Fecha:** 2026-07-18  
**Alcance:** Solo `catalog_profiles.py` (registry, checksums, row expectations).  
**Contexto:** Shared OK. Solo provisioning Dedicated nuevo.

---

## 1. ¿Dedicated ejecuta S010?

**Sí.**

Evidencia (`resolve_catalog_seed_profile`):

```python
script_codes = ["catalog_s010", "catalog_s020", "catalog_s030"]
```

Registry: `("catalog_s010", "02_catalog/S010__seed_modulo_menu_completo.sql", 10, None)`.

Al ejecutar S010 actualizado (tras Fase 1), el módulo/menú CFG se siembra en la BD Dedicated **si** el checksum de S010 coincide.

---

## 2. ¿Dedicated ejecuta S068?

**No.**

Evidencia:

- `_build_catalog_registry()` / `raw_defs`: no hay `catalog_s068`
- `_CATALOG_CHECKSUMS`: no hay clave `permisos_rbac/S068__permisos_rbac_cfg.sql`
- `resolve_catalog_seed_profile`: no añade S068 a `script_codes`

Sin S068, la BD Dedicated no recibe `cfg.secuencias.*` en `permiso` vía catalog seed → `bootstrap_global_grants_admin_tenant` no puede otorgarlos (no hay filas `cfg.%`).

---

## 3. ¿Deben actualizarse checksums tras S010?

**Sí.**

Exactamente:

| Clave en `_CATALOG_CHECKSUMS` | Motivo |
|-------------------------------|--------|
| `02_catalog/S010__seed_modulo_menu_completo.sql` | S010 modificado (módulo/sección/menú CFG); el SHA actual (`a60ab6d4…`) ya no corresponde |

No hace falta actualizar checksums de S020/S030/S04x por CFG (no se tocaron).  
Al registrar S068, habrá que **añadir** (no actualizar) su checksum.

---

## 4. ¿Debe actualizarse el número esperado de módulos?

**Sí.**

Dónde: `_row_expectations_for_plan()` en `catalog_profiles.py`:

```python
("modulo", 27),  # → debe ser 28
```

Motivo: S010 ahora inserta 28 filas en `modulo` (27 + CFG).

---

## 5. ¿Otro cambio estrictamente obligatorio?

**Sí — registrar y ejecutar S068 en el perfil Dedicated.**

Obligatorio para paridad Shared (permisos API `cfg.secuencias.*`):

1. Entrada en `_CATALOG_CHECKSUMS` para S068  
2. Entrada en `raw_defs` / registry (`catalog_s068`, order ~68, `module_code=None`)  
3. Incluir `catalog_s068` en la lista base de `resolve_catalog_seed_profile` (junto a S010/S020/S030), porque CFG no tiene script S04x en `_MODULE_TO_SCRIPT_CODES`

**No obligatorio** para esta paridad (dentro del alcance auditado):

- Añadir `CFG` a `ALL_CATALOG_MODULE_CODES` (enterprise solo selecciona S04x; CFG no tiene S04x)
- Entrada `_MODULE_TO_SCRIPT_CODES["CFG"]`
- S021

`TRIAL_MODULES` ya incluye CFG → onboarding RBAC Dedicated activará `cliente_modulo` + OwnerSync menú una vez el catálogo Dedicated tenga S010 (+ S068 para permisos).

---

## Archivos que realmente necesitan modificación

| Archivo | Cambios obligatorios |
|---------|----------------------|
| `app/infrastructure/provisioning/catalog_profiles.py` | (1) checksum S010, (2) `("modulo", 28)`, (3) registrar + ejecutar siempre `catalog_s068` (+ checksum S068) |

Ningún otro archivo dentro del alcance de esta micro-validación.

---

## Resumen respuestas

| # | Respuesta |
|---|-----------|
| 1 | **Sí** — S010 se ejecuta |
| 2 | **No** — S068 no se ejecuta |
| 3 | **Sí** — checksum de S010 |
| 4 | **Sí** — `("modulo", 27)` → `28` |
| 5 | **Sí** — registrar/ejecutar S068 en el profile |
