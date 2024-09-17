import asyncio
import json
from traceback import format_exception
from typing import Optional

from httptools import HttpRequestParser

from python_web_framework.src.response import Response
from python_web_framework.src.router import Router
from python_web_framework.src.request import Request


class Server(asyncio.Protocol, Router):
    def __init__(self, loop=None):
        self.mapping = {}
        self.loop = loop or asyncio.get_event_loop()
        self.encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser = HttpRequestParser(self)
        self.transport: Optional[asyncio.Transport] = None

    async def request_callback_handler(self, method, request):
        try:
            resp = await method(request)
        except Exception as exc:
            resp = format_exception(exc)

        if not isinstance(resp, Response):
            raise RuntimeError(f"expect Response instance but got {type(resp)}")

        self.response_writer(resp)

    def response_writer(self, response):
        self.transport.write(str(response).encode(self.encoding))
        self.transport.close()

    def connection_made(self, transport):
        self.transport = transport

    def add_route(self, path: str, methods_handler: dict):
        self.add(path, methods_handler)

    def on_url(self, url):
        self.url = url.decode('utf-8')

    def data_received(self, data):
        self._request_parser.feed_data(data)

    def on_body(self, data):
        self.body = data.decode(self.encoding)

    def on_message_complete(self):
        request = Request(
            method=self._request_parser.get_method().decode('utf-8'),
            url=self.url,
            body=json.loads(self.body),
        )
        self.loop.create_task(self.dispatch(request))

