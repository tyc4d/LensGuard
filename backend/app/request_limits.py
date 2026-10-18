"""Bound request bodies before multipart parsing can spool an oversized upload."""

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


MAX_IMAGE_BYTES = 10 * 1024 * 1024
# Allow the image plus multipart boundaries and bounded text fields.
MAX_UPLOAD_BODY_BYTES = MAX_IMAGE_BYTES + 64 * 1024
MAX_JSON_BODY_BYTES = 64 * 1024


class _BodyTooLarge(HTTPException):
    def __init__(self):
        super().__init__(413, 'Request body is too large. Images must be at most 10 MiB.')


class RequestBodyLimitMiddleware:
    """Enforce the same cap with Content-Length or a streamed/chunked body."""

    def __init__(self, app: ASGIApp, *, paths: tuple[str, ...],
                 json_limit: int = MAX_JSON_BODY_BYTES,
                 upload_limit: int = MAX_UPLOAD_BODY_BYTES):
        self.app = app
        self.paths = paths
        self.json_limit = json_limit
        self.upload_limit = upload_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (scope['type'] != 'http' or scope['method'] != 'POST'
                or scope['path'] not in self.paths):
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        limit = (self.upload_limit if headers.get('content-type', '').lower().startswith('multipart/form-data')
                 else self.json_limit)
        length = headers.get('content-length')
        try:
            if length is not None:
                declared = int(length)
                if declared < 0:
                    raise ValueError('Negative Content-Length')
                if declared > limit:
                    raise _BodyTooLarge
        except ValueError:
            await JSONResponse({'detail': 'Invalid Content-Length.'}, status_code=400)(scope, receive, send)
            return
        except _BodyTooLarge:
            await self._reject(scope, receive, send)
            return

        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > limit:
                    raise _BodyTooLarge
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _BodyTooLarge:
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        await JSONResponse({'detail': 'Request body is too large. Images must be at most 10 MiB.'},
                           status_code=413)(scope, receive, send)
