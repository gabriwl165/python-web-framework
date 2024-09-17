import re
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

    def add(self, path, methods_handler):
        self.mapping[self.parse_dynamic_url(path)] = methods_handler

    async def dispatch(self, request: Request):
        # Iterate through the compiled patterns
        for url, pattern in self.mapping.items():
            match = re.match(url, request.url)
            if not match:
                continue

            params = match.groupdict()
            handler = self.mapping[url].get(request.method)

            if handler:
                await self.request_callback_handler(handler, request, **params)
                return

        # Handle 404 Not Found if no matching route or method is found
        await self.response_writer(
            Response(
                404,
                {'message': 'Not Found'}
            )
        )

