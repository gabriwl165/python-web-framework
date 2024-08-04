import json
from typing import Any
from http.server import BaseHTTPRequestHandler


class Response:

    def __init__(
            self,
            status_code: int,
            body: Any
    ):
        self.status_code = status_code
        self.body = body
        self.version = "1.1"
        self.content_type = "application/json"
        self.headers = None

    def __str__(self):
        status_msg, _ = BaseHTTPRequestHandler.responses.get(self.status_code)
        messages = [
            f"HTTP/{self.version} {self.status_code} {status_msg}",
            f"Content-Type: {self.content_type}",
            f"Content-Length: {len(self.body)}",
            f"Connection: close"
        ]

        if self.headers:
            for header, value in self.headers.items():
                messages.append(f"{header}: {value}")

        if self.body is None:
            return "\n".join(messages)

        if isinstance(self.body, str):
            messages.append("\n" + self.body)
        elif isinstance(self.body, dict):
            messages.append("\n" + json.dumps(self.body))

        return "\n".join(messages)


