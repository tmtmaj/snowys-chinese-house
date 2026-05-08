# Auto-detect repo location (works across different machines)
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
$slug = "20260501_qing-mei-zhu-ma"
$episode = 23

$dest = "$repo\scripts\$slug"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$slug.md"   "$dest\" -Force
Copy-Item "$slug.html" "$dest\" -Force
Copy-Item "README.md"  "$dest\" -Force

Set-Location $repo
git add .
git commit -m "ep${episode}: add 青梅竹马 (qīng méi zhú mǎ) script"
git push
Write-Host "✅ Pushed to GitHub!"
