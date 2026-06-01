/**
 * ORG FE — Etapa A: tipos de sesión multiempresa (JWT-driven).
 * Copiar a: src/features/org/session/types.ts
 */

export type OrgScopeKind = 'tenant' | 'company' | 'hybrid';

/** Segmentos bajo /app/org/ usados para política de scope. */
export type OrgRouteSegment =
  | 'empresa'
  | 'sucursales'
  | 'departamentos'
  | 'cargos'
  | 'centros-costo'
  | 'parametros';

export interface JwtSessionClaims {
  cliente_id?: string | null;
  empresa_id?: string | null;
  empresa_selection_pending?: boolean;
  is_impersonation?: boolean;
  effective_scope?: string | null;
  user_type?: string | null;
  access_level?: number | null;
}

export interface OrgSessionScopeState {
  /** Tenant operativo (JWT impersonado > auth context). */
  clienteId: string | null;
  /** Empresa activa en sesión ERP (JWT / empresa_activa de /me). */
  empresaActivaId: string | null;
  empresaSelectionPending: boolean;
  isImpersonation: boolean;
  scopeKind: OrgScopeKind;
  /** True si la ruta company/hybrid puede cargar datos ERP. */
  canAccessCompanyScope: boolean;
  /** True si la ruta tenant (/org/empresa) puede cargar sin empresa. */
  canAccessTenantScope: boolean;
}

export interface OrgScopeGuardResult {
  allowed: boolean;
  redirectTo?: '/app/seleccion-empresa' | '/app/org/empresa';
  reason?: 'MISSING_SESSION_EMPRESA' | 'SELECTION_PENDING';
}
