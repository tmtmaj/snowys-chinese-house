$repo = "$HOME\github\snowys-chinese-house"
$slug = "20260413_hua-she-tian-zu"
$episode = 22

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add 画蛇添足 (huà shé tiān zú) script"
git push
Write-Host "Pushed to GitHub!"
