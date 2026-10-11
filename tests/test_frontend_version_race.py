import subprocess
import unittest
from pathlib import Path


APP_JS = Path(__file__).parents[1] / "frontend/app.js"


class FrontendVersionRaceTests(unittest.TestCase):
    def test_pending_audio_autoplay_cannot_override_user_pause(self):
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("  const tryPlay = () => {")
        end = app.index('  audio.addEventListener("canplay"', start)
        function = app[start:end]
        script = f"""
            const assert = require('node:assert/strict');
            let isMediaPausedByUser = false;
            let finishPlay, pauses = 0, plays = 0, iconUpdates = 0;
            const audio = {{
                play() {{ plays++; return new Promise(resolve => {{ finishPlay = resolve; }}); }},
                pause() {{ pauses++; }}
            }};
            const updateMusicIcons = () => {{ iconUpdates++; }};
            {function}
            (async () => {{
                tryPlay();
                isMediaPausedByUser = true;
                finishPlay();
                await Promise.resolve();
                assert.equal(pauses, 1);
                assert.equal(iconUpdates, 0);
                tryPlay();
                assert.equal(plays, 1);
            }})().catch(error => {{ console.error(error); process.exitCode = 1; }});
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_switch_media_resets_visible_video_after_user_pause(self):
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("function switchMediaForGame(gameId, resume = false) {")
        end = app.index("window.switchMediaForGame =", start)
        function = app[start:end]
        script = f"""
            const assert = require('node:assert/strict');
            class Video {{
                constructor(active = false) {{
                    const classes = new Set(active ? ['active'] : []);
                    this.classList = {{
                        add: name => classes.add(name),
                        remove: (...names) => names.forEach(name => classes.delete(name)),
                        contains: name => classes.has(name),
                    }};
                    this.dataset = {{}};
                    this.plays = 0;
                }}
                pause() {{}}
                play() {{ this.plays++; return Promise.resolve(); }}
                load() {{}}
                removeAttribute() {{}}
                setAttribute() {{}}
            }}
            const vidA = new Video();
            const vidB = new Video(true);
            const audio = {{paused: true, ended: false, dataset: {{}}, plays: 0, load() {{}}, play() {{ this.plays++; return Promise.resolve(); }}}};
            const window = {{}};
            const getMediaSources = game => ({{
                videoPrimary: game + '-video', videoFallback: game + '-fallback',
                audioPrimary: game + '-audio', audioFallback: game + '-audio-fallback'
            }});
            let currentVid = vidB, nextVid = vidA, isTransitioning = true;
            let videoTransitionTimer = null, mediaGeneration = 0;
            let isVideoPausedByFocusOrGame = false, isMediaPausedByUser = true;
            const updateMusicIcons = () => {{}};
            {function}
            switchMediaForGame('nte');
            assert.equal(currentVid, vidA);
            assert.equal(nextVid, vidB);
            assert.equal(isTransitioning, false);
            assert.equal(vidA.classList.contains('active'), true);
            assert.equal(vidB.classList.contains('active'), false);
            assert.equal(vidA.plays + vidB.plays, 0);
            assert.equal(audio.plays, 0);
            assert.equal(audio.src, 'nte-audio');
            switchMediaForGame('wuwa', true);
            assert.equal(isMediaPausedByUser, false);
            assert.equal(vidA.plays, 1);
            assert.equal(vidB.plays, 0);
            assert.equal(audio.plays, 1);
            assert.equal(vidA.src, 'wuwa-video');
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_media_uses_user_copy_then_same_game_bundled_fallback(self):
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("function getMediaSources(gameId) {")
        end = app.index("function switchMediaForGame", start)
        function = app[start:end]
        script = f"""
            const assert = require('node:assert/strict');
            const window = {{ASSETS_DIR: 'file:///user/assets', BUNDLED_ASSETS_DIR: 'file:///bundle/assets'}};
            {function}
            const nte = getMediaSources('nte');
            assert.equal(nte.videoPrimary, 'file:///user/assets/nte-bg-video.mp4');
            assert.equal(nte.videoFallback, 'file:///bundle/assets/nte-bg-video.mp4');
            assert.equal(nte.audioFallback, 'file:///bundle/assets/nte-bgm.mp3');
            const wuwa = getMediaSources('wuwa');
            assert.equal(wuwa.videoFallback, 'file:///bundle/assets/bg-video-720p.mp4');
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("window.BUNDLED_ASSETS_DIR", (APP_JS.parents[1] / "launcher.py").read_text())

    def test_old_game_version_response_is_ignored(self):
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("async function loadVersion() {")
        end = app.index("// ── Status check", start)
        function = app[start:end]
        script = f"""
            const assert = require('node:assert/strict');
            let activeGameId = 'wuwa';
            let serverInfo = null;
            const pending = [];
            const ipc = () => new Promise(resolve => pending.push(resolve));
            const document = {{getElementById: () => null}};
            const updateVhVersionUI = () => {{}};
            {function}
            (async () => {{
                const oldRequest = loadVersion();
                activeGameId = 'nte';
                const newRequest = loadVersion();
                pending[0]({{version: 'old', game: 'wuwa'}});
                await oldRequest;
                assert.equal(serverInfo, null);
                pending[1]({{version: 'new', game: 'nte'}});
                await newRequest;
                assert.equal(serverInfo.version, 'new');
            }})().catch(error => {{console.error(error); process.exitCode = 1}});
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
