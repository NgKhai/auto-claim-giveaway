"""Real Chromium acceptance smoke; run with Python providing playwright.
Uses an isolated temporary DB and starts/stops its own local server.
"""
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='aoh-browser-') as directory:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        url = f'http://127.0.0.1:{port}'
        environment = {**os.environ, 'AOH_DB_PATH': str(Path(directory) / 'smoke.db'), 'AOH_SECURE_COOKIES': 'false'}
        process = subprocess.Popen([str(ROOT / '.venv/bin/python'), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read().decode())
                try:
                    with opener.open(url + '/healthz', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.1)
            else:
                raise AssertionError('Server readiness timed out')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True)
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url + '/register')
                page.get_by_label('Email', exact=True).fill('browser@example.test')
                page.get_by_label('Password', exact=True).fill('browser-private-password-123')
                page.get_by_role('button', name='Create account', exact=True).click()
                expect(page.get_by_text('Research catalog', exact=True)).to_be_visible()
                page.get_by_label('Your goal', exact=True).fill('Find cloud credits for coding')
                page.get_by_role('button', name='Save goal', exact=True).click()
                expect(page.locator('.goal')).to_have_text('Find cloud credits for coding')
                page.get_by_label('Search research leads', exact=True).fill('cloud')
                page.get_by_role('button', name='Search', exact=True).click()
                expect(page.locator('.opportunity')).to_have_count(1)
                page.get_by_role('button', name='Track this lead', exact=True).click()
                expect(page.locator('.application')).to_have_count(1)
                expect(page.locator('.application')).to_contain_text('needs user action')
                page.get_by_role('button', name='Recheck eligibility', exact=True).click()
                expect(page.locator('.application')).to_contain_text('needs user action')
                page.get_by_role('button', name='Cancel tracking', exact=True).click()
                expect(page.locator('.application')).to_contain_text('cancelled')
                page.set_viewport_size({'width': 390, 'height': 844})
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile horizontal overflow'
                page.get_by_role('button', name='Sign out', exact=True).click()
                expect(page.get_by_role('heading', name='Welcome back')).to_be_visible()
                page.get_by_label('Email', exact=True).fill('browser@example.test')
                page.get_by_label('Password', exact=True).fill('browser-private-password-123')
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page.locator('.goal')).to_have_text('Find cloud credits for coding')
                expect(page.locator('.application')).to_contain_text('cancelled')
                assert not errors, errors
                browser.close()
                print('PASS: real Chromium signup, goal, search, track, recheck, cancel, mobile layout, logout/login persistence; no page errors')
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
