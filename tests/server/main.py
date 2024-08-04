import asyncio
from asyncio.selector_events import _SelectorSocketTransport
from functools import partial
from traceback import format_exception
from typing import Optional

from httptools import HttpRequestParser

from tests.Router import Router
from tests.request import Request
from tests.response import Response


async def _handler(self, request, response_writer):
    """
    Process incoming request
    :params request -> Request
    :params response_writer
    """
    try:
        match_info, handler = self._router.resolve(request)

        request.match_info = match_info

        if self._middlewares:
            for md in self._middlewares:
                handler = partial(md, handler=handler)

        resp = await handler(request)
    except Exception as exc:
        resp = format_exception(exc)

    if not isinstance(resp, Response):
        raise RuntimeError(f"expect Response instance but got {type(resp)}")

    response_writer(resp)


class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._encoding = "utf-8"
        self.url = None
        self.body = None
        self.transport: _SelectorSocketTransport = None
        self._request_parser = HttpRequestParser(self)
        self._request_callback_handler = self.request_callback_handler
        self.router = Router(self.loop, self._request_callback_handler)

    def connection_made(self, transport):
        self.transport = transport

    def response_writer(self, response):
        self.transport.write(str(response).encode(self._encoding))
        self.transport.close()

    def data_received(self, data):
        self._request_parser.feed_data(data)

    def on_body(self, data):
        self.body = data

    def on_url(self, url):
        self.url = url.decode('utf-8')

    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=self.body,
        )
        self.loop.create_task(self.router.dispatch(request))

    def add_route(self, path: str, methods_handler: dict):
        self.router.add(path, methods_handler)

    async def request_callback_handler(self, method, request):
        try:
            resp = await method(request)
        except Exception as exc:
            resp = format_exception(exc)

        if not isinstance(resp, Response):
            raise RuntimeError(f"expect Response instance but got {type(resp)}")

        self.response_writer(resp)
