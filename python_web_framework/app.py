from python_web_framework.main import run_app
from python_web_framework.src.application.main import Application
from python_web_framework.src.handler.request import Request
from python_web_framework.src.handler.response import make_success_response

app = Application()

async def hello_world(request: Request):
    return make_success_response({"message": "Hello World"})

async def test_post(request: Request):
    body = await request.json()
    return make_success_response({"body": body })

app.router.add_route(
    path="/api", methods_handler={'GET': hello_world, 'POST': test_post}
)


if __name__ == '__main__':
    run_app(app, host='127.0.0.1', port=5001)
