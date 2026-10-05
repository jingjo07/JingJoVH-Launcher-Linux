# Spec: `nte-ui`

## Objective

Add a clear game switcher and a dedicated NTE interface while keeping all existing Wuwa themes unchanged and unavailable in NTE mode.

## Tech Stack

Existing HTML, CSS, and vanilla JavaScript rendered by WebKit2GTK. Reuse the current IPC, progress, toast, menu, and accessibility patterns.

## Commands

- JavaScript syntax: `node --check frontend/app.js`
- Test: `python3 -m unittest discover -s tests -v`
- Markup checks: repository-local HTML/CSS checks where available.

## Project Structure

- `frontend/index.html`: game selector and NTE sections.
- `frontend/app.js`: active-game state and feature visibility.
- `frontend/themes/nte/theme.css`: NTE-only visual treatment.
- `frontend/assets/nte/`: only required NTE logo/background/media assets.

## Code Style

```javascript
function applyGame(gameId) {
  document.body.dataset.game = gameId;
  applyTheme(gameId === "nte" ? "nte" : savedWuwaTheme);
}
```

Prefer state expressed through `data-game` and CSS visibility over duplicated event handlers.

## Testing Strategy

Verify JavaScript syntax and add a small DOM-independent state test where practical. Manually render both games and check navigation, keyboard focus, disabled/loading states, and all three Wuwa themes after switching back.

## Boundaries

- Always: preserve Wuwa theme choice; provide keyboard-accessible selection; use NTE-specific labels and assets.
- Ask first: downloading large NTE media into the AppImage rather than using the existing writable media cache.
- Never: custom cursors, Wuwa theme controls in NTE mode, or CSharp controls for NTE.

## Success Criteria

- Users can switch between Wuwa and NTE without restarting.
- Wuwa shows Classic/Modern/Cyber; NTE shows only its NTE theme.
- NTE exposes shared operations and NTE performance, but not unsupported Wuwa-only controls.
- No custom cursor declaration or cursor image is included.
- Switching back to Wuwa restores its saved theme and state.

## Open Questions

- Use DangDev's NTE logo and remote media manifest as visual reference; do not copy unrelated Wuwa watercolor assets into NTE.
