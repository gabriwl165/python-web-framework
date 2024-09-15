import asyncio

from routes.hello_world import hello_world_app
from server.main import Server

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    protocol = Server(loop)
    hello_world_app(protocol)
    server = loop.run_until_complete(
        loop.create_server(lambda: protocol, host='127.0.0.1', port=8080)
    )
    loop.run_until_complete(server.serve_forever())
