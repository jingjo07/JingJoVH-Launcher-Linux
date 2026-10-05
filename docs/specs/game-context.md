# Spec: `game-context`

## Objective

Add a persisted active-game context (`wuwa` or `nte`) and route shared launcher operations through it without changing existing Wuthering Waves behavior.

## Tech Stack

Python 3 standard library, GTK3/WebKit2 IPC, and the existing vanilla JavaScript frontend. No new dependency.

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Python syntax: `python3 -m compileall -q backend launcher.py`
- JavaScript syntax: `node --check frontend/app.js`

## Project Structure

- `backend/wuwa_game.py`: existing Wuwa implementation; remains compatible.
- `backend/game_context.py`: game registry, persisted selection, shared dispatch.
- `backend/nte.py`: NTE implementation supplied by `nte-core`.
- `launcher.py`: IPC calls the active game through `game_context`.
- `tests/`: focused routing and configuration tests.

## Code Style

```python
GAMES = {"wuwa": wuwa, "nte": nte}

def active_game():
    return GAMES[get_active_game_id()]
```

Prefer a small module registry and ordinary functions over a class hierarchy.

## Testing Strategy

Use `unittest` with temporary config directories. Prove that selection persists, invalid ids are rejected, Wuwa remains the default for existing users, and dispatch reaches only the active game.

## Boundaries

- Always: preserve existing Wuwa config keys and behavior; validate the game id.
- Ask first: migration that deletes or renames user configuration.
- Never: mix NTE paths/status into Wuwa state or add speculative plugin loading.

## Success Criteria

- Existing users start in Wuwa with no migration action required.
- Selecting NTE persists across launcher restarts.
- Shared status/path/launch/install calls resolve through the active game.
- Adding a later game requires one registry entry and a game module, not edits across every IPC action.

## Open Questions

None.
