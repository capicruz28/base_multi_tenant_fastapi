/**
 * ORG FE — Etapa A: hook principal de sesión JWT-driven para módulo ORG.
 * Copiar a: src/features/org/session/useOrgSessionScope.ts
 *
 * INTEGRACIÓN: adaptar imports de useEmpresaActiva / useAuth al proyecto real.
 */
import { useMemo } from 'react';
import type { OrgRouteSegment, OrgSessionScopeState } from './types';
import {
  buildOrgSessionScope,
  evaluateOrgRouteGuard,
  assertBodyEmpresaMatchesSession,
} from './orgSessionGuards';

/**
 * Contrato mínimo esperado de useEmpresaActiva (existente en el proyecto FE).
 * Reemplazar por import real: `@/features/auth/hooks/useEmpresaActiva`
 */
export interface EmpresaActivaContextValue {
  empresaActivaId: string | null;
  clienteId: string | null;
  empresaSelectionPending: boolean;
  isImpersonation: boolean;
  /** POST /auth/empresa/cambiar — debe refrescar token y disparar invalidación ORG. */
  cambiarEmpresaActiva: (empresaId: string) => Promise<void>;
}

/**
 * Stub: sustituir por el hook real del proyecto.
 * Ejemplo de wiring en INTEGRACION_ETAPA_A.md
 */
export function useEmpresaActivaStub(): EmpresaActivaContextValue {
  throw new Error(
    'useOrgSessionScope: conectar useEmpresaActiva real del proyecto FE (ver INTEGRACION_ETAPA_A.md)',
  );
}

export interface UseOrgSessionScopeOptions {
  routeSegment: OrgRouteSegment;
  /**
   * Etapa A: si la página aún mantiene empresaFilter local, pasar setter para
   * sincronizar desde JWT y dejar de usarlo como fuente operativa de API.
   */
  legacyEmpresaFilter?: {
    value: string | null;
    setValue: (id: string | null) => void;
  };
}

export interface UseOrgSessionScopeResult {
  scope: OrgSessionScopeState;
  guard: ReturnType<typeof evaluateOrgRouteGuard>;
  /** ID de empresa para payloads Create (Etapa A: body sigue requerido). */
  empresaIdForBody: string | null;
  /** Sincroniza legacy filter → JWT (no usar filter para llamadas API). */
  syncLegacyFilterFromSession: () => void;
  assertBodyEmpresa: (bodyEmpresaId: string | null | undefined) => void;
}

export function useOrgSessionScope(
  options: UseOrgSessionScopeOptions,
  empresaActiva: EmpresaActivaContextValue = useEmpresaActivaStub(),
): UseOrgSessionScopeResult {
  const {
    empresaActivaId,
    clienteId,
    empresaSelectionPending,
    isImpersonation,
  } = empresaActiva;

  const scope = useMemo(
    () =>
      buildOrgSessionScope({
        clienteId,
        empresaActivaId,
        empresaSelectionPending,
        isImpersonation,
        routeSegment: options.routeSegment,
      }),
    [
      clienteId,
      empresaActivaId,
      empresaSelectionPending,
      isImpersonation,
      options.routeSegment,
    ],
  );

  const guard = useMemo(() => evaluateOrgRouteGuard(scope), [scope]);

  const syncLegacyFilterFromSession = () => {
    if (!options.legacyEmpresaFilter) return;
    const { value, setValue } = options.legacyEmpresaFilter;
    if (value !== empresaActivaId) {
      setValue(empresaActivaId);
    }
  };

  const assertBodyEmpresa = (bodyEmpresaId: string | null | undefined) => {
    assertBodyEmpresaMatchesSession(bodyEmpresaId ?? empresaActivaId, empresaActivaId);
  };

  return {
    scope,
    guard,
    empresaIdForBody: empresaActivaId,
    syncLegacyFilterFromSession,
    assertBodyEmpresa,
  };
}
