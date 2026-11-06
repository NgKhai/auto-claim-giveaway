"""Independent source-reader API acceptance; deterministic fixtures, no Internet."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sqlite3
import tempfile
import threading
import time
import unittest

import httpx
from fastapi.testclient import TestClient
from hunter.app import create_app

SOURCE = 'github-education'
CONTENT = b'# Official fixture\nEligible students must verify enrollment.\n'


class SourceApiAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = self.tmp.name + '/sources.db'
        self.calls = []
        self.behavior = lambda req: httpx.Response(200, content=CONTENT, headers={'content-type': 'text/plain'})
        def handler(request):
            self.calls.append(request)
            return self.behavior(request)
        self.transport = httpx.MockTransport(handler)
        self.app = create_app(self.path, source_transport=self.transport)
        self.client = TestClient(self.app)
        self.alice = self.register(self.client, 'alice@example.test')

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def register(self, client, email):
        response = client.post('/api/auth/register', json={
            'email': email, 'password': 'SourceTestPassword123!', 'country': 'VN'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def refresh(self, client=None, user=None, source=SOURCE):
        return (client or self.client).post(f'/api/sources/{source}/refresh', json={},
                    headers={'X-CSRF-Token': (user or self.alice)['csrf_token']})

    def test_auth_csrf_and_unknown_sources_never_fetch(self):
        with TestClient(self.app) as anonymous:
            self.assertEqual(anonymous.get('/api/sources').status_code, 401)
            self.assertEqual(anonymous.post(f'/api/sources/{SOURCE}/refresh', json={}).status_code, 401)
        self.assertEqual(self.client.post(f'/api/sources/{SOURCE}/refresh', json={}).status_code, 403)
        self.assertEqual(self.refresh(source='arbitrary-provider').status_code, 404)
        self.assertEqual(self.calls, [])

    def test_success_preserves_evidence_and_never_authorizes_real_application(self):
        initial = self.client.get('/api/sources').json()
        self.assertEqual(len(initial), 1)
        self.assertEqual(initial[0]['status'], 'not_fetched')
        response = self.refresh()
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['status'], 'fresh')
        self.assertEqual(result['evidence']['content_hash'], hashlib.sha256(CONTENT).hexdigest())
        self.assertIn('verify enrollment', result['evidence']['excerpt'])
        for field in ['eligibility', 'deadline', 'automation_status']:
            self.assertEqual(result[field], 'unknown', field)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0].url.host, 'raw.githubusercontent.com')
        self.assertNotIn('alice@example.test', str(self.calls[0].headers))
        rejected = self.client.post('/api/applications', json={'opportunity_id': SOURCE},
                    headers={'X-CSRF-Token': self.alice['csrf_token']})
        self.assertEqual(rejected.status_code, 404)
        self.assertEqual(self.client.get('/api/applications').json(), [])

    def test_source_state_and_export_are_owner_isolated(self):
        self.assertEqual(self.refresh().status_code, 200)
        with TestClient(self.app) as bob:
            user = self.register(bob, 'bob@example.test')
            self.assertEqual(bob.get('/api/sources').json()[0]['status'], 'not_fetched')
            self.assertEqual(self.refresh(bob, user).status_code, 200)
            self.assertEqual(len(self.calls), 2)
            own_export = self.client.get('/api/account/export').json()
            self.assertEqual(len(own_export['sources']), 1)
            self.assertNotIn('bob@example.test', json.dumps(own_export))
            self.assertEqual(self.client.post('/api/account/delete', json={'password': 'SourceTestPassword123!'},
                        headers={'X-CSRF-Token': self.alice['csrf_token']}).status_code, 200)
            self.assertEqual(bob.get('/api/sources').json()[0]['status'], 'fresh')
            with sqlite3.connect(self.path) as connection:
                self.assertEqual(connection.execute('SELECT count(*) FROM source_records WHERE user_id=?',
                                 (self.alice['id'],)).fetchone()[0], 0)

    def test_cooldown_persists_across_application_recreation(self):
        self.assertEqual(self.refresh().status_code, 200)
        with TestClient(create_app(self.path, source_transport=self.transport)) as restarted:
            restarted.cookies.update(self.client.cookies)
            response = self.refresh(restarted)
            self.assertEqual(response.status_code, 429, response.text)
        self.assertEqual(len(self.calls), 1)

    def test_concurrent_refresh_attempts_make_only_one_network_request(self):
        entered = threading.Event()
        release = threading.Event()
        def slow_response(request):
            entered.set()
            release.wait(timeout=5)
            return httpx.Response(200, content=CONTENT, headers={'content-type': 'text/plain'})
        self.behavior = slow_response
        def refresh_in_worker(_):
            with TestClient(self.app) as worker:
                worker.cookies.update(self.client.cookies)
                return self.refresh(worker).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(refresh_in_worker, 1)
            self.assertTrue(entered.wait(timeout=3))
            second = pool.submit(refresh_in_worker, 2)
            try:
                self.assertEqual(second.result(timeout=3), 429)
            finally:
                release.set()
            self.assertEqual(first.result(timeout=3), 200)
        self.assertEqual(len(self.calls), 1)

    def release_cooldown(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute('UPDATE source_records SET last_attempt_at=0 WHERE user_id=?', (self.alice['id'],))

    def test_same_changed_and_failed_fetch_keep_precise_evidence_history(self):
        first = self.refresh().json()['evidence']
        self.assertFalse(first['changed'])
        self.release_cooldown()
        unchanged = self.refresh().json()['evidence']
        self.assertFalse(unchanged['changed'])
        self.assertEqual(unchanged['content_hash'], first['content_hash'])
        self.release_cooldown()
        self.behavior = lambda req: httpx.Response(200, content=b'Changed official fixture', headers={'content-type': 'text/plain'})
        changed = self.refresh().json()['evidence']
        self.assertTrue(changed['changed'])
        self.assertNotEqual(changed['content_hash'], first['content_hash'])
        self.release_cooldown()
        self.behavior = lambda req: httpx.Response(503, content=b'upstream failed')
        self.assertEqual(self.refresh().status_code, 502)
        current = self.client.get('/api/sources').json()[0]
        self.assertEqual(current['evidence'], changed)
        self.assertTrue(current['last_error'])
        self.assertEqual(current['status'], 'unverified')

    def test_freshness_exact_24_hour_boundary_is_stale(self):
        from unittest.mock import patch
        self.refresh()
        now = time.time()
        for age, expected in [(86399, 'fresh'), (86400, 'stale'), (86401, 'stale')]:
            with sqlite3.connect(self.path) as connection:
                connection.execute('UPDATE source_records SET retrieved_at=? WHERE user_id=?',
                                   (now-age, self.alice['id']))
            with patch('hunter.sources.time.time', return_value=now):
                source = self.client.get('/api/sources').json()[0]
                self.assertEqual(source['status'], expected)

    def test_body_bounds_and_invalid_responses_preserve_previous_evidence(self):
        first = self.refresh().json()['evidence']
        scenarios = [
            (b'x' * (256*1024+1), {'content-type': 'text/plain'}),
            (b'\xff', {'content-type': 'text/plain'}),
            (b'{}', {'content-type': 'application/json'}),
            (b'', {'content-type': 'text/plain'}),
            (b'provider error', {'content-type': 'text/plain', 'content-encoding': 'br'}),
        ]
        for content, headers in scenarios:
            with self.subTest(headers=headers, length=len(content)):
                self.release_cooldown()
                self.behavior = lambda req, body=content, h=headers: httpx.Response(200, content=body, headers=h)
                self.assertEqual(self.refresh().status_code, 502)
                source = self.client.get('/api/sources').json()[0]
                self.assertEqual(source['evidence'], first)
                self.assertTrue(source['last_error'])
                self.assertEqual(self.refresh().status_code, 429)

    def test_client_url_override_rejected_and_no_auth_forwarding(self):
        response = self.client.post(f'/api/sources/{SOURCE}/refresh', json={'url': 'http://127.0.0.1/secret'},
                    headers={'X-CSRF-Token': self.alice['csrf_token']})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.refresh().status_code, 200)
        for header in ['authorization', 'cookie', 'x-csrf-token']:
            self.assertNotIn(header, self.calls[0].headers)

    def test_slow_stream_exceeds_total_fetch_budget_without_evidence(self):
        import asyncio
        from unittest.mock import patch
        class SlowStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                await asyncio.sleep(.15)
                yield b'late provider body'
        self.behavior = lambda request: httpx.Response(200, stream=SlowStream(), headers={'content-type': 'text/plain'})
        with patch('hunter.sources.TIMEOUT', .03):
            response = self.refresh()
        self.assertEqual(response.status_code, 502, response.text)
        self.assertIsNone(self.client.get('/api/sources').json()[0]['evidence'])

    def test_account_deleted_during_fetch_cannot_recreate_source_record(self):
        entered = threading.Event()
        release = threading.Event()
        def held_response(request):
            entered.set()
            release.wait(timeout=5)
            return httpx.Response(200, content=CONTENT, headers={'content-type': 'text/plain'})
        self.behavior = held_response
        def worker():
            with TestClient(self.app) as client:
                client.cookies.update(self.client.cookies)
                return self.refresh(client).status_code
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(worker)
            self.assertTrue(entered.wait(timeout=3))
            try:
                response = self.client.post('/api/account/delete', json={'password': 'SourceTestPassword123!'},
                    headers={'X-CSRF-Token': self.alice['csrf_token']})
                self.assertEqual(response.status_code, 200, response.text)
            finally:
                release.set()
            self.assertEqual(pending.result(timeout=3), 401)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM source_records WHERE user_id=?',
                             (self.alice['id'],)).fetchone()[0], 0)

    def test_redirect_cannot_escape_fixed_registry_destination(self):
        self.behavior = lambda request: httpx.Response(302, headers={'location': 'http://127.0.0.1/secret'})
        response = self.refresh()
        self.assertEqual(response.status_code, 502, response.text)
        self.assertEqual(len(self.calls), 1)
        self.assertNotEqual(self.client.get('/api/sources').json()[0]['status'], 'fresh')
        self.assertEqual(self.refresh().status_code, 429)

    def test_timeout_fails_safely_and_does_not_leak_exception_details(self):
        def fail(request):
            raise httpx.ReadTimeout('private token SECRET-NEVER-EXPOSE', request=request)
        self.behavior = fail
        response = self.refresh()
        self.assertEqual(response.status_code, 502, response.text)
        self.assertNotIn('SECRET-NEVER-EXPOSE', response.text)
        source = self.client.get('/api/sources').json()[0]
        self.assertNotIn('SECRET-NEVER-EXPOSE', json.dumps(source))
        self.assertIsNone(source['evidence'])
        self.assertEqual(self.refresh().status_code, 429)


if __name__ == '__main__':
    unittest.main()
