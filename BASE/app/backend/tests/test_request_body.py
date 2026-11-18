from __future__ import annotations

import asyncio

import pytest
from starlette.requests import Request

from app.services.request_body import (
    RequestBodyTooLarge,
    limit_request_receive,
    read_request_body_limited,
)


class ChunkedRequest:
    def __init__(self, chunks):
        self.messages = iter([
            {"type": "http.request", "body": chunk,
             "more_body": index < len(chunks) - 1}
            for index, chunk in enumerate(chunks)
        ])
        self.request = Request({
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("test", 1234),
            "server": ("test", 80),
        }, receive=self._receive)

    async def _receive(self):
        return next(self.messages)

    @property
    def headers(self):
        return self.request.headers

    @property
    def scope(self):
        return self.request.scope

    @property
    def receive(self):
        return self.request.receive


def test_streaming_body_limit_applies_without_content_length():
    request = ChunkedRequest([b"123", b"45"])

    with pytest.raises(RequestBodyTooLarge):
        asyncio.run(read_request_body_limited(request, 4))


def test_streaming_body_limit_accepts_body_at_limit():
    request = ChunkedRequest([b"12", b"34"])

    assert asyncio.run(read_request_body_limited(request, 4)) == b"1234"


def test_receive_limit_counts_streamed_chunks():
    messages = iter([
        {"type": "http.request", "body": b"123", "more_body": True},
        {"type": "http.request", "body": b"45", "more_body": False},
    ])

    async def receive():
        return next(messages)

    limited_receive = limit_request_receive(receive, 4)

    async def consume():
        await limited_receive()
        await limited_receive()

    with pytest.raises(RequestBodyTooLarge):
        asyncio.run(consume())
