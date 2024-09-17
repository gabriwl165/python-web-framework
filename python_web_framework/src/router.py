import asyncio

from python_web_framework.src.request import Request
from python_web_framework.src.response import Response


class Router:
    def add(self, path, methods_handler):
        self.mapping[path] = methods_handler

    async def dispatch(self, request: Request):
        handlers = self.mapping.get(request.url, None)
        if not handlers:
            await self.response_writer(Response(
              404,
                {
                    'message': f'Not Found'
                }
            ))
        method_handler = handlers.get(request.method, None)
        if not method_handler:
            await self.response_writer(Response(
                404,
                {
                    'message': f'Not Found'
                }
            ))

        await self.request_callback_handler(method_handler, request)
