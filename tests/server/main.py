import asyncio
from typing import Optional

from httptools import HttpRequestParser

from tests.Router import Router
from tests.request import Request


class Server(asyncio.Protocol):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._encoding = "utf-8"
        self.url = None
        self.body = None
        self._request_parser = HttpRequestParser(self)
        self.router = Router(self.loop)

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
        self.router.dispatch(request)

    def add_route(self, path: str, methods_handler: dict):
        self.router.add(path, methods_handler)
