import asyncio
from functools import partial, wraps
from traceback import format_exception

from python_web_framework.src.dispatcher import UrlDispatcher
from python_web_framework.src.handler.response import Response
from python_web_framework.src.server import Server


class Application:
    def __init__(self, loop=None, middlewares=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._router = UrlDispatcher()
        self._on_startup = []
        self._on_shutdown = []

        if middlewares is None:
            middlewares = []
        self._middlewares = middlewares

    @property
    def loop(self):
        return self._loop

    @property
    def router(self):
        return self._router

    @property
    def on_startup(self):
        return self._on_startup

    @property
    def on_shutdown(self):
        return self._on_shutdown

    def route(self, path, method="GET"):
        """
        Decorator Function for handler registration
        :params path
        :params method
        """

        @wraps(func)
        def handle(func):
            self._router.add_route(method, path, func)

        return handle

    async def startup(self):
        coros = [func(self) for func in self._on_startup]
        await asyncio.gather(*coros, loop=self._loop)

    async def shutdown(self):
        print("Shutdown process")
        coros = [func(self) for func in self._on_shutdown]
        await asyncio.gather(*coros, loop=self._loop)

    def _make_server(self):
        return Server(loop=self._loop, handler=self._handler, app=self)

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
