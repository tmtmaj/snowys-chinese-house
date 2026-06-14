# push_20260602_zhen-er-yu-long.ps1
# EP26 震耳欲聋 — GitHub 자동 push 스크립트 (Windows 백업용)

$candidates = @(
    "$HOME\Documents\github\snowys-chinese-house",
    "$HOME\github\snowys-chinese-house",
    "$HOME\Documents\snowys-chinese-house",
    "$HOME\Desktop\snowys-chinese-house"
)
$repo = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $repo) {
    Write-Error "snowys-chinese-house repo not found. Please clone it first."
    exit 1
}

$slug    = "20260602_zhen-er-yu-long"
$episode = 26
$idiom   = "震耳欲聋"

Write-Host "📁 Repo: $repo"
Write-Host "📝 Copying files..."

$srcDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$destDir = "$repo\scripts\$slug"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null

Copy-Item "$srcDir\$slug\$slug.md"            "$destDir\" -Force
Copy-Item "$srcDir\$slug\$slug.html"          "$destDir\" -Force
Copy-Item "$srcDir\$slug\README.md"           "$destDir\" -Force
Copy-Item "$srcDir\$slug\${slug}_script.docx" "$destDir\" -Force -ErrorAction SilentlyContinue

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add $idiom (zhen-er-yu-long) script"
git push
Write-Host "✅ ep${episode} $idiom pushed to GitHub!"
