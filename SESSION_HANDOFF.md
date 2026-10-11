# Session handoff — 2026-10-10

This is a snapshot for a new coding session, not a claim that every older request is still active. Read `AGENTS.md`, inspect `rtk git status --short`, and check the relevant source before changing anything.

## Project

JingJoVH is a Linux desktop launcher for Vietnamese translations of **Wuthering Waves (WuWa)** and **Neverness to Everness (NTE)**. It uses Python 3, GTK3/WebKit2GTK 4.1, a plain HTML/CSS/JavaScript frontend, and Python IPC. `launcher.py` is the entry point; `./launcher.sh` runs the source without building. `build_appimage.sh` packages an AppImage. There is no npm build step.

| Area | Current owner |
| --- | --- |
| Window, IPC, updates | `launcher.py` |
| Shared active-game routing | `backend/game_context.py` |
| WuWa files, launch, font | `backend/wuwa_game.py`, `backend/wuwa_font_packer.py` |
| NTE files, translation, font, performance | `backend/nte.py`, `backend/nte_downloader.py`, `backend/nte_font.py`, `backend/nte_performance.py` |
| Downloads and self-update | `backend/downloader.py`, `backend/launcher_update.py` |
| UI and themes | `frontend/app.js`, `frontend/index.html`, `frontend/style.css`, `frontend/themes/` |
| Tests | `tests/` |

`README.md` describes features and source setup. `docs/specs/` and `tasks/` contain earlier NTE plans, but some details are stale. `docs/project/antigravity-context.md` records useful WuWa font decisions. The existing `graphify-out/graph.json` is stale: it still describes an old, long `launcher.sh`; verify everything against current files.

## Product decisions and recent results

- WuWa and NTE have separate game paths, status, presets and font behavior. WuWa remains the default for old configurations. NTE custom fonts use a separate override PAK and must not rewrite the translation PAK.
- WuWa translation uses `WuWaVH_99_P.pak` and `winhttp.dll`; fonts are managed separately. Font PAKs load from `Client/Binaries/Win64/wuwaVietHoa/`. Do not move them to `~mods`: a prior attempt caused game crashes.
- The UI includes Classic/Modern/DangDev WuWa themes, Cyber NTE theme, a help tour shown on first launch, author information, and the Discord invite `https://discord.com/invite/irisishere`.
- A request for a new NTE theme based on an image appeared earlier in the conversation, but no such theme was implemented. The image is not preserved in this handoff; ask the user to resend it if they resume that request.
- Tab lag/flash was traced by the user to a Linux `pacman -Syu` regression and stopped after they rolled back Linux. Previous launcher-side performance experiments were reverted. Do not assume this bug remains or rework CSS for it without a fresh report.
- The latest authorized work fixed WuWa translation uninstall deleting font/unrelated PAKs, atomic WuWa file replacement, protection of a pre-existing `winhttp.dll`, cross-window update locking, a legacy self-update URL mismatch, and repeated media listener registration. See `tests/test_wuwa_installation.py`, `tests/test_update_lock.py`, and `tests/test_launcher_update.py`.

## Working tree and verification

The `main` working tree is **dirty and uncommitted**. As of this handoff, tracked edits include `README.md`, several `backend/` modules, `launcher.py`, `build_appimage.sh`, `frontend/app.js`, `frontend/index.html`, theme CSS, tests, and packaging tools. Untracked work includes `launcher.sh` and multiple new tests. These changes span earlier user requests; do not reset or overwrite them. Run `rtk git status --short` for the exact current list.

On 2026-10-10, these checks passed on this working tree:

```text
rtk proxy python3 -m pytest -q    -> 96 passed, 1 PyGIDeprecationWarning
rtk node --check frontend/app.js  -> passed
rtk git diff --check              -> passed
```

The GUI and game installation were not exercised on real game files by those checks. Do not infer release readiness from the test count. No commit, tag, release, or deployment was made for the uncommitted work.

## Start the next session

1. Read `AGENTS.md` and this file.
2. Run `rtk git status --short`; inspect the diff relevant to the **new** request.
3. Read the relevant source and tests, then make only the changes the user asks for.
4. Re-run focused tests and the full suite when the code changes.

Suggested first message to a new coding session:

> We are continuing JingJoVH Launcher in `/home/truongpham/Documents/WuwaVH`. Read `AGENTS.md` and `SESSION_HANDOFF.md`, inspect the current working tree, and preserve all uncommitted changes. Then help me with: [describe the next task].
