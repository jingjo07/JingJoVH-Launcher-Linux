import os
import tempfile
import unittest
from unittest import mock

import launcher


class UpdateLockTests(unittest.TestCase):
    def test_second_update_is_rejected_while_first_holds_lock(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            launcher, "UPDATE_LOCK_PATH", os.path.join(directory, "update.lock")
        ):
            ipc = launcher.IPC(None)
            events = []
            ipc.emit = lambda event, data: events.append((event, data))
            ran = []

            def first_update():
                ipc._run_update(lambda: ran.append("second"), "update_error")
                ran.append("first")

            ipc._run_update(first_update, "update_error")

        self.assertEqual(ran, ["first"])
        self.assertEqual(events[0][0], "update_error")
        self.assertIn("đang chạy", events[0][1]["error"])


if __name__ == "__main__":
    unittest.main()
