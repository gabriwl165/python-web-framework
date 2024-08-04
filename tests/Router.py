import asyncio

from tests.request import Request


class Router:
    def __init__(self, loop, handler):
        self.mapping = {}
        self.callback_handler = handler
        self.loop: asyncio.AbstractEventLoop = loop

    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    async def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            return
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            return

        await self.callback_handler(method_handler, request)

