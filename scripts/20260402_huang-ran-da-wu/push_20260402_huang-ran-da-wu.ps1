$repo = "$HOME\github\snowys-chinese-house"
$slug = "20260402_huang-ran-da-wu"
$episode = 19

Set-Location $repo
git add "scripts/$slug/"
git commit -m "ep${episode}: add 恍然大悟 (huǎng rán dà wù) script"
git push
Write-Host "Pushed to GitHub!"
