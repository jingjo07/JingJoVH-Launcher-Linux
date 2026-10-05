# Spec: `nte-core`

## Objective

Provide NTE folder selection, status detection, launch, and stop behavior on Linux/Wine while isolating all NTE state from Wuthering Waves.

Heroic keeps the game directory and Wine/Proton prefix separate. The backend therefore detects or stores `nte_game_path` and `nte_prefix_path` independently and launches a matched Heroic install through its protocol URL.

## Tech Stack

Python 3 standard library and the launch/process helpers already used by `backend/wuwa_game.py`.

## Commands

- Test: `python3 -m unittest -v tests.test_nte`
- Syntax: `python3 -m compileall -q backend launcher.py`

## Project Structure

- `backend/nte.py`: NTE constants and game operations.
- `backend/game_context.py`: active-game routing.
- `tests/test_nte.py`: path, process, and configuration tests.

## Code Style

```python
NTE_EXES = (
    "Client/WindowsNoEditor/HT/Binaries/Win64/HTGame-Win64-Shipping.exe",
    "Client/WindowsNoEditor/HT/Binaries/Win64/HTGame.exe",
)
```

Use explicit relative paths and normalize user-selected folders before accepting them.

## Testing Strategy

Use temporary directory trees and mocked processes. Cover a valid NTE root, a nested selected directory, invalid folders, running-state detection, launch arguments, and safe stop behavior.

## Boundaries

- Always: allow manual folder selection; verify an expected NTE executable before saving.
- Ask first: broad filesystem scanning outside known Wine/Steam/Heroic roots.
- Never: execute a path that was not validated as an NTE installation.

## Success Criteria

- The launcher can accept and remember a valid NTE installation folder.
- It reports missing, ready, and running states correctly.
- Play launches NTE through the detected Linux/Wine launcher path available to the installation.
- Stop targets only the NTE processes associated with the active installation.

## Open Questions

- Automatic detection will cover only installation roots confirmed from local code/reference data; manual selection is the required fallback.
