import base64
import json
import os
import struct
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from backend import wuwa_game


class NteFontTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_patch = mock.patch.object(
            wuwa_game, "CONFIG_PATH", os.path.join(self.temp.name, "config.json")
        )
        self.config_patch.start()
        wuwa_game._invalidate_config_cache()

        self.root = os.path.join(self.temp.name, "NTE")
        self.pak_dir = os.path.join(
            self.root, "Client", "WindowsNoEditor", "HT", "Content", "Paks"
        )
        os.makedirs(self.pak_dir)
        self.repak = os.path.join(self.temp.name, "repak")
        with open(self.repak, "w", encoding="utf-8") as output:
            output.write(
                "#!/usr/bin/env python3\n"
                "import json, os, shutil, sys\n"
                "command = sys.argv[1]\n"
                "if command == 'pack':\n"
                "    source, target = sys.argv[-2:]\n"
                "    entries = {}\n"
                "    for base, _, files in os.walk(source):\n"
                "        for name in files:\n"
                "            path = os.path.join(base, name)\n"
                "            relative = os.path.relpath(path, source).replace(os.sep, '/')\n"
                "            entries[relative] = open(path, 'rb').read().hex()\n"
                "    open(target, 'w').write(json.dumps(entries))\n"
                "elif command == 'list':\n"
                "    print('\\n'.join(json.load(open(sys.argv[-1])).keys()))\n"
                "elif command == 'get':\n"
                "    sys.stdout.buffer.write(bytes.fromhex(json.load(open(sys.argv[-2]))[sys.argv[-1]]))\n"
                "elif command == 'unpack':\n"
                "    source, target = sys.argv[-1], sys.argv[sys.argv.index('-o') + 1]\n"
                "    for relative, data in json.load(open(source)).items():\n"
                "        path = os.path.join(target, *relative.split('/'))\n"
                "        os.makedirs(os.path.dirname(path), exist_ok=True)\n"
                "        open(path, 'wb').write(bytes.fromhex(data))\n"
            )
        os.chmod(self.repak, 0o755)

    def tearDown(self):
        self.config_patch.stop()
        wuwa_game._invalidate_config_cache()
        self.temp.cleanup()

    def _patch_game(self):
        from backend import nte, nte_font

        return mock.patch.multiple(
            nte,
            detect_game_path=mock.DEFAULT,
            is_game_running=mock.DEFAULT,
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak)

    def _write_translation_pak(self):
        from backend import nte_font

        original_font = b"\x00\x01\x00\x00" + b"original-font-data"
        original_ufont = struct.pack("<I", len(original_font)) + original_font + b"\0\0\0\0"
        entries = {path: original_ufont.hex() for path in nte_font.FONT_ASSET_PATHS}
        entries["HT/Content/Localization/Game/en/game.locres"] = b"translation-data".hex()
        path = os.path.join(self.pak_dir, nte_font.TRANSLATION_PAK_NAME)
        with open(path, "w", encoding="utf-8") as output:
            json.dump(entries, output)
        return path, entries

    def test_ttf_install_creates_override_pak_and_leaves_translation_intact(self):
        from backend import nte, nte_font

        target, original_entries = self._write_translation_pak()
        font = os.path.join(self.temp.name, "My Font.ttf")
        font_data = b"\x00\x01\x00\x00" + b"valid-font-data" * 2
        with open(font, "wb") as output:
            output.write(font_data)

        game_patch, repak_patch = self._patch_game()
        with game_patch as game, repak_patch:
            game["detect_game_path"].return_value = self.root
            game["is_game_running"].return_value = False
            result = nte_font.install_custom_font(font)
            preview = nte_font.get_font_preview()

        # Translation pak must be completely intact and untouched!
        with open(target, encoding="utf-8") as source:
            entries = json.load(source)
        self.assertEqual(entries, original_entries)

        # Custom font override pak must exist and contain only the font assets
        override_pak = os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)
        self.assertTrue(os.path.isfile(override_pak))
        with open(override_pak, encoding="utf-8") as source:
            override_entries = json.load(source)
        self.assertEqual(set(override_entries), set(nte_font.FONT_ASSET_PATHS))

        expected = struct.pack("<I", len(font_data)) + font_data + b"\0\0\0\0"
        self.assertTrue(
            all(bytes.fromhex(override_entries[path]) == expected for path in nte_font.FONT_ASSET_PATHS)
        )
        self.assertEqual(result["font_name"], "My Font")
        self.assertEqual(result["pak_file"], nte_font.CUSTOM_FONT_PAK_NAME)
        self.assertEqual(base64.b64decode(preview["data"]), font_data)
        self.assertEqual(preview["mime"], "font/ttf")

    def test_restore_removes_override_pak(self):
        from backend import nte, nte_font

        translation, original_entries = self._write_translation_pak()
        font = os.path.join(self.temp.name, "My Font.ttf")
        with open(font, "wb") as output:
            output.write(b"\x00\x01\x00\x00" + b"custom-font-data")

        with mock.patch.object(nte, "detect_game_path", return_value=self.root), mock.patch.object(
            nte, "is_game_running", return_value=False
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak):
            nte_font.install_custom_font(font)
            self.assertTrue(os.path.isfile(os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)))
            result = nte_font.install_default_font()

        self.assertFalse(os.path.exists(os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)))
        with open(translation, encoding="utf-8") as source:
            self.assertEqual(json.load(source), original_entries)
        self.assertEqual(result["font_name"], "MiSans (Mặc định NTE)")

    def test_otf_is_converted_to_truetype_before_patching(self):
        from backend import nte, nte_font

        translation, _ = self._write_translation_pak()
        font = os.path.join(self.temp.name, "CFF Font.ttf")
        converted = b"\x00\x01\x00\x00" + b"converted-font-data"
        with open(font, "wb") as output:
            output.write(b"OTTO" + b"cff-font-data" * 2)

        with mock.patch.object(nte, "detect_game_path", return_value=self.root), mock.patch.object(
            nte, "is_game_running", return_value=False
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak), mock.patch.object(
            nte_font, "_convert_cff_to_ttf", return_value=converted
        ):
            nte_font.install_custom_font(font)
            preview = nte_font.get_font_preview()

        override_pak = os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)
        with open(override_pak, encoding="utf-8") as source:
            entries = json.load(source)
        expected = struct.pack("<I", len(converted)) + converted + b"\0\0\0\0"
        self.assertTrue(
            all(bytes.fromhex(entries[path]) == expected for path in nte_font.FONT_ASSET_PATHS)
        )
        self.assertEqual(base64.b64decode(preview["data"]), converted)
        self.assertEqual(preview["mime"], "font/ttf")

    def test_import_rejects_pak_with_non_font_entries(self):
        from backend import nte, nte_font

        source_pak = os.path.join(self.temp.name, "unsafe.pak")
        with open(source_pak, "w", encoding="utf-8") as output:
            json.dump({"HT/Content/Localization/Game/en/game.locres": "00"}, output)

        with mock.patch.object(nte, "detect_game_path", return_value=self.root), mock.patch.object(
            nte, "is_game_running", return_value=False
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak):
            with self.assertRaisesRegex(ValueError, "font NTE"):
                nte_font.install_font_from_pak(source_pak)

        self.assertFalse(os.path.exists(os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)))

    def test_imported_nte_font_pak_is_previewed(self):
        from backend import nte, nte_font

        self._write_translation_pak()
        font_data = b"\x00\x01\x00\x00" + b"imported-font-data" * 2
        ufont_data = struct.pack("<I", len(font_data)) + font_data + b"\0\0\0\0"
        source_pak = os.path.join(self.temp.name, "Imported Font.pak")
        with open(source_pak, "w", encoding="utf-8") as output:
            json.dump({path: ufont_data.hex() for path in nte_font.FONT_ASSET_PATHS}, output)

        with mock.patch.object(nte, "detect_game_path", return_value=self.root), mock.patch.object(
            nte, "is_game_running", return_value=False
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak):
            nte_font.install_font_from_pak(source_pak)
            preview = nte_font.get_font_preview()

        self.assertEqual(base64.b64decode(preview["data"]), font_data)
        self.assertEqual(preview["mime"], "font/ttf")

    def test_import_rejects_invalid_font_payload_before_install(self):
        from backend import nte, nte_font

        self._write_translation_pak()
        font_data = b"\x00\x01\x00\x00" + b"valid-font-data"
        valid = (struct.pack("<I", len(font_data)) + font_data + b"\0\0\0\0").hex()
        payloads = {path: valid for path in nte_font.FONT_ASSET_PATHS}
        payloads[nte_font.FONT_ASSET_PATHS[1]] = b"not-a-font-payload".hex()
        source_pak = os.path.join(self.temp.name, "broken-font.pak")
        with open(source_pak, "w", encoding="utf-8") as output:
            json.dump(payloads, output)

        with mock.patch.object(nte, "detect_game_path", return_value=self.root), mock.patch.object(
            nte, "is_game_running", return_value=False
        ), mock.patch.object(nte_font, "_find_repak", return_value=self.repak):
            with self.assertRaisesRegex(ValueError, "dữ liệu font"):
                nte_font.install_font_from_pak(source_pak)

        self.assertFalse(os.path.exists(os.path.join(self.pak_dir, nte_font.CUSTOM_FONT_PAK_NAME)))

    def test_appimage_build_bundles_repak(self):
        build = (Path(__file__).parents[1] / "build_appimage.sh").read_text(encoding="utf-8")

        self.assertIn('REPAK_BIN', build)
        self.assertIn('$APP_DIR/usr/bin/repak', build)
        self.assertIn('fontTools', build)


if __name__ == "__main__":
    unittest.main()
