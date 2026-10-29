"""Independent QA checks: auth, ownership, policy and persistent state (FR-01..12)."""
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.policy import evaluate

PASSWORD = 'correct-test-passphrase-938'


@pytest.fixture
def qa_app(tmp_path):
    return create_app(tmp_path / 'review.db')


def token(response):
    match = re.search(r'name="csrf"\s+value="([^"]+)"', response.text)
    assert match, response.text[:500]
    return match.group(1)


def account(app, email='reviewer@example.test'):
    client = TestClient(app)
    csrf = token(client.get('/register'))
    response = client.post('/register', data={'email': email, 'password': PASSWORD, 'csrf': csrf}, follow_redirects=False)
    assert response.status_code == 303, response.text
    return client


def mutation(client, path, **data):
    data['csrf'] = token(client.get('/'))
    return client.post(path, data=data, follow_redirects=False)


def rows(app, table):
    assert table in {'users', 'sessions', 'goals', 'applications', 'audit', 'notifications'}
    with sqlite3.connect(app.state.db_path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute('SELECT * FROM ' + table)]


@pytest.mark.parametrize('path,data', [('/goals', {'text': 'private goal'}), ('/settings', {'country': 'VN'}), ('/applications', {'opportunity_id': 'free-developer'}), ('/applications/1/cancel', {}), ('/account/delete', {'confirmation': 'DELETE'})])
def test_anonymous_mutations_fail_without_database_writes(qa_app, path, data):
    client = TestClient(qa_app)
    response = client.post(path, data=data)
    assert response.status_code == 401
    assert not rows(qa_app, 'goals')
    assert not rows(qa_app, 'applications')


@pytest.mark.parametrize('bad_token', ['', 'forged-token'])
def test_invalid_csrf_cannot_create_goal(qa_app, bad_token):
    client = account(qa_app)
    response = client.post('/goals', data={'text': 'Do not save', 'csrf': bad_token})
    assert response.status_code == 403
    assert not rows(qa_app, 'goals')


def test_tenants_cannot_view_or_mutate_other_application(qa_app):
    alice = account(qa_app, 'alice@example.test')
    bob = account(qa_app, 'bob@example.test')
    assert mutation(alice, '/goals', text='ALICE PRIVATE SEARCH 731').status_code == 303
    assert mutation(alice, '/applications', opportunity_id='free-developer').status_code == 303
    application = rows(qa_app, 'applications')[0]
    assert 'ALICE PRIVATE SEARCH 731' not in bob.get('/').text
    for action in ('cancel', 'review'):
        assert mutation(bob, f"/applications/{application['id']}/{action}").status_code == 404
    assert rows(qa_app, 'applications')[0]['status'] == application['status']


def test_logout_revokes_cookie_replay_and_password_not_stored(qa_app):
    client = account(qa_app)
    original = client.cookies.get('session')
    stored = rows(qa_app, 'users')[0]['password']
    assert PASSWORD not in stored
    assert original not in [row['token'] for row in rows(qa_app, 'sessions')]
    assert mutation(client, '/logout').status_code == 303
    client.cookies.set('session', original)
    assert client.get('/', follow_redirects=False).status_code == 303
    assert client.post('/goals', data={'text': 'replay'}).status_code == 401


def test_sequential_duplicate_requests_retain_one_intent(qa_app):
    client = account(qa_app)
    assert mutation(client, '/applications', opportunity_id='free-developer').status_code == 303
    assert mutation(client, '/applications', opportunity_id='free-developer').status_code == 409
    applications = rows(qa_app, 'applications')
    assert len(applications) == 1
    assert applications[0]['status'] == 'needs_user_action'
    assert len(rows(qa_app, 'notifications')) == 1


def test_concurrent_duplicate_requests_retain_one_intent(qa_app):
    client = account(qa_app)
    csrf = token(client.get('/'))
    cookies = dict(client.cookies)
    def attempt(_):
        with TestClient(qa_app, cookies=cookies) as worker:
            return worker.post('/applications', data={'opportunity_id': 'free-developer', 'csrf': csrf}, follow_redirects=False).status_code
    with ThreadPoolExecutor(max_workers=4) as executor:
        codes = list(executor.map(attempt, range(4)))
    assert sorted(codes) == [303, 409, 409, 409]
    assert len(rows(qa_app, 'applications')) == 1


def test_review_cannot_escalate_research_example_to_submission(qa_app):
    client = account(qa_app)
    assert mutation(client, '/settings', country='VN', automation='on').status_code == 303
    mutation(client, '/applications', opportunity_id='free-developer')
    application_id = rows(qa_app, 'applications')[0]['id']
    assert mutation(client, f'/applications/{application_id}/review').status_code == 303
    assert rows(qa_app, 'applications')[0]['status'] == 'needs_user_action'
    assert mutation(client, f'/applications/{application_id}/approve').status_code == 400
    mutation(client, '/settings', country='VN')
    assert rows(qa_app, 'users')[0]['automation'] == 0
    assert rows(qa_app, 'applications')[0]['status'] == 'needs_user_action'


def test_cancelled_intent_cannot_be_reactivated_by_review(qa_app):
    client = account(qa_app)
    mutation(client, '/applications', opportunity_id='free-developer')
    application_id = rows(qa_app, 'applications')[0]['id']
    assert mutation(client, f'/applications/{application_id}/cancel').status_code == 303
    assert mutation(client, f'/applications/{application_id}/review').status_code == 409
    assert rows(qa_app, 'applications')[0]['status'] == 'cancelled'


def test_untrusted_goal_is_escaped_and_security_headers_present(qa_app):
    client = account(qa_app)
    payload = '<script>alert("owned")</script>'
    assert mutation(client, '/goals', text=payload).status_code == 303
    response = client.get('/')
    assert payload not in response.text
    assert '&lt;script&gt;' in response.text
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert "form-action 'self'" in response.headers['content-security-policy']


def test_data_survives_app_restart_and_account_deletion_cascades(qa_app):
    client = account(qa_app)
    mutation(client, '/goals', text='Persist this goal')
    mutation(client, '/applications', opportunity_id='free-developer')
    restarted = create_app(qa_app.state.db_path)
    restored = TestClient(restarted, cookies=dict(client.cookies))
    assert 'Persist this goal' in restored.get('/').text
    assert len(rows(restarted, 'applications')) == 1
    assert mutation(restored, '/account/delete', confirmation='wrong').status_code == 400
    assert mutation(restored, '/account/delete', confirmation='DELETE').status_code == 303
    for table in ('users', 'sessions', 'goals', 'applications', 'audit', 'notifications'):
        assert not rows(restarted, table)


@pytest.mark.parametrize('goal', ['', 'ab', 'a' * 301])
def test_invalid_goal_does_not_write(qa_app, goal):
    client = account(qa_app)
    assert mutation(client, '/goals', text=goal).status_code == 400
    assert not rows(qa_app, 'goals')


@pytest.mark.parametrize('deadline', ['2026-11-01', 'not-a-date'])
def test_uncertain_deadline_fails_closed_without_exception(deadline):
    decision, _ = evaluate({'deadline': deadline, 'countries': [], 'automation': 'allowed', 'sample': False}, {'country': 'VN', 'student': 0}, True)
    assert decision in ('needs_user_action', 'blocked')


def test_expired_deadline_cannot_be_overridden():
    decision, _ = evaluate({'deadline': '2000-01-01T00:00:00+00:00', 'countries': [], 'automation': 'allowed', 'sample': False}, {'country': 'VN', 'student': 1}, True)
    assert decision == 'blocked'
