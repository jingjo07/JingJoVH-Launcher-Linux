# Spec: `nte-translation`

## Objective

Download, verify, install, update, and remove DangDev's NTE Vietnamese files using the launcher's existing downloader and progress UI.

## Tech Stack

Python standard library, `backend/downloader.py`, and DangDev's NTE metadata at `https://huggingface.co/datasets/BachMacThanh/DangDevVH/raw/main/NTE/version.json`.

## Commands

- Test: `python3 -m unittest -v tests.test_nte_translation`
- Full tests: `python3 -m unittest discover -s tests -v`

## Project Structure

- `backend/nte.py`: NTE install paths and installed-version state.
- `backend/nte_downloader.py`: manifest parsing and transactional file installation if separation is needed.
- `launcher.py`: reuse existing update progress events.
- `tests/test_nte_translation.py`: manifest and file-operation tests.

## Code Style

```python
NTE_INSTALLED_FILES = (
    "HT/Content/Paks/pakchunk999-Windows_999_P.pak",
    "HT/Content/Paks/pakchunk999-Windows_999_P.utoc",
    "HT/Content/Paks/pakchunk999-Windows_999_P.ucas",
)
```

Keep the authoritative file list explicit and install through temporary files followed by atomic replacement.

## Testing Strategy

Mock network calls and use temporary NTE directory trees. Verify valid installs, interrupted downloads, checksum mismatch when hashes are supplied, removal of only managed files, and preservation of the previous working installation on failure.

## Boundaries

- Always: reuse `download_file`; validate remote metadata; keep the old installation until the new files are complete.
- Ask first: changing from DangDev's authenticated mint endpoint to an unsigned third-party source.
- Never: delete unrecognized files from NTE directories or trust a destination path supplied by remote metadata.

## Success Criteria

- Available and installed NTE Vietnamese versions are shown separately from Wuwa.
- Install/update progress uses the existing launcher progress surface.
- A failed update leaves the prior NTE translation usable.
- Uninstall removes only the known files managed by this launcher.

## Open Questions

- DangDev's public `version.json` exposes version/date/note but no artifact hashes. The verified contract uses box `NTEVH`, provider `mod`, a version without the leading `v`, and a ZIP allowlisted to four managed files. Installation must validate the ZIP structure and CRC before replacement.
