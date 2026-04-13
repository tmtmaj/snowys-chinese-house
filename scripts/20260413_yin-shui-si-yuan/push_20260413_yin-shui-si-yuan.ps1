$repo = "$HOME\github\snowys-chinese-house"
$slug = "20260413_yin-shui-si-yuan"
$episode = 21

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add 饮水思源 (yǐn shuǐ sī yuán) script"
git push
Write-Host "Pushed to GitHub!"
