"""Neverness to Everness game integration."""

import json
import os
import re
import shutil
import subprocess

from backend import wuwa_game
from backend.version import LAUNCHER_VERSION


VERSION_URL = "https://huggingface.co/datasets/BachMacThanh/DangDevVH/raw/main/NTE/version.json"
DOWNLOAD_BOX = "NTEVH"
DOWNLOAD_PROVIDER = "mod"
STEAM_APP_ID = "4508340"

WEB_ASSETS = (
    ("nte-bgm.mp3", "https://huggingface.co/datasets/BachMacThanh/DangDevVH/resolve/main/NTE/Web/Audio/bgm.mp3?download=true", "Nh\u1ea1c n\u1ec1n NTE Launcher"),
    ("nte-bg-video.mp4", "https://huggingface.co/datasets/BachMacThanh/DangDevVH/resolve/main/NTE/Web/Video/bg-video.mp4?download=true", "Video n\u1ec1n NTE Launcher"),
)

EXE_RELATIVE_PATHS = (
    "Client/WindowsNoEditor/HT/Binaries/Win64/HTGame-Win64-Shipping.exe",
    "Client/WindowsNoEditor/HT/Binaries/Win64/HTGame.exe",
)

# Verified against the signed v1.4.0 artifact served by DangDev on 2026-10-05.
MANAGED_FILES = (
    "HT/Content/Paks/pakchunk999-Windows_999_P.pak",
    "HT/Content/Paks/pakchunk999-Windows_999_P.utoc",
    "HT/Content/Paks/pakchunk999-Windows_999_P.ucas",
    "HT/Binaries/Win64/winhttp.dll",
)

# Older reference builds used these files; they are removable only by explicit
# legacy cleanup, never treated as members of a newly downloaded archive.
LEGACY_FILES = (
    "HT/Content/Paks/pakchunk999-Android_999_P.pak",
    "HT/Content/Paks/pakchunk999-Android_999_P.utoc",
    "HT/Content/Paks/pakchunk999-Android_999_P.ucas",
    "HT/Binaries/Win64/netbios.dll",
    "HT/Binaries/Win64/version.dll",
    "HT/Binaries/Win64/game_vi.dat",
    "HT/Binaries/Win64/viet_font.ttf",
    "HT/Binaries/Win64/viet_font.bak.ttf",
)

DEFAULT_SEARCH_PATHS = (
    "~/Games/Neverness To Everness",
    "~/.local/share/Steam/steamapps/common/Neverness To Everness",
    "~/.steam/steam/steamapps/common/Neverness To Everness",
)

HEROIC_CONFIG_PATHS = (
    "~/.config/heroic",
    "~/.var/app/com.heroicgameslauncher.hgl/config/heroic",
)

STEAM_ROOTS = (
    "~/.local/share/Steam",
    "~/.steam/steam",
    "~/.steam/root",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
    "~/.var/app/com.valvesoftware.Steam/.steam/steam",
)


def resolve_game_root(path: str) -> str | None:
    """Return the NTE root for a selected root, child directory, or executable."""
    current = os.path.realpath(os.path.expanduser(path))
    if os.path.isfile(current):
        current = os.path.dirname(current)
    for _ in range(9):
        if any(os.path.isfile(os.path.join(current, relative)) for relative in EXE_RELATIVE_PATHS):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _steamapps_dirs():
    seen = set()
    for configured_root in STEAM_ROOTS:
        steam_root = os.path.realpath(os.path.expanduser(configured_root))
        candidates = [os.path.join(steam_root, "steamapps")]
        library_file = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
        try:
            with open(library_file, encoding="utf-8", errors="ignore") as source:
                text = source.read()
            for path in re.findall(r'"path"\s*"([^"]+)"', text, re.IGNORECASE):
                candidates.append(os.path.join(path.replace("\\\\", "\\"), "steamapps"))
        except OSError:
            pass
        for candidate in candidates:
            candidate = os.path.realpath(os.path.expanduser(candidate))
            if candidate not in seen:
                seen.add(candidate)
                yield candidate


def detect_steam_install(root: str | None = None) -> dict | None:
    """Find NTE through Steam manifests, including additional and Flatpak libraries."""
    requested_root = resolve_game_root(root) if root else None
    for steamapps in _steamapps_dirs():
        manifest = os.path.join(steamapps, f"appmanifest_{STEAM_APP_ID}.acf")
        try:
            with open(manifest, encoding="utf-8", errors="ignore") as source:
                text = source.read()
        except OSError:
            continue
        install_match = re.search(r'"installdir"\s*"([^"]+)"', text, re.IGNORECASE)
        if not install_match:
            continue
        game_root = resolve_game_root(os.path.join(steamapps, "common", install_match.group(1)))
        if not game_root or (requested_root and game_root != requested_root):
            continue
        name_match = re.search(r'"name"\s*"([^"]+)"', text, re.IGNORECASE)
        prefix = _resolve_prefix(os.path.join(steamapps, "compatdata", STEAM_APP_ID, "pfx"))
        return {
            "app_id": STEAM_APP_ID,
            "title": name_match.group(1) if name_match else "NTE: Neverness to Everness",
            "game_path": game_root,
            "prefix_path": prefix,
            "manifest": manifest,
        }
    return None


def _heroic_installations():
    """Yield NTE installs paired with their Heroic Wine prefix."""
    for config_root in HEROIC_CONFIG_PATHS:
        config_root = os.path.realpath(os.path.expanduser(config_root))
        installed_path = os.path.join(config_root, "legendaryConfig", "legendary", "installed.json")
        try:
            with open(installed_path, encoding="utf-8") as source:
                installed = json.load(source)
        except (OSError, ValueError):
            continue
        for app_name, info in installed.items():
            root = resolve_game_root(str(info.get("install_path", "")))
            title = str(info.get("title", "")).lower()
            if not root or ("neverness" not in title and "nte" not in title):
                continue
            prefix = None
            game_config_path = os.path.join(config_root, "GamesConfig", f"{app_name}.json")
            try:
                with open(game_config_path, encoding="utf-8") as source:
                    game_config = json.load(source).get(app_name, {})
                prefix = _resolve_prefix(game_config.get("winePrefix", ""))
            except (OSError, ValueError):
                pass
            yield {
                "config_root": config_root,
                "runner": "epic",
                "app_name": app_name,
                "title": info.get("title", "Neverness to Everness"),
                "game_path": root,
                "prefix_path": prefix,
            }


def detect_heroic_install(root: str | None = None) -> dict | None:
    root = resolve_game_root(root) if root else None
    installs = list(_heroic_installations())
    if root:
        return next((item for item in installs if item["game_path"] == root), None)
    saved = wuwa_game.load_config().get("nte_game_path")
    saved_root = resolve_game_root(saved) if saved else None
    return next((item for item in installs if not saved_root or item["game_path"] == saved_root), None)


def detect_game_path() -> str | None:
    cfg = wuwa_game.load_config()
    saved = cfg.get("nte_game_path")
    if saved:
        resolved = resolve_game_root(saved)
        if resolved:
            return resolved
    for candidate in DEFAULT_SEARCH_PATHS:
        resolved = resolve_game_root(candidate)
        if resolved:
            return resolved
    steam = detect_steam_install()
    if steam:
        return steam["game_path"]
    heroic = detect_heroic_install()
    if heroic:
        return heroic["game_path"]
    return None


def _resolve_prefix(path: str) -> str | None:
    prefix = os.path.realpath(os.path.expanduser(path))
    return prefix if os.path.isdir(os.path.join(prefix, "drive_c")) else None


def set_prefix_path(path: str):
    prefix = _resolve_prefix(path)
    if not prefix:
        raise ValueError("Th\u01b0 m\u1ee5c kh\xf4ng ph\u1ea3i Wine/Proton prefix h\u1ee3p l\u1ec7")
    cfg = wuwa_game.load_config()
    cfg["nte_prefix_path"] = prefix
    wuwa_game.save_config(cfg)
    return {"ok": True, "path": prefix}


def detect_prefix_path() -> str | None:
    cfg = wuwa_game.load_config()
    saved = _resolve_prefix(cfg.get("nte_prefix_path", ""))
    if saved:
        return saved

    root = detect_game_path()
    current = root
    while current:
        if os.path.basename(current).lower() == "drive_c":
            return os.path.dirname(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    steam = detect_steam_install(root)
    if steam and steam.get("prefix_path"):
        return steam["prefix_path"]
    heroic = detect_heroic_install(root)
    return heroic.get("prefix_path") if heroic else None


def set_game_path(path: str):
    root = resolve_game_root(path)
    if not root:
        raise ValueError("Th\u01b0 m\u1ee5c kh\xf4ng ch\u1ee9a b\u1ea3n c\xe0i NTE h\u1ee3p l\u1ec7")
    cfg = wuwa_game.load_config()
    cfg["nte_game_path"] = root
    wuwa_game.save_config(cfg)
    return {"ok": True, "path": root}


def get_game_exe() -> str | None:
    root = detect_game_path()
    if not root:
        return None
    return next(
        (os.path.join(root, relative) for relative in EXE_RELATIVE_PATHS if os.path.isfile(os.path.join(root, relative))),
        None,
    )


def is_game_running() -> bool:
    names = ("htgame-win64-shipping", "htgame-win64-shipping.exe", "htgame.exe")
    if wuwa_game.HAS_PSUTIL:
        for process in wuwa_game.psutil.process_iter(["name", "status"]):
            try:
                if process.info.get("status") in (wuwa_game.psutil.STATUS_ZOMBIE, wuwa_game.psutil.STATUS_DEAD):
                    continue
                name = (process.info.get("name") or "").lower()
                command = " ".join(process.cmdline()).lower()
                if any(token in name or token in command for token in names):
                    return True
            except (wuwa_game.psutil.NoSuchProcess, wuwa_game.psutil.AccessDenied, wuwa_game.psutil.ZombieProcess):
                continue
    else:
        return subprocess.run(
            ["pgrep", "-f", "HTGame(-Win64-Shipping)?(.exe)?"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
    return False


def get_launcher_info() -> dict:
    root = detect_game_path()
    heroic = detect_heroic_install(root)
    steam = detect_steam_install(root)
    default = "heroic" if heroic else "steam" if steam else "official"
    current = wuwa_game.load_config().get("nte_launcher", default)
    if current not in ("official", "steam", "heroic"):
        current = default
    official_available = bool(
        root
        and (
            os.path.isfile(os.path.join(root, "NTEGlobalLauncher.exe"))
            or any(os.path.isfile(os.path.join(root, relative)) for relative in EXE_RELATIVE_PATHS)
        )
    )
    return {
        "current": current,
        "official_available": official_available,
        "steam_available": bool(steam),
        "steam_has_game": bool(steam),
        "steam_game": steam,
        "heroic_available": bool(heroic),
        "heroic_has_game": bool(heroic),
        "heroic_game": heroic,
        "official": {"available": official_available},
        "steam": {
            "available": bool(steam),
            "game_found": bool(steam),
            "game_title": steam.get("title") if steam else None,
            "app_id": STEAM_APP_ID,
        },
        "heroic": {
            "available": bool(heroic),
            "game_found": bool(heroic),
            "game_title": heroic.get("title") if heroic else None,
            "runner": heroic.get("runner") if heroic else None,
            "app_name": heroic.get("app_name") if heroic else None,
        },
    }


def set_preferred_launcher(launcher_type: str) -> dict:
    if launcher_type not in ("official", "steam", "heroic"):
        raise ValueError(f"Launcher NTE không hỗ trợ: {launcher_type}")
    cfg = wuwa_game.load_config()
    cfg["nte_launcher"] = launcher_type
    wuwa_game.save_config(cfg)
    return get_launcher_info()


def launch_game() -> bool:
    root = detect_game_path()
    if not root:
        raise FileNotFoundError("Kh\xf4ng t\xecm th\u1ea5y th\u01b0 m\u1ee5c game NTE. H\xe3y ch\u1ecdn th\u01b0 m\u1ee5c game tr\u01b0\u1edbc.")
    heroic = detect_heroic_install(root)
    steam = detect_steam_install(root)
    default = "heroic" if heroic else "steam" if steam else "official"
    preferred = wuwa_game.load_config().get("nte_launcher", default)
    if preferred == "steam" and steam:
        steam_bin = shutil.which("steam")
        if steam_bin:
            subprocess.Popen(
                [steam_bin, "-silent", "-applaunch", STEAM_APP_ID],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        try:
            subprocess.Popen(
                ["xdg-open", f"steam://rungameid/{STEAM_APP_ID}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except OSError:
            raise RuntimeError("Không thể mở Steam để chạy NTE")
    if preferred == "heroic" and heroic:
        try:
            subprocess.Popen(
                ["xdg-open", f"heroic://launch/{heroic['runner']}/{heroic['app_name']}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except OSError:
            pass

    launcher = os.path.join(root, "NTEGlobalLauncher.exe")
    target = launcher if os.path.isfile(launcher) else get_game_exe()
    if not target:
        raise FileNotFoundError("Kh\xf4ng t\xecm th\u1ea5y executable NTE")
    wine = shutil.which("wine") or shutil.which("wine64")
    if not wine:
        raise RuntimeError("Kh\xf4ng t\xecm th\u1ea5y Wine \u0111\u1ec3 ch\u1ea1y NTE")
    prefix = detect_prefix_path()
    env = os.environ.copy()
    env["WINEDLLOVERRIDES"] = "winhttp=n,b"
    if prefix:
        env["WINEPREFIX"] = prefix
    subprocess.Popen(
        [wine, target],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    return True


def force_kill_game():
    if wuwa_game.HAS_PSUTIL:
        for process in wuwa_game.psutil.process_iter(["name"]):
            try:
                name = (process.info.get("name") or "").lower()
                command = " ".join(process.cmdline()).lower()
                if "htgame" in name or "htgame" in command:
                    process.kill()
            except (wuwa_game.psutil.NoSuchProcess, wuwa_game.psutil.AccessDenied, wuwa_game.psutil.ZombieProcess):
                continue
    else:
        subprocess.run(["pkill", "-9", "-f", "HTGame"], capture_output=True)


def open_game_folder():
    root = detect_game_path()
    if not root:
        raise FileNotFoundError("Kh\xf4ng t\xecm th\u1ea5y th\u01b0 m\u1ee5c game NTE")
    subprocess.Popen(["xdg-open", root])


def get_vh_version() -> str | None:
    return wuwa_game.load_config().get("nte_vh_version")


def set_vh_version(version: str):
    cfg = wuwa_game.load_config()
    cfg["nte_vh_version"] = version
    wuwa_game.save_config(cfg)


def get_version_info() -> dict:
    from backend import nte_downloader

    return nte_downloader.get_version_info()


def get_web_assets() -> list[tuple[str, str, str]]:
    return list(WEB_ASSETS)


def uninstall_paks() -> list[str]:
    from backend import nte_downloader

    return nte_downloader.uninstall()


def get_perf_settings() -> dict:
    from backend import nte_performance

    return nte_performance.get_settings()


def apply_perf_preset(preset: str, common=None) -> dict:
    from backend import nte_performance

    return nte_performance.apply_preset(preset, common)


def restore_perf_settings() -> dict:
    from backend import nte_performance

    return nte_performance.restore()


def install_wine_dll_overrides() -> dict:
    applied_count = 0
    prefix = detect_prefix_path()
    if prefix:
        for relative in ("user.reg", "pfx/user.reg"):
            reg = os.path.join(prefix, relative)
            if os.path.isfile(reg):
                if wuwa_game._inject_dll_overrides_into_reg(reg, ("winhttp",)):
                    applied_count += 1

    heroic = detect_heroic_install(detect_game_path())
    if heroic:
        config_path = os.path.join(heroic["config_root"], "GamesConfig", f"{heroic['app_name']}.json")
        with open(config_path, encoding="utf-8") as source:
            data = json.load(source)
        app_config = data.get(heroic["app_name"])
        if not isinstance(app_config, dict):
            raise RuntimeError("Cấu hình Heroic của NTE không hợp lệ")
        options = app_config.get("enviromentOptions")
        if not isinstance(options, list):
            options = []
            app_config["enviromentOptions"] = options
        override = next((item for item in options if item.get("key") == "WINEDLLOVERRIDES"), None)
        if override is None:
            options.append({"key": "WINEDLLOVERRIDES", "value": "winhttp=n,b"})
            changed = True
        else:
            values = [value.strip() for value in str(override.get("value", "")).split(",") if value.strip()]
            changed = not any(value.startswith("winhttp=") for value in values)
            if changed:
                override["value"] = ",".join((*values, "winhttp=n,b"))
        if changed:
            temporary = config_path + ".wuwavh.tmp"
            with open(temporary, "w", encoding="utf-8") as output:
                json.dump(data, output, indent=2)
            os.replace(temporary, config_path)
            applied_count += 1

    return {
        "ok": True,
        "count": applied_count,
        "message": f"Đã cấu hình WINEDLLOVERRIDES=\"winhttp=n,b\" cho NTE ({applied_count} vị trí).",
    }


def get_theme() -> str:
    cfg = wuwa_game.load_config()
    return cfg.get("nte_theme", "cyber")


def set_theme(theme_id: str) -> dict:
    cfg = wuwa_game.load_config()
    cfg["nte_theme"] = theme_id
    wuwa_game.save_config(cfg)
    return {"theme": theme_id}


def get_status() -> dict:
    root = detect_game_path()
    content_root = os.path.join(root, "Client", "WindowsNoEditor") if root else None
    installed = [relative for relative in MANAGED_FILES if content_root and os.path.isfile(os.path.join(content_root, relative))]
    return {
        "game": "nte",
        "game_path": root,
        "pak_dir": os.path.join(content_root, "HT", "Content", "Paks") if content_root else None,
        "game_running": is_game_running(),
        "installed_paks": installed,
        "installed_vh": len(installed) == len(MANAGED_FILES),
        "has_game": root is not None,
        "vh_version": get_vh_version(),
        "launcher_version": LAUNCHER_VERSION,
        "font_status": {"active_font": "none", "custom_font_name": None, "default_available": False},
        "prefix_path": detect_prefix_path(),
        "launcher_info": get_launcher_info(),
        "theme": get_theme(),
        "use_dx11": False,
        "use_csharp_env": False,
    }
