"""Independent deployment boundary acceptance; no external network or credentials."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from fastapi.testclient import TestClient
from hunter.config import ConfigurationError, Settings
from hunter.app import create_app


class DeploymentAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'production.sqlite3')
        self.env = {
            'HUNTER_ENV': 'production',
            'HUNTER_ALLOWED_HOSTS': 'hunter.example.test',
            'HUNTER_TRUSTED_ORIGINS': 'https://hunter.example.test',
            'HUNTER_DB_PATH': self.db,
            'HUNTER_SECURE_COOKIE': '1',
        }

    def tearDown(self):
        self.tmp.cleanup()

    def settings(self, **changes):
        return Settings.from_env({**self.env, **changes})

    def register(self, client, email='production@example.test', origin=None):
        headers = {} if origin is None else {'Origin': origin}
        return client.post('/api/auth/register', json={
            'email': email, 'password': 'ProductionTestPassword123!', 'country': 'VN'}, headers=headers)

    def user_count(self):
        with sqlite3.connect(self.db) as connection:
            return connection.execute('SELECT count(*) FROM users').fetchone()[0]

    def test_incomplete_or_invalid_production_configuration_is_rejected(self):
        invalid = {
            'HUNTER_ENV': ['prod', 'staging', ''],
            'HUNTER_DB_PATH': ['', 'relative.db'],
            'HUNTER_SECURE_COOKIE': ['', '0', 'false', 'yes'],
            'HUNTER_ALLOWED_HOSTS': ['', '*', '*.example.test', 'https://hunter.example.test',
                                     'hunter.example.test/path', 'hunter.example.test:443',
                                     'user@hunter.example.test', 'hunter.example.test,,other.example.test'],
            'HUNTER_TRUSTED_ORIGINS': ['', 'http://hunter.example.test', 'https://other.example.test',
                'https://user:password@hunter.example.test', 'https://hunter.example.test/path',
                'https://hunter.example.test?query=1', 'https://hunter.example.test#fragment',
                'https://hunter.example.test:0', 'https://hunter.example.test:99999',
                'https://hunter.example.test,'],
        }
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ConfigurationError):
                        self.settings(**{key: value})

    def test_settings_are_immutable_and_direct_replacement_still_validates(self):
        from dataclasses import FrozenInstanceError, replace
        settings = self.settings()
        with self.assertRaises(FrozenInstanceError):
            settings.secure_cookie = False
        for changes in [{'secure_cookie': False}, {'secure_cookie': '0'}, {'allowed_hosts': ('*',)},
                        {'trusted_origins': ('http://hunter.example.test',)}, {'db_path': 'relative.db'}]:
            with self.subTest(changes=changes):
                with self.assertRaises(ConfigurationError):
                    replace(settings, **changes)

    def test_configuration_error_omits_unsafe_setting_value(self):
        with self.assertRaises(ConfigurationError) as captured:
            self.settings(HUNTER_TRUSTED_ORIGINS='https://private-user:PRIVATE-SECRET@hunter.example.test')
        self.assertNotIn('PRIVATE-SECRET', str(captured.exception))
        self.assertNotIn('private-user', str(captured.exception))

    def test_production_http_and_spoofed_forwarded_proto_cannot_mutate(self):
        with TestClient(create_app(settings=self.settings()), base_url='http://hunter.example.test') as client:
            health = client.get('/api/health')
            self.assertEqual(health.status_code, 200)
            for headers in [{}, {'X-Forwarded-Proto': 'https'}]:
                response = client.post('/api/auth/register', json={
                    'email': 'http-denied@example.test', 'password': 'ProductionTestPassword123!', 'country': 'VN'},
                    headers=headers)
                self.assertIn(response.status_code, [400, 403, 426], response.text)
            self.assertEqual(self.user_count(), 0)
            self.assertIn(client.get('/').status_code, [400, 403, 426])

    def test_unknown_host_is_rejected_before_user_mutation(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://attacker.example') as client:
            response = self.register(client, origin='https://attacker.example')
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(self.user_count(), 0)

    def test_matching_forged_host_and_origin_cannot_authorize_request(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://hunter.example.test') as client:
            response = client.post('/api/auth/register', json={
                'email': 'forged@example.test', 'password': 'ProductionTestPassword123!', 'country': 'VN'},
                headers={'Host': 'attacker.example', 'Origin': 'https://attacker.example'})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.user_count(), 0)

    def test_allowed_host_does_not_make_unconfigured_origin_trusted(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://hunter.example.test') as client:
            for origin in ['', 'https://attacker.example', 'http://hunter.example.test',
                           'https://hunter.example.test.attacker.example', 'null']:
                with self.subTest(origin=origin):
                    self.assertEqual(self.register(client, origin=origin).status_code, 403)
            self.assertEqual(self.user_count(), 0)

    def test_trusted_https_origin_authentication_sets_secure_cookie_and_hsts(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://hunter.example.test') as client:
            response = self.register(client, origin='https://hunter.example.test')
            self.assertEqual(response.status_code, 201, response.text)
            cookie = response.headers['set-cookie'].lower()
            self.assertIn('secure', cookie)
            self.assertIn('httponly', cookie)
            self.assertIn('samesite=strict', cookie)
            self.assertIn('max-age=', response.headers.get('strict-transport-security', '').lower())
            self.assertEqual(client.get('/api/me').status_code, 200)
            goal = client.post('/api/goals', json={'query': 'authorized production fixture'},
                headers={'Origin': 'https://hunter.example.test', 'X-CSRF-Token': response.json()['csrf_token']})
            self.assertEqual(goal.status_code, 201)

    def test_ambiguous_origin_and_malformed_host_fail_before_mutation(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://hunter.example.test') as client:
            body = {'email': 'ambiguous@example.test', 'password': 'ProductionTestPassword123!', 'country': 'VN'}
            response = client.post('/api/auth/register', json=body, headers=[
                ('Origin', 'https://hunter.example.test'), ('Origin', 'https://attacker.example')])
            self.assertEqual(response.status_code, 403)
            for host in ['hunter.example.test:', 'hunter.example.test:bad',
                         'hunter.example.test:99999', 'hunter.example.test/path']:
                with self.subTest(host=host):
                    response = client.post('/api/auth/register', json=body, headers={
                        'Host': host, 'Origin': 'https://hunter.example.test'})
                    self.assertEqual(response.status_code, 400)
            self.assertEqual(self.user_count(), 0)

    def test_no_origin_nonbrowser_request_still_requires_authenticated_csrf(self):
        with TestClient(create_app(settings=self.settings()), base_url='https://hunter.example.test') as client:
            response = self.register(client)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(client.post('/api/goals', json={'query': 'blocked'}).status_code, 403)
            good = client.post('/api/goals', json={'query': 'explicit csrf'},
                headers={'X-CSRF-Token': response.json()['csrf_token']})
            self.assertEqual(good.status_code, 201)
            self.assertEqual(len(client.get('/api/goals').json()), 1)

    def test_development_defaults_remain_local_and_insecure_cookie_only_for_development(self):
        settings = Settings.from_env({})
        self.assertEqual(settings.environment, 'development')
        self.assertFalse(settings.secure_cookie)
        for host in ['localhost', '127.0.0.1', '::1', 'testserver']:
            self.assertIn(host, settings.allowed_hosts)
        self.assertNotIn('*', settings.allowed_hosts)
        with TestClient(create_app(self.db, settings=settings)) as client:
            response = self.register(client)
            self.assertEqual(response.status_code, 201)
            self.assertNotIn('strict-transport-security', response.headers)


if __name__ == '__main__':
    unittest.main()
