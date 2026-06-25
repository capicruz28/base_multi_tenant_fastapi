# 06 — Rollback Strategy

**Etapa:** 5.7 — Implementation Planning  
**Versión:** IP-1.0  
**Baseline:** BL-1.0

---

## 1. Principios rollback

| # | Principio |
|---|-----------|
| RB-01 | Todo PR debe ser **revertible con un revert commit** |
| RB-02 | PRs pequeños = rollback quirúrgico |
| RB-03 | Rollback **no** requiere redeploy schema |
| RB-04 | Post-rollback: repetir validaciones del PR + fase |
| RB-05 | Rollback F1 alto riesgo → freeze merges hasta green CI |

---

## 2. Estrategias por tipo

| Tipo | Método | Tiempo |
|------|--------|--------|
| PR individual | `git revert <merge-sha>` | Minutos |
| Fase completa | Revert PRs reverse order | Horas |
| Hotfix forward | New PR fix | Prefer if prod already broken |
| Feature flag | `dedicated_enabled=false` | Inmediato — no rollback code |

**BL-1.0:** `dedicated_enabled` default **false** — F1 changes inactive for real dedicated tenants until F6.

---

## 3. Rollback por PR

| PR | Riesgo | Revert impact | Tests repetir post-revert |
|----|--------|---------------|---------------------------|
| PR-F0-01–05 | Bajo | Menos coverage | Full CI |
| PR-F1-01 | Bajo | Engine leak on restart | Smoke shutdown |
| PR-F1-02 | Medio | Cache behavior default | Cache tests |
| PR-F1-03 | Medio | Extra metadata lookups | F1 perf smoke |
| PR-F1-04 | **Alto** | Routing security | **F0-02 + isolation full** |
| PR-F1-05 | Medio | Filter policy | Isolation |
| PR-F1-06 | **Alto** | Data access path | **Full regression** |
| PR-F1-07 | Bajo | Less observability | — |
| PR-F1-08 | Bajo | Less test coverage | — |
| PR-F1-09 | Medio | Repo bypass may return | Grep G-09 |
| PR-F2-01 | Bajo | No prod | — |
| PR-F2-02 | Bajo | CI optional again | — |
| PR-F3-01 | Medio | Mode visible L5 again | Auth tests |
| PR-F3-02 | Medio | IAM branches return | IAM full |
| PR-F3-03 | Medio | RBAC branches return | RBAC full |
| PR-F3-04 | Bajo | No grep enforcement | — |

---

## 4. Rollback por fase

### Revert F1 completa

1. Revert PR-F1-09 → … → PR-F1-01 (orden inverso)
2. Run full pytest + F0 harness
3. Confirm shared tenant staging smoke
4. Tag `rollback-f1-YYYYMMDD`
5. Post-mortem before retry

### Revert F3 completa

1. Revert PR-F3-04 → PR-F3-01
2. Auth + RBAC + grep manual
3. F2 benchmarks still valid (F3 doesn't affect perf path)

---

## 5. Checkpoints rollback

| Checkpoint | Acción si rollback |
|------------|-------------------|
| Post G-F0 | Safe — no prod touched |
| Post G-F1 | Revert F1; shared unchanged if tests pass |
| Post G-F2 | Revert F2 only; F1 remains |
| Post G-F3 | Partial revert F3; **do not** revert F1 without cause |

---

## 6. Producción (staging/prod)

| Escenario | Acción |
|-----------|--------|
| Shared tenant errors post-F1 | Revert last F1 PR; escalate |
| Latency >2x post-F1 | Revert F1-03,06 first suspects |
| Auth broken post-F3 | Revert F3-01,02 immediately |
| Dedicated tenant attempted (forbidden) | Config flag off; no code rollback needed |

**Nota:** Dedicated tenants **no deben existir** en prod during F0–F3.

---

## 7. Datos y migraciones

| Aspecto | Rollback |
|---------|----------|
| DDL changes | **Ninguno** en F0–F3 — N/A |
| Data migration | N/A |
| Cache invalidation | Restart workers post-rollback F1 |

---

## 8. Comunicación

| Evento | Canal | Owner |
|--------|-------|-------|
| Revert PR alto riesgo | Slack + ticket | Tech Lead |
| Revert fase | Steering notify | Architect |
| Post-mortem | Doc within 48h | Implementador |

---

## 9. Plantilla rollback PR

```markdown
## Rollback Plan
- Revert command: git revert -m 1 <sha>
- Risk: High/Med/Low
- Blast radius: shared tenants / infra only
- Re-test: [list from §3]
- Rollback owner: @name
- Decision window: 30 min post-merge monitor
```

---

## 10. Conclusión

Rollback **pre-planificado por PR**. F1-04 y F1-06 requieren **full regression** post-revert.
