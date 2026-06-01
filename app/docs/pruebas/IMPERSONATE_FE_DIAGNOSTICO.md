# Diagnóstico FE — POST /auth/impersonate/{cliente_id}/

El backend de este repo no incluye el frontend. Aplicar estos logs **temporales** en el proyecto Angular/React.

## auth.service.ts (método impersonate)

```typescript
const token = this.authStore.getAccessToken(); // o el getter que usen
console.log('[IMPERSONATE-FE] token present', !!token);
console.log('[IMPERSONATE-FE] token length', token?.length ?? 0);
console.log('[IMPERSONATE-FE] target cliente_id', clienteId);
// justo antes del POST:
console.log('[IMPERSONATE-FE] url', urlCompleta);
```

## Interceptor Axios (solo si URL contiene `/auth/impersonate`)

```typescript
if (config.url?.includes('/auth/impersonate')) {
  const token = /* mismo origen que /me */;
  console.log('[IMPERSONATE-FE] token present', !!token);
  console.log('[IMPERSONATE-FE] auth header', config.headers?.Authorization ?? config.headers?.authorization);
  console.log('[IMPERSONATE-FE] url', config.url);
  console.log('[IMPERSONATE-FE] baseURL', config.baseURL);
}
```

## Checklist

| Verificación | Esperado |
|--------------|----------|
| `token present` | `true` (mismo token que funciona en GET `/auth/me/`) |
| `auth header` | `Bearer eyJ...` (tres segmentos) |
| URL | `.../api/v1/auth/impersonate/{uuid}/` |
| Instancia HTTP | Misma que `/auth/me` (`api` / `apiCentral`), no cliente sin interceptor |
| Exclusión interceptor | `/auth/impersonate` **no** debe estar en lista de URLs sin Bearer |

Si `token present` es `false` o no hay `Authorization` → causa **A** (frontend).

Si FE envía Bearer y backend log `authorization_present=False` → causa **B/C** (proxy/CORS/preflight).
