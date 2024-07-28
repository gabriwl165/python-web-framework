from typing import Any


class Response:

    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
