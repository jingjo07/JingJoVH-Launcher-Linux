import os
import json
import tempfile
import unittest
from unittest import mock

from backend import game_context, wuwa_game


class WuwaGamePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp.name, "config.json")
        self.config_patch = mock.patch.object(wuwa_game, "CONFIG_PATH", self.config_path)
        self.config_patch.start()
        wuwa_game._invalidate_config_cache()

    def tearDown(self):
        self.config_patch.stop()
        wuwa_game._invalidate_config_cache()
        self.temp.cleanup()

    def _create_mock_wuwa_install(self, parent_name="Wuthering Waves", inner_name="Wuthering Waves Game"):
        outer = os.path.join(self.temp.name, parent_name)
        inner = os.path.join(outer, inner_name)
        bin_dir = os.path.join(inner, "Client", "Binaries", "Win64")
        os.makedirs(bin_dir, exist_ok=True)
        exe_path = os.path.join(bin_dir, wuwa_game.GAME_EXE_NAME)
        open(exe_path, "w").close()
        # Also create Engine folder
        os.makedirs(os.path.join(inner, "Engine"), exist_ok=True)
        return outer, inner, exe_path

    def test_resolve_from_inner_folder(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        self.assertEqual(wuwa_game.resolve_game_root(inner), inner)

    def test_resolve_from_outer_steam_folder(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        # Pointing to Steam's outer folder should resolve to the folder directly containing Client/
        self.assertEqual(wuwa_game.resolve_game_root(outer), inner)

    def test_resolve_from_executable_path(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        self.assertEqual(wuwa_game.resolve_game_root(exe_path), inner)

    def test_resolve_from_subfolder(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        sub = os.path.join(inner, "Client", "Binaries", "Win64")
        self.assertEqual(wuwa_game.resolve_game_root(sub), inner)

    def test_resolve_with_quotes_and_whitespace(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        quoted = f'  "{outer}"  '
        self.assertEqual(wuwa_game.resolve_game_root(quoted), inner)

    def test_set_game_path_resolves_and_persists(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        res = wuwa_game.set_game_path(outer)
        self.assertEqual(res, {"ok": True, "path": inner})
        self.assertEqual(wuwa_game.load_config().get("game_path"), inner)
        self.assertEqual(wuwa_game.detect_game_path(), inner)

    def test_game_context_routes_set_game_path_correctly(self):
        outer, inner, exe_path = self._create_mock_wuwa_install()
        game_context.set_active_game("wuwa")
        res = game_context.set_game_path(outer)
        self.assertEqual(res, {"ok": True, "path": inner})
        status = game_context.get_status()
        self.assertEqual(status["game_path"], inner)
        self.assertTrue(status["has_game"])

    def test_detect_game_path_resolves_steam_candidate(self):
        steamapps_common = os.path.join(self.temp.name, "steamapps", "common")
        outer = os.path.join(steamapps_common, "Wuthering Waves")
        inner = os.path.join(outer, "Wuthering Waves Game")
        bin_dir = os.path.join(inner, "Client", "Binaries", "Win64")
        os.makedirs(bin_dir, exist_ok=True)
        open(os.path.join(bin_dir, wuwa_game.GAME_EXE_NAME), "w").close()
        os.makedirs(os.path.join(inner, "Engine"), exist_ok=True)

        steam_lib = os.path.join(self.temp.name, "libraryfolders.vdf")
        lib_root = self.temp.name

        with open(steam_lib, "w", encoding="utf-8") as f:
            f.write(f'"libraryfolders"\n{{\n  "0"\n  {{\n    "path"    "{lib_root}"\n  }}\n}}\n')

        with mock.patch("backend.wuwa_game.DEFAULT_SEARCH_PATHS", []):
            with mock.patch("os.path.expanduser", side_effect=lambda p: steam_lib if "libraryfolders.vdf" in p else p):
                detected = wuwa_game._detect_game_path_uncached()
                self.assertEqual(detected, inner)


if __name__ == "__main__":
    unittest.main()
