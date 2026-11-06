import hashlib
import sqlite3
import tempfile
import time
import unittest
import httpx
from fastapi.testclient import TestClient
from hunter.app import create_app

class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=self.tmp.name+'/source.db'
        self.calls=[]
        self.on_fetch=None
        self.reply=httpx.Response(200,text='Official eligibility evidence. No automatic registration permission.',headers={'content-type':'text/plain; charset=utf-8'})
        def handler(request):
            self.calls.append(request)
            if self.on_fetch: self.on_fetch()
            return self.reply
        self.app=create_app(self.path,source_transport=httpx.MockTransport(handler))
        self.client=TestClient(self.app)
        self.user=self.register(self.client,'one@example.test')
    def tearDown(self):
        self.client.close(); self.tmp.cleanup()
    def register(self,c,email):
        return c.post('/api/auth/register',json={'email':email,'password':'StrongPass123!','country':'VN'}).json()
    def refresh(self):
        return self.client.post('/api/sources/github-education/refresh',json={},headers={'X-CSRF-Token':self.user['csrf_token']})
    def release(self):
        with sqlite3.connect(self.path) as c: c.execute('UPDATE source_records SET last_attempt_at=0')
    def test_success_bounded_fixed_url_and_no_forwarded_auth(self):
        r=self.refresh(); self.assertEqual(r.status_code,200,r.text)
        source=r.json(); self.assertEqual(source['status'],'fresh')
        self.assertEqual(source['automation_status'],'unknown')
        self.assertEqual(source['evidence']['content_hash'],hashlib.sha256(self.reply.content).hexdigest())
        request=self.calls[0]
        self.assertEqual(request.url.host,'raw.githubusercontent.com')
        for key in ['cookie','authorization','x-csrf-token']: self.assertNotIn(key,request.headers)
        self.assertEqual(self.refresh().status_code,429)
        self.assertEqual(len(self.calls),1)
    def test_failure_preserves_success_and_does_not_follow_redirects(self):
        first=self.refresh().json()['evidence']; self.release()
        self.reply=httpx.Response(302,headers={'location':'http://127.0.0.1/secrets'})
        self.assertEqual(self.refresh().status_code,502)
        source=self.client.get('/api/sources').json()[0]
        self.assertEqual(source['status'],'unverified')
        self.assertEqual(source['evidence'],first)
        self.assertEqual(len(self.calls),2)
    def test_unknown_and_arbitrary_input_cannot_trigger_network(self):
        headers={'X-CSRF-Token':self.user['csrf_token']}
        self.assertEqual(self.client.post('/api/sources/unknown/refresh',json={},headers=headers).status_code,404)
        self.assertEqual(self.client.post('/api/sources/github-education/refresh',json={'url':'http://localhost'},headers=headers).status_code,422)
        self.assertEqual(self.calls,[])
    def test_oversize_invalid_utf8_and_nontext_fail(self):
        for content,headers in [(b'x'*(256*1024+1),{'content-type':'text/plain'}),(b'\xff',{'content-type':'text/plain'}),(b'{}',{'content-type':'application/json'})]:
            self.reply=httpx.Response(200,content=content,headers=headers)
            self.release()
            self.assertEqual(self.refresh().status_code,502)
            self.assertIsNone(self.client.get('/api/sources').json()[0]['evidence'])
    def test_absolute_deadline_cancels_slow_trickle(self):
        import asyncio
        from unittest.mock import patch
        from hunter.sources import fetch_source, SourceFailure
        consumed=[]
        class SlowStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                for i in range(100):
                    await asyncio.sleep(.005)
                    consumed.append(i)
                    yield b'x'
        transport=httpx.MockTransport(lambda request:httpx.Response(200,headers={'content-type':'text/plain'},stream=SlowStream()))
        with patch('hunter.sources.TIMEOUT',.02):
            with self.assertRaisesRegex(SourceFailure,'upstream_timeout'):
                fetch_source('github-education',transport)
        self.assertLess(len(consumed),100)

    def test_deletion_during_fetch_cannot_recreate_source_records(self):
        def delete_during_io():
            with TestClient(self.app) as deleting:
                login=deleting.post('/api/auth/login',json={'email':'one@example.test','password':'StrongPass123!'}).json()
                result=deleting.post('/api/account/delete',json={'password':'StrongPass123!'},headers={'X-CSRF-Token':login['csrf_token']})
                self.assertEqual(result.status_code,200)
        self.on_fetch=delete_during_io
        self.assertEqual(self.refresh().status_code,401)
        with sqlite3.connect(self.path) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM source_records').fetchone()[0],0)

    def test_owner_isolation_export_delete_and_freshness(self):
        self.refresh()
        with sqlite3.connect(self.path) as c: c.execute('UPDATE source_records SET retrieved_at=?',(time.time()-86401,))
        self.assertEqual(self.client.get('/api/sources').json()[0]['status'],'stale')
        other=TestClient(self.app); self.register(other,'two@example.test')
        self.assertIsNone(other.get('/api/sources').json()[0]['evidence'])
        self.assertEqual(len(self.client.get('/api/account/export').json()['sources']),1)
        self.assertEqual(self.client.post('/api/account/delete',json={'password':'StrongPass123!'},headers={'X-CSRF-Token':self.user['csrf_token']}).status_code,200)
        with sqlite3.connect(self.path) as c: self.assertEqual(c.execute('SELECT COUNT(*) FROM source_records').fetchone()[0],0)
        other.close()

if __name__=='__main__': unittest.main()
