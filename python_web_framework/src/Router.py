import re
from typing import Callable

from request import Request
from response import Response


class Router:

    def parse_dynamic_url(self, url):
        leading_slash = url.startswith('/')
        trailing_slash = url.endswith('/')
        url = url.strip('/')

        pattern = re.compile(r"{(.*?)}")

        url_path = [
            pattern.sub(lambda m: f"(?P<{m.group(1)}>[^/]+?)", part)
            for part in url.split('/') if part
        ]

        path = '/' + '/'.join(url_path) if leading_slash else '/'.join(url_path)
        if trailing_slash and not path.endswith('/'):
            path += '/'

        return f"^{path}$"

    def add(self, path: str, method: str, handler: Callable):
        self.mapping.append((self.parse_dynamic_url(path), method, handler))

    async def dispatch(self, request: Request):
        # Iterate through the compiled patterns
        handler = [
            (handler, re.match(path, request.url))
            for path, method, handler in self.mapping
            if re.match(path, request.url) and
               method == request.method
        ]
        handle, match = handler[0]
        params = match.groupdict()
        if handler:
            await self.request_callback_handler(handle, request, **params)
            return

        # Handle 404 Not Found if no matching route or method is found
        await self.response_writer(
            Response(
                404,
                {'message': 'Not Found'}
            )
        )

