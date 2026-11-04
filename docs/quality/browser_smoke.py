"""Optional real-browser acceptance: python docs/quality/browser_smoke.py.
Requires Playwright and system Chromium; uses a temporary database/server.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as tmp:
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    environment = dict(os.environ, HUNTER_DB_PATH=f'{tmp}/browser.db')
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'hunter.app:app',
                                '--host', '127.0.0.1', '--port', str(port)],
                               cwd=ROOT, env=environment, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    try:
        origin = f'http://127.0.0.1:{port}'
        for attempt in range(100):
            try:
                with urllib.request.urlopen(origin + '/api/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError('Application did not become healthy')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium')
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(origin)
            page.locator('#auth-mode').click()
            page.locator('#email').fill('browser@example.test')
            page.locator('#password').fill('BrowserTestPassword123!')
            page.locator('#auth-submit').click()
            expect(page.locator('#workspace-view')).to_be_visible()
            page.locator('#goal-query').fill('credits')
            page.locator('#goal-form button').click()
            expect(page.locator('#current-goal')).to_have_text('credits')
            eligible = page.locator('.opportunity-card').filter(has_text='#sandbox-credits')
            expect(eligible).to_have_count(1)
            eligible.get_by_role('button').click()
            expect(page.locator('#tracking-panel')).to_be_visible()
            page.get_by_role('button', name='Xem & duyệt dữ liệu').click()
            expect(page.locator('#approval-dialog')).to_be_visible()
            expect(page.locator('#approval-details')).to_contain_text('browser@example.test')
            expect(page.locator('#approval-dialog')).to_contain_text('sandbox.register')
            expect(page.locator('#approval-dialog')).to_contain_text('sandbox://opportunity-hunter/credits')
            expect(page.locator('#approval-details')).to_contain_text('Phiên bản adapter')
            expect(page.locator('#approval-version')).to_contain_text('15 phút')
            page.locator('#approval-confirm').click()
            page.get_by_role('button', name='Gửi trong sandbox').click()
            expect(page.locator('#applications')).to_contain_text('Đã gửi trong sandbox')
            expect(page.locator('#applications')).to_contain_text('Biên nhận sandbox')
            page.reload()
            page.locator('[data-panel="tracking"]').click()
            expect(page.locator('#applications')).to_contain_text('Đã gửi trong sandbox')
            page.locator('[data-panel="activity"]').click()
            audit = page.evaluate("async () => (await fetch('/api/audit')).json()")
            assert audit, 'Expected persisted audit events'
            expected_year = page.evaluate('(seconds) => String(new Date(seconds * 1000).getFullYear())', audit[0]['created_at'])
            times = page.locator('#audit time')
            expect(times.first).to_be_visible()
            for displayed in times.all_text_contents():
                assert expected_year in displayed, f'Audit year mismatch: expected {expected_year}, saw {displayed}'
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile horizontal overflow'
            page.locator('#logout').click()
            expect(page.locator('#auth-view')).to_be_visible()
            assert not errors, errors
            browser.close()
        print('PASS browser signup → goal → approval destination/action → sandbox receipt → reload → audit year → mobile layout → logout; no JS errors')
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
