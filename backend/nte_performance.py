"""Apply and restore pinned AlteriaX NTE performance presets."""

import os
import shutil
import stat

from backend import nte, nte_presets_data, wuwa_game


FILES = ("Engine.ini", "DeviceProfiles.ini", "Game.ini", "Input.ini")
COMMON_KEYS = {
    "device_profiles": ("DeviceProfiles.ini", "device_profiles"),
    "game": ("Game.ini", "game"),
    "input": ("Input.ini", "input"),
}
CONFIG_KEY = "nte_performance_settings"


def get_config_dir() -> str | None:
    prefix = nte.detect_prefix_path()
    if not prefix:
        return None
    drive_c = os.path.join(prefix, "drive_c")
    users = os.path.join(drive_c, "users")
    candidates = ["steamuser", os.environ.get("USER", "")]
    if os.path.isdir(users):
        candidates.extend(name for name in sorted(os.listdir(users)) if name.lower() not in {"public", "default"})
    windows_user = next((name for name in candidates if name and os.path.isdir(os.path.join(users, name))), None)
    if not windows_user:
        return None
    local_ht = os.path.join(users, windows_user, "AppData", "Local", "HT")
    profiles = ("Saved_GlobalEpic", "Saved_Global")
    existing = next((name for name in profiles if os.path.isdir(os.path.join(local_ht, name))), None)
    profile = existing or "Saved_Global"
    return os.path.join(local_ht, profile, "Config", "Windows")


def _write_managed(path: str, content: str):
    backup = path + ".wuwavh_bak"
    created = path + ".wuwavh_created"
    if not os.path.exists(backup) and not os.path.exists(created):
        if os.path.isfile(path):
            shutil.copy2(path, backup)
        else:
            open(created, "w").close()
    if os.path.isfile(path):
        os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as output:
        output.write(content)
    os.replace(temporary, path)
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def _restore_managed(path: str) -> bool:
    backup = path + ".wuwavh_bak"
    created = path + ".wuwavh_created"
    managed = os.path.isfile(backup) or os.path.isfile(created)
    if os.path.isfile(backup):
        os.replace(backup, path)
    elif os.path.isfile(created) and os.path.isfile(path):
        os.unlink(path)
    if os.path.isfile(created):
        os.unlink(created)
    return managed


def apply_preset(preset: str, common=None) -> dict:
    if preset not in nte_presets_data.PRESETS:
        raise ValueError(f"NTE preset không hợp lệ: {preset}")
    config_dir = get_config_dir()
    if not config_dir:
        raise FileNotFoundError("Không tìm thấy Wine prefix/config NTE")
    os.makedirs(config_dir, exist_ok=True)
    _write_managed(os.path.join(config_dir, "Engine.ini"), nte_presets_data.PRESETS[preset])
    enabled = [key for key in COMMON_KEYS if (common or {}).get(key)]
    for key, (filename, data_key) in COMMON_KEYS.items():
        path = os.path.join(config_dir, filename)
        if key in enabled:
            _write_managed(path, nte_presets_data.COMMON[data_key])
        else:
            _restore_managed(path)
    cfg = wuwa_game.load_config()
    cfg[CONFIG_KEY] = {"preset": preset, "common": enabled}
    wuwa_game.save_config(cfg)
    return {"preset": preset, "common": enabled, "source_revision": nte_presets_data.SOURCE_REVISION}


def get_settings() -> dict:
    config_dir = get_config_dir()
    saved = wuwa_game.load_config().get(CONFIG_KEY, {})
    if not isinstance(saved, dict):
        saved = {}
    preset = saved.get("preset")
    if preset not in nte_presets_data.PRESETS:
        preset = "config-3"
    saved_common = saved.get("common", [])
    common = [key for key in COMMON_KEYS if isinstance(saved_common, list) and key in saved_common]
    return {
        "presets": [
            {"id": preset, "name": f"Config {preset[-1]}", "gpu_info": nte_presets_data.PRESET_INFO[preset]}
            for preset in nte_presets_data.PRESETS
        ],
        "source_revision": nte_presets_data.SOURCE_REVISION,
        "preset": preset,
        "common": common,
        "has_backup": bool(config_dir and os.path.isfile(os.path.join(config_dir, "Engine.ini.wuwavh_bak"))),
        "supports_common": ["device_profiles", "game", "input"],
    }


def restore() -> dict:
    config_dir = get_config_dir()
    if not config_dir:
        raise FileNotFoundError("Không tìm thấy Wine prefix/config NTE")
    restored = []
    for filename in FILES:
        path = os.path.join(config_dir, filename)
        if _restore_managed(path):
            restored.append(filename)
    cfg = wuwa_game.load_config()
    cfg.pop(CONFIG_KEY, None)
    wuwa_game.save_config(cfg)
    return {"restored": restored}
