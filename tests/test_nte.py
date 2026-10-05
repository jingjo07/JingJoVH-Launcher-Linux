import os
import json
import tempfile
import unittest
from unittest import mock

from backend import wuwa_game as game


class NteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp.name, "config.json")
        self.config_patch = mock.patch.object(game, "CONFIG_PATH", self.config_path)
        self.config_patch.start()
        game._invalidate_config_cache()

    def tearDown(self):
        self.config_patch.stop()
        game._invalidate_config_cache()
        self.temp.cleanup()

    def make_install(self):
        from backend import nte

        root = os.path.join(self.temp.name, "Neverness To Everness")
        exe = os.path.join(root, nte.EXE_RELATIVE_PATHS[0])
        os.makedirs(os.path.dirname(exe), exist_ok=True)
        open(exe, "wb").close()
        return root, exe

    def make_heroic_install(self):
        from backend import nte

        root, _ = self.make_install()
        prefix = os.path.join(self.temp.name, "Heroic Prefix")
        os.makedirs(os.path.join(prefix, "drive_c"))
        heroic = os.path.join(self.temp.name, "heroic")
        # Heroic/Epic app IDs are opaque hashes and do not identify the game.
        app_id = "b675fd2fd3354d48960f4c1eaa6af466"
        installed = os.path.join(heroic, "legendaryConfig", "legendary")
        games_config = os.path.join(heroic, "GamesConfig")
        os.makedirs(installed)
        os.makedirs(games_config)
        with open(os.path.join(installed, "installed.json"), "w", encoding="utf-8") as output:
            json.dump({app_id: {"title": "NTE: Neverness to Everness", "install_path": root}}, output)
        with open(os.path.join(games_config, f"{app_id}.json"), "w", encoding="utf-8") as output:
            json.dump({app_id: {"winePrefix": prefix}}, output)
        return root, prefix, heroic, app_id

    def make_steam_install(self):
        from backend import nte

        steam_root = os.path.join(self.temp.name, "steam")
        library = os.path.join(self.temp.name, "Steam Library")
        steamapps = os.path.join(library, "steamapps")
        install_dir = "NTE Neverness to Everness"
        root = os.path.join(steamapps, "common", install_dir)
        exe = os.path.join(root, nte.EXE_RELATIVE_PATHS[0])
        prefix = os.path.join(steamapps, "compatdata", nte.STEAM_APP_ID, "pfx")
        os.makedirs(os.path.dirname(exe), exist_ok=True)
        os.makedirs(os.path.join(prefix, "drive_c"))
        os.makedirs(os.path.join(steam_root, "steamapps"))
        open(exe, "wb").close()
        with open(os.path.join(steam_root, "steamapps", "libraryfolders.vdf"), "w", encoding="utf-8") as output:
            output.write(f'"libraryfolders"\n{{\n  "1"\n  {{\n    "path" "{library}"\n  }}\n}}\n')
        with open(os.path.join(steamapps, f"appmanifest_{nte.STEAM_APP_ID}.acf"), "w", encoding="utf-8") as output:
            output.write(f'"AppState"\n{{\n  "appid" "{nte.STEAM_APP_ID}"\n  "name" "NTE: Neverness to Everness"\n  "installdir" "{install_dir}"\n}}\n')
        return root, prefix, steam_root

    def test_reference_contract_uses_safe_managed_paths(self):
        from backend import nte

        self.assertEqual(nte.VERSION_URL, "https://huggingface.co/datasets/BachMacThanh/DangDevVH/raw/main/NTE/version.json")
        self.assertEqual(nte.DOWNLOAD_BOX, "NTEVH")
        self.assertEqual(nte.DOWNLOAD_PROVIDER, "mod")
        self.assertIn("HT/Content/Paks/pakchunk999-Windows_999_P.pak", nte.MANAGED_FILES)
        self.assertEqual(len(nte.MANAGED_FILES), 4)
        for relative in nte.MANAGED_FILES + nte.LEGACY_FILES:
            self.assertFalse(os.path.isabs(relative))
            self.assertNotIn("..", relative.split("/"))

    def test_resolve_game_root_accepts_root_or_nested_folder(self):
        from backend import nte

        root, exe = self.make_install()

        self.assertEqual(nte.resolve_game_root(root), root)
        self.assertEqual(nte.resolve_game_root(os.path.dirname(exe)), root)

    def test_set_game_path_rejects_invalid_folder(self):
        from backend import nte

        with self.assertRaisesRegex(ValueError, "NTE"):
            nte.set_game_path(self.temp.name)

    def test_set_game_path_persists_separately_from_wuwa(self):
        from backend import nte

        root, _ = self.make_install()
        game.save_config({"game_path": "/games/wuwa"})

        nte.set_game_path(root)

        self.assertEqual(game.load_config()["game_path"], "/games/wuwa")
        self.assertEqual(game.load_config()["nte_game_path"], root)
        self.assertEqual(nte.detect_game_path(), root)

    def test_status_reports_ready_nte_without_wuwa_only_features(self):
        from backend import nte

        root, _ = self.make_install()
        nte.set_game_path(root)

        status = nte.get_status()

        self.assertEqual(status["game"], "nte")
        self.assertTrue(status["has_game"])
        self.assertEqual(status["theme"], "cyber")
        self.assertFalse(status["use_csharp_env"])

    def test_launch_uses_wine_for_official_launcher(self):
        from backend import nte

        root, _ = self.make_install()
        launcher = os.path.join(root, "NTEGlobalLauncher.exe")
        open(launcher, "wb").close()
        nte.set_game_path(root)

        with mock.patch.object(nte.shutil, "which", return_value="/usr/bin/wine"), mock.patch.object(nte.subprocess, "Popen") as popen:
            self.assertTrue(nte.launch_game())

        self.assertEqual(popen.call_args.args[0], ["/usr/bin/wine", launcher])
        self.assertEqual(popen.call_args.kwargs["cwd"], root)
        self.assertEqual(popen.call_args.kwargs["env"]["WINEDLLOVERRIDES"], "winhttp=n,b")

    def test_manual_prefix_is_passed_to_wine_fallback(self):
        from backend import nte

        root, _ = self.make_install()
        launcher = os.path.join(root, "NTEGlobalLauncher.exe")
        open(launcher, "wb").close()
        prefix = os.path.join(self.temp.name, "manual-prefix")
        os.makedirs(os.path.join(prefix, "drive_c"))
        nte.set_game_path(root)
        nte.set_prefix_path(prefix)

        with mock.patch.object(nte.shutil, "which", return_value="/usr/bin/wine"), mock.patch.object(nte.subprocess, "Popen") as popen:
            self.assertTrue(nte.launch_game())

        self.assertEqual(popen.call_args.kwargs["env"]["WINEPREFIX"], prefix)
        self.assertEqual(popen.call_args.kwargs["env"]["WINEDLLOVERRIDES"], "winhttp=n,b")

    def test_heroic_install_and_separate_prefix_are_detected(self):
        from backend import nte

        root, prefix, heroic, app_id = self.make_heroic_install()
        with mock.patch.object(nte, "HEROIC_CONFIG_PATHS", (heroic,)):
            install = nte.detect_heroic_install()

            self.assertEqual(nte.detect_game_path(), root)
            self.assertEqual(nte.detect_prefix_path(), prefix)
            self.assertEqual(install["app_name"], app_id)

    def test_launch_uses_heroic_protocol_when_install_is_managed_by_heroic(self):
        from backend import nte

        root, _, heroic, app_id = self.make_heroic_install()
        open(os.path.join(root, "NTEGlobalLauncher.exe"), "wb").close()
        with mock.patch.object(nte, "HEROIC_CONFIG_PATHS", (heroic,)), mock.patch.object(
            nte.subprocess, "Popen"
        ) as popen:
            self.assertTrue(nte.launch_game())

        popen.assert_called_once_with(
            ["xdg-open", f"heroic://launch/epic/{app_id}"],
            stdout=nte.subprocess.DEVNULL,
            stderr=nte.subprocess.DEVNULL,
        )

    def test_launcher_preference_can_force_official_launcher(self):
        from backend import nte

        root, _, heroic, _ = self.make_heroic_install()
        launcher = os.path.join(root, "NTEGlobalLauncher.exe")
        open(launcher, "wb").close()
        with mock.patch.object(nte, "HEROIC_CONFIG_PATHS", (heroic,)):
            self.assertEqual(nte.get_launcher_info()["current"], "heroic")
            self.assertEqual(nte.set_preferred_launcher("official")["current"], "official")
            with mock.patch.object(nte.shutil, "which", return_value="/usr/bin/wine"), mock.patch.object(
                nte.subprocess, "Popen"
            ) as popen:
                self.assertTrue(nte.launch_game())

        self.assertEqual(popen.call_args.args[0], ["/usr/bin/wine", launcher])

    def test_steam_library_is_detected_and_can_launch_without_local_game(self):
        from backend import nte

        root, prefix, steam_root = self.make_steam_install()
        with mock.patch.object(nte, "STEAM_ROOTS", (steam_root,)):
            install = nte.detect_steam_install()
            self.assertEqual(install["app_id"], "4508340")
            self.assertEqual(install["game_path"], root)
            self.assertEqual(install["prefix_path"], prefix)
            self.assertEqual(nte.detect_game_path(), root)
            self.assertEqual(nte.detect_prefix_path(), prefix)
            self.assertTrue(nte.get_launcher_info()["steam_has_game"])
            nte.set_preferred_launcher("steam")
            with mock.patch.object(nte.shutil, "which", return_value="/usr/bin/steam"), mock.patch.object(
                nte.subprocess, "Popen"
            ) as popen:
                self.assertTrue(nte.launch_game())

        popen.assert_called_once_with(
            ["/usr/bin/steam", "-silent", "-applaunch", "4508340"],
            stdout=nte.subprocess.DEVNULL,
            stderr=nte.subprocess.DEVNULL,
        )

    def test_manual_prefix_is_validated_and_persisted(self):
        from backend import nte

        prefix = os.path.join(self.temp.name, "prefix")
        os.makedirs(os.path.join(prefix, "drive_c"))

        nte.set_prefix_path(prefix)

        self.assertEqual(game.load_config()["nte_prefix_path"], prefix)
        self.assertEqual(nte.detect_prefix_path(), prefix)

    def test_wine_overrides_update_only_the_detected_heroic_game(self):
        from backend import nte

        _, prefix, heroic, app_id = self.make_heroic_install()
        user_reg = os.path.join(prefix, "user.reg")
        with open(user_reg, "w", encoding="utf-8") as output:
            output.write(
                "WINE REGISTRY Version 2\n\n"
                "[Software\\\\Wine\\\\DllOverrides] 1700000000\n"
                '"winhttp"="builtin"\n'
            )

        unrelated_path = os.path.join(heroic, "GamesConfig", "unrelated.json")
        unrelated = {"unrelated-app": {"enviromentOptions": []}}
        with open(unrelated_path, "w", encoding="utf-8") as output:
            json.dump(unrelated, output)

        with mock.patch.object(nte, "HEROIC_CONFIG_PATHS", (heroic,)), mock.patch.dict(
            os.environ, {"HOME": self.temp.name}
        ):
            result = nte.install_wine_dll_overrides()

        with open(os.path.join(heroic, "GamesConfig", f"{app_id}.json"), encoding="utf-8") as source:
            heroic_game = json.load(source)[app_id]
        with open(unrelated_path, encoding="utf-8") as source:
            unrelated_after = json.load(source)
        with open(user_reg, encoding="utf-8") as source:
            registry = source.read()

        self.assertTrue(result["ok"])
        self.assertEqual(
            heroic_game["enviromentOptions"],
            [{"key": "WINEDLLOVERRIDES", "value": "winhttp=n,b"}],
        )
        self.assertEqual(unrelated_after, unrelated)
        self.assertIn('"winhttp"="native,builtin"', registry)
        self.assertNotIn('"winhttp"="builtin"', registry)
        self.assertNotIn('"dxgi"=', registry)

    def test_status_requires_every_translation_file(self):
        from backend import nte

        root, _ = self.make_install()
        nte.set_game_path(root)
        nte.set_vh_version("1.4.0")
        first = os.path.join(root, "Client", "WindowsNoEditor", nte.MANAGED_FILES[0])
        os.makedirs(os.path.dirname(first), exist_ok=True)
        open(first, "wb").close()

        status = nte.get_status()

        self.assertFalse(status["installed_vh"])


if __name__ == "__main__":
    unittest.main()
