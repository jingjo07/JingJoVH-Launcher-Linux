import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class FrontendGameTests(unittest.TestCase):
    def test_wuwa_files_and_themes_have_explicit_names(self):
        for name in ("game", "performance", "presets_data", "font_packer"):
            self.assertFalse((ROOT / f"backend/{name}.py").exists())
            self.assertTrue((ROOT / f"backend/wuwa_{name}.py").is_file())

        for name in ("classic", "modern"):
            self.assertFalse((ROOT / f"frontend/themes/{name}").exists())
            self.assertTrue((ROOT / f"frontend/themes/wuwa-{name}/theme.css").is_file())

        self.assertFalse((ROOT / "frontend/themes/wuwa-cyber").exists())
        self.assertTrue((ROOT / "frontend/themes/nte-cyber/theme.css").is_file())
        self.assertTrue((ROOT / "frontend/themes/wuwa-dangdev/theme.css").is_file())

    def test_nte_ui_contract(self):
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        themes = (ROOT / "frontend/themes/themes.js").read_text(encoding="utf-8")
        nte_css = ROOT / "frontend/themes/nte-cyber/theme.css"
        dangdev_css = ROOT / "frontend/themes/wuwa-dangdev/theme.css"

        self.assertIn('id="game-select"', html)
        self.assertIn('id="nte-common-options"', html)
        self.assertIn('id="prefix-input"', html)
        self.assertIn('ipc("set_active_game"', app)
        self.assertIn('ipc("set_game_prefix"', app)
        self.assertIn('activeGameId !== "wuwa"', app)
        self.assertIn('body[data-game="nte"] #btn-mode-advanced', (ROOT / "frontend/style.css").read_text(encoding="utf-8"))
        self.assertNotIn('id="toggle-dx11-cyber"', html)
        self.assertIn('css: "themes/nte-cyber/theme.css"', themes)
        self.assertIn('css: "themes/wuwa-dangdev/theme.css"', themes)
        self.assertTrue(nte_css.is_file())
        self.assertTrue(dangdev_css.is_file())
        dangdev_theme = dangdev_css.read_text(encoding="utf-8")
        self.assertIn('font-family: "Jade Charm"', dangdev_theme)
        self.assertIn("--wc-jade: #e5cd98", dangdev_theme)
        self.assertIsNone(re.search(r"cursor\s*:\s*url\s*\(", dangdev_theme, re.I))
        self.assertTrue((ROOT / "frontend/themes/wuwa-dangdev/assets/icons.png").is_file())
        self.assertFalse((ROOT / "frontend/themes/wuwa-dangdev/assets/nte-logo.png").exists())
        self.assertFalse((ROOT / "frontend/themes/wuwa-dangdev/assets/cursor-default.png").exists())
        self.assertFalse((ROOT / "frontend/themes/wuwa-dangdev/assets/cursor-pointer.png").exists())
        self.assertIn('cyberLogo.src = nte ? "assets/NTE_cor.png" : "assets/icon_cor.png"', app)
        self.assertIn('class="watercolor-news"', html)
        self.assertNotIn('class="watercolor-featured"', html)

    def test_nte_custom_font_ui_is_enabled(self):
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        style = (ROOT / "frontend/style.css").read_text(encoding="utf-8")
        launcher = (ROOT / "launcher.py").read_text(encoding="utf-8")

        self.assertNotIn('body[data-game="nte"] #dock-tab-font', style)
        self.assertNotIn('body[data-game="nte"] #drawer-item-font', style)
        self.assertNotIn('activeGameId === "nte" && tab === "font"', app)
        self.assertIn('id="font-page-subtitle"', html)
        self.assertIn('id="modern-font-subtitle"', html)
        self.assertIn('game_context.install_custom_font', launcher)
        self.assertIn('game_context.get_font_status', launcher)

    def test_hether_does_not_inherit_cyber_palette(self):
        cyber = (ROOT / "frontend/themes/nte-cyber/theme.css").read_text(encoding="utf-8")
        hether = (ROOT / "frontend/themes/nte-hether/theme.css").read_text(encoding="utf-8")
        shared_rules = cyber.split("/* ── Visibility Rules", 1)[1]

        for color in ("#ff1a53", "#ff4d6d", "#d9043d", "rgba(255, 26, 83", "rgba(255, 77, 109"):
            self.assertNotIn(color, shared_rules)
        self.assertIn("--cyan-rgb: 170, 139, 255", hether)
        self.assertIn("--panel-rgb: 20, 17, 49", hether)
        self.assertIn("--toast-bg: rgba(17, 14, 44, .98)", hether)

    def test_themes_separation(self):
        themes_text = (ROOT / "frontend/themes/themes.js").read_text(encoding="utf-8")
        app_text = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        style_text = (ROOT / "frontend/style.css").read_text(encoding="utf-8")

        # WUWA_THEMES should not contain NTE
        self.assertIn("const WUWA_THEMES = [", themes_text)
        self.assertIn("const NTE_THEMES = [", themes_text)
        self.assertIn("const THEMES = WUWA_THEMES;", themes_text)
        self.assertIn("function getThemesForGame", themes_text)

        # DangDev belongs to WuWa; Cyber and Hether belong to NTE.
        self.assertIn('id: "dangdev"', themes_text)
        self.assertIn('css: "themes/wuwa-dangdev/theme.css"', themes_text)
        self.assertIn('id: "cyber"', themes_text)
        self.assertIn('css: "themes/nte-cyber/theme.css"', themes_text)
        self.assertIn('id: "hether"', themes_text)
        self.assertIn('css: "themes/nte-hether/theme.css"', themes_text)
        self.assertTrue((ROOT / "frontend/themes/nte-hether/theme.css").is_file())
        self.assertNotIn('id: "hethe"', themes_text)
        self.assertFalse((ROOT / "frontend/themes/nte-hethe/theme.css").exists())
        self.assertIn('savedNte = "cyber"', app_text)
        self.assertIn('gameStatus.theme === "hethe" ? "hether" : gameStatus.theme', app_text)
        self.assertIn('themeId === "cyber" || themeId === "hether"', app_text)

        # app.js must use getThemesForGame and manage savedNteTheme
        self.assertIn("getThemesForGame", app_text)
        self.assertIn("savedNteTheme", app_text)
        self.assertIn("switchMediaForGame", app_text)
        self.assertIn("CHƠI NTE", app_text)

        # Theme switching must not be suppressed in NTE mode
        self.assertNotIn('body[data-game="nte"] #dock-tab-theme', style_text)
        self.assertNotIn('body[data-game="nte"] #drawer-item-theme', style_text)
        self.assertNotIn('body[data-game="nte"] #ctx-winedlloverrides', style_text)

    def test_dangdev_secondary_pages_keep_original_layout(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        css = (ROOT / "frontend/themes/wuwa-dangdev/theme.css").read_text(encoding="utf-8")

        self.assertIn('if (currentThemeId !== "dangdev") setModernDrawerOpen(false)', app)
        self.assertNotIn('setModernDrawerOpen(currentThemeId === "dangdev", false)', app)
        self.assertIn('currentThemeId !== "dangdev" && sidebarDrawer', app)
        self.assertIn('document.body.classList.toggle("modern-drawer-open", open)', app)
        self.assertIn("--wc-panel:", css)
        self.assertIn("body.theme-dangdev.modern-drawer-open #perf-page", css)
        self.assertIn("body.theme-dangdev #perf-page .perf-container", css)
        self.assertIn("body.theme-dangdev #modern-font-view", css)
        self.assertIn("body.theme-dangdev #theme-page .theme-page-container", css)

    def test_dangdev_sidebar_uses_one_persistent_set_of_icons(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        css = (ROOT / "frontend/themes/wuwa-dangdev/theme.css").read_text(encoding="utf-8")
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")

        self.assertNotIn("drawer-morph-clone", app)
        self.assertIn('sidebarDrawer.inert = !open && !persistentDrawer', app)
        self.assertIn('body.theme-dangdev #sidebar-dock { display: none !important; }', css)
        self.assertIn("body.theme-dangdev #sidebar-drawer.open", css)
        self.assertIn('id="dangdev-sidebar-toggle"', html)
        self.assertIn('body.theme-dangdev #dangdev-sidebar-toggle', css)
        self.assertIn('body.theme-dangdev #sidebar-drawer:not(.open) .drawer-header', css)
        self.assertIn('body.theme-dangdev #sidebar-drawer:not(.open) .drawer-nav-item', css)
        self.assertIn('body.theme-dangdev #sidebar-drawer:not(.open) .drawer-music-ctrl', css)
        self.assertIn('margin-top: max(8px, calc((100vh - 410px) / 2))', css)

    def test_modern_sidebar_morphs_without_wine_button(self):
        css = (ROOT / "frontend/themes/wuwa-modern/theme.css").read_text(encoding="utf-8")
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn('body.theme-modern #sidebar-dock { display: none !important; }', css)
        self.assertIn('body.theme-modern #sidebar-drawer.open', css)
        self.assertIn('body.theme-modern #drawer-item-winedll', css)
        self.assertIn('body.theme-modern .drawer-vol-label { display: none; }', css)
        self.assertIn('currentThemeId === "modern"', app)

    def test_game_switcher_shows_each_game_icon(self):
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        style = (ROOT / "frontend/style.css").read_text(encoding="utf-8")

        self.assertIn('id="game-switch-trigger"', html)
        self.assertIn('id="game-switch-menu"', html)
        self.assertIn('src="assets/icon.png"', html)
        self.assertIn('src="assets/NTE.png"', html)
        self.assertIn('gameSwitchIcon.src = nte ? "assets/NTE.png" : "assets/icon.png"', app)
        self.assertIn('#game-switch-menu[hidden]', style)
        self.assertIn('body.theme-cyber #game-switch-trigger', style)
        self.assertNotIn('game-switch-eyebrow', html)

    def test_theme_polish_and_nte_launcher_controls(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        style = (ROOT / "frontend/style.css").read_text(encoding="utf-8")
        dangdev = (ROOT / "frontend/themes/wuwa-dangdev/theme.css").read_text(encoding="utf-8")

        self.assertIn("body.theme-dangdev #drawer-item-winedll", dangdev)
        self.assertIn("body.theme-dangdev .drawer-vol-label", dangdev)
        self.assertIn("drop-shadow(0 0 10px", dangdev)
        self.assertIn("transition: width .36s", dangdev)
        self.assertIn("body.theme-dangdev #sidebar-drawer.open", dangdev)
        self.assertNotIn("mask: url(\"assets/icons.png\")", dangdev)
        self.assertIn('sidebarDock.inert = open || persistentDrawer', app)
        self.assertIn("appearance: none", style)
        self.assertNotIn('body[data-game="nte"] #ctx-update-launcher', style)
        self.assertNotIn('if (activeGameId !== "wuwa") return;', app[app.index("function openLauncherModal"):app.index("function closeLauncherModal")])
        self.assertIn('const officialType = activeGameId === "nte" ? "official" : "steam"', app)
        self.assertIn('id="opt-nte-steam"', (ROOT / "frontend/index.html").read_text(encoding="utf-8"))
        self.assertIn('cyber-platform-badge ${curr === "heroic" ? "heroic" : curr === "steam" ? "steam" : "official"}', app)
        self.assertIn('nteSteamBadge', app)

    def test_theme_name_glow_and_grouped_quick_menu(self):
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        style = (ROOT / "frontend/style.css").read_text(encoding="utf-8")
        themes = (ROOT / "frontend/themes/themes.js").read_text(encoding="utf-8")
        dangdev = (ROOT / "frontend/themes/wuwa-dangdev/theme.css").read_text(encoding="utf-8")

        self.assertIn('name: "Huyền Sắc"', themes)
        self.assertNotIn("DangDevVH Original", themes)
        self.assertEqual(html.count('<section class="ctx-group'), 4)
        self.assertIn('class="ctx-group-title"', html)
        self.assertIn(".ctx-group-title", style)
        self.assertIn("const menuWidth = ctxMenu.offsetWidth || 280", app)
        self.assertIn("const menuHeight = ctxMenu.offsetHeight", app)
        self.assertIn("body.theme-dangdev .drawer-nav-item.active", dangdev)
        self.assertIn("body.theme-dangdev .launcher-tag.steam", dangdev)
        self.assertIn("body.theme-dangdev .drawer-collapse-btn", dangdev)
        quick_menu = html[html.index('id="ctx-menu"'):html.index("</div>\n\n  </div>", html.index('id="ctx-menu"'))]
        self.assertEqual(quick_menu.count('class="ctx-icon"'), 9)
        self.assertIn('id="ctx-dx11" role="menuitemcheckbox"', quick_menu)
        self.assertIn('class="ctx-dx11-unavailable">NTE chưa hỗ trợ', quick_menu)
        self.assertIn('class="ctx-dx11-state" aria-hidden="true">BẬT', quick_menu)
        self.assertNotIn('id="toggle-dx11-', html)
        self.assertNotIn('toggle-dx11-', app)
        self.assertEqual(quick_menu.count("<svg"), 9)
        self.assertNotIn(">▣<", quick_menu)
        self.assertNotIn(">□<", quick_menu)

    def test_wine_dll_overrides_ui(self):
        html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
        app_text = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn('id="ctx-winedlloverrides"', html)
        self.assertIn('id="drawer-item-winedll"', html)
        self.assertNotIn('id="btn-modal-winedll"', html)
        self.assertIn("drawerItemWineDll", app_text)

    def test_dx11_quick_menu_is_disabled_for_nte(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")
        update = app[app.index("function updateLaunchOptionsUI() {"):app.index("async function toggleDx11(")]
        script = "\n".join((
            "const assert = require('node:assert/strict');",
            "const state = {};",
            "const menu = {setAttribute(key, value) { this[key] = value; }, querySelector: () => state};",
            "const document = {getElementById: () => menu};",
            "let activeGameId = 'wuwa', isDx11Enabled = true;",
            update,
            "updateLaunchOptionsUI(); assert.equal(menu.disabled, false); assert.equal(menu['aria-checked'], 'true'); assert.equal(state.textContent, 'BẬT');",
            "isDx11Enabled = false; updateLaunchOptionsUI(); assert.equal(menu['aria-checked'], 'false'); assert.equal(state.textContent, 'TẮT');",
            "activeGameId = 'nte'; updateLaunchOptionsUI(); assert.equal(menu.disabled, true); assert.equal(menu['aria-checked'], 'false');",
            "activeGameId = 'wuwa'; isDx11Enabled = true; updateLaunchOptionsUI(); assert.equal(menu.disabled, false); assert.equal(menu['aria-checked'], 'true'); assert.equal(state.textContent, 'BẬT');",
        ))
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_game_context_web_assets(self):
        from backend import game_context, nte

        assets = nte.get_web_assets()
        self.assertTrue(len(assets) >= 2)
        filenames = [item[0] for item in assets]
        self.assertIn("nte-bgm.mp3", filenames)
        self.assertIn("nte-bg-video.mp4", filenames)

    def test_remote_version_notes_are_rendered_as_text(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("newsContent.textContent = noteText", app)
        self.assertIn("newsContentModern.textContent = noteText", app)
        self.assertIn("newsContentCyber.textContent = noteText", app)
        self.assertNotIn("innerHTML = noteHtml", app)

    def test_game_switch_ignores_stale_status_and_avoids_double_media_load(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("const requestedGame = activeGameId", app)
        self.assertIn("requestedGame !== activeGameId || (status.game && status.game !== activeGameId)", app)
        self.assertIn("let mediaInitialized = false", app)
        self.assertIn("if (mediaInitialized) switchMediaForGame(activeGameId, resumeMedia)", app)
        self.assertIn("applyGameUI(gameId, true)", app)

    def test_nte_startup_auto_updates_missing_or_outdated_translation(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn('const needsTranslationUpdate = activeGameId === "nte"', app)
        self.assertIn('!gameStatus.installed_vh || gameStatus.vh_version !== serverInfo.version', app)
        self.assertIn("if (needsTranslationUpdate)", app)

    def test_nte_performance_choices_are_restored_in_the_ui(self):
        app = (ROOT / "frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("nteCommonDeviceProfiles.checked = common.includes(\"device_profiles\")", app)
        self.assertIn("nteCommonGame.checked = common.includes(\"game\")", app)
        self.assertIn("nteCommonInput.checked = common.includes(\"input\")", app)
        self.assertNotIn("Preset AlteriaX/NTE-Configs đã được ghim phiên bản", app)
        self.assertIn("perfDetailSubtitle.hidden = true", app)


if __name__ == "__main__":
    unittest.main()
