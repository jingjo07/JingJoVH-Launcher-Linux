import os
import ssl
import tempfile
import unittest
from unittest import mock

from backend import downloader, wuwa_game


class DownloaderTlsTests(unittest.TestCase):
    def test_bad_certificate_never_retries_without_verification(self):
        with tempfile.TemporaryDirectory() as home, mock.patch.dict(os.environ, {"HOME": home}), mock.patch.object(
            downloader, "VERSION_MIRRORS", ["https://example.invalid/version.json"]
        ), mock.patch.object(
            downloader.urllib.request, "urlopen", side_effect=ssl.SSLCertVerificationError("bad certificate")
        ) as fetch, mock.patch.object(wuwa_game, "get_vh_version", return_value=None):
            downloader.get_version_info()

        self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
