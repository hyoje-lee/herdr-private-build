"""Installer regression tests; use temporary files and never a real app/session."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
from unittest.mock import patch

import secure_build as builder
from secure_policy import POLICY, apply


class InstallTests(unittest.TestCase):
    def fixture(self, root):
        work = root / "work"
        (work / "target/release").mkdir(parents=True)
        for name in ("herdr-core", "herdr-app"):
            (work / "target/release" / name).write_text(f"#!/bin/sh\nprintf '{POLICY}\\n'\n")
            (work / "target/release" / name).chmod(0o755)
        (work / "manifest.json").write_text("{}")
        (work / "private.patch").write_text("fixture patch")
        icons = work / "herdr-app/assets/icons"
        icons.mkdir(parents=True)
        (icons / "herdr-ui-icon-clean.svg").write_text("<svg/>")
        return work

    def test_core_install_backs_up_official_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            (prefix / "bin").mkdir(parents=True)
            (prefix / "bin/herdr-core").write_text("official core")
            (prefix / "bin/hc").symlink_to("herdr-core")
            builder.install(work, prefix, data, "core")
            self.assertTrue(builder.is_private(prefix / "bin/herdr-core"))
            self.assertEqual(os.readlink(prefix / "bin/hc"), "herdr-core")
            record = json.loads(next((data / "herdr-build/backups").glob("core-*/restore.json")).read_text())
            self.assertEqual(Path(record[0]["backup"]).read_text(), "official core")
            self.assertTrue(Path(record[1]["backup"]).is_symlink())
            self.assertEqual((data / "herdr-build/core/private.patch").read_text(), "fixture patch")

    def test_failed_install_restores_previous_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            (prefix / "bin").mkdir(parents=True)
            (prefix / "bin/herdr-core").write_text("official core")
            real_replace = os.replace
            calls = []

            def failing_replace(source, target):
                calls.append(target)
                if len(calls) == 2:
                    raise OSError("disk full")
                return real_replace(source, target)

            with patch.object(builder.os, "replace", side_effect=failing_replace):
                with self.assertRaises(OSError):
                    builder.install(work, prefix, data, "core")
            self.assertEqual((prefix / "bin/herdr-core").read_text(), "official core")
            self.assertFalse(os.path.lexists(prefix / "bin/hc"))
            self.assertEqual([p.name for p in (prefix / "bin").iterdir()], ["herdr-core"])

    def test_failed_provenance_write_restores_binaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            (prefix / "bin").mkdir(parents=True)
            (prefix / "bin/herdr-core").write_text("official core")
            (prefix / "bin/hc").symlink_to("herdr-core")
            old_record = data / "herdr-build/core/manifest.json"
            old_record.parent.mkdir(parents=True)
            old_record.write_text("previous manifest")
            real_replace = os.replace

            def failing_replace(source, target):
                if Path(target).name == "private.patch":
                    raise OSError("disk full")
                return real_replace(source, target)

            with patch.object(builder.os, "replace", side_effect=failing_replace):
                with self.assertRaises(OSError):
                    builder.install(work, prefix, data, "core")
            self.assertEqual((prefix / "bin/herdr-core").read_text(), "official core")
            self.assertEqual(os.readlink(prefix / "bin/hc"), "herdr-core")
            self.assertEqual(old_record.read_text(), "previous manifest")
            self.assertFalse((data / "herdr-build/core/private.patch").exists())

    def test_directory_target_is_refused_before_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            (prefix / "bin/hc").mkdir(parents=True)
            (prefix / "bin/herdr-core").write_text("official core")
            with self.assertRaisesRegex(RuntimeError, "Refusing to replace directory"):
                builder.install(work, prefix, data, "core")
            self.assertEqual((prefix / "bin/herdr-core").read_text(), "official core")

    def test_app_install_requires_patched_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            (prefix / "bin").mkdir(parents=True)
            official = prefix / "bin/herdr-core"
            official.write_text("#!/bin/sh\necho unknown flag >&2\nexit 2\n")
            official.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "Install the patched core first"):
                builder.install(work, prefix, data, "app")
            self.assertFalse((prefix / "bin/herdr-app").exists())
            self.assertFalse(data.exists())

    def test_app_install_keeps_core_and_writes_desktop_entry(self):
        with tempfile.TemporaryDirectory(prefix="herdr test '") as tmp:
            root = Path(tmp)
            work = self.fixture(root)
            prefix, data = root / "prefix", root / "data"
            builder.install(work, prefix, data, "core")
            core = (prefix / "bin/herdr-core").read_bytes()
            (prefix / "bin/herdr-app").symlink_to(root / "official-app")
            builder.install(work, prefix, data, "app")
            self.assertEqual((prefix / "bin/herdr-core").read_bytes(), core)
            self.assertFalse((prefix / "bin/herdr-app").is_symlink())
            desktop = (data / "applications/herdr-app.desktop").read_text()
            self.assertIn(f'Exec="{prefix / "bin/herdr-app"}"', desktop)
            self.assertTrue((data / "icons/hicolor/scalable/apps/herdr-app.svg").is_file())

    def test_unpatched_binary_is_not_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "herdr-core"
            binary.write_text("#!/bin/sh\necho herdr-core 0.1.21\n")
            binary.chmod(0o755)
            self.assertFalse(builder.is_private(binary))
            self.assertFalse(builder.is_private(Path(tmp) / "missing"))


class PrerequisiteTests(unittest.TestCase):
    def test_explicit_zig_is_the_version_checked(self):
        def versions(argv):
            return "rustc 1.95.0 (test)" if argv[0] == "rustc" else "0.17.0"

        with patch.dict(os.environ, {"ZIG": "/custom/zig"}), \
             patch.object(builder.shutil, "which", side_effect=lambda name: name if name.startswith("/") else "/tool/" + name), \
             patch.object(builder, "output", side_effect=versions) as commands:
            with self.assertRaisesRegex(RuntimeError, "Zig 0.16.0 required"):
                builder.prerequisites("core")
            self.assertIn((["/custom/zig", "version"],), [call.args for call in commands.call_args_list])

    def test_core_does_not_require_app_tools_or_libraries(self):
        tools = lambda name: None if name in ("clang", "pkg-config") else "/tool/" + name
        versions = lambda argv: "rustc 1.95.0 (test)" if argv[0] == "rustc" else "0.16.0"
        with patch.object(builder.shutil, "which", side_effect=tools), \
             patch.object(builder, "output", side_effect=versions), \
             patch.object(builder.subprocess, "run") as runner:
            builder.prerequisites("core")
            runner.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, "clang"):
                builder.prerequisites("app")


class PatchTests(unittest.TestCase):
    def test_core_patch_needs_no_app_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = Path("herdr-core/crates/herdr-core/src")
            shutil.copytree(builder.ROOT / relative, root / relative)
            diff = apply(root, "core")
            self.assertIn("Self-update disabled in private build", diff)
            self.assertNotIn("herdr-app", diff)
            self.assertFalse((root / "herdr-app").exists())

    def source_copy(self, root):
        for project, directory in (("herdr-app", "src"), ("herdr-core", "crates/herdr-core/src")):
            shutil.copytree(builder.ROOT / project / directory, root / project / directory)
        dependency = Path("herdr-app/vendor/gpui-kit/crates/shell/src/dependencies.rs")
        (root / dependency).parent.mkdir(parents=True)
        shutil.copy2(builder.ROOT / dependency, root / dependency)

    def test_current_sources_patch_once_and_reject_second_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_copy(root)
            diff = apply(root)
            self.assertIn("NetworkGrant::Denied", diff)
            self.assertIn("Self-update disabled in private build", diff)
            self.assertIn("private_policy_download", diff)
            with self.assertRaises(RuntimeError):
                apply(root)

    def test_changed_function_signature_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_copy(root)
            path = root / "herdr-app/src/telemetry.rs"
            path.write_text(path.read_text().replace("fn read_env_off()", "fn changed_env_off()"))
            with self.assertRaisesRegex(RuntimeError, "Patch context mismatch"):
                apply(root)


if __name__ == "__main__":
    unittest.main()
