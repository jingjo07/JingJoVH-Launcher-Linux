"""Persist the selected game and route common launcher actions."""

from backend import nte, wuwa_game, wuwa_performance


GAMES = {"wuwa": wuwa_game, "nte": nte}
GAME_LABELS = {"wuwa": "Wuthering Waves", "nte": "Neverness to Everness"}


def get_active_game_id() -> str:
    game_id = wuwa_game.load_config().get("active_game", "wuwa")
    return game_id if game_id in GAMES else "wuwa"


def set_active_game(game_id: str) -> dict:
    if game_id not in GAMES:
        raise ValueError(f"Game kh\xf4ng h\u1ed7 tr\u1ee3: {game_id}")
    cfg = wuwa_game.load_config()
    cfg["active_game"] = game_id
    wuwa_game.save_config(cfg)
    return {"game": game_id}


def get_games() -> dict:
    return {
        "active": get_active_game_id(),
        "games": [{"id": game_id, "name": GAME_LABELS[game_id]} for game_id in GAMES],
    }


def active_game():
    return GAMES[get_active_game_id()]


def get_status():
    status = active_game().get_status()
    status.setdefault("game", get_active_game_id())
    return status


def get_version_info():
    selected = active_game()
    if selected is nte:
        return nte.get_version_info()
    from backend import downloader

    return downloader.get_version_info()


def get_web_assets():
    selected = active_game()
    if hasattr(selected, "get_web_assets"):
        return selected.get_web_assets()
    from backend import downloader

    return downloader.get_web_assets()


def set_game_path(path: str):
    return active_game().set_game_path(path)


def set_prefix_path(path: str):
    if active_game() is not nte:
        raise ValueError("Wine prefix ri\xeang ch\u1ec9 \xe1p d\u1ee5ng cho NTE")
    return nte.set_prefix_path(path)


def launch_game():
    return active_game().launch_game()


def get_launcher_info():
    return active_game().get_launcher_info()


def set_preferred_launcher(launcher_type: str):
    return active_game().set_preferred_launcher(launcher_type)


def force_kill_game():
    return active_game().force_kill_game()


def open_game_folder():
    return active_game().open_game_folder()


def set_vh_version(version: str):
    return active_game().set_vh_version(version)


def uninstall_paks():
    return active_game().uninstall_paks()


def get_perf_settings():
    selected = active_game()
    if selected is nte:
        return nte.get_perf_settings()
    return wuwa_performance.get_perf_settings()


def apply_perf_preset(preset: str, common=None):
    selected = active_game()
    if selected is nte:
        return nte.apply_perf_preset(preset, common)
    return wuwa_performance.apply_perf_preset(preset)


def restore_perf_settings():
    selected = active_game()
    if selected is nte:
        return nte.restore_perf_settings()
    return wuwa_performance.restore_default_ini()


def install_wine_dll_overrides() -> dict:
    selected = active_game()
    if hasattr(selected, "install_wine_dll_overrides"):
        return selected.install_wine_dll_overrides()
    return wuwa_game.install_wine_dll_overrides()


def get_theme() -> str:
    selected = active_game()
    if hasattr(selected, "get_theme"):
        return selected.get_theme()
    return wuwa_game.get_theme()


def set_theme(theme_id: str) -> dict:
    selected = active_game()
    if hasattr(selected, "set_theme"):
        return selected.set_theme(theme_id)
    return wuwa_game.set_theme(theme_id)
