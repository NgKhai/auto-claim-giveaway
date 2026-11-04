import os
import tempfile
import unittest
from fastapi.testclient import TestClient

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        from hunter.app import create_app
        self.client = TestClient(create_app(self.tmp.name + '/test.db'))
        self.user = self.signup(self.client, 'one@example.test')

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def signup(self, client, email):
        r = client.post('/api/auth/register', json={'email':email,'password':'StrongPass123!', 'country':'VN'})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def post(self, path, data=None, client=None, user=None):
        return (client or self.client).post(path,json=data or {},headers={'X-CSRF-Token':(user or self.user)['csrf_token']})

    def application(self):
        r = self.post('/api/applications', {'opportunity_id':'sandbox-credits'})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_approval_submission_and_idempotency(self):
        a = self.application()
        self.assertEqual(self.post(f"/api/applications/{a['id']}/submit").status_code,409)
        self.assertEqual(self.post(f"/api/applications/{a['id']}/approve", {'version':99}).status_code,409)
        self.assertEqual(self.post(f"/api/applications/{a['id']}/approve", {'version':a['version']}).status_code,200)
        first = self.post(f"/api/applications/{a['id']}/submit").json()
        again = self.post(f"/api/applications/{a['id']}/submit").json()
        self.assertEqual(first['status'],'submitted')
        self.assertEqual(first['receipt'],again['receipt'])
        self.assertEqual(len(self.client.get('/api/applications').json()),1)

    def test_revocation_blocks_submission(self):
        a=self.application()
        self.post(f"/api/applications/{a['id']}/approve",{'version':a['version']})
        self.post(f"/api/applications/{a['id']}/revoke")
        self.assertEqual(self.post(f"/api/applications/{a['id']}/submit").status_code,409)

    def test_tenant_isolation_and_csrf(self):
        a=self.application()
        self.assertEqual(self.client.post('/api/goals',json={'query':'credits'}).status_code,403)
        other=TestClient(self.client.app)
        user=self.signup(other,'two@example.test')
        self.assertEqual(other.get('/api/applications').json(),[])
        self.assertEqual(self.post(f"/api/applications/{a['id']}/approve",{'version':a['version']},other,user).status_code,404)
        other.close()

    def test_blocked_evidence_expiry_country_and_sensitive(self):
        for opportunity in ['sandbox-expired','sandbox-country','sandbox-unverified','sandbox-sensitive']:
            a=self.post('/api/applications',{'opportunity_id':opportunity}).json()
            self.assertEqual(a['status'],'blocked',a)
            self.assertEqual(self.post(f"/api/applications/{a['id']}/approve",{'version':a['version']}).status_code,409)

    def test_expired_and_revoked_requests_can_be_renewed_with_fresh_consent(self):
        import sqlite3
        a = self.application()
        self.post(f"/api/applications/{a['id']}/approve", {'version':a['version']})
        with sqlite3.connect(self.tmp.name + '/test.db') as db:
            db.execute('UPDATE applications SET approval_expires=0 WHERE id=?', (a['id'],))
        self.assertEqual(self.post(f"/api/applications/{a['id']}/submit").status_code, 409)
        renewed = self.application()
        self.assertEqual(renewed['id'], a['id'])
        self.assertEqual(renewed['status'], 'awaiting_approval')
        self.assertGreater(renewed['version'], a['version'])
        self.assertEqual(self.post(f"/api/applications/{a['id']}/approve", {'version':a['version']}).status_code, 409)
        self.post(f"/api/applications/{a['id']}/revoke")
        renewed = self.application()
        self.assertEqual(renewed['status'], 'awaiting_approval')
        self.assertEqual(self.post(f"/api/applications/{a['id']}/approve", {'version':renewed['version']}).status_code, 200)
        self.assertEqual(self.post(f"/api/applications/{a['id']}/submit").json()['status'], 'submitted')
        self.assertEqual(self.application()['status'], 'submitted')

    def test_changed_destination_invalidates_approval(self):
        from hunter.app import OPPORTUNITIES
        a = self.application()
        self.post(f"/api/applications/{a['id']}/approve", {'version':a['version']})
        original = OPPORTUNITIES['sandbox-credits']['source_url']
        try:
            OPPORTUNITIES['sandbox-credits']['source_url'] = 'sandbox://changed-destination'
            self.assertEqual(self.post(f"/api/applications/{a['id']}/submit").status_code, 409)
            self.assertEqual(self.client.get('/api/applications').json()[0]['status'], 'ready')
        finally:
            OPPORTUNITIES['sandbox-credits']['source_url'] = original

    def test_cross_origin_mutations_are_rejected_even_with_csrf(self):
        for headers in [{'Origin':'https://attacker.example'}, {'Sec-Fetch-Site':'cross-site'}]:
            headers['X-CSRF-Token'] = self.user['csrf_token']
            self.assertEqual(self.client.post('/api/goals', json={'query':'credits'}, headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/goals').json(), [])
        headers = {'Origin':'http://testserver', 'X-CSRF-Token':self.user['csrf_token']}
        self.assertEqual(self.client.post('/api/goals', json={'query':'credits'}, headers=headers).status_code, 201)
        self.assertEqual(self.client.post('/api/auth/login', json={'email':'one@example.test','password':'StrongPass123!'}, headers={'Origin':'https://attacker.example'}).status_code, 403)

    def test_account_export_contains_owner_data_without_credentials(self):
        self.application()
        self.post('/api/goals', {'query':'credits'})
        response = self.client.get('/api/account/export')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment;', response.headers['content-disposition'])
        data = response.json()
        self.assertEqual(data['schema_version'], 1)
        from datetime import datetime
        self.assertIsNotNone(datetime.fromisoformat(data['exported_at']).tzinfo)
        self.assertEqual(data['profile'], {k:self.user[k] for k in ['id','email','country']})
        self.assertEqual(len(data['goals']), 1)
        self.assertEqual(len(data['applications']), 1)
        self.assertTrue(data['audit'])
        raw = response.text
        for excluded in ['csrf_token','approval_hash','password','hunter_session',self.user['csrf_token']]:
            self.assertNotIn(excluded, raw)

    def test_deletion_removes_owner_throttle_records_and_retains_other_owner(self):
        import sqlite3
        other=TestClient(self.client.app)
        other_user=self.signup(other,'two@example.test')
        self.client.post('/api/auth/login',json={'email':self.user['email'],'password':'wrong'})
        other.post('/api/auth/login',json={'email':other_user['email'],'password':'wrong'})
        with TestClient(self.client.app,client=('192.0.2.10',50001)) as another_ip:
            another_ip.post('/api/auth/login',json={'email':self.user['email'],'password':'wrong'})
        with sqlite3.connect(self.tmp.name+'/test.db') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM login_limits WHERE user_id=?',(self.user['id'],)).fetchone()[0],2)
        self.assertEqual(self.post('/api/account/delete',{'password':'StrongPass123!'}).status_code,200)
        with sqlite3.connect(self.tmp.name+'/test.db') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM login_limits WHERE user_id=?',(self.user['id'],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM login_limits WHERE user_id=?',(other_user['id'],)).fetchone()[0],1)
        other.close()

    def test_account_deletion_requires_password_and_invalidates_every_session(self):
        import sqlite3
        self.application()
        self.post('/api/goals', {'query':'credits'})
        second = TestClient(self.client.app)
        self.assertEqual(second.post('/api/auth/login', json={'email':self.user['email'],'password':'StrongPass123!'}).status_code, 200)
        self.assertEqual(self.post('/api/account/delete', {'password':'wrong'}).status_code, 401)
        self.assertEqual(self.client.get('/api/me').status_code, 200)
        self.assertEqual(self.post('/api/account/delete', {'password':'StrongPass123!'}).json(), {'status':'deleted'})
        self.assertEqual(self.client.get('/api/me').status_code, 401)
        self.assertEqual(second.get('/api/me').status_code, 401)
        with sqlite3.connect(self.tmp.name + '/test.db') as db:
            for table in ['users','sessions','goals','applications','audit']:
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0],0)
        second.close()

    def test_goals_are_scoped_and_login_validated(self):
        self.assertEqual(self.post('/api/goals',{'query':'developer credits'}).status_code,201)
        self.assertEqual(len(self.client.get('/api/goals').json()),1)
        self.assertEqual(self.client.post('/api/auth/login',json={'email':'one@example.test','password':'wrong'}).status_code,401)
        self.assertEqual(self.post('/api/goals',{'query':' '}).status_code,422)

if __name__ == '__main__': unittest.main()
