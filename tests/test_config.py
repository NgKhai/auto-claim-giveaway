import tempfile
import unittest
from fastapi.testclient import TestClient

class ConfigurationTests(unittest.TestCase):
    def test_production_missing_and_unsafe_configuration_rejected(self):
        from hunter.config import Settings, ConfigurationError
        for config in [
            {'HUNTER_ENV':'production'},
            {'HUNTER_ENV':'unknown'},
            {'HUNTER_ALLOWED_HOSTS':'*'},
            {'HUNTER_ALLOWED_HOSTS':'https://app.example'},
            {'HUNTER_TRUSTED_ORIGINS':'https://app.example/'},
        ]:
            with self.subTest(config=config), self.assertRaises(ConfigurationError): Settings.from_env(config)

    def test_production_cookies_headers_and_exact_origin_policy(self):
        from hunter.config import Settings
        from hunter.app import create_app
        with tempfile.TemporaryDirectory() as tmp:
            settings=Settings.from_env({'HUNTER_ENV':'production','HUNTER_ALLOWED_HOSTS':'app.example,api.example','HUNTER_TRUSTED_ORIGINS':'https://app.example','HUNTER_SECURE_COOKIE':'1','HUNTER_DB_PATH':tmp+'/test.db'})
            with TestClient(create_app(settings=settings),base_url='https://api.example') as client:
                data={'email':'user@example.test','password':'StrongPass123!','country':'VN'}
                self.assertEqual(client.post('/api/auth/register',json=data,headers={'Host':'evil.example','Origin':'https://app.example'}).status_code,400)
                self.assertEqual(client.post('/api/auth/register',json=data,headers={'Origin':'https://evil.example'}).status_code,403)
                response=client.post('/api/auth/register',json=data,headers={'Origin':'https://app.example'})
                self.assertEqual(response.status_code,201,response.text)
                self.assertIn('Secure',response.headers['set-cookie'])
                self.assertEqual(response.headers['strict-transport-security'],'max-age=31536000')
                token=response.json()['csrf_token']
                self.assertEqual(client.post('/api/goals',json={'query':'credits'}).status_code,403)
                self.assertEqual(client.post('/api/goals',json={'query':'credits'},headers={'X-CSRF-Token':token}).status_code,201)

    def test_strict_authority_syntax_and_duplicate_origins(self):
        from hunter.config import Settings, ConfigurationError, normalize_origin
        from hunter.app import create_app
        from dataclasses import replace
        for origin in ['https://app.example:','https://[::1]garbage','https://app.exa\tmple','https://[::1]:','https://app.example/']:
            with self.subTest(origin=origin), self.assertRaises(ConfigurationError): normalize_origin(origin)
        with self.assertRaises(ConfigurationError): replace(Settings(),secure_cookie='0')
        with tempfile.TemporaryDirectory() as tmp:
            with TestClient(create_app(tmp+'/test.db',settings=Settings())) as client:
                for host in ['testserver:','[::1]garbage','[::1]:','testserver:bad']:
                    self.assertEqual(client.get('/api/health',headers={'Host':host}).status_code,400)
                self.assertEqual(client.get('/api/health',headers={'Host':'TESTSERVER'}).status_code,200)
                data={'email':'user@example.test','password':'StrongPass123!'}
                headers=[('Origin','http://testserver'),('Origin','https://evil.example')]
                self.assertEqual(client.post('/api/auth/register',json=data,headers=headers).status_code,403)
                self.assertEqual(client.post('/api/auth/register',json=data,headers={'Origin':''}).status_code,403)

    def test_development_ipv6_loopback_and_secure_settings_immutable(self):
        from hunter.config import Settings
        from hunter.app import create_app
        from dataclasses import FrozenInstanceError
        settings=Settings.from_env({})
        with self.assertRaises(FrozenInstanceError): settings.environment='production'
        with tempfile.TemporaryDirectory() as tmp:
            with TestClient(create_app(tmp+'/test.db',settings=settings),base_url='http://testserver',headers={'Host':'[::1]'}) as client:
                self.assertEqual(client.get('/api/health').status_code,200)
                self.assertNotIn('strict-transport-security',client.get('/api/health').headers)
