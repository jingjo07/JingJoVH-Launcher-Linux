import os
import stat
import tempfile
import unittest
from unittest import mock

from backend import wuwa_game as game


class NtePerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.prefix = os.path.join(self.temp.name, "prefix")
        self.root = os.path.join(self.prefix, "drive_c", "Program Files", "Neverness To Everness")
        os.makedirs(self.root)
        self.config_dir = os.path.join(
            self.prefix, "drive_c", "users", "steamuser", "AppData", "Local", "HT", "Saved_Global", "Config", "Windows"
        )
        os.makedirs(self.config_dir)
        self.config_patch = mock.patch.object(game, "CONFIG_PATH", os.path.join(self.temp.name, "launcher-config.json"))
        self.config_patch.start()
        game._invalidate_config_cache()
        self.path_patch = mock.patch("backend.nte.detect_game_path", return_value=self.root)
        self.path_patch.start()

    def tearDown(self):
        self.path_patch.stop()
        self.config_patch.stop()
        game._invalidate_config_cache()
        self.temp.cleanup()

    def test_config_directory_is_resolved_from_wine_prefix(self):
        from backend import nte_performance

        self.assertEqual(nte_performance.get_config_dir(), self.config_dir)

    def test_heroic_global_epic_config_is_resolved_from_separate_prefix(self):
        from backend import nte_performance

        prefix = os.path.join(self.temp.name, "separate-prefix")
        config_dir = os.path.join(
            prefix, "drive_c", "users", "steamuser", "AppData", "Local", "HT", "Saved_GlobalEpic", "Config", "Windows"
        )
        os.makedirs(config_dir)
        with mock.patch("backend.nte.detect_prefix_path", return_value=prefix):
            self.assertEqual(nte_performance.get_config_dir(), config_dir)

    def test_apply_preset_backs_up_and_makes_files_read_only(self):
        from backend import nte_performance, nte_presets_data

        engine = os.path.join(self.config_dir, "Engine.ini")
        with open(engine, "w", encoding="utf-8") as output:
            output.write("original")

        result = nte_performance.apply_preset("config-3", {"input": True})

        self.assertEqual(result["preset"], "config-3")
        with open(engine, encoding="utf-8") as installed, open(engine + ".wuwavh_bak", encoding="utf-8") as backup:
            self.assertEqual(installed.read(), nte_presets_data.PRESETS["config-3"])
            self.assertEqual(backup.read(), "original")
        self.assertFalse(os.stat(engine).st_mode & stat.S_IWUSR)
        self.assertTrue(os.path.isfile(os.path.join(self.config_dir, "Input.ini")))

    def test_restore_returns_original_and_removes_launcher_created_files(self):
        from backend import nte_performance

        engine = os.path.join(self.config_dir, "Engine.ini")
        with open(engine, "w", encoding="utf-8") as output:
            output.write("original")

        nte_performance.apply_preset("config-5", {"game": True})
        nte_performance.restore()

        with open(engine, encoding="utf-8") as restored:
            self.assertEqual(restored.read(), "original")
        self.assertFalse(os.path.exists(os.path.join(self.config_dir, "Game.ini")))

    def test_unknown_preset_is_rejected(self):
        from backend import nte_performance

        with self.assertRaisesRegex(ValueError, "preset"):
            nte_performance.apply_preset("ultra-future")

    def test_applied_preset_and_common_choices_are_persisted(self):
        from backend import nte_performance

        nte_performance.apply_preset("config-4", {"device_profiles": True, "game": False, "input": True})
        game._invalidate_config_cache()

        settings = nte_performance.get_settings()
        self.assertEqual(settings["preset"], "config-4")
        self.assertEqual(settings["common"], ["device_profiles", "input"])

    def test_unchecked_common_choice_restores_the_original_file(self):
        from backend import nte_performance

        game_ini = os.path.join(self.config_dir, "Game.ini")
        with open(game_ini, "w", encoding="utf-8") as output:
            output.write("original-game")
        nte_performance.apply_preset("config-3", {"game": True})

        nte_performance.apply_preset("config-3", {"game": False})

        with open(game_ini, encoding="utf-8") as restored:
            self.assertEqual(restored.read(), "original-game")
        self.assertEqual(nte_performance.get_settings()["common"], [])


if __name__ == "__main__":
    unittest.main()
