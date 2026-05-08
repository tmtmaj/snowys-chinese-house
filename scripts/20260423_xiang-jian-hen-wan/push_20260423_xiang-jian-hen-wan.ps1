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

$slug = "20260423_xiang-jian-hen-wan"
$episode = 20

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add 相见恨晚 (xiāng jiàn hèn wǎn) script"
git push
Write-Host "Pushed ep$episode to GitHub!"
