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

    async def process_dynamic_url(request: Request, name: str):
        try:
            return Response(
                200,
                {
                    'msg': f'Hello {name}'
                }
            )
        except Exception as e:
            print(e)

    server.add_route("/hello_world", {
        "GET": hello_world,
        "POST": process_request
    })

    server.add_route("/hello_world/{name}", {
        "GET": process_dynamic_url
    })
