# Spec: `nte-performance`

## Objective

Offer five NTE performance presets sourced from AlteriaX/NTE-Configs, with backup and restore of the user's original files.

## Tech Stack

Python standard library and tracked preset data derived from `https://github.com/AlteriaX/NTE-Configs`.

## Commands

- Test: `python3 -m unittest -v tests.test_nte_performance`
- Full tests: `python3 -m unittest discover -s tests -v`

## Project Structure

- `backend/nte_performance.py`: NTE config location, backup, apply, and restore.
- `backend/nte_presets_data.py`: Config 1–5 and optional Common files with source revision recorded.
- `tests/test_nte_performance.py`: file-operation and preset tests.

## Code Style

```python
NTE_CONFIG_DIR = "HT/Saved_Global/Config/Windows"
PRESETS = {"config_1": ENGINE_CONFIG_1, "config_2": ENGINE_CONFIG_2}
```

Store reviewed preset contents with the application so applying a preset is deterministic and works offline.

## Testing Strategy

Use a temporary Wine-prefix tree. Verify initial backup, preset application, read-only permissions, idempotent reapplication, optional Common files, and exact restoration.

## Boundaries

- Always: back up before the first write; apply NTE files only to NTE's config directory; cite the upstream revision.
- Ask first: silently overwriting user edits made after a launcher backup.
- Never: reuse Wuwa preset values or expose CSharp controls for NTE.

## Success Criteria

- Config 1–5 match the selected AlteriaX/NTE-Configs revision.
- Files are written under the detected NTE Wine prefix. Epic/Heroic uses `%LocalAppData%/HT/Saved_GlobalEpic/Config/Windows`; standalone installs may use `Saved_Global/Config/Windows`. Applied files are made read-only as upstream requires.
- Users can restore their exact pre-launcher files.
- Optional DeviceProfiles/Game/Input settings are explicit choices, not silently enabled.

## Open Questions

None. Upstream README and tree were verified on 2026-10-05.
