import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import encrypt_payload


ROOT = Path(__file__).parents[1]


class EncryptionPackagingTests(unittest.TestCase):
    def test_refuses_to_package_source_tree(self):
        with self.assertRaises(ValueError):
            encrypt_payload._checked_app_dir(str(ROOT))

    def test_obfuscator_failure_stops_packaging(self):
        (ROOT / "build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(suffix=".AppDir", dir=ROOT / "build") as directory:
            app_dir = Path(directory)
            (app_dir / "backend").mkdir()
            (app_dir / "backend" / "demo.py").write_text("VALUE = 1\n")
            (app_dir / "launcher.py").write_text("print('launcher')\n")
            (app_dir / "frontend").mkdir()
            (app_dir / "frontend" / "app.js").write_text("console.log('app');\n")

            with mock.patch.object(sys, "argv", ["encrypt_payload.py", directory]), mock.patch.object(
                encrypt_payload.subprocess, "check_call"
            ), mock.patch.object(
                encrypt_payload.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "npx")
            ) as obfuscator:
                with self.assertRaises(subprocess.CalledProcessError):
                    encrypt_payload.main()
            command = obfuscator.call_args.args[0]
            self.assertIn("--package=javascript-obfuscator@4.1.1", command)

    def test_loader_keeps_compiled_code_not_source_strings(self):
        (ROOT / "build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(suffix=".AppDir", dir=ROOT / "build") as directory:
            app_dir = Path(directory)
            (app_dir / "backend").mkdir()
            (app_dir / "backend" / "demo.py").write_text("VALUE = 42\n")
            (app_dir / "launcher.py").write_text("print('launcher')\n")
            with mock.patch.object(sys, "argv", ["encrypt_payload.py", directory]):
                encrypt_payload.main()

            env = os.environ.copy()
            env.pop("APPDIR", None)
            env["PYTHONPATH"] = directory
            check = subprocess.run(
                [sys.executable, "-c", "import backend, types; from backend import demo; "
                 "assert demo.VALUE == 42; "
                 "assert isinstance(backend._modules['demo'], types.CodeType)"],
                cwd=directory, env=env, capture_output=True, text=True,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            launch = subprocess.run(
                [sys.executable, "launcher.py"], cwd=directory, env=env,
                capture_output=True, text=True,
            )
            self.assertEqual(launch.returncode, 0, launch.stderr)
            self.assertEqual(launch.stdout.strip(), "launcher")

    def test_apprun_only_accepts_webkit_version_launcher_uses(self):
        build = (ROOT / "build_appimage.sh").read_text(encoding="utf-8")
        self.assertNotIn("WebKit2', '4.0'", build)


if __name__ == "__main__":
    unittest.main()
