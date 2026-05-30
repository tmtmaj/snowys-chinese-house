# push_20260528_qing-miao-dan-xie.ps1
# EP25 轻描淡写 — GitHub 자동 push 스크립트 (Windows 백업용)

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

$slug = "20260528_qing-miao-dan-xie"
$episode = 25
$idiom = "轻描淡写"

Write-Host "📁 Repo: $repo"
Write-Host "📝 Copying files..."

$srcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$destDir = "$repo\scripts\$slug"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null

Copy-Item "$srcDir\$slug\$slug.md"            "$destDir\" -Force
Copy-Item "$srcDir\$slug\$slug.html"          "$destDir\" -Force
Copy-Item "$srcDir\$slug\README.md"           "$destDir\" -Force
Copy-Item "$srcDir\$slug\${slug}_script.docx" "$destDir\" -Force -ErrorAction SilentlyContinue

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add $idiom (qing-miao-dan-xie) script"
git push
Write-Host "✅ ep${episode} $idiom pushed to GitHub!"
