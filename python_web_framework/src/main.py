from python_web_framework.src.app import App
from python_web_framework.src.request import Request
from python_web_framework.src.routes.jwt import jwt_app
from python_web_framework.src.routes.user import user_app
from routes.hello_world import hello_world_app

app = App()


@app.middleware()
async def add_logger(request: Request):
    try:
        print(f"HTTP {request.method}: {request.url} {request.body if request.body else ''}")
    except Exception as e:
        print(f"HTTP {request.method}: {request}, {e!s}")


@app.middleware()
async def add_security(request: Request):
    if request.url not in [""]:
        raise Exception("No permission")


if __name__ == "__main__":
    hello_world_app(app)
    jwt_app(app)
    user_app(app)
    app.start('127.0.0.1', 8080)