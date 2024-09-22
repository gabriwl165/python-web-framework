from python_web_framework.src.app import App
from routes.hello_world import hello_world_app

app = App()


if __name__ == "__main__":
    hello_world_app(app)
    app.start('127.0.0.1', 8080)