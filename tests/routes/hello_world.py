from tests.Response import Response
from tests.request import Request
from tests.server.main import Server


def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")

    server.add_route("/hello_world", {"GET": hello_world})
