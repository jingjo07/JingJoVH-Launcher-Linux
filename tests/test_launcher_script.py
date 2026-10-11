"""The source launcher must run the checkout from any working directory."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceLauncherTests(unittest.TestCase):
    def test_runs_source_entry_point_without_appimage_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            stub = Path(directory, "python3")
            stub.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE_ARGS"\n'
                'printf "%s\\n" "${APPDIR-unset}" "${APPIMAGE-unset}" > "$CAPTURE_ENV"\n'
            )
            stub.chmod(0o755)
            args_file = Path(directory, "args")
            env_file = Path(directory, "env")
            env = {
                **os.environ,
                "PATH": f"{directory}:{os.environ['PATH']}",
                "APPDIR": "/old/AppDir",
                "APPIMAGE": "/old/Launcher.AppImage",
                "CAPTURE_ARGS": str(args_file),
                "CAPTURE_ENV": str(env_file),
            }

            subprocess.run([ROOT / "launcher.sh", "--test-arg"], cwd=directory, env=env, check=True)

            self.assertEqual(args_file.read_text().splitlines(), [str(ROOT / "launcher.py"), "--test-arg"])
            self.assertEqual(env_file.read_text().splitlines(), ["unset", "unset"])


if __name__ == "__main__":
    unittest.main()
