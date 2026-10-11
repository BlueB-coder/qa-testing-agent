# Standalone checks, no Pester/Python dependency. Writes only to temporary directories.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$temp = Join-Path ([IO.Path]::GetTempPath()) ('qa kit tests ' + [guid]::NewGuid())
[void][IO.Directory]::CreateDirectory($temp)
$utf8 = New-Object Text.UTF8Encoding($false)
$script = Join-Path $root 'install/install.ps1'
$script:checks = 0
function Assert([bool]$Condition, [string]$Message) {
    if (!$Condition) { throw $Message }
    $script:checks++
}
function Snapshot([string]$Directory) {
    $rows = @(Get-ChildItem -LiteralPath $Directory -Recurse -Force -File | Sort-Object FullName | ForEach-Object {
        $_.FullName.Substring($Directory.Length) + ':' + [Convert]::ToBase64String([IO.File]::ReadAllBytes($_.FullName))
    })
    return ($rows -join "`n")
}
function Expect-Failure([scriptblock]$Action, [string]$Message) {
    $failed = $false
    try { & $Action | Out-Null } catch { $failed = $true }
    Assert $failed $Message
}
try {
    foreach ($targetName in @('codex','claude','both')) {
        foreach ($scopeName in @('project','user')) {
            $project = Join-Path $temp "$targetName $scopeName app"
            [void][IO.Directory]::CreateDirectory($project)
            $installer = $script
            if ($scopeName -eq 'user') {
                # Mock only the platform home lookup in an isolated copy, never the real user profile.
                $kit = Join-Path $temp "$targetName isolated kit"
                [void][IO.Directory]::CreateDirectory((Join-Path $kit 'install'))
                Copy-Item -LiteralPath (Join-Path $root 'skills') -Destination $kit -Recurse
                Copy-Item -LiteralPath (Join-Path $root 'agents') -Destination $kit -Recurse
                $installer = Join-Path $kit 'install/install.ps1'
                $text = [IO.File]::ReadAllText($script)
                $text = $text.Replace("[Environment]::GetFolderPath('UserProfile')", "'" + $project.Replace("'", "''") + "'")
                [IO.File]::WriteAllText($installer, $text, $utf8)
            }
            $savedCodexHome = $env:CODEX_HOME
            try {
                # Avoid a real inherited custom Codex directory; use an isolated one for user scope.
                if ($scopeName -eq 'user') { $env:CODEX_HOME = Join-Path $project 'custom codex' }
                & $installer -Target $targetName -Scope $scopeName -ProjectPath $project
                $before = Snapshot $project
                Expect-Failure { & $installer -Target $targetName -Scope $scopeName -ProjectPath $project } 'Repeat install should refuse'
                Assert ((Snapshot $project) -eq $before) 'Refusal changed files'
                foreach ($hostName in @('codex','claude')) {
                    if ($targetName -ne 'both' -and $targetName -ne $hostName) { continue }
                    $skillPrefix = '.claude'
                    if ($hostName -eq 'codex') { $skillPrefix = '.agents' }
                    $skill = Join-Path $project "$skillPrefix/skills/qa-testing"
                    Assert (Test-Path -LiteralPath (Join-Path $skill 'templates/qa-report.md')) 'Report template missing'
                    Assert (Test-Path -LiteralPath (Join-Path $skill 'templates/defect-report.md')) 'Defect template missing'
                    $agentDir = Join-Path $project ".$hostName/agents"
                    $extension = 'md'
                    if ($hostName -eq 'codex') {
                        $extension = 'toml'
                        if ($scopeName -eq 'user') { $agentDir = Join-Path $project 'custom codex/agents' }
                    }
                    $descriptor = [IO.File]::ReadAllText((Join-Path $agentDir "qa-tester.$extension"))
                    Assert (!$descriptor.Contains('@@SKILL_PATH@@')) 'Unresolved skill marker'
                    if ($hostName -eq 'codex') {
                        $expectedPath = (Join-Path $skill 'SKILL.md').Replace('\','\\').Replace('"','\"')
                        Assert ($descriptor.Contains($expectedPath)) 'Escaped TOML skill path missing'
                    }
                }
                $unrelated = Join-Path $project 'unrelated.txt'
                [IO.File]::WriteAllText($unrelated, 'keep me', $utf8)
                & $installer -Target $targetName -Scope $scopeName -ProjectPath $project -Force
                Assert (@(Get-ChildItem -LiteralPath $project -Recurse -Force -Filter '*.bak').Count -gt 0) 'No backups'
                Assert ([IO.File]::ReadAllText($unrelated) -eq 'keep me') 'Unrelated file changed'
                $before = Snapshot $project
                Expect-Failure { & $installer -Target $targetName -Scope $scopeName -ProjectPath $project -Force } 'Backup collision should refuse'
                Assert ((Snapshot $project) -eq $before) 'Collision changed files'
            } finally { $env:CODEX_HOME = $savedCodexHome }
        }
    }
    $project = Join-Path $temp 'late conflict'
    [void][IO.Directory]::CreateDirectory((Join-Path $project '.claude/agents'))
    [IO.File]::WriteAllText((Join-Path $project '.claude/agents/qa-tester.md'), 'old', $utf8)
    $before = Snapshot $project
    Expect-Failure { & $script -Target both -ProjectPath $project } 'Late conflict should refuse'
    Assert ((Snapshot $project) -eq $before) 'Late conflict caused partial install'
    Assert (!(Test-Path -LiteralPath (Join-Path $project '.agents'))) 'Preflight created a directory'

    $project = Join-Path $temp 'parent conflict'
    [void][IO.Directory]::CreateDirectory($project)
    [IO.File]::WriteAllText((Join-Path $project '.claude'), 'file', $utf8)
    $before = Snapshot $project
    Expect-Failure { & $script -Target both -ProjectPath $project } 'Parent-file conflict should refuse'
    Assert ((Snapshot $project) -eq $before) 'Parent conflict caused partial install'

    $project = Join-Path $temp 'broken backup link'
    [void][IO.Directory]::CreateDirectory((Join-Path $project '.claude/agents'))
    $agent = Join-Path $project '.claude/agents/qa-tester.md'
    [IO.File]::WriteAllText($agent, 'old', $utf8)
    $linked = $false
    try {
        New-Item -ItemType SymbolicLink -Path ($agent + '.bak') -Target (Join-Path $temp 'missing target') | Out-Null
        $linked = $true
    } catch { Write-Host 'Symlink creation unavailable; broken-backup check skipped.' }
    if ($linked) {
        Expect-Failure { & $script -Target both -ProjectPath $project -Force } 'Broken backup link should refuse'
        Assert (!(Test-Path -LiteralPath (Join-Path $project '.agents'))) 'Broken backup preflight created files'
        Assert ([IO.File]::ReadAllText($agent) -eq 'old') 'Broken backup conflict changed original'
    }

    # Exercise rollback through a deterministic failure injected into a temporary kit copy.
    $kit = Join-Path $temp 'rollback kit'
    [void][IO.Directory]::CreateDirectory((Join-Path $kit 'install'))
    Copy-Item -LiteralPath (Join-Path $root 'skills') -Destination $kit -Recurse
    Copy-Item -LiteralPath (Join-Path $root 'agents') -Destination $kit -Recurse
    $project = Join-Path $temp 'rollback app'
    [void][IO.Directory]::CreateDirectory($project)
    $modified = [IO.File]::ReadAllText($script).Replace(
        '$stream = [IO.File]::Open($entry.dst, $mode)',
        'if ($entry.dst.EndsWith("qa-tester.md")) { throw "simulated write failure" }; $stream = [IO.File]::Open($entry.dst, $mode)')
    $failingScript = Join-Path $kit 'install/install.ps1'
    [IO.File]::WriteAllText($failingScript, $modified, $utf8)
    Expect-Failure { & $failingScript -Target both -ProjectPath $project } 'Injected failure should surface'
    Assert (@(Get-ChildItem -LiteralPath $project -Force).Count -eq 0) 'Fresh rollback left artifacts'
    & $script -Target both -ProjectPath $project
    $before = Snapshot $project
    Expect-Failure { & $failingScript -Target both -ProjectPath $project -Force } 'Forced write failure should surface'
    Assert ((Snapshot $project) -eq $before) 'Forced rollback changed original files'
    Write-Host "Passed $script:checks PowerShell assertions."
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}
