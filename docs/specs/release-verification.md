# Spec: `release-verification`

## Objective

Prove the multi-game changes do not regress Wuthering Waves and that NTE resources are packaged correctly before any release decision.

## Tech Stack

Existing unittest suite, Python/Node syntax checks, `build_appimage.sh`, and AppImage extraction.

## Commands

- Tests: `python3 -m unittest discover -s tests -v`
- Python syntax: `python3 -m compileall -q backend launcher.py`
- JavaScript syntax: `node --check frontend/app.js`
- Build syntax: `bash -n build_appimage.sh`
- Build: `bash build_appimage.sh`
- Diff hygiene: `git diff --check`

## Project Structure

- `tests/`: focused Wuwa regression and NTE tests.
- `build_appimage.sh`: package new source/assets using the existing process.
- `build/`: ignored build output only.

## Code Style

Verification commands remain simple shell commands; do not introduce a new test runner or CI framework for this feature.

## Testing Strategy

Run focused tests after each slice, then the full suite. Extract the final AppImage and compare packaged game modules, version data, NTE theme, and absence of custom cursor assets/declarations.

## Boundaries

- Always: test existing updater behavior and Wuwa flows; inspect the packaged artifact.
- Ask first: changing version numbers, tags, releases, or GitHub assets.
- Never: publish an artifact merely because it builds.

## Success Criteria

- All existing and new automated tests pass.
- Python, JavaScript, shell, and diff checks pass.
- Wuwa remains the default and its existing features remain reachable.
- The extracted AppImage contains NTE support and no NTE custom cursor.
- No GitHub release, tag, push, or upload occurs without a separate user request.

## Open Questions

None.
