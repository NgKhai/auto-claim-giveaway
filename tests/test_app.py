import re
import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app


def csrf(response):
    return re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)


def test_secure_cookie_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv('AOH_SECURE_COOKIES', '1')
    client = TestClient(create_app(tmp_path / 'app.db'), base_url='https://testserver')
    response = client.get('/register')
    assert 'Secure' in response.headers['set-cookie']
    response = client.post('/register', data={'csrf': csrf(response), 'email': 'person@example.test', 'password': 'long-password-123'}, follow_redirects=False)
    assert response.status_code == 303
    assert 'Secure' in response.headers['set-cookie']


def test_auth_login_logout_and_invalid_password(tmp_path):
    app = create_app(tmp_path / 'app.db')
    client = TestClient(app)
    response = client.post('/register', data={'csrf': csrf(client.get('/register')), 'email': 'person@example.test', 'password': 'long-password-123'}, follow_redirects=False)
    assert response.status_code == 303
    assert client.post('/logout', data={'csrf': csrf(client.get('/'))}, follow_redirects=False).status_code == 303
    bad = client.post('/login', data={'csrf': csrf(client.get('/login')), 'email': 'person@example.test', 'password': 'wrong-password-123'}, follow_redirects=False)
    assert bad.status_code == 400
    assert client.get('/', follow_redirects=False).status_code == 303
    good = client.post('/login', data={'csrf': csrf(client.get('/login')), 'email': 'person@example.test', 'password': 'long-password-123'}, follow_redirects=False)
    assert good.status_code == 303
    assert client.get('/').status_code == 200
    with sqlite3.connect(app.state.db_path) as db:
        assert db.execute('SELECT count(*) FROM users').fetchone()[0] == 1


def test_browser_error_explains_recovery_without_json(tmp_path):
    client = TestClient(create_app(tmp_path / 'app.db'))
    response = client.post('/login', data={'csrf': csrf(client.get('/login')), 'email': 'wrong', 'password': 'short'}, headers={'Accept': 'text/html'})
    assert response.status_code == 400
    assert response.headers['content-type'].startswith('text/html')
    assert 'Use a valid email' in response.text
    assert 'href="/login"' in response.text
