/**
 * ORG FE — Etapa A: manejo centralizado de errores de scope (axios/fetch).
 * Copiar a: src/features/org/session/orgScopeErrors.ts
 */

import type { AxiosError } from 'axios';

export const ORG_SCOPE_ERROR_CODES = {
  MISSING_SESSION_EMPRESA: 'MISSING_SESSION_EMPRESA',
  EMPRESA_SCOPE_MISMATCH: 'EMPRESA_SCOPE_MISMATCH',
  TENANT_SCOPE_MISMATCH: 'TENANT_SCOPE_MISMATCH',
  GLOBAL_PARAM_FORBIDDEN: 'GLOBAL_PARAM_FORBIDDEN',
} as const;

export type OrgScopeErrorCode =
  (typeof ORG_SCOPE_ERROR_CODES)[keyof typeof ORG_SCOPE_ERROR_CODES];

export interface ApiErrorBody {
  detail?: string | { msg?: string; internal_code?: string }[];
  internal_code?: string;
}

function extractInternalCode(data: unknown): string | undefined {
  if (!data || typeof data !== 'object') return undefined;
  const body = data as ApiErrorBody;
  if (typeof body.internal_code === 'string') return body.internal_code;
  if (Array.isArray(body.detail)) {
    for (const item of body.detail) {
      if (item && typeof item === 'object' && 'internal_code' in item) {
        const code = (item as { internal_code?: string }).internal_code;
        if (code) return code;
      }
    }
  }
  return undefined;
}

export function getOrgScopeErrorCode(error: unknown): OrgScopeErrorCode | undefined {
  const axiosErr = error as AxiosError<ApiErrorBody>;
  const status = axiosErr?.response?.status;
  const code = extractInternalCode(axiosErr?.response?.data);
  if (status === 403 && code && code in ORG_SCOPE_ERROR_CODES) {
    return code as OrgScopeErrorCode;
  }
  return undefined;
}

export function isMissingSessionEmpresaError(error: unknown): boolean {
  return (
    getOrgScopeErrorCode(error) === ORG_SCOPE_ERROR_CODES.MISSING_SESSION_EMPRESA
  );
}

export function isEmpresaScopeMismatchError(error: unknown): boolean {
  return (
    getOrgScopeErrorCode(error) === ORG_SCOPE_ERROR_CODES.EMPRESA_SCOPE_MISMATCH
  );
}

/** Mensaje UX en español (Etapa A: sin cambiar pantallas; toast central). */
export function orgScopeErrorMessage(code: OrgScopeErrorCode | undefined): string {
  switch (code) {
    case ORG_SCOPE_ERROR_CODES.MISSING_SESSION_EMPRESA:
      return 'Seleccione una empresa activa antes de continuar en Organización.';
    case ORG_SCOPE_ERROR_CODES.EMPRESA_SCOPE_MISMATCH:
      return 'La empresa enviada no coincide con la sesión activa.';
    case ORG_SCOPE_ERROR_CODES.TENANT_SCOPE_MISMATCH:
      return 'El tenant de la solicitud no coincide con su sesión.';
    case ORG_SCOPE_ERROR_CODES.GLOBAL_PARAM_FORBIDDEN:
      return 'Solo un administrador del tenant puede gestionar parámetros globales.';
    default:
      return 'No tiene permisos o el ámbito de la sesión no es válido.';
  }
}

/**
 * Handler central para interceptores API (solo módulo ORG en Etapa A).
 * Retorna true si el error fue consumido (evitar toast duplicado).
 */
export function handleOrgScopeApiError(
  error: unknown,
  options?: {
    onMissingEmpresa?: () => void;
    onScopeMismatch?: () => void;
    notify?: (message: string) => void;
  },
): boolean {
  const code = getOrgScopeErrorCode(error);
  if (!code) return false;

  const message = orgScopeErrorMessage(code);
  options?.notify?.(message);

  if (code === ORG_SCOPE_ERROR_CODES.MISSING_SESSION_EMPRESA) {
    options?.onMissingEmpresa?.();
    return true;
  }
  if (code === ORG_SCOPE_ERROR_CODES.EMPRESA_SCOPE_MISMATCH) {
    options?.onScopeMismatch?.();
    return true;
  }
  return true;
}
