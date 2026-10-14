"""Check the guided tour highlights real controls and restores the UI."""

from pathlib import Path
import subprocess
import unittest


FRONTEND = Path(__file__).parents[1] / "frontend"


class HelpTourTests(unittest.TestCase):
    def test_tour_moves_from_game_to_menu_and_closes_cleanly(self):
        html = (FRONTEND / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="help-trigger"', html)
        self.assertIn('id="help-card" role="dialog" aria-modal="true"', html)

        app = (FRONTEND / "app.js").read_text(encoding="utf-8")
        start = app.index("// ── Help Modal")
        end = app.index("// ── Credit / About Modal", start)
        script = f"""
            const assert = require('node:assert/strict');
            const elements = new Map();
            const menus = [];
            const saved = new Map();
            let focused, currentTab = 'home';
            const document = {{
              activeElement: null,
              body: {{classList: {{add() {{}}, remove() {{}}}}}},
              getElementById(id) {{
                if (!elements.has(id)) elements.set(id, {{
                  id, style: {{}}, hidden: false, innerHTML: '', textContent: '',
                  offsetWidth: 370, offsetHeight: 220, handlers: {{}},
                  addEventListener(type, fn) {{ this.handlers[type] = fn; }},
                  focus() {{ focused = id; document.activeElement = this; }},
                  getClientRects() {{ return [true]; }},
                  getBoundingClientRect() {{ return {{ left: 900, top: 400, width: 120, height: 36 }}; }}
                }});
                return elements.get(id);
              }}
            }};
            const window = {{innerWidth: 1280, innerHeight: 720, addEventListener() {{}}}};
            const localStorage = {{getItem: key => saved.get(key) ?? null, setItem: (key, value) => saved.set(key, value)}};
            const sidebarDrawer = {{classList: {{contains: () => false}}}};
            const ctxMenu = {{getBoundingClientRect: () => ({{left: 870, right: 1150}})}};
            let currentThemeId = 'classic', activeGameId = 'wuwa';
            const usesNteControls = theme => theme === 'cyber' || theme === 'hether';
            const setGameSwitchOpen = () => {{}};
            const setModernDrawerOpen = () => {{}};
            const switchTab = tab => currentTab = tab;
            const toggleMenu = open => menus.push(open);
            const tour = document.getElementById('help-tour');
            tour.hidden = true;
            tour.querySelectorAll = () => Array.from({{length: 4}}, () => ({{style: {{}}}}));
            const card = document.getElementById('help-card');
            card.querySelectorAll = () => [document.getElementById('help-skip'), document.getElementById('help-next')];
            {app[start:end]}
            showFirstRunHelp();
            assert.equal(tour.hidden, false);
            assert.equal(saved.get('wuwavh_help_seen'), '1');
            assert.equal(focused, 'help-next');
            const next = document.getElementById('help-next');
            next.handlers.click();
            assert.equal(document.getElementById('help-title').textContent, 'Chọn game');
            next.handlers.click();
            next.handlers.click();
            assert.equal(document.getElementById('help-title').textContent, 'Cài hoặc cập nhật Việt hoá');
            assert.equal(menus.at(-1), true);
            assert.equal(document.getElementById('help-spotlight').hidden, false);
            assert(Number.parseFloat(card.style.left) < ctxMenu.getBoundingClientRect().left);
            next.handlers.click();
            next.handlers.click();
            assert.equal(document.getElementById('help-title').textContent, 'DirectX 11 (DXVK)');
            assert.equal(document.getElementById('help-counter').textContent, '6 / 9');
            assert.equal(helpTargetFor(tourSteps[5]).id, 'ctx-dx11');
            assert.equal(menus.at(-1), true);
            document.getElementById('help-skip').handlers.click();
            assert.equal(tour.hidden, true);
            assert.equal(menus.at(-1), false);
            assert.equal(focused, 'help-trigger');
            showFirstRunHelp();
            assert.equal(tour.hidden, true);
            document.getElementById('help-trigger').handlers.click();
            assert.equal(tour.hidden, false);
            document.getElementById('help-skip').handlers.click();
            activeGameId = 'nte';
            currentThemeId = 'cyber';
            document.getElementById('help-trigger').handlers.click();
            for (let i = 0; i < 5; i++) next.handlers.click();
            assert.equal(document.getElementById('help-title').textContent, 'Bật Việt hoá trong Wine/Proton');
            assert.equal(document.getElementById('help-counter').textContent, '6 / 8');
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
