# Implementation Plan: Multi-game Launcher with NTE

## Overview

Extend the existing Wuthering Waves launcher with a persisted game context and a complete NTE vertical slice. Wuwa remains the backward-compatible default. NTE receives its own backend behavior, translation installer, AlteriaX performance presets, and dedicated theme without custom cursors.

## Architecture Decisions

- Keep `backend/wuwa_game.py` as the Wuwa implementation; do not rewrite its mature behavior during this feature.
- Route common operations through a small module registry in `backend/game_context.py`; avoid a plugin framework or class hierarchy.
- Store NTE state under separate config keys while reading all existing Wuwa keys unchanged.
- Treat the NTE translation download contract as untrusted until extracted and verified from `references/DangDevVH.exe`.
- Install translation updates transactionally: download first, validate, then replace managed files.
- Vendor a reviewed snapshot of AlteriaX/NTE-Configs with its upstream commit recorded so presets work offline and remain reproducible.
- Drive frontend differences with the active game id and a dedicated `nte` theme; preserve the user's Wuwa theme independently.
- Do not add dependencies, custom cursors, CSharp support for NTE, or release automation.

## Dependency Order

```text
Reference contract
       |
Game context -> NTE core -> NTE translation -----+
                    \----> NTE performance ------+-> NTE UI -> Final verification
```

## Task List

### Phase 1: Foundations

#### Task 1: Lock down the NTE reference contract

**Description:** Extract the exact NTE artifact names, source URLs, install locations, and launch expectations from `references/DangDevVH.exe`; record fixtures without executing the Windows binary.

**Acceptance criteria:**
- The translation artifact contract is explicit and traceable to reference data.
- Remote filenames cannot choose arbitrary local destinations.
- Unknown or unverifiable fields are rejected rather than guessed.

**Verification:**
- Focused manifest/parser test fails before implementation and passes afterward.
- Compare constants with strings/resources extracted from `references/DangDevVH.exe`.

**Dependencies:** None

**Files likely touched:**
- `backend/nte.py`
- `tests/test_nte.py`
- `docs/specs/nte-translation.md` only if the verified contract changes it

**Estimated scope:** Medium

#### Task 2: Add persisted game context

**Description:** Add the `wuwa`/`nte` registry, retain Wuwa as the default, and expose selection through IPC.

**Acceptance criteria:**
- Existing config loads as Wuwa without migration.
- Valid selection persists; invalid game ids are rejected.
- Common status/path/launch calls can target the active module.

**Verification:**
- `python3 -m unittest -v tests.test_game_context`
- Existing launcher updater tests remain green.

**Dependencies:** Task 1

**Files likely touched:**
- `backend/game_context.py`
- `launcher.py`
- `tests/test_game_context.py`

**Estimated scope:** Medium

#### Task 3: Implement NTE path, status, launch, and stop

**Description:** Validate manual NTE folder selection, add conservative auto-detection, report status, and launch/stop only the selected NTE installation.

**Acceptance criteria:**
- Both known NTE executable layouts are recognized.
- Manual selection is always available when auto-detection fails.
- Launch/stop cannot target unrelated processes or invalid paths.

**Verification:**
- `python3 -m unittest -v tests.test_nte`
- Temporary fake installation covers missing, ready, and running states.

**Dependencies:** Task 2

**Files likely touched:**
- `backend/nte.py`
- `backend/game_context.py`
- `launcher.py`
- `tests/test_nte.py`

**Estimated scope:** Medium

### Checkpoint: Foundations

- All current and new tests pass.
- Existing Wuwa is still the default and its status/launch routes behave unchanged.
- NTE can be selected and a valid installation recognized without frontend redesign.

### Phase 2: NTE Features

#### Task 4: Add transactional NTE translation management

**Description:** Use the shared downloader for NTE version checks and managed-file install/update/uninstall with safe failure behavior.

**Acceptance criteria:**
- NTE version and installed state are independent from Wuwa.
- Partial or invalid downloads never replace the working installation.
- Uninstall removes only the explicit managed-file allowlist.

**Verification:**
- `python3 -m unittest -v tests.test_nte_translation`
- Tests cover successful install, partial failure, invalid metadata, and uninstall preservation.

**Dependencies:** Tasks 1 and 3

**Files likely touched:**
- `backend/nte.py`
- `backend/nte_downloader.py`
- `launcher.py`
- `tests/test_nte_translation.py`

**Estimated scope:** Medium

#### Task 5: Add pinned AlteriaX NTE performance presets

**Description:** Add Config 1–5 and optional Common settings with first-write backup, read-only application, and exact restore.

**Acceptance criteria:**
- Presets match the recorded AlteriaX/NTE-Configs revision.
- Writes are limited to NTE's `HT/Saved_Global/Config/Windows` path.
- Restore returns every pre-existing file and permission state handled by the launcher.

**Verification:**
- `python3 -m unittest -v tests.test_nte_performance`
- Compare vendored content hashes with the pinned upstream revision.

**Dependencies:** Task 3

**Files likely touched:**
- `backend/nte_performance.py`
- `backend/nte_presets_data.py`
- `launcher.py`
- `tests/test_nte_performance.py`

**Estimated scope:** Medium

### Checkpoint: NTE Backend

- Full Python test suite passes.
- Translation failure preserves the old NTE installation.
- Preset restore is byte-for-byte correct in temporary test data.
- No NTE action reads or writes Wuwa paths.

### Phase 3: User Interface

#### Task 6: Add game selection and NTE theme shell

**Description:** Add an accessible game selector, persist it through IPC, and create the NTE-only visual shell using NTE assets/reference styling.

**Acceptance criteria:**
- Switching games updates the UI without restart.
- Wuwa theme choice is restored when returning to Wuwa.
- NTE uses only its dedicated theme and contains no custom cursor rule or image.

**Verification:**
- `node --check frontend/app.js`
- Render/manual check both game states and keyboard navigation.

**Dependencies:** Tasks 2 and 3

**Files likely touched:**
- `frontend/index.html`
- `frontend/app.js`
- `frontend/themes/nte/theme.css`
- `frontend/assets/nte/`

**Estimated scope:** Medium

#### Task 7: Connect shared NTE actions and progress UI

**Description:** Connect NTE status, folder selection, Play/Stop, translation update/uninstall, and shared progress/toast states to the NTE screen.

**Acceptance criteria:**
- All shared actions operate on NTE while NTE is active.
- Concurrent update actions remain blocked as in Wuwa.
- Switching games cannot redirect an already-running update to another game's paths.

**Verification:**
- Full unit suite passes.
- Manual state check covers missing folder, ready, updating, failed, installed, and running.

**Dependencies:** Tasks 4 and 6

**Files likely touched:**
- `launcher.py`
- `frontend/index.html`
- `frontend/app.js`
- `tests/test_game_context.py`

**Estimated scope:** Medium

#### Task 8: Connect NTE performance and feature visibility

**Description:** Expose NTE Config 1–5, optional Common switches, and restore; hide unsupported Wuwa-only controls such as CSharp.

**Acceptance criteria:**
- NTE shows its performance controls and never shows CSharp.
- Wuwa retains its current Font/Performance/DX11/CSharp behavior.
- Unsupported controls cannot be invoked through stale hidden UI state.

**Verification:**
- NTE performance tests pass.
- Manual switch Wuwa → NTE → Wuwa confirms correct feature visibility and retained state.

**Dependencies:** Tasks 5 and 6

**Files likely touched:**
- `launcher.py`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/themes/nte/theme.css`

**Estimated scope:** Medium

### Checkpoint: Complete UI

- NTE's end-to-end path works from selection through launch and translation management.
- Wuwa's three themes and existing features remain intact.
- Keyboard focus, disabled states, progress, errors, and notifications are usable.
- Repository search finds no custom cursor declaration under NTE assets/theme.

### Phase 4: Verification and Packaging

#### Task 9: Regression-test and package locally

**Description:** Run all checks, build an AppImage, extract it, and verify both games and required resources are present.

**Acceptance criteria:**
- Full automated suite and syntax/diff checks pass.
- Extracted AppImage contains the NTE backend, pinned presets, and NTE theme.
- Existing Wuwa assets/features remain packaged.
- No tag, push, release, or upload is performed.

**Verification:**
- `python3 -m unittest discover -s tests -v`
- `python3 -m compileall -q backend launcher.py`
- `node --check frontend/app.js`
- `bash -n build_appimage.sh`
- `git diff --check`
- `bash build_appimage.sh`, followed by AppImage extraction and file inspection

**Dependencies:** Tasks 1–8

**Files likely touched:**
- `tests/` only for missing regression coverage
- `build_appimage.sh` only if packaging omits required source/assets

**Estimated scope:** Small

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| DangDev NTE metadata lacks artifact hashes | High | Extract the exact contract first; reject unverifiable remote metadata and preserve existing files |
| NTE launch layout differs across Wine installs | High | Validate known executable layouts and keep manual selection as the required fallback |
| Shared IPC accidentally modifies Wuwa | High | Default to Wuwa, route through focused registry tests, and checkpoint before UI work |
| AlteriaX upstream changes | Medium | Pin a commit and vendor reviewed preset contents with hashes |
| Theme work duplicates the existing frontend | Medium | Reuse existing elements/events and switch visibility through `data-game` |
| Large remote NTE media inflates AppImage | Medium | Use the existing writable media cache; package only essential lightweight assets |

## Open Questions

No user decision is currently required. Task 1 resolves the remaining technical uncertainty before feature code proceeds.

## Progress Reporting

Report after each named checkpoint with:

- Completed tasks and files changed.
- Tests/checks run and exact result.
- Newly discovered risk or deviation from the approved specs.
- Next tasks to execute.
