# ORG FE — Etapa A: cierre (infra sesión / contexto / guards)

**Estado:** Blueprint + guía de integración listos en este repo backend.  
**Pendiente en repo FE React:** copiar archivos y cablear `useEmpresaActiva` real (ver `INTEGRACION_ETAPA_A.md`).

---

## Diff resumido

| Área | Entregable |
|------|------------|
| Hook sesión | `useOrgSessionScope()` — cliente/empresa JWT, scope tenant/company/hybrid, guards |
| Sync + RQ | `useOrgSessionSync()` — invalidación segmentada al cambiar empresa |
| Guards | `orgSessionGuards.ts`, `OrgRouteGuard.tsx` — `selection_pending`, company-scoped |
| Errores API | `orgScopeErrors.ts` — `MISSING_SESSION_EMPRESA`, `EMPRESA_SCOPE_MISMATCH` |
| Query keys | `orgQueryKeys.ts` — prefijos por `clienteId` + `empresaActivaId` |
| Docs | `INTEGRACION_ETAPA_A.md`, tipos en `types.ts` |

**Explícitamente NO incluido (Etapa B+):**

- Eliminar `empresa_id` de `org.service` / query strings.
- Refactor visual completo de páginas (selectores empresa locales).
- UI híbrida parámetros (Etapa D).

---

## Archivos creados (repo backend)

```
docs/frontend/org/etapa-a/
├── types.ts
├── orgScopeErrors.ts
├── orgSessionGuards.ts
├── orgQueryKeys.ts
├── useOrgSessionScope.ts
├── useOrgSessionSync.ts
├── OrgRouteGuard.tsx
├── index.ts
├── INTEGRACION_ETAPA_A.md
└── ETAPA_A_CIERRE.md
```

**Copiar a repo FE:** `src/features/org/session/` (misma estructura).

---

## Criterios de cierre Etapa A

| Criterio | Blueprint | Verificación en FE |
|----------|-----------|-------------------|
| ORG usa `empresaActivaId` JWT/contexto | `useOrgSessionScope` | Páginas sin `empresaFilter` en `queryFn` |
| `selection_pending` = backend | `evaluateOrgRouteGuard` | Company routes → redirect selección |
| `cambiarEmpresaActiva` refresca ORG | `useOrgSessionSync` | Cambiar empresa en header → listas recargan |
| Sin contaminación filtros locales | `onEmpresaChanged` | Buscar/página reset al cambiar empresa |
| Services aún con `empresa_id` body OK | `assertBodyEmpresa` | POST create con `empresa_id` = JWT |

---

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Doble fuente empresa (filter + JWT) | `syncLegacyFilterFromSession` solo mirror; API sin filter en Etapa A |
| Olvidar `enabled: scope.canAccessCompanyScope` en useQuery | Queries no disparan con `selection_pending` |
| Interceptor global rompe otros módulos | Filtrar URL `/org/` solo |
| `useEmpresaActiva` sin `clienteId` en impersonación | Validar JWT decode igual que backend Etapa D |
| Invalidación demasiado amplia | Prefijos en `getOrgInvalidationKeyPrefixes` |

---

## Checklist manual (QA Etapa A)

### Sesión normal

- [ ] Login → seleccionar empresa → entrar `/app/org/sucursales` → listado carga sin selector local.
- [ ] Cambiar empresa en header → listado sucursales cambia; filtros búsqueda reseteados.
- [ ] Crear sucursal: body `empresa_id` = empresa JWT; sin `?empresa_id=` en URL.

### selection_pending

- [ ] Token con `empresa_selection_pending=true` → `/app/org/empresa` OK.
- [ ] Mismo token → `/app/org/sucursales` redirige a selección (o 403 si entra directo a API).

### Impersonación

- [ ] Platform impersona ACME → `clienteId` en logs DEV = ACME.
- [ ] Empresa A → datos A; cambiar a B en header → datos B.
- [ ] No aparecen empresas/registros de otro tenant en listados.

### Errores

- [ ] Forzar body `empresa_id` distinto en create → mensaje `EMPRESA_SCOPE_MISMATCH` (client o 403 API).
- [ ] Llamada ORG sin empresa en JWT → toast + redirect `MISSING_SESSION_EMPRESA`.

### Regresión

- [ ] INV sin cambios (no montar layout ORG en rutas INV).
- [ ] Otros módulos no usan interceptor ORG.

---

## Impacto cross-módulo

| Módulo | Etapa A |
|--------|---------|
| **ORG** | Integración directa (layout + 6 rutas) |
| **INV** | Sin cambios — blueprint futuro puede reutilizar `orgQueryKeys` patrón |
| **Auth** | Solo consumo `useEmpresaActiva` / cambiar empresa |
| **PUR, SLS, etc.** | No tocar |

---

## Estado de alineación (post Etapa A FE)

| Dimensión | Backend | FE (tras integrar blueprint) |
|-----------|---------|----------------------------|
| tenant-aware | ✅ | ✅ vía `clienteId` sesión |
| company-aware (API) | ✅ JWT | ✅ guards + sync; query legacy aún en services hasta B |
| impersonation-safe | ✅ | ✅ si `useEmpresaActiva` expone JWT impersonado |
| selection_pending-safe | ✅ | ✅ `OrgRouteGuard` |
| JWT-driven operativo | ✅ | ✅ Etapa A; B elimina query param |

---

## Siguiente paso

1. Abrir repo FE en workspace **o** indicar ruta (`D:\...\caxis-frontend`).
2. Copiar `docs/frontend/org/etapa-a/*` → `src/features/org/session/`.
3. Seguir `INTEGRACION_ETAPA_A.md` y marcar checklist.
4. **No iniciar Etapa B** hasta cerrar checklist manual Etapa A.

**Etapa B (preview):** remover `empresa_id` query en services; deprecar `OrgListParams.empresa_id`; `useEmpresasTenant()`.
