import tempfile
import unittest
from unittest import mock

from backend import wuwa_game as game


class GameContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_path = f"{self.temp.name}/config.json"
        self.config_patch = mock.patch.object(game, "CONFIG_PATH", self.config_path)
        self.config_patch.start()
        game._invalidate_config_cache()

    def tearDown(self):
        self.config_patch.stop()
        game._invalidate_config_cache()
        self.temp.cleanup()

    def test_existing_config_defaults_to_wuwa(self):
        from backend import game_context

        game.save_config({"theme": "modern", "game_path": "/games/wuwa"})

        self.assertEqual(game_context.get_active_game_id(), "wuwa")
        self.assertIs(game_context.active_game(), game)

    def test_selection_persists_without_changing_wuwa_settings(self):
        from backend import game_context

        game.save_config({"theme": "cyber", "game_path": "/games/wuwa"})

        result = game_context.set_active_game("nte")

        self.assertEqual(result, {"game": "nte"})
        self.assertEqual(game_context.get_active_game_id(), "nte")
        self.assertEqual(game.load_config()["theme"], "cyber")
        self.assertEqual(game.load_config()["game_path"], "/games/wuwa")

    def test_invalid_game_id_is_rejected(self):
        from backend import game_context

        with self.assertRaisesRegex(ValueError, "không hỗ trợ"):
            game_context.set_active_game("unknown")

    def test_status_is_dispatched_only_to_active_game(self):
        from backend import game_context

        game_context.set_active_game("nte")
        with mock.patch.object(game_context.GAMES["nte"], "get_status", return_value={"game": "nte"}) as nte_status, mock.patch.object(
            game_context.GAMES["wuwa"], "get_status"
        ) as wuwa_status:
            self.assertEqual(game_context.get_status(), {"game": "nte"})

        nte_status.assert_called_once_with()
        wuwa_status.assert_not_called()

    def test_prefix_path_is_available_only_for_nte(self):
        from backend import game_context

        game_context.set_active_game("nte")
        with mock.patch.object(game_context.GAMES["nte"], "set_prefix_path", return_value={"ok": True}) as setter:
            self.assertEqual(game_context.set_prefix_path("/prefix"), {"ok": True})
        setter.assert_called_once_with("/prefix")

        game_context.set_active_game("wuwa")
        with self.assertRaisesRegex(ValueError, "prefix"):
            game_context.set_prefix_path("/prefix")

    def test_theme_dispatch_and_separation(self):
        from backend import game_context, nte

        game_context.set_active_game("wuwa")
        game_context.set_theme("dangdev")
        self.assertEqual(game_context.get_theme(), "dangdev")
        self.assertEqual(game.get_theme(), "dangdev")
        self.assertEqual(nte.get_theme(), "cyber")

        game_context.set_active_game("nte")
        self.assertEqual(game_context.get_theme(), "cyber")
        game_context.set_theme("cyber")
        self.assertEqual(game_context.get_theme(), "cyber")
        self.assertEqual(nte.get_theme(), "cyber")
        self.assertEqual(game.get_theme(), "dangdev")

    def test_install_wine_dll_overrides_dispatches_to_active_game(self):
        from backend import game_context

        game_context.set_active_game("nte")
        with mock.patch.object(game_context.GAMES["nte"], "install_wine_dll_overrides", return_value={"ok": True, "count": 1}) as nte_ov:
            res = game_context.install_wine_dll_overrides()
            self.assertTrue(res.get("ok"))
        nte_ov.assert_called_once_with()

    def test_launcher_selection_dispatches_to_active_game(self):
        from backend import game_context

        game_context.set_active_game("nte")
        selected = game_context.GAMES["nte"]
        with mock.patch.object(selected, "get_launcher_info", return_value={"current": "official"}) as getter, mock.patch.object(
            selected, "set_preferred_launcher", return_value={"current": "heroic"}
        ) as setter:
            self.assertEqual(game_context.get_launcher_info(), {"current": "official"})
            self.assertEqual(game_context.set_preferred_launcher("heroic"), {"current": "heroic"})

        getter.assert_called_once_with()
        setter.assert_called_once_with("heroic")

    def test_font_management_dispatches_to_active_game(self):
        from backend import game_context

        game_context.set_active_game("nte")
        selected = game_context.GAMES["nte"]
        with mock.patch.object(selected, "get_font_status", return_value={"active_font": "custom"}) as status, mock.patch.object(
            selected, "install_custom_font", return_value={"font_name": "NTE Font"}
        ) as install:
            self.assertEqual(game_context.get_font_status()["active_font"], "custom")
            self.assertEqual(game_context.install_custom_font("/font.ttf")["font_name"], "NTE Font")

        status.assert_called_once_with()
        install.assert_called_once_with("/font.ttf")


if __name__ == "__main__":
    unittest.main()
