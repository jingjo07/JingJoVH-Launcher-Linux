import unittest
from unittest import mock

import launcher


class NteProgressTests(unittest.TestCase):
    def test_progress_is_throttled_but_completion_is_reported(self):
        ipc = launcher.IPC(None)
        events = []
        ipc.emit = lambda event, data: events.append((event, data))

        def install(version, progress):
            for done in (10, 20, 40, 100):
                progress(done, 100)
            return {"installed": [], "font_reapplied": False}

        with mock.patch("backend.nte_downloader.get_version_info", return_value={"version": "1.0"}), mock.patch(
            "backend.nte_downloader.install", side_effect=install
        ), mock.patch.object(launcher.time, "monotonic", side_effect=(0, 0.1, 0.2, 0.4, 0.41)):
            ipc._do_update_nte()

        self.assertEqual([data["progress"] for event, data in events if event == "update_progress"], [0.4, 1.0])
        self.assertEqual(events[-1][0], "update_done")


if __name__ == "__main__":
    unittest.main()
