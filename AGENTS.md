# JingJoVH Launcher — agent instructions

@/home/truongpham/.codex/RTK.md

- Reply concisely in English by default. Reply in Vietnamese when the user writes in Vietnamese.
- Read [SESSION_HANDOFF.md](SESSION_HANDOFF.md) and run `rtk git status --short` at the start of a new coding session. The working tree often contains unfinished, uncommitted work; preserve it.
- Treat the current source and tests as authoritative. Some older plans and `graphify-out/` refer to code that has since changed.
- Run `rtk proxy python3 -m pytest -q` for tests, `rtk node --check frontend/app.js` for frontend syntax, and `rtk git diff --check` after relevant edits.
- Keep Wuthering Waves and NTE files/configuration separate. WuWa font PAKs belong in `Client/Binaries/Win64/wuwaVietHoa/`, not `Client/Content/Paks/~mods` (that location caused crashes).
- Do not publish, tag, deploy, or overwrite user game data unless the current user request authorizes the action.
