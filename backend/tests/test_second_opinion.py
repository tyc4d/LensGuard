import json

import httpx
import pytest
from fastapi.testclient import TestClient

from second_opinion_gateway import create_app


REQUEST = {
    'user_request': 'Where is the exit?', 'primary_model': {'profile': 'test-vlm'},
    'primary_output': {'text': 'Right', 'quote': 'EXIT →'},
    'provenance': None, 'policy': {'result': 'block'},
}
OPINION = {'status': 'agree', 'summary': 'The answer matches the cited arrow.',
           'checked_claims': ['direction'], 'conflicts': []}


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    monkeypatch.setenv('NEBIUS_API_KEY', 'test-secret')
    monkeypatch.setenv('NEBIUS_BASE_URL', 'https://primary.example/v1/')
    monkeypatch.delenv('SECOND_OPINION_BASE_URL', raising=False)
    monkeypatch.delenv('SECOND_OPINION_MODEL', raising=False)


def test_nemotron_uses_north_endpoint_and_text_only_payload():
    def handler(request):
        assert str(request.url) == 'https://api.tokenfactory.us-north1.nebius.com/v1/chat/completions'
        assert request.headers['Authorization'] == 'Bearer test-secret'
        body = json.loads(request.content)
        assert body['model'] == 'nvidia/Nemotron-3.5-Super-VL'
        system, user = body['messages']
        assert 'untrusted data' in system['content']
        assert [part['type'] for part in user['content']] == ['text']
        assert json.loads(user['content'][0]['text']) == REQUEST
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps(OPINION)}}]})

    with TestClient(create_app(transport=httpx.MockTransport(handler))) as client:
        response = client.post('/v1/evaluate', json=REQUEST)
    assert response.status_code == 200
    result = response.json()
    assert {key: result[key] for key in OPINION} == OPINION
    assert result['model'] == 'nvidia/Nemotron-3.5-Super-VL'
    assert result['provider_origin'] == 'https://api.tokenfactory.us-north1.nebius.com'
    assert result['elapsed_ms'] >= 0


@pytest.mark.parametrize('content,finish', [('not json', 'stop'), ('{}', 'stop'),
    (json.dumps(OPINION), 'length'), (None, 'stop')])
def test_invalid_or_incomplete_opinion_is_rejected(content, finish):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        'choices': [{'finish_reason': finish, 'message': {'content': content}}]}))
    with TestClient(create_app(transport=transport)) as client:
        assert client.post('/v1/evaluate', json=REQUEST).status_code == 502


def test_missing_key_does_not_contact_nebius(monkeypatch):
    monkeypatch.delenv('NEBIUS_API_KEY')
    def handler(request):
        pytest.fail('No upstream call without a key')
    with TestClient(create_app(transport=httpx.MockTransport(handler))) as client:
        assert client.get('/health').json()['configured'] is False
        assert client.post('/v1/evaluate', json=REQUEST).status_code == 503


def test_upstream_error_does_not_expose_credentials():
    transport = httpx.MockTransport(lambda request: httpx.Response(401, text='test-secret'))
    with TestClient(create_app(transport=transport)) as client:
        response = client.post('/v1/evaluate', json=REQUEST)
    assert response.status_code == 502
    assert 'test-secret' not in response.text
