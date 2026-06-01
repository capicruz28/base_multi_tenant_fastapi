/**
 * ORG FE — Etapa A: guard de ruta (company / hybrid vs tenant).
 * Copiar a: src/features/org/session/OrgRouteGuard.tsx
 */
import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import type { OrgRouteSegment } from './types';
import { useOrgSessionScope } from './useOrgSessionScope';
import type { EmpresaActivaContextValue } from './useOrgSessionScope';

export interface OrgRouteGuardProps {
  segment: OrgRouteSegment;
  children: ReactNode;
  /** Inyectar contexto real de useEmpresaActiva desde layout padre. */
  empresaActiva: EmpresaActivaContextValue;
  /** Pantalla mientras redirige (opcional). */
  fallback?: ReactNode;
}

export function OrgRouteGuard({
  segment,
  children,
  empresaActiva,
  fallback = null,
}: OrgRouteGuardProps) {
  const { guard } = useOrgSessionScope({ routeSegment: segment }, empresaActiva);

  if (!guard.allowed) {
    if (guard.redirectTo) {
      return <Navigate to={guard.redirectTo} replace />;
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
