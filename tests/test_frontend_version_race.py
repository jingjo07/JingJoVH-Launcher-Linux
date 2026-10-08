import subprocess
import unittest
from pathlib import Path


APP_JS = Path(__file__).parents[1] / "frontend/app.js"


class FrontendVersionRaceTests(unittest.TestCase):
    def test_old_game_version_response_is_ignored(self):
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("async function loadVersion() {")
        end = app.index("// ── Status check", start)
        function = app[start:end]
        script = f"""
            const assert = require('node:assert/strict');
            let activeGameId = 'wuwa';
            let serverInfo = null;
            const pending = [];
            const ipc = () => new Promise(resolve => pending.push(resolve));
            const document = {{getElementById: () => null}};
            const updateVhVersionUI = () => {{}};
            {function}
            (async () => {{
                const oldRequest = loadVersion();
                activeGameId = 'nte';
                const newRequest = loadVersion();
                pending[0]({{version: 'old', game: 'wuwa'}});
                await oldRequest;
                assert.equal(serverInfo, null);
                pending[1]({{version: 'new', game: 'nte'}});
                await newRequest;
                assert.equal(serverInfo.version, 'new');
            }})().catch(error => {{console.error(error); process.exitCode = 1}});
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
