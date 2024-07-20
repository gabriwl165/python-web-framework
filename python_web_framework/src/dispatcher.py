from python_web_framework.src.handler.request import Request
from python_web_framework.src.routing import Routes


class UrlDispatcher:

    def __init__(self):
        self.routes = Routes()

    def resolve(self, request: Request):
        """
        Function to resolve Route
        params: request - > Request
        return: path_parameters, handler
        """
        try:
            match = self.routes.match(request.url.raw_path)
            parameters = match.params if match.params else {}
            handler = match.anything.get(request.method.upper())
            if not handler:
                raise Exception("{method} Not allowed for {path}".format(method=request.method.upper()
                                                                                           , path=request.url.raw_path))
            return parameters, handler
        except Exception as e:
            raise Exception(f"Could not find {request.url.raw_path}")

    def add_route(self, path: str, methods_handler: dict):
        """
        Function to add api routes
        params: path "recipe/:id"
        params: methods_handler {method: handler}
        """
        self.routes.add(path, methods_handler)