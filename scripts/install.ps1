# Install Kite for the current Windows user. Run with:
# irm https://raw.githubusercontent.com/MrKK4/kite/main/scripts/install.ps1 | iex
# Optional: KITE_VERSION=v0.1.1, KITE_INSTALL_DIR=<directory>, KITE_NO_MODIFY_PATH=1.
& {
    $ErrorActionPreference = 'Stop'
    if ($env:OS -ne 'Windows_NT') {
        throw 'This installer supports Windows x64. Native Linux/macOS binaries are not published yet.'
    }
    $architecture = $env:PROCESSOR_ARCHITECTURE
    if ($env:PROCESSOR_ARCHITEW6432) { $architecture = $env:PROCESSOR_ARCHITEW6432 }
    if ($architecture -ne 'AMD64') {
        throw "Kite currently provides a Windows x64 binary; detected $architecture."
    }

    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $repository = 'MrKK4/kite'
    $version = $env:KITE_VERSION
    if (-not $version) {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$repository/releases/latest" -Headers @{ 'User-Agent' = 'Kite-Installer' }
        $version = $release.tag_name
    }
    if ($version -notmatch '^v[0-9][A-Za-z0-9._-]*$') {
        throw 'KITE_VERSION must be a release tag such as v0.1.1.'
    }

    $installDirectory = if ($env:KITE_INSTALL_DIR) {
        [IO.Path]::GetFullPath($env:KITE_INSTALL_DIR)
    } else {
        Join-Path ([Environment]::GetFolderPath('UserProfile')) '.kite\bin'
    }
    $temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
    $temporaryDirectory = Join-Path $temporaryRoot ('kite-install-' + [Guid]::NewGuid().ToString('N'))
    $pending = $null
    [IO.Directory]::CreateDirectory($temporaryDirectory) | Out-Null
    try {
        $asset = 'kite-windows-x64.exe'
        $base = "https://github.com/$repository/releases/download/$version"
        $binary = Join-Path $temporaryDirectory $asset
        $checksums = Join-Path $temporaryDirectory 'SHA256SUMS'
        Write-Host "Downloading Kite $version..."
        $savedProgress = $ProgressPreference
        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -UseBasicParsing -Uri "$base/SHA256SUMS" -OutFile $checksums
            Invoke-WebRequest -UseBasicParsing -Uri "$base/$asset" -OutFile $binary
        } finally {
            $ProgressPreference = $savedProgress
        }
        $matchingLines = @(Get-Content -LiteralPath $checksums | Where-Object {
            $_ -match '^([a-fA-F0-9]{64})\s+\*?kite-windows-x64\.exe$'
        })
        if ($matchingLines.Count -ne 1) {
            throw 'The release checksum file must contain exactly one entry for the Windows binary.'
        }
        $expected = ($matchingLines[0] -split '\s+')[0]
        $hasher = [Security.Cryptography.SHA256]::Create()
        $stream = [IO.File]::OpenRead($binary)
        try {
            $actual = [BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-', '')
        } finally {
            $stream.Dispose()
            $hasher.Dispose()
        }
        if ($actual -ne $expected) {
            throw 'SHA-256 verification failed. The existing installation was not changed.'
        }

        [IO.Directory]::CreateDirectory($installDirectory) | Out-Null
        $installed = Join-Path $installDirectory 'kite.exe'
        $pending = Join-Path $installDirectory ('.kite-' + [Guid]::NewGuid().ToString('N') + '.download')
        [IO.File]::Copy($binary, $pending)
        try {
            if ([IO.File]::Exists($installed)) {
                [IO.File]::Replace($pending, $installed, [NullString]::Value)
            } else {
                [IO.File]::Move($pending, $installed)
            }
        } catch {
            throw "Could not replace $installed. Close any running Kite processes and try again. $($_.Exception.Message)"
        }

        if ($env:KITE_NO_MODIFY_PATH -ne '1') {
            $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
            $alreadyPresent = @($userPath -split ';' | Where-Object {
                [Environment]::ExpandEnvironmentVariables($_).TrimEnd('\', '/') -eq $installDirectory.TrimEnd('\', '/')
            }).Count -gt 0
            if (-not $alreadyPresent) {
                $newPath = if ([string]::IsNullOrEmpty($userPath)) { $installDirectory } else { "$($userPath.TrimEnd(';'));$installDirectory" }
                [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
            }
        }
        # irm | iex runs in this PowerShell session, so kite is available immediately.
        $env:Path = "$installDirectory;$env:Path"
        Write-Host "Installed Kite $version to $installed (SHA-256 verified)."
        Write-Host 'Run: kite --version'
        Write-Host 'Connect a model: kite login http://localhost:8080/v1'
    } finally {
        if ($pending -and [IO.File]::Exists($pending)) {
            Remove-Item -LiteralPath $pending -Force
        }
        $resolvedTemporary = [IO.Path]::GetFullPath($temporaryDirectory)
        if (-not $resolvedTemporary.StartsWith($temporaryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Refusing to clean a directory outside the installer temporary root.'
        }
        Remove-Item -LiteralPath $resolvedTemporary -Recurse -Force
    }
}
