# bootstrap_v2 — Línea oficial de bootstrap ERP multiempresa

Nueva estructura reproducible que **reorganiza** los scripts SQL auditados sin modificar los originales en `app/docs/database/`.

## Inicio rápido

1. Leer orden: [`00_manifest/BOOTSTRAP_ORDER.md`](00_manifest/BOOTSTRAP_ORDER.md)
2. Inventario: [`00_manifest/BOOTSTRAP_MANIFEST.md`](00_manifest/BOOTSTRAP_MANIFEST.md)
3. Problemas conocidos: [`00_manifest/BOOTSTRAP_GAPS.md`](00_manifest/BOOTSTRAP_GAPS.md)
4. Mapa legacy ↔ v2: [`00_manifest/SOURCE_MAP.json`](00_manifest/SOURCE_MAP.json)

## Árbol

```
app/bootstrap_v2/
├── README_BOOTSTRAP.md          ← este archivo
├── 00_manifest/                 ← documentación
├── 01_schema/                   ← V010, V020, V030 (DDL)
├── 02_catalog/                  ← S010–S030 + permisos_rbac/
├── 03_runtime/                  ← R010, R020
├── 04_qa/                       ← D010–D030 (solo QA)
└── 05_dedicated/                ← RBAC en BD dedicada
```

## Qué cambió respecto a `app/docs/database/`

| Antes | Ahora |
|-------|--------|
| Nombres numerados mezclados (`1.-`, `3.-`, seeds sueltos) | Capas por responsabilidad + prefijos `V/S/R/D` |
| Orden documentado incorrecto (central antes ERP) | Orden oficial: **V010 ERP → V020 central** |
| Demo y prod en mismos scripts | `04_qa/` aislado |
| 27+ archivos permisos sin orden | `02_catalog/permisos_rbac/S040–S066` |

Los archivos bajo `bootstrap_v2/` son **copias** del contenido legacy (misma lógica). Ver cabecera en cada `.sql`.

## Ejecución mínima producción

```text
01_schema/V010 → V020 → V030
02_catalog/S010 → S020 → S030 → S040…S066 (sin S067)
[start FastAPI]
03_runtime/R010 → R020
[API onboarding por tenant]
```

## Ejecución desarrollo / QA

Añadir después del mínimo prod:

```text
04_qa/D010 → D020 → D030
+ SQL manual multiempresa (ver app/docs/pruebas/)
```

## Dedicated

En cada BD dedicada del tenant:

```text
01_schema/V010 (en BD dedicada)
05_dedicated/V010
```

## No incluido en v2

- `SEED_BD_DEDICADA_TECHCORP.sql` / `GLOBALLOG.sql` (desalineados; ver GAPS)
- Scripts en `app/docs/database/migrations/`
- Cualquier SQL fuera de la lista auditada

## Próximos pasos (fuera de este PR)

- Migraciones versionadas desde `01_schema/`
- Script refresh copias desde legacy
- Corregir gaps en fuente legacy (no en copias v2)
- Automatizar runner CLI/CI contra `BOOTSTRAP_ORDER.md`
