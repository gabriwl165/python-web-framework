from python_web_framework.src.response import Response
from python_web_framework.src.request import Request
from python_web_framework.src.server.main import Server


def hello_world_app(server: Server):
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")
        return Response(
            200,
            {
                "hello": "world"
            }
        )

    async def process_request(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body!s}")
        return Response(
            200,
            {
                **request.body,
                'hello': 'back'
            }
        )

    server.add_route("/hello_world", {
        "GET": hello_world,
        "POST": process_request
    })
