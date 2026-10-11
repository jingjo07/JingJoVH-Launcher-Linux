"""Download and transactionally install the NTE Vietnamese translation."""

import json
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile

from backend import downloader, nte, wuwa_game


def get_version_info() -> dict:
    request = urllib.request.Request(nte.VERSION_URL, headers={"User-Agent": "WuWaVH-Launcher"})
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.load(response)
    version = str(data.get("version", "")).strip().lstrip("vV")
    if not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise RuntimeError("Phiên bản NTE không hợp lệ")
    return {"version": version, "date": data.get("date", ""), "note": data.get("note", "")}


def _content_root() -> str:
    root = nte.detect_game_path()
    if not root:
        raise FileNotFoundError("Không tìm thấy thư mục game NTE")
    return os.path.join(root, "Client", "WindowsNoEditor")


def _validated_archive(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    if archive.testzip() is not None:
        raise RuntimeError("Gói Việt hóa NTE bị lỗi CRC")
    files = [info for info in archive.infolist() if not info.is_dir()]
    members = {info.filename.replace("\\", "/"): info for info in files}
    if set(members) != set(nte.MANAGED_FILES) or len(files) != len(nte.MANAGED_FILES):
        raise RuntimeError("Gói Việt hóa NTE không hợp lệ")
    return members


def _marker(path: str) -> str:
    return path + ".wuwavh_sha256"


def _refresh_owned_hash(path: str):
    marker = _marker(path)
    if not os.path.isfile(marker):
        return
    fd, temporary = tempfile.mkstemp(prefix=".wuwavh-hash-", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="ascii") as output:
            output.write(wuwa_game.sha256_file(path))
        os.replace(temporary, marker)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _check_owned(path: str):
    marker = _marker(path)
    if not os.path.isfile(marker):
        return False
    with open(marker, encoding="ascii") as source:
        expected = source.read().strip()
    if not os.path.isfile(path) or wuwa_game.sha256_file(path) != expected:
        raise RuntimeError(f"File NTE đã thay đổi bên ngoài launcher: {path}")
    return True


def install(version: str, progress=None) -> dict:
    version = str(version).strip().lstrip("vV")
    if not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise ValueError("Phiên bản NTE không hợp lệ")
    content_root = _content_root()
    os.makedirs(content_root, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".nte-update-", dir=content_root) as workspace:
        archive_path = os.path.join(workspace, "nte.zip")
        href = downloader.mint_href(nte.DOWNLOAD_PROVIDER, version, box=nte.DOWNLOAD_BOX)
        downloader.download_file(href, archive_path, progress)

        stage = os.path.join(workspace, "stage")
        backup = os.path.join(workspace, "backup")
        os.makedirs(stage)
        os.makedirs(backup)
        with zipfile.ZipFile(archive_path) as archive:
            members = _validated_archive(archive)
            for relative, info in members.items():
                staged = os.path.join(stage, relative)
                os.makedirs(os.path.dirname(staged), exist_ok=True)
                with archive.open(info) as source, open(staged, "wb") as destination:
                    shutil.copyfileobj(source, destination)

        previous = {}
        previous_markers = {}
        new_backups = []
        try:
            for relative in members:
                target = os.path.join(content_root, relative)
                saved = os.path.join(backup, relative)
                marker = _marker(target)
                owned = _check_owned(target)
                if not owned and os.path.exists(target + ".wuwavh_bak"):
                    raise RuntimeError(f"Không thể xác định bản sao lưu NTE: {target}")
                if os.path.isfile(target):
                    os.makedirs(os.path.dirname(saved), exist_ok=True)
                    shutil.copy2(target, saved)
                    previous[target] = saved
                    if not owned:
                        new_backups.append(target + ".wuwavh_bak")
                        shutil.copy2(target, target + ".wuwavh_bak")
                else:
                    previous[target] = None
                old_marker = os.path.join(backup, relative + ".sha256")
                if os.path.isfile(marker):
                    shutil.copy2(marker, old_marker)
                    previous_markers[marker] = old_marker
                else:
                    previous_markers[marker] = None
                os.makedirs(os.path.dirname(target), exist_ok=True)
                os.replace(os.path.join(stage, relative), target)
                with open(marker, "w", encoding="ascii") as output:
                    output.write(wuwa_game.sha256_file(target))
        except Exception:
            for target, saved in previous.items():
                if saved and os.path.isfile(saved):
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    os.replace(saved, target)
                elif os.path.isfile(target):
                    os.unlink(target)
            for marker, saved in previous_markers.items():
                if saved and os.path.isfile(saved):
                    os.replace(saved, marker)
                elif os.path.isfile(marker):
                    os.unlink(marker)
            for path in new_backups:
                if os.path.isfile(path):
                    os.unlink(path)
            raise

    from backend import nte_font
    font_reapplied = nte_font.refresh_after_translation_update()
    _refresh_owned_hash(os.path.join(content_root, nte.MANAGED_FILES[0]))
    cfg = wuwa_game.load_config()
    cfg["nte_vh_version"] = version
    wuwa_game.save_config(cfg)
    return {"version": version, "installed": list(nte.MANAGED_FILES), "font_reapplied": font_reapplied}


def uninstall() -> list[str]:
    try:
        content_root = _content_root()
    except FileNotFoundError:
        return []
    removed = []
    owned = []
    unknown = []
    for relative in nte.MANAGED_FILES:
        path = os.path.join(content_root, relative)
        if _check_owned(path):
            owned.append((relative, path))
        elif os.path.isfile(path):
            unknown.append(relative)
    if unknown:
        raise RuntimeError("File NTE không rõ quyền sở hữu; cần kiểm tra thủ công trước khi gỡ: " + ", ".join(unknown))
    for relative, path in owned:
        backup = path + ".wuwavh_bak"
        if os.path.isfile(backup):
            os.replace(backup, path)
        else:
            os.unlink(path)
        os.unlink(_marker(path))
        removed.append(relative)
    if not any(os.path.isfile(os.path.join(content_root, relative)) for relative in nte.MANAGED_FILES):
        cfg = wuwa_game.load_config()
        cfg["nte_vh_version"] = ""
        wuwa_game.save_config(cfg)
    return removed
