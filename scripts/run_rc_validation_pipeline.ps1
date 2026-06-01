# Wrapper PowerShell — pipeline RC
param(
    [switch]$UnitOnly,
    [switch]$HttpSmoke,
    [switch]$FullStaging,
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Subdominio,
    [string]$Username = "admin",
    [string]$Password,
    [switch]$CreateTenant
)

$argsList = @()
if ($UnitOnly) { $argsList += "--unit-only" }
if ($HttpSmoke) { $argsList += "--http-smoke" }
if ($FullStaging) { $argsList += "--full-staging" }
$argsList += @("--base-url", $BaseUrl)
if ($Subdominio) { $argsList += @("--subdominio", $Subdominio) }
if ($Username) { $argsList += @("--username", $Username) }
if ($Password) { $argsList += @("--password", $Password) }
if ($CreateTenant) { $argsList += "--create-tenant" }

$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    python scripts/run_rc_validation_pipeline.py @argsList
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
