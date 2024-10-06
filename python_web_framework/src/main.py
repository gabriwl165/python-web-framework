import logging
from asyncio.log import logger

from python_web_framework.src.app import App
from python_web_framework.src.request import Request
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
    try:
        print(request.body)
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    hello_world_app(app)
    app.start('127.0.0.1', 8080)