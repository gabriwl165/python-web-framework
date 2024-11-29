from python_web_framework.src.app import App
from python_web_framework.src.request import Request
from python_web_framework.src.response import Response


def hello_world_app(app: App):
    @app.get("/hello_world")
    async def hello_world(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body}")
        return Response(
            200,
            {
                "hello": "world"
            }
        )

    @app.post("/hello_world")
    async def process_request(request: Request):
        print(f"Handle: {request.method} {request.url} {request.body!s}")
        return Response(
            200,
            {
                **request.body,
                'hello': 'back'
            }
        )

    @app.get("/hello_world/{name}")
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
