class Request:

    def __init__(self, method, url, body):
        self.encoding = "utf-8"
        self.method = method
        self.url = url
        self.body = body
