import asyncio
from httptools import HttpRequestParser


class Server(asyncio.Protocol, HttpRequestParser):
    def __init__(self):
        super().__init__(None)
        self._encoding = "utf-8"
        self._request_parser = HttpRequestParser(self)

    def data_received(self, data):
        print("Received: ", data)
        result = self._request_parser.feed_data(data)
        http_version = self._request_parser.get_http_version()
        print(result)

    def feed_data(self, data: bytes):
        pass


loop = asyncio.get_event_loop()
protocol = Server()
server = loop.run_until_complete(
    loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
)
loop.run_until_complete(server.serve_forever())
