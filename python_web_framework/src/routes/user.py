import jwt

from python_web_framework.src.app import App
from python_web_framework.src.request import Request
from python_web_framework.src.response import Response

algorithm = "HS256"
secret = "test"


def user_app(app: App):

    @app.get("/user/me")
    async def read_me(request: Request):
        try:
            encoded_jwt = request.headers['Authorization']
            info = jwt.decode(encoded_jwt, secret, algorithms=[algorithm])
            return Response(
                200,
                info
            )
        except Exception as e:
            print(str(e))
