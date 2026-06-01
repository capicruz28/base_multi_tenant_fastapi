/**
 * ORG FE — Etapa A: sync empresa JWT → páginas ORG + invalidación React Query.
 * Copiar a: src/features/org/session/useOrgSessionSync.ts
 */
import { useEffect, useRef } from 'react';
import type { QueryClient } from '@tanstack/react-query';
import type { EmpresaActivaContextValue } from './useOrgSessionScope';
import { getOrgInvalidationKeyPrefixes } from './orgQueryKeys';

export interface UseOrgSessionSyncOptions {
  queryClient: QueryClient;
  empresaActiva: EmpresaActivaContextValue;
  /** Reset de filtros locales (buscar, solo_activos, etc.) — no empresa operativa. */
  onEmpresaChanged?: (prevEmpresaId: string | null, nextEmpresaId: string | null) => void;
  /** Rutas bajo /app/org/* que montan este hook (layout ORG recomendado). */
  enabled?: boolean;
}

/**
 * Montar en layout ORG (`/app/org/*`) o en cada página durante migración gradual.
 *
 * - Al cambiar empresaActivaId: invalida caches ORG segmentados.
 * - Invoca onEmpresaChanged para limpiar estado UI local (evita contaminación cross-company).
 */
export function useOrgSessionSync({
  queryClient,
  empresaActiva,
  onEmpresaChanged,
  enabled = true,
}: UseOrgSessionSyncOptions): void {
  const prevEmpresaRef = useRef<string | null>(empresaActiva.empresaActivaId);

  useEffect(() => {
    if (!enabled) return;

    const prev = prevEmpresaRef.current;
    const next = empresaActiva.empresaActivaId;

    if (prev === next) return;

    prevEmpresaRef.current = next;

    onEmpresaChanged?.(prev, next);

    const prefixes = getOrgInvalidationKeyPrefixes({
      clienteId: empresaActiva.clienteId,
      empresaActivaId: next,
      tenantOnly: !next,
    });

    for (const prefix of prefixes) {
      void queryClient.invalidateQueries({ queryKey: prefix });
    }

    if (import.meta.env.DEV) {
      console.info('[ORG-FE-SESSION-SYNC] empresa_changed', {
        prev,
        next,
        clienteId: empresaActiva.clienteId,
        invalidated: prefixes.length,
      });
    }
  }, [
    enabled,
    empresaActiva.empresaActivaId,
    empresaActiva.clienteId,
    onEmpresaChanged,
    queryClient,
  ]);
}
