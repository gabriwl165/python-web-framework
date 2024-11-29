import asyncio

from python_web_framework.src.server.main import Server


class App:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.server = Server(self.loop)
        self.socket = None

    def get(self, path):
        def decorator(func):
            self.server.add_route(path, "GET", func)
            return func
        return decorator

    def post(self, path):
        def decorator(func):
            self.server.add_route(path, "POST", func)
            return func
        return decorator

    def put(self, path):
        def decorator(func):
            self.server.add_route(path, "PUT", func)
            return func
        return decorator

    def middleware(self):
        def decorator(func):
            self.server.middlewares.append(func)
            return func

        return decorator

    def start(self, host, port):
        self.socket = self.loop.run_until_complete(
            self.loop.create_server(lambda: self.server, host=host, port=port)
        )
        print(f"Server started on {host}:{port}")
        self.loop.run_until_complete(self.socket.serve_forever())