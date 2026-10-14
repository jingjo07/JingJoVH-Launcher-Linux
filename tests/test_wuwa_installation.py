import os
import json
import tempfile
import unittest
from unittest import mock

from backend import wuwa_game


class WuwaInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game = os.path.join(self.temp.name, "game")
        self.source = os.path.join(self.temp.name, "source")
        os.makedirs(self.source)
        self.pak_dir = os.path.join(self.game, wuwa_game.PAK_SUBPATH)
        os.makedirs(self.pak_dir)
        self.config = mock.patch.object(wuwa_game, "CONFIG_PATH", os.path.join(self.temp.name, "config.json"))
        self.path = mock.patch.object(wuwa_game, "detect_game_path", return_value=self.game)
        self.bundled = mock.patch.object(wuwa_game, "get_bundled_paks_dir", return_value=self.source)
        for patch in (self.config, self.path, self.bundled):
            patch.start()
        wuwa_game._invalidate_config_cache()

    def tearDown(self):
        for patch in (self.bundled, self.path, self.config):
            patch.stop()
        wuwa_game._invalidate_config_cache()
        self.temp.cleanup()

    def test_uninstall_preserves_font_and_unrelated_paks(self):
        names = ("WuWaVH_99_P.pak", "zzz_CustomFont_99_P.pak", "another_mod_99_P.pak")
        for name in names:
            with open(os.path.join(self.pak_dir, name), "wb") as output:
                output.write(name.encode())

        removed = wuwa_game.uninstall_paks()

        self.assertEqual(removed, ["WuWaVH_99_P.pak"])
        self.assertFalse(os.path.exists(os.path.join(self.pak_dir, names[0])))
        for name in names[1:]:
            self.assertTrue(os.path.isfile(os.path.join(self.pak_dir, name)))

    def test_font_alone_does_not_count_as_translation(self):
        with open(os.path.join(self.pak_dir, "zzz_CustomFont_99_P.pak"), "wb") as output:
            output.write(b"font")
        with mock.patch.object(wuwa_game, "is_game_running", return_value=False), mock.patch.object(
            wuwa_game, "get_launcher_info", return_value={}
        ):
            status = wuwa_game.get_status()
        self.assertFalse(status["installed_vh"])
        self.assertEqual(status["installed_paks"], [])

    def test_heroic_sync_removes_legacy_csharp_flag(self):
        heroic_root = os.path.join(self.temp.name, "heroic")
        games_dir = os.path.join(heroic_root, "GamesConfig")
        os.makedirs(games_dir)
        config_path = os.path.join(games_dir, "wuwa.json")
        with open(config_path, "w", encoding="utf-8") as output:
            json.dump({
                "wuwa": {"launcherArgs": "--foo -ForceEnableCSharpEnvironment --bar"},
                "other-game": {"launcherArgs": "-ForceEnableCSharpEnvironment"},
            }, output)

        original_expanduser = os.path.expanduser
        def heroic_path(path):
            if path == "~/.config/heroic":
                return heroic_root
            if path == "~/.var/app/com.heroicgameslauncher.hgl/config/heroic":
                return os.path.join(self.temp.name, "missing-heroic")
            return original_expanduser(path)

        with mock.patch.object(wuwa_game.os.path, "expanduser", side_effect=heroic_path), mock.patch.object(
            wuwa_game, "get_dx11_mode", return_value=False
        ), mock.patch.object(wuwa_game, "get_required_dll_overrides", return_value="winhttp=n,b"), mock.patch.object(
            wuwa_game, "detect_heroic_game", return_value={"app_name": "wuwa"}
        ):
            wuwa_game.optimize_heroic_config()

        with open(config_path, encoding="utf-8") as source:
            config = json.load(source)
        self.assertEqual(config["wuwa"]["launcherArgs"], "--foo --bar")
        self.assertEqual(config["other-game"]["launcherArgs"], "-ForceEnableCSharpEnvironment")

    def test_steam_launch_ignores_saved_csharp_setting(self):
        wuwa_game.save_config({"use_csharp_env": True})
        with mock.patch.object(wuwa_game, "get_launcher_info", return_value={"current": "steam"}), mock.patch.object(
            wuwa_game, "get_game_exe", return_value="/games/Wuwa/Client-Win64-Shipping.exe"
        ), mock.patch.object(wuwa_game, "fix_steam_launch_options"), mock.patch.object(
            wuwa_game.subprocess, "Popen"
        ) as popen:
            self.assertTrue(wuwa_game.launch_game())

        self.assertEqual(popen.call_args.args[0], ["steam", "-silent", "-applaunch", wuwa_game.STEAM_APP_ID, "-dx11"])

    def test_failed_copy_preserves_installed_pak(self):
        name = "WuWaVH_99_P.pak"
        source = os.path.join(self.source, name)
        target = os.path.join(self.pak_dir, name)
        with open(source, "wb") as output:
            output.write(b"new translation")
        with open(target, "wb") as output:
            output.write(b"old translation")

        def fail_during_copy(src, dst):
            with open(dst, "wb") as output:
                output.write(b"partial")
            raise OSError("disk full")

        with mock.patch.object(wuwa_game.shutil, "copy2", side_effect=fail_during_copy):
            with self.assertRaisesRegex(OSError, "disk full"):
                wuwa_game.install_paks(self.source)

        with open(target, "rb") as installed:
            self.assertEqual(installed.read(), b"old translation")

    def test_install_does_not_copy_unrelated_paks_from_cache(self):
        for name in ("WuWaVH_99_P.pak", "another_mod_99_P.pak"):
            with open(os.path.join(self.source, name), "wb") as output:
                output.write(name.encode())

        installed = wuwa_game.install_paks(self.source)

        self.assertEqual(installed, ["WuWaVH_99_P.pak"])
        self.assertFalse(os.path.exists(os.path.join(self.pak_dir, "another_mod_99_P.pak")))

    def test_uninstall_restores_preexisting_dll(self):
        bin_dir = os.path.join(self.game, "Client", "Binaries", "Win64")
        os.makedirs(bin_dir, exist_ok=True)
        target = os.path.join(bin_dir, "winhttp.dll")
        with open(target, "wb") as output:
            output.write(b"user dll")
        with open(os.path.join(self.source, "winhttp.dll"), "wb") as output:
            output.write(b"launcher dll")

        wuwa_game.install_paks(self.source)
        wuwa_game.uninstall_paks()

        with open(target, "rb") as restored:
            self.assertEqual(restored.read(), b"user dll")

    def test_uninstall_preserves_dll_changed_after_install(self):
        with open(os.path.join(self.source, "winhttp.dll"), "wb") as output:
            output.write(b"launcher dll")
        wuwa_game.install_paks(self.source)
        target = os.path.join(self.game, "Client", "Binaries", "Win64", "winhttp.dll")
        with open(target, "wb") as output:
            output.write(b"new user dll")

        wuwa_game.uninstall_paks()

        with open(target, "rb") as current:
            self.assertEqual(current.read(), b"new user dll")

    def test_updating_existing_translation_does_not_restore_old_launcher_dll(self):
        bin_dir = os.path.join(self.game, "Client", "Binaries", "Win64")
        os.makedirs(bin_dir, exist_ok=True)
        target = os.path.join(bin_dir, "winhttp.dll")
        with open(target, "wb") as output:
            output.write(b"old launcher dll")
        with open(os.path.join(self.source, "winhttp.dll"), "wb") as output:
            output.write(b"new launcher dll")
        wuwa_game.set_vh_version("1.0")

        wuwa_game.install_paks(self.source)
        wuwa_game.uninstall_paks()

        self.assertFalse(os.path.exists(target))


if __name__ == "__main__":
    unittest.main()
