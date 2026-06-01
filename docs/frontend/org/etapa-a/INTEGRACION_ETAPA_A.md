# ORG FE — Etapa A: guía de integración

Stack objetivo: **React + TypeScript + Vite** (ver `contexto-refactorizacion.mdc`).

El código de referencia está en `docs/frontend/org/etapa-a/`. Copiar a:

```
src/features/org/session/
```

## 1. Conectar `useEmpresaActiva` real

En `useOrgSessionScope.ts`, reemplazar el stub:

```ts
import { useEmpresaActiva } from '@/features/auth/hooks/useEmpresaActiva'; // ruta real

export function useOrgSessionScope(options: UseOrgSessionScopeOptions) {
  const empresaActiva = useEmpresaActiva();
  // ... resto igual sin segundo argumento
}
```

Requisitos del contexto auth existente:

| Campo | Fuente |
|-------|--------|
| `clienteId` | JWT `cliente_id` o `/auth/me` (impersonación: tenant destino) |
| `empresaActivaId` | JWT `empresa_id` / `empresa_activa` |
| `empresaSelectionPending` | JWT `empresa_selection_pending` |
| `isImpersonation` | JWT `is_impersonation` |
| `cambiarEmpresaActiva` | `POST /api/v1/auth/empresa/cambiar/` |

## 2. Layout ORG (`/app/org/*`)

```tsx
// src/features/org/layout/OrgModuleLayout.tsx
import { Outlet } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useEmpresaActiva } from '@/features/auth/hooks/useEmpresaActiva';
import { useOrgSessionSync } from '@/features/org/session/useOrgSessionSync';

export function OrgModuleLayout() {
  const queryClient = useQueryClient();
  const empresaActiva = useEmpresaActiva();

  useOrgSessionSync({
    queryClient,
    empresaActiva,
    onEmpresaChanged: () => {
      // Reset filtros locales no operativos (buscar, página, etc.)
      // NO resetear empresa desde aquí — viene del JWT
    },
  });

  return <Outlet />;
}
```

Registrar en router:

```tsx
{
  path: 'org',
  element: <OrgModuleLayout />,
  children: [
    { path: 'empresa', element: <OrgRouteGuard segment="empresa" ...><EmpresaPage /></OrgRouteGuard> },
    { path: 'sucursales', element: <OrgRouteGuard segment="sucursales" ...><SucursalesPage /></OrgRouteGuard> },
    // ...
  ],
}
```

## 3. Páginas ORG — patrón Etapa A

### Company-scoped (sucursales, departamentos, cargos, centros-costo)

```tsx
const empresaActiva = useEmpresaActiva();
const { scope, guard, empresaIdForBody, syncLegacyFilterFromSession, assertBodyEmpresa } =
  useOrgSessionScope({
    routeSegment: 'sucursales',
    legacyEmpresaFilter: { value: empresaFilter, setValue: setEmpresaFilter }, // temporal
  });

useEffect(() => {
  syncLegacyFilterFromSession();
}, [syncLegacyFilterFromSession]);

// Listado: NO pasar empresaFilter a org.service — JWT define scope (Etapa B quita query)
const { data } = useQuery({
  queryKey: orgQueryKeys.sucursales(scope.clienteId, scope.empresaActivaId),
  enabled: scope.canAccessCompanyScope,
  queryFn: () => orgService.listSucursales({ solo_activos: true }), // sin empresa_id query
});

// Create (Etapa A: body sigue con empresa_id)
const onSubmit = (form) => {
  assertBodyEmpresa(form.empresa_id);
  const payload = { ...form, empresa_id: empresaIdForBody! };
  ...
};
```

### Tenant-scoped (`/org/empresa`)

```tsx
useOrgSessionScope({ routeSegment: 'empresa' });
// Permite selection_pending; listado usa clienteId de sesión
```

### Hybrid (`/org/parametros`)

Igual que company-scoped en guard; lógica UI global/override es Etapa D.

## 4. Interceptor API (errores scope)

En el cliente axios del ERP (`/app/*`):

```ts
import { handleOrgScopeApiError } from '@/features/org/session/orgScopeErrors';

api.interceptors.response.use(
  (r) => r,
  (error) => {
    const url = error.config?.url ?? '';
    if (url.includes('/org/')) {
      handleOrgScopeApiError(error, {
        notify: toast.error,
        onMissingEmpresa: () => navigate('/app/seleccion-empresa'),
      });
    }
    return Promise.reject(error);
  },
);
```

## 5. Eliminar dependencia operativa de `empresaFilter`

| Antes (legacy) | Etapa A |
|----------------|---------|
| `listX({ empresa_id: empresaFilter })` | `listX({ solo_activos })` — empresa en JWT |
| Selector empresa en página ORG | Solo badge + cambio en header global |
| `empresaFilter` como fuente de verdad | Solo mirror opcional vía `syncLegacyFilterFromSession` |

**No eliminar** aún `empresa_id` en body de POST (backend Etapa B FE).

## 6. `cambiarEmpresaActiva` (header global)

Tras éxito de `POST /auth/empresa/cambiar/`:

1. Actualizar tokens en auth store.
2. `useOrgSessionSync` invalidará queries ORG automáticamente si el layout está montado.
3. Si la página tenía filtros locales, `onEmpresaChanged` los resetea.

## 7. Impersonación

- `clienteId` del JWT impersonado (ACME), no del usuario platform en memoria.
- Con `selection_pending`: solo rutas `segment="empresa"` montadas; resto → guard redirige.
- Tras `POST /auth/impersonate/.../empresa/seleccionar` equivalente: mismo flujo que cambiar empresa.

## 8. Archivos del proyecto FE a tocar (checklist integración)

- [ ] `src/features/org/session/*` (copiar blueprint)
- [ ] `src/features/org/layout/OrgModuleLayout.tsx` (nuevo o extender)
- [ ] Router `/app/org/*`
- [ ] Páginas: Sucursales, Departamentos, Cargos, CentrosCosto, Parametros, Empresa
- [ ] Interceptor axios ERP
- [ ] **No tocar** INV ni otros módulos en Etapa A
