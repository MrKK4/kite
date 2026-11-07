"""Test release checkout selection with real Git repositories, without Modal."""

import ast
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
# Load the exact local preflight function without constructing Modal images.
module = ast.parse((ROOT / "scripts/modal_build.py").read_text(encoding="utf-8"))
function = next(node for node in module.body if isinstance(node, ast.FunctionDef)
                and node.name == "release_source_revision")
namespace = {"Path": Path, "subprocess": subprocess}
exec(compile(ast.Module(body=[function], type_ignores=[]), "modal_build.py", "exec"), namespace)
release_source_revision = namespace["release_source_revision"]


class ReleaseProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="kite-provenance-")
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Kite Test")
        self.git("config", "user.email", "kite-test@example.com")
        self.git("remote", "add", "origin", "https://github.com/MrKK4/kite.git")
        (self.repository / "source.txt").write_text("source\n")
        (self.repository / ".gitignore").write_text("/dist/\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Fixture source")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repository), *args], text=True).strip()

    def test_clean_kite_checkout_uses_its_commit(self):
        self.assertEqual(release_source_revision(self.repository), self.git("rev-parse", "HEAD"))

    def test_ssh_and_https_remote_spellings_are_supported(self):
        for remote in ("git@github.com:MrKK4/kite.git", "ssh://git@github.com/MrKK4/kite.git",
                       "https://github.com/MrKK4/kite"):
            self.git("remote", "set-url", "origin", remote)
            self.assertEqual(release_source_revision(self.repository), self.git("rev-parse", "HEAD"))

    def test_upstream_history_checkout_cannot_be_used_for_release(self):
        self.git("remote", "set-url", "origin", "https://github.com/xai-org/grok-build.git")
        with self.assertRaisesRegex(RuntimeError, "origin must be"):
            release_source_revision(self.repository)

    def test_modified_source_cannot_be_used_for_release(self):
        (self.repository / "source.txt").write_text("modified\n")
        with self.assertRaisesRegex(RuntimeError, "commit the changes"):
            release_source_revision(self.repository)

    def test_untracked_source_cannot_be_used_for_release(self):
        (self.repository / "new-source.txt").write_text("new\n")
        with self.assertRaisesRegex(RuntimeError, "commit the changes"):
            release_source_revision(self.repository)

    def test_ignored_artifacts_do_not_change_source_revision(self):
        (self.repository / "dist").mkdir()
        (self.repository / "dist/kite.exe").write_bytes(b"artifact")
        self.assertEqual(release_source_revision(self.repository), self.git("rev-parse", "HEAD"))

    def test_missing_origin_has_actionable_error(self):
        self.git("remote", "remove", "origin")
        with self.assertRaisesRegex(RuntimeError, "clean clone"):
            release_source_revision(self.repository)


if __name__ == "__main__":
    unittest.main(verbosity=2)
