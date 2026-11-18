from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.types import Message


class RequestBodyTooLarge(Exception):
    """El cuerpo superó el límite configurado para el endpoint."""


def limit_request_receive(
        receive: Callable[[], Awaitable[Message]],
        max_bytes: int) -> Callable[[], Awaitable[Message]]:
    received = 0

    async def limited_receive() -> Message:
        nonlocal received
        message = await receive()
        if message["type"] == "http.request":
            received += len(message.get("body", b""))
            if received > max_bytes:
                raise RequestBodyTooLarge
        return message

    return limited_receive


async def read_request_body_limited(request: Request, max_bytes: int) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None
        if declared_size is not None and declared_size > max_bytes:
            raise RequestBodyTooLarge

    limited_request = Request(
        request.scope, receive=limit_request_receive(request.receive, max_bytes))
    body = bytearray()
    async for chunk in limited_request.stream():
        body.extend(chunk)
    return bytes(body)
