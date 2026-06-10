#Requires -RunAsAdministrator
param(
    [string]$RedisHost     = "10.10.191.15",
    [string]$RedisPassword = "changeme",
    [string]$Zone          = "ZoneB",
    [string]$Version       = "8.17.4"
)

$ErrorActionPreference = "Stop"
$InstallDir = "C:\Program Files\Winlogbeat"

Write-Host "==> Winlogbeat $Version 설치 시작 ($Zone)" -ForegroundColor Cyan

# 다운로드
$ZipUrl  = "https://artifacts.elastic.co/downloads/beats/winlogbeat/winlogbeat-$Version-windows-x86_64.zip"
$ZipPath = "$env:TEMP\winlogbeat.zip"

Write-Host "다운로드 중..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath -UseBasicParsing

# 압축 해제 및 설치
Expand-Archive -Path $ZipPath -DestinationPath $env:TEMP -Force
$ExtractedDir = "$env:TEMP\winlogbeat-$Version-windows-x86_64"

if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
Move-Item $ExtractedDir $InstallDir

# 설정 파일 복사 및 환경변수 치환
$ConfigSrc = Join-Path $PSScriptRoot "winlogbeat.yml"
$ConfigDst = "$InstallDir\winlogbeat.yml"
Copy-Item $ConfigSrc $ConfigDst

(Get-Content $ConfigDst) `
    -replace '\$\{REDIS_HOST:10\.10\.191\.15\}', $RedisHost `
    -replace '\$\{REDIS_PASSWORD\}',              $RedisPassword `
    -replace '"ZoneB"',                           "`"$Zone`"" |
  Set-Content $ConfigDst

# 설정 유효성 검사
& "$InstallDir\winlogbeat.exe" test config -c $ConfigDst
if ($LASTEXITCODE -ne 0) { throw "설정 파일 오류" }

# 서비스 등록 및 시작
& "$InstallDir\install-service-winlogbeat.ps1"
Start-Service winlogbeat
Set-Service  winlogbeat -StartupType Automatic

Write-Host "==> Winlogbeat 설치 완료" -ForegroundColor Green
Get-Service winlogbeat | Select-Object Name, Status, StartType
