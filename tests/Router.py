import asyncio

from tests.request import Request


class Router:
    def __init__(self, loop):
        self.mapping = {}
        self.loop: asyncio.AbstractEventLoop = loop

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            return
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            return

        self.loop.create_task(method_handler(request))
