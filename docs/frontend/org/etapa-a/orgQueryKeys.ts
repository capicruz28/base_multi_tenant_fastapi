/**
 * ORG FE — Etapa A: claves e invalidación React Query por scope de sesión.
 * Copiar a: src/features/org/session/orgQueryKeys.ts
 *
 * Etapa B eliminará empresa_id de params; Etapa A invalida por empresaActivaId.
 */

export const orgQueryKeys = {
  all: ['org'] as const,
  tenant: (clienteId: string | null) =>
    [...orgQueryKeys.all, 'tenant', clienteId] as const,
  empresa: (clienteId: string | null) =>
    [...orgQueryKeys.tenant(clienteId), 'empresa'] as const,
  company: (
    resource: string,
    clienteId: string | null,
    empresaId: string | null,
  ) => [...orgQueryKeys.all, resource, clienteId, empresaId] as const,
  sucursales: (clienteId: string | null, empresaId: string | null) =>
    orgQueryKeys.company('sucursales', clienteId, empresaId),
  departamentos: (clienteId: string | null, empresaId: string | null) =>
    orgQueryKeys.company('departamentos', clienteId, empresaId),
  cargos: (clienteId: string | null, empresaId: string | null) =>
    orgQueryKeys.company('cargos', clienteId, empresaId),
  centrosCosto: (clienteId: string | null, empresaId: string | null) =>
    orgQueryKeys.company('centros-costo', clienteId, empresaId),
  parametros: (clienteId: string | null, empresaId: string | null) =>
    orgQueryKeys.company('parametros', clienteId, empresaId),
};

export type OrgQueryInvalidationScope = {
  clienteId: string | null;
  empresaActivaId: string | null;
  /** Si true, solo tenant (/org/empresa). */
  tenantOnly?: boolean;
};

/**
 * Invalidación segmentada al cambiar empresa JWT o tras cambiarEmpresaActiva.
 */
export function getOrgInvalidationKeyPrefixes(
  scope: OrgQueryInvalidationScope,
): readonly (readonly string[])[] {
  const { clienteId, empresaActivaId, tenantOnly } = scope;
  const keys: (readonly string[])[] = [
    orgQueryKeys.empresa(clienteId),
  ];
  if (tenantOnly || !empresaActivaId) {
    return keys;
  }
  keys.push(
    orgQueryKeys.sucursales(clienteId, empresaActivaId),
    orgQueryKeys.departamentos(clienteId, empresaActivaId),
    orgQueryKeys.cargos(clienteId, empresaActivaId),
    orgQueryKeys.centrosCosto(clienteId, empresaActivaId),
    orgQueryKeys.parametros(clienteId, empresaActivaId),
  );
  return keys;
}
