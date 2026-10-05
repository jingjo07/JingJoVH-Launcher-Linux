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


def _validated_archive(archive: zipfile.ZipFile) -> list[str]:
    if archive.testzip() is not None:
        raise RuntimeError("Gói Việt hóa NTE bị lỗi CRC")
    members = [info.filename.replace("\\", "/") for info in archive.infolist() if not info.is_dir()]
    if set(members) != set(nte.MANAGED_FILES) or len(members) != len(nte.MANAGED_FILES):
        raise RuntimeError("Gói Việt hóa NTE không hợp lệ")
    return members


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
            for relative in members:
                staged = os.path.join(stage, relative)
                os.makedirs(os.path.dirname(staged), exist_ok=True)
                with archive.open(relative) as source, open(staged, "wb") as destination:
                    shutil.copyfileobj(source, destination)

        previous = {}
        try:
            for relative in members:
                target = os.path.join(content_root, relative)
                saved = os.path.join(backup, relative)
                if os.path.isfile(target):
                    os.makedirs(os.path.dirname(saved), exist_ok=True)
                    shutil.copy2(target, saved)
                    previous[target] = saved
                else:
                    previous[target] = None
                os.makedirs(os.path.dirname(target), exist_ok=True)
                os.replace(os.path.join(stage, relative), target)
        except Exception:
            for target, saved in previous.items():
                if saved and os.path.isfile(saved):
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    os.replace(saved, target)
                elif os.path.isfile(target):
                    os.unlink(target)
            raise

    for relative in nte.LEGACY_FILES:
        legacy = os.path.join(content_root, relative)
        if os.path.isfile(legacy):
            os.unlink(legacy)
    cfg = wuwa_game.load_config()
    cfg["nte_vh_version"] = version
    wuwa_game.save_config(cfg)
    return {"version": version, "installed": list(nte.MANAGED_FILES)}


def uninstall() -> list[str]:
    try:
        content_root = _content_root()
    except FileNotFoundError:
        return []
    removed = []
    for relative in nte.MANAGED_FILES + nte.LEGACY_FILES:
        path = os.path.join(content_root, relative)
        if os.path.isfile(path):
            os.unlink(path)
            removed.append(relative)
    cfg = wuwa_game.load_config()
    cfg["nte_vh_version"] = ""
    wuwa_game.save_config(cfg)
    return removed
