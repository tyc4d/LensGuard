import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.request_limits import (
    MAX_IMAGE_BYTES, MAX_JSON_BODY_BYTES, MAX_UPLOAD_BODY_BYTES,
    RequestBodyLimitMiddleware,
)


@pytest.mark.parametrize('streamed', [False, True])
def test_oversized_json_is_rejected_before_validation_or_run(streamed):
    body = b' ' * (MAX_JSON_BODY_BYTES + 1)
    with TestClient(create_app(Settings(mock_stage_delay_ms=0))) as client:
        response = client.post('/api/run', content=iter([body]) if streamed else body,
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 413
        assert not client.app.state.runtime.records


def test_oversized_multipart_is_rejected_before_creating_a_run():
    with TestClient(create_app(Settings(mock_stage_delay_ms=0))) as client:
        response = client.post('/api/run', files={'image': (
            'scene.png', b'x' * (MAX_UPLOAD_BODY_BYTES + 1), 'image/png')},
            data={'scenario_id': 'clean-navigation', 'guard_enabled': 'true',
                  'user_request': 'Which direction does the sign indicate?'})
        assert response.status_code == 413
        assert not client.app.state.runtime.records


def test_existing_ten_mib_image_boundary_is_preserved():
    # Mock mode does not decode images; this checks the transport boundary only.
    with TestClient(create_app(Settings(mock_stage_delay_ms=0))) as client:
        fields = {'scenario_id': 'clean-navigation', 'guard_enabled': 'true',
                  'user_request': 'Which direction does the sign indicate?'}
        accepted = client.post('/api/run', files={'image': (
            'scene.png', b'x' * MAX_IMAGE_BYTES, 'image/png')}, data=fields)
        assert accepted.status_code == 202
        rejected = client.post('/api/run', files={'image': (
            'scene.png', b'x' * (MAX_IMAGE_BYTES + 1), 'image/png')}, data=fields)
        assert rejected.status_code == 413


@pytest.mark.parametrize('declared_length', [None, b'1'])
def test_streamed_body_limit_stops_consumption_even_with_missing_or_false_length(declared_length):
    consumed = []
    sent = []

    async def application(scope, receive, send):
        while True:
            event = await receive()
            consumed.append(event)
            if not event.get('more_body'):
                break
        raise AssertionError('An oversized body must never reach processing.')

    chunks = iter([
        {'type': 'http.request', 'body': b'123', 'more_body': True},
        {'type': 'http.request', 'body': b'456', 'more_body': True},
        {'type': 'http.request', 'body': b'never read', 'more_body': False},
    ])

    async def receive():
        return next(chunks)

    async def send(event):
        sent.append(event)

    headers = [(b'content-type', b'application/json')]
    if declared_length is not None:
        headers.append((b'content-length', declared_length))
    asyncio.run(RequestBodyLimitMiddleware(application, paths=('/api/run',), json_limit=5)(
        {'type': 'http', 'method': 'POST', 'path': '/api/run', 'headers': headers}, receive, send))
    assert len(consumed) == 1
    assert sent[0]['status'] == 413
    assert next(chunks)['body'] == b'never read'


def test_declared_oversize_is_rejected_without_reading_body():
    sent = []

    async def unavailable(*args):
        raise AssertionError('Do not consume or parse a declared oversized request.')

    async def send(event):
        sent.append(event)

    asyncio.run(RequestBodyLimitMiddleware(unavailable, paths=('/api/run',), json_limit=5)(
        {'type': 'http', 'method': 'POST', 'path': '/api/run',
         'headers': [(b'content-length', b'6')]}, unavailable, send))
    assert sent[0]['status'] == 413


def test_local_gateway_rejects_streamed_oversize_before_model_access():
    from model_gateway import create_app as create_gateway_app

    class UnusedGateway:
        async def close(self):
            pass

        async def analyze(self, *args):
            raise AssertionError('An oversized upload cannot reach inference.')

    boundary = 'test-boundary'
    chunks = iter([
        (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="x.png"\r\n'
         'Content-Type: image/png\r\n\r\n').encode(),
        b'x' * (MAX_UPLOAD_BODY_BYTES + 1),
        f'\r\n--{boundary}--\r\n'.encode(),
    ])
    with TestClient(create_gateway_app(UnusedGateway())) as client:
        response = client.post('/v1/analyze', content=chunks,
            headers={'content-type': f'multipart/form-data; boundary={boundary}'})
        assert response.status_code == 413


def test_cloud_gateway_rejects_oversize_before_model_access():
    pytest.importorskip('PIL')
    from cloud_gateway import create_cloud_app

    class UnusedRuntime:
        def close(self):
            pass

    with TestClient(create_cloud_app(UnusedRuntime())) as client:
        response = client.post('/v1/analyze', content=b'x' * (MAX_UPLOAD_BODY_BYTES + 1),
            headers={'content-type': 'multipart/form-data; boundary=test'})
        assert response.status_code == 413


def test_reviewer_caps_json_before_validation_or_provider_call():
    from second_opinion_gateway import create_app as create_reviewer_app

    with TestClient(create_reviewer_app()) as client:
        response = client.post('/v1/evaluate', content=iter([b'x' * (1024 * 1024 + 1)]),
            headers={'content-type': 'application/json'})
        assert response.status_code == 413


def test_deeply_nested_json_is_invalid_input_not_an_internal_error():
    with TestClient(create_app(Settings(mock_stage_delay_ms=0))) as client:
        response = client.post('/api/run', content=b'[' * 2000 + b']' * 2000,
                               headers={'content-type': 'application/json'})
        assert response.status_code == 422
        assert not client.app.state.runtime.records


@pytest.mark.parametrize('length', ['-1', 'invalid'])
def test_invalid_content_length_is_rejected(length):
    with TestClient(create_app(Settings(mock_stage_delay_ms=0))) as client:
        response = client.post('/api/run', content=b'{}', headers={
            'content-type': 'application/json', 'content-length': length})
        assert response.status_code == 400
        assert not client.app.state.runtime.records
