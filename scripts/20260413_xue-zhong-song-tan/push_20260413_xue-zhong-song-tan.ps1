$repo = "$HOME\github\snowys-chinese-house"
$slug = "20260413_xue-zhong-song-tan"
$episode = 20

Set-Location $repo
git add "scripts/$slug"
git commit -m "ep${episode}: add 雪中送炭 (xuě zhōng sòng tàn) script"
git push
Write-Host "Pushed to GitHub!"
