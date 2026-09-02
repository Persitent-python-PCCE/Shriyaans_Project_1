$ErrorActionPreference = "Stop"

$Namespace = "it-service-desk"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$InitSql = Join-Path $PSScriptRoot "init.sql"
$K8sDir = Join-Path $PSScriptRoot "k8s"

function Get-DotEnvValue([string]$Path, [string]$Name) {
    if (-not (Test-Path $Path)) { return $null }
    foreach ($line in Get-Content $Path) {
        if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.*)\s*$") {
            $value = $Matches[1]
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            return $value
        }
    }
    return $null
}

if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    throw "kubectl is not installed or is not in PATH."
}

kubectl config use-context docker-desktop
kubectl get nodes

if (-not (Test-Path $EnvFile)) {
    throw "Could not find .env at $EnvFile"
}
if (-not (Test-Path $InitSql)) {
    throw "Could not find init.sql at $InitSql"
}

$dbUser = Get-DotEnvValue $EnvFile "DB_USER"
$dbPassword = Get-DotEnvValue $EnvFile "DB_PASSWORD"
$dbName = Get-DotEnvValue $EnvFile "DB_NAME"
$secretKey = Get-DotEnvValue $EnvFile "SECRET_KEY"
$jwtSecretKey = Get-DotEnvValue $EnvFile "JWT_SECRET_KEY"
$jwtExpires = Get-DotEnvValue $EnvFile "JWT_EXPIRES_MINUTES"

if ([string]::IsNullOrWhiteSpace($dbUser) -or [string]::IsNullOrWhiteSpace($dbPassword) -or [string]::IsNullOrWhiteSpace($dbName)) {
    throw ".env must contain DB_USER, DB_PASSWORD and DB_NAME."
}
if ([string]::IsNullOrWhiteSpace($secretKey) -or [string]::IsNullOrWhiteSpace($jwtSecretKey)) {
    throw ".env must contain SECRET_KEY and JWT_SECRET_KEY."
}
if ([string]::IsNullOrWhiteSpace($jwtExpires)) { $jwtExpires = "15" }

$mysqlRootPassword = $env:MYSQL_ROOT_PASSWORD
if ([string]::IsNullOrWhiteSpace($mysqlRootPassword)) {
    $secureRoot = Read-Host "Enter the MySQL root password to use for Kubernetes" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureRoot)
    try {
        $mysqlRootPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}
if ([string]::IsNullOrWhiteSpace($mysqlRootPassword)) {
    throw "MYSQL_ROOT_PASSWORD cannot be empty."
}

kubectl apply -f (Join-Path $K8sDir "namespace.yaml")

kubectl create secret generic app-secrets `
    -n $Namespace `
    --from-literal=MYSQL_ROOT_PASSWORD=$mysqlRootPassword `
    --from-literal=DB_USER=$dbUser `
    --from-literal=DB_PASSWORD=$dbPassword `
    --from-literal=DB_NAME=$dbName `
    --from-literal=SECRET_KEY=$secretKey `
    --from-literal=JWT_SECRET_KEY=$jwtSecretKey `
    --from-literal=JWT_EXPIRES_MINUTES=$jwtExpires `
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap mysql-init `
    -n $Namespace `
    --from-file=init.sql=$InitSql `
    --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f (Join-Path $K8sDir "mysql-pvc.yaml")
kubectl apply -f (Join-Path $K8sDir "mysql-deployment.yaml")
kubectl apply -f (Join-Path $K8sDir "mysql-service.yaml")

kubectl apply -f (Join-Path $K8sDir "ollama-pvc.yaml")
kubectl apply -f (Join-Path $K8sDir "ollama-deployment.yaml")
kubectl apply -f (Join-Path $K8sDir "ollama-service.yaml")

kubectl apply -f (Join-Path $K8sDir "flask-upload-pvc.yaml")
kubectl apply -f (Join-Path $K8sDir "flask-deployment.yaml")
kubectl apply -f (Join-Path $K8sDir "flask-service.yaml")

Write-Host ""
Write-Host "Waiting for MySQL..."
kubectl rollout status deployment/mysql-deployment -n $Namespace --timeout=180s
Write-Host "Waiting for Ollama..."
kubectl rollout status deployment/ollama-deployment -n $Namespace --timeout=180s
Write-Host "Waiting for Flask..."
kubectl rollout status deployment/flask-deployment -n $Namespace --timeout=180s

Write-Host ""
Write-Host "Pods:"
kubectl get pods -n $Namespace -o wide
Write-Host ""
Write-Host "Services:"
kubectl get svc -n $Namespace
Write-Host ""
Write-Host "Flask: http://localhost:30007"
Write-Host "Ollama (inside cluster): http://ollama-service:11434"
Write-Host "MySQL (inside cluster): mysql-service:3306"
