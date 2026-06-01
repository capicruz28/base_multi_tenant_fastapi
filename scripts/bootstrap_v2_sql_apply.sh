#!/usr/bin/env bash
# Aplica schema + catálogo bootstrap_v2 (Fase A). No R010/R020 ni S040-S066.
set -euo pipefail
SERVER="${1:-localhost}"
DATABASE="${2:-bd_sistema}"
USER="${3:-sa}"
PASSWORD="${4:-}"
ROOT="$(cd "$(dirname "$0")/../app/bootstrap_v2" && pwd)"

if ! command -v sqlcmd >/dev/null 2>&1; then
  echo "sqlcmd no encontrado. Ver STAGING_VALIDATION_PIPELINE.md" >&2
  exit 1
fi

FILES=(
  "01_schema/V010__tablas_bd_erp_completo.sql"
  "01_schema/V020__tablas_bd_central.sql"
  "01_schema/V030__rbac_tablas_central.sql"
  "02_catalog/S010__seed_modulo_menu_completo.sql"
  "02_catalog/S020__seed_admin_menu.sql"
  "02_catalog/S030__seed_permisos_core.sql"
)

for rel in "${FILES[@]}"; do
  path="$ROOT/$rel"
  echo ">> $rel"
  sqlcmd -S "$SERVER" -d "$DATABASE" -U "$USER" -P "$PASSWORD" -C -I -i "$path" -b
done
echo "OK bootstrap_v2 Fase A"
