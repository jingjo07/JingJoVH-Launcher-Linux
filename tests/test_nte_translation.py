import io
import json
import os
import tempfile
import unittest
import zipfile
from unittest import mock

from backend import wuwa_game as game, nte


def make_archive(files=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for relative in files or nte.MANAGED_FILES:
            archive.writestr(relative, relative.encode())
    return output.getvalue()


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class NteTranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config_patch = mock.patch.object(game, "CONFIG_PATH", os.path.join(self.temp.name, "config.json"))
        self.config_patch.start()
        game._invalidate_config_cache()
        self.root = os.path.join(self.temp.name, "NTE")
        exe = os.path.join(self.root, nte.EXE_RELATIVE_PATHS[0])
        os.makedirs(os.path.dirname(exe), exist_ok=True)
        open(exe, "wb").close()
        nte.set_game_path(self.root)

    def tearDown(self):
        self.config_patch.stop()
        game._invalidate_config_cache()
        self.temp.cleanup()

    def test_version_info_validates_and_normalizes_version(self):
        from backend import nte_downloader

        payload = json.dumps({"version": "v1.4.0", "date": "30/09/2026", "note": "NTE"}).encode()
        with mock.patch.object(nte_downloader.urllib.request, "urlopen", return_value=Response(payload)):
            info = nte_downloader.get_version_info()

        self.assertEqual(info["version"], "1.4.0")

    def test_install_uses_verified_box_provider_and_exact_archive_members(self):
        from backend import nte_downloader

        archive_data = make_archive()

        def download(url, destination, progress):
            with open(destination, "wb") as output:
                output.write(archive_data)

        with mock.patch.object(nte_downloader.downloader, "mint_href", return_value="https://signed.example/nte") as mint, mock.patch.object(
            nte_downloader.downloader, "download_file", side_effect=download
        ):
            result = nte_downloader.install("v1.4.0")

        mint.assert_called_once_with("mod", "1.4.0", box="NTEVH")
        self.assertEqual(set(result["installed"]), set(nte.MANAGED_FILES))
        for relative in nte.MANAGED_FILES:
            self.assertTrue(os.path.isfile(os.path.join(self.root, "Client", "WindowsNoEditor", relative)))
        self.assertEqual(game.load_config()["nte_vh_version"], "1.4.0")

    def test_install_rejects_unexpected_archive_member(self):
        from backend import nte_downloader

        archive_data = make_archive([*nte.MANAGED_FILES, "../../outside.dll"])

        def download(url, destination, progress):
            with open(destination, "wb") as output:
                output.write(archive_data)

        with mock.patch.object(nte_downloader.downloader, "mint_href", return_value="https://signed.example/nte"), mock.patch.object(
            nte_downloader.downloader, "download_file", side_effect=download
        ):
            with self.assertRaisesRegex(RuntimeError, "không hợp lệ"):
                nte_downloader.install("1.4.0")

        self.assertFalse(os.path.exists(os.path.join(self.temp.name, "outside.dll")))

    def test_install_failure_restores_previous_files(self):
        from backend import nte_downloader

        content_root = os.path.join(self.root, "Client", "WindowsNoEditor")
        first = os.path.join(content_root, nte.MANAGED_FILES[0])
        os.makedirs(os.path.dirname(first), exist_ok=True)
        with open(first, "wb") as output:
            output.write(b"old")

        archive_data = make_archive()

        def download(url, destination, progress):
            with open(destination, "wb") as output:
                output.write(archive_data)

        real_replace = os.replace

        def fail_on_second_staged_file(source, destination):
            if f"{os.sep}stage{os.sep}" in source and destination.endswith(nte.MANAGED_FILES[1]):
                raise OSError("disk failure")
            return real_replace(source, destination)

        with mock.patch.object(nte_downloader.downloader, "mint_href", return_value="https://signed.example/nte"), mock.patch.object(
            nte_downloader.downloader, "download_file", side_effect=download
        ), mock.patch.object(nte_downloader.os, "replace", side_effect=fail_on_second_staged_file):
            with self.assertRaisesRegex(OSError, "disk failure"):
                nte_downloader.install("1.4.0")

        with open(first, "rb") as restored:
            self.assertEqual(restored.read(), b"old")
        self.assertFalse(os.path.exists(os.path.join(content_root, nte.MANAGED_FILES[1])))
        self.assertIsNone(game.load_config().get("nte_vh_version"))

    def test_uninstall_removes_only_allowlisted_files(self):
        from backend import nte_downloader

        content_root = os.path.join(self.root, "Client", "WindowsNoEditor")
        for relative in nte.MANAGED_FILES:
            path = os.path.join(content_root, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").close()
        unrelated = os.path.join(content_root, "HT", "Content", "Paks", "keep-me.pak")
        open(unrelated, "wb").close()

        removed = nte_downloader.uninstall()

        self.assertEqual(set(removed), set(nte.MANAGED_FILES))
        self.assertTrue(os.path.isfile(unrelated))


if __name__ == "__main__":
    unittest.main()
