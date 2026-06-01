# Aplica schema + catálogo bootstrap_v2 (Fase A staging). No ejecuta R010/R020 ni S040-S066.
param(
    [string]$Server = "localhost",
    [string]$Database = "bd_sistema",
    [string]$User = "sa",
    [string]$Password = "",
    [string]$BootstrapRoot = (Join-Path $PSScriptRoot "..\app\bootstrap_v2")
)

$ErrorActionPreference = "Stop"
$sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (-not $sqlcmd) {
    Write-Error "sqlcmd no encontrado. Instale SQL Server tools o ejecute los .sql manualmente (STAGING_VALIDATION_PIPELINE.md)."
}

$files = @(
    "01_schema\V010__tablas_bd_erp_completo.sql",
    "01_schema\V020__tablas_bd_central.sql",
    "01_schema\V030__rbac_tablas_central.sql",
    "02_catalog\S010__seed_modulo_menu_completo.sql",
    "02_catalog\S020__seed_admin_menu.sql",
    "02_catalog\S030__seed_permisos_core.sql"
)

foreach ($rel in $files) {
    $path = Join-Path $BootstrapRoot $rel
    if (-not (Test-Path $path)) { throw "No existe: $path" }
    Write-Host ">> $rel"
    & sqlcmd -S $Server -d $Database -U $User -P $Password -C -I -i $path -b
    if ($LASTEXITCODE -ne 0) { throw "Fallo en $rel" }
}
Write-Host "OK bootstrap_v2 Fase A (schema + catalogo S010-S030)"
