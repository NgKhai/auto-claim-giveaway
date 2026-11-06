"""Independent citation-bound deterministic analysis acceptance; no live network."""
import hashlib
import json
import sqlite3
import tempfile
import time
import unittest

import httpx
from fastapi.testclient import TestClient
from hunter.app import create_app

SOURCE = 'github-education'
CHECKLIST = '''Préface tiếng Việt 🌱
## Do I qualify for GitHub Education?

You qualify for {% data variables.product.prodname_global_campus %} if you:

* Are enrolled in a degree- or diploma-granting program, such as a high school, college, university, or homeschool.
* Provide documents that prove your current student status. See [Academic email requirements](#academic-email-requirements) below.
* Own a [{% data variables.product.prodname_dotcom %} personal account](/account-and-profile/how-tos/account-management/creating-an-account-on-github).
* Are at least 13 years old.

## Following section
Untrusted website text never authorizes registration.
'''
FIELDS = ['minimum_age', 'enrollment_required', 'student_status_evidence_required', 'personal_account_required']


class AnalysisApiAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = self.tmp.name + '/analysis.db'
        self.body = CHECKLIST
        self.calls = 0
        def handler(request):
            self.calls += 1
            return httpx.Response(200, text=self.body, headers={'content-type': 'text/plain'})
        self.app = create_app(self.path, source_transport=httpx.MockTransport(handler))
        self.client = TestClient(self.app)
        self.user = self.signup(self.client, 'analysis@example.test')

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def signup(self, client, email):
        response = client.post('/api/auth/register', json={
            'email': email, 'password': 'AnalysisPassword123!', 'country': 'VN'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def refresh(self, client=None, user=None):
        response = (client or self.client).post(f'/api/sources/{SOURCE}/refresh', json={},
                    headers={'X-CSRF-Token': (user or self.user)['csrf_token']})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def analysis(self, client=None):
        response = (client or self.client).get(f'/api/sources/{SOURCE}/analysis')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def assert_unknown_claims(self, analysis):
        for field in FIELDS:
            self.assertEqual(analysis['claims'][field]['state'], 'unknown', field)
            self.assertIsNone(analysis['claims'][field]['value'], field)
            self.assertIsNone(analysis['claims'][field]['citation'], field)

    def clear_cooldown(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute('UPDATE source_records SET last_attempt_at=0 WHERE user_id=?', (self.user['id'],))

    def test_auth_unknown_id_and_missing_evidence_do_not_fetch_or_guess(self):
        with TestClient(self.app) as anonymous:
            self.assertEqual(anonymous.get(f'/api/sources/{SOURCE}/analysis').status_code, 401)
        self.assertEqual(self.client.get('/api/sources/arbitrary/analysis').status_code, 404)
        missing = self.analysis()
        self.assertEqual(missing['status'], 'unknown')
        self.assert_unknown_claims(missing)
        self.assertEqual(self.calls, 0)

    def test_candidates_have_exact_unicode_slice_citations_without_eligibility_claim(self):
        source = self.refresh()
        with sqlite3.connect(self.path) as connection:
            audit_before = connection.execute('SELECT count(*) FROM audit').fetchone()[0]
            rows_before = connection.execute('SELECT * FROM source_records').fetchall()
        result = self.analysis()
        self.assertEqual(self.calls, 1)
        self.assertEqual(result['status'], 'candidate_claims', result)
        self.assertEqual(result['offset_unit'], 'unicode_code_points')
        self.assertEqual(result['content_hash'], hashlib.sha256(CHECKLIST.encode()).hexdigest())
        self.assertEqual(result['claims']['minimum_age']['value'], 13)
        for field in FIELDS:
            claim = result['claims'][field]
            self.assertEqual(claim['state'], 'candidate')
            if field != 'minimum_age': self.assertIs(claim['value'], True)
            citation = claim['citation']
            self.assertEqual(CHECKLIST[citation['start']:citation['end']], citation['quote'])
            self.assertEqual(citation['content_hash'], source['evidence']['content_hash'])
            self.assertEqual(citation['retrieved_at'], source['evidence']['retrieved_at'])
            self.assertEqual(citation['source_url'], source['source_url'])
            self.assertEqual(citation['extractor_version'], result['extractor_version'])
        for field in ['eligibility', 'deadline', 'automation_status']:
            self.assertEqual(result[field], 'unknown')
        self.analysis()
        self.assertEqual(self.calls, 1, 'Read-only analysis unexpectedly fetched source')
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM audit').fetchone()[0], audit_before)
            self.assertEqual(connection.execute('SELECT * FROM source_records').fetchall(), rows_before)
        response = self.client.post('/api/applications', json={'opportunity_id': SOURCE},
                    headers={'X-CSRF-Token': self.user['csrf_token']})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get('/api/applications').json(), [])

    def test_stale_failed_or_truncated_evidence_cannot_yield_candidates(self):
        self.refresh()
        for updates, expected in [
            ({'retrieved_at': time.time()-86401}, 'needs_refresh'),
            ({'last_error': 'upstream_timeout'}, 'needs_refresh'),
            ({'truncated': 1}, 'unknown'),
        ]:
            with self.subTest(updates=updates):
                with sqlite3.connect(self.path) as connection:
                    connection.execute('UPDATE source_records SET retrieved_at=?,last_error=NULL,truncated=0', (time.time(),))
                    for key, value in updates.items():
                        connection.execute(f'UPDATE source_records SET {key}=?', (value,))
                result = self.analysis()
                self.assertEqual(result['status'], expected)
                self.assert_unknown_claims(result)
        self.assertEqual(self.calls, 1)

    def test_changed_source_updates_hash_version_and_age_citation(self):
        first = self.refresh()
        initial = self.analysis()
        self.clear_cooldown()
        self.body = CHECKLIST.replace('13 years old', '16 years old')
        second = self.refresh()
        result = self.analysis()
        self.assertNotEqual(result['content_hash'], initial['content_hash'])
        self.assertEqual(result['content_hash'], second['evidence']['content_hash'])
        self.assertEqual(result['claims']['minimum_age']['value'], 16)
        quote = result['claims']['minimum_age']['citation']
        self.assertEqual(self.body[quote['start']:quote['end']], quote['quote'])
        self.assertNotEqual(quote['content_hash'], first['evidence']['content_hash'])

    def test_conflicting_age_cannot_select_convenient_value(self):
        self.body = CHECKLIST.replace('* Are at least 13 years old.', '* Are at least 13 years old.\n* Are at least 18 years old.')
        self.refresh()
        age = self.analysis()['claims']['minimum_age']
        self.assertEqual(age['state'], 'unknown')
        self.assertIsNone(age['value'])
        self.assertIsNone(age['citation'])

    def test_unsupported_or_negated_qualification_is_not_fabricated(self):
        for body in [
            'This source has no supported qualification checklist.',
            CHECKLIST.replace('* Are at least 13 years old.', '* Are NOT at least 13 years old.'),
            CHECKLIST.replace('* Are at least 13 years old.', '* Are at least 13 years old.\n* Must also satisfy an unimplemented requirement.'),
        ]:
            with self.subTest(body=body[:30]):
                self.body = body
                self.clear_cooldown()
                self.refresh()
                self.assert_unknown_claims(self.analysis())

    def test_examples_blockquotes_and_duplicate_sections_do_not_create_claims(self):
        for body in ['```markdown\n' + CHECKLIST + '\n```',
                     '\n'.join('> ' + line for line in CHECKLIST.splitlines()),
                     CHECKLIST + '\n' + CHECKLIST]:
            with self.subTest(body=body[:25]):
                self.body = body
                self.clear_cooldown()
                self.refresh()
                self.assert_unknown_claims(self.analysis())

    def test_owner_export_and_deletion_do_not_expose_or_retain_other_analysis(self):
        self.refresh()
        with TestClient(self.app) as bob:
            user = self.signup(bob, 'bob@example.test')
            self.assert_unknown_claims(self.analysis(bob))
            self.body = CHECKLIST.replace('13 years old', '17 years old')
            self.refresh(bob, user)
            alice_export = self.client.get('/api/account/export').json()
            bob_export = bob.get('/api/account/export').json()
            self.assertEqual(alice_export['analyses'][0]['claims']['minimum_age']['value'], 13)
            self.assertEqual(bob_export['analyses'][0]['claims']['minimum_age']['value'], 17)
            self.assertNotIn('bob@example.test', json.dumps(alice_export))
            deleted = self.client.post('/api/account/delete', json={'password': 'AnalysisPassword123!'},
                        headers={'X-CSRF-Token': self.user['csrf_token']})
            self.assertEqual(deleted.status_code, 200)
            self.assertEqual(self.client.get(f'/api/sources/{SOURCE}/analysis').status_code, 401)
            self.assertEqual(self.analysis(bob)['claims']['minimum_age']['value'], 17)
            self.assertEqual(self.calls, 2)


if __name__ == '__main__':
    unittest.main()
