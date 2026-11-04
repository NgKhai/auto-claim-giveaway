"""Independent API acceptance tests for the sandbox increment."""
import tempfile
import unittest
from fastapi.testclient import TestClient
from hunter.app import create_app


class ApiAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = self.tmp.name + '/acceptance.db'
        self.app = create_app(self.db)
        self.client = TestClient(self.app)
        response = self.client.post('/api/auth/register', json={
            'email': 'alice@example.test', 'password': 'DistinctPassword123!', 'country': 'VN'})
        self.assertEqual(response.status_code, 201, response.text)
        self.csrf = response.json()['csrf_token']

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def post(self, path, body=None):
        return self.client.post(path, json=body or {}, headers={'X-CSRF-Token': self.csrf})

    def application(self):
        response = self.post('/api/applications', {'opportunity_id': 'sandbox-credits'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_unauthenticated_access_cannot_read_or_mutate_account_data(self):
        with TestClient(self.app) as stranger:
            for path in ['/api/me', '/api/goals', '/api/applications', '/api/audit']:
                self.assertEqual(stranger.get(path).status_code, 401, path)
            self.assertEqual(stranger.post('/api/applications', json={
                'opportunity_id': 'sandbox-credits'}).status_code, 401)

    def test_wrong_csrf_token_cannot_create_goal(self):
        response = self.client.post('/api/goals', json={'query': 'AI credits'},
                                    headers={'X-CSRF-Token': 'attacker-controlled'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get('/api/goals').json(), [])

    def test_unknown_opportunity_does_not_create_registration(self):
        response = self.post('/api/applications', {'opportunity_id': 'invented-provider'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get('/api/applications').json(), [])

    def test_account_isolation_for_submit_revoke_and_audit(self):
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        with TestClient(self.app) as bob:
            signup = bob.post('/api/auth/register', json={
                'email': 'bob@example.test', 'password': 'DifferentPassword123!', 'country': 'VN'})
            self.assertEqual(signup.status_code, 201)
            headers = {'X-CSRF-Token': signup.json()['csrf_token']}
            for action in ['submit', 'revoke', 'approve']:
                response = bob.post(f"/api/applications/{application['id']}/{action}",
                                    json={'version': application['version']}, headers=headers)
                self.assertEqual(response.status_code, 404, action)
            self.assertEqual(bob.get('/api/applications').json(), [])
            audit = bob.get('/api/audit').json()
            self.assertNotIn(application['id'], str(audit))

    def test_application_survives_process_recreation(self):
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        result = self.post(f"/api/applications/{application['id']}/submit")
        self.assertEqual(result.status_code, 200, result.text)
        receipt = result.json()['receipt']
        self.assertTrue(receipt)
        with TestClient(create_app(self.db)) as restarted:
            login = restarted.post('/api/auth/login', json={
                'email': 'alice@example.test', 'password': 'DistinctPassword123!'})
            self.assertEqual(login.status_code, 200)
            saved = restarted.get('/api/applications').json()
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]['status'], 'submitted')
            self.assertEqual(saved[0]['receipt'], receipt)
            again = restarted.post(f"/api/applications/{application['id']}/submit", json={},
                headers={'X-CSRF-Token': login.json()['csrf_token']})
            self.assertEqual(again.status_code, 200)
            self.assertEqual(again.json()['receipt'], receipt)

    def test_unmatched_search_returns_honest_empty_result(self):
        goal = self.post('/api/goals', {'query': 'zzzz-unmatched-quantum-potato'}).json()
        response = self.client.get('/api/opportunities', params={'goal_id': goal['id']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_payload_tampered_after_approval_cannot_execute(self):
        import sqlite3
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        with sqlite3.connect(self.db) as connection:
            connection.execute('UPDATE applications SET payload=? WHERE id=?',
                               ('{"email":"different@example.test"}', application['id']))
        response = self.post(f"/api/applications/{application['id']}/submit")
        self.assertEqual(response.status_code, 409)
        self.assertIsNone(self.client.get('/api/applications').json()[0]['receipt'])

    def test_opportunity_policy_rechecked_after_approval(self):
        from unittest.mock import patch
        from hunter.app import OPPORTUNITIES
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        with patch.dict(OPPORTUNITIES['sandbox-credits'], {'deadline': '2020-01-01T00:00:00+00:00'}):
            response = self.post(f"/api/applications/{application['id']}/submit")
        self.assertEqual(response.status_code, 409)
        self.assertIsNone(self.client.get('/api/applications').json()[0]['receipt'])

    def test_expired_approval_cannot_execute(self):
        import sqlite3
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        with sqlite3.connect(self.db) as connection:
            connection.execute('UPDATE applications SET approval_expires=0 WHERE id=?', (application['id'],))
        self.assertEqual(self.post(f"/api/applications/{application['id']}/submit").status_code, 409)
        self.assertIsNone(self.client.get('/api/applications').json()[0]['receipt'])

    def test_changed_adapter_descriptor_invalidates_approval(self):
        from unittest.mock import patch
        from hunter.app import OPPORTUNITIES
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        with patch.dict(OPPORTUNITIES['sandbox-credits'], {'source_url': 'sandbox://different-destination'}):
            response = self.post(f"/api/applications/{application['id']}/submit")
        self.assertEqual(response.status_code, 409)

    def test_cross_origin_authentication_request_is_denied(self):
        response = self.client.post('/api/auth/login', json={
            'email': 'alice@example.test', 'password': 'DistinctPassword123!'},
            headers={'Origin': 'https://attacker.example'})
        self.assertEqual(response.status_code, 403)

    def test_concurrent_submit_creates_one_receipt_and_one_audit_event(self):
        from concurrent.futures import ThreadPoolExecutor
        application = self.application()
        self.post(f"/api/applications/{application['id']}/approve", {'version': application['version']})
        def submit(_):
            with TestClient(self.app) as worker:
                worker.cookies.update(self.client.cookies)
                response = worker.post(f"/api/applications/{application['id']}/submit", json={},
                    headers={'X-CSRF-Token': self.csrf})
                return response.status_code, response.json().get('receipt')
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(submit, range(4)))
        self.assertEqual([status for status, _ in results], [200] * 4)
        self.assertEqual(len({receipt for _, receipt in results}), 1)
        events = [event for event in self.client.get('/api/audit').json()
                  if event['action'] == 'sandbox_submitted']
        self.assertEqual(len(events), 1)

    def test_login_failure_does_not_establish_session(self):
        with TestClient(self.app) as stranger:
            response = stranger.post('/api/auth/login', json={
                'email': 'alice@example.test', 'password': 'wrong-password'})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(stranger.get('/api/me').status_code, 401)

    def test_client_cannot_replace_registration_payload_with_sensitive_data(self):
        response = self.post('/api/applications', {
            'opportunity_id': 'sandbox-credits',
            'payload': {'password': 'sensitive', 'card_number': '4242424242424242'}})
        # Reject unknown input or discard it; never persist attacker-selected fields.
        if response.status_code == 201:
            self.assertNotIn('card_number', response.json()['payload'])
            self.assertNotIn('password', response.json()['payload'])
        else:
            self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
