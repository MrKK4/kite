"""Installer smoke tests with local download fixtures; never change user PATH.

Run on Windows: python scripts/test_installers.py
"""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe")
BASH = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "Windows PowerShell required")
class PowerShellInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="kite-installer-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.payload = b"fixture release binary\n"
        (self.directory / "kite-windows-x64.exe").write_bytes(self.payload)
        digest = hashlib.sha256(self.payload).hexdigest()
        (self.directory / "SHA256SUMS").write_text(f"{digest}  kite-windows-x64.exe\n")
        self.install = self.directory / "install with spaces"

    def run_installer(self, version="", checksum=None, existing=None):
        if checksum is not None:
            (self.directory / "SHA256SUMS").write_text(checksum)
        if existing is not None:
            self.install.mkdir()
            (self.install / "kite.exe").write_bytes(existing)
        wrapper = self.directory / "run.ps1"
        wrapper.write_text(
            r"""
$ErrorActionPreference = 'Stop'
$before = [Environment]::GetEnvironmentVariable('Path', 'User')
function Invoke-RestMethod {
    param($Uri, $Headers)
    if ($env:KITE_VERSION) { throw 'Pinned install must not query latest release' }
    if ($Uri -ne 'https://api.github.com/repos/MrKK4/kite/releases/latest') { throw 'Wrong metadata URL' }
    return @{ tag_name = 'v9.9.9' }
}
function Invoke-WebRequest {
    param($Uri, $OutFile, [switch]$UseBasicParsing)
    $tag = if ($env:KITE_VERSION) { $env:KITE_VERSION } else { 'v9.9.9' }
    $name = ($Uri -split '/')[-1]
    if ($Uri -ne "https://github.com/MrKK4/kite/releases/download/$tag/$name") { throw 'Unpinned download' }
    Copy-Item -LiteralPath (Join-Path $env:KITE_TEST_FIXTURES $name) -Destination $OutFile
}
try {
    & $env:KITE_TEST_INSTALLER
    if (($env:Path -split ';')[0] -ne $env:KITE_INSTALL_DIR) { throw 'Current session PATH missing install directory' }
} finally {
    if ([Environment]::GetEnvironmentVariable('Path', 'User') -ne $before) { throw 'Test modified user PATH' }
}
""",
            encoding="utf-8",
        )
        env = dict(os.environ, KITE_VERSION=version, KITE_INSTALL_DIR=str(self.install),
                   KITE_NO_MODIFY_PATH="1", KITE_TEST_FIXTURES=str(self.directory),
                   KITE_TEST_INSTALLER=str(ROOT / "scripts/install.ps1"))
        return subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(wrapper)],
                              env=env, capture_output=True, text=True, timeout=30)

    def test_latest_installs_verified_binary_in_directory_with_spaces(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.install / "kite.exe").read_bytes(), self.payload)
        self.assertEqual(list(self.install.glob("*.download")), [])

    def test_pinned_release_replaces_existing_binary(self):
        result = self.run_installer(version="v0.1.1", existing=b"previous binary")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.install / "kite.exe").read_bytes(), self.payload)

    def test_checksum_mismatch_preserves_previous_installation(self):
        result = self.run_installer(checksum="0" * 64 + "  kite-windows-x64.exe\n", existing=b"previous binary")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA-256 verification failed", result.stderr)
        self.assertEqual((self.install / "kite.exe").read_bytes(), b"previous binary")

    def test_missing_checksum_never_installs_binary(self):
        result = self.run_installer(checksum="0" * 64 + "  other.exe\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.install.exists())

    def test_duplicate_checksum_is_rejected(self):
        checksum = (self.directory / "SHA256SUMS").read_text()
        result = self.run_installer(checksum=checksum * 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.install.exists())

    def test_invalid_release_tag_is_rejected(self):
        result = self.run_installer(version="../../main")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KITE_VERSION must be a release tag", result.stderr)
        self.assertFalse(self.install.exists())


@unittest.skipUnless(BASH.exists(), "Git Bash required")
class GitBashInstallerTests(unittest.TestCase):
    def run_wrapper(self, directory, exit_code=0):
        (directory / "curl").write_text(
            '#!/usr/bin/env bash\ncp "$(cygpath -u "$KITE_TEST_INSTALLER")" "${!#}"\n', newline="\n")
        (directory / "powershell.exe").write_text(
            '#!/usr/bin/env bash\nset -eu\n'
            'test -f "$(cygpath -u "${!#}")"\n'
            'printf "%s\\n%s" "$KITE_INSTALL_DIR" "${!#}" > "$(cygpath -u "$KITE_TEST_TRACE")"\n'
            'exit "$KITE_TEST_EXIT"\n', newline="\n")
        command = 'export PATH="$(cygpath -u "$KITE_TEST_COMMANDS"):$PATH"; bash scripts/install.sh'
        env = dict(os.environ, KITE_TEST_COMMANDS=str(directory),
                   KITE_TEST_INSTALLER=str(ROOT / "scripts/install.ps1"),
                   KITE_TEST_TRACE=str(directory / "trace"), KITE_TEST_EXIT=str(exit_code),
                   KITE_INSTALL_DIR=str(directory / "install with spaces"))
        result = subprocess.run([str(BASH), "-c", command], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=15)
        return result

    def test_delegates_to_powershell_with_quoted_paths_and_cleans_download(self):
        with tempfile.TemporaryDirectory(prefix="kite-bash-test-") as temporary:
            directory = Path(temporary)
            result = self.run_wrapper(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            install, downloaded = (directory / "trace").read_text().splitlines()
            self.assertEqual(Path(install), directory / "install with spaces")
            self.assertFalse(Path(downloaded).exists())
            self.assertIn('export PATH=', result.stdout)

    def test_propagates_powershell_failure_and_cleans_download(self):
        with tempfile.TemporaryDirectory(prefix="kite-bash-test-") as temporary:
            directory = Path(temporary)
            result = self.run_wrapper(directory, exit_code=17)
            self.assertEqual(result.returncode, 17, result.stdout + result.stderr)
            _, downloaded = (directory / "trace").read_text().splitlines()
            self.assertFalse(Path(downloaded).exists())
            self.assertNotIn('export PATH=', result.stdout)

    def test_shell_syntax(self):
        result = subprocess.run([str(BASH), "-n", "scripts/install.sh"], cwd=ROOT,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_linux_fails_before_download(self):
        with tempfile.TemporaryDirectory(prefix="kite-bash-test-") as temporary:
            directory = Path(temporary)
            (directory / "uname").write_text("#!/usr/bin/env bash\necho Linux\n", newline="\n")
            command = 'export PATH="$(cygpath -u "$KITE_TEST_COMMANDS"):$PATH"; bash scripts/install.sh'
            result = subprocess.run([str(BASH), "-c", command], cwd=ROOT,
                                    env=dict(os.environ, KITE_TEST_COMMANDS=str(directory)),
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Native Linux/macOS release binaries are not available", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
