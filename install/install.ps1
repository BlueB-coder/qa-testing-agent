# Offline installer. No Python, host configuration edits, authentication or QA execution.
param(
    [ValidateSet('codex','claude','both')][string]$Target = 'both',
    [ValidateSet('project','user')][string]$Scope = 'project',
    [string]$ProjectPath = '.',
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($Scope -eq 'project') {
    if (!(Test-Path -LiteralPath $ProjectPath -PathType Container)) {
        throw "Project directory does not exist: $ProjectPath"
    }
    $base = (Resolve-Path -LiteralPath $ProjectPath).Path
} else { $base = [Environment]::GetFolderPath('UserProfile') }
$utf8 = New-Object System.Text.UTF8Encoding($false)
$plan = New-Object System.Collections.ArrayList
$required = @('SKILL.md', 'references/workflow.md', 'references/evidence.md',
    'references/openproject.md', 'references/model-selection.md',
    'templates/qa-report.md', 'templates/defect-report.md')
$skillSource = Join-Path $root 'skills/qa-testing'
foreach ($name in $required) {
    if (!(Test-Path -LiteralPath (Join-Path $skillSource $name) -PathType Leaf)) {
        throw "Incomplete kit; missing source: $name"
    }
}
function Assert-NoLink([string]$Path) {
    $current = $Path
    while ($current) {
        $item = Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Refusing link destination or ancestor: $current"
        }
        $current = Split-Path -Parent $current
    }
}
foreach ($hostName in @('codex','claude')) {
    if ($Target -ne 'both' -and $Target -ne $hostName) { continue }
    $hostDir = Join-Path $base ('.' + $hostName)
    if ($hostName -eq 'codex') {
        $skillDir = Join-Path $base '.agents/skills/qa-testing'
        $extension = 'toml'
        if ($Scope -eq 'user' -and $env:CODEX_HOME) {
            $hostDir = [IO.Path]::GetFullPath($env:CODEX_HOME)
        }
    } else {
        $skillDir = Join-Path $base '.claude/skills/qa-testing'
        $extension = 'md'
    }
    Assert-NoLink $skillSource
    Get-ChildItem -LiteralPath $skillSource -Recurse -Force | ForEach-Object {
        Assert-NoLink $_.FullName
        if (!$_.PSIsContainer) {
            $relative = $_.FullName.Substring($skillSource.Length).TrimStart([char]'\',[char]'/')
            [void]$plan.Add(@{ dst = (Join-Path $skillDir $relative); data = [IO.File]::ReadAllBytes($_.FullName) })
        }
    }
    $source = Join-Path $root "agents/qa-tester.$hostName.$extension"
    Assert-NoLink $source
    $descriptor = [IO.File]::ReadAllText($source)
    if (!$descriptor.Contains('@@SKILL_PATH@@')) { throw "Missing skill path marker: $source" }
    $skillPath = Join-Path $skillDir 'SKILL.md'
    if ($hostName -eq 'codex') {
        # Escape the path for the enclosing TOML multiline basic string.
        $skillPath = $skillPath.Replace('\','\\').Replace('"','\"').Replace("`t",'\t').Replace("`r",'\r').Replace("`n",'\n')
    }
    [void]$plan.Add(@{ dst = (Join-Path $hostDir "agents/qa-tester.$extension");
        data = $utf8.GetBytes($descriptor.Replace('@@SKILL_PATH@@', $skillPath)) })
}
# Preflight the complete plan before creating even a directory.
foreach ($entry in $plan) {
    Assert-NoLink $entry.dst
    $item = Get-Item -LiteralPath $entry.dst -Force -ErrorAction SilentlyContinue
    if ($item) {
        if ($item.PSIsContainer) { throw "Destination is not a file: $($entry.dst)" }
        if (!$Force) { throw "Existing file; use -Force to back up and replace: $($entry.dst)" }
        if ($item.IsReadOnly) { throw "Destination is read-only: $($entry.dst)" }
        $backupItem = Get-Item -LiteralPath ($entry.dst + '.bak') -Force -ErrorAction SilentlyContinue
        if ($backupItem) { throw "Backup collision; move .bak first: $($entry.dst)" }
    }
    $parent = Split-Path -Parent $entry.dst
    while ($parent) {
        $parentItem = Get-Item -LiteralPath $parent -Force -ErrorAction SilentlyContinue
        if ($parentItem -and !$parentItem.PSIsContainer) { throw "Parent is not a directory: $parent" }
        $parent = Split-Path -Parent $parent
    }
}
$changed = New-Object System.Collections.ArrayList
$backups = New-Object System.Collections.ArrayList
$directories = New-Object System.Collections.ArrayList
try {
    foreach ($entry in $plan) {
        $missing = New-Object System.Collections.ArrayList
        $parent = Split-Path -Parent $entry.dst
        while (!(Test-Path -LiteralPath $parent)) {
            [void]$missing.Add($parent)
            $parent = Split-Path -Parent $parent
        }
        for ($i = $missing.Count - 1; $i -ge 0; $i--) {
            [void][IO.Directory]::CreateDirectory($missing[$i])
            [void]$directories.Add($missing[$i])
        }
        $old = $null
        if (Test-Path -LiteralPath $entry.dst) {
            $old = [IO.File]::ReadAllBytes($entry.dst)
            $stream = [IO.File]::Open($entry.dst + '.bak', [IO.FileMode]::CreateNew)
            [void]$backups.Add($entry.dst + '.bak')
            try { $stream.Write($old, 0, $old.Length) } finally { $stream.Dispose() }
        }
        [void]$changed.Add(@{ dst = $entry.dst; old = $old })
        $mode = [IO.FileMode]::CreateNew
        if ($null -ne $old) { $mode = [IO.FileMode]::Create }
        $stream = [IO.File]::Open($entry.dst, $mode)
        try { $stream.Write($entry.data, 0, $entry.data.Length) } finally { $stream.Dispose() }
    }
} catch {
    $originalError = $_
    $failures = New-Object System.Collections.ArrayList
    for ($i = $changed.Count - 1; $i -ge 0; $i--) {
        $entry = $changed[$i]
        try {
            if ($null -eq $entry.old) {
                if (Test-Path -LiteralPath $entry.dst) { [IO.File]::Delete($entry.dst) }
            } else { [IO.File]::WriteAllBytes($entry.dst, $entry.old) }
        } catch { [void]$failures.Add($_.Exception.Message) }
    }
    if ($failures.Count -eq 0) { foreach ($backup in $backups) { [IO.File]::Delete($backup) } }
    for ($i = $directories.Count - 1; $i -ge 0; $i--) {
        try { [IO.Directory]::Delete($directories[$i]) } catch { }
    }
    if ($failures.Count -gt 0) {
        throw "Install failed: $originalError; rollback failures: $($failures -join '; '); retain .bak files for recovery"
    }
    throw $originalError
}
foreach ($entry in $plan) { Write-Host "Installed: $($entry.dst)" }
Write-Host 'Restart the host and verify qa-tester discovery. No host config was edited.'
Write-Host 'OpenProject is optional; install/authenticate its integration separately for task-ID mode.'
