# Push ep28 眼花缭乱 to GitHub
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
$slug    = "20260612_yan-hua-liao-luan"
$episode = 28
$idiom   = "眼花缭乱"

$destDir = "$repo\scripts\$slug"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$srcDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item "$srcDir\$slug\$slug.md"            "$destDir\" -Force
Copy-Item "$srcDir\$slug\$slug.html"          "$destDir\" -Force
Copy-Item "$srcDir\$slug\README.md"           "$destDir\" -Force
Copy-Item "$srcDir\$slug\${slug}_script.docx" "$destDir\" -Force -ErrorAction SilentlyContinue

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add $idiom (yan hua liao luan) script"
git push
Write-Host "ep${episode} $idiom pushed to GitHub!"
