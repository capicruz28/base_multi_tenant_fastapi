/**
 * ORG FE — Etapa A: guards puros (sin React).
 * Alineado a backend: session_scope.py + org_deps.py
 */
import type {
  OrgRouteSegment,
  OrgScopeGuardResult,
  OrgScopeKind,
  OrgSessionScopeState,
} from './types';

export function resolveOrgScopeKind(segment: OrgRouteSegment): OrgScopeKind {
  if (segment === 'empresa') return 'tenant';
  if (segment === 'parametros') return 'hybrid';
  return 'company';
}

export function buildOrgSessionScope(input: {
  clienteId: string | null;
  empresaActivaId: string | null;
  empresaSelectionPending: boolean;
  isImpersonation: boolean;
  routeSegment: OrgRouteSegment;
}): OrgSessionScopeState {
  const scopeKind = resolveOrgScopeKind(input.routeSegment);
  const selectionPending = input.empresaSelectionPending;

  const canAccessTenantScope = scopeKind === 'tenant';
  const canAccessCompanyScope =
    (scopeKind === 'company' || scopeKind === 'hybrid') &&
    !selectionPending &&
    Boolean(input.empresaActivaId);

  return {
    clienteId: input.clienteId,
    empresaActivaId: input.empresaActivaId,
    empresaSelectionPending: selectionPending,
    isImpersonation: input.isImpersonation,
    scopeKind,
    canAccessTenantScope,
    canAccessCompanyScope,
  };
}

/** Guard de navegación / render condicional por página ORG. */
export function evaluateOrgRouteGuard(
  scope: OrgSessionScopeState,
): OrgScopeGuardResult {
  if (scope.scopeKind === 'tenant') {
    return { allowed: true };
  }

  if (scope.empresaSelectionPending) {
    return {
      allowed: false,
      redirectTo: '/app/seleccion-empresa',
      reason: 'SELECTION_PENDING',
    };
  }

  if (!scope.empresaActivaId) {
    return {
      allowed: false,
      redirectTo: '/app/seleccion-empresa',
      reason: 'MISSING_SESSION_EMPRESA',
    };
  }

  return { allowed: true };
}

/** Etapa A: body create/update — empresa debe coincidir con JWT (services aún envían body). */
export function assertBodyEmpresaMatchesSession(
  bodyEmpresaId: string | null | undefined,
  sessionEmpresaId: string | null,
): void {
  if (!sessionEmpresaId) {
    throw new Error('MISSING_SESSION_EMPRESA');
  }
  if (bodyEmpresaId && bodyEmpresaId !== sessionEmpresaId) {
    throw new Error('EMPRESA_SCOPE_MISMATCH');
  }
}
