import asyncio
import json
from functools import partial
from traceback import format_exception
from typing import Optional

from httptools import HttpRequestParser

from tests.Router import Router
from tests.request import Request
from tests.response import Response


class Server(asyncio.Protocol, Router):
    def __init__(self, loop=None):
        self.mapping = {}
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self.transport: Optional[asyncio.Transport] = None
        self._request_parser = HttpRequestParser(self)
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, *args):
        self.transport = None

    def response_writer(self, response):
        self.transport.write(str(response).encode(self.encoding))
        self.transport.close()

    def data_received(self, data):
        self._request_parser.feed_data(data)

    def on_body(self, data):
        self.body = data.decode(self.encoding)

    def on_url(self, url):
        self.url = url.decode('utf-8')

    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=json.loads(self.body),
        )
        self.loop.create_task(self.dispatch(request))

    def add_route(self, path: str, methods_handler: dict):
        self.add(path, methods_handler)

    async def request_callback_handler(self, method, request):
        try:
            resp = await method(request)
        except Exception as exc:
            resp = format_exception(exc)

        if not isinstance(resp, Response):
            raise RuntimeError(f"expect Response instance but got {type(resp)}")

        self.response_writer(resp)
