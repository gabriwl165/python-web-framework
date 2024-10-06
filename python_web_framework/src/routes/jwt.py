from python_web_framework.src.app import App
from python_web_framework.src.request import Request
import jwt

from python_web_framework.src.response import Response

algorithm = "HS256"
secret = "test"


def jwt_app(app: App):

    @app.post("/login")
    async def login(request: Request):
        try:
            if not request.body:
                return Response(
                    400,
                    {
                        "message": "Missing body"
                    }
                )

            login = request.body.get("login", None)
            password = request.body.get("password", None)
            if not login or not password:
                return Response(
                    400,
                    {
                        "message": "Login and password must be provided."
                    }
                )

            if login != "admin" or password != "password":
                return Response(
                    400,
                    {
                        "message": "Login or password is incorrect."
                    }
                )

            encoded_jwt = jwt.encode({
                **request.body,
                "role": "admin"
            }, secret, algorithm=algorithm)
            
            return Response(
                200,
                {
                    "token": encoded_jwt
                }
            )

        except Exception as e:
            print(e)