"""Optional deterministic analysis browser acceptance, no live upstream claims.
Run python docs/quality/analysis_browser_smoke.py; Playwright + system Chromium.
"""
import ast
import copy
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
parsed = ast.parse((ROOT / 'tests/test_analysis_api.py').read_text())
TEXT = next(ast.literal_eval(node.value) for node in parsed.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == 'CHECKLIST' for target in node.targets))
with tempfile.TemporaryDirectory() as tmp:
    db = str(Path(tmp) / 'analysis-browser.db')
    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]; sock.close()
    runner = Path(tmp) / 'fixture.py'
    runner.write_text('''import sys
sys.path.insert(0,sys.argv[1])
import httpx
import uvicorn
from hunter.app import create_app
body=''' + repr(TEXT) + '''
transport=httpx.MockTransport(lambda request:httpx.Response(200,text=body,headers={'content-type':'text/plain'}))
app=create_app(sys.argv[2],source_transport=transport)
uvicorn.run(app,host='127.0.0.1',port=int(sys.argv[3]),log_level='error')
''')
    process = subprocess.Popen([sys.executable, str(runner), str(ROOT), db, str(port)],
                               cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        origin = f'http://127.0.0.1:{port}'
        for _ in range(100):
            try:
                with urllib.request.urlopen(origin + '/api/health', timeout=1) as response:
                    if response.status == 200: break
            except OSError: time.sleep(.1)
        else: raise RuntimeError('Fixture app did not start')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium')
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            errors = []; external = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: external.append(request.url) if 'unsafe.example' in request.url else None)
            page.goto(origin); page.locator('#auth-mode').click()
            page.locator('#email').fill('analysis-browser@example.test')
            page.locator('#password').fill('AnalysisBrowserPassword123!')
            page.locator('#auth-submit').click()
            expect(page.locator('#workspace-view')).to_be_visible()
            page.locator('[data-panel="sources"]').click()
            card = page.locator('[data-source-id="github-education"]')
            analysis_button = card.locator('[data-source-analysis="github-education"]')
            analysis_button.click()
            expect(card.locator('.source-analysis')).to_have_attribute('data-analysis-status', 'unknown')
            expect(card.locator('.claim-quote')).to_have_count(0)
            card.locator('[data-source-refresh="github-education"]').click()
            analysis_button.click()
            analysis = card.locator('.source-analysis')
            expect(analysis).to_have_attribute('data-analysis-status', 'candidate_claims')
            expect(card.locator('[data-claim="minimum_age"] .claim-quote')).to_have_text('* Are at least 13 years old.')
            expect(analysis.locator('.claim-quote')).to_have_count(4)
            expect(analysis).to_contain_text('chưa phải kết luận bạn đủ điều kiện')
            api_result = page.request.get(origin + '/api/sources/github-education/analysis').json()
            claim = card.locator('[data-claim="minimum_age"]')
            claim.locator('.claim-provenance summary').click()
            expect(claim).to_contain_text(api_result['content_hash'])
            expect(claim).to_contain_text('github-education-checklist-v1')
            assert analysis.get_by_role('button').count() == 0, 'Analysis acquired an action control'
            # An adversarial API-response fixture tests text-only quote rendering;
            # it does not claim the parser would accept this noncanonical quote.
            malicious = copy.deepcopy(api_result)
            payload = '<img src="https://unsafe.example/pixel" onerror="window.ANALYSIS_EXECUTED=true"><script>window.ANALYSIS_EXECUTED=true</script>'
            malicious['claims']['minimum_age']['citation']['quote'] = payload
            endpoint = '**/api/sources/github-education/analysis'
            page.reload(); page.locator('[data-panel="sources"]').click()
            page.route(endpoint, lambda route: route.fulfill(json=malicious))
            analysis_button.click()
            expect(card.locator('[data-claim="minimum_age"] .claim-quote')).to_have_text(payload)
            assert card.locator('.source-analysis script, .source-analysis img').count() == 0
            assert not page.evaluate('Boolean(window.ANALYSIS_EXECUTED)')
            assert external == [], external
            page.unroute(endpoint)
            with sqlite3.connect(db) as connection:
                connection.execute('UPDATE source_records SET retrieved_at=?', (time.time()-86400+2.5,))
            page.reload(); page.locator('[data-panel="sources"]').click(); analysis_button.click()
            expect(analysis).to_have_attribute('data-analysis-status', 'candidate_claims')
            expect(card).to_contain_text('BẢN LƯU: QUÁ 24 GIỜ', timeout=7000)
            expect(card.locator('.claim-quote')).to_have_count(0)
            with sqlite3.connect(db) as connection:
                connection.execute('UPDATE source_records SET retrieved_at=?', (time.time()-86401,))
            page.reload(); page.locator('[data-panel="sources"]').click(); analysis_button.click()
            expect(analysis).to_have_attribute('data-analysis-status', 'needs_refresh')
            expect(analysis.locator('.claim-quote')).to_have_count(0)
            expect(analysis).to_contain_text('Cần cập nhật nguồn')
            with sqlite3.connect(db) as connection:
                connection.execute('UPDATE source_records SET retrieved_at=?,last_attempt_at=0', (time.time(),))
            page.reload(); page.locator('[data-panel="sources"]').click()
            alice_result = page.request.get(origin + '/api/sources/github-education/analysis').json()
            pending = []
            page.route(endpoint, lambda route: pending.append(route))
            analysis_button.click()
            page.wait_for_timeout(100)
            assert pending, 'Expected delayed Alice analysis request'
            page.locator('#logout').click()
            expect(page.locator('#auth-view')).to_be_visible()
            page.locator('#auth-mode').click()
            page.locator('#email').fill('other-analysis-browser@example.test')
            page.locator('#password').fill('OtherAnalysisPassword123!')
            page.locator('#auth-submit').click()
            expect(page.locator('#workspace-view')).to_be_visible()
            page.locator('[data-panel="sources"]').click()
            pending[0].fulfill(json=alice_result)
            page.wait_for_timeout(100)
            expect(card.locator('.source-analysis')).to_have_count(0)
            expect(card).to_contain_text('Chưa truy xuất')
            page.unroute(endpoint)
            analysis_button.click()
            expect(analysis).to_have_attribute('data-analysis-status', 'unknown')
            expect(analysis.locator('.claim-quote')).to_have_count(0)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            assert not errors, errors
            browser.close()
        print('PASS analysis browser: missing→candidate exactquotes/provenance→adversarial quote inert→open-page expiry clears candidates→stale unknown→delayed prior-owner response ignored→new owner unknown; no JS errors')
    finally:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
