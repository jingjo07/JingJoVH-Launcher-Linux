"""Check the author dialog's keyboard behavior without starting GTK."""

from pathlib import Path
import subprocess
import unittest


APP_JS = Path(__file__).parents[1] / "frontend/app.js"
INDEX_HTML = APP_JS.with_name("index.html")


class CreditModalTests(unittest.TestCase):
    def test_focus_stays_in_dialog_and_returns_to_menu(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('id="credit-modal" role="dialog" aria-modal="true"', html)
        self.assertIn('<button type="button" class="credit-community"', html)
        app = APP_JS.read_text(encoding="utf-8")
        start = app.index("// ── Credit / About Modal")
        end = app.index("function updateLauncherModalUI", start)
        script = f"""
            const assert = require('node:assert/strict');
            const classes = new Set();
            const attributes = {{}};
            const document = {{activeElement: null, getElementById: () => modal}};
            const closeButton = {{focus() {{ document.activeElement = this; }}}};
            const communityButton = {{focus() {{ document.activeElement = this; }}}};
            let onKeydown;
            const modal = {{
              classList: {{add: value => classes.add(value), remove: value => classes.delete(value)}},
              setAttribute: (name, value) => attributes[name] = value,
              querySelector: () => closeButton,
              querySelectorAll: () => [closeButton, communityButton],
              addEventListener: (_, handler) => onKeydown = handler,
            }};
            const menuToggleClassic = {{focus() {{ document.activeElement = this; }}}};
            const menuToggleModern = null;
            const btnMenuToggleCyber = null;
            const currentThemeId = 'classic';
            const ipc = () => Promise.resolve();
            const window = {{}};
            {app[start:end]}
            openCreditModal();
            assert(classes.has('visible'));
            assert.equal(attributes['aria-hidden'], 'false');
            assert.equal(document.activeElement, closeButton);
            document.activeElement = communityButton;
            let prevented = false;
            onKeydown({{key: 'Tab', shiftKey: false, preventDefault() {{ prevented = true; }}}});
            assert(prevented);
            assert.equal(document.activeElement, closeButton);
            prevented = false;
            onKeydown({{key: 'Tab', shiftKey: true, preventDefault() {{ prevented = true; }}}});
            assert(prevented);
            assert.equal(document.activeElement, communityButton);
            closeCreditModal();
            assert.equal(attributes['aria-hidden'], 'true');
            assert.equal(document.activeElement, menuToggleClassic);
        """
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
