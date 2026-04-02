$repo = "$HOME\github\snowys-chinese-house"
$slug = "20260402_yi-zhen-jian-xue"
$episode = 18

Set-Location $repo
git add "scripts/$slug/"
git commit -m "ep${episode}: add 一针见血 (yī zhēn jiàn xuè) script"
git push
Write-Host "Pushed to GitHub!"
