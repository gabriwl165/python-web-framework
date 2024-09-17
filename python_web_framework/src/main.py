import asyncio

from python_web_framework.src.routes import hello_world_app
from python_web_framework.src.server import Server

loop = asyncio.get_event_loop()
protocol = Server()

hello_world_app(protocol)

server = loop.run_until_complete(
    loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
)
loop.run_until_complete(server.serve_forever())
