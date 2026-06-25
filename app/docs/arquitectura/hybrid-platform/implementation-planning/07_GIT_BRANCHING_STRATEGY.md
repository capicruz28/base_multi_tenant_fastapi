# 07 — Git Branching Strategy

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Modelo

**Trunk-based development** con feature branches **cortas** (<5 días) merge a `main`.

```
main (protected)
  ├── hybrid/f0-harness          → PR-F0-*
  ├── hybrid/f1-gateway          → PR-F1-* (sequential or stacked)
  ├── hybrid/f2-regression       → PR-F2-*
  └── hybrid/f3-l5-cleanup       → PR-F3-*
```

---

## 2. Convención de ramas

| Pattern | Uso | Ejemplo |
|---------|-----|---------|
| `hybrid/f{N}-{topic}` | Fase container branch | `hybrid/f1-gateway` |
| `hybrid/f{N}-{topic}/{wp-id}` | PR-specific (opcional) | `hybrid/f1-gateway/wp03-route-cache` |
| `hotfix/hybrid-{desc}` | Producción urgente | `hotfix/hybrid-routing-revert` |

**Regla:** Max **1** fase activa en paralelo por developer en infra.

---

## 3. Orden de merge

| Paso | Acción |
|------|--------|
| 1 | Merge all F0 PRs → `main` |
| 2 | Tag checkpoint `hybrid-gate-f0` |
| 3 | Branch `hybrid/f1-gateway` from `main` |
| 4 | Merge F1 PRs **sequentially** (rebase on main between) |
| 5 | Tag `hybrid-gate-f1` |
| 6 | F2 branch → merge → tag `hybrid-gate-f2` |
| 7 | F3 branch → merge → tag `hybrid-bl10-f0-f3-complete` |

**Prohibido:** Merge F1 PRs directly to long-lived branch without syncing main daily.

---

## 4. Branch protection `main`

| Rule | Setting |
|------|---------|
| Require PR | ✅ |
| Require reviews | 2 (1 infra + 1 architect for F1+) |
| Require status checks | `pytest`, `openapi-diff`, `erp-guard`, `shared-regression` (F2+) |
| No force push | ✅ |
| Linear history | Optional squash |

---

## 5. Checkpoints y tags

| Tag | Cuándo | Propósito |
|-----|--------|-----------|
| `hybrid-gate-f0` | G-F0 pass | Rollback reference pre-F1 |
| `hybrid-gate-f1` | G-F1 pass | Benchmark baseline anchor |
| `hybrid-gate-f2` | G-F2 pass | Pre-F3 stable |
| `hybrid-bl10-f0-f3-complete` | G-F3 pass | Etapa 6 scope complete |

---

## 6. Stacked PRs (opcional)

Si equipo usa Graphite/stack:

| Regla | Descripción |
|-------|-------------|
| SP-01 | Max stack depth 3 |
| SP-02 | Only within same phase |
| SP-03 | Bottom PR must pass CI independently where possible |

Prefer **sequential merge** over deep stacks for F1.

---

## 7. Sync y conflictos

| Situación | Acción |
|-----------|--------|
| Main advanced | Rebase feature branch daily |
| Conflict infra | Infra owner resolves |
| Conflict test | Test owner resolves |

---

## 8. Hotfix

| Escenario | Branch from | Merge to |
|-----------|-------------|----------|
| Prod shared broken | `main` or last gate tag | `main` + cherry-pick if mid-phase |
| F1 in progress | Last gate tag | `main`, then rebase F1 branch |

---

## 9. Rollback git

| Acción | Comando |
|--------|---------|
| Revert merge | `git revert -m 1 <merge-commit>` |
| Reset to gate | Deploy from tag `hybrid-gate-f{N}` — **no** force push main |

Detalle: `06_ROLLBACK_STRATEGY.md`

---

## 10. Feature flags

| Flag | Branch | Default |
|------|--------|---------|
| `DEDICATED_ENABLED` | Config only F1+ | `false` all envs prod |

Branch changes for flag **only** in `core/config.py` — separate PR if needed.

---

## 11. Conclusión

Git strategy: **short branches**, **sequential F1 merges**, **4 gate tags**, **protected main**.
