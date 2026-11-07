"""Exercise the real Rust build script, including source uploads without .git.

Run on Modal, where rustc and git are available. No application build is needed.
"""

import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
REVISION = "0123456789abcdef0123456789abcdef01234567"


class VersionStampingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="kite-version-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.executable = cls.directory / ("build-script.exe" if os.name == "nt" else "build-script")
        subprocess.run(["rustc", "--edition", "2024", str(ROOT / "crates/codegen/kite-pager-bin/build.rs"),
                        "-o", str(cls.executable)], check=True)
        cls.version = tomllib.loads((ROOT / "crates/codegen/kite-version/Cargo.toml").read_text())["package"]["version"]

    def stamp(self, revision=REVISION, override=True, cwd=None):
        env = {k: v for k, v in os.environ.items()
               if k not in {"GROK_VERSION", "KITE_BUILD_COMMIT", "GIT_DIR", "GIT_WORK_TREE"}}
        env["CARGO_PKG_VERSION"] = self.version
        if override:
            env["GROK_VERSION"] = self.version
        if revision is not None:
            env["KITE_BUILD_COMMIT"] = revision
        return subprocess.run([str(self.executable)], cwd=cwd or self.directory,
                              env=env, capture_output=True, text=True, timeout=15)

    def assert_stamp(self, result, commit):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"cargo:rustc-env=VERSION_WITH_COMMIT={self.version} ({commit})", result.stdout)
        self.assertIn("cargo:rerun-if-env-changed=KITE_BUILD_COMMIT", result.stdout)

    def test_release_upload_without_git_has_version_and_revision(self):
        self.assertFalse((self.directory / ".git").exists())
        self.assert_stamp(self.stamp(), REVISION[:12])

    def test_source_build_defaults_to_kite_package_version(self):
        self.assert_stamp(self.stamp(override=False), REVISION[:12])

    def test_modified_source_retains_dirty_label(self):
        self.assert_stamp(self.stamp(revision=REVISION + "-dirty"), REVISION[:12] + "-dirty")

    def test_invalid_explicit_revision_is_rejected(self):
        result = self.stamp(revision="unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KITE_BUILD_COMMIT must be a Git revision", result.stderr)

    def test_local_build_reads_git_and_explicit_revision_takes_precedence(self):
        with tempfile.TemporaryDirectory(prefix="kite-version-repo-") as temporary:
            subprocess.run(["git", "init", "--quiet", temporary], check=True)
            subprocess.run(["git", "-C", temporary, "-c", "user.name=Kite Test",
                            "-c", "user.email=kite-test@example.com", "commit", "--quiet",
                            "--allow-empty", "-m", "Test revision"], check=True)
            commit = subprocess.check_output(["git", "-C", temporary, "rev-parse", "HEAD"], text=True).strip()
            self.assert_stamp(self.stamp(revision=None, cwd=temporary), commit[:12])
            self.assert_stamp(self.stamp(cwd=temporary), REVISION[:12])

    def test_cli_crate_versions_remain_in_sync(self):
        for crate in ("kite-version", "kite-pager-bin", "kite-pager", "kite-shell"):
            package = tomllib.loads((ROOT / "crates/codegen" / crate / "Cargo.toml").read_text())["package"]
            self.assertEqual(package["version"], self.version, crate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
