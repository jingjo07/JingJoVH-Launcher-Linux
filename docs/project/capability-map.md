# Capability Map: Multi-game Vietnamese Launcher

## Goal

Keep the existing Wuthering Waves launcher working while adding Neverness to Everness (NTE) as the first independently configured game and making later games cheaper to add.

| Module id | Responsibility | Depends on |
|---|---|---|
| `game-context` | Select and persist the active game; route shared launcher actions to that game's implementation | — |
| `nte-core` | Detect/select the NTE folder, report status, launch/stop NTE, and keep NTE state separate from Wuwa | `game-context` |
| `nte-translation` | Read DangDev's NTE manifest; download, verify, install, update, and remove NTE Vietnamese files | `nte-core` |
| `nte-performance` | Apply and restore NTE presets sourced from AlteriaX/NTE-Configs | `nte-core` |
| `nte-ui` | Add the game selector and an NTE-only theme while preserving the existing Wuwa themes | `game-context`, `nte-core`, `nte-translation`, `nte-performance` |
| `release-verification` | Regression-test Wuwa and NTE, validate packaged resources, and build an AppImage locally | all modules |

Build order:

1. `game-context`
2. `nte-core`
3. `nte-translation` and `nte-performance`
4. `nte-ui`
5. `release-verification`

## Approved product boundaries

- Wuthering Waves keeps its current Classic, Modern, and Cyber themes and existing features.
- NTE gets a separate theme; Wuwa themes are unavailable while NTE is active.
- No custom cursor is allowed.
- NTE does not expose the CSharp option because the game does not support it.
- NTE performance presets come from `https://github.com/AlteriaX/NTE-Configs`, not Wuwa presets.
- Wuwa-only features are not shown for NTE unless their compatibility is verified.
- Existing Wuwa user configuration must remain compatible.
- Publishing, tagging, or uploading a release is outside this initiative unless separately requested.
