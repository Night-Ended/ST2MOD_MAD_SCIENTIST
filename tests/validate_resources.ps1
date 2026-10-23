# PowerShell 7 equivalent of the dependency-free resource checks, with issue 2 coverage.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$passed = 0
function Check($condition, [string]$name) {
    if (-not $condition) { throw "FAIL $name" }
    $script:passed++
    Write-Output "PASS $name"
}
function ReadJson([string]$path) { [IO.File]::ReadAllText((Join-Path $root $path)) | ConvertFrom-Json -AsHashtable }
$eng = ReadJson 'MadScientist/localization/eng/cards.json'
$zhs = ReadJson 'MadScientist/localization/zhs/cards.json'
foreach ($file in Get-ChildItem (Join-Path $root 'MadScientist/localization/eng') -Filter '*.json') {
    $en = ReadJson "MadScientist/localization/eng/$($file.Name)"
    $zh = ReadJson "MadScientist/localization/zhs/$($file.Name)"
    Check (-not (Compare-Object @($en.Keys | Sort-Object) @($zh.Keys | Sort-Object))) "$($file.Name): matching language keys"
    foreach ($key in $en.Keys) { Check ($en[$key] -notmatch '[\u4e00-\u9fff]') "English text: $($file.Name):$key" }
}
$classes = @{}
foreach ($file in Get-ChildItem (Join-Path $root 'MadScientistCode/Cards') -Filter '*.cs') {
    $text = [IO.File]::ReadAllText($file.FullName)
    foreach ($match in [regex]::Matches($text, 'public class (\w+) : MadScientistCard(.*?)(?=\npublic class |\z)', 'Singleline')) {
        $name = $match.Groups[1].Value
        $body = $match.Groups[2].Value
        $key = [regex]::Replace($name, '(?<!^)(?=[A-Z])', '_').ToUpperInvariant()
        $vars = @('IfUpgraded')
        foreach ($m in [regex]::Matches($body, 'new (Damage|Block|Cards|Energy)Var\(|new PowerVar<(\w+)>|new DynamicVar\("(\w+)"')) {
            $vars += ($m.Groups | Select-Object -Skip 1 | Where-Object Success | Select-Object -First 1).Value
        }
        $classes[$key] = $vars
        Check ($eng.Contains("MADSCIENTIST-$key.title") -and $zhs.Contains("MADSCIENTIST-$key.description")) "$name has localized title and description"
        Check (Test-Path -LiteralPath (Join-Path $root "MadScientist/images/card_portraits/$($key.ToLowerInvariant()).png")) "$name has card portrait"
    }
}
Check ($classes.Count -eq 63) 'exactly 63 issue card classes'
$classes['FUSED_CARD'] = $classes['FUSED_X_CARD'] = @('Effects')
foreach ($data in @($eng,$zhs)) {
    foreach ($key in $data.Keys | Where-Object { $_ -like 'MADSCIENTIST-*.description' }) {
        $name = $key.Replace('MADSCIENTIST-','').Replace('.description','')
        foreach ($var in [regex]::Matches($data[$key], '\{(\w+)')) {
            Check ($classes[$name] -contains $var.Groups[1].Value) "${key}: dynamic variable $($var.Groups[1].Value)"
        }
    }
}
foreach ($lang in @('eng','zhs')) {
    $data = ReadJson "MadScientist/localization/$lang/cards.json"
    foreach ($key in @('X_RAY','BLASTING_DEVICE')) { Check ($data["MADSCIENTIST-$key.description"] -notmatch 'X\(X\+1\)') "$lang $key does not show X(X+1)" }
    $ancients = ReadJson "MadScientist/localization/$lang/ancients.json"
    $names = @($ancients.Keys | ForEach-Object { ($_ -split '\.')[0] } | Sort-Object -Unique)
    Check ($names.Count -eq 8) "$lang has eight ancient dialogue groups (static only)"
}
foreach ($file in @('images/rooms/rest_site.png','images/ui/hands/multiplayer_hand_madscientist_point.png','images/ui/hands/multiplayer_hand_madscientist_rock.png','images/ui/hands/multiplayer_hand_madscientist_paper.png','images/ui/hands/multiplayer_hand_madscientist_scissors.png')) {
    $bytes = [IO.File]::ReadAllBytes((Join-Path $root "MadScientist/$file"))
    Check ($bytes.Length -gt 24 -and [Convert]::ToHexString($bytes[0..7]) -eq '89504E470D0A1A0A') "$file is a PNG (layout not tested)"
}
[xml]$project = [IO.File]::ReadAllText((Join-Path $root 'MadScientist.csproj'))
foreach ($copy in $project.SelectNodes('//Copy')) { Check ($copy.DestinationFolder.TrimEnd('/') -eq '$(ModOutputDir)') 'build output uses isolated-overridable ModOutputDir' }
Write-Output "$passed static resource assertions passed; no rendering/gameplay/multiplayer claim."
